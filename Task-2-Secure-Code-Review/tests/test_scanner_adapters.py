"""Additional adapter tests for success and malformed-scan paths."""

from __future__ import annotations

import pytest

from app.scanner import bandit_runner, semgrep_runner
from app.scanner.bandit_runner import BanditRunner
from app.scanner.common import ScannerCommandResult, ScannerError
from app.scanner.semgrep_runner import SemgrepRunner


def _sample(tmp_path):
    (tmp_path / "sample.py").write_text("print('safe')\n", encoding="utf-8")
    return tmp_path


def test_semgrep_returns_normalized_findings(monkeypatch, tmp_path):
    target = _sample(tmp_path)
    payload = {
        "results": [
            {
                "check_id": "python.lang.security.audit.eval",
                "path": str(target / "sample.py"),
                "start": {"line": 4},
                "end": {"line": 6},
                "extra": {
                    "message": "Avoid eval\nSecond line",
                    "severity": "ERROR",
                    "lines": "eval(user_input)",
                    "metadata": {
                        "cwe": ["CWE-95"],
                        "owasp": ["A03:2021"],
                        "confidence": "HIGH",
                        "fix": "Use ast.literal_eval",
                    },
                },
            }
        ],
        "errors": [],
    }
    monkeypatch.setattr(semgrep_runner, "semgrep_command_prefix", lambda: ["semgrep"])
    monkeypatch.setattr(
        semgrep_runner,
        "run_json_command",
        lambda *args, **kwargs: ScannerCommandResult(0, payload, ""),
    )

    findings = SemgrepRunner().scan(target)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "python.lang.security.audit.eval"
    assert finding.severity.value == "HIGH"
    assert finding.start_line == 4
    assert finding.end_line == 6
    assert finding.cwe_id == "CWE-95"
    assert finding.owasp_mapping == "A03:2021"
    assert finding.file_path == "sample.py"
    assert finding.title == "Avoid eval"


def test_semgrep_rejects_malformed_results(monkeypatch, tmp_path):
    target = _sample(tmp_path)
    monkeypatch.setattr(semgrep_runner, "semgrep_command_prefix", lambda: ["semgrep"])
    monkeypatch.setattr(
        semgrep_runner,
        "run_json_command",
        lambda *args, **kwargs: ScannerCommandResult(0, {"results": "nope"}, ""),
    )

    with pytest.raises(ScannerError) as error:
        SemgrepRunner().scan(target)
    assert error.value.code == "semgrep_malformed"


def test_semgrep_rejects_analysis_errors(monkeypatch, tmp_path):
    target = _sample(tmp_path)
    monkeypatch.setattr(semgrep_runner, "semgrep_command_prefix", lambda: ["semgrep"])
    monkeypatch.setattr(
        semgrep_runner,
        "run_json_command",
        lambda *args, **kwargs: ScannerCommandResult(0, {"results": [], "errors": [{}]}, ""),
    )

    with pytest.raises(ScannerError) as error:
        SemgrepRunner().scan(target)
    assert error.value.code == "semgrep_errors"


def test_semgrep_rejects_nonzero_exit(monkeypatch, tmp_path):
    target = _sample(tmp_path)
    monkeypatch.setattr(semgrep_runner, "semgrep_command_prefix", lambda: ["semgrep"])
    monkeypatch.setattr(
        semgrep_runner,
        "run_json_command",
        lambda *args, **kwargs: ScannerCommandResult(2, {}, "boom"),
    )

    with pytest.raises(ScannerError) as error:
        SemgrepRunner().scan(target)
    assert error.value.code == "semgrep_failed"


def test_semgrep_empty_directory_returns_nothing(monkeypatch, tmp_path):
    monkeypatch.setattr(semgrep_runner, "semgrep_command_prefix", lambda: ["semgrep"])

    assert SemgrepRunner().scan(tmp_path) == []


def test_bandit_rejects_malformed_results(monkeypatch, tmp_path):
    target = _sample(tmp_path)
    monkeypatch.setattr(
        bandit_runner,
        "run_json_command",
        lambda *args, **kwargs: ScannerCommandResult(0, {"results": {}}, ""),
    )

    with pytest.raises(ScannerError) as error:
        BanditRunner().scan(target)
    assert error.value.code == "bandit_malformed"


def test_bandit_rejects_parse_errors(monkeypatch, tmp_path):
    target = _sample(tmp_path)
    monkeypatch.setattr(
        bandit_runner,
        "run_json_command",
        lambda *args, **kwargs: ScannerCommandResult(0, {"results": [], "errors": [{}]}, ""),
    )

    with pytest.raises(ScannerError) as error:
        BanditRunner().scan(target)
    assert error.value.code == "bandit_parse_errors"


def test_bandit_rejects_nonzero_exit(monkeypatch, tmp_path):
    target = _sample(tmp_path)
    monkeypatch.setattr(
        bandit_runner,
        "run_json_command",
        lambda *args, **kwargs: ScannerCommandResult(2, {}, "boom"),
    )

    with pytest.raises(ScannerError) as error:
        BanditRunner().scan(target)
    assert error.value.code == "bandit_failed"


def test_bandit_skips_non_dict_items_and_handles_missing_fields(monkeypatch, tmp_path):
    target = _sample(tmp_path)
    payload = {
        "results": [
            "not-a-dict",
            {
                "test_id": "B101",
                "filename": "sample.py",
                "line_number": "not-a-number",
                "issue_severity": "UNKNOWN",
            },
        ],
        "errors": [],
    }
    monkeypatch.setattr(
        bandit_runner,
        "run_json_command",
        lambda *args, **kwargs: ScannerCommandResult(1, payload, ""),
    )

    findings = BanditRunner().scan(target)

    assert len(findings) == 1
    assert findings[0].start_line == 0
    assert findings[0].end_line == 0
    assert findings[0].severity.value == "MEDIUM"
