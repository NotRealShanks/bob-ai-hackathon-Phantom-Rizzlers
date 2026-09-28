# Architecture — Child Online Safety Monitor (COSM)

**Team: Phantom Rizzlers | IBM Bob Hackathon 2025 | Track: AI**

---

## Overview

COSM is a single-process, fully local Streamlit application. There is no backend server, no database, and no external API calls. All analysis happens in-memory on the user's machine.

```
┌─────────────────────────────────────────────────────────┐
│                   Browser (localhost:8501)               │
│                                                         │
│  ┌─────────────┐    ┌──────────────────────────────┐   │
│  │  Sidebar     │    │  Main Panel                  │   │
│  │  ─────────  │    │  ──────────                  │   │
│  │  Sample     │    │  Text Input Area              │   │
│  │  Cases (5)  │───▶│  ↓                            │   │
│  │             │    │  [Analyse Now] button         │   │
│  │  Emergency  │    │  ↓                            │   │
│  │  Contacts   │    │  Results: Risk Badge          │   │
│  └─────────────┘    │  Tabs: Warnings / Legal /     │   │
│                     │        Preservation / Report  │   │
│                     └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
           │                        │
           ▼                        ▼
┌──────────────────┐    ┌────────────────────────┐
│  sample_cases.py │    │      analyzer.py        │
│  ───────────── │    │  ──────────────────     │
│  5 synthetic    │    │  detect_input_type()    │
│  demo cases     │    │  analyse_text()         │
└──────────────────┘    │  BEHAVIOURAL_PATTERNS   │
                        │  POCSO_SECTIONS         │
                        │  IT_ACT_SECTIONS        │
                        │  PRESERVATION_STEPS     │
                        └────────────┬───────────┘
                                     │ AnalysisResult
                                     ▼
                        ┌────────────────────────┐
                        │   report_generator.py   │
                        │  ──────────────────     │
                        │  generate_markdown()    │
                        │  generate_pdf_bytes()   │
                        └────────────────────────┘
```

---

## Component Descriptions

### `src/app.py` — Streamlit UI
- Entry-point; run with `streamlit run src/app.py`
- Manages session state (`input_text`, `result`, `reporter_context`)
- Renders risk badges, warning sign cards, legal cards, step cards
- Sidebar hosts 5 one-click demo case buttons
- Triggers analysis on button click; renders results in 4 tabs
- Download buttons for Markdown and PDF report

### `src/analyzer.py` — Core Analysis Engine
- `detect_input_type(text)` — heuristically classifies input as `chat` or `behavioural`
- `analyse_text(text) → AnalysisResult` — main analysis pipeline:
  1. Runs text against 12 compiled regex patterns (`BEHAVIOURAL_PATTERNS`)
  2. Sums category-weighted scores (behavioural: 8, communication: 10, digital: 15)
  3. Applies critical-trigger boosts (+20 per hit)
  4. Maps score to Low / Medium / High / Critical risk band
  5. Forces Critical on coercion/blackmail detection
  6. Selects relevant POCSO and IT Act provisions
  7. Returns typed `AnalysisResult` dataclass
- No I/O, no network calls, no side-effects

### `src/sample_cases.py` — Synthetic Demo Cases
- 5 `SampleCase` dataclasses, entirely fictional
- Cover the full risk spectrum (Low → Critical)
- Loaded on sidebar button click via `st.session_state`

### `src/report_generator.py` — Report Builder
- `generate_markdown_report(result, context) → str` — produces a CyberTipline-style incident report with no harmful content; includes risk summary, warning signs, legal provisions, preservation checklist, and reporting contacts
- `generate_pdf_bytes(markdown) → bytes` — renders markdown to PDF via `reportlab`; gracefully falls back to UTF-8 encoded markdown if `reportlab` is unavailable

---

## Data Flow

```
User Input (text)
       │
       ▼
analyse_text()  ← regex patterns, legal catalog, preservation steps
       │
       ▼
AnalysisResult  (dataclass: risk_level, score, warning_signs, legal_mappings, ...)
       │
       ├─▶  app.py renders UI tabs
       │
       └─▶  generate_markdown_report() / generate_pdf_bytes()
                    │
                    ▼
             Download button (Markdown or PDF)
```

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **No LLM / API calls** | Fully offline, zero latency, no cost, no data-privacy risk |
| **Regex pattern matching** | Transparent, auditable, deterministic — appropriate for a safety tool |
| **No raw input in report** | Prevents re-exposure of potentially harmful content |
| **Streamlit** | Zero-boilerplate MVP; judges can run it in 3 commands |
| **reportlab for PDF** | Pure-Python, no external services, no cloud dependency |
| **Dataclasses** | Clear typed interfaces; easy to extend to ML/LLM backend later |

---

## Extension Points

This MVP is deliberately pattern-based. Future versions could:
- Replace `analyse_text()` with a **watsonx.ai** NLP call for richer semantic analysis
- Add a **vector similarity** layer against a known grooming script database
- Integrate with **cybercrime.gov.in API** when one becomes available
- Add **multi-language support** (Hindi, Tamil, etc.)
- Deploy as a **Streamlit Community Cloud** or **IBM Cloud Code Engine** app

---

*Architecture document for IBM Bob Hackathon 2025 submission.*
