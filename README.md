# CodeAlpha Cybersecurity Internship — Project Bundle

Three completed cybersecurity tasks, kept together as a single reviewable
monorepo. Each task also has a standalone repository, linked below.

**Author:** Bejjam Charan Sai Teja

[![CI](https://github.com/charansaiteja-cloud/codealpha_tasks/actions/workflows/ci.yml/badge.svg)](https://github.com/charansaiteja-cloud/codealpha_tasks/actions/workflows/ci.yml)

---

## Projects

| Task | What it does | Verification | Standalone repository |
| --- | --- | --- | --- |
| **01 — Basic Network Sniffer** | Scapy packet capture with protocol decoding, metadata-first CSV export, ICMP payload preview, and BPF filtering. | 18 tests, Ruff clean | [CodeAlpha_BasicNetworkSniffer](https://github.com/charansaiteja-cloud/CodeAlpha_BasicNetworkSniffer) |
| **02 — Secure Code Review** | FastAPI reference app plus Bandit/Semgrep scan orchestration, defensive middleware, parameterised SQL, and security fixtures. | 74 tests, 82.8% branch coverage, Ruff and Bandit clean | [CodeAlpha_SecureCodeReview](https://github.com/charansaiteja-cloud/CodeAlpha_SecureCodeReview) |
| **03 — Phishing Awareness Training** | Streamlit training module with annotated phishing examples, an interactive quiz, scoring, and a completion flow. | 16 tests, 98.9% branch coverage, Ruff clean | [CodeAlpha_PhishingAwarenessTraining](https://github.com/charansaiteja-cloud/CodeAlpha_PhishingAwarenessTraining) |

Every project includes its own README, dependency files, tests, and CI
workflow. The copies here are kept in sync with the standalone repositories.

---

## Repository layout

```text
codealpha_tasks/
├── Task-1-Basic-Network-Sniffer/     # Scapy capture -> CSV
├── Task-2-Secure-Code-Review/        # FastAPI + Bandit + Semgrep
├── Phishing-Awareness-Training/      # Streamlit quiz and training
└── .github/workflows/ci.yml          # runs all three test suites
```

## Run a task locally

Each task is self-contained. For example:

```bash
# Task 1 — metadata-only packet capture
cd Task-1-Basic-Network-Sniffer
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python sniffer.py --list-interfaces
python sniffer.py -i lo -c 20 --bpf "icmp or arp"

# Task 2 — secure code review service
cd ../Task-2-Secure-Code-Review
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest

# Task 3 — phishing awareness training
cd ../Phishing-Awareness-Training
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Live packet capture needs `CAP_NET_RAW` (or root). Prefer a BPF filter and a
small `--count` while testing. Use these tools only on networks you own or have
written permission to monitor.

## Quality checks

The root workflow runs each task independently:

```bash
# Task 1
cd Task-1-Basic-Network-Sniffer
ruff check sniffer.py tests && ruff format --check sniffer.py tests
python -m pytest

# Task 2
cd ../Task-2-Secure-Code-Review
ruff check app tests && ruff format --check app tests
python -m pytest

# Task 3
cd ../Phishing-Awareness-Training
ruff check app.py quiz.py tests && ruff format --check app.py quiz.py tests
python -m pytest
```

## Scope and limitations

- The sniffer records packet metadata, not full payloads. Optional ICMP previews
  are capped at 16 bytes.
- The secure-code-review app is a teaching reference. Its `vulnerable_samples/`
  directory is intentionally insecure and must never be deployed.
- The phishing module uses fictional examples for training; it does not send
  email or collect credentials.
- These are internship projects, not production security products. Read each
  task README for its specific limitations.

## License

MIT — see [LICENSE](LICENSE). Each task directory also carries its own copy.
