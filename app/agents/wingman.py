from typing import List, Dict

def wingman(reasons: List[str], flags: List[Dict]) -> List[str]:
    tips: List[str] = []
    # positives
    if any("same city" in r.lower() for r in reasons):
        tips.append("You're in the same city - logistics are easy.")
    if any("budget" in r.lower() for r in reasons):
        tips.append("Budgets align - split rent fairly and track utilities.")

    # conflicts → suggestions
    for f in flags or []:
        t = (f.get("type") or "").lower() if isinstance(f, dict) else str(f).lower()
        if t == "sleep_vs_guests":
            tips.append("Set quiet hours (10pm-7am) and keep hosting to weekends.")
        elif t == "cleanliness_mismatch":
            tips.append("Use a weekly cleaning rota and a shared supplies list.")
        elif t == "smoking_clash":
            tips.append("Keep indoor smoke-free; designate an outdoor smoking spot.")
        elif t:
            tips.append(f"Address potential issue: {t}")

    if not tips:
        tips.append("Looks compatible - align on groceries, utilities split, and quiet hours early.")

    # normalize fancy unicode dashes → ASCII for safer rendering everywhere
    clean = []
    for t in tips:
        t2 = (t or "").replace("—", "-").replace("–", "-").replace("±", "+/-")
        clean.append(t2)
    return clean
