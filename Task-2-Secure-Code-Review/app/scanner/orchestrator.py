"""Orchestration and normalisation for Bandit and Semgrep scans."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from app.scanner.common import (
    PROJECT_ROOT,
    ScannerError,
    collect_python_files,
    display_path,
    is_excluded_target,
    run_json_command,
    semgrep_command_prefix,
    semgrep_rules_path,
)

logger = logging.getLogger(__name__)

SEVERITY_WEIGHTS = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
    "INFO": 0,
}

VALID_SEVERITIES = frozenset({"CRITICAL", "HIGH", "MEDIUM", "LOW"})
SEMGREP_SEVERITIES = {
    "CRITICAL": "CRITICAL",
    "ERROR": "HIGH",
    "WARNING": "MEDIUM",
    "INFO": "LOW",
}
BANDIT_TIMEOUT_SECONDS = 60
SEMGREP_TIMEOUT_SECONDS = 90


def _severity_breakdown() -> dict[str, int]:
    return {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}


def _coerce_int(value: Any, default: int = 0) -> int:
    """Normalize numeric scanner fields without trusting their JSON type."""
    if isinstance(value, bool):
        return default
    try:
        number = int(value)
    except (TypeError, ValueError, OverflowError):
        return default
    return number if number >= 0 else default


def _location(value: Any) -> dict[str, Any]:
    """Return a scanner location object even when the payload is malformed."""
    return value if isinstance(value, dict) else {}


def _result(
    *,
    status: str,
    target: Path,
    findings: list[dict[str, Any]],
    scanner_statuses: dict[str, str],
    scanner_errors: dict[str, str],
    total_files: int,
    error_code: str | None = None,
) -> dict[str, Any]:
    breakdown = _severity_breakdown()
    for finding in findings:
        severity = str(finding.get("severity", "MEDIUM")).upper()
        if severity in breakdown:
            breakdown[severity] += 1
        else:
            breakdown["MEDIUM"] += 1

    succeeded = [name for name, state in scanner_statuses.items() if state == "success"]
    scanners_healthy = bool(succeeded) or (total_files == 0 and error_code is None)
    if error_code or status == "error":
        summary_status = "failed"
    elif total_files == 0:
        summary_status = "completed"
    elif all(state == "success" for state in scanner_statuses.values()):
        summary_status = "completed"
    elif scanners_healthy:
        summary_status = "completed_with_warnings"
    else:
        summary_status = "failed"

    summary: dict[str, Any] = {
        "total_files_scanned": total_files,
        "scanner_statuses": scanner_statuses,
        "scanner_errors": scanner_errors,
        "scanners_healthy": scanners_healthy,
        "status": summary_status,
    }
    if error_code:
        summary["error"] = error_code

    return {
        "status": status,
        "target_scanned": display_path(target),
        "total_findings": len(findings),
        "severity_breakdown": breakdown,
        "findings": findings,
        "summary": summary,
    }


def _error_result(target: Path, code: str) -> dict[str, Any]:
    return _result(
        status="error",
        target=target,
        findings=[],
        scanner_statuses={"bandit": "failed", "semgrep": "failed"},
        scanner_errors={"bandit": code, "semgrep": code},
        total_files=0,
        error_code=code,
    )


def _bandit_findings(
    payload: dict[str, Any], *, base: Path | None = None
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        return findings
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        raw_severity = str(item.get("issue_severity", "MEDIUM")).upper()
        severity = raw_severity if raw_severity in VALID_SEVERITIES else "MEDIUM"
        cwe = item.get("issue_cwe") or {}
        cwe_id = f"CWE-{cwe.get('id')}" if isinstance(cwe, dict) and cwe.get("id") else None
        line = _coerce_int(item.get("line_number"))
        line_range = item.get("line_range")
        if isinstance(line_range, list) and line_range:
            end_line = max(line, _coerce_int(line_range[-1], line))
        else:
            end_line = line
        findings.append(
            {
                "tool": "bandit",
                "scanner_name": "Bandit",
                "rule_id": item.get("test_id", "B000"),
                "category": item.get("test_name", "Security issue"),
                "title": item.get("test_name", "Security issue"),
                "severity": severity,
                "confidence": str(item.get("issue_confidence", "MEDIUM")).upper(),
                "file_path": display_path(
                    item.get("filename", ""), fallback_base=base
                ),
                "line": line,
                "start_line": line,
                "end_line": end_line,
                "message": item.get("issue_text", ""),
                "cwe_id": cwe_id,
                "owasp_mapping": None,
            }
        )
    return findings


def _semgrep_findings(
    payload: dict[str, Any], *, base: Path | None = None
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        return findings
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        extra = item.get("extra") or {}
        if not isinstance(extra, dict):
            extra = {}
        metadata = extra.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}

        raw_severity = str(extra.get("severity", "WARNING")).upper()
        severity = SEMGREP_SEVERITIES.get(raw_severity, "MEDIUM")
        message = str(extra.get("message", "Security finding"))
        start = _location(item.get("start"))
        end = _location(item.get("end"))
        start_line = _coerce_int(start.get("line"))
        end_line = max(start_line, _coerce_int(end.get("line"), start_line))

        cwe = metadata.get("cwe")
        if isinstance(cwe, list):
            cwe = cwe[0] if cwe else None
        owasp = metadata.get("owasp")
        if isinstance(owasp, list):
            owasp = owasp[0] if owasp else None

        findings.append(
            {
                "tool": "semgrep",
                "scanner_name": "Semgrep",
                "rule_id": item.get("check_id", "semgrep.rule"),
                "category": "Custom Semgrep rule",
                "title": message.splitlines()[0][:200],
                "severity": severity,
                "confidence": str(metadata.get("confidence", "MEDIUM")).upper(),
                "file_path": display_path(
                    item.get("path", ""), fallback_base=base
                ),
                "line": start_line,
                "start_line": start_line,
                "end_line": end_line,
                "message": message,
                "cwe_id": str(cwe) if cwe else None,
                "owasp_mapping": str(owasp) if owasp else None,
            }
        )
    return findings


def _deduplicate(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for finding in findings:
        key = (
            f"{finding.get('file_path')}:{finding.get('line')}:"
            f"{finding.get('rule_id')}"
        )
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = finding
            continue
        current_weight = SEVERITY_WEIGHTS.get(
            str(finding.get("severity", "MEDIUM")).upper(), 2
        )
        existing_weight = SEVERITY_WEIGHTS.get(
            str(existing.get("severity", "MEDIUM")).upper(), 2
        )
        if current_weight > existing_weight:
            deduped[key] = finding

    final = list(deduped.values())
    final.sort(
        key=lambda item: (
            -SEVERITY_WEIGHTS.get(str(item.get("severity", "MEDIUM")).upper(), 2),
            str(item.get("file_path", "")),
            _coerce_int(item.get("line")),
            str(item.get("rule_id", "")),
        )
    )
    return final


class ScanOrchestrator:
    """Run both scanners, normalise findings, and report scanner health."""

    def __init__(self, max_files: int | None = None) -> None:
        self.max_files = max_files

    def run_scan(self, target_dir: Path) -> dict[str, Any]:
        try:
            resolved_path = Path(target_dir).resolve()
        except (OSError, RuntimeError, ValueError):
            logger.exception("Unable to resolve scan target")
            return _error_result(Path(str(target_dir)), "invalid_target")
        if not resolved_path.exists() or not resolved_path.is_dir():
            return _error_result(resolved_path, "invalid_target")

        if resolved_path.is_relative_to(PROJECT_ROOT) and is_excluded_target(
            PROJECT_ROOT, resolved_path
        ):
            return _error_result(resolved_path, "excluded_target")

        try:
            python_files = collect_python_files(resolved_path, self.max_files)
        except ScannerError as exc:
            logger.warning("Scan target rejected: %s", exc.code)
            return _error_result(resolved_path, exc.code)
        except (OSError, ValueError):
            logger.exception("Unable to enumerate scan target")
            return _error_result(resolved_path, "target_unreadable")

        if not python_files:
            return _result(
                status="success",
                target=resolved_path,
                findings=[],
                scanner_statuses={"bandit": "skipped", "semgrep": "skipped"},
                scanner_errors={},
                total_files=0,
            )

        findings: list[dict[str, Any]] = []
        scanner_statuses = {"bandit": "failed", "semgrep": "failed"}
        scanner_errors: dict[str, str] = {}
        file_arguments = [str(path) for path in python_files]

        # Bandit is invoked with explicit files so virtual environments and
        # caches cannot silently inflate the scan target.
        try:
            bandit_result = run_json_command(
                [
                    sys.executable,
                    "-m",
                    "bandit",
                    "-f",
                    "json",
                    "-q",
                    "-ll",
                    *file_arguments,
                ],
                timeout=BANDIT_TIMEOUT_SECONDS,
            )
            if bandit_result.returncode not in (0, 1):
                raise ScannerError("bandit_failed", bandit_result.stderr)
            if bandit_result.payload.get("errors"):
                raise ScannerError("bandit_parse_errors", "Bandit reported file errors")
            findings.extend(_bandit_findings(bandit_result.payload, base=resolved_path))
            scanner_statuses["bandit"] = "success"
        except ScannerError as exc:
            logger.warning("Bandit scan failed: %s (%s)", exc.code, exc.detail)
            scanner_errors["bandit"] = exc.code
        except Exception:
            logger.exception("Unexpected Bandit scanner failure")
            scanner_errors["bandit"] = "unexpected_error"

        # Semgrep uses the repository's maintained local rules. It never falls
        # back to "auto": auto configuration requires metrics and is forbidden
        # in this project.
        try:
            rules_path = semgrep_rules_path()
            semgrep_result = run_json_command(
                [
                    *semgrep_command_prefix(),
                    "scan",
                    "--config",
                    str(rules_path),
                    "--json",
                    "--metrics=off",
                    "--error",
                    "--strict",
                    "--disable-version-check",
                    "--no-rewrite-rule-ids",
                    *file_arguments,
                ],
                timeout=SEMGREP_TIMEOUT_SECONDS,
            )
            if semgrep_result.returncode not in (0, 1):
                raise ScannerError("semgrep_failed", semgrep_result.stderr)
            if semgrep_result.payload.get("errors"):
                raise ScannerError("semgrep_errors", "Semgrep reported analysis errors")
            findings.extend(_semgrep_findings(semgrep_result.payload, base=resolved_path))
            scanner_statuses["semgrep"] = "success"
        except ScannerError as exc:
            logger.warning("Semgrep scan failed: %s (%s)", exc.code, exc.detail)
            scanner_errors["semgrep"] = exc.code
        except Exception:
            logger.exception("Unexpected Semgrep scanner failure")
            scanner_errors["semgrep"] = "unexpected_error"

        final_findings = _deduplicate(findings)

        if all(state == "success" for state in scanner_statuses.values()):
            overall_status = "success"
        elif any(state == "success" for state in scanner_statuses.values()):
            overall_status = "partial"
        else:
            overall_status = "error"

        return _result(
            status=overall_status,
            target=resolved_path,
            findings=final_findings,
            scanner_statuses=scanner_statuses,
            scanner_errors=scanner_errors,
            total_files=len(python_files),
            error_code="all_scanners_failed" if overall_status == "error" else None,
        )
