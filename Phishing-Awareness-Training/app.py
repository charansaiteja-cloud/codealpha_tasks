import streamlit as st

st.set_page_config(
    page_title="Phishing Awareness Training",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Phishing Awareness Training")
st.caption("Learn • Identify • Protect")

st.info(
    "Learn to recognize phishing emails, fake websites, "
    "and social engineering attacks."
)

learn, email, websites, social, quiz = st.tabs([
    "📘 Learn",
    "📧 Email Examples",
    "🌐 Fake Websites",
    "🧠 Social Engineering",
    "✅ Quiz",
])

with learn:
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

with email:
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

with websites:
    st.header("How to spot fake websites")
    st.markdown("""
    - Inspect the complete domain, not just the logo or page design.
    - Watch for misspellings and misleading subdomains.
    - HTTPS encrypts a connection but does not prove a site is genuine.
    - Be suspicious of unexpected login pages reached through messages.
    - Never rely on a padlock icon alone.
    """)
    st.code("Example: https://login.example.invalid")
    st.caption(
        "The .invalid domain is reserved for examples; "
        "this is not a real login website."
    )

with social:
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

with quiz:
    st.header("Knowledge check")

    questions = [
        {
            "q": "An email demands your password immediately. What should you do?",
            "options": [
                "Reply with your password",
                "Click its link quickly",
                "Verify independently and report it",
                "Forward it to everyone",
            ],
            "answer": 2,
            "why": "Never provide passwords through unexpected requests.",
        },
        {
            "q": "Does HTTPS guarantee a website is legitimate?",
            "options": [
                "Yes, always",
                "No, fraudulent sites can also use HTTPS",
                "Only on phones",
                "Only for email links",
            ],
            "answer": 1,
            "why": "HTTPS encrypts traffic but does not establish trustworthiness.",
        },
        {
            "q": "Your manager unexpectedly requests gift cards by email. What is safest?",
            "options": [
                "Buy them immediately",
                "Reply asking for their password",
                "Verify through a separate known channel",
                "Send the gift card codes",
            ],
            "answer": 2,
            "why": "Verify unusual financial requests using a trusted channel.",
        },
        {
            "q": "What is multifactor authentication useful for?",
            "options": [
                "Adding another layer of account protection",
                "Making every email genuine",
                "Removing all malware",
                "Verifying every website automatically",
            ],
            "answer": 0,
            "why": "MFA can help protect accounts even if a password is stolen.",
        },
        {
            "q": "You clicked a suspicious work link and entered your password. What now?",
            "options": [
                "Ignore it",
                "Report it immediately and follow IT guidance",
                "Delete the browser",
                "Wait several days",
            ],
            "answer": 1,
            "why": "Prompt reporting helps security teams limit potential damage.",
        },
    ]

    with st.form("phishing_quiz"):
        answers = []
        for i, question in enumerate(questions):
            st.subheader(f"Question {i + 1}")
            st.write(question["q"])
            choice = st.radio(
                "Choose one answer:",
                question["options"],
                key=f"question_{i}",
                index=None,
            )
            answers.append(choice)

        submitted = st.form_submit_button("Submit quiz")

    if submitted:
        unanswered = sum(answer is None for answer in answers)

        if unanswered:
            st.warning("Please answer all questions before submitting.")
        else:
            score = 0
            for i, question in enumerate(questions):
                correct = answers[i] == question["options"][question["answer"]]
                if correct:
                    score += 1
                    st.success(f"Question {i + 1}: Correct")
                else:
                    st.error(
                        f"Question {i + 1}: Incorrect. "
                        f"Correct answer: {question['options'][question['answer']]}"
                    )
                st.caption(question["why"])

            percentage = round(score / len(questions) * 100)
            st.subheader(f"Your score: {score}/{len(questions)}")
            st.progress(percentage / 100)

            if percentage >= 80:
                st.success("Training completed successfully!")
                certificate = (
                    "PHISHING AWARENESS TRAINING\n"
                    "CERTIFICATE OF COMPLETION\n\n"
                    f"Score: {score}/{len(questions)}\n"
                    f"Result: {percentage}%\n"
                    "Status: PASSED\n"
                    "Issued by: Phishing Awareness Training Project\n"
                )
                st.download_button(
                    "Download Completion Certificate",
                    certificate,
                    file_name="phishing_training_certificate.txt",
                    mime="text/plain",
                )
            else:
                st.info("Score at least 80% to qualify. Review and try again.")

            report = (
                "PHISHING AWARENESS TRAINING - QUIZ REPORT\n\n"
                f"Score: {score}/{len(questions)}\n"
                f"Percentage: {percentage}%\n"
                f"Status: {'PASSED' if percentage >= 80 else 'NOT PASSED'}\n"
            )
            st.download_button(
                "Download Quiz Report",
                report,
                file_name="phishing_quiz_report.txt",
                mime="text/plain",
            )

st.divider()
st.caption(
    "Educational project | Fictional examples for defensive learning."
)
