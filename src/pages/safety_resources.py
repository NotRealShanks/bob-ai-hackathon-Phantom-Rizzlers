"""
pages/safety_resources.py — Static safety resources and helplines page.
"""
from __future__ import annotations

import streamlit as st


def render() -> None:
    st.markdown("# 🆘 Safety Resources")
    st.markdown(
        "This page provides helplines, reporting guides, and evidence preservation reminders. "
        "You do not need to have an active case to use these resources."
    )
    st.divider()

    # ── Emergency contacts ──
    st.markdown("## 📞 Emergency & Helpline Contacts")
    st.markdown(
        """
| Service | Contact | Available |
|---------|---------|-----------|
| **Emergency (Police / Fire / Medical)** | **112** | 24×7 |
| **Childline India** | **1098** | 24×7 |
| **National Cyber Helpline** | **1930** | 24×7 |
| **Women Helpline** | **1091** | 24×7 |
| **iCall (Mental health)** | 9152987821 | Mon–Sat 8 am–10 pm |
| **Vandrevala Foundation** | 1860-2662-345 | 24×7 |
"""
    )

    st.divider()

    # ── How to report online ──
    st.markdown("## 🌐 How to Report Online")

    with st.expander("📋 cybercrime.gov.in — National Cyber Crime Reporting Portal", expanded=True):
        st.markdown(
            """
1. Go to **[cybercrime.gov.in](https://cybercrime.gov.in)**
2. Click **"Report Cyber Crime"**
3. Select the appropriate category — for child-related concerns, choose **"Child Pornography / Child Sexual Abuse Material (CSAM)"** or **"Online Grooming"**
4. Fill in the form with details you know (platform name, username, approximate dates)
5. **Do NOT upload or attach any harmful images or videos** — report their existence only
6. You will receive a report acknowledgement number — save this
7. A copy of the COSM incident report draft can be used as supporting documentation

> ⚠️ You do not need to have been a victim yourself to make a report. Any person with knowledge of an offence against a child may report it.
"""
        )

    with st.expander("📞 Childline 1098 Process"):
        st.markdown(
            """
1. **Call 1098** (free, 24×7 across India)
2. A trained counsellor will answer
3. Describe the situation — you do not need to have all details
4. The counsellor can guide you on immediate next steps, professional support, and reporting
5. Childline can also initiate a welfare check for the child if needed

> Childline is for **any adult concerned about a child's welfare**, not only for the child themselves.
"""
        )

    with st.expander("🌍 International Resources"):
        st.markdown(
            """
| Resource | URL |
|----------|-----|
| NCMEC CyberTipline (USA / INTERPOL gateway) | [missingkids.org/gethelpnow/cybertipline](https://www.missingkids.org/gethelpnow/cybertipline) |
| INTERPOL ICSE Database | [icse.interpol.int](https://icse.interpol.int) |
| Internet Watch Foundation (IWF) | [iwf.org.uk/report](https://www.iwf.org.uk/report/) |
"""
        )

    st.divider()

    # ── Evidence Preservation ──
    st.markdown("## 🔒 Evidence Preservation Reminder")
    st.markdown(
        """
<div style="background:#fff8e1;border-left:4px solid #f59e0b;padding:12px 16px;border-radius:0 6px 6px 0;margin-bottom:16px;font-size:0.92rem;color:#78350f;">
🔒 <strong>Do NOT re-open, re-read, or share the original content.</strong>
Viewing it again may cause additional harm and may compromise the integrity of evidence.
</div>
""",
        unsafe_allow_html=True,
    )

    try:
        from services.safety_rules import PRESERVATION_STEPS
        steps = PRESERVATION_STEPS
    except Exception:
        steps = [
            "Take a screenshot of the sender's profile — username, profile picture, account URL.",
            "Note the platform name, the date, and approximate time of the interaction.",
            "Use the platform's official 'Export / Download your data' function to preserve logs.",
            "Do NOT scroll through or re-read harmful content while preserving evidence.",
            "Do NOT delete messages, accounts, or apps — they are potential evidence.",
            "Store any screenshots in a password-protected location, not in messaging apps.",
            "Do NOT forward screenshots to friends, family, or social media.",
            "Write down everything you remember about the sequence of events while it is fresh.",
            "If a device was used, do not perform a factory reset — consult authorities first.",
        ]

    for step in steps:
        st.markdown(f'<div class="step-card">✅ {step}</div>', unsafe_allow_html=True)

    st.divider()

    # ── Platform-specific reporting ──
    st.markdown("## 📱 Platform-Specific Reporting Guides")

    with st.expander("WhatsApp"):
        st.markdown(
            """
1. Open the chat with the concerning contact
2. Tap the contact name / group name at the top
3. Scroll down → **Report** (and optionally **Block**)
4. Select the reason: **"Inappropriate content"** or **"Child exploitation"**
5. WhatsApp will review and may report to NCMEC
6. **Do NOT delete the chat** before or after reporting — preserve the evidence
7. Also report to cybercrime.gov.in with the phone number / account details
"""
        )

    with st.expander("Instagram"):
        st.markdown(
            """
1. Go to the concerning account profile
2. Tap the **⋮** (three dots) menu
3. Select **Report** → appropriate category (e.g. "It's inappropriate" → "Involves a child")
4. Alternatively, go to the specific message or post and tap **Report**
5. Instagram will review and may escalate to NCMEC for CSAM
6. Also report to cybercrime.gov.in
"""
        )

    with st.expander("Telegram"):
        st.markdown(
            """
1. Open the chat with the concerning contact
2. Tap the contact name at the top
3. Tap **⋮** → **Report**
4. Choose the appropriate report type
5. Telegram also has a dedicated email: **abuse@telegram.org**
6. For CSAM, also report to the NCMEC CyberTipline at **missingkids.org**
7. Report to cybercrime.gov.in with the account username / link
"""
        )

    with st.expander("YouTube / Google"):
        st.markdown(
            """
1. Click the **⋮** (three dots) on the video or comment
2. Select **Report**
3. Choose **"Sexual content" → "Involves a minor"**
4. Google / YouTube will review and report to NCMEC as required
5. You can also report via **[support.google.com/youtube/answer/2802027](https://support.google.com/youtube/answer/2802027)**
"""
        )

    st.divider()

    # ── Support organisations ──
    st.markdown("## 🤝 Support Organisations")
    st.markdown(
        """
| Organisation | What they offer | Contact |
|--------------|----------------|---------|
| **Childline India** | Free helpline for children in distress; also guides adults | 1098 |
| **iCall (TISS)** | Free, confidential psychological counselling | 9152987821 |
| **Vandrevala Foundation** | 24×7 mental health helpline | 1860-2662-345 |
| **Tulir – Centre for Prevention of Child Sexual Abuse** | Specialist support for child sexual abuse, including online | [tulir.org](https://www.tulir.org) |
| **POCSO e-Box** | Anonymous reporting for children under POCSO | [ncpcr.gov.in/pocso-e-box](https://ncpcr.gov.in) |
"""
    )

    st.divider()
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
