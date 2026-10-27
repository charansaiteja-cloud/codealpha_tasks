import json

from app.services.report_service import ReportService


def test_json_report_round_trip():
    scan_results = {"status": "success", "findings": []}
    encoded = ReportService.generate_json_report(scan_results)
    assert json.loads(encoded) == scan_results


def test_sarif_report_contains_github_code_scanning_fields():
    scan_results = {
        "findings": [
            {
                "rule_id": "B602",
                "title": "subprocess shell",
                "description": "shell=True",
                "remediation": "Use an argument list.",
                "severity": "HIGH",
                "file_path": "app/example.py",
                "start_line": 10,
                "end_line": 12,
            }
        ]
    }

    sarif = ReportService.generate_sarif_report(scan_results)
    assert sarif["version"] == "2.1.0"
    assert sarif["$schema"].endswith("sarif-schema-2.1.0.json")

    run = sarif["runs"][0]
    assert run["tool"]["driver"]["name"] == "CodeAlpha SecureCodeReview"
    assert run["tool"]["driver"]["rules"][0]["id"] == "B602"
    assert run["results"][0]["ruleId"] == "B602"
    location = run["results"][0]["locations"][0]["physicalLocation"]
    assert location["artifactLocation"]["uri"] == "app/example.py"
    assert location["region"] == {"startLine": 10, "endLine": 12}


def test_sarif_security_severity_reflects_finding_severity():
    findings = [
        {
            "rule_id": rule_id,
            "title": rule_id,
            "description": rule_id,
            "remediation": "fix",
            "severity": severity,
            "file_path": f"app/{rule_id}.py",
            "start_line": 0,
            "end_line": 0,
        }
        for rule_id, severity in (
            ("CRITICAL_RULE", "CRITICAL"),
            ("HIGH_RULE", "HIGH"),
            ("MEDIUM_RULE", "MEDIUM"),
            ("LOW_RULE", "LOW"),
        )
    ]

    sarif = ReportService.generate_sarif_report({"findings": findings})
    rules = {
        rule["id"]: rule["properties"]["security-severity"]
        for rule in sarif["runs"][0]["tool"]["driver"]["rules"]
    }
    assert rules == {
        "CRITICAL_RULE": "9.5",
        "HIGH_RULE": "8.0",
        "MEDIUM_RULE": "5.5",
        "LOW_RULE": "2.0",
    }
    for result in sarif["runs"][0]["results"]:
        region = result["locations"][0]["physicalLocation"]["region"]
        assert region["startLine"] == 1
        assert region["endLine"] == 1
