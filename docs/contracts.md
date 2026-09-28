# COSM — Architecture & Service Contracts

> **Source of truth for Backend Agent and Frontend Agent.**
> Do not deviate from the interfaces defined here without updating this document first.

---

## 1. Directory Layout

```
src/
  app.py                        ← thin Streamlit router (page routing + sidebar only)
  database.py                   ← SQLite init + connection helper
  sample_cases.py               ← unchanged from original
  models/
    __init__.py
    assessment.py               ← AIAssessment, SignalItem, DeterministicResult, CombinedAssessment
    case.py                     ← CaseRecord, CaseStatus
  services/
    __init__.py
    safety_rules.py             ← refactored from analyzer.py (same logic, renamed class/function)
    ai_service.py               ← AIProvider ABC + WatsonxProvider + MockProvider + assess()
    case_service.py             ← SQLite CRUD (wraps database.py)
    report_service.py           ← refactored from report_generator.py (accepts CaseRecord)
  ui/
    __init__.py
    components.py               ← shared CSS injection + all render helper functions
  pages/
    __init__.py
    dashboard.py                ← summary stats, recent cases, quick-start CTA
    new_assessment.py           ← 2-step assessment flow (input → results → save)
    case_history.py             ← paginated/filtered case list
    case_detail.py              ← open a single case; update status; download report
    reports.py                  ← generate / download report for a selected case
    safety_resources.py         ← static helplines, reporting guides, platform links
```

**Notes:**
- `src/analyzer.py` and `src/report_generator.py` are superseded by
  `services/safety_rules.py` and `services/report_service.py` respectively.
  They are retained temporarily for backward-compatibility during migration
  and may be deleted once all pages import from `services/`.
- `src/sample_cases.py` is kept exactly as-is; pages import from it directly.

---

## 2. Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `WATSONX_API_KEY` | Yes (for live AI) | — | IBM watsonx.ai API key |
| `WATSONX_PROJECT_ID` | Yes (for live AI) | — | watsonx project ID |
| `WATSONX_URL` | No | `https://us-south.ml.cloud.ibm.com` | watsonx regional endpoint |
| `WATSONX_MODEL_ID` | No | `ibm/granite-3-8b-instruct` | Model used for assessment |
| `COSM_DEMO_MODE` | No | `false` | Set `"true"` to force MockProvider even when credentials are present |

**Fallback rule:** If `WATSONX_API_KEY` **or** `WATSONX_PROJECT_ID` is absent (or empty),
`get_provider()` silently returns `MockProvider`. The UI must display a visible
"Demo mode — AI not configured" notice whenever `MockProvider` is active.

All credentials must be read via `os.environ.get(...)` or `python-dotenv`.
**Never hardcode any credential.**

---

## 3. SQLite Schema

Database file: `cosm.db` (created in the same directory as `database.py`, i.e. `src/`).

