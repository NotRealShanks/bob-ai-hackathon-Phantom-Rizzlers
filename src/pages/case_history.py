"""
pages/case_history.py — Case History list page.
"""
from __future__ import annotations

import streamlit as st

from ui.components import render_case_row


def _open_case(case_id: str) -> None:
    st.session_state["selected_case_id"] = case_id
    st.session_state["page"] = "case_detail"
    st.rerun()


def render() -> None:
    st.markdown("# 📂 Case History")
    st.markdown("Review previously saved assessments, update case status, and generate report drafts.")
    st.divider()

    # ── Filters ──
    fcol1, fcol2, _ = st.columns([2, 2, 3])
    with fcol1:
        status_options = ["All", "Open", "Under Review", "Report Prepared", "Resolved"]
        status_filter = st.selectbox("Filter by status", status_options, key="ch_status_filter")
    with fcol2:
        severity_options = ["All", "URGENT_SAFETY_CONCERN", "HIGH", "MODERATE", "LOW"]
        sev_filter = st.selectbox("Filter by severity", severity_options, key="ch_sev_filter")

    # ── Load cases ──
    try:
        from services.case_service import list_cases
        filter_arg = None if status_filter == "All" else status_filter
        cases = list_cases(limit=100, status_filter=filter_arg)
    except Exception as e:
        st.error(f"Unable to load cases: {e}")
        return

    # Apply severity filter client-side
    if sev_filter != "All":
        cases = [c for c in cases if c.severity == sev_filter]

    st.caption(f"Showing {len(cases)} case{'s' if len(cases) != 1 else ''}")

    if not cases:
        st.info(
            "No cases found with the selected filters.\n\n"
            "Start a new assessment to create your first case."
        )
        if st.button("🔍 New Assessment"):
            st.session_state["page"] = "new_assessment"
            st.rerun()
        return

    # ── Column headers ──
    hcols = st.columns([2, 3, 2, 2, 1])
    header_labels = ["**Severity**", "**Category**", "**Date**", "**Status**", ""]
    for col, label in zip(hcols, header_labels):
        with col:
            st.caption(label)
    st.markdown(
        '<hr style="margin:4px 0 0 0;border:none;border-top:1px solid #e5e7eb;">',
        unsafe_allow_html=True,
    )

    for case in cases:
        render_case_row(case, _open_case)

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
