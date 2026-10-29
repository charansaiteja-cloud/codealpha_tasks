# 🛡️ CodeAlpha Secure Code Review

A Python secure-coding lab that compares intentionally vulnerable examples with a corrected FastAPI application and validates the result with tests, Bandit, Semgrep, and dependency auditing.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white) ![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white) ![Security](https://img.shields.io/badge/Focus-Application%20Security-red) ![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

Author: Bejjam Charan Sai Teja
Project: CodeAlpha Cybersecurity Internship — Secure Code Review
Repository: [CodeAlpha_SecureCodeReview](https://github.com/charansaiteja-cloud/CodeAlpha_SecureCodeReview)

## Overview

The repository separates three kinds of code:

- `app/` — the corrected application and scanner integration. This is the blocking production target.
- `vulnerable_samples/` — intentionally insecure examples used for education and detection tests. Never deploy or execute these functions with untrusted input.
- `benchmarks/` — a vulnerable/safe pair used to verify that both scanners detect real issues and do not flag the safe implementation.

The application stores items in SQLite, requires an API key for protected routes, validates input, uses parameterized SQL, and returns defensive HTTP security headers. It can also run Bandit and Semgrep against a directory inside a configured scan root.

> **Scope:** this is an educational lab, not a production service. Do not expose it to the internet or point `LAB_SCAN_ROOT` at sensitive data.

## Objectives

- Demonstrate common application security weaknesses and their remediations.
- Show the difference between intentionally vulnerable code and corrected code.
- Verify the application with regression tests, not only with source review.
- Make security-scanner failures and findings visible in local checks and CI.
- Document residual risk instead of treating a clean scan as proof of security.

## Key Features

| Feature | Description |
| --- | --- |
| API-key authentication | Protected routes require `X-API-Key`; the application fails closed when `LAB_API_KEY` is unset. |
| Constant-time key comparison | Uses `hmac.compare_digest` over UTF-8 bytes. |
| Parameterized SQL | Item creation and lookup use bound parameters. |
| Literal search matching | SQL `LIKE` wildcards in the search term are escaped and treated as text. |
| Input validation | Item names are 1–64 characters, non-blank, and free of control characters. |
| Security headers | Strict API CSP, HSTS, frame denial, `no-store`, permissions policy, COOP/CORP, and related headers. |
| Optional API docs | Swagger/OpenAPI is disabled by default and can be enabled explicitly for local use. |
| Scanner API | Runs Bandit and the maintained local Semgrep rules against a contained directory. |
| Scanner health reporting | Distinguishes success, partial completion, and scanner failure instead of returning an empty result as success. |
| CI security gate | Tests on Python 3.11/3.12 plus Ruff, Bandit, coverage, and an SBOM artifact. |
| Container hardening | Non-root user, read-only root filesystem in Compose, dropped capabilities, and required API key. |

## Repository Layout

```text
CodeAlpha_SecureCodeReview/
├── app/
│   ├── main.py                    # FastAPI routes, authentication, validation, scan endpoint
│   ├── middleware.py              # HTTP security headers
│   ├── models/                    # Normalized finding model
│   ├── scanner/                   # Bandit/Semgrep orchestration, rules, and shared helpers
│   └── services/                  # JSON and SARIF report generation utilities
├── benchmarks/
│   ├── vulnerable_sample.py       # Deliberately vulnerable scanner target
│   └── safe_sample.py             # Secure counterpart used for false-positive checks
├── vulnerable_samples/            # Intentionally insecure educational examples
├── tests/                         # Application, scanner, rule, benchmark, and report tests
├── .semgrep/rules.yml             # Maintained local Semgrep rules
├── .github/workflows/ci.yml       # Consolidated test and security workflow
├── docs/                          # Architecture and security policy
├── scripts/verify.sh              # Local verification gate and evidence generation
├── Dockerfile
├── docker-compose.yml
├── requirements.txt               # Runtime dependencies
├── requirements-dev.txt           # Runtime plus test and audit dependencies
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11 or newer (CI tests 3.11 and 3.12; the container uses 3.11).
- Git.
- A shell on Linux/macOS, or PowerShell/Command Prompt on Windows.
- Network access for the first dependency installation.

### Linux / macOS

```bash
git clone https://github.com/charansaiteja-cloud/CodeAlpha_SecureCodeReview.git
cd CodeAlpha_SecureCodeReview

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

export LAB_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export LAB_DB_PATH="$PWD/data/review.sqlite3"

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Windows PowerShell

```powershell
git clone https://github.com/charansaiteja-cloud/CodeAlpha_SecureCodeReview.git
cd CodeAlpha_SecureCodeReview

py -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

$env:LAB_API_KEY = python -c "import secrets; print(secrets.token_urlsafe(48))"
$env:LAB_DB_PATH = "$PWD\data\review.sqlite3"

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

If PowerShell blocks activation, run `.venv\Scripts\python.exe` directly or use `cmd.exe` with `.venv\Scripts\activate.bat`.

The default database location is `data/review.sqlite3`. The parent directory is created automatically.

### Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `LAB_API_KEY` | unset | Required for protected routes. If unset, every protected route returns 401. Use a long random value. |
| `LAB_DB_PATH` | `data/review.sqlite3` | SQLite database path. |
| `LAB_SCAN_ROOT` | project root | Root directory that `/api/v1/scan` may inspect. Resolved at startup. |
| `LAB_ENABLE_DOCS` | `false` | Enables `/docs`, `/redoc`, and `/openapi.json` when set to `1`, `true`, `yes`, or `on`. |
| `LAB_MAX_SCAN_FILES` | `2000` | Maximum number of Python files in one scan. Invalid or non-positive values fall back to the default. |

Copy `.env.example` to `.env` for a local template. Do not commit `.env` or real credentials. Docker Compose reads `LAB_API_KEY` from the environment and refuses to start without it.

## API Reference

| Method | Endpoint | Authentication | Purpose |
| --- | --- | --- | --- |
| `GET` | `/health` | No | Liveness check. Returns `{"status": "healthy"}`. |
| `GET` | `/api/v1/demo` | Yes | Lists user tables in the database. |
| `GET` | `/items` | Yes | Lists or searches items. Query parameter `q` is optional, max 64 characters. |
| `POST` | `/items` | Yes | Creates an item. Body: `{"name": "..."}`. |
| `GET` | `/items/{item_id}` | Yes | Returns one item; rejects non-positive IDs and returns 404 when absent. |
| `POST` | `/api/v1/scan` | Yes | Runs Bandit and Semgrep against a directory under `LAB_SCAN_ROOT`. |
| `GET` | `/docs`, `/redoc` | No | Available only when `LAB_ENABLE_DOCS=true`. |

Protected routes expect the header `X-API-Key: <value>`. Missing, wrong, oversized, or unconfigured keys produce 401. Item names must be 1–64 characters, contain at least one non-whitespace character, and contain no control characters. Search terms are limited to 64 characters.

### Examples

```bash
BASE=http://127.0.0.1:8000
KEY="$LAB_API_KEY"

curl "$BASE/health"

curl -H "X-API-Key: $KEY" "$BASE/api/v1/demo"

curl -X POST "$BASE/items" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $KEY" \
  -d '{"name":"Secure Coding Demo"}'

curl -G "$BASE/items" \
  -H "X-API-Key: $KEY" \
  --data-urlencode "q=Secure"

curl -H "X-API-Key: $KEY" "$BASE/items/1"
```

There is no seeded demo item; the database starts empty. A `%` or `_` in `q` is matched literally rather than as a SQL wildcard.

### Scan API

```bash
curl -X POST "$BASE/api/v1/scan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $KEY" \
  -d '{"target_path":"app"}'
```

`target_path` is relative to `LAB_SCAN_ROOT` (default `.`). It is resolved and rejected if it escapes the root, resolves through a symlink outside the root, or contains an excluded directory such as `.git`, `.venv`, `data`, `reports`, `build`, or `dist`. The scan collects regular Python files only, skips dot-directories and symlinked directories, caps the file count, and never accepts an absolute path from the client.

The response reports:

- `status`: `success` when both scanners complete, `partial` when one completes, `error` when both fail.
- `summary.scanner_statuses`: per-scanner state.
- `summary.scanner_errors`: stable error codes, not raw scanner output.
- `summary.status`: `completed`, `completed_with_warnings`, or `failed`.
- `findings` and `severity_breakdown`.

HTTP behavior:

- `400` — invalid or excluded target.
- `401` — missing or invalid API key.
- `422` — invalid request body.
- `429` — another scan is already running in this process.
- `503` — both scanners are unavailable.
- `500` — unexpected orchestration failure.

The semaphore is an in-process concurrency guard, not a distributed rate limiter. Run one process per container and keep the endpoint on a trusted network.

## Security Testing and CI

Run the local gate from the repository root:

```bash
bash scripts/verify.sh
```

The script writes output to `reports/evidence/` and fails if a corrected-code check fails or an expected vulnerable-fixture detection disappears. It does not treat fixture findings as application failures.

### Tests

```bash
python -m pytest -v
```

The suite covers health and security headers, authentication, fail-closed configuration, item validation, SQL metacharacters, literal `LIKE` wildcards, database path creation, scan-target containment, excluded directories, the busy-scan response, all-scanners-failed handling, custom-rule validity, vulnerable-fixture detection, the safe benchmark, and JSON/SARIF report generation.

### Bandit

```bash
python -m bandit -r app -ll
```

`-ll` blocks medium and higher severity findings in `app/`. The intentionally vulnerable fixtures are outside this target and are checked separately.

### Semgrep

Local maintained rules, blocking:

```bash
semgrep scan \
  --config .semgrep/rules.yml \
  --metrics=off \
  --error \
  --strict \
  --disable-version-check \
  --no-rewrite-rule-ids \
  app/
```

Broader Python registry rules, also blocking:

```bash
semgrep scan \
  --config p/python \
  --metrics=off \
  --error \
  --strict \
  --disable-version-check \
  app/
```

`--error` is required: without it, Semgrep exits 0 even when it reports findings. `--config auto` is intentionally not used. Auto configuration requires metrics, and this project keeps metrics disabled.

To inspect the deliberately vulnerable fixtures, scan them separately and expect a nonzero exit:

```bash
semgrep scan \
  --config .semgrep/rules.yml \
  --metrics=off \
  --error \
  --strict \
  --disable-version-check \
  vulnerable_samples
```

### Dependency checks

```bash
python -m pip check
python -m pip_audit --strict -r requirements-dev.txt
```

`requirements-dev.txt` includes the runtime requirements plus pytest, HTTPX, and pip-audit.

### Finding and failure policy

The blocking scope, severity thresholds, suppression rules, and triage process are defined in [`docs/security-policy.md`](docs/security-policy.md). In short:

- Findings in `app/` block the gate; test fixtures are not production scope.
- Scanner crashes, invalid JSON, missing rules, timeouts, and unexpected exit codes are failures, not clean results.
- Suppressions must be narrow and justified; blanket exclusions, disabled scanners, and `continue-on-error` are not used.
- A clean scan is evidence for the scanned revision and ruleset, not proof that the application is vulnerability-free.

### CI workflow

`.github/workflows/ci.yml` runs on pushes to `main`, pull requests targeting `main`, and manual dispatch. It uses read-only repository permissions, cancels superseded runs, pins third-party actions to commit SHAs, and contains two jobs:

1. **Tests** — Python 3.11 and 3.12, `pip check`, and pytest.
2. **Security and supply-chain checks** — Bandit, local Semgrep rule validation and scan, `p/python` Semgrep scan, and `pip-audit --strict`.

There is one workflow with this name; the former duplicate `security.yml` workflow was removed.

## Local Verification Results

Recorded on 2026-10-27 with Python 3.14.8, Bandit 1.9.4, Semgrep 1.79.0, and pip-audit in the local virtual environment:

| Check | Result |
| --- | --- |
| Pytest | `74 passed`, 82.8% branch coverage |
| Python compilation | `app`, `tests`, `benchmarks`, `vulnerable_samples` compiled successfully |
| `pip check` | No broken requirements |
| Bandit `app` | Exit 0; no findings |
| Local Semgrep rules on `app/` | 8 rules, 0 findings |
| `p/python` Semgrep rules on `app/` | 151 rules, 0 findings |
| Local Semgrep rules on `vulnerable_samples/` | All 8 fixture classes detected; expected nonzero exit |
| Bandit fixture scan | Expected findings detected; expected nonzero exit |
| `pip-audit --strict -r requirements-dev.txt` | No known vulnerabilities |

These are local results. A clean result does not guarantee that every code path, dependency, or deployment configuration is safe.

## Docker

The image installs runtime dependencies only, copies `app/` and `.semgrep/`, and runs as a non-root user. Compose additionally uses a read-only root filesystem, a writable data volume, a `/tmp` tmpfs, `no-new-privileges`, and dropped capabilities.

```bash
export LAB_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
docker compose up --build
```

Then test from the host:

```bash
curl http://127.0.0.1:8000/health
```

Compose publishes the port only on `127.0.0.1`. `LAB_ENABLE_DOCS` defaults to `false`; enable it only for local documentation if needed. The scan endpoint is privileged and expensive, so keep it off untrusted networks.

## Security Practices Demonstrated

- **Parameter binding** separates SQL syntax from data:

  ```python
  db.execute("SELECT id, name FROM items WHERE id = ?", (item_id,))
  ```

- **Literal search semantics** escape `%`, `_`, and the escape character before constructing a `LIKE` pattern.
- **API-key verification** uses constant-time comparison and fails closed when no key is configured.
- **Input constraints** reject blank names, oversized values, and control characters.
- **Defensive headers** include `Content-Security-Policy: default-src 'none'; ...`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Cache-Control: no-store`, HSTS, `Referrer-Policy: no-referrer`, `Permissions-Policy`, COOP/CORP, and `X-Permitted-Cross-Domain-Policies: none`.
- **Docs isolation** gives documentation paths a relaxed CSP only when documentation is enabled; API responses keep the strict policy.
- **Scanner containment** rejects traversal, symlink escape, excluded directories, and oversized targets.
- **Honest scanner status** does not report an empty finding list when both tools failed.

## Threat Model and Limitations

In scope: local application behavior, the scanner subprocess boundary, SQLite access, API-key handling, HTTP response headers, and the CI configuration.

Out of scope or not implemented: production identity management, per-user authorization, TLS termination, distributed rate limiting, durable audit logging, secrets management, OS-level sandboxing of scanner subprocesses, multi-tenant isolation, and incident response.

Additional limitations:

- Bandit and Semgrep are pattern-based tools; they can miss vulnerabilities and produce false positives.
- The scanner endpoint executes installed tools against files readable by the application user. The scan root, file cap, exclusions, timeouts, and API key reduce exposure but do not form a sandbox.
- A single semaphore slot bounds one process only.
- The API key is a shared secret, not a user identity or authorization model.
- The container hardening is a baseline, not a complete production deployment profile.
- Reports and evidence describe a specific revision and tool set.

## Troubleshooting

- **`semgrep: command not found`** — install `requirements-dev.txt` in the active environment, or use a dedicated scanner environment and call its `semgrep` executable.
- **`semgrep` exits 0 despite findings** — add `--error`; this project's commands already do.
- **`Cannot create auto config when metrics are off`** — do not combine `--config auto` with `SEMGREP_SEND_METRICS=off`; use an explicit rule file or `p/python`.
- **Protected routes return 401** — set `LAB_API_KEY` in the same environment that starts the server and send the exact value.
- **Scan returns 400** — use a relative directory under `LAB_SCAN_ROOT` that is not an excluded directory.
- **Scan returns 429** — wait for the current scan to finish; there is one in-process slot.
- **Scan returns 503** — check that Bandit and Semgrep are installed and working in the application environment.
- **Database cannot be opened** — ensure the database parent directory is writable by the process/container user.

## Future Improvements

- Add authenticated report export endpoints for the existing JSON/SARIF generators.
- Add structured audit logging and per-client rate limiting at a trusted reverse proxy.
- Add more languages and framework-specific Semgrep rules with fixture coverage.
- Add SBOM generation and signed container images.
- Improve remediation guidance for each custom rule.
- Run the consolidated workflow remotely and record the result before claiming CI success.

## 🎬 Project Demo

Watch the 56-second Secure Code Review demonstration.

- **Demo video:** [secure-code-review-demo.mp4](demo-video/secure-code-review-demo.mp4)
- **Demo documentation:** [Demo README](demo-video/README.md)
- **Security evidence:** [Demo evidence](demo-video/evidence/)

## Contributing

1. Fork the repository and create a feature branch.
2. Add or update tests for behavior changes.
3. Run `bash scripts/verify.sh`.
4. Open a pull request describing the change and the exact verification performed.

Only use the intentionally vulnerable examples in authorized, controlled educational environments.

## License

MIT. See [LICENSE](LICENSE).

## Author

Bejjam Charan Sai Teja
Cybersecurity enthusiast focused on secure coding, application security, vulnerability analysis, and security testing.

GitHub: [@charansaiteja-cloud](https://github.com/charansaiteja-cloud)
Repository: [CodeAlpha_SecureCodeReview](https://github.com/charansaiteja-cloud/CodeAlpha_SecureCodeReview)
