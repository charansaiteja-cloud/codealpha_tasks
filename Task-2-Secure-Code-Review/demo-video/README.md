# Secure Code Review — Demo Video

A 56-second, 16:9 demo of the **CodeAlpha Cybersecurity Internship — Secure Code Review** project. The film was planned with Brag and composed/rendered with OpenFilm. It uses only real local results captured from the project; no findings, scanner behavior, or test counts were invented.

## Deliverables

| Deliverable | Path |
| --- | --- |
| Rendered master (MP4) | [`secure-code-review-demo.mp4`](secure-code-review-demo.mp4) |
| Editable OpenFilm project | [`openfilm/film.html`](openfilm/film.html) |
| Brag plan / storyboard | [`brag-plan.md`](brag-plan.md) |
| Share copy | [`share-copy.txt`](share-copy.txt) |
| Verified run evidence | [`evidence/`](evidence/) |
| Original score generator | [`production/make_score.py`](production/make_score.py) |

## Video facts

| Property | Verified value |
| --- | --- |
| Duration | 56.000 s |
| Resolution | 1920 × 1080 (16:9) |
| Frame rate | 30 fps (1680 frames) |
| Video codec | H.264 / `yuv420p` |
| Audio codec | AAC, 48 kHz, stereo |
| File size | 14,706,660 bytes (~14.0 MiB) |
| Integrated loudness | −16.2 LUFS |
| True peak | −4.1 dBTP |
| SHA-256 | `41e51f0f0b6fc7c573979971aef347c9ceef0e7c184c7229a95d581c28e33ece` |
| Narration | None — on-screen captions + music, suitable for silent autoplay |

## What the film shows

| Time | Scene | Content |
| --- | --- | --- |
| 0:00–0:05 | Hook | A real vulnerable fixture excerpt, with `shell=True` highlighted. “Correct-looking code. Real security risk.” |
| 0:05–0:12 | Reveal | The product and its one authenticated scan endpoint; Bandit + Semgrep converge on one schema. |
| 0:12–0:19 | Architecture | Client → FastAPI → scanners → findings → JSON, plus live `401` / `400` containment evidence. |
| 0:19–0:29 | Live scan | A real `curl` request and JSON response; 15 findings (9 HIGH, 6 MEDIUM) in the vulnerable fixture. |
| 0:29–0:38 | Classification | How Bandit and Semgrep severities map to one model; 15 vs. 0 findings comparison. |
| 0:38–0:48 | Tests | 64 passing tests, a 64-cell result matrix, and the six behavior groups they protect. |
| 0:48–0:56 | Outro | Secure Code Review, the method, the author, and the repository URL. |

## Claims and evidence

The video’s numbers come from fresh local runs against the project at its current revision. Raw output is preserved in [`evidence/`](evidence/).

| Claim in the film | Evidence |
| --- | --- |
| `64 passed in 6.92s` | [`evidence/pytest.txt`](evidence/pytest.txt), [`evidence/pytest-verbose.txt`](evidence/pytest-verbose.txt) |
| Vulnerable fixture: 15 findings, 9 HIGH / 6 MEDIUM, 1 Python file, both scanners `success` | [`evidence/scan-vulnerable.json`](evidence/scan-vulnerable.json) |
| Hardened `app/`: 13 files, 0 findings, both scanners `success` | [`evidence/scan-app.json`](evidence/scan-app.json) |
| Missing API key returns `401` | [`evidence/unauthorized-status.txt`](evidence/unauthorized-status.txt), [`evidence/unauthorized.json`](evidence/unauthorized.json) |
| Traversal / absolute path is rejected with `400` | [`evidence/traversal-status.txt`](evidence/traversal-status.txt), [`evidence/traversal.json`](evidence/traversal.json), [`evidence/absolute-status.txt`](evidence/absolute-status.txt), [`evidence/absolute.json`](evidence/absolute.json) |
| Bandit reports no medium/high findings in `app/` (2 low-severity items sit below the `-ll` gate) | [`evidence/bandit-app.txt`](evidence/bandit-app.txt) |
| Local Semgrep rules report 0 findings in `app/` | [`evidence/semgrep-app.txt`](evidence/semgrep-app.txt) |
| Security headers are present | [`evidence/health-headers.txt`](evidence/health-headers.txt) |

**Scope note shown in the film:** a clean scan is evidence for one revision and ruleset, not proof that the software is vulnerability-free. This is an educational lab, not a production service.

## How it was made

### Brag

Brag’s planning workflow supplied the creative spine:

