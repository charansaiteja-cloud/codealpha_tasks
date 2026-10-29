"""Bandit scanner adapter used by the scanner API."""

from __future__ import annotations

import hashlib
import importlib.metadata
import logging
import sys
from pathlib import Path

from app.models.findings import Finding, Severity
from app.scanner.base import BaseScanner
from app.scanner.common import (
    ScannerError,
    collect_python_files,
    display_path,
    run_json_command,
)

logger = logging.getLogger(__name__)

_SEVERITY_MAP = {
    "HIGH": Severity.HIGH,
    "MEDIUM": Severity.MEDIUM,
    "LOW": Severity.LOW,
}


def _coerce_line(value: object) -> int:
    if isinstance(value, bool):
        return 0
    try:
        line = int(value)
    except (TypeError, ValueError, OverflowError):
        return 0
    return max(line, 0)


def _package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


class BanditRunner(BaseScanner):
    name = "Bandit"

    def __init__(self) -> None:
        self.version = _package_version("bandit")

    def scan(self, target_dir: Path) -> list[Finding]:
        findings: list[Finding] = []
        resolved_target = Path(target_dir).resolve()
        try:
            files = collect_python_files(resolved_target)
            if not files:
                return findings

            result = run_json_command(
                [
                    sys.executable,
                    "-m",
                    "bandit",
                    "-f",
                    "json",
                    "-q",
                    "-ll",
                    *[str(path) for path in files],
                ],
                timeout=60,
            )
            if result.returncode not in (0, 1):
                raise ScannerError("bandit_failed", result.stderr)
            if result.payload.get("errors"):
                raise ScannerError("bandit_parse_errors", "Bandit reported file errors")

            raw_results = result.payload.get("results")
            if not isinstance(raw_results, list):
                raise ScannerError("bandit_malformed", "Bandit results were not a list")
            for item in raw_results:
                if not isinstance(item, dict):
                    continue
                rule_id = item.get("test_id", "B000")
                file_path = display_path(item.get("filename", ""), fallback_base=resolved_target)
                line_number = _coerce_line(item.get("line_number"))
                line_range = item.get("line_range")
                if isinstance(line_range, list) and line_range:
                    end_line = max(line_number, _coerce_line(line_range[-1]))
                else:
                    end_line = line_number
                raw_severity = str(item.get("issue_severity", "MEDIUM")).upper()
                severity = _SEVERITY_MAP.get(raw_severity, Severity.MEDIUM)

                cwe = item.get("issue_cwe") or {}
                cwe_id = f"CWE-{cwe.get('id')}" if isinstance(cwe, dict) and cwe.get("id") else None

                unique_str = f"{rule_id}:{file_path}:{line_number}"
                finding_id = hashlib.sha256(unique_str.encode("utf-8")).hexdigest()[:16]

                findings.append(
                    Finding(
                        finding_id=finding_id,
                        rule_id=rule_id,
                        title=item.get("test_name", "Security issue"),
                        description=item.get("issue_text", ""),
                        severity=severity,
                        confidence=str(item.get("issue_confidence", "MEDIUM")).upper(),
                        file_path=file_path,
                        start_line=line_number,
                        end_line=end_line,
                        code_snippet=str(item.get("code", "")).strip(),
                        remediation=(
                            "Review secure coding guidelines for Python and remediate "
                            "the vulnerable pattern."
                        ),
                        cwe_id=cwe_id,
                        scanner_name=self.name,
                        scanner_version=self.version,
                    )
                )
        except ScannerError:
            raise
        except Exception as exc:
            logger.exception("Unexpected Bandit runner failure")
            raise ScannerError("unexpected_error", type(exc).__name__) from exc

        return findings
