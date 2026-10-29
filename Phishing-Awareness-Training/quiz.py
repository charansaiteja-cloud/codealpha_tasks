"""Quiz data, scoring, and downloadable result generation.

This module is intentionally free of Streamlit calls so the scoring and
document-building logic can be tested without a browser or an app runtime.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from html import escape

PASS_PERCENTAGE = 80


@dataclass(frozen=True)
class Question:
    prompt: str
    options: tuple[str, ...]
    answer: int
    why: str


QUESTIONS: tuple[Question, ...] = (
    Question(
        prompt="An email demands your password immediately. What should you do?",
        options=(
            "Reply with your password",
            "Click its link quickly",
            "Verify independently and report it",
            "Forward it to everyone",
        ),
        answer=2,
        why="Never provide passwords through unexpected requests.",
    ),
    Question(
        prompt="Does HTTPS guarantee a website is legitimate?",
        options=(
            "Yes, always",
            "No, fraudulent sites can also use HTTPS",
            "Only on phones",
            "Only for email links",
        ),
        answer=1,
        why="HTTPS encrypts traffic but does not establish trustworthiness.",
    ),
    Question(
        prompt="Your manager unexpectedly requests gift cards by email. What is safest?",
        options=(
            "Buy them immediately",
            "Reply asking for their password",
            "Verify through a separate known channel",
            "Send the gift card codes",
        ),
        answer=2,
        why="Verify unusual financial requests using a trusted channel.",
    ),
    Question(
        prompt="What is multifactor authentication useful for?",
        options=(
            "Adding another layer of account protection",
            "Making every email genuine",
            "Removing all malware",
            "Verifying every website automatically",
        ),
        answer=0,
        why="MFA can help protect accounts even if a password is stolen.",
    ),
    Question(
        prompt="You clicked a suspicious work link and entered your password. What now?",
        options=(
            "Ignore it",
            "Report it immediately and follow IT guidance",
            "Delete the browser",
            "Wait several days",
        ),
        answer=1,
        why="Prompt reporting helps security teams limit potential damage.",
    ),
)


@dataclass(frozen=True)
class QuizResult:
    answers: tuple[str | None, ...]
    score: int
    total: int
    percentage: int
    passed: bool
    unanswered: int


def evaluate_quiz(answers: Sequence[str | None]) -> QuizResult:
    """Score a complete set of answers against the training questions."""
    if len(answers) != len(QUESTIONS):
        raise ValueError(f"Expected {len(QUESTIONS)} answers, received {len(answers)}.")

    normalized = tuple(answers)
    score = 0
    unanswered = 0

    for answer, question in zip(normalized, QUESTIONS, strict=False):
        if answer is None:
            unanswered += 1
        elif answer == question.options[question.answer]:
            score += 1

    total = len(QUESTIONS)
    percentage = round(score / total * 100)
    passed = unanswered == 0 and percentage >= PASS_PERCENTAGE

    return QuizResult(
        answers=normalized,
        score=score,
        total=total,
        percentage=percentage,
        passed=passed,
        unanswered=unanswered,
    )


def _display_name(learner_name: str | None) -> str:
    """Normalise a learner name and provide a safe fallback."""
    cleaned = " ".join((learner_name or "").split())
    return cleaned[:60] or "Learner"


def _iso_date(issued_on: str | date | None) -> str:
    if isinstance(issued_on, date):
        return issued_on.isoformat()
    if issued_on:
        return date.fromisoformat(issued_on).isoformat()
    return date.today().isoformat()


def _format_date(issued_on: str | date | None) -> str:
    return date.fromisoformat(_iso_date(issued_on)).strftime("%B %d, %Y")


def certificate_reference(
    result: QuizResult,
    learner_name: str | None,
    issued_on: str | date | None = None,
) -> str:
    """Return a stable, human-readable reference for a completion record."""
    raw = "|".join(
        (
            _display_name(learner_name),
            _iso_date(issued_on),
            str(result.score),
            str(result.total),
        )
    )
    return "PAT-" + sha256(raw.encode("utf-8")).hexdigest()[:10].upper()


def build_report(
    result: QuizResult,
    learner_name: str | None = "Learner",
    issued_on: str | date | None = None,
) -> str:
    """Build the downloadable, question-by-question quiz report."""
    lines = [
        "PHISHING AWARENESS TRAINING - QUIZ REPORT",
        "",
        f"Learner: {_display_name(learner_name)}",
        f"Date: {_format_date(issued_on)}",
        f"Score: {result.score}/{result.total} ({result.percentage}%)",
        f"Status: {'PASSED' if result.passed else 'NOT PASSED'}",
        "",
    ]

    for index, (question, answer) in enumerate(
        zip(QUESTIONS, result.answers, strict=False), start=1
    ):
        is_correct = answer == question.options[question.answer]
        lines.extend(
            [
                f"Question {index}: {'Correct' if is_correct else 'Incorrect'}",
                f"  {question.prompt}",
                f"  Selected: {answer or 'No answer'}",
                f"  Correct answer: {question.options[question.answer]}",
                f"  Why: {question.why}",
                "",
            ]
        )

    lines.extend(
        [
            f"Passing score: {PASS_PERCENTAGE}%",
            "This report reflects the learner's selections at submission time.",
            "",
        ]
    )
    return "\n".join(lines)


_CERTIFICATE_CSS = """
  :root {
    --navy: #0b1220;
    --navy-soft: #111c31;
    --blue: #2f6fe4;
    --cyan: #16a3c7;
    --ink: #142033;
    --muted: #5b6b82;
    --line: #d8e2f1;
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0;
    min-height: 100%;
    background: #eef3fa;
    color: var(--ink);
    font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, Arial, sans-serif;
  }
  body {
    display: grid;
    place-items: center;
    padding: 28px;
  }
  .certificate {
    width: 1000px;
    max-width: 100%;
    background: #ffffff;
    border: 1px solid var(--line);
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 24px 70px rgba(11, 18, 32, .18);
  }
  .band {
    background: linear-gradient(135deg, var(--navy) 0%, var(--navy-soft) 65%, #17345f 100%);
    color: #ffffff;
    padding: 34px 48px 30px;
    position: relative;
  }
  .band::after {
    content: "";
    position: absolute;
    right: -40px;
    top: -70px;
    width: 260px;
    height: 260px;
    border: 1px solid rgba(120, 180, 255, .28);
    border-radius: 50%;
  }
  .eyebrow {
    font-size: 12px;
    letter-spacing: 3px;
    font-weight: 700;
    color: #8fc2ff;
    text-transform: uppercase;
  }
  h1 {
    margin: 14px 0 4px;
    font-size: 42px;
    line-height: 1.1;
    letter-spacing: -.8px;
  }
  h1 span { color: #8fc2ff; }
  .subtitle {
    margin: 0;
    color: #b9cbe4;
    font-size: 16px;
  }
  .body { padding: 40px 48px 34px; }
  .lead {
    margin: 0 0 6px;
    color: var(--muted);
    font-size: 15px;
    letter-spacing: .2px;
  }
  h2 {
    margin: 8px 0 22px;
    font-size: 38px;
    line-height: 1.2;
    color: var(--navy);
    border-bottom: 2px solid var(--blue);
    display: inline-block;
    padding-bottom: 8px;
  }
  .statement {
    margin: 0 0 26px;
    max-width: 760px;
    color: #34445a;
    font-size: 17px;
    line-height: 1.65;
  }
  .stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin: 0 0 28px;
  }
  .stat {
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 14px 16px;
    background: #f7faff;
  }
  .stat .label {
    display: block;
    color: var(--muted);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    margin-bottom: 6px;
  }
  .stat .value {
    color: var(--navy);
    font-size: 20px;
    font-weight: 800;
  }
  .meta {
    display: flex;
    justify-content: space-between;
    gap: 20px;
    border-top: 1px solid var(--line);
    padding-top: 18px;
    color: var(--muted);
    font-size: 12px;
  }
  .meta strong { color: var(--ink); }
  .note {
    margin: 18px 0 0;
    color: #7a8799;
    font-size: 11px;
    line-height: 1.5;
  }
  .seal {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-top: 16px;
    padding: 7px 12px;
    border: 1px solid rgba(143, 194, 255, .45);
    border-radius: 999px;
    color: #b9d7ff;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.4px;
    text-transform: uppercase;
  }
  .seal::before {
    content: "";
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #46d39a;
    box-shadow: 0 0 12px #46d39a;
  }
  @media print {
    @page { size: A4 landscape; margin: 0; }
    body { background: #ffffff; padding: 0; }
    .certificate { border: 0; border-radius: 0; box-shadow: none; }
  }
"""


def build_certificate_html(
    result: QuizResult,
    learner_name: str | None = "Learner",
    issued_on: str | date | None = None,
) -> str:
    """Build a printable HTML certificate for a passing result."""
    if not result.passed:
        raise ValueError("A certificate requires a passing quiz result.")

    name = escape(_display_name(learner_name), quote=True)
    issued = _format_date(issued_on)
    reference = certificate_reference(result, learner_name, issued_on)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Certificate of Completion - {name}</title>
<style>{_CERTIFICATE_CSS}</style>
</head>
<body>
<main class="certificate">
  <header class="band">
    <div class="eyebrow">CodeAlpha - Cybersecurity Awareness</div>
    <h1>Certificate <span>of Completion</span></h1>
    <p class="subtitle">Phishing Awareness Training</p>
    <div class="seal">Passed</div>
  </header>
  <section class="body">
    <p class="lead">This certificate is presented to</p>
    <h2>{name}</h2>
    <p class="statement">
      for completing the Phishing Awareness Training knowledge check and
      demonstrating an understanding of phishing indicators, suspicious
      websites, social engineering tactics, and safe reporting practices.
    </p>
    <div class="stats">
      <div class="stat"><span class="label">Score</span><span class="value">{result.score}/{result.total}</span></div>
      <div class="stat"><span class="label">Result</span><span class="value">{result.percentage}%</span></div>
      <div class="stat"><span class="label">Status</span><span class="value">Passed</span></div>
    </div>
    <div class="meta">
      <span>Issued <strong>{issued}</strong></span>
      <span>Reference <strong>{reference}</strong></span>
    </div>
    <p class="note">
      This is an educational completion record. It is not a formal
      certification and is not independently verifiable.
    </p>
  </section>
</main>
</body>
</html>
"""
