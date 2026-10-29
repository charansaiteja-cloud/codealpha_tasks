import re

def check_insecure_pickle(file_content: str, filename: str):
    findings = []
    if "pickle.loads" in file_content or "pickle.load" in file_content:
        findings.append({
            "rule_id": "CUSTOM-001",
            "severity": "HIGH",
            "message": "Insecure deserialization detected using Python 'pickle'.",
            "file": filename
        })
    return findings

def check_hardcoded_jwt_secret(file_content: str, filename: str):
    findings = []
    pattern = re.compile(r"jwt_secret\s*=\s*['\"].{4,}[\"']", re.IGNORECASE)
    if pattern.search(file_content):
        findings.append({
            "rule_id": "CUSTOM-002",
            "severity": "CRITICAL",
            "message": "Hardcoded JWT secret detected in source code.",
            "file": filename
        })
    return findings
