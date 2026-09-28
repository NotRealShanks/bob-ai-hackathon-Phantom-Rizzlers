"""
analyzer.py — Core analysis engine for Child Online Safety Monitor.

All analysis is based on keyword/pattern matching against synthetic/mock input.
This module never stores, transmits, or re-displays raw harmful content.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class WarningSigns:
    sign: str
    explanation: str
    category: str  # behavioural | communication | digital


@dataclass
class LegalMapping:
    act: str
    section: str
    description: str
    max_penalty: str


@dataclass
class AnalysisResult:
    risk_level: str          # Low | Medium | High | Critical
    risk_score: int          # 0–100
    warning_signs: List[WarningSigns] = field(default_factory=list)
    legal_mappings: List[LegalMapping] = field(default_factory=list)
    preservation_steps: List[str] = field(default_factory=list)
    summary: str = ""
    input_type: str = "unknown"  # behavioural | chat


# ---------------------------------------------------------------------------
# Grooming / abuse pattern catalogs
# ---------------------------------------------------------------------------

BEHAVIOURAL_PATTERNS: List[Tuple[re.Pattern, WarningSigns]] = [
    (
        re.compile(r"\b(secret|don't tell|keep.{0,10}secret|no one.{0,10}know|our.{0,10}secret)\b", re.I),
        WarningSigns("Secrecy demands", "Perpetrators often instruct children to keep contact confidential to prevent disclosure.", "communication"),
    ),
    (
        re.compile(r"\b(gift|present|money|buy.{0,10}you|reward|surprise)\b", re.I),
        WarningSigns("Unsolicited gifting", "Offering gifts or money is a common grooming tactic to build trust and create obligation.", "behavioural"),
    ),
    (
        re.compile(r"\b(alone|meet.{0,10}up|come.{0,10}over|visit|in.{0,10}person|offline)\b", re.I),
        WarningSigns("Requests for in-person meeting", "Attempts to move contact offline significantly escalate risk of physical harm.", "communication"),
    ),
    (
        re.compile(r"\b(photo|pic|selfie|picture|send.{0,15}(me|us)|image|video)\b", re.I),
        WarningSigns("Soliciting images or videos", "Requesting photos or videos — especially escalating to intimate content — is a primary CSAM indicator.", "digital"),
    ),
    (
        re.compile(r"\b(love you|special.{0,10}friend|only one|soulmate|relationship|boyfriend|girlfriend|crush)\b", re.I),
        WarningSigns("Premature emotional intimacy", "Rapid or excessive expressions of affection are used to build an illusion of a special relationship.", "communication"),
    ),
    (
        re.compile(r"\b(password|account|login|hack|phish|link|click.{0,10}here|download)\b", re.I),
        WarningSigns("Digital manipulation / phishing", "Soliciting credentials or sending suspicious links may indicate coercive control or entrapment.", "digital"),
    ),
    (
        re.compile(r"\b(parents.{0,15}(don't|won't)|hide.{0,10}phone|delete.{0,10}(messages?|chat|history)|clear.{0,10}history)\b", re.I),
        WarningSigns("Instruction to conceal from parents/guardians", "Directing a child to delete messages or hide contact is a strong indicator of predatory intent.", "behavioural"),
    ),
    (
        re.compile(r"\b(sexy|hot|beautiful|attractive|mature.{0,10}for.{0,10}age|grown.{0,10}up|adult)\b", re.I),
        WarningSigns("Sexualised compliments targeting age/body", "Comments that sexualise or label a child as 'mature' are early grooming signals.", "communication"),
    ),
    (
        re.compile(r"\b(threat|tell.{0,10}everyone|expose|share.{0,10}(photo|these|pics?)|blackmail|ruin.{0,10}you|tell.{0,10}school)\b", re.I),
        WarningSigns("Coercion / blackmail", "Threatening to share images or information is a hallmark of sextortion, a criminal offence under IT Act §66E and §67B.", "communication"),
    ),
    (
        re.compile(r"\b(drug|alcohol|party|high|drunk|sleep.{0,10}over|run.{0,10}away)\b", re.I),
        WarningSigns("Substance or risky behaviour encouragement", "Encouraging substance use or risky activities lowers a child's inhibitions and creates vulnerability.", "behavioural"),
    ),
    (
        re.compile(r"\b(no one.{0,15}understand|parents.{0,15}wrong|family.{0,15}bad|only.{0,10}I.{0,10}care|really.{0,10}understand|everything.{0,15}wrong)\b", re.I),
        WarningSigns("Isolation from family/support network", "Creating a wedge between child and trusted adults is a core grooming strategy.", "behavioural"),
    ),
    (
        re.compile(r"\b(webcam|live.{0,10}stream|show.{0,10}me|camera.{0,10}on|video.{0,10}call)\b", re.I),
        WarningSigns("Webcam/live-stream solicitation", "Requesting live video sessions, especially private ones, is linked to real-time CSAM production.", "digital"),
    ),
]

# ---------------------------------------------------------------------------
# Risk scoring weights
# ---------------------------------------------------------------------------

CATEGORY_WEIGHTS = {
    "behavioural": 8,
    "communication": 10,
    "digital": 15,
}

CRITICAL_TRIGGERS = [
    re.compile(r"\b(photo|pic|selfie|picture|video|webcam|stream)\b", re.I),
    re.compile(r"\b(threat|blackmail|expose|sextortion)\b", re.I),
    re.compile(r"\b(meet.{0,10}up|come.{0,10}over|in.{0,10}person|offline|alone)\b", re.I),
]

# ---------------------------------------------------------------------------
# Legal mappings
# ---------------------------------------------------------------------------

POCSO_SECTIONS: List[LegalMapping] = [
    LegalMapping("POCSO Act 2012", "Section 11", "Sexual harassment of a child — includes any unwelcome communication, gestures, or requests of a sexual nature.", "3 years imprisonment + fine"),
    LegalMapping("POCSO Act 2012", "Section 12", "Punishment for sexual harassment as defined under Section 11.", "3 years imprisonment + fine"),
    LegalMapping("POCSO Act 2012", "Section 13", "Use of child for pornographic purposes — producing, distributing, or facilitating CSAM.", "5 years imprisonment (first offence), 7 years (repeat)"),
    LegalMapping("POCSO Act 2012", "Section 14", "Punishment for use of child for pornographic purposes under Section 13.", "5–7 years imprisonment + fine"),
    LegalMapping("POCSO Act 2012", "Section 15", "Storage of pornographic material involving a child (even without intent to distribute).", "3 years imprisonment / fine / both"),
    LegalMapping("POCSO Act 2012", "Section 19", "Mandatory reporting obligation — any person with knowledge of an offence MUST report to Special Juvenile Police Unit or local police.", "Failure to report: 6 months imprisonment or fine"),
]

IT_ACT_SECTIONS: List[LegalMapping] = [
    LegalMapping("IT Act 2000", "Section 67B", "Publishing, transmitting, or causing to be published/transmitted material depicting children in sexually explicit acts. The primary online CSAM provision.", "5 years imprisonment + ₹10 lakh fine (first offence); 7 years + ₹10 lakh (repeat)"),
    LegalMapping("IT Act 2000", "Section 66E", "Violation of privacy by capturing, publishing or transmitting images of a person's private area without consent.", "3 years imprisonment or ₹2 lakh fine"),
    LegalMapping("IT Act 2000", "Section 67", "Publishing or transmitting obscene material in electronic form.", "3 years imprisonment + ₹5 lakh fine (first offence)"),
    LegalMapping("IT Act 2000", "Section 66C / 66D", "Identity theft and impersonation — relevant when perpetrators create fake profiles to contact children.", "3 years imprisonment + ₹1 lakh fine"),
]

# ---------------------------------------------------------------------------
# Evidence preservation guidance
# ---------------------------------------------------------------------------

PRESERVATION_STEPS = [
    "⚠️  Do NOT open, view, or re-read the original content again — this protects both you and legal chain-of-custody.",
    "📸  Take screenshots of the conversation/platform WITHOUT scrolling through explicit content — capture metadata (timestamp, username, URL).",
    "🔗  Preserve the URL/profile link of the suspected perpetrator without clicking any further.",
    "💾  Export/save chat logs through the platform's official export function (WhatsApp: Chat > Export Chat; Instagram: Settings > Privacy > Download Data).",
    "📁  Store all evidence in a password-protected folder on a separate device or USB drive — do NOT share via messaging apps.",
    "🚫  Do NOT delete any messages, accounts, or posts — even ones that seem harmful; deletion destroys evidence.",
    "📝  Write a contemporaneous note: date/time you discovered the content, who else was present, what platform/device.",
    "👮  Report immediately to: cybercrime.gov.in (National Cyber Crime Reporting Portal) or call 1930 (National Cyber Helpline).",
    "🏥  If the child is in immediate danger, call 112 (Emergency) or 1098 (Childline India).",
    "⚖️  Retain a copy of this report — it can be submitted directly to the Special Juvenile Police Unit (SJPU) or CWC.",
]


# ---------------------------------------------------------------------------
# Core analysis function
# ---------------------------------------------------------------------------

def detect_input_type(text: str) -> str:
    """Heuristically determine if input is behavioural description or chat excerpt."""
    chat_markers = re.compile(r"(\d{1,2}[:/]\d{2}|AM|PM|said|replied|wrote|msg|message|chat|[A-Z][a-z]+\s*:\s)", re.I)
    if chat_markers.search(text):
        return "chat"
    return "behavioural"


def analyse_text(text: str) -> AnalysisResult:
    """
    Main analysis entry-point.
    Accepts raw text (behavioural description or mock chat excerpt).
    Returns AnalysisResult with all findings.
    """
    if not text or len(text.strip()) < 10:
        return AnalysisResult(
            risk_level="Low",
            risk_score=0,
            summary="Insufficient input provided for analysis.",
            input_type="unknown",
        )

    input_type = detect_input_type(text)
    matched_signs: List[WarningSigns] = []
    raw_score = 0

    for pattern, sign in BEHAVIOURAL_PATTERNS:
        if pattern.search(text):
            if sign not in matched_signs:
                matched_signs.append(sign)
                raw_score += CATEGORY_WEIGHTS[sign.category]

    # Check for critical triggers — these force at least High risk
    critical_hits = sum(1 for p in CRITICAL_TRIGGERS if p.search(text))

    # Cap at 100
    score = min(raw_score + (critical_hits * 20), 100)

    # Determine risk level
    if score == 0:
        risk_level = "Low"
    elif score <= 20:
        risk_level = "Low"
    elif score <= 45:
        risk_level = "Medium"
    elif score <= 70:
        risk_level = "High"
    else:
        risk_level = "Critical"

    # Force Critical if coercion/blackmail detected
    coercion = re.compile(
        r"\b(threat|blackmail|expose|sextortion|ruin.{0,10}you|tell.{0,10}everyone"
        r"|share.{0,25}(school|friends|everyone)|i.{0,10}(will|ll).{0,15}(tell|show|send|share).{0,20}everyone)\b",
        re.I,
    )
    if coercion.search(text):
        risk_level = "Critical"
        score = max(score, 90)

    # Select relevant legal mappings
    legal: List[LegalMapping] = []
    has_image = re.compile(r"\b(photo|pic|image|video|webcam|stream|selfie)\b", re.I)
    has_coercion = re.compile(
        r"\b(threat|blackmail|expose|sextortion|ruin.{0,10}you|tell.{0,10}everyone"
        r"|share.{0,25}(school|friends|everyone))\b",
        re.I,
    )
    has_contact = re.compile(r"\b(meet|in.{0,10}person|offline|come.{0,10}over)\b", re.I)

    # Always include POCSO §19 (mandatory reporting) and §11 if any sign found
    if matched_signs:
        legal.append(next(m for m in POCSO_SECTIONS if m.section == "Section 19"))
        legal.append(next(m for m in POCSO_SECTIONS if m.section == "Section 11"))
        legal.append(next(m for m in POCSO_SECTIONS if m.section == "Section 12"))

    if has_image.search(text):
        legal.append(next(m for m in POCSO_SECTIONS if m.section == "Section 13"))
        legal.append(next(m for m in POCSO_SECTIONS if m.section == "Section 14"))
        legal.append(next(m for m in POCSO_SECTIONS if m.section == "Section 15"))
        legal.append(next(m for m in IT_ACT_SECTIONS if m.section == "Section 67B"))
        legal.append(next(m for m in IT_ACT_SECTIONS if m.section == "Section 67"))

    if has_coercion.search(text):
        legal.append(next(m for m in IT_ACT_SECTIONS if m.section == "Section 66E"))

    # De-duplicate
    seen = set()
    unique_legal = []
    for item in legal:
        key = f"{item.act}:{item.section}"
        if key not in seen:
            seen.add(key)
            unique_legal.append(item)

    # Build summary
    sign_count = len(matched_signs)
    summary = _build_summary(risk_level, score, sign_count, input_type)

    return AnalysisResult(
        risk_level=risk_level,
        risk_score=score,
        warning_signs=matched_signs,
        legal_mappings=unique_legal,
        preservation_steps=PRESERVATION_STEPS,
        summary=summary,
        input_type=input_type,
    )


def _build_summary(risk_level: str, score: int, sign_count: int, input_type: str) -> str:
    type_label = "chat excerpt" if input_type == "chat" else "behavioural description"
    if risk_level == "Low":
        return (
            f"Analysis of this {type_label} identified {sign_count} potential warning sign(s). "
            "Current indicators do not suggest immediate danger, but ongoing monitoring is recommended."
        )
    elif risk_level == "Medium":
        return (
            f"Analysis of this {type_label} detected {sign_count} warning sign(s) consistent with early-stage grooming. "
            "Increased supervision, open conversation with the child, and professional guidance are advised."
        )
    elif risk_level == "High":
        return (
            f"This {type_label} contains {sign_count} significant warning sign(s) indicating active grooming behaviour. "
            "Immediate action is required: preserve evidence, restrict access to the platform, and report to cybercrime.gov.in."
        )
    else:  # Critical
        return (
            f"CRITICAL ALERT — This {type_label} contains {sign_count} severe warning sign(s) including indicators of "
            "coercion, image solicitation, or offline meeting requests. Report to law enforcement immediately. "
            "Call Childline 1098 or Emergency 112 if the child is in immediate danger."
        )
