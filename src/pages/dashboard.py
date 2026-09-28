"""
pages/dashboard.py — COSM Dashboard page.

Shows summary metrics, recent cases, and a quick-start CTA.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

import streamlit as st

from ui.components import render_case_row


def _open_case(case_id: str) -> None:
    st.session_state["selected_case_id"] = case_id
    st.session_state["page"] = "case_detail"
    st.rerun()


def render() -> None:
    # ── Demo mode notice ──
    try:
        from services.ai_service import get_provider, MockProvider
        provider = get_provider()
        if isinstance(provider, MockProvider):
            st.markdown(
                '<div class="demo-notice">ℹ️ <strong>Demo Mode</strong> — AI assessment is simulated. '
                'Configure <code>WATSONX_API_KEY</code> and <code>WATSONX_PROJECT_ID</code> to enable live IBM watsonx AI.</div>',
                unsafe_allow_html=True,
            )
    except Exception:
        pass

    st.markdown("# 🛡️ Child Online Safety Monitor")
    st.markdown(
        "A first-response tool for **parents, caregivers, teachers, and child-protection workers** "
        "to assess concerning online situations, understand safety signals, and generate structured "
        "incident report drafts — without re-exposing harmful content."
    )
    st.divider()

    # ── Load cases ──
    try:
        from services.case_service import list_cases
        cases = list_cases(limit=50)
    except Exception:
        cases = []

    # ── Metrics ──
    total = len(cases)
    open_count = sum(
        1 for c in cases
        if (c.case_status.value if hasattr(c.case_status, "value") else c.case_status) == "Open"
    )
    high_urgent_count = sum(
        1 for c in cases
        if c.severity in ("HIGH", "URGENT_SAFETY_CONCERN", "High", "Critical")
    )
    # Cases this week
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    this_week = 0
    for c in cases:
        try:
            dt = datetime.strptime(c.created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            if dt >= week_ago:
                this_week += 1
        except Exception:
            pass

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{total}</div>'
            f'<div class="metric-label">Total Cases</div></div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{open_count}</div>'
            f'<div class="metric-label">Open Cases</div></div>',
            unsafe_allow_html=True,
        )
    with m3:
        colour = "#9a3412" if high_urgent_count > 0 else "#1f2328"
        st.markdown(
            f'<div class="metric-card"><div class="metric-value" style="color:{colour};">{high_urgent_count}</div>'
            f'<div class="metric-label">High / Urgent</div></div>',
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{this_week}</div>'
            f'<div class="metric-label">This Week</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("")

    # ── CTA ──
    cta_col, _ = st.columns([2, 3])
    with cta_col:
        if st.button("🔍 Start New Assessment", type="primary", use_container_width=True):
            # Reset assessment state
            st.session_state["assessment_step"] = 1
            st.session_state["assessment_input"] = ""
            st.session_state["combined_assessment"] = None
            st.session_state["saved_case_id"] = None
            st.session_state["page"] = "new_assessment"
            st.rerun()

    st.divider()

    # ── Recent cases ──
    st.markdown("## 📂 Recent Cases")

    if not cases:
        st.info(
            "No cases saved yet. Run your first assessment to get started.\n\n"
            "Use the **sample cases** in the sidebar to try a demo instantly."
        )
        col_cta, _ = st.columns([2, 3])
        with col_cta:
            if st.button("▶️ Load a Demo Case", use_container_width=True):
                st.session_state["assessment_step"] = 1
                st.session_state["page"] = "new_assessment"
                st.rerun()
    else:
        recent = cases[:5]
        # Column headers
        hcols = st.columns([2, 3, 2, 2, 1])
        with hcols[0]:
            st.caption("**Severity**")
        with hcols[1]:
            st.caption("**Category**")
        with hcols[2]:
            st.caption("**Date**")
        with hcols[3]:
            st.caption("**Status**")
        with hcols[4]:
            st.caption("")
        st.markdown('<hr style="margin:4px 0 0 0;border:none;border-top:1px solid #e5e7eb;">', unsafe_allow_html=True)

        for case in recent:
            render_case_row(case, _open_case)

        if len(cases) > 5:
            st.caption(f"Showing 5 of {len(cases)} cases.")
            if st.button("📂 View All Cases"):
                st.session_state["page"] = "case_history"
                st.rerun()

    st.divider()

    # ── Footer ──
    st.markdown(
        """
<div class="cosm-footer">
    🛡️ Child Online Safety Monitor (COSM) &nbsp;|&nbsp;
    IBM Bob Hackathon 2025 &nbsp;|&nbsp; Team: Phantom Rizzlers &nbsp;|&nbsp;
    Mock/demo data only — not a substitute for professional law enforcement<br>
    Emergency: <strong>112</strong> &nbsp;|&nbsp; Childline: <strong>1098</strong> &nbsp;|&nbsp; Cyber Helpline: <strong>1930</strong>
</div>
""",
        unsafe_allow_html=True,
    )
