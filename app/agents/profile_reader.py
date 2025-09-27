import re
from typing import Dict, Tuple
from ..utils.lexicons import LEX

INT = lambda s: int(re.sub(r'[,_. ]','',s)) if s else None

BUDGET_RE = re.compile(r'(?:PKR|Rs|Rupees|rup(?:ee|ay)?)[\s:]*([0-9][0-9,_. ]+)', re.I)
TIME_10PM_RE = re.compile(r'(\b10\s*pm\b)|(\b10\s*bjy\b)', re.I)

def parse_profile_text(text:str, mode:str='degraded')->Tuple[Dict,Dict]:
    text_low = text.lower()
    prof = {
        "id": None,
        "name": None,
        "city": None,
        "budget_pkr": None,
        "sleep_schedule": None,
        "cleanliness": None,
        "noise_tolerance": None,
        "study_habits": None,
        "food_pref": None,
        "smoking": None,
        "guests_freq": None,
        "gender_pref": None,
        "languages": ["ur","en"],
        "raw_text": text
    }
    conf = {}

    # budget
    m = BUDGET_RE.search(text)
    if m:
        prof["budget_pkr"] = INT(m.group(1)); conf["budget"] = 0.9

    # sleep
    if any(k in text_low for k in LEX["night_owl"]):
        prof["sleep_schedule"] = "night_owl"; conf["sleep"] = 0.8
    elif any(k in text_low for k in LEX["early_bird"]) or TIME_10PM_RE.search(text_low):
        prof["sleep_schedule"] = "early_bird"; conf["sleep"] = 0.7

    # cleanliness
    if any(k in text_low for k in LEX["clean_high"]):
        prof["cleanliness"] = "high"; conf["cleanliness"] = 0.75
    elif any(k in text_low for k in LEX["clean_low"]):
        prof["cleanliness"] = "low"; conf["cleanliness"] = 0.7

    # noise/quiet
    if any(k in text_low for k in LEX["quiet"]):
        prof["noise_tolerance"] = "low"; conf["noise"] = 0.7
    elif any(k in text_low for k in LEX["party"]) or any(k in text_low for k in LEX["music"]):
        prof["noise_tolerance"] = "high"; conf["noise"] = 0.7

    # smoking
    if any(k in text_low for k in LEX["smoking_yes"]): prof["smoking"]="yes"; conf["smoking"]=0.7
    if any(k in text_low for k in LEX["smoking_no"]): prof["smoking"]="no"; conf["smoking"]=0.7

    # guests
    if any(k in text_low for k in LEX["party"]):
        prof["guests_freq"] = "often"; conf["guests"]=0.7

    return prof, conf

def normalize_profile(p:Dict)->Dict:
    # Ensure keys exist and normalize typical enums
    out = {
        "id": p.get("id"),
        "name": p.get("name"),
        "city": (p.get("city") or ""),
        "budget_pkr": p.get("budget_pkr"),
        "sleep_schedule": p.get("sleep_schedule"),
        "cleanliness": p.get("cleanliness"),
        "noise_tolerance": p.get("noise_tolerance"),
        "study_habits": p.get("study_habits"),
        "food_pref": p.get("food_pref"),
        "smoking": p.get("smoking"),
        "guests_freq": p.get("guests_freq"),
        "gender_pref": p.get("gender_pref"),
        "languages": p.get("languages") or ["ur","en"],
        "raw_text": p.get("raw_text",""),
    }
    return out
