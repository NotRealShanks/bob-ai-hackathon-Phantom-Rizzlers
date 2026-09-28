"""
ui/components.py — Shared CSS injection and render helper functions for COSM.

All pages import from here; no page should duplicate rendering logic.
"""
from __future__ import annotations

from typing import Callable

import streamlit as st

from models.assessment import CombinedAssessment, SignalItem
from models.case import CaseRecord


# ---------------------------------------------------------------------------
# Severity colour map — handles both old vocabulary and new
# ---------------------------------------------------------------------------

_SEVERITY_COLOURS: dict[str, tuple[str, str, str]] = {
    # New vocabulary (from AIAssessment.concern_level)
    "LOW":                    ("#d1fae5", "#065f46", "🟢"),
    "MODERATE":               ("#fef9c3", "#854d0e", "🟡"),
    "HIGH":                   ("#ffedd5", "#9a3412", "🟠"),
    "URGENT_SAFETY_CONCERN":  ("#fee2e2", "#991b1b", "🔴"),
    # Old vocabulary (from DeterministicResult.risk_level) — kept for backward compat
    "Low":      ("#d1fae5", "#065f46", "🟢"),
    "Medium":   ("#fef9c3", "#854d0e", "🟡"),
    "High":     ("#ffedd5", "#9a3412", "🟠"),
    "Critical": ("#fee2e2", "#991b1b", "🔴"),
}

_SEVERITY_LABELS: dict[str, str] = {
    "LOW":                   "LOW",
    "MODERATE":              "MODERATE",
    "HIGH":                  "HIGH",
    "URGENT_SAFETY_CONCERN": "URGENT SAFETY CONCERN",
    "Low":      "LOW",
    "Medium":   "MODERATE",
    "High":     "HIGH",
    "Critical": "URGENT SAFETY CONCERN",
}

_BADGE_CSS_CLASS: dict[str, str] = {
    "LOW":                   "badge-low",
    "MODERATE":              "badge-medium",
    "HIGH":                  "badge-high",
    "URGENT_SAFETY_CONCERN": "badge-critical",
    "Low":      "badge-low",
    "Medium":   "badge-medium",
    "High":     "badge-high",
    "Critical": "badge-critical",
}


def severity_colour(severity: str) -> tuple[str, str, str]:
    """Return (bg_hex, fg_hex, emoji) for the given severity string."""
    return _SEVERITY_COLOURS.get(severity, ("#f7f8fa", "#57606a", "⚪"))


# ---------------------------------------------------------------------------
# CSS injection
# ---------------------------------------------------------------------------

