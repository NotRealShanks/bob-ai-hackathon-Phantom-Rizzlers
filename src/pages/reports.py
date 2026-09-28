"""
pages/reports.py — Generate and download incident report drafts.
"""
from __future__ import annotations

import streamlit as st


_DRAFT_DISCLAIMER = """
> ⚠️ **DRAFT REPORT — FOR REVIEW PURPOSES ONLY**
>
> This is a structured draft prepared to assist a human reporter.
> It is **NOT** a legal determination.
> It is **NOT** an official complaint or court submission.
> It has **NOT** been verified by law enforcement.
> It requires human review before any submission to authorities.
"""


def render() -> None:
    case_id = st.session_state.get("selected_case_id")

    # ── Back button ──
    back_col, _ = st.columns([2, 5])
    with back_col:
        if st.button("← Back to Case", key="reports_back_btn"):
            if case_id:
                st.session_state["page"] = "case_detail"
            else:
                st.session_state["page"] = "case_history"
            st.rerun()

    if not case_id:
        st.warning("No case selected. Please open a case from Case History first.")
        if st.button("📂 Go to Case History"):
            st.session_state["page"] = "case_history"
            st.rerun()
        return

    try:
        from services.case_service import get_case, save_report_draft
        case = get_case(case_id)
    except Exception as e:
        st.error(f"Unable to load case: {e}")
        return

    if case is None:
        st.error(f"Case {case_id!r} not found.")
        return

    st.markdown(f"# 📄 Incident Report Draft")
    st.markdown(f"Case: **{case.id}**")
    st.divider()

    # ── Prominent disclaimer (always shown) ──
    st.markdown(_DRAFT_DISCLAIMER)
    st.divider()

    # ── Generate / show report ──
    if not case.report_draft_md:
        st.info(
            "No report draft has been generated yet. "
            "Click below to generate one. The report will be saved with the case."
        )
        if st.button("📄 Generate Report Draft", type="primary", key="gen_report_btn"):
            try:
                from services.report_service import generate_markdown
                draft = generate_markdown(case)
                save_report_draft(case_id, draft)
                st.success("Report draft generated and saved.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to generate report: {e}")
    else:
        st.success("✅ Report draft is ready for download and review.")

        # ── Download buttons ──
        dl_col1, dl_col2, _ = st.columns([2, 2, 3])
        with dl_col1:
            st.download_button(
                label="⬇️ Download as Markdown (.md)",
                data=case.report_draft_md.encode("utf-8"),
                file_name=f"cosm_report_{case.id}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with dl_col2:
            try:
                from services.report_service import generate_pdf
                pdf_bytes = generate_pdf(case.report_draft_md)
                st.download_button(
                    label="⬇️ Download as PDF",
                    data=pdf_bytes,
                    file_name=f"cosm_report_{case.id}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception:
                st.info("Install `reportlab` for PDF export: `pip install reportlab`")

        # ── Regenerate button ──
        if st.button("🔄 Regenerate Report", key="regen_report_btn"):
            try:
                from services.report_service import generate_markdown
                from services.case_service import save_report_draft as _save
                draft = generate_markdown(case)
                _save(case_id, draft)
                st.success("Report regenerated.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to regenerate: {e}")

        st.divider()

        # ── Preview (collapsed by default) ──
        with st.expander("📖 Preview report content", expanded=False):
            st.markdown(case.report_draft_md)

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
