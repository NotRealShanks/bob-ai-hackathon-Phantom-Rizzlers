"""
app.py — Child Online Safety Monitor (COSM)
Streamlit application entry-point and page router.

Team: Phantom Rizzlers | IBM Bob Hackathon 2025 | Track: AI

IMPORTANT: This tool uses mock/synthetic data only. No real CSAM or
real victim data is ever processed, stored, or transmitted.
"""
from __future__ import annotations
import sys
import os

# Ensure src/ is on the path when running from repo root
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

# Load .env before any service imports
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from database import init_db
from ui.components import inject_css
from sample_cases import SAMPLE_CASES

# ── One-time startup ──
init_db()

st.set_page_config(
    page_title="Child Online Safety Monitor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# ── Session state defaults ──
_DEFAULTS = {
    "page": "dashboard",
    "assessment_step": 1,
    "assessment_input": "",
    "assessment_role": "Parent / Guardian",
    "assessment_immediate": False,
    "assessment_notes": "",
    "combined_assessment": None,
    "saved_case_id": None,
    "selected_case_id": None,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Sidebar ──
with st.sidebar:
    try:
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/IBM_logo.svg/320px-IBM_logo.svg.png",
            width=80,
        )
    except Exception:
        pass
    st.markdown("## 🛡️ COSM")
    st.markdown("**Child Online Safety Monitor**")
    st.markdown("*IBM Bob Hackathon 2025 — Phantom Rizzlers*")
    st.divider()

    # ── Demo mode indicator ──
    try:
        from services.ai_service import get_provider, MockProvider
        if isinstance(get_provider(), MockProvider):
            st.markdown(
                '<div class="demo-notice">ℹ️ Demo Mode — AI simulated</div>',
                unsafe_allow_html=True,
            )
    except Exception:
        pass

    # ── Navigation ──
    _NAV = {
        "dashboard":       "🏠 Dashboard",
        "new_assessment":  "🔍 New Assessment",
        "case_history":    "📂 Case History",
        "reports":         "📄 Reports",
        "safety_resources": "🆘 Safety Resources",
    }
    for _page_id, _label in _NAV.items():
        if st.button(_label, key=f"nav_{_page_id}", use_container_width=True):
            st.session_state["page"] = _page_id
            # Reset assessment state when navigating away from assessment
            if _page_id != "new_assessment":
                st.session_state["assessment_step"] = 1
                st.session_state["combined_assessment"] = None
                st.session_state["saved_case_id"] = None
            st.rerun()

    st.divider()

    # ── Sample demo cases ──
    st.markdown("### 📋 Demo Cases")
    st.caption("Click to load a sample case")
    _RISK_EMOJI = {"Low": "🟢", "Medium": "🟡", "High": "🟠", "Critical": "🔴"}
    for _i, _case in enumerate(SAMPLE_CASES):
        _em = _RISK_EMOJI.get(_case.expected_risk, "⚪")
        if st.button(f"{_em} {_case.title}", key=f"sidebar_sample_{_i}", use_container_width=True):
            st.session_state["assessment_input"] = _case.text.strip()
            st.session_state["assessment_notes"] = f"Demo: {_case.label} — {_case.persona}"
            st.session_state["assessment_immediate"] = False
            st.session_state["assessment_step"] = 1
            st.session_state["combined_assessment"] = None
            st.session_state["saved_case_id"] = None
            st.session_state["page"] = "new_assessment"
            st.rerun()

    st.divider()

    # ── Emergency contacts ──
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
    st.caption(
        "⚠️ This tool uses mock/synthetic data only. "
        "Not a substitute for professional law enforcement."
    )

# ── Page routing ──
_page = st.session_state.get("page", "dashboard")

if _page == "dashboard":
    from pages.dashboard import render
    render()
elif _page == "new_assessment":
    from pages.new_assessment import render
    render()
elif _page == "case_history":
    from pages.case_history import render
    render()
elif _page == "case_detail":
    from pages.case_detail import render
    render()
elif _page == "reports":
    from pages.reports import render
    render()
elif _page == "safety_resources":
    from pages.safety_resources import render
    render()
else:
    from pages.dashboard import render
    render()
