# app/utils/keyword_filter.py
from typing import Optional

CITY_MAP = {
    "lahore": "lahore",
    "lhr": "lahore",
    "karachi": "karachi",
    "khi": "karachi",
    "islamabad": "islamabad",
    "isb": "islamabad",
    "peshawar": "peshawar",
    "quetta": "quetta",
}

def normalize_city(s: Optional[str]) -> str:
    if not s:
        return ""
    s = s.strip().lower()
    return CITY_MAP.get(s, s)

def percent_diff(a, b) -> float:
    if not a or not b:
        return 1.0
    return abs(a - b) / max(a, b)