```sql
CREATE TABLE IF NOT EXISTS cases (
    -- Identity
    id                       TEXT PRIMARY KEY,
        -- Format: "CASE-YYYYMMDD-HHMMSS-xxxx"  (xxxx = 4 random hex chars)
        -- Example: "CASE-20250715-143022-a1b2"

    -- Timestamps (ISO 8601 UTC, e.g. "2025-07-15T14:30:22Z")
    created_at               TEXT NOT NULL,
    updated_at               TEXT NOT NULL,

    -- Reporter
    reporter_role            TEXT NOT NULL,
        -- e.g. "Parent / Guardian", "Teacher / School Counsellor"

    -- Situation (NEVER store harmful imagery; text is the reporter's own words only)
    situation_summary        TEXT NOT NULL,
        -- Max 2000 characters of the reporter's OWN description.
        -- Truncated server-side before insert.

    -- AI-derived classification (NULL if AI was unavailable)
    situation_category       TEXT,
        -- e.g. "Grooming", "Sextortion", "Cyberbullying", "General Concern"

    -- Assessment severity
    severity                 TEXT NOT NULL,
        -- "LOW" | "MODERATE" | "HIGH" | "URGENT_SAFETY_CONCERN"

    -- Immediate safety flag
    immediate_safety_concern INTEGER NOT NULL DEFAULT 0,
        -- 0 = No, 1 = Yes (reporter-stated)

    -- Structured AI response (JSON)
    ai_assessment_json       TEXT,
        -- Full AIAssessment serialised to JSON; NULL if AI unavailable.

    -- Deterministic engine output (JSON)
    deterministic_signals_json TEXT,
        -- DeterministicResult serialised to JSON.

    -- Extracted lists (JSON arrays of strings / SignalItem dicts)
    recommended_actions_json TEXT,
        -- JSON array of action strings.

    safety_signals_json      TEXT,
        -- JSON array of SignalItem dicts: {"signal": str, "explanation": str, "severity": str}

    -- Case lifecycle
    case_status              TEXT NOT NULL DEFAULT 'Open',
        -- "Open" | "Under Review" | "Report Prepared" | "Resolved"

    report_status            TEXT NOT NULL DEFAULT 'Not Generated',
        -- "Not Generated" | "Draft Generated" | "Submitted"

    -- Optional free text from reporter
    reporter_notes           TEXT,

    -- Cached report draft (generated on demand)
    report_draft_md          TEXT
);
```

---

## 4. Python Dataclass Definitions

### `models/assessment.py`

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class SignalItem:
    signal: str
    explanation: str
    severity: str   # "informational" | "concerning" | "serious"


@dataclass
class AIAssessment:
    concern_level: str           # "LOW" | "MODERATE" | "HIGH" | "URGENT_SAFETY_CONCERN"
    situation_category: str      # e.g. "Grooming", "Sextortion", "Cyberbullying", "General Concern"
    confidence: str              # "LOW" | "MODERATE" | "HIGH"
    uncertainty_note: str        # e.g. "Assessment is based only on the description provided."
    situation_summary: str       # 2–3 sentence neutral summary of the reported situation
    safety_signals: List[SignalItem]
    why_this_matters: str        # plain-language explanation for a non-expert parent
    recommended_actions: List[str]
    actions_to_avoid: List[str]
    evidence_guidance: List[str]
    reporting_guidance: List[str]
    escalation_guidance: str
    legal_context_note: str      # framed as "potentially relevant", never definitive
    disclaimer: str              # must always be non-empty
    error_note: str = ""         # non-empty string if the AI call failed or was unavailable


@dataclass
class DeterministicResult:
    """
    Direct rename of AnalysisResult from analyzer.py.
    All fields are identical; only the class name changes.
    """
    risk_level: str              # "Low" | "Medium" | "High" | "Critical"
    risk_score: int              # 0–100
    warning_signs: List = field(default_factory=list)     # List[WarningSigns] from safety_rules
    legal_mappings: List = field(default_factory=list)    # List[LegalMapping] from safety_rules
    preservation_steps: List[str] = field(default_factory=list)
    summary: str = ""
    input_type: str = "unknown"  # "behavioural" | "chat"


# Severity mapping from deterministic risk_level to AI concern_level vocabulary
DETERMINISTIC_TO_SEVERITY = {
    "Low":      "LOW",
    "Medium":   "MODERATE",
    "High":     "HIGH",
    "Critical": "URGENT_SAFETY_CONCERN",
}

# Severity ordering for taking the higher of two levels
SEVERITY_ORDER = {
    "LOW": 0,
    "MODERATE": 1,
    "HIGH": 2,
    "URGENT_SAFETY_CONCERN": 3,
}


