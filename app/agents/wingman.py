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
from typing import List, Dict, Any


def wingman(reasons: List[str], flags: List[Dict], profile: Dict = None, other: Dict = None) -> List[str]:
    """Generate friendly tips based on match reasons, conflicts, and profile context."""

    tips: List[str] = []
    seen: set[str] = set()

    def _clean(text: str) -> str:
        return (text or "").replace("—", "-").replace("–", "-").replace("±", "+/-")

    def _norm_key(text: str) -> str:
        return " ".join((text or "").lower().split())

    def _add_tip(text: str) -> None:
        key = _norm_key(text)
        if not key or key in seen:
            return
        seen.add(key)
        tips.append(_clean(text))

    # ---------------- Positive nudges ----------------
    if any("same city" in (r or "").lower() for r in reasons):
        _add_tip("You're in the same city - logistics are easy.")
    if any("budget" in (r or "").lower() for r in reasons):
        _add_tip("Budgets align - split rent fairly and track utilities.")

    # ---------------- Anchor context ----------------
    def _anchor_label(anchor: Dict[str, Any] | None) -> str:
        if not isinstance(anchor, dict):
            return ""
        return anchor.get("label") or anchor.get("name") or ""

    anchor_a = _anchor_label((profile or {}).get("anchor_location"))
    anchor_b = _anchor_label((other or {}).get("anchor_location"))
    if anchor_a and anchor_b:
        _add_tip(
            f"Anchors spotted: you're near {anchor_a}, they're near {anchor_b} — align commute expectations early."
        )
    elif any("anchor" in (r or "").lower() for r in reasons):
        _add_tip("💡 Easy commute - you're both anchored in the same area.")

    # ---------------- Role-based tips ----------------
    role_a = (profile or {}).get("role")
    role_b = (other or {}).get("role")
    if role_a and role_b:
        if role_a == "student" and role_b == "student":
            _add_tip("Study buddies? Set shared quiet study blocks and celebrate wins together.")
        elif role_a == "professional" and role_b == "professional":
            _add_tip("Two professionals: align on work-from-home days and split ride-share costs.")
        elif {role_a, role_b} == {"student", "professional"}:
            _add_tip("Mixed routines: share class schedules and office hours to prevent noise clashes.")

    # ---------------- Conflict resolutions ----------------
    mitigation_map = {
        "sleep_vs_guests": "Set quiet hours (10pm-7am) and keep hosting to weekends.",
        "cleanliness_mismatch": "Use a weekly cleaning rota and a shared supplies list.",
        "smoking_clash": "Keep indoor smoke-free; designate an outdoor smoking spot.",
        "anchor_too_far": "⚠️ Anchors are far apart — budget for transport or consider a midpoint.",
        "anchor_city_mismatch": "⚠️ Different anchor cities — agree on long-term plans before committing.",
        "anchor_commute_heavy": "Commute is heavy — explore ride-shares or alternating WFH days.",
        "anchor_commute_notice": "Test the commute at rush hour so surprises stay low.",
        "role_lifestyle_gap": "Sync weekly routines: post a shared calendar for classes, work shifts, and quiet hours.",
    }

    for f in flags or []:
        t = (f.get("type") or "").lower() if isinstance(f, dict) else str(f).lower()
        if not t:
            continue
        if t in mitigation_map:
            _add_tip(mitigation_map[t])
        else:
            _add_tip(f"Address potential issue: {t}")

    # ---------------- Default fallback ----------------
    if not tips:
        _add_tip("Looks compatible - align on groceries, utilities split, and quiet hours early.")

    return tips
