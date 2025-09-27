W = dict(city=10, budget=25, sleep=15, cleanliness=15, noise=10, study=10, smoking=8, guests=7)  # total 100

def score_pair(a, b):
    s = {"city":0,"budget":0,"sleep":0,"cleanliness":0,"noise":0,"study":0,"smoking":0,"guests":0}
    reasons = []

    if a.get("city") and b.get("city") and a["city"] == b["city"]:
        s["city"] = W["city"]; reasons.append("Same city")

    if a.get("budget_pkr") and b.get("budget_pkr"):
        win = max(2000, int(0.2 * a["budget_pkr"]))
        if abs(a["budget_pkr"] - b["budget_pkr"]) <= win:
            s["budget"] = W["budget"]; reasons.append("Budgets align (±20%)")

    if a.get("sleep_schedule") and b.get("sleep_schedule") and a["sleep_schedule"] == b["sleep_schedule"]:
        s["sleep"] = W["sleep"]; reasons.append("Similar sleep schedule")

    if a.get("cleanliness") and b.get("cleanliness") and a["cleanliness"] == b["cleanliness"]:
        s["cleanliness"] = W["cleanliness"]; reasons.append("Same cleanliness preference")

    if a.get("noise_tolerance") and b.get("noise_tolerance") and a["noise_tolerance"] == b["noise_tolerance"]:
        s["noise"] = W["noise"]; reasons.append("Noise tolerance looks compatible")

    if a.get("study_habits") and b.get("study_habits"):
        if ("library" in a["study_habits"] and "library" in b["study_habits"]) or                ("home" in a["study_habits"] and "home" in b["study_habits"]):
            s["study"] = W["study"]; reasons.append("Study habits match")

    if a.get("smoking") == b.get("smoking"):
        s["smoking"] = W["smoking"]; reasons.append("Smoking preference aligned")

    if a.get("guests_freq") and b.get("guests_freq") and a["guests_freq"] == b["guests_freq"]:
        s["guests"] = W["guests"]; reasons.append("Similar guest frequency")

    total = sum(s.values())
    return total, reasons, s
