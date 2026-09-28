"""
pages/new_assessment.py — Two-step assessment flow.

Step 1: Parent describes the situation.
Step 2: AI + deterministic results, Safety Plan, tabs, save case.
"""
from ui.components import render_legal_card
# pyrefly: ignore [invalid-syntax]
from __future__ import annotations

import streamlit as st

from ui.components import (
    render_do_not_reopen_banner,
    render_urgent_banner,
    render_severity_badge,
    render_signal_card,
    render_step_card,
    render_safety_plan,
)
from sample_cases import SAMPLE_CASES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reset_assessment() -> None:
    """Clear all assessment session state and return to Step 1."""
    st.session_state["assessment_step"] = 1
    st.session_state["assessment_input"] = ""
    st.session_state["assessment_role"] = "Parent / Guardian"
    st.session_state["assessment_immediate"] = False
    st.session_state["assessment_notes"] = ""
    st.session_state["combined_assessment"] = None
    st.session_state["saved_case_id"] = None


def _run_assessment(description: str, immediate: bool) -> None:
    """Run both deterministic + AI assessment and store CombinedAssessment."""
    from services.safety_rules import analyse
    from services.ai_service import assess
    from models.assessment import CombinedAssessment

    det = analyse(description)
    ai_result = assess(description, immediate)
    combined = CombinedAssessment(
        ai=ai_result,
        deterministic=det,
        immediate_safety_concern=immediate,
    )
    st.session_state["combined_assessment"] = combined
    st.session_state["assessment_step"] = 2


# ---------------------------------------------------------------------------
# Step 1: Input form
# ---------------------------------------------------------------------------

def _render_step1() -> None:
    st.markdown("# 🔍 New Safety Assessment")
    st.markdown(
        "Describe what you have observed or what your child has experienced online. "
        "You do not need to provide images, videos, or harmful content."
    )

    render_do_not_reopen_banner()

    st.divider()

    # ── Demo mode notice ──
    try:
        from services.ai_service import get_provider, MockProvider
        if isinstance(get_provider(), MockProvider):
            st.markdown(
                '<div class="demo-notice">ℹ️ <strong>Demo Mode</strong> — AI is simulated. '
                'Add <code>WATSONX_API_KEY</code> to enable live IBM watsonx AI.</div>',
                unsafe_allow_html=True,
            )
    except Exception:
        pass

    col_main, col_meta = st.columns([3, 1])

    with col_main:
        st.markdown("### 📝 Describe the situation")
        st.caption(
            "Describe behavioural changes you've noticed, concerning messages you've seen, "
            "or anything that has made you worried about your child's online safety. "
            "You do not need to quote harmful content word-for-word."
        )

        description = st.text_area(
            label="Situation description",
            value=st.session_state.get("assessment_input", ""),
            height=220,
            placeholder=(
                "Example: 'My 13-year-old daughter has become very secretive about her phone. "
                "She mentioned a new online friend who sends her gifts. She deleted messages "
                "when I came near and said I wouldn't understand the friendship…'"
            ),
            label_visibility="collapsed",
            key="new_assessment_input",
        )
        st.session_state["assessment_input"] = description

        # Immediate safety concern checkbox
        immediate = st.checkbox(
            "⚠️ I believe my child may be in **IMMEDIATE danger** right now",
            value=st.session_state.get("assessment_immediate", False),
            key="new_assessment_immediate",
        )
        st.session_state["assessment_immediate"] = immediate

        if immediate:
            render_urgent_banner()

        st.markdown("")
        st.markdown("### 📋 Optional notes")
        notes = st.text_area(
            "Additional context (optional)",
            value=st.session_state.get("assessment_notes", ""),
            height=80,
            placeholder="E.g. child's age, platform involved, how you discovered this",
            key="new_assessment_notes",
        )
        st.session_state["assessment_notes"] = notes

    with col_meta:
        st.markdown("### 👤 Your role")
        role = st.selectbox(
            "Reporter role",
            [
                "Parent / Guardian",
                "Teacher / School Counsellor",
                "NGO / Child-Protection Worker",
                "Healthcare Professional",
                "Other",
            ],
            index=["Parent / Guardian", "Teacher / School Counsellor",
                   "NGO / Child-Protection Worker", "Healthcare Professional", "Other"]
                   .index(st.session_state.get("assessment_role", "Parent / Guardian")),
            key="new_assessment_role",
        )
        st.session_state["assessment_role"] = role

        st.markdown("")
        st.markdown("### 🎭 Load a demo case")
        st.caption("Click to pre-fill the form instantly")
        risk_emoji = {"Low": "🟢", "Medium": "🟡", "High": "🟠", "Critical": "🔴"}
        for i, case in enumerate(SAMPLE_CASES):
            em = risk_emoji.get(case.expected_risk, "⚪")
            if st.button(f"{em} {case.title}", key=f"sample_case_{i}", use_container_width=True):
                st.session_state["assessment_input"] = case.text.strip()
                st.session_state["assessment_role"] = case.persona if case.persona in [
                    "Parent / Guardian", "Teacher / School Counsellor",
                    "NGO / Child-Protection Worker", "Healthcare Professional",
                ] else "Other"
                st.session_state["assessment_immediate"] = False
                st.session_state["assessment_notes"] = f"Demo case: {case.label} — persona: {case.persona}"
                st.rerun()

    st.markdown("")
    btn_col, _ = st.columns([1, 3])
    with btn_col:
        analyse_clicked = st.button(
            "🔍 Run Assessment →",
            type="primary",
            use_container_width=True,
            key="run_assessment_btn",
        )

    if analyse_clicked:
        desc = st.session_state.get("assessment_input", "").strip()
        if len(desc) < 20:
            st.warning("Please provide at least a sentence describing the situation (minimum 20 characters).")
        else:
            with st.spinner("Analysing situation — please wait…"):
                _run_assessment(desc, st.session_state.get("assessment_immediate", False))
            st.rerun()