- Inspected the repository rather than a landing page.
- Chose a `polished` tone with the freeform direction “a security engineer’s evidence reel — calm, exact, quietly confident.”
- Wrote a hook, a reveal, three evidence-led highlights, and a restrained outro.
- Defined a dark navy/cyan visual identity and a Space Grotesk + JetBrains Mono type system suited to the project’s technical, terminal-led subject.
- Wrote the share copy and the LinkedIn caption.
- Supplied the CC0 UI click cue used for the hook beats and transitions.
- Handed the finished storyboard to OpenFilm as one shared deliverable.

Brag’s usual 15–25 second guidance was deliberately extended to 56 seconds because the brief asked for a 45–60 second internship demo. The extra time is used for readable evidence, not filler.

### OpenFilm

OpenFilm handled composition and delivery:

- Editable HTML/CSS/SVG film with seven scene pages under `openfilm/`.
- `film.html` track structure: one picture track of seven trimmed iframes and two audio tracks (score and sparse SFX).
- Deterministic `window.film.frame(t)` animation; all motion and seeded decoration depend only on time, so repeated renders match.
- A shared design system (`shared.css`) and animation helpers (`shared.js`).
- `open` for the Studio preview, `look` for contact sheets, full-size frame checks, audio waveform/loudness reports, and the same-time/same-picture determinism check.
- Final render: 1680 frames at 30 fps, 1920×1080, four workers, H.264/AAC MP4.

### Audio

The 56-second score is original and synthesized locally by [`production/make_score.py`](production/make_score.py); chord changes land on the picture cuts. The only borrowed sound is Brag’s bundled CC0 `click2.ogg` UI cue. No narration was used.

The final mix was raised from an initial −24.9 LUFS to **−16.2 LUFS integrated / −4.1 dBTP**, which is comfortable for social playback and leaves headroom below clipping.

## Reproduction

From this directory:

```bash
cd openfilm
npx -y openfilm@latest open .
npx -y openfilm@latest look
npx -y openfilm@latest render --out ../secure-code-review-demo.mp4 --fps 30
```

Regenerate the score (requires Python with NumPy and SciPy):

```bash
cd ../production
python3 make_score.py
```

The OpenFilm Studio for this project was previewed locally at `http://127.0.0.1:4747`; that URL is ephemeral and not part of the deliverable.

## Verification

The delivered MP4 was checked with:

- `ffprobe` — 56.000 s, 1920×1080, 30/1 fps, H.264 + AAC, nonzero size.
- Full `ffmpeg -f null -` decode — exit 0, no decode errors.
- `blackdetect` over the picture track — no black segments at the configured threshold.
- `ebur128` — −16.2 LUFS integrated, −4.1 dBTP true peak.
- Visual spot checks from the final master at 0.2 s, 34.8 s, 42.0 s, and 55.8 s — frames preserved in [`evidence/render-frames/`](evidence/render-frames/).
- OpenFilm `look` — same `t`, same picture across shuffled orders.

Rendering reported **SwiftShader software WebGL**. The output is deterministic in this environment, but a GPU-backed browser can differ slightly in rasterization; the MP4 is the canonical master.

## LinkedIn caption

```text
I built a secure code review lab for my CodeAlpha Cybersecurity internship: one authenticated FastAPI endpoint, Bandit + Semgrep, one normalized severity model, and 64 tests.

This 56-second demo uses real local results — 15 findings (9 HIGH, 6 MEDIUM) in the vulnerable fixture, 0 findings across 13 hardened app files, a 401 for a missing API key, and a 400 for a path traversal attempt.

Code: https://github.com/charansaiteja-cloud/CodeAlpha_SecureCodeReview

#CodeAlpha #Cybersecurity #AppSec #SecureCoding #FastAPI #Semgrep #Bandit
```

## Limitations

- Scanner results describe the captured revision, ruleset, and tool versions. They are not a guarantee of security.
- The `6.92s` pytest duration is the captured evidence run; timing varies with machine state and pytest cache warmth.
- The demo was rendered locally with software WebGL; performance and minor rasterization may differ on other machines.
- The film has no narration. It is designed to work muted, with on-screen text carrying the story.
- The score is an original synthesized bed, not a licensed commercial track.
- The project’s CI workflow was not executed remotely for this video; the tests and scans shown are local runs.
- Generated media is intentionally **not committed** to the repository. Keep the MP4 and `demo-video/` as release/demo artifacts.
- The repository link, author name, and license badge are drawn from the project’s public README; no secrets, API keys, tokens, or `.env` contents appear in the film.
