# W = dict(city=10, budget=25, sleep=15, cleanliness=15, noise=10, study=10, smoking=8, guests=7)  # total 100

# def score_pair(a, b):
#     s = {"city":0,"budget":0,"sleep":0,"cleanliness":0,"noise":0,"study":0,"smoking":0,"guests":0}
#     reasons = []

#     if a.get("city") and b.get("city") and a["city"] == b["city"]:
#         s["city"] = W["city"]; reasons.append("Same city")

#     if a.get("budget_pkr") and b.get("budget_pkr"):
#         win = max(2000, int(0.2 * a["budget_pkr"]))
#         if abs(a["budget_pkr"] - b["budget_pkr"]) <= win:
#             s["budget"] = W["budget"]; reasons.append("Budgets align (±20%)")

#     if a.get("sleep_schedule") and b.get("sleep_schedule") and a["sleep_schedule"] == b["sleep_schedule"]:
#         s["sleep"] = W["sleep"]; reasons.append("Similar sleep schedule")

#     if a.get("cleanliness") and b.get("cleanliness") and a["cleanliness"] == b["cleanliness"]:
#         s["cleanliness"] = W["cleanliness"]; reasons.append("Same cleanliness preference")

#     if a.get("noise_tolerance") and b.get("noise_tolerance") and a["noise_tolerance"] == b["noise_tolerance"]:
#         s["noise"] = W["noise"]; reasons.append("Noise tolerance looks compatible")

#     if a.get("study_habits") and b.get("study_habits"):
#         if ("library" in a["study_habits"] and "library" in b["study_habits"]) or                ("home" in a["study_habits"] and "home" in b["study_habits"]):
#             s["study"] = W["study"]; reasons.append("Study habits match")

#     if a.get("smoking") == b.get("smoking"):
#         s["smoking"] = W["smoking"]; reasons.append("Smoking preference aligned")

#     if a.get("guests_freq") and b.get("guests_freq") and a["guests_freq"] == b["guests_freq"]:
#         s["guests"] = W["guests"]; reasons.append("Similar guest frequency")

#     total = sum(s.values())
#     return total, reasons, s


# app/agents/match_scorer.py
from typing import Dict, Tuple, List
from math import radians, sin, cos, sqrt, atan2
from ..utils.num import as_int

# ---------------- Weights ----------------
W = dict(
    city=10,
    budget=20,
    sleep=12,
    cleanliness=12,
    noise=8,
    study=8,
    smoking=8,
    guests=7,
    role=5,
    anchor=10  # new!
)
# total = 100

# ---------------- Helpers ----------------
def haversine_km(loc1: Dict, loc2: Dict) -> float:
    """Distance in km between two lat/lng dicts."""
    try:
        lat1, lon1 = float(loc1["lat"]), float(loc1["lng"])
        lat2, lon2 = float(loc2["lat"]), float(loc2["lng"])
    except Exception:
        return 9999  # invalid coords = far away

    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

# ---------------- Core Scorer ----------------
def score_pair(a: Dict, b: Dict) -> Tuple[int, List[str], Dict[str,int]]:
    s = {k:0 for k in W}
    reasons = []

    # --- City ---
    if a.get("city") and b.get("city") and a["city"] == b["city"]:
        s["city"] = W["city"]; reasons.append("Same city")

    # --- Budget ---
    ab, bb = as_int(a.get("budget_pkr")), as_int(b.get("budget_pkr"))
    if ab and bb:
        win = max(2000, int(0.2 * ab))
        if abs(ab - bb) <= win:
            s["budget"] = W["budget"]; reasons.append("Budgets align (±20%)")

    # --- Sleep ---
    if a.get("sleep_schedule") and b.get("sleep_schedule") and a["sleep_schedule"] == b["sleep_schedule"]:
        s["sleep"] = W["sleep"]; reasons.append("Similar sleep schedule")

    # --- Cleanliness ---
    if a.get("cleanliness") and b.get("cleanliness") and a["cleanliness"] == b["cleanliness"]:
        s["cleanliness"] = W["cleanliness"]; reasons.append("Same cleanliness preference")

    # --- Noise ---
    if a.get("noise_tolerance") and b.get("noise_tolerance") and a["noise_tolerance"] == b["noise_tolerance"]:
        s["noise"] = W["noise"]; reasons.append("Noise tolerance looks compatible")

    # --- Study habits ---
    if a.get("study_habits") and b.get("study_habits"):
        if ("library" in a["study_habits"] and "library" in b["study_habits"]) or \
           ("home" in a["study_habits"] and "home" in b["study_habits"]):
            s["study"] = W["study"]; reasons.append("Study habits match")

    # --- Smoking ---
    if a.get("smoking") and b.get("smoking") and a["smoking"] == b["smoking"]:
        s["smoking"] = W["smoking"]; reasons.append("Smoking preference aligned")

    # --- Guests ---
    if a.get("guests_freq") and b.get("guests_freq") and a["guests_freq"] == b["guests_freq"]:
        s["guests"] = W["guests"]; reasons.append("Similar guest frequency")

    # --- Role (student/professional) ---
    if a.get("role") and b.get("role") and a["role"] == b["role"]:
        s["role"] = W["role"]; reasons.append(f"Both are {a['role']}s")

    # --- Anchor location (distance-based) ---
    if a.get("anchor_location") and b.get("anchor_location"):
        d = haversine_km(a["anchor_location"], b["anchor_location"])
        if d <= 2:
            s["anchor"] = W["anchor"]; reasons.append("Same anchor location")
        elif d <= 5:
            s["anchor"] = int(W["anchor"] * 0.8); reasons.append("Anchors very close (<5 km)")
        elif d <= 20:
            s["anchor"] = int(W["anchor"] * 0.5); reasons.append("Anchors in same area (<20 km)")
        else:
            reasons.append("Anchors far apart")

    total = sum(s.values())
    return total, reasons, s
