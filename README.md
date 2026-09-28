# 🛡️ Child Online Safety Monitor (COSM) v2

**IBM Bob Hackathon 2025 — Team: Phantom Rizzlers | Track: AI**

An AI-assisted tool that helps parents, teachers, and child-protection workers recognize potential online safety risks and organize appropriate next steps — without re-exposing harmful content.

---

## ⚠️ Important Notice

> **Mock/synthetic data only.** No real CSAM or real victim data is processed, stored, or transmitted. All sample cases are entirely fictional. This tool is an AI-assisted first-response aid — not a substitute for professional law enforcement.

---

## What it does

| Step | Feature |
|------|---------|
| 1 | Parent/caregiver describes the situation in plain language |
| 2 | IBM watsonx AI (Granite) + deterministic safety rules analyse the description |
| 3 | Severity level: LOW / MODERATE / HIGH / URGENT SAFETY CONCERN |
| 4 | Safety signals with plain-language explanations |
| 5 | **Personalised Safety Plan** — what to do, what to avoid, evidence guidance, escalation |
| 6 | Legal context (POCSO Act 2012, IT Act 2000) — framed as potentially relevant, not definitive |
| 7 | Save to Case History (SQLite) |
| 8 | Generate a structured **Incident Report Draft** (Markdown + PDF) |
| 9 | Case History — view, filter, update status |

---

## Quick Start

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd bob-ai-hackathon-Phantom-Rizzlers

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Configure IBM watsonx.ai for live AI
cp src/.env.example src/.env
# Edit src/.env and add your WATSONX_API_KEY + WATSONX_PROJECT_ID

# 4. Run
streamlit run src/app.py
```

Opens at **http://localhost:8501**

---

## Environment Variables

| Variable | Required for live AI | Default |
|----------|---------------------|---------|
| `WATSONX_API_KEY` or `WATSONX_APIKEY` | Yes | — |
| `WATSONX_PROJECT_ID` | Yes | — |
| `WATSONX_URL` | No | `https://us-south.ml.cloud.ibm.com` |
| `WATSONX_MODEL_ID` | No | `ibm/granite-3-8b-instruct` |
| `COSM_DEMO_MODE` | No | `false` |

**Without credentials:** The app runs in Demo Mode with realistic simulated AI responses. All other features (case history, reports, safety plan) work fully.

---

## Project Structure

```
src/
  app.py                    ← Streamlit entry-point + page router
  database.py               ← SQLite init + connection
  sample_cases.py           ← 5 synthetic demo cases
  models/
    assessment.py           ← AIAssessment, DeterministicResult, CombinedAssessment
    case.py                 ← CaseRecord, CaseStatus
  services/
    ai_service.py           ← WatsonxProvider + MockProvider + assess()
    safety_rules.py         ← Deterministic pattern-matching engine (12+ signals)
    case_service.py         ← SQLite CRUD
    report_service.py       ← Markdown + PDF report generator
  ui/
    components.py           ← CSS + shared render helpers
  pages/
    dashboard.py            ← Metrics, recent cases, CTA
    new_assessment.py       ← 2-step assessment flow
    case_history.py         ← Filterable case list
    case_detail.py          ← Single case view + status management
    reports.py              ← Report generation + download
    safety_resources.py     ← Static helplines and guidance
docs/
  architecture.md
  setup-guide.md
  contracts.md              ← Service interface contracts (used by Bob subagents)
```

---

## 5 Synthetic Demo Cases

| # | Scenario | Severity |
|---|----------|----------|
| 1 | Gaming platform — adult grooming a 13-year-old | 🔴 URGENT |
| 2 | School teacher reports behavioural changes | 🟠 HIGH |
| 3 | Instagram sextortion / blackmail | 🔴 URGENT |
| 4 | Normal school homework group chat | 🟢 LOW |
| 5 | Telegram webcam coercion + isolation | 🔴 URGENT |

Click any demo case in the sidebar to load it instantly.

---

## Safety Safeguards

- ❌ Does not ask users to upload images or video
- ❌ Does not encourage contacting the suspected person
- ❌ Does not suggest forwarding harmful material
- ✅ "Do not re-open" warning on every assessment
- ✅ Immediate danger → urgent banner + emergency numbers always shown
- ✅ Report never reproduces the raw description
- ✅ Legal provisions framed as "potentially relevant" — not definitive conclusions
- ✅ All AI credentials server-side via environment variables

---

## Emergency Contacts (India)

| Service | Number |
|---------|--------|
| Emergency | **112** |
| Childline India | **1098** (24×7) |
| National Cyber Helpline | **1930** |
| Cyber Crime Portal | [cybercrime.gov.in](https://cybercrime.gov.in) |

---

## Team

- **Shashank Yadav** (Lead) — shashank.yadav.10a@gmail.com
- **Jammi Sunder Karthikeya** — jskarthikeya05@gmail.com

---

*IBM Bob Hackathon 2025 | Built with IBM Bob subagent workflow*
