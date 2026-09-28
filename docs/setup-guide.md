# Setup Guide — Child Online Safety Monitor (COSM)

**Team: Phantom Rizzlers | IBM Bob Hackathon 2025**

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.9+ | 3.11 recommended |
| pip | 23+ | Bundled with Python |
| Git | Any | For cloning |

No API keys, cloud accounts, or internet connection are required — the app runs fully locally with mock data.

---

## Installation

### 1 — Clone the repository

```bash
git clone <repo-url>
cd bob-ai-hackathon-Phantom-Rizzlers
```

### 2 — Create a virtual environment (recommended)

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `streamlit` — web application framework
- `reportlab` — PDF generation (optional but included for PDF export)

### 4 — Run the application

```bash
streamlit run src/app.py
```

The app will open automatically at **http://localhost:8501**.

---

## Using the Demo

1. **Open the app** — navigate to `http://localhost:8501`
2. **Load a sample case** — click any of the 5 buttons in the left sidebar (e.g. "🔴 Case 3 — Sextortion via Instagram DMs")
3. **Click "Analyse Now"** — results appear in under a second
4. **Browse the 4 tabs:**
   - ⚠️ Warning Signs
   - ⚖️ Legal Provisions
   - 🔒 Evidence Preservation
   - 📄 Download Report
5. **Download the report** — click "Download as Markdown" or "Download as PDF"

---

## Running on a Remote Server / Cloud

To share the app during a demo:

```bash
# Option A — Streamlit's built-in sharing (requires account)
streamlit run src/app.py --server.port 8501 --server.address 0.0.0.0

# Option B — ngrok tunnel (quick public URL)
# In one terminal:
streamlit run src/app.py
# In another terminal:
ngrok http 8501
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: streamlit` | Run `pip install -r requirements.txt` inside the virtual environment |
| `ModuleNotFoundError: reportlab` | Run `pip install reportlab` — PDF export falls back to markdown if missing |
| Port 8501 already in use | Run `streamlit run src/app.py --server.port 8502` |
| App opens but sidebar is empty | Ensure you are running from the repo root, not the `src/` directory |
| Import errors for `analyzer` | Confirm you run `streamlit run src/app.py` (not `python src/app.py`) |

---

## File Structure Reference

```
bob-ai-hackathon-Phantom-Rizzlers/
├── src/
│   ├── app.py               ← Streamlit UI entry-point
│   ├── analyzer.py          ← Pattern analysis, risk scoring, legal mapping
│   ├── sample_cases.py      ← 5 synthetic demo cases
│   └── report_generator.py  ← Markdown + PDF report builder
├── docs/
│   ├── setup-guide.md       ← This file
│   └── architecture.md      ← System design overview
├── requirements.txt
├── README.md
└── submission.yaml
```

---

## No Configuration Required

This MVP uses:
- **No environment variables** — no `.env` file needed
- **No database** — all analysis is in-memory
- **No external APIs** — fully offline
- **No authentication** — single-user local tool

---

*For questions, contact the Phantom Rizzlers team via the hackathon platform.*
