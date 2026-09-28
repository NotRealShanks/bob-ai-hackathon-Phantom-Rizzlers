"""
services/ai_service.py — AI provider abstraction and IBM watsonx.ai integration.

Provider selection:
  - WatsonxProvider: used when WATSONX_API_KEY + WATSONX_PROJECT_ID are set in env
                     AND COSM_DEMO_MODE != "true"
  - MockProvider:    used otherwise (no API call; returns keyword-driven fixture responses)

All credentials are read from environment variables only. Never hardcoded.
"""

from __future__ import annotations

import json
import logging
import os
import re
from abc import ABC, abstractmethod

# Load .env file if present (harmless if file doesn't exist)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from models.assessment import AIAssessment, SignalItem

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates (from contracts.md Section 6)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a child online safety assessment assistant. Your role is to help parents and caregivers understand concerning online situations involving their child. You must follow these rules strictly:

1. NEVER claim that a crime has definitely occurred. Use language like "may indicate", "could suggest", "potentially consistent with".
2. NEVER encourage the parent or child to continue communicating with a suspected person to gather evidence.
3. NEVER suggest viewing, re-opening, forwarding, or sharing potentially harmful material.
4. NEVER ask for or encourage the sharing of sexual imagery involving children under any circumstances.
5. Use plain, calm language. The reader may be distressed.
6. Always respond with ONLY valid JSON matching the schema below. Do not include any text outside the JSON object.
7. If the situation suggests immediate physical danger, use concern_level "URGENT_SAFETY_CONCERN".
8. Legal references must be framed as "potentially relevant" — never as definitive legal conclusions.
9. Include a non-empty disclaimer field in every response.
10. If you are uncertain, say so in uncertainty_note and use a lower confidence value.