@dataclass
class CombinedAssessment:
    """
    Merges AI assessment + deterministic safety-rules result into one object
    consumed by pages and case_service.
    """
    ai: AIAssessment
    deterministic: DeterministicResult
    immediate_safety_concern: bool

    @property
    def final_severity(self) -> str:
        """
        Returns the higher of ai.concern_level and the mapped deterministic level.
        If immediate_safety_concern is True, returns at minimum "HIGH".
        """
        ai_level = SEVERITY_ORDER.get(self.ai.concern_level, 0)
        det_level = SEVERITY_ORDER.get(
            DETERMINISTIC_TO_SEVERITY.get(self.deterministic.risk_level, "LOW"), 0
        )
        combined = max(ai_level, det_level)
        # Ensure immediate safety concern is never hidden
        if self.immediate_safety_concern:
            combined = max(combined, SEVERITY_ORDER["HIGH"])
        return list(SEVERITY_ORDER.keys())[combined]
```

### `models/case.py`

```python
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class CaseStatus(str, Enum):
    OPEN = "Open"
    UNDER_REVIEW = "Under Review"
    REPORT_PREPARED = "Report Prepared"
    RESOLVED = "Resolved"


@dataclass
class CaseRecord:
    id: str
    created_at: str
    updated_at: str
    reporter_role: str
    situation_summary: str
    situation_category: str           # may be empty string if AI unavailable
    severity: str                     # "LOW" | "MODERATE" | "HIGH" | "URGENT_SAFETY_CONCERN"
    immediate_safety_concern: bool
    ai_assessment_json: str           # raw JSON string; empty string if AI unavailable
    deterministic_signals_json: str   # raw JSON string
    recommended_actions_json: str     # raw JSON string (array)
    safety_signals_json: str          # raw JSON string (array of SignalItem dicts)
    case_status: CaseStatus
    report_status: str                # "Not Generated" | "Draft Generated" | "Submitted"
    reporter_notes: str               # empty string if none provided
    report_draft_md: str              # empty string until generated
```

---

## 5. Service Interface Contracts

### `database.py`

```python
def init_db() -> None:
    """
    Create the cases table if it does not exist.
    Called once at application startup (from app.py before page routing).
    Safe to call multiple times (uses CREATE TABLE IF NOT EXISTS).
    """

def get_connection() -> sqlite3.Connection:
    """
    Return a new SQLite connection to cosm.db.
    Caller is responsible for closing or using as a context manager.
    Row factory is set to sqlite3.Row so columns are accessible by name.
    """
```

### `services/safety_rules.py`

```python
def analyse(text: str) -> DeterministicResult:
    """
    Main entry-point for the deterministic analysis engine.
    Renamed from analyse_text() in analyzer.py.
    Implementation is identical to analyzer.py — same patterns, scoring, legal mappings.
    Returns DeterministicResult (renamed from AnalysisResult).
    """
```

Internal helpers (`detect_input_type`, `_build_summary`) remain private (underscore prefix).
All pattern constants (`BEHAVIOURAL_PATTERNS`, `CRITICAL_TRIGGERS`, `POCSO_SECTIONS`,
`IT_ACT_SECTIONS`, `PRESERVATION_STEPS`, etc.) are retained as module-level constants
and may be imported by other modules that need them (e.g. `report_service.py`).

### `services/ai_service.py`

```python
from abc import ABC, abstractmethod
from models.assessment import AIAssessment

class AIProvider(ABC):
    @abstractmethod
    def assess(self, description: str, immediate_safety_concern: bool) -> AIAssessment:
        """Analyse the description and return a structured AIAssessment."""
        ...

class WatsonxProvider(AIProvider):
    """
    Uses ibm-watsonx-ai SDK to call the configured Granite model.
    Reads credentials from environment variables (never from arguments).
    Sends the system prompt + user prompt template defined in Section 6.
    Parses the JSON response into AIAssessment.
    """

class MockProvider(AIProvider):
    """
    Returns realistic fixture responses without any API call.
    Used when credentials are absent or COSM_DEMO_MODE=true.
    Should provide different fixture responses depending on keywords in the description
    so demo cases feel realistic (e.g. return URGENT_SAFETY_CONCERN for sextortion keywords).
    """