# ---------------------------------------------------------------------------
# Step 2: Results
# ---------------------------------------------------------------------------

def _render_step2() -> None:
    combined = st.session_state.get("combined_assessment")
    if combined is None:
        st.error("No assessment found. Please start a new assessment.")
        if st.button("← Start New Assessment"):
            _reset_assessment()
            st.rerun()
        return

    ai = combined.ai
    det = combined.deterministic
    severity = combined.final_severity
    immediate = combined.immediate_safety_concern

    # ── URGENT banner — ALWAYS at top if immediate concern or critical severity ──
    if immediate or severity == "URGENT_SAFETY_CONCERN":
        render_urgent_banner()

    # ── Header ──
    st.markdown("# 📊 Assessment Results")
    col_badge, col_info = st.columns([2, 5])
    with col_badge:
        render_severity_badge(severity)
    with col_info:
        category = ai.situation_category or det.input_type.capitalize() or "General"
        st.markdown(f"**Category:** {category}")
        if ai.confidence and not ai.error_note:
            st.caption(f"AI Confidence: {ai.confidence}")

    # ── Demo / error notice ──
    if ai.error_note:
        st.warning(
            f"⚠️ Running in demo mode — AI assessment unavailable. "
            f"Showing pattern-matched indicators only. ({ai.error_note})"
        )
    else:
        # Show demo mode notice
        try:
            from services.ai_service import get_provider, MockProvider
            if isinstance(get_provider(), MockProvider):
                st.info(
                    "ℹ️ Running in Demo Mode — AI assessment is simulated. "
                    "Configure WATSONX_API_KEY to enable live IBM watsonx AI."
                )
        except Exception:
            pass

    # ── Uncertainty note ──
    if ai.uncertainty_note and not ai.error_note:
        st.caption(f"ℹ️ {ai.uncertainty_note}")

    # ── Situation summary ──
    if ai.situation_summary and not ai.error_note:
        st.info(f"**Summary:** {ai.situation_summary}")
    elif det.summary:
        st.info(f"**Pattern analysis summary:** {det.summary}")

    st.divider()

    # ── Safety Plan — the centrepiece ──
    render_safety_plan(combined)

    st.divider()

    # ── Tabs ──
    tab_signals, tab_legal, tab_evidence, tab_save = st.tabs([
        "⚠️ Safety Signals",
        "⚖️ Legal Context",
        "🔒 Evidence Guidance",
        "📄 Save & Report",
    ])

    with tab_signals:
        st.markdown("### Safety Signals")
        st.caption(
            "These signals were identified in the description you provided. "
            "Multiple signals together increase concern levels. "
            "No single signal confirms that a crime occurred."
        )

        ai_signals = ai.safety_signals if not ai.error_note else []
        det_signs = det.warning_signs or []

        if ai_signals:
            if not ai.error_note:
                st.markdown("**AI-assessed signals:**")
            for sig in ai_signals:
                render_signal_card(sig)

        if det_signs:
            st.markdown("**Pattern-matched indicators:**")
            for sign in det_signs:
                render_signal_card(sign)

        if not ai_signals and not det_signs:
            st.success("No specific safety signals were detected in this description.")

    with tab_legal:
        st.markdown("### Potentially Relevant Legal Context")
        st.info(
            "📌 The following legal provisions are provided as **potentially relevant information only**. "
            "They are NOT a legal determination. No crime has been confirmed based on this description alone. "
            "Consult a qualified legal professional or law enforcement for advice."
        )

        if ai.legal_context_note and not ai.error_note:
            st.markdown(ai.legal_context_note)
            st.divider()

        if det.legal_mappings:
            st.markdown("**Provisions flagged by pattern analysis:**")
            for lm in det.legal_mappings:
                render_legal_card(lm)
        else:
            st.info("No specific legal provisions were flagged at this concern level.")

        st.info(
            "📌 **Mandatory Reporting (POCSO §19):** Any person with knowledge of a sexual offence "
            "against a child is legally obligated to report it. Failure to do so is itself an offence."
        )

    with tab_evidence:
        st.markdown("### Evidence Preservation Guidance")
        st.caption(
            "Follow these steps carefully. Incorrect handling of digital evidence can affect its usefulness "
            "for law enforcement. Only preserve what is already available to you."
        )
        render_do_not_reopen_banner()

        evidence_items = list(ai.evidence_guidance) if not ai.error_note else []
        for step in det.preservation_steps:
            if step not in evidence_items:
                evidence_items.append(step)

        if evidence_items:
            for step in evidence_items:
                render_step_card(step)
        else:
            st.info("No specific evidence steps at this concern level.")

        if ai.reporting_guidance and not ai.error_note:
            st.markdown("### Reporting Guidance")
            for item in ai.reporting_guidance:
                render_step_card(item)

    with tab_save:
        st.markdown("### Save this Case")

        saved_id = st.session_state.get("saved_case_id")

        if not saved_id:
            st.markdown(
                "Save this assessment to your Case History so you can review it later, "
                "update its status, and generate a report draft."
            )

            if st.button("💾 Save to Case History", type="primary", key="save_case_btn"):
                try:
                    from services.case_service import create_case
                    case = create_case(
                        reporter_role=st.session_state.get("assessment_role", "Parent / Guardian"),
                        situation_summary=st.session_state.get("assessment_input", ""),
                        combined=combined,
                        reporter_notes=st.session_state.get("assessment_notes", ""),
                    )
                    st.session_state["saved_case_id"] = case.id
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save case: {e}")
        else:
            st.success(f"✅ Case saved: **{saved_id}**")
            col_v, col_r, _ = st.columns([2, 2, 3])
            with col_v:
                if st.button("📂 View Case", use_container_width=True):
                    st.session_state["selected_case_id"] = saved_id
                    st.session_state["page"] = "case_detail"
                    st.rerun()
            with col_r:
                if st.button("📄 Generate Report", use_container_width=True):
                    st.session_state["selected_case_id"] = saved_id
                    st.session_state["page"] = "reports"
                    st.rerun()

    st.divider()

    # ── Footer ──
    if ai.disclaimer and not ai.error_note:
        st.caption(f"ℹ️ {ai.disclaimer}")

    if st.button("← Start New Assessment", key="start_new_btn"):
        _reset_assessment()
        st.rerun()

    st.markdown(
        """
<div class="cosm-footer">
    🛡️ COSM &nbsp;|&nbsp; IBM Bob Hackathon 2025 &nbsp;|&nbsp; Team: Phantom Rizzlers<br>
    Emergency: <strong>112</strong> &nbsp;|&nbsp; Childline: <strong>1098</strong> &nbsp;|&nbsp; Cyber Helpline: <strong>1930</strong>
</div>
""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Page entry-point
# ---------------------------------------------------------------------------

def render() -> None:
    step = st.session_state.get("assessment_step", 1)
    if step == 1:
        _render_step1()
    else:
        _render_step2()
