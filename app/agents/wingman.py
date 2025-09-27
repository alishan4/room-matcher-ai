from typing import Dict, List

def explain_and_tips(a:Dict,b:Dict,score:int,reasons:List[str],flags:List[Dict])->List[str]:
    tips: List[str] = []
    # Summarize positives
    if "Same city" in reasons: tips.append("You're in the same city—logistics are easy.")
    if any("Budgets" in r for r in reasons): tips.append("Budgets align—split rent fairly and track utilities.")
    # Resolve conflicts
    for f in flags:
        t = f.get("type")
        if t=="sleep_vs_guests":
            tips.append("Set quiet hours (10pm–7am) and prefer weekend hosting.")
        if t=="cleanliness_mismatch":
            tips.append("Create a weekly cleaning rota and shared supplies list.")
        if t=="smoking_clash":
            tips.append("Agree smoke-free indoor policy; designate an outdoor spot if needed.")
    # Default suggestion
    if not tips:
        tips.append("Message to confirm house rules (guests, quiet hours, chores).")
    # Trim in degraded mode handled by caller/UI if needed
    return tips
