"""
services/report_service.py — Generates structured DRAFT incident reports for COSM cases.

Reports are refactored from report_generator.py but now accept a CaseRecord.

Key safety rules preserved from the original:
  - The situation_summary (raw parent description) is NOT included in the report.
  - No claim is made that any crime has definitely occurred.
  - Reports include a prominent DRAFT disclaimer at the top.
  - Evidence guidance explicitly warns against re-viewing content.
"""

from __future__ import annotations

import datetime
import json
from typing import List

from models.case import CaseRecord


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_json_list(json_str: str) -> List:
    """Safely parse a JSON array string; returns empty list on error."""
    if not json_str:
        return []
    try:
        result = json.loads(json_str)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _parse_ai_json(json_str: str) -> dict:
    """Safely parse the ai_assessment_json column; returns empty dict on error."""
    if not json_str:
        return {}
    try:
        result = json.loads(json_str)
        return result if isinstance(result, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


_SEVERITY_EMOJI = {
    "LOW": "🟢",
    "MODERATE": "🟡",
    "HIGH": "🟠",
    "URGENT_SAFETY_CONCERN": "🔴",
}

_SEVERITY_LABEL = {
    "LOW": "Low",
    "MODERATE": "Moderate",
    "HIGH": "High",
    "URGENT_SAFETY_CONCERN": "Urgent Safety Concern",
}


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def generate_markdown(case: CaseRecord) -> str:
    """
    Produce a structured DRAFT incident report in Markdown format.

    The report:
    - Includes a prominent DRAFT disclaimer at the top.
    - Does NOT include the original situation_summary text.
    - Does NOT claim any crime definitely occurred.
    - Includes case metadata, signals, actions, evidence guidance, contacts.
    - Includes reporter_notes if non-empty.
    """
    now = datetime.datetime.now()
    timestamp = now.strftime("%d %B %Y, %H:%M IST")
    report_id = f"RPT-{case.id[-8:]}-{now.strftime('%H%M%S')}"

    severity_emoji = _SEVERITY_EMOJI.get(case.severity, "⚪")
    severity_label = _SEVERITY_LABEL.get(case.severity, case.severity)

    safety_signals = _parse_json_list(case.safety_signals_json)
    recommended_actions = _parse_json_list(case.recommended_actions_json)

    ai_data = _parse_ai_json(case.ai_assessment_json)
    actions_to_avoid: List[str] = ai_data.get("actions_to_avoid", [])
    evidence_guidance: List[str] = ai_data.get("evidence_guidance", [])
    reporting_guidance: List[str] = ai_data.get("reporting_guidance", [])
    why_this_matters: str = ai_data.get("why_this_matters", "")
    legal_note: str = ai_data.get("legal_context_note", "")

    # Fall back to deterministic preservation steps if AI evidence guidance absent
    if not evidence_guidance:
        det_data = _parse_ai_json(case.deterministic_signals_json)
        evidence_guidance = det_data.get("preservation_steps", [])

    lines = [
        "# CHILD ONLINE SAFETY INCIDENT REPORT",
        "",
        "> ⚠️ DRAFT REPORT — FOR REVIEW PURPOSES ONLY",
        "> This is a structured draft prepared to assist a human reporter.",
        "> It is NOT a legal determination.",
        "> It is NOT an official complaint or court submission.",
        "> It has NOT been verified by law enforcement.",
        "> It requires human review before any submission to authorities.",
        "",
        "---",
        "",
        f"**Report ID:** `{report_id}`",
        f"**Generated:** {timestamp}",
        f"**Case ID:** `{case.id}`",
        f"**Tool:** Child Online Safety Monitor (COSM) v2 — Phantom Rizzlers / IBM Bob Hackathon",
        "",
        "---",
        "",
        "## 1. CASE SUMMARY",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| **Concern Level** | {severity_emoji} **{severity_label}** |",
        f"| **Situation Category** | {case.situation_category or 'Not determined'} |",
        f"| **Case Created** | {case.created_at} |",
        f"| **Reporter Role** | {case.reporter_role} |",
        f"| **Case Status** | {case.case_status.value if hasattr(case.case_status, 'value') else case.case_status} |",
        f"| **Immediate Safety Concern** | {'Yes' if case.immediate_safety_concern else 'No'} |",
        "",
        "> **Note:** The reporter's original description has been intentionally omitted from this report",
        "> to prevent re-exposure to potentially harmful content.",
        "",
        "---",
        "",
    ]

    # --- Why this matters ---
    if why_this_matters:
        lines += [
            "## 2. SITUATION CONTEXT",
            "",
            why_this_matters,
            "",
            "---",
            "",
        ]
        section_offset = 1
    else:
        section_offset = 0

    # --- Safety signals ---
    lines += [
        f"## {2 + section_offset}. SAFETY SIGNALS IDENTIFIED",
        "",
    ]
    if safety_signals:
        for i, sig in enumerate(safety_signals, 1):
            if isinstance(sig, dict):
                signal_name = sig.get("signal", f"Signal {i}")
                explanation = sig.get("explanation", "")
                severity = sig.get("severity", "informational")
                lines += [
                    f"### {i}. {signal_name}",
                    f"- **Severity:** {severity.capitalize()}",
                    f"- **Explanation:** {explanation}",
                    "",
                ]
            else:
                lines += [f"- {sig}", ""]
    else:
        lines += ["No specific signals were recorded for this case.", ""]

    lines += ["---", ""]

    # --- Recommended actions ---
    lines += [
        f"## {3 + section_offset}. RECOMMENDED ACTIONS",
        "",
    ]
    if recommended_actions:
        for action in recommended_actions:
            lines.append(f"- {action}")
        lines.append("")
    else:
        lines += ["No specific recommendations recorded.", ""]

    lines += ["---", ""]

    # --- Actions to avoid ---
    if actions_to_avoid:
        lines += [
            f"## {4 + section_offset}. ACTIONS TO AVOID",
            "",
        ]
        for action in actions_to_avoid:
            lines.append(f"- {action}")
        lines += ["", "---", ""]
        evidence_section = 5 + section_offset
    else:
        evidence_section = 4 + section_offset

    # --- Evidence guidance ---
    lines += [
        f"## {evidence_section}. EVIDENCE PRESERVATION GUIDANCE",
        "",
        "> ⚠️ Follow these steps carefully. Do NOT re-open or re-read harmful content.",
        "",
    ]
    if evidence_guidance:
        for step in evidence_guidance:
            lines.append(f"- {step}")
        lines.append("")
    else:
        lines += [
            "- Take screenshots of usernames and profile information, not harmful content.",
            "- Preserve any platform links or account URLs.",
            "- Store evidence in a password-protected location.",
            "- Do NOT delete any messages or accounts — they are potential evidence.",
            "",
        ]

    lines += ["---", ""]

    # --- Reporting contacts ---
    reporting_section = evidence_section + 1
    lines += [
        f"## {reporting_section}. REPORTING CONTACTS",
        "",
        "| Resource | Details |",
        "|----------|---------|",
        "| **National Cyber Crime Portal** | [cybercrime.gov.in](https://cybercrime.gov.in) |",
        "| **National Cyber Helpline** | 1930 |",
        "| **Childline India** | 1098 (24×7) |",
        "| **Emergency** | 112 |",
        "| **NCMEC CyberTipline** | [missingkids.org/gethelpnow/cybertipline](https://www.missingkids.org/gethelpnow/cybertipline) |",
        "| **iReport Portal (INTERPOL)** | [icse.interpol.int](https://icse.interpol.int) |",
        "",
    ]

    if reporting_guidance:
        lines += ["**Additional guidance:**", ""]
        for item in reporting_guidance:
            lines.append(f"- {item}")
        lines.append("")

    lines += ["---", ""]

    # --- Legal context (if available) ---
    if legal_note:
        legal_section = reporting_section + 1
        lines += [
            f"## {legal_section}. POTENTIALLY RELEVANT LEGAL CONTEXT",
            "",
            "> ⚠️ The following is general information only. It is NOT legal advice.",
            "> It does NOT confirm that any legal violation has occurred.",
            "",
            legal_note,
            "",
            "---",
            "",
        ]
        notes_section = legal_section + 1
    else:
        notes_section = reporting_section + 1

    # --- Reporter notes ---
    if case.reporter_notes:
        lines += [
            f"## {notes_section}. REPORTER NOTES",
            "",
            case.reporter_notes,
            "",
            "---",
            "",
        ]

    # --- Footer ---
    lines += [
        "*This report was auto-generated by the Child Online Safety Monitor (COSM) v2.*",
        "*It is a structured draft only — professional review and law enforcement assessment are required.*",
        "*Generated for IBM Bob Hackathon 2025 — Team Phantom Rizzlers.*",
    ]

    return "\n".join(lines)


def generate_pdf(markdown_text: str) -> bytes:
    """
    Convert markdown to PDF bytes using reportlab.
    Falls back to UTF-8-encoded markdown bytes if reportlab is not installed.
    Implementation adapted from report_generator.py.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        import io

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle(
            "CTitle", parent=styles["Title"],
            fontSize=16, spaceAfter=6,
            textColor=colors.HexColor("#1f2328"),
        )
        h2_style = ParagraphStyle(
            "CH2", parent=styles["Heading2"],
            fontSize=12, spaceBefore=12, spaceAfter=4,
            textColor=colors.HexColor("#3b82d4"),
        )
        h3_style = ParagraphStyle(
            "CH3", parent=styles["Heading3"],
            fontSize=10, spaceBefore=8, spaceAfter=2,
            textColor=colors.HexColor("#1f2328"),
        )
        body_style = ParagraphStyle(
            "CBody", parent=styles["Normal"],
            fontSize=9, leading=14, spaceAfter=4,
        )
        warning_style = ParagraphStyle(
            "CWarn", parent=styles["Normal"],
            fontSize=9, leading=14,
            backColor=colors.HexColor("#fff8e1"),
            borderPadding=6,
        )

        for line in markdown_text.split("\n"):
            stripped = line.strip()
            if not stripped:
                story.append(Spacer(1, 4))
                continue
            if stripped.startswith("# "):
                story.append(Paragraph(stripped[2:], title_style))
            elif stripped.startswith("## "):
                story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb")))
                story.append(Paragraph(stripped[3:], h2_style))
            elif stripped.startswith("### "):
                story.append(Paragraph(stripped[4:], h3_style))
            elif stripped.startswith("---"):
                story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb")))
            elif stripped.startswith("> "):
                story.append(Paragraph(stripped[2:], warning_style))
            elif stripped.startswith("- "):
                story.append(Paragraph(f"• {stripped[2:]}", body_style))
            elif stripped.startswith("**") or stripped.startswith("*"):
                clean = stripped.replace("**", "<b>", 1).replace("**", "</b>", 1)
                story.append(Paragraph(clean, body_style))
            elif stripped.startswith("|"):
                # Skip markdown table lines in PDF
                pass
            else:
                story.append(Paragraph(stripped, body_style))

        doc.build(story)
        buffer.seek(0)
        return buffer.read()

    except ImportError:
        # Fallback: return UTF-8-encoded markdown bytes
        return markdown_text.encode("utf-8")
