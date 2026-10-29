"""Run the same security checks locally and in CI without loading .env files."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parent
REPORTS = PROJECT / ".security-reports"
SEMGREP_VERSION = "1.182.1"


def run(command, *, cwd=PROJECT, env=None):
    print(f"\nRunning: {' '.join(map(str, command))}", flush=True)
    try:
        return subprocess.run(command, cwd=cwd, env=env, check=False).returncode
    except OSError as error:
        print(f"Cannot run check: {error}", file=sys.stderr)
        return 2


def scan_semgrep():
    executable = shutil.which("semgrep")
    if executable is None:
        candidate = Path.home() / ".local/bin/semgrep"
        executable = str(candidate) if candidate.is_file() else None
    if executable is None:
        print(f"Install Semgrep: uv tool install semgrep=={SEMGREP_VERSION}", file=sys.stderr)
        return 2
    env = dict(os.environ, SEMGREP_SEND_METRICS="off", SEMGREP_ENABLE_VERSION_CHECK="0")
    if run([
        executable, "--test", "--config", ".semgrep/security.yml", ".semgrep/security.py",
    ], cwd=ROOT, env=env):
        return 2
    report = REPORTS / "semgrep.json"
    # Never interpret a stale report as a successful scan.
    report.unlink(missing_ok=True)
    result = run([
        executable, "scan", "--config", "p/python", "--config", ".semgrep/security.yml",
        "--metrics", "off", "--disable-version-check", "--strict",
        "--json-output", str(report), "--sarif-output", str(REPORTS / "semgrep.sarif"),
        "sprig-config-module/src",
    ], cwd=ROOT, env=env)
    if result:
        return result
    try:
        data = json.loads(report.read_text())
        if data.get("errors") or not data.get("paths", {}).get("scanned"):
            print("Semgrep reported scan errors or scanned no files.", file=sys.stderr)
            return 2
        findings = data["results"]
        blocking = sum(item["extra"]["severity"] == "ERROR" for item in findings)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Invalid Semgrep report: {error}", file=sys.stderr)
        return 2
    print(f"Semgrep: {len(findings)} findings; {blocking} ERROR findings block this check.")
    return int(blocking > 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=["bandit", "semgrep", "tests", "audit"])
    parser.add_argument("--deep", action="store_true", help="500 generated examples per property")
    parser.add_argument("--strict-known", action="store_true", help="Fail on unresolved issue #41 cases")
    args = parser.parse_args()
    REPORTS.mkdir(exist_ok=True)
    env = dict(os.environ)
    env["HYPOTHESIS_PROFILE"] = "security-deep" if args.deep else "security"
    if args.strict_known:
        env["SECURITY_ENFORCE_KNOWN"] = "1"
    checks = {
        "bandit": lambda: run([sys.executable, "-m", "bandit", "-r", "src"]),
        "semgrep": scan_semgrep,
        "tests": lambda: run([
            sys.executable, "-m", "pytest", "security_tests", "-q", "-rxX",
            f"--junitxml={REPORTS / 'security-tests.xml'}",
        ], env=env),
        "audit": lambda: run([sys.executable, "-m", "pip_audit"]),
    }
    results = {name: check() for name, check in checks.items() if args.only in (None, name)}
    print("\nSecurity check exit codes:", results)
    print("Known #41 cases are explicit strict xfails unless --strict-known is used.")
    return int(any(results.values()))


if __name__ == "__main__":
    raise SystemExit(main())
