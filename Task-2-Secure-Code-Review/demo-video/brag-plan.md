# Brag Plan: CodeAlpha Secure Code Review

## What is this app?

A Python/FastAPI secure-coding lab that sends a contained directory through Bandit and maintained Semgrep rules, normalizes both scanners into one severity schema, reports scanner health honestly, and proves the behavior with 64 regression tests.

## The angle

**Evidence over adjectives.** The video is a quiet, technical walkthrough for reviewers who distrust launch videos. The hook is the uncomfortable gap between code that looks correct and code that is actually risky. Every claim after that is tied to a real local run: a fixture scan with 15 normalized findings, a hardened `app/` scan with 0 findings, a 401 for a missing key, a 400 for a traversal attempt, and 64 passing tests. No fake dashboard, no invented customer, no "10x" number.

## Hook (first 2-3 seconds)

A real excerpt from `vulnerable_samples/insecure_examples.py` sits in a code panel, with `shell=True` lit up. On the left, the line lands: **"CORRECT-LOOKING CODE. REAL SECURITY RISK."** The dot after "CODE" is the only warm punctuation; everything else is cool and controlled.

## Key moments (the middle)

- **One API, two scanners, contained by design** — a five-stage path from `Client` to `JSON`, with three live-verification cards underneath: fail-closed auth (`401`), relative-path containment (`400`), and honest per-scanner status.
- **A real scan, not a mock-up** — the actual `curl` request and a trim of the returned JSON beside a 15-finding panel (9 HIGH, 6 MEDIUM) and a 0-finding panel for 13 hardened app files.
- **The security claims have tests** — 64 lit test cells, `64 passed in 6.92s` in a terminal, and six cards that name the behavior each test group protects.
- **Outro** — the public repository, the author, the stack, and the honest footer: demo results recorded 27 Oct 2026.

## Outro / punchline

**"Secure Code Review. Scan. Normalize. Verify."** The repository URL is the call to action, not a logo. The final note stays deliberately unvictorious: a clean scan is evidence for one revision and ruleset, not proof that software is vulnerability-free.

## User flow worth showing

`POST /api/v1/scan` with `{"target_path": "vulnerable_samples"}` → Bandit + Semgrep execute under the scan root → findings are normalized into one schema → JSON returns 15 findings and `scanner_statuses` for both tools. The architecture and live-scan scenes carry this flow; the tests scene shows the guardrails around it.

## Tone

- **Preset:** `polished`
- **Creative direction:** "A security engineer's evidence reel — calm, exact, quietly confident."
- **Interpretation:** Longer holds than a startup ad, restrained motion, no hype language, and enough empty space that each number can be read. The tension comes from the code and the counts, not from the edit.

## Format: landscape — 1920x1080

## Duration: 56 seconds

> **Deliberate deviation:** Brag's default 15–25s window was extended because the brief explicitly asked for a 45–60s internship demo. The story still follows Brag's Hook → Reveal → highlights → outro shape; the extra time is used for readable evidence, not filler.

## Visual identity (from the project)

- **Background:** `#04070D` black / `#071421` navy
- **Accent:** `#22D3EE` cyan
- **Text:** `#E8F4FF`
- **Support:** `#4ADE80` green (verified/pass), `#FF5D6C` red (risk), `#FBBF24` amber (medium)
- **Display font:** Space Grotesk
- **Body/mono font:** JetBrains Mono
- **Strongest visual element:** the real code panel with a highlighted dangerous line, paired with the normalized-finding table. These are the product's actual artifacts, not decorative UI.

## Share copy (draft)

> I built a secure code review lab for my CodeAlpha internship: one authenticated FastAPI endpoint, Bandit + Semgrep, one normalized severity model, and 64 tests. This 56-second demo shows the real scan results — including the 15 findings in the vulnerable fixture and the 0 findings in the hardened app.
>
> Code: https://github.com/charansaiteja-cloud/CodeAlpha_SecureCodeReview
>
> #CodeAlpha #Cybersecurity #AppSec #SecureCoding #FastAPI #Semgrep #Bandit

## Audio direction

- **Role:** quiet, precise bed with sparse interface accents.
- **Music:** original 56s synthesized score (`production/make_score.py`); chord changes land on the picture cuts. No third-party music.
- **Music treatment:** starts under the first frame, stays below the copy, and resolves into the outro. No drops, no risers, no trailer hits.
- **Music cue guidance:** original score, so cues were written to the cut list rather than detected: 0.0 hook, 5.15 reveal bell, 19.35 scan start, 24.55 scan confirm, 29.35 classification, 38.35 tests, 44.15 test confirm, 48.25 outro bell.
- **Audio-reactive treatment:** none. The visuals are deterministic and time-driven; nothing pulses to the music.
- **SFX posture:** sparse; a soft click on each hook word, a bell on the reveal, a confirm when the scan returns, a confirm when the tests finish.
- **Audio-coupled moments:** the four hook beats, the scan return, and the test result. Sounds mark state changes, not decorative motion.
- **Restraint rule:** the audio must never make the security claims feel like a product ad. No whooshes on every card, no bass drops, no loud narration.

