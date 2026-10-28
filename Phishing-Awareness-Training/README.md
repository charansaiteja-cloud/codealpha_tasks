# 🛡️ Phishing Awareness Training

An interactive cybersecurity awareness application built with Python and Streamlit to educate users about phishing attacks, fraudulent websites, and social engineering techniques.

**Author:** Bejjam Charan Sai Teja  
**License:** MIT  
**Project Type:** Cybersecurity Awareness and Education

---

## 📌 Project Overview

Phishing is a cyberattack in which attackers impersonate trusted organizations or individuals to trick users into revealing sensitive information, transferring money, or opening malicious links and attachments.

This project provides an interactive learning environment that helps users recognize common phishing indicators, understand attacker tactics, and practice safer online behavior.

## ✨ Features

- 📘 **Phishing Fundamentals** — Learn how phishing attacks work.
- 📧 **Email Analysis** — Understand suspicious senders, urgent requests, and malicious links.
- 🌐 **Fake Website Awareness** — Identify suspicious domains and fraudulent login pages.
- 🧠 **Social Engineering** — Learn about impersonation, urgency, fear, and manipulation.
- ✅ **Interactive Quiz** — Test your knowledge and review your answers.
- 📊 **Score Tracking** — View your quiz performance.
- 🏆 **Completion Certificate** — Download a certificate when the required score is achieved, if enabled.
- 📄 **Quiz Report** — Download your results, if enabled.

## 🛠️ Technologies Used

- Python 3
- Streamlit
- Git and GitHub (optional, for version control)

## 📂 Project Structure

```text
Phishing-Awareness-Training/
├── app.py
├── README.md
├── LICENSE
└── .venv/             # Local virtual environment; do not commit
```

Additional files may be present depending on your implementation.

## ⚙️ Installation and Setup

### Prerequisites

Install Python 3.10 or newer and ensure that Python and pip are available from your terminal.

Verify your installation:

```bash
python --version
python -m pip --version
```

### 🐧 Linux Installation (Kali Linux, Ubuntu, Debian)

**1. Install Python and virtual environment support**

On Debian-based systems:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

**2. Navigate to the project directory**

```bash
cd ~/Phishing-Awareness-Training
```

**3. Create a virtual environment**

```bash
python3 -m venv .venv
```

**4. Activate the environment**

```bash
source .venv/bin/activate
```

**5. Install Streamlit**

```bash
python -m pip install --upgrade pip
python -m pip install streamlit
```

**6. Check the application syntax**

```bash
python -m py_compile app.py
```

No output indicates that the syntax check passed.

**7. Start the application**

```bash
streamlit run app.py
```

### 🪟 Windows Installation

**1. Install Python**

Download Python from:

https://www.python.org/downloads/windows/

During installation, enable **Add Python to PATH**.

**2. Open PowerShell**

Navigate to the folder containing the project:

```powershell
cd "$HOME\Phishing-Awareness-Training"
```

If you have not downloaded or copied the project yet, first obtain the project files and navigate to their location.

**3. Create a virtual environment**

```powershell
py -m venv .venv
```

**4. Activate the environment**

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

**5. Install Streamlit**

```powershell
python -m pip install --upgrade pip
python -m pip install streamlit
```

**6. Check the application syntax**

```powershell
python -m py_compile app.py
```

**7. Start the application**

```powershell
python -m streamlit run app.py
```

## 🚀 How to Use the Application

**Step 1 — Launch the application**

Run the Streamlit command for your operating system.

**Step 2 — Open the dashboard**

Streamlit normally displays a local URL:

http://localhost:8501

Open this address in your web browser.

**Step 3 — Study the learning module**

Read the introductory material to understand phishing and its common warning signs.

**Step 4 — Explore email examples**

Examine suspicious sender addresses, unexpected attachments, urgent messages, and unusual requests.

**Step 5 — Learn about fake websites**

Review suspicious domain names, misleading URLs, and fraudulent login pages. Remember that HTTPS alone does not prove a website is trustworthy.

**Step 6 — Study social engineering**

Learn how attackers exploit trust, authority, fear, curiosity, and urgency.

**Step 7 — Complete the quiz**

Open the quiz section, answer each question, submit your answers, and review the explanations.

**Step 8 — Download your results**

If the relevant features are enabled, download your quiz report or completion certificate.

**Step 9 — Stop the application**

Return to the terminal running Streamlit and press:

```text
Ctrl + C
```

## 🔄 Application Workflow

```text
Start
  |
  v
Launch Streamlit Application
  |
  v
Open Dashboard in Browser
  |
  v
Study Phishing Awareness Topics
  |
  v
Explore Email and Website Examples
  |
  v
Learn Social Engineering Techniques
  |
  v
Complete Interactive Quiz
  |
  v
Review Score and Explanations
  |
  v
Download Available Report or Certificate
  |
  v
End
```

## 🔐 Security Best Practices

- Verify the sender before responding to unexpected messages.
- Do not share passwords or one-time verification codes.
- Avoid opening unexpected attachments or suspicious links.
- Visit sensitive websites using a known bookmark or a manually entered trusted address.
- Verify payment and account-change requests through a separate trusted channel.
- Enable multifactor authentication.
- Report suspected phishing to the relevant security team.
- Never use real credentials in training demonstrations.

## 🎯 Learning Outcomes

After completing the training, users should be better able to:

- Recognize common phishing indicators.
- Identify suspicious URLs and fraudulent websites.
- Understand common social engineering techniques.
- Respond safely to suspicious communications.
- Apply practical cybersecurity hygiene.

## ⚠️ Disclaimer

This project is intended for cybersecurity awareness, education, and defensive learning.

All examples should be fictional or appropriately sanitized. Do not use this project to collect credentials, impersonate real organizations, or conduct unauthorized security testing.

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## 👨‍💻 Author

**Bejjam Charan Sai Teja**

Phishing Awareness Training — Cybersecurity Education Project.
