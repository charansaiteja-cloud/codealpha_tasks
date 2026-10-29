"""Phishing Awareness Training - interactive Streamlit application."""

from __future__ import annotations

from datetime import date

import streamlit as st
import streamlit.components.v1 as components

from quiz import (
    PASS_PERCENTAGE,
    QUESTIONS,
    QuizResult,
    build_certificate_html,
    build_report,
    evaluate_quiz,
)


def _render_learn() -> None:
    st.header("What is phishing?")
    st.write(
        "Phishing is an attempt to trick people into revealing "
        "sensitive information, sending money, or opening "
        "malicious links and attachments."
    )
    st.subheader("Warning signs")
    st.markdown("""
    - Unexpected requests for passwords or verification codes.
    - Urgent threats about account closure.
    - Suspicious links or unexpected attachments.
    - Sender addresses that do not match the claimed organization.
    - Requests to bypass normal security procedures.
    """)
    st.subheader("Best practices")
    st.markdown("""
    - Verify requests through a separate, trusted channel.
    - Visit websites using a known bookmark or typed address.
    - Never share passwords or one-time verification codes.
    - Enable multifactor authentication.
    - Report suspicious messages to your IT or security team.
    """)


def _render_email_examples() -> None:
    st.header("Example: suspicious email")
    st.warning("FICTIONAL TRAINING EXAMPLE")
    st.code("""
From: Security Team <security@example.invalid>
Subject: URGENT! Your account will close in 10 minutes

Your account has a problem.
Click the link below immediately to keep access.
Enter your password and verification code.
""")
    st.markdown("""
    **Red flags**
    - Artificial urgency.
    - A request for a password and verification code.
    - An unexpected link.
    - The sender and request have not been independently verified.
    """)
    st.success(
        "Safe response: do not click. Contact the organization "
        "using its official website or known support number."
    )


def _render_websites() -> None:
    st.header("How to spot fake websites")
    st.markdown("""
    - Inspect the complete domain, not just the logo or page design.
    - Watch for misspellings and misleading subdomains.
    - HTTPS encrypts a connection but does not prove a site is genuine.
    - Be suspicious of unexpected login pages reached through messages.
    - Never rely on a padlock icon alone.
    """)
    st.code("Example: https://login.example.invalid")
    st.caption("The .invalid domain is reserved for examples; this is not a real login website.")


def _render_social_engineering() -> None:
    st.header("Social engineering tactics")
    st.markdown("""
    - **Authority:** pretending to be a manager or IT administrator.
    - **Urgency:** demanding immediate action.
    - **Fear:** threatening account suspension or legal trouble.
    - **Curiosity:** tempting you with unexpected documents or news.
    - **Familiarity:** impersonating a colleague or supplier.
    - **Baiting:** offering a prize or download to encourage risky action.
    """)
    st.info(
        "Pause, verify the request independently, and follow "
        "your organization's security procedures."
    )


def _scroll_to_top_once(flag: str) -> None:
    if st.session_state.pop(flag, False):
        components.html(
            """
            <script>
              const scrollToTop = () => {
                const main = window.parent.document.getElementById("stMain");
                if (main) main.scrollTo({top: 0, behavior: "auto"});
              };
              let attempts = 0;
              const timer = setInterval(() => {
                scrollToTop();
                if (++attempts >= 50) clearInterval(timer);
              }, 100);
            </script>
            """,
            height=0,
        )