def get_provider() -> AIProvider:
    """
    Returns WatsonxProvider if WATSONX_API_KEY and WATSONX_PROJECT_ID are both
    set and non-empty in os.environ AND COSM_DEMO_MODE != "true".
    Otherwise returns MockProvider.
    """

def assess(description: str, immediate_safety_concern: bool) -> AIAssessment:
    """
    Convenience function. Calls get_provider().assess(...).
    NEVER raises an exception.
    On any error (network, parse, timeout, etc.), catches the exception,
    logs a warning, and returns an AIAssessment with:
      - concern_level = "LOW"
      - error_note = "<human-readable error description>"
      - all list fields = []
      - disclaimer = "AI assessment unavailable. Please rely on the safety signals below."
    """
```

### `services/case_service.py`

```python
from models.assessment import CombinedAssessment
from models.case import CaseRecord, CaseStatus

def create_case(
    reporter_role: str,
    situation_summary: str,
    combined: CombinedAssessment,
    reporter_notes: str = "",
) -> CaseRecord:
    """
    Persist a new case to SQLite and return the full CaseRecord.
    - Generates id in format "CASE-YYYYMMDD-HHMMSS-xxxx".
    - Truncates situation_summary to 2000 characters before storing.
    - Serialises combined.ai and combined.deterministic to JSON.
    - Sets case_status = "Open", report_status = "Not Generated".
    - Sets immediate_safety_concern from combined.immediate_safety_concern.
    - Sets severity from combined.final_severity.
    - Sets situation_category from combined.ai.situation_category.
    """

def get_case(case_id: str) -> CaseRecord | None:
    """Return the CaseRecord for the given id, or None if not found."""

def list_cases(
    limit: int = 50,
    status_filter: str | None = None,
) -> list[CaseRecord]:
    """
    Return up to `limit` cases ordered by created_at DESC.
    If status_filter is provided, filter by case_status.
    """

def update_case_status(case_id: str, new_status: str) -> CaseRecord:
    """
    Update case_status and updated_at for the given case.
    Returns the updated CaseRecord.
    Raises ValueError if case_id not found.
    """

def save_report_draft(case_id: str, draft_md: str) -> None:
    """
    Store the generated markdown report draft in report_draft_md.
    Set report_status = "Draft Generated".
    Update updated_at.
    """
```

### `services/report_service.py`

```python
from models.case import CaseRecord

def generate_markdown(case: CaseRecord) -> str:
    """
    Produce a structured DRAFT incident report in Markdown format.

    The report MUST:
    1. Include a prominent disclaimer at the top:
       "DRAFT REPORT — FOR REVIEW PURPOSES ONLY
        This is a structured draft prepared to assist a human reporter.
        It is NOT a legal determination.
        It is NOT an official complaint or court submission.
        It has NOT been verified by law enforcement.
        It requires human review before any submission to authorities."
    2. Include: case ID, date, reporter role, severity, situation category,
       safety signals, recommended actions, evidence guidance, reporting contacts.
    3. NOT include the original situation_summary text (prevents re-exposure).
    4. NOT claim that any crime has definitely occurred.
    5. Include the reporter_notes if non-empty (these are the reporter's own annotations,
       not reproduced harmful content).

    Returns the markdown string.
    """

def generate_pdf(markdown_text: str) -> bytes:
    """
    Convert markdown to PDF bytes using reportlab.
    Falls back to UTF-8-encoded markdown bytes if reportlab is not installed.
    Implementation adapted from report_generator.py — same PDF logic.
    """
```

---

## 6. Watsonx AI Prompt Template

These exact strings must be used in `WatsonxProvider.assess()`.

### System Prompt

```
You are a child online safety assessment assistant. Your role is to help parents and caregivers understand concerning online situations involving their child. You must follow these rules strictly:

