"""
app.py — Child Online Safety Monitor & Reporting Guide (COSM)
Streamlit application entry-point.

Team: Phantom Rizzlers | IBM Bob Hackathon 2025
Track: AI

IMPORTANT: This tool uses mock/synthetic data only. No real CSAM or
real victim data is ever processed, stored, or transmitted.
"""

from __future__ import annotations
import sys
import os

# Ensure src/ is on the path when running from repo root
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from analyzer import analyse_text, AnalysisResult
from sample_cases import SAMPLE_CASES
from report_generator import generate_markdown_report, generate_pdf_bytes

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Child Online Safety Monitor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS — minimal professional theme
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
/* ── Global ── */
html, body, [class*="css"] { font-family: -apple-system, "Segoe UI", system-ui, sans-serif; }

/* ── Risk badges ── */
.badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.95rem;
    letter-spacing: 0.04em;
}
.badge-low      { background:#d1fae5; color:#065f46; }
.badge-medium   { background:#fef9c3; color:#854d0e; }
.badge-high     { background:#ffedd5; color:#9a3412; }
.badge-critical { background:#fee2e2; color:#991b1b; }

/* ── Warning banner ── */
.warning-banner {
    background: #fff8e1;
    border-left: 4px solid #f59e0b;
    padding: 12px 16px;
    border-radius: 0 6px 6px 0;
    margin-bottom: 16px;
    font-size: 0.88rem;
    color: #78350f;
}

/* ── Critical banner ── */
.critical-banner {
    background: #fee2e2;
    border-left: 4px solid #dc2626;
    padding: 12px 16px;
    border-radius: 0 6px 6px 0;
    margin-bottom: 16px;
    font-size: 0.92rem;
    font-weight: 600;
    color: #7f1d1d;
}

/* ── Sign card ── */
.sign-card {
    background: #f7f8fa;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 10px;
}
.sign-card .sign-title { font-weight: 700; font-size: 0.95rem; color: #1f2328; }
.sign-card .sign-cat   { font-size: 0.78rem; color: #57606a; text-transform: uppercase; letter-spacing: 0.06em; }
.sign-card .sign-expl  { font-size: 0.88rem; color: #374151; margin-top: 4px; }

/* ── Legal card ── */
.legal-card {
    background: #f0f4ff;
    border: 1px solid #c7d2fe;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 10px;
}
.legal-card .legal-title   { font-weight: 700; font-size: 0.92rem; color: #1e3a8a; }
.legal-card .legal-penalty { font-size: 0.82rem; color: #7f1d1d; margin-top: 4px; }
.legal-card .legal-desc    { font-size: 0.88rem; color: #374151; margin-top: 4px; }

/* ── Step card ── */
.step-card {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 8px;
    padding: 10px 16px;
    margin-bottom: 8px;
    font-size: 0.88rem;
    color: #14532d;
}

/* ── Score gauge container ── */
.score-container {
    text-align: center;
    padding: 16px;
    background: #f7f8fa;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
}
.score-number { font-size: 3rem; font-weight: 800; line-height: 1; }
.score-label  { font-size: 0.78rem; color: #57606a; text-transform: uppercase; letter-spacing: 0.08em; }

/* ── Sample case button styling ── */
[data-testid="stButton"] button {
    width: 100%;
    text-align: left;
    border-radius: 8px;
}

/* ── Footer ── */
.cosm-footer {
    margin-top: 40px;
    padding-top: 16px;
    border-top: 1px solid #e5e7eb;
    font-size: 0.78rem;
    color: #57606a;
    text-align: center;
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "result" not in st.session_state:
    st.session_state.result = None
if "reporter_context" not in st.session_state:
    st.session_state.reporter_context = ""


# ---------------------------------------------------------------------------
# Helper renderers
# ---------------------------------------------------------------------------

RISK_COLOURS = {
    "Low": ("#d1fae5", "#065f46", "🟢"),
    "Medium": ("#fef9c3", "#854d0e", "🟡"),
    "High": ("#ffedd5", "#9a3412", "🟠"),
    "Critical": ("#fee2e2", "#991b1b", "🔴"),
}


def render_risk_badge(risk_level: str) -> None:
    cls = f"badge badge-{risk_level.lower()}"
    emoji = RISK_COLOURS.get(risk_level, ("", "", "⚪"))[2]
    st.markdown(f'<span class="{cls}">{emoji} {risk_level} Risk</span>', unsafe_allow_html=True)


def render_score_gauge(score: int, risk_level: str) -> None:
    colour = RISK_COLOURS.get(risk_level, ("#f7f8fa", "#1f2328", ""))[1]
    st.markdown(
        f"""
<div class="score-container">
    <div class="score-number" style="color:{colour};">{score}</div>
    <div class="score-label">Risk Score / 100</div>
</div>""",
        unsafe_allow_html=True,
    )


def render_warning_signs(result: AnalysisResult) -> None:
    if not result.warning_signs:
        st.success("No significant grooming indicators detected in this text.")
        return
    for sign in result.warning_signs:
        cat_colour = {"behavioural": "#7c5cd8", "communication": "#d97706", "digital": "#2563eb"}.get(sign.category, "#57606a")
        st.markdown(
            f"""<div class="sign-card">
  <div class="sign-title">⚠️ {sign.sign}</div>
  <div class="sign-cat" style="color:{cat_colour};">● {sign.category}</div>
  <div class="sign-expl">{sign.explanation}</div>
</div>""",
            unsafe_allow_html=True,
        )


def render_legal_mappings(result: AnalysisResult) -> None:
    if not result.legal_mappings:
        st.info("No specific legal provisions flagged at this risk level.")
        return
    for lm in result.legal_mappings:
        st.markdown(
            f"""<div class="legal-card">
  <div class="legal-title">⚖️ {lm.act} — {lm.section}</div>
  <div class="legal-desc">{lm.description}</div>
  <div class="legal-penalty">🔒 Max Penalty: {lm.max_penalty}</div>
</div>""",
            unsafe_allow_html=True,
        )


def render_preservation_steps(result: AnalysisResult) -> None:
    for step in result.preservation_steps:
        st.markdown(f'<div class="step-card">{step}</div>', unsafe_allow_html=True)


def render_critical_banner() -> None:
    st.markdown(
        """<div class="critical-banner">
🚨 CRITICAL RISK DETECTED — Take immediate action.<br>
Report now: <strong>cybercrime.gov.in</strong> | Call <strong>1930</strong> (Cyber Helpline) | Call <strong>1098</strong> (Childline) | Emergency <strong>112</strong>
</div>""",
        unsafe_allow_html=True,
    )


def render_do_not_reopen_banner() -> None:
    st.markdown(
        """<div class="warning-banner">
🔒 <strong>Do NOT re-open, re-read, or share the original content.</strong>
Viewing it again may harm the child further and compromise legal evidence integrity.
Evidence must be preserved through official channels only.
</div>""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/IBM_logo.svg/320px-IBM_logo.svg.png", width=80)
    st.markdown("## 🛡️ COSM")
    st.markdown("**Child Online Safety Monitor**")
    st.markdown("*IBM Bob Hackathon 2025 — Phantom Rizzlers*")
    st.divider()

    st.markdown("### 📋 Sample Demo Cases")
    st.caption("Click to load a synthetic case instantly")

    for i, case in enumerate(SAMPLE_CASES):
        risk_emoji = {"Low": "🟢", "Medium": "🟡", "High": "🟠", "Critical": "🔴"}.get(case.expected_risk, "⚪")
        label = f"{risk_emoji} {case.title}"
        if st.button(label, key=f"sample_{i}"):
            st.session_state.input_text = case.text.strip()
            st.session_state.result = None
            st.rerun()

    st.divider()
    st.markdown("### 🆘 Emergency Contacts")
    st.markdown(
        """
| Service | Number |
|---------|--------|
| Cyber Helpline | **1930** |
| Childline | **1098** |
| Emergency | **112** |
| Women Helpline | **1091** |
"""
    )
    st.divider()
    st.caption("⚠️ This tool uses mock/synthetic data only. Not a substitute for professional law enforcement.")


# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

st.markdown("# 🛡️ Child Online Safety Monitor")
st.markdown(
    "A first-response tool for **parents, teachers, and child-protection workers** to identify grooming warning signs, "
    "understand applicable law, and generate a ready-to-submit incident report — all without re-exposing harmful content."
)

render_do_not_reopen_banner()

st.divider()

# ── Input section ──
col_input, col_meta = st.columns([3, 1])

with col_input:
    st.markdown("### 📝 Input: Paste Behavioural Description or Chat Excerpt")
    st.caption(
        "Paste either: (a) a description of concerning behavioural changes, or (b) a mock/anonymised chat excerpt. "
        "Use the sidebar sample cases to demo instantly."
    )
    input_text = st.text_area(
        label="Input text",
        value=st.session_state.input_text,
        height=220,
        placeholder="Paste behavioural notes or chat excerpt here…\n\nExample: 'Student has become secretive about phone, mentions a new online friend who sends gifts…'",
        label_visibility="collapsed",
        key="main_input",
    )
    st.session_state.input_text = input_text

with col_meta:
    st.markdown("### 👤 Reporter Context")
    st.caption("Optional — included in report")
    reporter_role = st.selectbox(
        "Your role",
        ["Parent / Guardian", "Teacher / School Counsellor", "NGO / Child-Protection Worker", "Healthcare Professional", "Other"],
        key="reporter_role",
    )
    reporter_notes = st.text_area(
        "Additional notes",
        placeholder="e.g. Discovered on child's device, 14-year-old girl, Delhi",
        height=120,
        key="reporter_notes",
        label_visibility="visible",
    )
    st.session_state.reporter_context = f"**Reporter Role:** {reporter_role}\n\n**Notes:** {reporter_notes}"

st.markdown("")

btn_col, _ = st.columns([1, 3])
with btn_col:
    analyse_clicked = st.button("🔍 Analyse Now", type="primary", use_container_width=True)

if analyse_clicked:
    if not input_text or len(input_text.strip()) < 10:
        st.warning("Please paste at least a sentence of text before analysing.")
    else:
        with st.spinner("Analysing for grooming indicators…"):
            st.session_state.result = analyse_text(input_text)

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

result: AnalysisResult | None = st.session_state.result

if result is not None:
    st.divider()

    if result.risk_level == "Critical":
        render_critical_banner()

    # ── Risk overview ──
    st.markdown("## 📊 Analysis Results")

    r_col1, r_col2, r_col3 = st.columns([1, 1, 2])

    with r_col1:
        render_score_gauge(result.risk_score, result.risk_level)

    with r_col2:
        st.markdown("**Risk Level**")
        render_risk_badge(result.risk_level)
        st.markdown(f"<br>**Input Type:** {result.input_type.capitalize()}", unsafe_allow_html=True)
        st.markdown(f"**Signs Found:** {len(result.warning_signs)}")

    with r_col3:
        st.markdown("**Summary**")
        st.info(result.summary)

    st.divider()

    # ── Tabs for detail sections ──
    tab1, tab2, tab3, tab4 = st.tabs([
        "⚠️ Warning Signs",
        "⚖️ Legal Provisions",
        "🔒 Evidence Preservation",
        "📄 Download Report",
    ])

    with tab1:
        st.markdown("### Grooming Warning Signs Detected")
        st.caption(
            "Each indicator below was matched against known grooming/predatory behaviour patterns. "
            "Multiple indicators in the same interaction significantly increase risk."
        )
        render_warning_signs(result)

    with tab2:
        st.markdown("### Applicable Legal Provisions")
        st.caption(
            "These sections of Indian law are relevant based on the indicators found. "
            "A qualified legal professional or law enforcement officer should be consulted."
        )
        render_legal_mappings(result)
        st.info(
            "📌 **Mandatory Reporting (POCSO §19):** Any person with knowledge of a sexual offence against a child "
            "is legally obligated to report it. Failure to do so is itself an offence."
        )

    with tab3:
        st.markdown("### Evidence Preservation Steps")
        st.caption(
            "Follow these steps carefully. Incorrect handling of digital evidence can render it inadmissible in court."
        )
        render_do_not_reopen_banner()
        render_preservation_steps(result)

    with tab4:
        st.markdown("### Download Incident Report")
        st.markdown(
            "This auto-filled report follows the **cybercrime.gov.in** and **CyberTipline** format. "
            "It contains **no harmful content** — only metadata, indicators, and legal references."
        )

        md_report = generate_markdown_report(result, st.session_state.reporter_context)

        col_dl1, col_dl2 = st.columns(2)

        with col_dl1:
            st.download_button(
                label="⬇️ Download as Markdown (.md)",
                data=md_report.encode("utf-8"),
                file_name="cosm_incident_report.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with col_dl2:
            try:
                pdf_bytes = generate_pdf_bytes(md_report)
                st.download_button(
                    label="⬇️ Download as PDF",
                    data=pdf_bytes,
                    file_name="cosm_incident_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception:
                st.info("PDF generation requires `reportlab`. Install via `pip install reportlab` for PDF export.")

        st.divider()
        st.markdown("**Report Preview:**")
        with st.expander("Click to preview report content", expanded=False):
            st.markdown(md_report)


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown(
    """
<div class="cosm-footer">
    🛡️ Child Online Safety Monitor (COSM) &nbsp;|&nbsp;
    IBM Bob Hackathon 2025 &nbsp;|&nbsp;
    Team: Phantom Rizzlers &nbsp;|&nbsp;
    Mock data only — not a substitute for professional law enforcement<br>
    Emergency: <strong>112</strong> &nbsp;|&nbsp; Childline: <strong>1098</strong> &nbsp;|&nbsp; Cyber Helpline: <strong>1930</strong>
</div>
""",
    unsafe_allow_html=True,
)
