import json
from typing import Any

_SECURITY_SEVERITY = {
    "CRITICAL": "9.5",
    "HIGH": "8.0",
    "MEDIUM": "5.5",
    "LOW": "2.0",
    "INFORMATIONAL": "0.0",
}


def _line_number(value: Any, default: int = 1) -> int:
    try:
        line = int(value)
    except (TypeError, ValueError, OverflowError):
        return default
    return line if line > 0 else default


class ReportService:
    @staticmethod
    def generate_json_report(scan_results: dict[str, Any]) -> str:
        return json.dumps(scan_results, indent=2)

    @staticmethod
    def generate_sarif_report(scan_results: dict[str, Any]) -> dict[str, Any]:
        """
        Converts normalized scan findings into SARIF v2.1.0 format
        compatible with GitHub Code Scanning.
        """
        findings = scan_results.get("findings", [])
        rules_dict = {}
        results = []

        for f in findings:
            rule_id = f.get("rule_id", "UNKNOWN")
            severity = str(f.get("severity", "MEDIUM")).upper()
            start_line = _line_number(f.get("start_line"))
            end_line = max(start_line, _line_number(f.get("end_line"), start_line))
            if rule_id not in rules_dict:
                rules_dict[rule_id] = {
                    "id": rule_id,
                    "name": f.get("title", rule_id),
                    "shortDescription": {"text": f.get("title", "")},
                    "fullDescription": {"text": f.get("description", "")},
                    "help": {"text": f.get("remediation", "")},
                    "properties": {
                        "security-severity": _SECURITY_SEVERITY.get(
                            severity, _SECURITY_SEVERITY["MEDIUM"]
                        )
                    },
                }

            results.append(
                {
                    "ruleId": rule_id,
                    "message": {"text": f.get("description", "")},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": f.get("file_path", "")},
                                "region": {
                                    "startLine": start_line,
                                    "endLine": end_line,
                                },
                            }
                        }
                    ],
                }
            )

        sarif_report = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "CodeAlpha SecureCodeReview",
                            "version": "2.1.0",
                            "rules": list(rules_dict.values()),
                        }
                    },
                    "results": results,
                }
            ],
        }
        return sarif_report