1. NEVER claim that a crime has definitely occurred. Use language like "may indicate", "could suggest", "potentially consistent with".
2. NEVER encourage the parent or child to continue communicating with a suspected person to gather evidence.
3. NEVER suggest viewing, re-opening, forwarding, or sharing potentially harmful material.
4. NEVER ask for or encourage the sharing of sexual imagery involving children under any circumstances.
5. Use plain, calm language. The reader may be distressed.
6. Always respond with ONLY valid JSON matching the schema below. Do not include any text outside the JSON object.
7. If the situation suggests immediate physical danger, use concern_level "URGENT_SAFETY_CONCERN".
8. Legal references must be framed as "potentially relevant" — never as definitive legal conclusions.
9. Include a non-empty disclaimer field in every response.
10. If you are uncertain, say so in uncertainty_note and use a lower confidence value.

You must return a JSON object with EXACTLY these fields:
{
  "concern_level": "LOW" | "MODERATE" | "HIGH" | "URGENT_SAFETY_CONCERN",
  "situation_category": string,
  "confidence": "LOW" | "MODERATE" | "HIGH",
  "uncertainty_note": string,
  "situation_summary": string,
  "safety_signals": [{"signal": string, "explanation": string, "severity": "informational" | "concerning" | "serious"}],
  "why_this_matters": string,
  "recommended_actions": [string],
  "actions_to_avoid": [string],
  "evidence_guidance": [string],
  "reporting_guidance": [string],
  "escalation_guidance": string,
  "legal_context_note": string,
  "disclaimer": string
}
```

### User Prompt Template (Python f-string)

```python
f"""A parent or caregiver has described the following situation involving their child online.

Immediate safety concern reported by parent: {"YES" if immediate_safety_concern else "NO"}

Description:
{description}

Assess this situation and return ONLY a JSON object matching the required schema. Do not include any text before or after the JSON."""
```

### JSON Parsing Notes for `WatsonxProvider`

- Strip leading/trailing whitespace and any markdown code fences (` ```json ` … ` ``` `) before `json.loads()`.
- On `json.JSONDecodeError` or any missing required field, fall back to an `AIAssessment` with `error_note` set.
- Validate that `concern_level` is one of the four permitted values; if not, default to `"MODERATE"`.
- Construct `safety_signals` as `[SignalItem(**s) for s in raw["safety_signals"]]`.

---

## 7. Page Routing Design

`app.py` is the single Streamlit entry-point. It uses `st.session_state["page"]`
for routing — no Streamlit `pages/` folder magic; the `pages/` directory contains
plain Python modules imported by `app.py`.

```python
# --- Initialisation (top of app.py, after st.set_page_config) ---
from database import init_db
init_db()   # idempotent; safe to call on every rerun

# --- Session state defaults ---
if "page" not in st.session_state:
    st.session_state["page"] = "dashboard"
if "selected_case_id" not in st.session_state:
    st.session_state["selected_case_id"] = None

# --- Sidebar navigation ---
# Clicking a nav item sets st.session_state["page"] and calls st.rerun()
# Valid page values:
#   "dashboard"
#   "new_assessment"
#   "case_history"
#   "case_detail"     (requires selected_case_id to be set first)
#   "reports"         (requires selected_case_id to be set first)
#   "safety_resources"

# --- Page dispatch ---
if st.session_state["page"] == "dashboard":
    from pages.dashboard import render
    render()
elif st.session_state["page"] == "new_assessment":
    from pages.new_assessment import render
    render()
# ... etc.
```

**Navigation labels and order (sidebar):**

| Label | page value |
|---|---|
| 🏠 Dashboard | `dashboard` |
| 🔍 New Assessment | `new_assessment` |
| 📂 Case History | `case_history` |
| 📄 Reports | `reports` |
| 🆘 Safety Resources | `safety_resources` |

Case Detail is not a top-level nav item. It is reached by clicking "Open" on a case
in Case History or Dashboard. It sets `st.session_state["selected_case_id"]` and
`st.session_state["page"] = "case_detail"` then calls `st.rerun()`.

---

## 8. New Assessment Flow State

All state is stored in `st.session_state`. The New Assessment page manages a
two-step flow:

```python
# Step tracking
st.session_state["assessment_step"]       # int: 1 (input form) | 2 (results)

