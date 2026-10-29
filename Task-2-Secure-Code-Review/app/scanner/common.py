"""Shared helpers for running external security scanners safely."""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import shutil
import subprocess  # nosec B404
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEMGREP_RULES_PATH = PROJECT_ROOT / ".semgrep" / "rules.yml"

# Directories that must never be scanned. They contain dependencies, generated
# artefacts, local configuration, or the database rather than application code.
EXCLUDED_DIRECTORIES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        ".semgrep-venv",
        ".tox",
        ".nox",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "__pycache__",
        "node_modules",
        "site-packages",
        "data",
        "reports",
        "build",
        "dist",
        "htmlcov",
    }
)

DEFAULT_MAX_SCAN_FILES = 2000


class ScannerError(RuntimeError):
    """A scanner was unavailable or its output could not be trusted."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(detail or code)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class ScannerCommandResult:
    returncode: int
    payload: dict[str, Any]
    stderr: str


def _positive_int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning("Ignoring invalid %s value; using %d", name, default)
        return default
    return value if value > 0 else default


def max_scan_files() -> int:
    return _positive_int_env("LAB_MAX_SCAN_FILES", DEFAULT_MAX_SCAN_FILES)


def display_path(
    path: Path | str,
    *,
    base: Path | None = None,
    fallback_base: Path | None = None,
) -> str:
    """Return a response-safe path relative to a trusted base directory.

    API responses must never disclose absolute server paths. Try *base*
    (the project root by default) first, then *fallback_base* (normally the
    scan target), and finally return only the file name.
    """
    if path is None or str(path) == "":
        return ""
    candidate = Path(path)
    try:
        resolved = candidate.resolve()
    except (OSError, RuntimeError, ValueError):
        resolved = candidate

    for directory in (base or PROJECT_ROOT, fallback_base):
        if directory is None:
            continue
        try:
            return str(resolved.relative_to(Path(directory).resolve()))
        except (OSError, RuntimeError, ValueError):
            continue
    return resolved.name


def is_excluded_target(root: Path, target: Path) -> bool:
    """Return True when *target* is outside *root* or inside an excluded dir."""
    try:
        relative = target.relative_to(root)
    except ValueError:
        return True
    return any(part in EXCLUDED_DIRECTORIES for part in relative.parts)


def collect_python_files(root: Path, limit: int | None = None) -> list[Path]:
    """Collect regular Python files below *root* without following symlinks out.

    Directory symlinks are not followed. File symlinks are resolved and kept
    only when their destination remains inside the scan root.
    """
    root = Path(root).resolve()
    limit = limit if limit is not None else max_scan_files()
    files: list[Path] = []

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(dirpath)
        dirnames[:] = sorted(
            name
            for name in dirnames
            if name not in EXCLUDED_DIRECTORIES and not name.startswith(".")
        )

        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            candidate = (current / filename).resolve()
            if not candidate.is_file() or not candidate.is_relative_to(root):
                continue
            # A symlinked .py file can resolve into an excluded directory such
            # as data/ even when its destination is still inside the scan root.
            # Never hand that file to a scanner.
            relative = candidate.relative_to(root)
            if any(part in EXCLUDED_DIRECTORIES for part in relative.parts):
                continue
            files.append(candidate)
            if len(files) > limit:
                raise ScannerError(
                    "target_too_large",
                    f"target contains more than {limit} Python files",
                )

    return files


def semgrep_command_prefix() -> list[str]:
    """Return a command prefix for the installed Semgrep CLI.

    Prefer the executable installed alongside the running interpreter so the
    application uses the same environment it installed its dependencies into.
    Fall back to PATH and finally to the module entry point for older releases.
    """
    for executable_name in ("semgrep", "semgrep.exe"):
        candidate = Path(sys.executable).with_name(executable_name)
        if candidate.is_file():
            return [str(candidate)]

    executable = shutil.which("semgrep")
    if executable:
        return [executable]

    try:
        if importlib.util.find_spec("semgrep") is not None:
            return [sys.executable, "-m", "semgrep"]
    except (ImportError, ValueError):
        pass

    raise ScannerError("semgrep_not_installed", "Semgrep is not installed")


def semgrep_rules_path() -> Path:
    if not SEMGREP_RULES_PATH.is_file():
        raise ScannerError(
            "rules_missing",
            f"Semgrep rules file is missing: {SEMGREP_RULES_PATH}",
        )
    return SEMGREP_RULES_PATH


def _truncate(value: str, limit: int = 500) -> str:
    cleaned = " ".join(value.split())
    return cleaned[:limit]


def run_json_command(
    command: list[str],
    *,
    timeout: int,
    env: dict[str, str] | None = None,
) -> ScannerCommandResult:
    """Run a scanner and parse its single JSON document.

    Scanner stderr is retained for server-side diagnostics only. Callers must
    expose a stable error code to clients rather than raw tool output.
    """
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    # Scanners only need their normal runtime environment. Never hand the
    # application's shared secret to a child process that does not need it.
    merged_env.pop("LAB_API_KEY", None)
    # Semgrep refuses to create its "auto" configuration when metrics are off.
    # All invocations use explicit rule files, and metrics stay disabled.
    merged_env["SEMGREP_SEND_METRICS"] = "off"

    # argv list, shell=False, fixed tool names: no shell interpretation.
    try:
        completed = subprocess.run(  # nosec B603
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            env=merged_env,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired as exc:
        raise ScannerError("timeout", f"scanner exceeded {timeout}s") from exc
    except FileNotFoundError as exc:
        raise ScannerError("executable_not_found", str(exc)) from exc
    except PermissionError as exc:
        raise ScannerError("executable_not_permitted", str(exc)) from exc
    except (OSError, ValueError) as exc:
        raise ScannerError("execution_failed", str(exc)) from exc

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    if not stdout.strip():
        raise ScannerError("empty_output", _truncate(stderr) or "scanner produced no output")

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ScannerError("invalid_json", _truncate(stderr) or str(exc)) from exc

    if not isinstance(payload, dict):
        raise ScannerError("invalid_json", "scanner output was not a JSON object")

    return ScannerCommandResult(
        returncode=completed.returncode,
        payload=payload,
        stderr=_truncate(stderr),
    )