You must return a JSON object with EXACTLY these fields:
{
  "concern_level": "LOW" | "MODERATE" | "HIGH" | "URGENT_SAFETY_CONCERN",
  "situation_category": string,
  "confidence": "LOW" | "MODERATE" | "HIGH",
  "uncertainty_note": string,
  "situation_summary": string,
  "safety_signals": [{"signal": string, "explanation": string, "severity": "informational" | "concerning" | "serious"}],
  "why_this_matters": string,
  "recommended_actions": [string],
  "actions_to_avoid": [string],
  "evidence_guidance": [string],
  "reporting_guidance": [string],
  "escalation_guidance": string,
  "legal_context_note": string,
  "disclaimer": string
}"""

VALID_CONCERN_LEVELS = {"LOW", "MODERATE", "HIGH", "URGENT_SAFETY_CONCERN"}
STANDARD_DISCLAIMER = (
    "This assessment is based solely on the description provided. "
    "It is not a legal determination and does not confirm that any crime occurred. "
    "Please consult qualified professionals and law enforcement as appropriate."
)


def _make_user_prompt(description: str, immediate_safety_concern: bool) -> str:
    return (
        f"A parent or caregiver has described the following situation involving their child online.\n\n"
        f"Immediate safety concern reported by parent: {'YES' if immediate_safety_concern else 'NO'}\n\n"
        f"Description:\n{description}\n\n"
        f"Assess this situation and return ONLY a JSON object matching the required schema. "
        f"Do not include any text before or after the JSON."
    )


def _parse_ai_response(raw: str) -> AIAssessment:
    """
    Parse the raw text response from the model into an AIAssessment.
    Strips markdown fences, then json.loads. Falls back on error.
    """
    # Strip markdown code fences if present
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON decode error: {exc}") from exc

    # Validate concern_level
    concern = data.get("concern_level", "MODERATE")
    if concern not in VALID_CONCERN_LEVELS:
        concern = "MODERATE"

    # Build safety_signals list
    raw_signals = data.get("safety_signals", [])
    signals = []
    for s in raw_signals:
        if isinstance(s, dict):
            signals.append(SignalItem(
                signal=str(s.get("signal", "")),
                explanation=str(s.get("explanation", "")),
                severity=str(s.get("severity", "informational")),
            ))

    return AIAssessment(
        concern_level=concern,
        situation_category=str(data.get("situation_category", "General Concern")),
        confidence=str(data.get("confidence", "LOW")),
        uncertainty_note=str(data.get("uncertainty_note", "Assessment is based only on the description provided.")),
        situation_summary=str(data.get("situation_summary", "")),
        safety_signals=signals,
        why_this_matters=str(data.get("why_this_matters", "")),
        recommended_actions=list(data.get("recommended_actions", [])),
        actions_to_avoid=list(data.get("actions_to_avoid", [])),
        evidence_guidance=list(data.get("evidence_guidance", [])),
        reporting_guidance=list(data.get("reporting_guidance", [])),
        escalation_guidance=str(data.get("escalation_guidance", "")),
        legal_context_note=str(data.get("legal_context_note", "")),
        disclaimer=str(data.get("disclaimer", STANDARD_DISCLAIMER)),
    )


def _error_assessment(error_msg: str) -> AIAssessment:
    """Return a safe low-confidence AIAssessment when AI call fails."""
    return AIAssessment(
        concern_level="LOW",
        situation_category="General Concern",
        confidence="LOW",
        uncertainty_note="AI assessment was unavailable. Results below are from the deterministic safety engine only.",
        situation_summary="",
        safety_signals=[],
        why_this_matters="",
        recommended_actions=[],
        actions_to_avoid=[],
        evidence_guidance=[],
        reporting_guidance=[],
        escalation_guidance="If you are concerned for your child's safety, contact Childline India on 1098 or Emergency 112.",
        legal_context_note="",
        disclaimer="AI assessment unavailable. Please rely on the safety signals below.",
        error_note=error_msg,
    )


# ---------------------------------------------------------------------------
# Provider abstraction
# ---------------------------------------------------------------------------

class AIProvider(ABC):
    @abstractmethod
    def assess(self, description: str, immediate_safety_concern: bool) -> AIAssessment:
        """Analyse the description and return a structured AIAssessment."""
        ...


# ---------------------------------------------------------------------------
# WatsonxProvider
# ---------------------------------------------------------------------------

class WatsonxProvider(AIProvider):
    """
    Uses ibm-watsonx-ai SDK to call the configured Granite model.
    Reads credentials from environment variables only.
    """

    def __init__(self) -> None:
        # Support both WATSONX_API_KEY and WATSONX_APIKEY
        self.api_key = (
            os.environ.get("WATSONX_API_KEY", "").strip()
            or os.environ.get("WATSONX_APIKEY", "").strip()
        )
        self.project_id = os.environ.get("WATSONX_PROJECT_ID", "").strip()
        self.url = os.environ.get("WATSONX_URL", "https://us-south.ml.cloud.ibm.com").strip()
        self.model_id = os.environ.get("WATSONX_MODEL_ID", "ibm/granite-3-8b-instruct").strip()

    def assess(self, description: str, immediate_safety_concern: bool) -> AIAssessment:
        from ibm_watsonx_ai import Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference

        user_prompt = _make_user_prompt(description, immediate_safety_concern)

        # Granite instruct models work best with a system+user message format
        # Try chat API first; fall back to generate_text with instruction format
        model = ModelInference(
            model_id=self.model_id,
            credentials=Credentials(api_key=self.api_key, url=self.url),
            project_id=self.project_id,
        )

        raw_response = None
        # Try chat-style API (ibm-watsonx-ai >= 1.1)
        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
            result = model.chat(
                messages=messages,
                params={"max_tokens": 1400, "temperature": 0.1},
            )
            # chat() returns a dict; extract content
            raw_response = (
                result.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
        except Exception:
            pass

        # Fall back to generate_text with Llama-style instruction wrapper
        if not raw_response:
            full_prompt = (
                f"[INST] <<SYS>>\n{SYSTEM_PROMPT}\n<</SYS>>\n\n{user_prompt} [/INST]"
            )
            raw_response = model.generate_text(
                prompt=full_prompt,
                params={"max_new_tokens": 1400},
            )

        return _parse_ai_response(raw_response)


# ---------------------------------------------------------------------------
# MockProvider — keyword-driven fixture responses for demo / no-credential mode
# ---------------------------------------------------------------------------

class MockProvider(AIProvider):
    """
    Returns realistic fixture responses without any API call.
    Varies the response based on keywords in the description.
    """

    def assess(self, description: str, immediate_safety_concern: bool) -> AIAssessment:
        desc_lower = description.lower()

        # --- URGENT: Sextortion / blackmail ---
        if any(kw in desc_lower for kw in ["sextortion", "blackmail", "threat", "expose", "will send", "will share"]):
            return AIAssessment(
                concern_level="URGENT_SAFETY_CONCERN",
                situation_category="Sextortion / Online Blackmail",
                confidence="HIGH",
                uncertainty_note="The described situation contains multiple indicators of sextortion. Assessment is based only on the description provided.",
                situation_summary=(
                    "The situation described may involve sextortion — a form of online blackmail where a person "
                    "threatens to share private or intimate images of a child unless demands are met. "
                    "This is an extremely serious situation that warrants immediate action."
                ),
                safety_signals=[
                    SignalItem("Coercive threats", "The described threats to share images or information are consistent with sextortion behaviour.", "serious"),
                    SignalItem("Demand for compliance", "Threats tied to demands suggest an attempt to control the child through fear.", "serious"),
                    SignalItem("Potential image exploitation", "Any intimate or sensitive imagery that exists may be at risk of being shared without consent.", "serious"),
                ],
                why_this_matters=(
                    "Sextortion causes severe psychological harm to children. The threats are real even if the person making them "
                    "is far away. The child is not at fault. Do NOT pay or comply with demands — this typically escalates rather "
                    "than resolves the situation."
                ),
                recommended_actions=[
                    "Contact the police or cybercrime.gov.in immediately — this situation warrants urgent professional help.",
                    "Reassure your child that they are not in trouble and not to blame.",
                    "Do not pay any money or comply with demands — compliance typically leads to further demands.",
                    "Preserve evidence safely: screenshot usernames and profile information without viewing harmful content.",
                    "Contact the platform where the contact occurred and report the account.",
                    "Call Childline India on 1098 for immediate support guidance.",
                ],
                actions_to_avoid=[
                    "Do NOT comply with demands or pay money.",
                    "Do NOT encourage your child to continue contact with this person.",
                    "Do NOT view, forward, or share any potentially harmful imagery.",
                    "Do NOT confront the suspected person directly — this could escalate risk.",
                    "Do NOT delete accounts or messages — these are evidence.",
                ],
                evidence_guidance=[
                    "Screenshot usernames, profile pictures, and account URLs without opening harmful content.",
                    "Note the platform name, date, and approximate time the contact occurred.",
                    "Do NOT take screenshots of any intimate imagery — report its existence to authorities instead.",
                    "Store any screenshots in a password-protected location.",
                ],
                reporting_guidance=[
                    "Report to cybercrime.gov.in — India's National Cyber Crime Reporting Portal.",
                    "Call the National Cyber Helpline: 1930.",
                    "Report the account on the platform where contact occurred.",
                    "If imagery may have been shared, report to NCMEC CyberTipline at missingkids.org.",
                ],
                escalation_guidance=(
                    "Given the severity of this situation, contact law enforcement today. "
                    "If your child is in immediate physical danger, call 112 (Emergency) immediately. "
                    "For emotional support, call Childline India on 1098."
                ),
                legal_context_note=(
                    "This situation may potentially be relevant to provisions including IT Act 2000 Section 67B "
                    "(transmission of material depicting children in sexually explicit acts), Section 66E (privacy violation), "
                    "and POCSO Act 2012. These are for informational purposes only — a legal determination requires professional assessment."
                ),
                disclaimer=STANDARD_DISCLAIMER,
                error_note="",
            )

        # --- HIGH: Grooming signals ---
        if any(kw in desc_lower for kw in ["grooming", "gift", "secret", "meet", "photo", "selfie", "mature", "special friend", "love you"]):
            return AIAssessment(
                concern_level="HIGH",
                situation_category="Potential Online Grooming",
                confidence="MODERATE",
                uncertainty_note="Several indicators are consistent with grooming behaviour, but the full context is not available. Assessment is based only on the description provided.",
                situation_summary=(
                    "The situation described contains several indicators that may be consistent with online grooming — "
                    "a process where an adult builds trust with a child in order to exploit them. "
                    "It is important to take these signals seriously without assuming the worst."
                ),
                safety_signals=[
                    SignalItem("Secrecy or boundary-crossing", "Requests for secrecy or to keep contact hidden from parents are common early grooming tactics.", "serious"),
                    SignalItem("Trust-building behaviour", "Offering gifts, expressing special affection, or claims of a unique relationship may indicate an attempt to build inappropriate trust.", "concerning"),
                    SignalItem("Escalating requests", "Requests for photos, meetings, or personal information represent a potential escalation of risk.", "serious"),
                ],
                why_this_matters=(
                    "Grooming is a gradual process. Each individual sign may seem minor, but together they form a pattern "
                    "that warrants serious attention. Children are rarely able to identify grooming as it happens. "
                    "Your concern as a caregiver is an important protective factor."
                ),
                recommended_actions=[
                    "Have a calm, non-accusatory conversation with your child about online safety.",
                    "Check parental controls and privacy settings on devices and platforms.",
                    "Preserve any evidence of concerning communications safely.",
                    "Contact your local police or cybercrime.gov.in to seek guidance.",
                    "Consider speaking to a school counsellor or child protection professional.",
                ],
                actions_to_avoid=[
                    "Do NOT confront the suspected person directly — this could alert them and lead to evidence destruction.",
                    "Do NOT re-read or re-open potentially harmful content.",
                    "Do NOT ask your child to continue communicating to gather more information.",
                    "Do NOT share screenshots of content publicly.",
                ],
                evidence_guidance=[
                    "Screenshot usernames, profile pictures, and conversation metadata (timestamps, platform).",
                    "Use the platform's official export function to preserve chat history.",
                    "Do not scroll through or re-read harmful content while preserving evidence.",
                    "Store evidence in a password-protected location, not in messaging apps.",
                ],
                reporting_guidance=[
                    "Report to cybercrime.gov.in — India's National Cyber Crime Reporting Portal.",
                    "Call the National Cyber Helpline: 1930.",
                    "Report the account on the platform where contact occurred.",
                ],
                escalation_guidance=(
                    "If at any point you believe your child is in immediate danger, call 112 (Emergency) or "
                    "Childline India on 1098. A qualified child protection professional can provide guidance tailored to your situation."
                ),
                legal_context_note=(
                    "Depending on the nature of communications, potentially relevant provisions may include "
                    "POCSO Act 2012 Section 11 (sexual harassment of a child) and Section 19 (mandatory reporting obligation). "
                    "These are for informational purposes only and do not constitute legal advice."
                ),
                disclaimer=STANDARD_DISCLAIMER,
                error_note="",
            )

        # --- MODERATE: Behavioural changes ---
        if any(kw in desc_lower for kw in ["withdrawn", "anxious", "hiding", "deletes", "secretive", "changed", "behaviour", "behavior", "worried", "phone", "online late"]):
            return AIAssessment(
                concern_level="MODERATE",
                situation_category="Concerning Behavioural Changes",
                confidence="LOW",
                uncertainty_note="Behavioural changes alone have many possible causes. This assessment cannot determine whether online safety is a factor without more information. Assessment is based only on the description provided.",
                situation_summary=(
                    "The situation describes behavioural changes in a child that may warrant attention. "
                    "While these changes can have many causes, some patterns may be associated with distressing online experiences. "
                    "Gentle inquiry and open conversation are the most appropriate first steps."
                ),
                safety_signals=[
                    SignalItem("Secretive device use", "Increased secrecy around phones or devices, or deleting messages, may indicate the child is protecting a relationship or communication they feel they cannot share.", "concerning"),
                    SignalItem("Withdrawal or anxiety", "Changes in mood or social withdrawal can sometimes be linked to distressing online interactions.", "informational"),
                ],
                why_this_matters=(
                    "Children who are experiencing uncomfortable or harmful online situations often show behavioural changes before "
                    "disclosing what is happening. Creating a safe, non-judgmental space for your child to talk is one of the most "
                    "important protective actions you can take."
                ),
                recommended_actions=[
                    "Have an open, calm conversation with your child — let them know they can talk to you without fear of punishment.",
                    "Review privacy settings and parental controls on devices and apps.",
                    "Speak to your child's school or a counsellor if you remain concerned.",
                    "Continue to monitor while maintaining trust with your child.",
                ],
                actions_to_avoid=[
                    "Do NOT demand to see your child's phone in a way that damages trust — this may cause them to hide more.",
                    "Do NOT immediately assume the worst — there may be non-safety explanations.",
                    "Do NOT confront anyone online on your child's behalf without first seeking professional advice.",
                ],
                evidence_guidance=[
                    "At this stage, note the specific behavioural changes you have observed and when they started.",
                    "If you observe direct signs of harmful contact, preserve evidence at that point.",
                ],
                reporting_guidance=[
                    "If you discover evidence of harmful contact, report to cybercrime.gov.in or call 1930.",
                    "Childline India (1098) can provide guidance on next steps even before a formal report.",
                ],
                escalation_guidance=(
                    "If your child discloses anything that suggests they are in immediate danger or being exploited, "
                    "contact Childline India (1098) or the police (112) immediately."
                ),
                legal_context_note=(
                    "At this stage there is insufficient information to identify specific potentially relevant legal provisions. "
                    "If harmful contact is confirmed, POCSO Act 2012 Section 19 (mandatory reporting) may be relevant."
                ),
                disclaimer=STANDARD_DISCLAIMER,
                error_note="",
            )

        # --- LOW: Default ---
        return AIAssessment(
            concern_level="LOW",
            situation_category="General Online Safety Concern",
            confidence="LOW",
            uncertainty_note="The description does not contain clear indicators of specific risk. Assessment is based only on the description provided.",
            situation_summary=(
                "The situation described does not contain clear indicators of immediate risk based on the information provided. "
                "This does not mean your concern is invalid — if something feels wrong, it is always appropriate to seek guidance."
            ),
            safety_signals=[
                SignalItem("Parent concern", "A parent's concern about their child's online activities is itself a valid signal worth taking seriously.", "informational"),
            ],
            why_this_matters=(
                "Even when there are no clear immediate risk signals, staying engaged with your child's online life and "
                "maintaining open communication is one of the most important things you can do."
            ),
            recommended_actions=[
                "Continue open conversations with your child about their online activities.",
                "Review privacy settings and age-appropriate platform usage.",
                "Familiarise yourself with the platforms your child uses.",
            ],
            actions_to_avoid=[
                "Do NOT ignore your instincts — if you remain concerned, seek a second opinion from a professional.",
            ],
            evidence_guidance=[
                "No specific evidence preservation steps are needed at this stage.",
                "If something concerning arises, note the platform, usernames, and dates.",
            ],
            reporting_guidance=[
                "If your concern increases, contact cybercrime.gov.in or call the National Cyber Helpline: 1930.",
                "Childline India (1098) can provide guidance at any level of concern.",
            ],
            escalation_guidance=(
                "If the situation changes or you discover new information, reassess and consider reporting to "
                "cybercrime.gov.in or contacting Childline India (1098)."
            ),
            legal_context_note="No specific legal provisions are flagged at this concern level.",
            disclaimer=STANDARD_DISCLAIMER,
            error_note="",
        )


# ---------------------------------------------------------------------------
# Provider factory + convenience wrapper
# ---------------------------------------------------------------------------

def get_provider() -> AIProvider:
    """
    Returns WatsonxProvider if credentials are present and demo mode is off.
    Supports both WATSONX_API_KEY and WATSONX_APIKEY env var names.
    Otherwise returns MockProvider.
    """
    demo_mode = os.environ.get("COSM_DEMO_MODE", "false").strip().lower() == "true"
    api_key = (
        os.environ.get("WATSONX_API_KEY", "").strip()
        or os.environ.get("WATSONX_APIKEY", "").strip()
    )
    project_id = os.environ.get("WATSONX_PROJECT_ID", "").strip()

    if not demo_mode and api_key and project_id:
        try:
            return WatsonxProvider()
        except Exception as exc:
            logger.warning("Failed to initialise WatsonxProvider: %s — falling back to MockProvider", exc)
            return MockProvider()
    return MockProvider()


def assess(description: str, immediate_safety_concern: bool) -> AIAssessment:
    """
    Convenience function. Calls get_provider().assess(...).
    NEVER raises an exception — returns an error AIAssessment on any failure.
    """
    try:
        provider = get_provider()
        return provider.assess(description, immediate_safety_concern)
    except Exception as exc:
        logger.warning("AI assessment failed: %s", exc, exc_info=True)
        return _error_assessment(str(exc))