# Step 1 inputs
st.session_state["assessment_input"]      # str: the description the parent typed
st.session_state["assessment_role"]       # str: reporter role selection
st.session_state["assessment_immediate"]  # bool: immediate safety concern checkbox
st.session_state["assessment_notes"]      # str: optional reporter notes

# Step 2 outputs
st.session_state["combined_assessment"]   # CombinedAssessment | None

# Post-save
st.session_state["saved_case_id"]         # str | None: set after "Save Case" clicked
```

**Step transitions:**

1. User fills Step 1 form → clicks "Analyse" → `assessment_step` is set to 2,
   `combined_assessment` is populated, page reruns.
2. On Step 2, user can click "Save Case" → `case_service.create_case()` is called,
   `saved_case_id` is set, a success message is shown with a link to Case History.
3. User can click "← Start New Assessment" → clears all `assessment_*` keys,
   sets `assessment_step = 1`.

**Immediate safety concern rule (must be enforced in the page):**

If `assessment_immediate` is `True`, the urgent banner (`render_urgent_banner()`)
must be rendered at the very top of Step 2 results, **before** any tabs or other content,
**regardless of the AI's `concern_level` or `confidence`**.

---

## 9. UI Component Signatures

All functions live in `ui/components.py`. Pages import them with:
```python
from ui.components import inject_css, render_severity_badge, ...
```

```python
def inject_css() -> None:
    """Inject the shared CSS block via st.markdown(..., unsafe_allow_html=True)."""

def severity_colour(severity: str) -> tuple:
    """
    Map a severity string to (bg_hex, fg_hex, emoji).
    Handles both old vocabulary (Low/Medium/High/Critical) and new
    (LOW/MODERATE/HIGH/URGENT_SAFETY_CONCERN).
    Returns a neutral grey triple for unknown values.
    """

def render_severity_badge(severity: str) -> None:
    """Render a coloured pill badge for the given severity."""

def render_urgent_banner() -> None:
    """
    Render the full-width red urgent/emergency banner.
    Content: emergency contacts (112, 1098, 1930, cybercrime.gov.in).
    Must be called at the top of Step 2 when immediate_safety_concern=True.
    """

def render_do_not_reopen_banner() -> None:
    """
    Render the amber 'Do NOT re-open the original content' warning banner.
    Preserved from original app.py verbatim.
    """

def render_signal_card(signal: SignalItem) -> None:
    """
    Render a single SafetySignal / WarningSigns as a card.
    Accepts either SignalItem (from AI) or WarningSigns (from deterministic engine).
    Both have .signal/.sign and .explanation fields.
    """

def render_legal_card(lm) -> None:
    """
    Render a single LegalMapping as a card.
    lm has .act, .section, .description, .max_penalty fields.
    """

def render_step_card(text: str) -> None:
    """Render a single evidence/action step as a green step card."""

def render_safety_plan(combined: CombinedAssessment) -> None:
    """
    Render the full Personalized Safety Plan component.
    This is a prominent, self-contained card containing:
      - Severity badge
      - What we noticed (safety_signals from AI or deterministic)
      - Why this matters (combined.ai.why_this_matters or deterministic summary)
      - What you can do now (recommended_actions)
      - What to avoid (actions_to_avoid)
      - Evidence guidance (evidence_guidance)
      - When to seek additional help (escalation_guidance)
    Must show urgent banner inline if combined.immediate_safety_concern is True.
    """

def render_case_row(case: CaseRecord, on_open_callback) -> None:
    """
    Render one row/card in the Case History list.
    Shows: severity badge, category, created_at (formatted), case_status, "Open" button.
    on_open_callback is called (with case.id) when the Open button is clicked.
    """
