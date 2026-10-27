import json
import os
import subprocess

import yaml

from app.scanner.common import (
    PROJECT_ROOT,
    SEMGREP_RULES_PATH,
    semgrep_command_prefix,
)


def _run_semgrep(target: str) -> tuple[int, dict]:
    command = [
        *semgrep_command_prefix(),
        "scan",
        "--config",
        str(SEMGREP_RULES_PATH),
        "--json",
        "--metrics=off",
        "--error",
        "--strict",
        "--disable-version-check",
        "--no-rewrite-rule-ids",
        target,
    ]
    environment = os.environ.copy()
    environment["SEMGREP_SEND_METRICS"] = "off"
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        env=environment,
    )
    assert completed.returncode in (0, 1), completed.stderr
    return completed.returncode, json.loads(completed.stdout)


def test_local_semgrep_rules_are_valid_and_complete():
    rules_document = yaml.safe_load(SEMGREP_RULES_PATH.read_text(encoding="utf-8"))
    rules = rules_document["rules"]
    assert len(rules) >= 8

    identifiers = [rule["id"] for rule in rules]
    assert len(identifiers) == len(set(identifiers))
    for rule in rules:
        assert rule["id"]
        assert rule["message"]
        assert rule["severity"] in {"ERROR", "WARNING", "INFO"}
        assert rule["languages"]
        assert rule.get("pattern") or rule.get("patterns") or rule.get(
            "pattern-either"
        ) or rule.get("pattern-regex")


def test_custom_rules_detect_all_vulnerable_fixture_classes():
    returncode, payload = _run_semgrep("vulnerable_samples")
    assert payload["errors"] == []
    assert returncode == 1, "Semgrep --error must fail when fixture findings exist"

    rule_ids = {result["check_id"] for result in payload["results"]}
    expected = {
        "codealpha.python.sql-string-construction",
        "codealpha.python.subprocess-shell-true",
        "codealpha.python.pickle-deserialization",
        "codealpha.python.dynamic-code-execution",
        "codealpha.python.unsafe-yaml-load",
        "codealpha.python.disabled-tls-verification",
        "codealpha.python.insecure-tempfile",
        "codealpha.python.hardcoded-secret",
    }
    assert expected <= rule_ids


def test_custom_rules_do_not_find_issues_in_application_code():
    returncode, payload = _run_semgrep("app")
    assert payload["errors"] == []
    assert payload["results"] == []
    assert returncode == 0


def test_custom_rules_do_not_flag_safe_loader_and_tls_variants(tmp_path):
    safe_fixture = tmp_path / "safe_variants.py"
    safe_fixture.write_text(
        """\
import os
import subprocess
import tempfile

import httpx
import requests
import yaml


def safe_yaml_safe(data):
    return yaml.load(data, Loader=yaml.SafeLoader)


def safe_yaml_csafe(data):
    return yaml.load(data, Loader=yaml.CSafeLoader)


def safe_yaml_base(data):
    return yaml.load(data, Loader=yaml.BaseLoader)


def safe_yaml_cloader(data):
    return yaml.load(data, Loader=yaml.CLoader)


def safe_process(argv):
    return subprocess.run(argv, shell=False, check=False)


def safe_requests(url):
    return requests.get(url, verify=True, timeout=2)


def safe_httpx(url):
    return httpx.get(url, verify=True, timeout=2)


def safe_tempfile():
    with tempfile.NamedTemporaryFile(delete=False) as handle:
        return handle.name


API_KEY = os.environ.get("API_KEY")
""",
        encoding="utf-8",
    )

    returncode, payload = _run_semgrep(str(safe_fixture))
    assert payload["errors"] == []
    assert payload["results"] == []
    assert returncode == 0
