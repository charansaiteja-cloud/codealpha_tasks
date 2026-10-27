# Security Finding and Failure Policy

This document defines how security results are produced, interpreted, and enforced in this repository. It applies to local verification and to `.github/workflows/ci.yml`.

## 1. Scope

| Path | Role | Blocking in CI |
| --- | --- | --- |
| `app/` | Corrected application and scanner integration | Yes |
| `tests/` | Regression and detection tests | Test failures block; scanners are not run directly against test files |
| `benchmarks/` | Deliberately vulnerable/safe scanner verification | Exercised by tests |
| `vulnerable_samples/` | Intentionally insecure educational examples | No; expected findings are asserted separately |
| `.semgrep/rules.yml` | Maintained local detection rules | Rule validation and the `app/` scan block |

The production security target is `app/`. Scanning the whole repository would mix intentionally vulnerable fixtures into the application result and make the gate meaningless. Fixtures are still covered: tests assert that the maintained rules and Bandit detect the insecure examples and stay quiet on the safe benchmark.

## 2. Enforcement

### Tests

`python -m pytest -v` must pass on Python 3.11 and 3.12 in CI, and on the supported local interpreter. A test that cannot run is not a pass.

### Bandit

```bash
python -m bandit -r app -ll
```

`-ll` reports medium and higher severity. Any nonzero Bandit exit fails the gate. Bandit findings below the threshold are not treated as a security pass; they are outside the configured policy and may be reviewed separately.

### Semgrep

Both commands are blocking:

```bash
semgrep scan --config .semgrep/rules.yml --metrics=off --error --strict \
  --disable-version-check --no-rewrite-rule-ids app/
semgrep scan --config p/python --metrics=off --error --strict \
  --disable-version-check app/
```

- `--error` makes findings produce a nonzero exit. Semgrep's default exit code is 0 when findings exist.
- `--strict` turns scanner errors into failures.
- `--metrics=off` keeps telemetry disabled. `--config auto` is forbidden because Semgrep refuses to create auto configuration with metrics off.
- Any finding in `app/` blocks, regardless of severity. The maintained rules use ERROR for exploitable classes and WARNING for insecure temporary-file creation; both are actionable.
- `--config p/python` adds community rules. A finding from either ruleset must be triaged; it cannot be ignored merely because the other ruleset is clean.

### Dependencies

`python -m pip check` must succeed. `python -m pip_audit --strict -r requirements-dev.txt` must report no known vulnerabilities. An audit failure is a failure; a missing or broken audit tool is also a failure.

## 3. Failure Handling

The following are **failures**, not clean results:

- Scanner executable missing, not permitted, or timing out.
- Empty, truncated, non-JSON, or unexpected scanner output.
- Semgrep internal/parse errors or an invalid rule file.
- Bandit file errors or an unexpected exit code.
- A scan target that is unreadable, too large, outside the allowed root, or excluded.
- A pipeline step that is skipped because a previous step failed silently.
- `continue-on-error`, `|| true`, `--exit-zero`, disabled jobs, empty rule files, or fake/stub results.

The scan API reports stable error codes and distinguishes `success`, `partial`, and `error`. It returns 503 when both scanners fail so that callers cannot mistake an unavailable scanner for a clean application.

## 4. Triage and Suppression

1. Reproduce the finding with the exact tool, version, rule, and revision.
2. Determine whether the code path is reachable with attacker-controlled input.
3. Fix the code or narrow the rule. Prefer a code fix.
4. If a finding is a verified false positive, add the narrowest possible suppression at the specific line, include the rule ID and a written justification, and add a regression test or documented review note.
5. Never suppress a whole file, directory, ruleset, or scanner to make a gate pass.
6. Re-run the full verification gate after any suppression.

A suppression is an accepted risk with an owner and rationale, not a finding that disappeared.

## 5. Rule Maintenance

- Local rules live in `.semgrep/rules.yml` and must pass `semgrep scan --validate`.
- Rule IDs are stable and prefixed `codealpha.python.`.
- Each rule declares a message, severity, language, CWE, OWASP mapping, and references.
- Adding or changing a rule requires fixture coverage: a positive example and, where practical, a safe counterpart.
- Removing a rule requires a documented reason and review of the findings it previously covered.

## 6. CI Supply Chain and Permissions

- The workflow uses `permissions: contents: read`.
- Checkout does not persist credentials.
- Third-party actions are pinned to full commit SHAs with version comments.
- Workflow runs for the same ref are serialized/cancelled to avoid stale duplicate results.
- Secrets are not required for the CI security jobs. The application API key is a runtime setting, not a CI secret.
- Unauthenticated pull requests must not receive repository secrets. The workflow does not use `pull_request_target`.
- Pinned action SHAs must be reviewed when updated.

## 7. Evidence and Reporting

Verification evidence is generated under `reports/evidence/` by `scripts/verify.sh`. Evidence is tied to a revision, date, tool versions, and command. It must not be edited to imply a different result.

A report should state:

- What was scanned and what was excluded.
- Exact commands and tool versions.
- Findings, triage decisions, and residual risk.
- Which checks actually ran, which failed, and which did not run.
- That a clean result is not proof of absence of vulnerabilities.

## 8. Review Cadence

- Every pull request: tests, Bandit, local Semgrep, `p/python`, `pip check`, and `pip-audit`.
- Dependency changes: re-run the audit and review transitive changes.
- Rule changes: validate and run fixture tests.
- Before a release or submission: run `scripts/verify.sh` and record the exact revision.
- Periodically review the policy itself, pinned actions, scanner versions, and the threat model.

## 9. Out of Scope

This policy does not provide production incident response, vulnerability disclosure handling, identity and access management review, infrastructure penetration testing, or assurance that third-party scanner rules are complete. See the threat model and limitations in the [README](../README.md) and [architecture](architecture.md).
