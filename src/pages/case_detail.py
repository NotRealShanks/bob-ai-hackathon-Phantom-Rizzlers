"""
pages/case_detail.py — Single case detail view.
"""
from __future__ import annotations

import json

import streamlit as st

from ui.components import (
    render_severity_badge,
    render_urgent_banner,
    render_do_not_reopen_banner,
    render_signal_card,
    render_legal_card,
    render_step_card,
    render_safety_plan,
)
from models.case import CaseStatus


def _parse_json_safe(json_str: str, default):
    """Safely parse JSON; return default on error or empty input."""
    if not json_str:
        return default
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def _reconstruct_combined(case):
    """
    Attempt to reconstruct a CombinedAssessment from a CaseRecord's JSON fields.
    Returns None if reconstruction fails (e.g. missing data).
    """
    from models.assessment import (
        AIAssessment, DeterministicResult, CombinedAssessment, SignalItem,
        DETERMINISTIC_TO_SEVERITY, SEVERITY_ORDER,
    )

    # ── Reconstruct AIAssessment ──
    ai_data = _parse_json_safe(case.ai_assessment_json, {})
    if ai_data:
        raw_signals = ai_data.get("safety_signals", [])
        signals = []
        for s in raw_signals:
            if isinstance(s, dict):
                signals.append(SignalItem(
                    signal=s.get("signal", ""),
                    explanation=s.get("explanation", ""),
                    severity=s.get("severity", "informational"),
                ))
        ai = AIAssessment(
            concern_level=ai_data.get("concern_level", "LOW"),
            situation_category=ai_data.get("situation_category", ""),
            confidence=ai_data.get("confidence", "LOW"),
            uncertainty_note=ai_data.get("uncertainty_note", ""),
            situation_summary=ai_data.get("situation_summary", ""),
            safety_signals=signals,
            why_this_matters=ai_data.get("why_this_matters", ""),
            recommended_actions=ai_data.get("recommended_actions", []),
            actions_to_avoid=ai_data.get("actions_to_avoid", []),
            evidence_guidance=ai_data.get("evidence_guidance", []),
            reporting_guidance=ai_data.get("reporting_guidance", []),
            escalation_guidance=ai_data.get("escalation_guidance", ""),
            legal_context_note=ai_data.get("legal_context_note", ""),
            disclaimer=ai_data.get("disclaimer", ""),
            error_note=ai_data.get("error_note", ""),
        )
    else:
        # AI was unavailable when case was created
        from services.ai_service import _error_assessment
        ai = _error_assessment("AI assessment was not available when this case was created.")

    # ── Reconstruct DeterministicResult ──
    det_data = _parse_json_safe(case.deterministic_signals_json, {})

    # Rebuild warning_signs and legal_mappings from stored JSON
    from services.safety_rules import WarningSigns, LegalMapping
    warning_signs = []
    raw_ws = det_data.get("warning_signs", [])
    for ws in raw_ws:
        if isinstance(ws, dict):
            warning_signs.append(WarningSigns(
                sign=ws.get("sign", ""),
                category=ws.get("category", ""),
                explanation=ws.get("explanation", ""),
            ))

    legal_mappings = []
    raw_lm = det_data.get("legal_mappings", [])
    for lm in raw_lm:
        if isinstance(lm, dict):
            legal_mappings.append(LegalMapping(
                act=lm.get("act", ""),
                section=lm.get("section", ""),
                description=lm.get("description", ""),
                max_penalty=lm.get("max_penalty", ""),
            ))

    det = DeterministicResult(
        risk_level=det_data.get("risk_level", "Low"),
        risk_score=det_data.get("risk_score", 0),
        warning_signs=warning_signs,
        legal_mappings=legal_mappings,
        preservation_steps=det_data.get("preservation_steps", []),
        summary=det_data.get("summary", ""),
        input_type=det_data.get("input_type", "unknown"),
    )

    return CombinedAssessment(
        ai=ai,
        deterministic=det,
        immediate_safety_concern=case.immediate_safety_concern,
    )


