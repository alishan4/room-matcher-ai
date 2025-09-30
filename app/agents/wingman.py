# from typing import List, Dict

# def wingman(reasons: List[str], flags: List[Dict]) -> List[str]:
#     tips: List[str] = []
#     # positives
#     if any("same city" in r.lower() for r in reasons):
#         tips.append("You're in the same city - logistics are easy.")
#     if any("budget" in r.lower() for r in reasons):
#         tips.append("Budgets align - split rent fairly and track utilities.")

#     # conflicts → suggestions
#     for f in flags or []:
#         t = (f.get("type") or "").lower() if isinstance(f, dict) else str(f).lower()
#         if t == "sleep_vs_guests":
#             tips.append("Set quiet hours (10pm-7am) and keep hosting to weekends.")
#         elif t == "cleanliness_mismatch":
#             tips.append("Use a weekly cleaning rota and a shared supplies list.")
#         elif t == "smoking_clash":
#             tips.append("Keep indoor smoke-free; designate an outdoor smoking spot.")
#         elif t:
#             tips.append(f"Address potential issue: {t}")

#     if not tips:
#         tips.append("Looks compatible - align on groceries, utilities split, and quiet hours early.")

#     # normalize fancy unicode dashes → ASCII for safer rendering everywhere
#     clean = []
#     for t in tips:
#         t2 = (t or "").replace("—", "-").replace("–", "-").replace("±", "+/-")
#         clean.append(t2)
#     return clean

# app/agents/wingman.py
from typing import List, Dict

def wingman(reasons: List[str], flags: List[Dict], profile: Dict = None, other: Dict = None) -> List[str]:
    """
    Generate friendly tips based on match reasons, conflicts, and profile context.
    """
    tips: List[str] = []

    # ---------------- Positive nudges ----------------
    if any("same city" in r.lower() for r in reasons):
        tips.append("You're in the same city - logistics are easy.")
    if any("budget" in r.lower() for r in reasons):
        tips.append("Budgets align - split rent fairly and track utilities.")

    # ---------------- Role-based tips ----------------
    if profile and other:
        role_a, role_b = profile.get("role"), other.get("role")
        if role_a and role_b:
            if role_a == "student" and role_b == "student":
                tips.append("💡 Plan shared study hours or library sessions.")
            elif role_a == "professional" and role_b == "professional":
                tips.append("💡 Share commute costs or coordinate office timings.")
            elif {role_a, role_b} == {"student", "professional"}:
                tips.append("💡 Respect different routines: classes vs office work.")

    # ---------------- Anchor-based tips ----------------
    if reasons:
        for r in reasons:
            if "anchor" in r.lower() or "same anchor" in r.lower() or "close" in r.lower():
                tips.append("💡 Easy commute - you’re both anchored in the same area.")

    # ---------------- Conflict resolutions ----------------
    for f in flags or []:
        t = (f.get("type") or "").lower() if isinstance(f, dict) else str(f).lower()
        if t == "sleep_vs_guests":
            tips.append("Set quiet hours (10pm-7am) and keep hosting to weekends.")
        elif t == "cleanliness_mismatch":
            tips.append("Use a weekly cleaning rota and a shared supplies list.")
        elif t == "smoking_clash":
            tips.append("Keep indoor smoke-free; designate an outdoor smoking spot.")
        elif t == "anchor_too_far":
            tips.append("⚠️ Anchors are far apart - consider transport or relocation options.")
        elif t == "anchor_city_mismatch":
            tips.append("⚠️ Different anchor cities - this may not be practical long-term.")
        elif t:
            tips.append(f"Address potential issue: {t}")

    # ---------------- Default fallback ----------------
    if not tips:
        tips.append("Looks compatible - align on groceries, utilities split, and quiet hours early.")

    # Normalize fancy unicode dashes
    clean = []
    for t in tips:
        t2 = (t or "").replace("—", "-").replace("–", "-").replace("±", "+/-")
        clean.append(t2)

    return clean