def _render_quiz_result(
    result: QuizResult,
    learner_name: str,
    submitted_on: str | None,
    attempt: int,
) -> None:
    _scroll_to_top_once("scroll_to_result")
    st.divider()
    st.subheader(f"Your score: {result.score}/{result.total}")
    st.progress(result.percentage / 100)

    if result.passed:
        st.success("Training completed successfully!")
    else:
        st.info(f"Score at least {PASS_PERCENTAGE}% to qualify. Review your answers and try again.")

    if result.unanswered:
        st.warning(
            f"{result.unanswered} question(s) were left unanswered. "
            "Answer every question to qualify for a certificate."
        )

    st.caption(
        f"Prepared for {learner_name or 'Learner'} · Submitted {submitted_on or 'this session'}"
    )

    if result.passed:
        certificate = build_certificate_html(result, learner_name, submitted_on)
        st.download_button(
            "Download Completion Certificate",
            certificate,
            file_name="phishing_training_certificate.html",
            mime="text/html",
            key=f"download_certificate_{attempt}",
        )
        st.caption(
            "The certificate is an educational completion record, "
            "not an independently verifiable credential."
        )

    report = build_report(result, learner_name, submitted_on)
    st.download_button(
        "Download Quiz Report",
        report,
        file_name="phishing_quiz_report.txt",
        mime="text/plain",
        key=f"download_report_{attempt}",
    )

    if st.button("Retry quiz", key=f"retry_quiz_{attempt}"):
        for key in (
            "quiz_result",
            "quiz_answers",
            "quiz_submitted_on",
            "scroll_to_result",
        ):
            st.session_state.pop(key, None)
        st.session_state["quiz_attempt"] = attempt + 1
        st.session_state["scroll_to_form"] = True
        st.rerun()

    st.divider()
    st.subheader("Review your answers")
    for index, (question, answer) in enumerate(
        zip(QUESTIONS, result.answers, strict=False), start=1
    ):
        selected = answer or "No answer"
        if answer == question.options[question.answer]:
            st.success(f"Question {index}: Correct")
            st.caption(f"Your answer: {selected} · {question.why}")
        else:
            st.error(f"Question {index}: Incorrect")
            st.caption(
                f"Your answer: {selected} · "
                f"Correct answer: {question.options[question.answer]} · "
                f"{question.why}"
            )


def _render_quiz_form(attempt: int, stored_name: str) -> None:
    answers: list[str | None] = []

    with st.form(f"phishing_quiz_{attempt}"):
        name = st.text_input(
            "Your name (optional, used on the certificate)",
            value=stored_name,
            max_chars=60,
            placeholder="Defaults to Learner",
        )
        for index, question in enumerate(QUESTIONS):
            st.subheader(f"Question {index + 1}")
            st.write(question.prompt)
            choice = st.radio(
                "Choose one answer:",
                question.options,
                key=f"question_{attempt}_{index}",
                index=None,
            )
            answers.append(choice)

        submitted = st.form_submit_button("Submit quiz")

    if not submitted:
        return

    if any(answer is None for answer in answers):
        st.warning("Please answer all questions before submitting.")
        return

    st.session_state["learner_name"] = name.strip()
    st.session_state["quiz_submitted_on"] = date.today().isoformat()
    st.session_state["quiz_result"] = evaluate_quiz(answers)
    st.session_state["scroll_to_result"] = True
    st.rerun()


def _render_quiz() -> None:
    st.header("Knowledge check")
    st.caption(
        f"Answer all {len(QUESTIONS)} questions. "
        f"A score of {PASS_PERCENTAGE}% or higher earns a certificate."
    )

    attempt = int(st.session_state.get("quiz_attempt", 0))
    result = st.session_state.get("quiz_result")

    if result is None:
        _scroll_to_top_once("scroll_to_form")
        _render_quiz_form(attempt, st.session_state.get("learner_name", ""))
        return

    _render_quiz_result(
        result,
        st.session_state.get("learner_name", ""),
        st.session_state.get("quiz_submitted_on"),
        attempt,
    )


st.set_page_config(
    page_title="Phishing Awareness Training",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Phishing Awareness Training")
st.caption("Learn • Identify • Protect")

st.info("Learn to recognize phishing emails, fake websites, and social engineering attacks.")

learn_tab, email_tab, websites_tab, social_tab, quiz_tab = st.tabs(
    [
        "📘 Learn",
        "📧 Email Examples",
        "🌐 Fake Websites",
        "🧠 Social Engineering",
        "✅ Quiz",
    ]
)

with learn_tab:
    _render_learn()

with email_tab:
    _render_email_examples()

with websites_tab:
    _render_websites()

with social_tab:
    _render_social_engineering()

with quiz_tab:
    _render_quiz()

st.divider()
st.caption("Educational project | Fictional examples for defensive learning.")