def render() -> None:
    case_id = st.session_state.get("selected_case_id")

    # ── Back button ──
    if st.button("← Back to Case History", key="case_detail_back"):
        st.session_state["page"] = "case_history"
        st.rerun()

    if not case_id:
        st.warning("No case selected. Please open a case from Case History.")
        return

    try:
        from services.case_service import get_case, update_case_status
        case = get_case(case_id)
    except Exception as e:
        st.error(f"Unable to load case: {e}")
        return

    if case is None:
        st.error(f"Case {case_id!r} not found.")
        return

    # ── Urgent banner if needed ──
    if case.immediate_safety_concern or case.severity in ("URGENT_SAFETY_CONCERN", "Critical"):
        render_urgent_banner()

    # ── Header ──
    st.markdown(f"# 📋 Case {case.id}")
    col_badge, col_meta = st.columns([2, 5])
    with col_badge:
        render_severity_badge(case.severity)
    with col_meta:
        try:
            from datetime import datetime
            dt = datetime.strptime(case.created_at, "%Y-%m-%dT%H:%M:%SZ")
            date_str = dt.strftime("%d %B %Y, %H:%M UTC")
        except Exception:
            date_str = case.created_at
        st.markdown(
            f"**Opened:** {date_str} &nbsp;|&nbsp; "
            f"**Reporter:** {case.reporter_role} &nbsp;|&nbsp; "
            f"**Category:** {case.situation_category or 'General'}"
        )

    st.divider()

    # ── Status update ──
    status_col, update_col, _ = st.columns([2, 1, 4])
    current_status = case.case_status.value if hasattr(case.case_status, "value") else str(case.case_status)
    status_options = [s.value for s in CaseStatus]
    with status_col:
        new_status = st.selectbox(
            "Case Status",
            status_options,
            index=status_options.index(current_status) if current_status in status_options else 0,
            key="case_detail_status_sel",
        )
    with update_col:
        st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
        if st.button("Update Status", key="update_status_btn"):
            try:
                update_case_status(case_id, new_status)
                st.success(f"Status updated to **{new_status}**")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update status: {e}")

    # ── Report status ──
    st.caption(f"Report status: **{case.report_status}**")

    st.divider()

    # ── Reconstruct combined assessment ──
    try:
        combined = _reconstruct_combined(case)
        combined_ok = True
    except Exception as e:
        combined_ok = False
        combined_err = str(e)

    # ── Tabs ──
    tab_plan, tab_signals, tab_legal, tab_evidence, tab_report = st.tabs([
        "🛡️ Safety Plan",
        "⚠️ Signals",
        "⚖️ Legal Context",
        "🔒 Evidence",
        "📄 Report",
    ])

    with tab_plan:
        if combined_ok:
            render_safety_plan(combined)
        else:
            st.warning(f"Could not reconstruct safety plan: {combined_err}")
            # Fall back to signals JSON
            signals = _parse_json_safe(case.safety_signals_json, [])
            if signals:
                for sig in signals:
                    if isinstance(sig, dict):
                        st.markdown(f"- **{sig.get('signal', '')}**: {sig.get('explanation', '')}")

    with tab_signals:
        st.markdown("### Safety Signals")
        signals = _parse_json_safe(case.safety_signals_json, [])
        if signals:
            for sig in signals:
                if isinstance(sig, dict):
                    from models.assessment import SignalItem
                    render_signal_card(SignalItem(
                        signal=sig.get("signal", ""),
                        explanation=sig.get("explanation", ""),
                        severity=sig.get("severity", "informational"),
                    ))
        elif combined_ok and combined.deterministic.warning_signs:
            for sign in combined.deterministic.warning_signs:
                render_signal_card(sign)
        else:
            st.info("No signals recorded for this case.")

    with tab_legal:
        st.markdown("### Potentially Relevant Legal Context")
        st.info(
            "📌 The following is general information only. It is NOT legal advice. "
            "It does NOT confirm that any crime occurred."
        )
        if combined_ok and combined.ai.legal_context_note and not combined.ai.error_note:
            st.markdown(combined.ai.legal_context_note)
            st.divider()
        if combined_ok and combined.deterministic.legal_mappings:
            for lm in combined.deterministic.legal_mappings:
                render_legal_card(lm)
        else:
            st.info("No specific legal provisions recorded for this case.")

    with tab_evidence:
        st.markdown("### Evidence Preservation Guidance")
        render_do_not_reopen_banner()
        if combined_ok:
            evidence = list(combined.ai.evidence_guidance) if not combined.ai.error_note else []
            for step in combined.deterministic.preservation_steps:
                if step not in evidence:
                    evidence.append(step)
            if evidence:
                for step in evidence:
                    render_step_card(step)
            else:
                st.info("No specific evidence guidance recorded.")
        else:
            st.info("Evidence guidance not available for this case.")

    with tab_report:
        st.markdown("### Incident Report Draft")

        if case.report_draft_md:
            st.success("✅ A report draft has been generated for this case.")
            st.download_button(
                label="⬇️ Download as Markdown",
                data=case.report_draft_md.encode("utf-8"),
                file_name=f"cosm_report_{case.id}.md",
                mime="text/markdown",
                use_container_width=False,
            )
            try:
                from services.report_service import generate_pdf
                pdf_bytes = generate_pdf(case.report_draft_md)
                st.download_button(
                    label="⬇️ Download as PDF",
                    data=pdf_bytes,
                    file_name=f"cosm_report_{case.id}.pdf",
                    mime="application/pdf",
                    use_container_width=False,
                )
            except Exception:
                pass
            with st.expander("Preview report", expanded=False):
                st.markdown(case.report_draft_md)
        else:
            st.info("No report draft generated yet.")
            if st.button("📄 Generate Report Draft", key="gen_report_from_detail"):
                st.session_state["selected_case_id"] = case_id
                st.session_state["page"] = "reports"
                st.rerun()

    st.divider()
    st.markdown(
        """
<div class="cosm-footer">
    🛡️ COSM &nbsp;|&nbsp; IBM Bob Hackathon 2025 &nbsp;|&nbsp; Team: Phantom Rizzlers<br>
    Emergency: <strong>112</strong> &nbsp;|&nbsp; Childline: <strong>1098</strong> &nbsp;|&nbsp; Cyber Helpline: <strong>1930</strong>
</div>
""",
        unsafe_allow_html=True,
    )
