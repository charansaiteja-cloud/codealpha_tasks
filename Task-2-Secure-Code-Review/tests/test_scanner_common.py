"""Regression tests for the shared scanner subprocess boundary."""

from __future__ import annotations

import subprocess

import pytest

from app.scanner import common
from app.scanner.common import ScannerError, display_path, run_json_command


def _completed(command, stdout: str, stderr: str = "", returncode: int = 0):
    return subprocess.CompletedProcess(
        command,
        returncode,
        stdout=stdout,
        stderr=stderr,
    )


def test_run_json_command_parses_json_object(monkeypatch):
    monkeypatch.setattr(
        common.subprocess,
        "run",
        lambda *args, **kwargs: _completed(args[0], '{"results": []}'),
    )

    result = run_json_command(["scanner"], timeout=5)
    assert result.returncode == 0
    assert result.payload == {"results": []}
    assert result.stderr == ""


def test_run_json_command_rejects_empty_output(monkeypatch):
    monkeypatch.setattr(
        common.subprocess,
        "run",
        lambda *args, **kwargs: _completed(args[0], "", "no output"),
    )

    with pytest.raises(ScannerError) as error:
        run_json_command(["scanner"], timeout=5)
    assert error.value.code == "empty_output"


@pytest.mark.parametrize("stdout", ["not json", "[]", "null", '"text"'])
def test_run_json_command_rejects_invalid_or_non_object_json(monkeypatch, stdout):
    monkeypatch.setattr(
        common.subprocess,
        "run",
        lambda *args, **kwargs: _completed(args[0], stdout),
    )

    with pytest.raises(ScannerError) as error:
        run_json_command(["scanner"], timeout=5)
    assert error.value.code == "invalid_json"


def test_run_json_command_reports_missing_executable():
    with pytest.raises(ScannerError) as error:
        run_json_command(
            ["/definitely-not-a-real-codealpha-scanner"],
            timeout=5,
        )
    assert error.value.code == "executable_not_found"


def test_run_json_command_reports_timeout(monkeypatch):
    def timed_out(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs.get("timeout", 5))

    monkeypatch.setattr(common.subprocess, "run", timed_out)

    with pytest.raises(ScannerError) as error:
        run_json_command(["scanner"], timeout=5)
    assert error.value.code == "timeout"


def test_run_json_command_does_not_leak_api_key_or_read_stdin(monkeypatch):
    captured = {}

    def fake_run(command, **kwargs):
        captured.update(kwargs)
        captured["command"] = command
        return _completed(command, '{"ok": true}')

    monkeypatch.setenv("LAB_API_KEY", "super-secret-api-key")
    monkeypatch.setattr(common.subprocess, "run", fake_run)

    run_json_command(["scanner"], timeout=5, env={"EXTRA_SETTING": "1"})

    assert "LAB_API_KEY" not in captured["env"]
    assert captured["env"]["SEMGREP_SEND_METRICS"] == "off"
    assert captured["env"]["EXTRA_SETTING"] == "1"
    assert captured["stdin"] == subprocess.DEVNULL


def test_display_path_never_returns_an_absolute_path(tmp_path):
    outside = tmp_path / "outside.py"
    outside.write_text("print('outside')\n", encoding="utf-8")

    assert display_path(outside) == "outside.py"
    assert display_path(outside, fallback_base=tmp_path) == "outside.py"
    assert display_path("") == ""
