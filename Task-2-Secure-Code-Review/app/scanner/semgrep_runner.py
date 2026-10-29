"""Semgrep scanner adapter used by the scanner API."""

from __future__ import annotations

import hashlib
import importlib.metadata
import logging
from pathlib import Path

from app.models.findings import Finding, Severity
from app.scanner.base import BaseScanner
from app.scanner.common import (
    ScannerError,
    collect_python_files,
    display_path,
    run_json_command,
    semgrep_command_prefix,
    semgrep_rules_path,
)

logger = logging.getLogger(__name__)

_SEVERITY_MAP = {
    "CRITICAL": Severity.CRITICAL,
    "ERROR": Severity.HIGH,
    "WARNING": Severity.MEDIUM,
    "INFO": Severity.LOW,
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


class SemgrepRunner(BaseScanner):
    name = "Semgrep"

    def __init__(self) -> None:
        self.version = _package_version("semgrep")

    def scan(self, target_dir: Path) -> list[Finding]:
        findings: list[Finding] = []
        resolved_target = Path(target_dir).resolve()
        try:
            files = collect_python_files(resolved_target)
            if not files:
                return findings

            result = run_json_command(
                [
                    *semgrep_command_prefix(),
                    "scan",
                    "--config",
                    str(semgrep_rules_path()),
                    "--json",
                    "--metrics=off",
                    "--error",
                    "--strict",
                    "--disable-version-check",
                    "--no-rewrite-rule-ids",
                    *[str(path) for path in files],
                ],
                timeout=90,
            )
            if result.returncode not in (0, 1):
                raise ScannerError("semgrep_failed", result.stderr)
            if result.payload.get("errors"):
                raise ScannerError("semgrep_errors", "Semgrep reported analysis errors")

            raw_results = result.payload.get("results")
            if not isinstance(raw_results, list):
                raise ScannerError("semgrep_malformed", "Semgrep results were not a list")
            for item in raw_results:
                if not isinstance(item, dict):
                    continue
                extra = item.get("extra") or {}
                if not isinstance(extra, dict):
                    extra = {}
                metadata = extra.get("metadata") or {}
                if not isinstance(metadata, dict):
                    metadata = {}

                rule_id = item.get("check_id", "semgrep.rule")
                file_path = display_path(item.get("path", ""), fallback_base=resolved_target)
                start = item.get("start") or {}
                end = item.get("end") or {}
                if not isinstance(start, dict):
                    start = {}
                if not isinstance(end, dict):
                    end = {}
                start_line = _coerce_line(start.get("line"))
                end_line = max(start_line, _coerce_line(end.get("line")))

                message = str(extra.get("message", "Security vulnerability detected"))
                raw_severity = str(extra.get("severity", "WARNING")).upper()
                severity = _SEVERITY_MAP.get(raw_severity, Severity.MEDIUM)

                cwe = metadata.get("cwe")
                if isinstance(cwe, list):
                    cwe = cwe[0] if cwe else None
                owasp = metadata.get("owasp")
                if isinstance(owasp, list):
                    owasp = owasp[0] if owasp else None

                unique_str = f"{rule_id}:{file_path}:{start_line}"
                finding_id = hashlib.sha256(unique_str.encode("utf-8")).hexdigest()[:16]

                findings.append(
                    Finding(
                        finding_id=finding_id,
                        rule_id=rule_id,
                        title=message.splitlines()[0][:200],
                        description=message,
                        severity=severity,
                        confidence=str(metadata.get("confidence", "MEDIUM")).upper(),
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line,
                        code_snippet=str(extra.get("lines", "")).strip(),
                        remediation=str(
                            metadata.get(
                                "fix",
                                "Review the code path and apply secure coding practices.",
                            )
                        ),
                        cwe_id=str(cwe) if cwe else None,
                        owasp_mapping=str(owasp) if owasp else None,
                        scanner_name=self.name,
                        scanner_version=self.version,
                    )
                )
        except ScannerError:
            raise
        except Exception as exc:
            logger.exception("Unexpected Semgrep runner failure")
            raise ScannerError("unexpected_error", type(exc).__name__) from exc

        return findings
