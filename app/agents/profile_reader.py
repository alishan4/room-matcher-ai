# from typing import Dict
# from ..utils.num import as_int

# _BUDGET_KEYS = [
#     "budget_pkr","budget","budget_PKR","monthly_budget","rent_budget","expected_budget"
# ]

# # Map human-ish labels to our canonical enums
# _SLEEP_MAP = {
#     "early riser": "early_bird",
#     "early_bird": "early_bird",
#     "early": "early_bird",
#     "night owl": "night_owl",
#     "night_owl": "night_owl",
#     "late": "night_owl",
#     "flex": "flex",
#     "flexible": "flex",
# }

# _CLEAN_MAP = {
#     "high": "high",
#     "medium": "medium",
#     "moderate": "medium",
#     "avg": "medium",
#     "average": "medium",
#     "low": "low",
#     "messy": "low",
#     "neat": "high",
#     "tidy": "high",
# }

# _NOISE_MAP = {
#     "low": "low",
#     "quiet": "low",
#     "medium": "medium",
#     "moderate": "medium",
#     "high": "high",
#     "loud": "high",
# }

# _GUESTS_MAP = {
#     "never": "rare",
#     "rare": "rare",
#     "sometimes": "sometimes",
#     "weekly": "sometimes",
#     "often": "often",
#     "daily": "daily",
#     "frequent": "often",
# }

# def _norm_enum(val: str, table: Dict[str, str]) -> str | None:
#     if not val: return None
#     return table.get(str(val).strip().lower())

# def _pick_budget(p: Dict) -> int | None:
#     for k in _BUDGET_KEYS:
#         if k in p and p.get(k) is not None:
#             return as_int(p.get(k))
#     return None

# def normalize_profile(p: Dict) -> Dict:
#     sleep = _norm_enum(p.get("sleep_schedule"), _SLEEP_MAP)
#     clean = _norm_enum(p.get("cleanliness"), _CLEAN_MAP)
#     noise = _norm_enum(p.get("noise_tolerance"), _NOISE_MAP)
#     guests = _norm_enum(p.get("guests_freq"), _GUESTS_MAP)

#     # Some datasets use alternative field names
#     raw_text = p.get("raw_text") or p.get("raw_profile_text") or ""

#     # Normalize smoking to "yes"/"no"/None
#     sm = p.get("smoking")
#     if isinstance(sm, bool):
#         sm = "yes" if sm else "no"
#     elif isinstance(sm, str):
#         sm = sm.strip().lower()
#         if sm in ("y","yes","true"): sm = "yes"
#         elif sm in ("n","no","false"): sm = "no"
#         else: sm = None
#     else:
#         sm = None

#     out = {
#         "id": p.get("id"),
#         "name": p.get("name"),
#         "city": (p.get("city") or ""),
#         "budget_pkr": _pick_budget(p),
#         "sleep_schedule": sleep,
#         "cleanliness": clean,
#         "noise_tolerance": noise,
#         "study_habits": p.get("study_habits"),
#         "food_pref": p.get("food_pref"),
#         "smoking": sm,
#         "guests_freq": guests,
#         "gender_pref": p.get("gender_pref"),
#         "languages": p.get("languages") or ["ur","en"],
#         "raw_text": raw_text,
#     }
#     return out

# app/agents/profile_reader.py
from typing import Dict, Any
from ..utils.num import as_int

_BUDGET_KEYS = [
    "budget_pkr","budget","budget_PKR","monthly_budget","rent_budget","expected_budget"
]

_SLEEP_MAP = {
    "early riser": "early_bird",
    "early_bird": "early_bird",
    "early": "early_bird",
    "night owl": "night_owl",
    "night_owl": "night_owl",
    "late": "night_owl",
    "flex": "flex",
    "flexible": "flex",
}

_CLEAN_MAP = {
    "high": "high",
    "medium": "medium",
    "moderate": "medium",
    "avg": "medium",
    "average": "medium",
    "low": "low",
    "messy": "low",
    "neat": "high",
    "tidy": "high",
}

_NOISE_MAP = {
    "low": "low",
    "quiet": "low",
    "medium": "medium",
    "moderate": "medium",
    "high": "high",
    "loud": "high",
}

_GUESTS_MAP = {
    "never": "rare",
    "rare": "rare",
    "sometimes": "sometimes",
    "weekly": "sometimes",
    "often": "often",
    "daily": "daily",
    "frequent": "often",
}

_ROLE_MAP = {
    "student": "student",
    "undergrad": "student",
    "bs": "student",
    "professional": "professional",
    "job": "professional",
    "office": "professional",
}

def _norm_enum(val: str, table: Dict[str, str]) -> str | None:
    if not val: return None
    return table.get(str(val).strip().lower())

def _pick_budget(p: Dict) -> int | None:
    for k in _BUDGET_KEYS:
        if k in p and p.get(k) is not None:
            return as_int(p.get(k))
    return None

def normalize_profile(p: Dict[str, Any]) -> Dict[str, Any]:
    sleep = _norm_enum(p.get("sleep_schedule"), _SLEEP_MAP)
    clean = _norm_enum(p.get("cleanliness"), _CLEAN_MAP)
    noise = _norm_enum(p.get("noise_tolerance"), _NOISE_MAP)
    guests = _norm_enum(p.get("guests_freq"), _GUESTS_MAP)
    role = _norm_enum(p.get("role"), _ROLE_MAP)

    # Some datasets use alternative field names
    raw_text = p.get("raw_text") or p.get("raw_profile_text") or ""

    # Normalize smoking to "yes"/"no"/None
    sm = p.get("smoking")
    if isinstance(sm, bool):
        sm = "yes" if sm else "no"
    elif isinstance(sm, str):
        sm = sm.strip().lower()
        if sm in ("y","yes","true"): sm = "yes"
        elif sm in ("n","no","false"): sm = "no"
        else: sm = None
    else:
        sm = None

    # Anchor location (structured dict if exists)
    anchor = None
    if isinstance(p.get("anchor_location"), dict):
        anchor = {
            "label": p["anchor_location"].get("label"),
            "lat": p["anchor_location"].get("lat"),
            "lng": p["anchor_location"].get("lng")
        }

    # Geo location (structured dict if exists)
    geo = None
    if isinstance(p.get("geo"), dict):
        geo = {
            "lat": p["geo"].get("lat"),
            "lng": p["geo"].get("lng"),
            "source": p["geo"].get("source", "unknown")
        }

    out = {
        "id": p.get("id"),
        "name": p.get("name"),
        "role": role,
        "city": (p.get("city") or ""),
        "budget_pkr": _pick_budget(p),
        "sleep_schedule": sleep,
        "cleanliness": clean,
        "noise_tolerance": noise,
        "study_habits": p.get("study_habits"),
        "food_pref": p.get("food_pref"),
        "smoking": sm,
        "guests_freq": guests,
        "gender_pref": p.get("gender_pref"),
        "languages": p.get("languages") or ["ur","en"],
        "anchor_location": anchor,
        "geo": geo,
        "raw_text": raw_text,
    }
    return out
