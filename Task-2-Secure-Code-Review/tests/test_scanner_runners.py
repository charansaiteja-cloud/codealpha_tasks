"""Regression tests for the individual scanner adapter classes."""
from __future__ import annotations

import pytest

from app.scanner import bandit_runner, semgrep_runner
from app.scanner.bandit_runner import BanditRunner
from app.scanner.common import ScannerCommandResult, ScannerError
from app.scanner.semgrep_runner import SemgrepRunner


def test_bandit_runner_propagates_failure(monkeypatch, tmp_path):
    (tmp_path / "sample.py").write_text("print('safe')\n", encoding="utf-8")

    def fail(*args, **kwargs):
        raise ScannerError("timeout", "Bandit exceeded the timeout")

    monkeypatch.setattr(bandit_runner, "run_json_command", fail)

    with pytest.raises(ScannerError) as error:
        BanditRunner().scan(tmp_path)
    assert error.value.code == "timeout"


def test_semgrep_runner_propagates_failure(monkeypatch, tmp_path):
    (tmp_path / "sample.py").write_text("print('safe')\n", encoding="utf-8")
    monkeypatch.setattr(semgrep_runner, "semgrep_command_prefix", lambda: ["semgrep"])

    def fail(*args, **kwargs):
        raise ScannerError("semgrep_not_installed", "Semgrep is not installed")

    monkeypatch.setattr(semgrep_runner, "run_json_command", fail)

    with pytest.raises(ScannerError) as error:
        SemgrepRunner().scan(tmp_path)
    assert error.value.code == "semgrep_not_installed"


def test_bandit_runner_returns_normalized_findings(monkeypatch, tmp_path):
    (tmp_path / "sample.py").write_text("print('safe')\n", encoding="utf-8")
    payload = {
        "results": [
            {
                "test_id": "B602",
                "test_name": "subprocess_popen_with_shell_equals_true",
                "filename": str(tmp_path / "sample.py"),
                "line_number": 3,
                "line_range": [3, 4],
                "issue_severity": "HIGH",
                "issue_confidence": "HIGH",
                "issue_text": "shell=True",
                "issue_cwe": {"id": 78},
                "code": "subprocess.run(cmd, shell=True)",
            }
        ],
        "errors": [],
    }
    monkeypatch.setattr(
        bandit_runner,
        "run_json_command",
        lambda *args, **kwargs: ScannerCommandResult(1, payload, ""),
    )

    findings = BanditRunner().scan(tmp_path)
    assert len(findings) == 1
    assert findings[0].rule_id == "B602"
    assert findings[0].file_path == "sample.py"
    assert findings[0].start_line == 3
    assert findings[0].end_line == 4
    assert findings[0].cwe_id == "CWE-78"
