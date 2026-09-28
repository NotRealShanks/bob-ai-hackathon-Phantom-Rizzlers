"""
sample_cases.py — Synthetic demo cases for the Child Online Safety Monitor.

ALL content here is completely fictional and created solely for demonstration
purposes. No real individuals, victims, or perpetrators are referenced.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class SampleCase:
    title: str
    label: str        # e.g., "Chat Excerpt" or "Behavioural Report"
    persona: str      # Who reported this
    text: str
    expected_risk: str


SAMPLE_CASES: list[SampleCase] = [
    SampleCase(
        title="Case 1 — New 'Friend' on Gaming Platform",
        label="Chat Excerpt",
        persona="Parent of a 13-year-old",
        expected_risk="Critical",
        text="""
[Gaming chat — 9:47 PM]
User_Striker99: hey you play really well, you're so mature for your age
User_Striker99: how old are you? i'm 24 but age doesn't matter between real friends
User_Striker99: i can buy you V-Bucks as a gift if you want, you just have to be my special friend
User_Striker99: don't tell your parents we're talking, they won't understand our friendship
User_Striker99: can you send me a selfie? i want to see how cool you look irl
User_Striker99: we should meet up sometime, i know a place near your school
""",
    ),

    SampleCase(
        title="Case 2 — Behavioural Changes at School",
        label="Behavioural Report",
        persona="School teacher / counsellor",
        expected_risk="High",
        text="""
Student (14F) has shown sudden behavioural changes over the past three weeks.
She appears withdrawn from her usual friend group and becomes visibly anxious
when teachers approach her phone. She has mentioned someone she met online who
"really understands her unlike anyone else" and says her parents are wrong about
everything and no one at home cares. She was overheard saying this person sends
her gifts and money via UPI. She has started hiding her phone screen and deletes
messages when adults are nearby. She skipped two classes last week without
explanation. She mentioned wanting to meet this person alone.
""",
    ),

    SampleCase(
        title="Case 3 — Sextortion via Instagram DMs",
        label="Chat Excerpt",
        persona="NGO child-protection worker",
        expected_risk="Critical",
        text="""
[Instagram DM — 11:23 PM]
model_scout_official: Hi sweetheart, I saw your profile, you're so beautiful and hot
model_scout_official: I can make you famous, just send me some photos for our portfolio
model_scout_official: Don't tell your parents yet, it's a surprise for them
model_scout_official: I already have some of your photos from your public profile
model_scout_official: If you don't send me more I will share these with everyone at your school
model_scout_official: You have 24 hours. Delete this conversation after reading.
model_scout_official: Download this link to see your contract: bit.ly/m0d3l-c0ntract
""",
    ),

    SampleCase(
        title="Case 4 — Low-Risk: Normal Online Interaction",
        label="Chat Excerpt",
        persona="Parent reviewing child's chat",
        expected_risk="Low",
        text="""
[WhatsApp — School group — 4:15 PM]
Aanya: Did anyone finish the science homework?
Rohan: Yeah I did, it was easy
Priya: Can you share your notes Rohan?
Rohan: Sure, sending in the group now
Teacher_Mrs_Sharma: Good work everyone, see you tomorrow
Aanya: Thanks Mrs Sharma!
""",
    ),

    SampleCase(
        title="Case 5 — Webcam Coercion & Isolation",
        label="Chat Excerpt",
        persona="Childline case worker",
        expected_risk="Critical",
        text="""
[Telegram — 1:14 AM]
FriendForever_Alex: turn your webcam on, I just want to see you
FriendForever_Alex: you're the only one who understands me, your parents don't care about you
FriendForever_Alex: let's do a live stream together, I'll keep it private just for us
FriendForever_Alex: if you love me you'll do this, don't be scared
FriendForever_Alex: I'll send you money after, and we can run away together
FriendForever_Alex: don't tell anyone about our relationship, they'll try to separate us
FriendForever_Alex: if you stop talking to me I'll tell your school friends everything
""",
    ),
]
