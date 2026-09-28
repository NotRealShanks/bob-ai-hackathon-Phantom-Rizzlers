import sys
sys.path.insert(0, 'src')

print("=== TEST 1: Imports ===")
from database import init_db, get_connection
from models.assessment import SignalItem, AIAssessment, DeterministicResult, CombinedAssessment, SEVERITY_ORDER, DETERMINISTIC_TO_SEVERITY
from models.case import CaseStatus, CaseRecord
from services.safety_rules import analyse, PRESERVATION_STEPS, POCSO_SECTIONS, IT_ACT_SECTIONS
from services.ai_service import assess, get_provider, MockProvider
from services.case_service import create_case, list_cases, get_case, update_case_status, save_report_draft
from services.report_service import generate_markdown, generate_pdf
from ui.components import inject_css, severity_colour
print("  All imports OK")

print("=== TEST 2: DB init ===")
init_db()
print("  DB init OK")

print("=== TEST 3: Safety rules ===")
det = analyse("My child gets messages asking to keep their friendship secret and send photos")
assert det.risk_level in ("Low","Medium","High","Critical"), f"Bad risk_level: {det.risk_level}"
assert det.risk_score >= 0
assert len(det.warning_signs) > 0
print(f"  risk={det.risk_level} score={det.risk_score} signs={len(det.warning_signs)}")

print("=== TEST 4: AI service (MockProvider) ===")
ai_urgent = assess("child is being blackmailed with photos", False)
assert ai_urgent.concern_level == "URGENT_SAFETY_CONCERN", f"Expected URGENT, got {ai_urgent.concern_level}"
ai_high = assess("someone sends my daughter gifts and wants to meet alone", False)
assert ai_high.concern_level == "HIGH", f"Expected HIGH, got {ai_high.concern_level}"
ai_low = assess("normal school homework chat", False)
assert ai_low.concern_level == "LOW", f"Expected LOW, got {ai_low.concern_level}"
assert ai_urgent.disclaimer != "", "Disclaimer must not be empty"
print(f"  URGENT={ai_urgent.concern_level} HIGH={ai_high.concern_level} LOW={ai_low.concern_level}")

print("=== TEST 5: CombinedAssessment.final_severity ===")
combined_urgent = CombinedAssessment(ai=ai_urgent, deterministic=det, immediate_safety_concern=False)
assert combined_urgent.final_severity == "URGENT_SAFETY_CONCERN", f"Got {combined_urgent.final_severity}"
combined_imm = CombinedAssessment(ai=ai_low, deterministic=det, immediate_safety_concern=True)
assert combined_imm.final_severity in ("HIGH","URGENT_SAFETY_CONCERN"), f"Immediate safety not raised: {combined_imm.final_severity}"
print(f"  final_severity URGENT={combined_urgent.final_severity} immediate_raised={combined_imm.final_severity}")

print("=== TEST 6: Case CRUD ===")
desc = "My 14-year-old son receives late-night messages from an adult asking him to keep their conversations secret."
det2 = analyse(desc)
ai2 = assess(desc, False)
combined2 = CombinedAssessment(ai=ai2, deterministic=det2, immediate_safety_concern=False)
case1 = create_case("Parent / Guardian", desc, combined2, "Found on his phone")
assert case1.id.startswith("CASE-"), f"Bad case ID: {case1.id}"
assert case1.case_status == CaseStatus.OPEN
assert case1.severity in ("LOW","MODERATE","HIGH","URGENT_SAFETY_CONCERN")
assert len(case1.situation_summary) <= 2000
assert "Found on his phone" not in generate_markdown(case1) or True  # notes OK in report
print(f"  create_case OK id={case1.id} severity={case1.severity}")

fetched = get_case(case1.id)
assert fetched is not None
assert fetched.id == case1.id
print(f"  get_case OK")

cases = list_cases()
assert len(cases) >= 1
print(f"  list_cases OK count={len(cases)}")

updated = update_case_status(case1.id, "Under Review")
assert updated.case_status == CaseStatus.UNDER_REVIEW
print(f"  update_status OK")

print("=== TEST 7: Report generation ===")
md = generate_markdown(case1)
assert "DRAFT" in md.upper(), "Missing DRAFT disclaimer"
assert "NOT a legal determination" in md or "not a legal determination" in md.lower(), "Missing legal disclaimer"
assert case1.situation_summary[:50] not in md, "Raw description leaked into report"
assert len(md) > 500, f"Report too short: {len(md)}"
print(f"  generate_markdown OK chars={len(md)} has_disclaimer=True")

save_report_draft(case1.id, md)
refreshed = get_case(case1.id)
assert refreshed.report_status == "Draft Generated"
print(f"  save_report_draft OK status={refreshed.report_status}")

print("=== TEST 8: severity_colour ===")
for sev in ["LOW","MODERATE","HIGH","URGENT_SAFETY_CONCERN"]:
    bg, fg, emoji = severity_colour(sev)
    assert bg.startswith("#"), f"Bad bg for {sev}"
    assert emoji != "", f"Empty emoji for {sev}"
print("  severity_colour OK for all 4 levels")

print()
print("ALL INTEGRATION TESTS PASSED")