```

---

## 10. Files to Remove

After the new implementation is complete and verified, delete:

| File | Reason |
|---|---|
| `docs/template-guide.md` | Hackathon template boilerplate |
| `docs/problem-statement.md` | Hackathon template boilerplate |
| `docs/solution-overview.md` | Superseded by updated architecture docs |
| `src/README.md` | Template boilerplate (if it exists) |

**Do NOT delete yet** (retained for backward-compatibility during migration):
- `src/analyzer.py` — superseded by `services/safety_rules.py`
- `src/report_generator.py` — superseded by `services/report_service.py`

These can be deleted in the Security/Code Review pass once all imports have been updated.

---

## 11. Backward Compatibility Notes

- **`sample_cases.py` is unchanged.** It uses the existing `SampleCase` dataclass.
  Pages that load sample cases read `SAMPLE_CASES` from `sample_cases` and populate
  `st.session_state["assessment_input"]` — the same mechanism as the current app.

- **5 sample cases continue to work.** The sidebar "Sample Demo Cases" section is
  preserved in the new `app.py` sidebar and pre-fills the New Assessment form.

- **All existing safety language is preserved verbatim**, including:
  - "Do NOT re-open, re-read, or share the original content."
  - Emergency contact numbers (112, 1098, 1930, 1091).
  - "Viewing it again may harm the child further and compromise legal evidence integrity."

- **Report disclaimer language is updated.** The old report said
  "intended as a first-step aid — professional law enforcement investigation is required."
  The new report must say (verbatim in the prominent disclaimer block):
  > "DRAFT REPORT — FOR REVIEW PURPOSES ONLY.
  > This is a structured draft prepared to assist a human reporter.
  > It is NOT a legal determination. It is NOT an official complaint.
  > It has NOT been verified by law enforcement.
  > It requires human review before submission to any authority."

- **The word "court-ready" must not appear anywhere in the application.**

- **Legal provisions are framed as "potentially relevant."** No page, service, or
  report may state that a specific law was definitely violated based solely on the
  parent's description.

- **The deterministic safety-rules layer always runs**, even when AI is available.
  The `CombinedAssessment` merges both results. Pages render signals from both sources.

---

## 12. Implementation Notes for Agents

### For the Backend Agent

1. Implement files in this order:
   `database.py` → `models/__init__.py` → `models/assessment.py` → `models/case.py`
   → `services/__init__.py` → `services/safety_rules.py` → `services/ai_service.py`
   → `services/case_service.py` → `services/report_service.py`

2. `safety_rules.py` must import nothing from `analyzer.py`. It is a clean copy
   with renamed class (`DeterministicResult`) and renamed function (`analyse`).

3. `ai_service.py` must load `.env` via `python-dotenv` if present:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

4. `WatsonxProvider` uses `ibm_watsonx_ai.foundation_models.ModelInference`.
   Check the ibm-watsonx-ai SDK docs for the correct import path.

5. `case_service.py` must call `init_db()` itself if database.py has not been
   initialised (defensive programming), though `app.py` also calls it at startup.

6. Do not use `dataclasses.asdict()` on `CombinedAssessment` for SQLite storage —
   serialise each sub-object individually to avoid recursive nested dicts.

### For the Frontend Agent

1. Implement files in this order:
   `ui/__init__.py` → `ui/components.py` → `pages/__init__.py`
   → `pages/safety_resources.py` → `pages/dashboard.py`
   → `pages/new_assessment.py` → `pages/case_history.py`
   → `pages/case_detail.py` → `pages/reports.py` → `app.py`

2. Every page module exports a single `render()` function that takes no arguments.
   All data access goes through service functions; no page queries SQLite directly.

3. `new_assessment.py` is the most complex page — build it last among the pages
   so the component library is fully tested first.

4. The "Demo mode — AI not configured" notice must appear in the sidebar whenever
   `MockProvider` is active. Import `get_provider` from `services.ai_service` and
   check `isinstance(get_provider(), MockProvider)`.

5. The Safety Plan (`render_safety_plan`) is the centrepiece of the results view.
   It must appear prominently — above the detail tabs, directly after the severity badge.
