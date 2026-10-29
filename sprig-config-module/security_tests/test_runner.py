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
