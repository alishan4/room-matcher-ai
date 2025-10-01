# # app/agents/red_flag.py
# from typing import Dict, List, Any

# def _norm(v: Any) -> str:
#     return (str(v or "").strip().lower())

# def _score_gap(a: Dict, b: Dict, key: str) -> int:
#     """Simple 0/1/2 mismatch score for categorical fields."""
#     va, vb = _norm(a.get(key)), _norm(b.get(key))
#     if not va or not vb:
#         return 0
#     return 0 if va == vb else 2

# def _budget_gap(a: Dict, b: Dict) -> float:
#     try:
#         qa = float(a.get("budget_pkr") or 0)
#         qb = float(b.get("budget_pkr") or 0)
#         if not qa or not qb:
#             return 0.0
#         return abs(qa - qb) / max(qa, qb)
#     except Exception:
#         return 0.0

# def red_flags(a: Dict, b: Dict) -> List[Dict[str, str]]:
#     """
#     Return a list of conflicts: [{type, severity, details}, ...]
#     Keep them short and machine-friendly; frontend will pretty-print.
#     """
#     A = {k: _norm(v) for k, v in (a or {}).items()}
#     B = {k: _norm(v) for k, v in (b or {}).items()}
#     flags: List[Dict[str, str]] = []

#     # --- Smoking clash ---
#     if A.get("smoking") and B.get("smoking"):
#         if (A["smoking"] == "no" and B["smoking"] == "yes") or (A["smoking"] == "yes" and B["smoking"] == "no"):
#             flags.append({
#                 "type": "smoking_clash",
#                 "severity": "high",
#                 "details": "One smokes, the other does not"
#             })

#     # --- Sleep vs guests / noise ---
#     # Early bird + daily/often guests or high noise vs low noise tolerance
#     sleep_pair = (A.get("sleep_schedule"), B.get("sleep_schedule"))
#     guests_pair = (A.get("guests_freq"), B.get("guests_freq"))
#     noise_pair  = (A.get("noise_tolerance"), B.get("noise_tolerance"))

#     def _often(x: str) -> bool:
#         return x in ("often", "daily", "frequent", "always")

#     if any(s in ("early_bird", "early riser") for s in sleep_pair) and any(_often(g) for g in guests_pair):
#         flags.append({
#             "type": "sleep_vs_guests",
#             "severity": "medium",
#             "details": "Early riser with frequent hosting"
#         })

#     # Noise mismatch (low vs high)
#     if {"low", "high"} <= set([noise_pair[0] or "", noise_pair[1] or ""]):
#         flags.append({
#             "type": "noise_mismatch",
#             "severity": "medium",
#             "details": "Low noise tolerance vs high noise preference"
#         })

#     # --- Cleanliness mismatch (high vs low) ---
#     clean_pair = (A.get("cleanliness"), B.get("cleanliness"))
#     if {"high", "low"} <= set([clean_pair[0] or "", clean_pair[1] or ""]):
#         flags.append({
#             "type": "cleanliness_mismatch",
#             "severity": "medium",
#             "details": "High vs low cleanliness preference"
#         })

#     # --- Study habits clash (e.g., 'late night' vs 'early') ---
#     study_pair = (A.get("study_habits"), B.get("study_habits"))
#     study_txt = " / ".join([x for x in study_pair if x])
#     if ("late" in study_txt and "early" in study_txt) or ("group" in study_txt and "quiet" in study_txt):
#         flags.append({
#             "type": "study_routine_clash",
#             "severity": "low",
#             "details": "Different study routines"
#         })

#     # --- Budget gap (> 35%) still a red flag even if 'reasons' say ±20% ---
#     gap = _budget_gap(a, b)
#     if gap > 0.35:
#         flags.append({
#             "type": "budget_gap",
#             "severity": "low",
#             "details": f"Budget gap ~{int(gap*100)}%"
#         })

#     return flags

# app/agents/red_flag.py
from typing import Dict, List, Any
from math import radians, sin, cos, sqrt, atan2

COMMUTE_COST_PER_KM = 40  # Rough PKR cost per km (one-way) for daily commute

def _norm(v: Any) -> str:
    return (str(v or "").strip().lower())

def _score_gap(a: Dict, b: Dict, key: str) -> int:
    va, vb = _norm(a.get(key)), _norm(b.get(key))
    if not va or not vb:
        return 0
    return 0 if va == vb else 2

def _budget_gap(a: Dict, b: Dict) -> float:
    try:
        qa = float(a.get("budget_pkr") or 0)
        qb = float(b.get("budget_pkr") or 0)
        if not qa or not qb:
            return 0.0
        return abs(qa - qb) / max(qa, qb)
    except Exception:
        return 0.0

