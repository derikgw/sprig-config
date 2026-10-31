"""The scanner gate must distinguish findings, scan failures, and clean scans."""
import json

import pytest

from scripts import security_check


@pytest.mark.parametrize(
    ("report", "scan_exit", "expected"),
    [
        ({"paths": {"scanned": ["source.py"]}, "results": []}, 0, 0),
        ({"paths": {"scanned": ["source.py"]}, "results": [
            {"extra": {"severity": "WARNING"}},
        ]}, 0, 0),
        ({"paths": {"scanned": ["source.py"]}, "results": [
            {"extra": {"severity": "ERROR"}},
        ]}, 0, 1),
        ({"errors": [{"message": "Synthetic scan failure"}]}, 0, 2),
        ({"paths": {"scanned": []}, "results": []}, 0, 2),
        ({"paths": {"scanned": ["source.py"]}}, 0, 2),
        (None, 0, 2),
        (None, 2, 2),
    ],
)
def test_semgrep_gate_fails_closed(tmp_path, monkeypatch, report, scan_exit, expected):
    monkeypatch.setattr(security_check, "REPORTS", tmp_path)
    monkeypatch.setattr(security_check.shutil, "which", lambda _: "semgrep")
    # A stale successful report must not hide a failed or incomplete scan.
    (tmp_path / "semgrep.json").write_text(json.dumps({"results": []}))

    def run(command, **kwargs):
        if "--test" in command:
            return 0
        if report is not None:
            (tmp_path / "semgrep.json").write_text(json.dumps(report))
        return scan_exit

    monkeypatch.setattr(security_check, "run", run)
    assert security_check.scan_semgrep() == expected


def test_lock_audit_includes_inactive_packages_without_installing(tmp_path, monkeypatch):
    monkeypatch.setattr(security_check, "PROJECT", tmp_path)
    monkeypatch.setattr(security_check, "REPORTS", tmp_path)
    (tmp_path / "poetry.lock").write_text('''
[[package]]
name = "synthetic-package"
version = "1.0.0"
markers = "python_version < '1.0'"
groups = ["docs"]
''')
    commands = []

    def run(command):
        commands.append(command)
        return 1  # Vulnerability service result must propagate.

    monkeypatch.setattr(security_check, "run", run)
    assert security_check.audit_lock() == 1
    assert (tmp_path / "locked-requirements.txt").read_text() == "synthetic-package==1.0.0\n"
    assert "--disable-pip" in commands[0]
    assert "--no-deps" in commands[0]
    assert "--strict" in commands[0]


@pytest.mark.parametrize("content", ["", "[[package]]\nname='bad name'\nversion='1.0'\n"])
def test_invalid_lock_cannot_pass_audit(tmp_path, monkeypatch, content):
    monkeypatch.setattr(security_check, "PROJECT", tmp_path)
    monkeypatch.setattr(security_check, "REPORTS", tmp_path)
    (tmp_path / "poetry.lock").write_text(content)
    assert security_check.audit_lock() == 2