def inject_css() -> None:
    """Inject the shared CSS block via st.markdown (unsafe_allow_html=True)."""
    st.markdown(
        """
<style>
/* ── Global ── */
html, body, [class*="css"] {
    font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
}

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
    padding: 16px 20px;
    border-radius: 0 6px 6px 0;
    margin-bottom: 16px;
    font-size: 0.94rem;
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

/* ── Safety plan ── */
.safety-plan-container {
    background: #ffffff;
    border-left: 4px solid #3b82d4;
    border-radius: 0 8px 8px 0;
    padding: 20px 24px;
    margin-bottom: 16px;
    border: 1px solid #bfdbfe;
    border-left-width: 4px;
    border-left-color: #3b82d4;
}
.safety-plan-section {
    background: #f7f8fa;
    border-radius: 6px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 0.90rem;
    color: #374151;
}
.safety-plan-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #1e3a8a;
    margin-bottom: 4px;
}
.safety-plan-label {
    font-size: 0.80rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #57606a;
    margin-bottom: 4px;
    margin-top: 10px;
}

/* ── Case row ── */
.case-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 0;
    border-bottom: 1px solid #e5e7eb;
    font-size: 0.91rem;
    color: #1f2328;
}
.case-row:hover { background: #f7f8fa; }

/* ── Metric card ── */
.metric-card {
    background: #f7f8fa;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 16px 20px;
    text-align: center;
}
.metric-value {
    font-size: 2.2rem;
    font-weight: 800;
    color: #1f2328;
    line-height: 1.1;
}
.metric-label {
    font-size: 0.78rem;
    color: #57606a;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-top: 2px;
}

/* ── Demo mode notice ── */
.demo-notice {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 0.82rem;
    color: #1e40af;
    margin-bottom: 12px;
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

/* ── Button width ── */
[data-testid="stButton"] button {
    border-radius: 8px;
}
</style>
""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Severity badge
# ---------------------------------------------------------------------------

def render_severity_badge(severity: str) -> None:
    """Render a coloured pill badge for the given severity."""
    css_cls = _BADGE_CSS_CLASS.get(severity, "badge-low")
    label = _SEVERITY_LABELS.get(severity, severity)
    _, _, emoji = severity_colour(severity)
    st.markdown(
        f'<span class="badge {css_cls}">{emoji} {label}</span>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Banners
# ---------------------------------------------------------------------------

def render_urgent_banner() -> None:
    """Render the full-width red urgent/emergency banner with contacts."""
    st.markdown(
        """<div class="critical-banner">
🚨 <strong>URGENT SAFETY CONCERN</strong> — If your child is in immediate danger, act now.<br><br>
📞 <strong>Emergency: 112</strong> &nbsp;|&nbsp;
📞 <strong>Childline: 1098</strong> &nbsp;|&nbsp;
📞 <strong>Cyber Helpline: 1930</strong> &nbsp;|&nbsp;
🌐 <strong>cybercrime.gov.in</strong><br><br>
Do NOT wait. If you believe your child is at immediate risk of physical harm, call <strong>112</strong> now.
</div>""",
        unsafe_allow_html=True,
    )


def render_do_not_reopen_banner() -> None:
    """Render the amber 'Do NOT re-open the original content' warning banner."""
    st.markdown(
        """<div class="warning-banner">
🔒 <strong>Do NOT re-open, re-read, or share the original content.</strong>
Viewing it again may harm the child further and compromise legal evidence integrity.
Evidence must be preserved through official channels only.
</div>""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Signal / legal / step cards
# ---------------------------------------------------------------------------

def render_signal_card(signal) -> None:
    """
    Render a single safety signal as a card.
    Accepts either SignalItem (from AI) or WarningSigns (from deterministic engine).
    Both have a .signal/.sign and .explanation attribute.
    """
    # SignalItem uses .signal; WarningSigns (from analyzer) uses .sign
    title = getattr(signal, "signal", None) or getattr(signal, "sign", "Signal")
    explanation = getattr(signal, "explanation", "")
    severity = getattr(signal, "severity", "")
    category = getattr(signal, "category", "")  # deterministic only

    # Choose colour based on severity
    sev_lower = severity.lower() if severity else ""
    cat_colour = {
        "behavioural": "#7c5cd8",
        "communication": "#d97706",
        "digital": "#2563eb",
    }.get(category, "#57606a")

    if sev_lower == "serious":
        icon = "🔴"
    elif sev_lower == "concerning":
        icon = "🟠"
    else:
        icon = "🟡"

    # Build secondary label
    secondary_parts = []
    if category:
        secondary_parts.append(f'<span style="color:{cat_colour};">● {category}</span>')
    if severity:
        secondary_parts.append(severity)
    secondary_html = " &nbsp;·&nbsp; ".join(secondary_parts) if secondary_parts else ""

    st.markdown(
        f"""<div class="sign-card">
  <div class="sign-title">{icon} {title}</div>
  {f'<div class="sign-cat">{secondary_html}</div>' if secondary_html else ''}
  <div class="sign-expl">{explanation}</div>
</div>""",
        unsafe_allow_html=True,
    )


def render_legal_card(lm) -> None:
    """Render a single LegalMapping as a card."""
    act = getattr(lm, "act", "")
    section = getattr(lm, "section", "")
    description = getattr(lm, "description", "")
    max_penalty = getattr(lm, "max_penalty", "")
    st.markdown(
        f"""<div class="legal-card">
  <div class="legal-title">⚖️ {act} — {section}</div>
  <div class="legal-desc">{description}</div>
  <div class="legal-penalty">🔒 Max Penalty: {max_penalty}</div>
</div>""",
        unsafe_allow_html=True,
    )


def render_step_card(text: str) -> None:
    """Render a single evidence/action step as a green step card."""
    st.markdown(f'<div class="step-card">✅ {text}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Safety Plan — the centrepiece component
# ---------------------------------------------------------------------------

def render_safety_plan(combined: CombinedAssessment) -> None:
    """
    Render the full Personalized Safety Plan card.
    Uses AI assessment data primarily; falls back to deterministic signals when AI unavailable.
    """
    ai = combined.ai
    det = combined.deterministic
    severity = combined.final_severity
    _, _, emoji = severity_colour(severity)
    label = _SEVERITY_LABELS.get(severity, severity)

    ai_unavailable = bool(ai.error_note)

    st.markdown(
        f"""<div class="safety-plan-container">
  <div class="safety-plan-title">🛡️ Your Personalized Safety Plan</div>
  <div style="margin-top:6px;">
    <span class="badge {_BADGE_CSS_CLASS.get(severity, 'badge-low')}">{emoji} {label}</span>
  </div>
</div>""",
        unsafe_allow_html=True,
    )

    if ai_unavailable:
        st.warning(
            "ℹ️ AI assessment unavailable — showing pattern-matched safety indicators only. "
            "Configure WATSONX_API_KEY and WATSONX_PROJECT_ID for AI-powered analysis."
        )

    # ── What we noticed ──
    signals_to_show = ai.safety_signals if ai.safety_signals else []
    det_signs = det.warning_signs if det.warning_signs else []

    if signals_to_show or det_signs:
        st.markdown('<div class="safety-plan-label">⚠️ What we noticed</div>', unsafe_allow_html=True)
        for sig in signals_to_show:
            render_signal_card(sig)
        if not signals_to_show and det_signs:
            for sign in det_signs:
                render_signal_card(sign)

    # ── Why this matters ──
    why = ai.why_this_matters if not ai_unavailable else det.summary
    if why:
        st.markdown('<div class="safety-plan-label">💡 Why this matters</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="safety-plan-section">{why}</div>', unsafe_allow_html=True)

    # ── What you can do now ──
    actions = ai.recommended_actions if not ai_unavailable else []
    if actions:
        st.markdown('<div class="safety-plan-label">✅ What you can do now</div>', unsafe_allow_html=True)
        for action in actions:
            render_step_card(action)

    # ── What to avoid ──
    avoid = ai.actions_to_avoid if not ai_unavailable else []
    if avoid:
        st.markdown('<div class="safety-plan-label">🚫 What to avoid</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="safety-plan-section"><ul style="margin:0;padding-left:20px;">'
            + "".join(f"<li>{a}</li>" for a in avoid)
            + "</ul></div>",
            unsafe_allow_html=True,
        )

    # ── Evidence guidance ──
    evidence = list(ai.evidence_guidance) if not ai_unavailable else []
    # Always augment with deterministic preservation steps
    for step in det.preservation_steps:
        if step not in evidence:
            evidence.append(step)
    if evidence:
        st.markdown('<div class="safety-plan-label">🔒 Evidence guidance</div>', unsafe_allow_html=True)
        render_do_not_reopen_banner()
        for step in evidence:
            render_step_card(step)

    # ── When to seek help ──
    escalation = ai.escalation_guidance if not ai_unavailable else ""
    if escalation:
        st.markdown('<div class="safety-plan-label">🆘 When to seek additional help</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="safety-plan-section">{escalation}</div>', unsafe_allow_html=True)

    st.markdown("")  # spacing


# ---------------------------------------------------------------------------
# Case row (Case History list)
# ---------------------------------------------------------------------------

def render_case_row(case: CaseRecord, on_open_callback: Callable) -> None:
    """
    Render one row/card in the Case History list.
    Shows: severity badge, category, created_at (formatted), case_status, "Open" button.
    on_open_callback is called with case.id when the Open button is clicked.
    """
    # Format date
    try:
        from datetime import datetime
        dt = datetime.strptime(case.created_at, "%Y-%m-%dT%H:%M:%SZ")
        date_str = dt.strftime("%d %b %Y")
    except Exception:
        date_str = case.created_at[:10] if case.created_at else "—"

    category = case.situation_category or "General"
    status = case.case_status.value if hasattr(case.case_status, "value") else str(case.case_status)
    _, fg, emoji = severity_colour(case.severity)
    css_cls = _BADGE_CSS_CLASS.get(case.severity, "badge-low")

    col_badge, col_cat, col_date, col_status, col_btn = st.columns([2, 3, 2, 2, 1])
    with col_badge:
        st.markdown(
            f'<span class="badge {css_cls}">{emoji} {_SEVERITY_LABELS.get(case.severity, case.severity)}</span>',
            unsafe_allow_html=True,
        )
    with col_cat:
        st.markdown(f"**{category}**")
    with col_date:
        st.markdown(date_str)
    with col_status:
        st.markdown(status)
    with col_btn:
        if st.button("Open →", key=f"open_case_{case.id}", use_container_width=True):
            on_open_callback(case.id)