def haversine_km(loc1: Dict, loc2: Dict) -> float:
    try:
        lat1, lon1 = float(loc1["lat"]), float(loc1["lng"])
        lat2, lon2 = float(loc2["lat"]), float(loc2["lng"])
    except Exception:
        return 9999
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def red_flags(a: Dict, b: Dict) -> List[Dict[str, str]]:
    """
    Return a list of conflicts: [{type, severity, details}, ...]
    """
    A = {k: _norm(v) for k, v in (a or {}).items()}
    B = {k: _norm(v) for k, v in (b or {}).items()}
    flags: List[Dict[str, str]] = []

    def _role_label(role_key: str) -> str:
        mapping = {
            "student": "student",
            "professional": "working professional",
        }
        return mapping.get(role_key, role_key or "")

    # --- Smoking clash ---
    if A.get("smoking") and B.get("smoking"):
        if (A["smoking"] == "no" and B["smoking"] == "yes") or (A["smoking"] == "yes" and B["smoking"] == "no"):
            flags.append({
                "type": "smoking_clash",
                "severity": "high",
                "details": "One smokes, the other does not"
            })

    # --- Sleep vs guests / noise ---
    sleep_pair = (A.get("sleep_schedule"), B.get("sleep_schedule"))
    guests_pair = (A.get("guests_freq"), B.get("guests_freq"))
    noise_pair  = (A.get("noise_tolerance"), B.get("noise_tolerance"))

    def _often(x: str) -> bool:
        return x in ("often", "daily", "frequent", "always")

    if any(s in ("early_bird", "early riser") for s in sleep_pair) and any(_often(g) for g in guests_pair):
        flags.append({
            "type": "sleep_vs_guests",
            "severity": "medium",
            "details": "Early riser with frequent hosting"
        })

    if {"low", "high"} <= set([noise_pair[0] or "", noise_pair[1] or ""]):
        flags.append({
            "type": "noise_mismatch",
            "severity": "medium",
            "details": "Low noise tolerance vs high noise preference"
        })

    clean_pair = (A.get("cleanliness"), B.get("cleanliness"))
    if {"high", "low"} <= set([clean_pair[0] or "", clean_pair[1] or ""]):
        flags.append({
            "type": "cleanliness_mismatch",
            "severity": "medium",
            "details": "High vs low cleanliness preference"
        })

    study_pair = (A.get("study_habits"), B.get("study_habits"))
    study_txt = " / ".join([x for x in study_pair if x])
    if ("late" in study_txt and "early" in study_txt) or ("group" in study_txt and "quiet" in study_txt):
        flags.append({
            "type": "study_routine_clash",
            "severity": "low",
            "details": "Different study routines"
        })

    # --- Role lifestyle gap (e.g., student vs professional) ---
    role_a, role_b = A.get("role"), B.get("role")
    if role_a and role_b and role_a != role_b:
        flags.append({
            "type": "role_lifestyle_gap",
            "severity": "medium",
            "details": f"Different routines: {_role_label(role_a)} vs {_role_label(role_b)}"
        })

    gap = _budget_gap(a, b)
    if gap > 0.35:
        flags.append({
            "type": "budget_gap",
            "severity": "low",
            "details": f"Budget gap ~{int(gap*100)}%"
        })

    # --- Anchor conflicts ---
    a_anchor, b_anchor = a.get("anchor_location"), b.get("anchor_location")
    if isinstance(a_anchor, dict) and isinstance(b_anchor, dict):
        def _label(anchor: Dict[str, Any]) -> str:
            return anchor.get("label") or anchor.get("name") or "their anchor"

        label_a = _label(a_anchor)
        label_b = _label(b_anchor)

        # Different cities in anchor labels
        if a_anchor.get("label") and b_anchor.get("label"):
            if a_anchor["label"].split(",")[0].strip().lower() != b_anchor["label"].split(",")[0].strip().lower():
                flags.append({
                    "type": "anchor_city_mismatch",
                    "severity": "high",
                    "details": f"Different anchor cities: {a_anchor['label']} vs {b_anchor['label']}"
                })

        def _commute_cost(distance_km: float) -> int:
            # Two-way commute estimate (there and back)
            return int(max(distance_km, 0) * 2 * COMMUTE_COST_PER_KM)

        d = haversine_km(a_anchor, b_anchor)
        if d > 0 and d <= 10:
            pass  # Considered fine, no flag
        elif 10 < d <= 25:
            flags.append({
                "type": "anchor_commute_notice",
                "severity": "low",
                "details": f"Commute between {label_a} and {label_b} is ~{int(d)} km (≈PKR {_commute_cost(d)} / day)"
            })
        elif 25 < d <= 50:
            flags.append({
                "type": "anchor_commute_heavy",
                "severity": "medium",
                "details": f"Lengthy commute: {label_a} ↔ {label_b} ~{int(d)} km (≈PKR {_commute_cost(d)} / day)"
            })
        elif d > 50:
            flags.append({
                "type": "anchor_too_far",
                "severity": "high",
                "details": f"Anchors {label_a} and {label_b} are {int(d)} km apart (≈PKR {_commute_cost(d)} / day)"
            })

    return flags
