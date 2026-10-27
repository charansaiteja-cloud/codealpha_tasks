#!/usr/bin/env bash
# Run the local verification gate and write evidence to reports/evidence/.
# Expected findings in the intentionally vulnerable fixture are asserted, not
# treated as gate failures.
set -uo pipefail

cd "$(dirname "$0")/.."
mkdir -p reports/evidence

if [ -n "${PYTHON:-}" ]; then
  :
elif [ -x .venv/bin/python ]; then
  PYTHON=.venv/bin/python
else
  PYTHON=python3
fi

OVERALL=0

record() {
  local name="$1"
  shift
  "$@" >"reports/evidence/$name.txt" 2>&1
  local rc=$?
  cat "reports/evidence/$name.txt"
  echo "$rc" >"reports/evidence/$name.exitcode"
  echo "$name exit code: $rc"
  if [ "$rc" -ne 0 ]; then
    OVERALL=1
  fi
  return 0
}

record pytest "$PYTHON" -m pytest -q
record compile "$PYTHON" -m compileall -q app tests benchmarks vulnerable_samples
record pip-check "$PYTHON" -m pip check

if "$PYTHON" -m bandit --version >/dev/null 2>&1; then
  record bandit-corrected "$PYTHON" -m bandit -r app -ll

  "$PYTHON" -m bandit -r vulnerable_samples -f json -q \
    >reports/evidence/bandit-vulnerable.json 2>reports/evidence/bandit-vulnerable.err
  bandit_fixture_rc=$?
  if [ "$bandit_fixture_rc" -ne 1 ]; then
    echo "Expected Bandit fixture findings (exit 1), got exit $bandit_fixture_rc"
    OVERALL=1
  fi
  if ! "$PYTHON" - <<'PY'
import json
from pathlib import Path

path = Path("reports/evidence/bandit-vulnerable.json")
data = json.loads(path.read_text(encoding="utf-8"))
rule_ids = {item.get("test_id") for item in data.get("results", [])}
expected = {"B301", "B307", "B501", "B602", "B608"}
missing = expected - rule_ids
if missing:
    raise SystemExit(f"Bandit missed fixture rules: {sorted(missing)}")
print(f"Bandit fixture rules detected: {sorted(rule_ids)}")
PY
  then
    OVERALL=1
  fi
else
  echo "Bandit is not installed; skipping Bandit checks"
  OVERALL=1
fi

SEMGREP=()
if [ -x .venv/bin/semgrep ]; then
  SEMGREP=(.venv/bin/semgrep)
elif [ -x .semgrep-venv/bin/semgrep ]; then
  SEMGREP=(.semgrep-venv/bin/semgrep)
elif command -v semgrep >/dev/null 2>&1; then
  SEMGREP=(semgrep)
fi

if [ "${#SEMGREP[@]}" -gt 0 ]; then
  record semgrep-config "${SEMGREP[@]}" scan --validate --config .semgrep/rules.yml
  record semgrep-corrected "${SEMGREP[@]}" scan \
    --config .semgrep/rules.yml \
    --metrics=off \
    --error \
    --strict \
    --disable-version-check \
    --no-rewrite-rule-ids \
    app

  record semgrep-python-registry "${SEMGREP[@]}" scan \
    --config p/python \
    --metrics=off \
    --error \
    --strict \
    --disable-version-check \
    app

  "${SEMGREP[@]}" scan \
    --config .semgrep/rules.yml \
    --json \
    --metrics=off \
    --error \
    --strict \
    --disable-version-check \
    --no-rewrite-rule-ids \
    vulnerable_samples \
    >reports/evidence/semgrep-vulnerable.json 2>reports/evidence/semgrep-vulnerable.err
  semgrep_fixture_rc=$?
  if [ "$semgrep_fixture_rc" -ne 1 ]; then
    echo "Expected Semgrep fixture findings (exit 1), got exit $semgrep_fixture_rc"
    OVERALL=1
  fi
  if ! "$PYTHON" - <<'PY'
import json
from pathlib import Path

path = Path("reports/evidence/semgrep-vulnerable.json")
data = json.loads(path.read_text(encoding="utf-8"))
rule_ids = {item.get("check_id") for item in data.get("results", [])}
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
missing = expected - rule_ids
if missing:
    raise SystemExit(f"Semgrep missed fixture rules: {sorted(missing)}")
print(f"Semgrep fixture rules detected: {sorted(rule_ids)}")
PY
  then
    OVERALL=1
  fi
else
  echo "Semgrep is not installed; skipping Semgrep checks"
  OVERALL=1
fi

if "$PYTHON" -m pip_audit --version >/dev/null 2>&1; then
  record pip-audit "$PYTHON" -m pip_audit --strict -r requirements-dev.txt
else
  echo "pip-audit is not installed; skipping dependency audit"
  OVERALL=1
fi

if [ "$OVERALL" -ne 0 ]; then
  echo "Verification failed"
  exit 1
fi

echo "All verification checks passed"
