from pathlib import Path

from app.scanner.orchestrator import ScanOrchestrator


def test_benchmark_detection_rate():
    """Both scanners must detect real vulnerable code and ignore the safe sample."""
    benchmarks_dir = Path("benchmarks").resolve()
    assert benchmarks_dir.is_dir(), "Benchmarks directory must exist."

    results = ScanOrchestrator().run_scan(benchmarks_dir)
    findings = results.get("findings", [])

    assert results["status"] == "success"
    assert results["summary"]["scanner_statuses"] == {
        "bandit": "success",
        "semgrep": "success",
    }
    assert results["summary"]["total_files_scanned"] == 2
    assert findings, "Benchmark failed: expected findings in the vulnerable sample."

    finding_names = {Path(f["file_path"]).name for f in findings}
    assert "vulnerable_sample.py" in finding_names
    assert "safe_sample.py" not in finding_names, (
        "Safe sample produced security findings: "
        f"{[f for f in findings if Path(f['file_path']).name == 'safe_sample.py']}"
    )

    rule_ids = {f["rule_id"] for f in findings}
    assert "B102" in rule_ids, "Bandit failed to detect exec()."
    assert "B605" in rule_ids, "Bandit failed to detect os.system()."
    assert "codealpha.python.dynamic-code-execution" in rule_ids
    assert "codealpha.python.subprocess-shell-true" in rule_ids
    print(f"Benchmark detected rule IDs: {sorted(rule_ids)}")
