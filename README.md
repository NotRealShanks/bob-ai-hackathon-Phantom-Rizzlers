# 🛡️ Child Online Safety Monitor (COSM)

**IBM Bob Hackathon 2025 — Team: Phantom Rizzlers | Track: AI**

A first-response Streamlit tool for parents, teachers, and NGO / child-protection workers to detect online grooming warning signs, understand applicable Indian law, and generate a ready-to-submit incident report — without re-exposing harmful content.

---

## ⚠️ Important Notice

> This tool uses **mock / synthetic data only**. No real CSAM (Child Sexual Abuse Material) or real victim data is ever processed, stored, or transmitted. All sample cases are entirely fictional.

---

## Features

| Feature | Description |
|---------|-------------|
| **Grooming detection** | Pattern-matching against 12+ known grooming/predatory behaviour signals |
| **Risk scoring** | Automated Low / Medium / High / Critical risk level with 0–100 score |
| **Legal mapping** | Automatic mapping to POCSO Act 2012 (§11–§19) and IT Act 2000 (§67B, §66E) |
| **Evidence guide** | 10-step evidence preservation checklist without re-exposing content |
| **Auto-filled report** | CyberTipline / cybercrime.gov.in style report, downloadable as Markdown or PDF |
| **5 demo cases** | Synthetic sample cases for instant demo — one click loads them |

---

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url>
cd bob-ai-hackathon-Phantom-Rizzlers

# 2. Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run src/app.py
```

The app will open at `http://localhost:8501`.

---

## Project Structure

```
src/
  app.py               — Streamlit UI (main entry-point)
  analyzer.py          — Core analysis engine (grooming patterns, risk scoring, legal mapping)
  sample_cases.py      — 5 synthetic demo cases
  report_generator.py  — Markdown + PDF report builder
docs/
  setup-guide.md       — Detailed setup and deployment guide
  architecture.md      — System architecture overview
requirements.txt
README.md
submission.yaml
```

---

## Sample Cases (Demo)

| # | Scenario | Expected Risk |
|---|----------|---------------|
| 1 | New 'friend' on gaming platform (gifting + secrecy + image request) | 🔴 Critical |
| 2 | Behavioural changes at school (withdrawal, phone hiding, isolation) | 🟠 High |
| 3 | Sextortion via Instagram DMs (coercion + blackmail) | 🔴 Critical |
| 4 | Normal school group chat | 🟢 Low |
| 5 | Webcam coercion + isolation on Telegram | 🔴 Critical |

---

## Legal References

- **POCSO Act 2012** — Protection of Children from Sexual Offences: Sections 11, 12, 13, 14, 15, 19
- **IT Act 2000** — Information Technology Act: Sections 67B (online CSAM), 66E (privacy), 67, 66C/66D

---

## Reporting Contacts (India)

| Resource | Details |
|----------|---------|
| National Cyber Crime Portal | [cybercrime.gov.in](https://cybercrime.gov.in) |
| National Cyber Helpline | **1930** |
| Childline India | **1098** (24×7) |
| Emergency | **112** |

---

## Team

- **Shashank Yadav** (Lead)
- **Jammi Sunder Karthikeya**

---

*Built for IBM Bob Hackathon 2025. This tool is a first-response aid — professional law enforcement investigation is always required.*
