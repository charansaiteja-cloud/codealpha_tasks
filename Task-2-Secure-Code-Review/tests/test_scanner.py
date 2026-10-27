import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.scanner import orchestrator as orchestrator_module
from app.scanner.common import ScannerCommandResult, ScannerError, collect_python_files

client = TestClient(main.app)


def test_orchestrator_invalid_directory(tmp_path):
    from app.scanner.orchestrator import ScanOrchestrator

    invalid_dir = tmp_path / "nonexistent"
    result = ScanOrchestrator().run_scan(invalid_dir)
    assert result["status"] == "error"
    assert result["summary"]["scanners_healthy"] is False
    assert result["summary"]["error"] == "invalid_target"


def test_collect_python_files_skips_dependencies_and_caches(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "main.py").write_text("print('safe')\n", encoding="utf-8")
    (tmp_path / ".venv" / "lib").mkdir(parents=True)
    (tmp_path / ".venv" / "lib" / "vendor.py").write_text(
        "print('vendor')\n", encoding="utf-8"
    )
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "cached.py").write_text(
        "print('cached')\n", encoding="utf-8"
    )

    files = collect_python_files(tmp_path)
    names = {path.name for path in files}
    assert names == {"main.py"}


def test_collect_python_files_skips_file_symlink_outside_root(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("print('outside')\n", encoding="utf-8")
    os.symlink(outside, root / "linked.py")

    assert collect_python_files(root) == []


def test_collect_python_files_skips_directory_symlink_outside_root(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "escaped.py").write_text("print('outside')\n", encoding="utf-8")
    os.symlink(outside, root / "linked-directory", target_is_directory=True)

    assert collect_python_files(root) == []


def test_collect_python_files_skips_symlink_into_excluded_directory(tmp_path):
    (tmp_path / "data").mkdir()
    database_module = tmp_path / "data" / "database_module.py"
    database_module.write_text("print('not application code')\n", encoding="utf-8")
    os.symlink(database_module, tmp_path / "linked.py")

    assert collect_python_files(tmp_path) == []


def test_scan_endpoint_unauthorized():
    response = client.post("/api/v1/scan", json={"target_path": "."})
    assert response.status_code == 401


def test_scan_endpoint_path_traversal(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "secret-key")
    response = client.post(
        "/api/v1/scan",
        json={"target_path": "../etc"},
        headers={"X-API-Key": "secret-key"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Path traversal detected."


def test_scan_endpoint_rejects_absolute_path(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "secret-key")
    response = client.post(
        "/api/v1/scan",
        json={"target_path": "/etc"},
        headers={"X-API-Key": "secret-key"},
    )
    assert response.status_code == 400


def test_scan_endpoint_rejects_symlink_escape(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "API_KEY", "secret-key")
    scan_root = tmp_path / "scan-root"
    scan_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "outside.py").write_text("print('outside')\n", encoding="utf-8")
    os.symlink(outside, scan_root / "escape", target_is_directory=True)
    monkeypatch.setattr(main, "SCAN_ROOT", scan_root.resolve())

    response = client.post(
        "/api/v1/scan",
        json={"target_path": "escape"},
        headers={"X-API-Key": "secret-key"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Path traversal detected."


def test_scan_endpoint_sibling_prefix_bypass(monkeypatch):
    """Regression test for string-prefix containment flaws (e.g. /workspace-evil)."""
    monkeypatch.setattr(main, "API_KEY", "secret-key")
    response = client.post(
        "/api/v1/scan",
        json={"target_path": "../CodeAlpha_SecureCodeReview-evil"},
        headers={"X-API-Key": "secret-key"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Path traversal detected."


@pytest.mark.parametrize(
    "target_path",
    [".git", ".venv", "data", "reports"],
)
def test_scan_endpoint_rejects_excluded_directories(monkeypatch, target_path):
    monkeypatch.setattr(main, "API_KEY", "secret-key")
    response = client.post(
        "/api/v1/scan",
        json={"target_path": target_path},
        headers={"X-API-Key": "secret-key"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Target directory is not allowed."


def test_scan_endpoint_rejects_control_characters(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "secret-key")
    response = client.post(
        "/api/v1/scan",
        json={"target_path": "app\n"},
        headers={"X-API-Key": "secret-key"},
    )
    assert response.status_code == 422


def test_scan_endpoint_rejects_oversized_target_path(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "secret-key")
    response = client.post(
        "/api/v1/scan",
        json={"target_path": "a" * 257},
        headers={"X-API-Key": "secret-key"},
    )
    assert response.status_code == 422


def test_scan_endpoint_success(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "secret-key")
    response = client.post(
        "/api/v1/scan",
        json={"target_path": "app"},
        headers={"X-API-Key": "secret-key"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["summary"]["scanners_healthy"] is True
    assert data["summary"]["scanner_statuses"] == {
        "bandit": "success",
        "semgrep": "success",
    }
    assert data["total_findings"] == 0
    assert data["findings"] == []


def test_scan_endpoint_returns_429_when_busy(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "secret-key")
    acquired = main._SCAN_SLOT.acquire(blocking=False)
    assert acquired is True
    try:
        response = client.post(
            "/api/v1/scan",
            json={"target_path": "app"},
            headers={"X-API-Key": "secret-key"},
        )
    finally:
        main._SCAN_SLOT.release()

    assert response.status_code == 429


def test_scan_endpoint_returns_503_when_all_scanners_fail(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "secret-key")

    class FailingOrchestrator:
        def __init__(self, *args, **kwargs):
            pass

        def run_scan(self, target_dir):
            return {
                "status": "error",
                "target_scanned": str(target_dir),
                "total_findings": 0,
                "findings": [],
                "summary": {"error": "all_scanners_failed"},
            }

    monkeypatch.setattr(main, "ScanOrchestrator", FailingOrchestrator)
    response = client.post(
        "/api/v1/scan",
        json={"target_path": "app"},
        headers={"X-API-Key": "secret-key"},
    )
    assert response.status_code == 503


def test_orchestrator_reports_partial_when_one_scanner_fails(monkeypatch, tmp_path):
    (tmp_path / "safe.py").write_text("print('safe')\n", encoding="utf-8")

    def fake_run_json_command(command, *, timeout, env=None):
        if "bandit" in command:
            return ScannerCommandResult(0, {"results": [], "errors": []}, "")
        raise ScannerError("timeout", "Semgrep exceeded the timeout")

    monkeypatch.setattr(orchestrator_module, "run_json_command", fake_run_json_command)
    monkeypatch.setattr(
        orchestrator_module, "semgrep_command_prefix", lambda: ["semgrep"]
    )
    result = orchestrator_module.ScanOrchestrator().run_scan(tmp_path)

    assert result["status"] == "partial"
    assert result["summary"]["status"] == "completed_with_warnings"
    assert result["summary"]["scanners_healthy"] is True
    assert result["summary"]["scanner_statuses"] == {
        "bandit": "success",
        "semgrep": "failed",
    }
    assert result["summary"]["scanner_errors"] == {"semgrep": "timeout"}


def test_orchestrator_reports_error_when_all_scanners_fail(monkeypatch, tmp_path):
    (tmp_path / "safe.py").write_text("print('safe')\n", encoding="utf-8")

    def fake_run_json_command(command, *, timeout, env=None):
        raise ScannerError("executable_not_found", "scanner is unavailable")

    monkeypatch.setattr(orchestrator_module, "run_json_command", fake_run_json_command)
    monkeypatch.setattr(
        orchestrator_module, "semgrep_command_prefix", lambda: ["semgrep"]
    )
    result = orchestrator_module.ScanOrchestrator().run_scan(tmp_path)

    assert result["status"] == "error"
    assert result["summary"]["status"] == "failed"
    assert result["summary"]["scanners_healthy"] is False
    assert result["summary"]["error"] == "all_scanners_failed"
    assert result["summary"]["scanner_errors"] == {
        "bandit": "executable_not_found",
        "semgrep": "executable_not_found",
    }
    assert result["findings"] == []


def test_malformed_scanner_records_are_normalized(tmp_path):
    bandit_findings = orchestrator_module._bandit_findings(
        {
            "results": [
                {
                    "test_id": "B000",
                    "filename": "",
                    "line_number": "not-a-number",
                    "line_range": "also-not-a-list",
                    "issue_severity": "unexpected",
                }
            ]
        },
        base=tmp_path,
    )
    assert bandit_findings[0]["line"] == 0
    assert bandit_findings[0]["end_line"] == 0
    assert bandit_findings[0]["severity"] == "MEDIUM"

    semgrep_findings = orchestrator_module._semgrep_findings(
        {
            "results": [
                {
                    "check_id": "codealpha.test",
                    "path": "",
                    "start": "not-an-object",
                    "end": None,
                    "extra": {"metadata": "not-a-dict"},
                }
            ]
        },
        base=tmp_path,
    )
    assert semgrep_findings[0]["line"] == 0
    assert semgrep_findings[0]["end_line"] == 0
    assert semgrep_findings[0]["severity"] == "MEDIUM"