## Storyboard

### Scene 1 — Hook — 5s
Real `vulnerable_samples/insecure_examples.py` excerpt in a terminal-style panel. The dangerous `shell=True` line is highlighted. Left copy: **"CORRECT-LOOKING CODE. REAL SECURITY RISK."** Subcopy: "The risk hides in the pattern, not the syntax. Static analysis finds what a quick read misses."

**Sequential/interaction:** the hook lines rise in on four soft beats; the code panel is present from the first frame so the opening is never empty.
**Audio intent:** establish quiet tension.
**Audio-coupled idea:** one soft click per hook line.
**Music:** low, unresolved bed.
**Transition mood:** clean cut → Scene 2.

### Scene 2 — Reveal — 7s
The product name and one-sentence explanation: **"A Python security review API. One authenticated endpoint runs Bandit and maintained Semgrep rules, then normalizes every finding into a single severity model."** The right side is an orbital diagram with Bandit and Semgrep feeding a normalized core.

**Sequential/interaction:** title, description, stack chips, then orbit labels.
**Audio intent:** a single bell marks the name reveal; the bed opens slightly.
**Audio-coupled idea:** bell at 5.15s.
**Transition mood:** soft → Scene 3.

### Scene 3 — Architecture — 7s
**"One API. Two scanners. Contained by design."** Five numbered stages: Client → FastAPI → Scanners → Findings → JSON. Below, three verification cards: **"Fails closed when unset" (live 401)**, **"Relative paths only" (live 400)**, **"No false clean result" (per-scanner status)**. Footer: "Containment reduces exposure. It is not an OS sandbox."

**Sequential/interaction:** stage cards arrive left to right, then the three evidence cards.
**Audio intent:** steady, procedural.
**Audio-coupled idea:** none beyond the bed; this scene is read, not performed.
**Transition mood:** clean → Scene 4.

### Scene 4 — Live scan — 10s
**"A real scan, not a mock-up."** Left: the actual `curl` command and a trimmed JSON response, typed line by line. Right: a findings panel that counts to **15** (9 HIGH, 6 MEDIUM) with bars, then a smaller result card for the hardened app: **13 files, 0 findings**, both scanners `success`.

**Sequential/interaction:** command types, JSON lines land, count-up runs, status row turns green.
**Audio intent:** the scan should feel like work finishing, not a magic trick.
**Audio-coupled idea:** click at scan start (19.35s), confirm when the result resolves (24.55s).
**Transition mood:** clean → Scene 5.

### Scene 5 — Classification — 9s
**"Two engines. One severity model."** Three columns: Bandit pattern checks, Semgrep's 8 maintained rules, and the normalizer's stable output fields (`rule_id`, `severity`, `file`, `line`, `cwe`, `scanner_statuses`). Bottom row compares the vulnerable fixture's **15** findings with the hardened app's **0**.

**Sequential/interaction:** columns rise; both counts run; the bars fill.
**Audio intent:** clarity, no new drama.
**Audio-coupled idea:** one soft click at 29.35s.
**Transition mood:** clean → Scene 6.

### Scene 6 — Tests — 10s
**"The security claims have tests."** A giant **64**, a 64-cell matrix, and a terminal showing `python -m pytest -q` → `64 passed in 6.92s`. Six cards name the groups: auth & headers, input & SQL, scan containment, scanner status, rule fixtures, reports.

**Sequential/interaction:** the count and matrix fill; cards arrive in pairs; terminal result lands last.
**Audio intent:** release. This is the proof, so the scene can breathe.
**Audio-coupled idea:** click at 38.35s, confirm at 44.15s when the result lands.
**Transition mood:** soft lift → Scene 7.

### Scene 7 — Outro — 8s
**"Secure Code Review."** Author, cohort label, three-word method (**Scan. Normalize. Verify.**), GitHub URL, and a shield graphic. Small badges: 64 tests passed, Bandit + Semgrep, FastAPI, contained scans, Python 3.11+, MIT license.

**Sequential/interaction:** title, method, repository card, then badges.
**Audio intent:** resolve, leave a little air, end cleanly.
**Audio-coupled idea:** outro bell at 48.25s.
**Transition mood:** final hold to black.

**Music mood for this video:** restrained, optimistic, technical.
**Audio summary:** a quiet synth bed that follows the cuts, with a handful of UI clicks and two confirms marking the only moments the system actually returns a result.
