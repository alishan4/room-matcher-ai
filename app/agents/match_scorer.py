from typing import Dict, Tuple, List

def _enum_align(a,b,full:int, label:str, conflicts:List[str]):
    if not a or not b: return 0
    if a==b: return full
    # partial: night_owl vs flexible
    if "flex" in (a or "") or "flex" in (b or ""):
        return int(full*0.6)
    conflicts.append(f"{label} mismatch")
    return 0

def _pct_diff(x:int,y:int)->float:
    if not x or not y: return 1.0
    return abs(x-y)/max(x,y)

def score_pair(a:Dict,b:Dict)->Tuple[int,List[str],Dict]:
    score = 0
    reasons: List[str] = []
    subs = {}

    # City
    if a.get("city") and b.get("city") and a["city"].lower()==b["city"].lower():
        score += 15; subs["city"]=15; reasons.append("Same city")
    else:
        subs["city"]=0

    # Budget per-person alignment
    pd = _pct_diff(a.get("budget_pkr"), b.get("budget_pkr"))
    if pd <= 0.15: score += 20; subs["budget"]=20; reasons.append(f"Budgets within {int(pd*100)}%")
    elif pd <= 0.25: score += 10; subs["budget"]=10; reasons.append("Budgets close")
    else: subs["budget"]=0

    conflicts: List[str] = []

    # Sleep
    sleep_pts = _enum_align(a.get("sleep_schedule"), b.get("sleep_schedule"), 15, "Sleep schedule", conflicts)
    score += sleep_pts; subs["sleep"]=sleep_pts
    if sleep_pts==15 and a.get("sleep_schedule"): reasons.append("Same sleep schedule")

    # Cleanliness
    clean_pts = _enum_align(a.get("cleanliness"), b.get("cleanliness"), 15, "Cleanliness", conflicts)
    score += clean_pts; subs["cleanliness"]=clean_pts
    if clean_pts==15 and a.get("cleanliness"): reasons.append("Cleanliness aligned")

    # Noise tolerance
    noise_pts = _enum_align(a.get("noise_tolerance"), b.get("noise_tolerance"), 10, "Noise tolerance", conflicts)
    score += noise_pts; subs["noise"]=noise_pts
    if noise_pts==10 and a.get("noise_tolerance"): reasons.append("Similar noise tolerance")

    # Study habits (simple)
    study_pts = _enum_align(a.get("study_habits"), b.get("study_habits"), 10, "Study habits", conflicts)
    score += study_pts; subs["study"]=study_pts

    # Smoking
    sm_a, sm_b = a.get("smoking"), b.get("smoking")
    if sm_a and sm_b:
        if sm_a==sm_b: score += 5; subs["smoking"]=5; reasons.append("Smoking preference aligned")
        elif sm_a=="no" and sm_b=="yes" or sm_a=="yes" and sm_b=="no":
            conflicts.append("Smoking clash"); subs["smoking"]=0
        else: subs["smoking"]=2
    else: subs["smoking"]=0

    # Guests frequency (rare/sometimes/often)
    gf_a, gf_b = a.get("guests_freq"), b.get("guests_freq")
    if gf_a and gf_b:
        if gf_a==gf_b: score += 5; subs["guests"]=5; reasons.append("Guests expectations aligned")
        else: subs["guests"]=0
    else: subs["guests"]=0

    score = min(100, score)
    return score, reasons, subs
