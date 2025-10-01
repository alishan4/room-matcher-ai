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
import re
from typing import Dict, Any, Tuple

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


def _optional_hook(name: str):
    """Return a callable enrichment hook from app_patches if available."""
    try:
        from app_patches import profile_reader_patch  # type: ignore
    except Exception:  # pragma: no cover - optional dependency
        return None
    return getattr(profile_reader_patch, name, None)


def parse_profile_text(text: str, mode: str) -> Tuple[Dict[str, Any], float]:
    """Parse unstructured profile text into a normalized profile dict.

    The parser first applies lightweight regex/keyword heuristics so that it
    works in fully offline (``degraded``) deployments.  When optional hooks are
    available we call them to enrich the extraction – for example
    ``app_patches.profile_reader_patch.ml_enrich`` can attach ML classifiers for
    higher fidelity attributes.
    """

    raw_text = text or ""
    lower_text = raw_text.lower()

    # Early fallback for empty payloads – still pass through normalizer to make
    # sure we get consistent default values (e.g. languages).
    if not raw_text.strip():
        profile = normalize_profile({"raw_text": raw_text})
        return profile, 0.0

    extracted: Dict[str, Any] = {"raw_text": raw_text}
    heur_hits = 0
    heur_total = 0

    def _record(field: str, value: Any, weight: float = 1.0) -> None:
        nonlocal heur_hits
        if value is None:
            return
        extracted[field] = value
        heur_hits += weight

    def _probe(weight: float = 1.0) -> None:
        nonlocal heur_total
        heur_total += weight

    # --- City ---
    _probe()
    for city in [
        "karachi",
        "lahore",
        "islamabad",
        "rawalpindi",
        "peshawar",
        "multan",
        "faisalabad",
        "quetta",
        "hyderabad",
        "sialkot",
    ]:
        if re.search(rf"\b{re.escape(city)}\b", lower_text):
            _record("city", city.title())
            break

    # --- Budget ---
    _probe()
    budget_val = None
    budget_patterns = [
        re.compile(r"(?:pkr|rs|rupees)?\s*([0-9][0-9,\.]{3,})\s*(?:/\s*mo|per month|monthly|pkr|rs|rupees)?"),
        re.compile(r"([0-9]{2,})\s*[kK]\b"),
    ]
    for pat in budget_patterns:
        match = pat.search(lower_text)
        if not match:
            continue
        raw_num = match.group(1).replace(",", "").replace(".", "")
        if raw_num.endswith("k") or raw_num.endswith("K"):
            raw_num = raw_num[:-1]
        as_num = as_int(raw_num)
        if pat.pattern.endswith("[kK]\\b") and as_num is not None:
            as_num *= 1000
        if as_num:
            budget_val = as_num
            break
    if budget_val is not None:
        _record("budget", budget_val)

    # --- Sleep schedule ---
    _probe()
    sleep_guess = None
    for token in list(_SLEEP_MAP.keys()) + ["morning person", "night person"]:
        if token in lower_text:
            sleep_guess = _norm_enum(token, _SLEEP_MAP)
            if not sleep_guess and token == "morning person":
                sleep_guess = "early_bird"
            if not sleep_guess and token == "night person":
                sleep_guess = "night_owl"
            if sleep_guess:
                break
    if sleep_guess:
        _record("sleep_schedule", sleep_guess)

    # --- Cleanliness ---
    _probe()
    clean_guess = None
    if "neat" in lower_text or "tidy" in lower_text:
        clean_guess = "high"
    elif "messy" in lower_text or "laid back" in lower_text:
        clean_guess = "low"
    else:
        for token in _CLEAN_MAP.keys():
            if token in lower_text:
                clean_guess = _norm_enum(token, _CLEAN_MAP)
                break
    if clean_guess:
        _record("cleanliness", clean_guess)

    # --- Noise tolerance ---
    _probe()
    noise_guess = None
    if "quiet" in lower_text or "silence" in lower_text:
        noise_guess = "low"
    elif "party" in lower_text or "music" in lower_text:
        noise_guess = "high"
    else:
        for token in _NOISE_MAP.keys():
            if token in lower_text:
                noise_guess = _norm_enum(token, _NOISE_MAP)
                break
    if noise_guess:
        _record("noise_tolerance", noise_guess)

    # --- Guests frequency ---
    _probe()
    guests_guess = None
    if "guests" in lower_text:
        for token in _GUESTS_MAP.keys():
            if token in lower_text:
                guests_guess = _norm_enum(token, _GUESTS_MAP)
                break
        if not guests_guess and "weekend" in lower_text:
            guests_guess = "sometimes"
    if guests_guess:
        _record("guests_freq", guests_guess)

    # --- Smoking ---
    _probe()
    smoking = None
    if "non smoker" in lower_text or "non-smoker" in lower_text or "don't smoke" in lower_text:
        smoking = "no"
    elif "smoker" in lower_text or "smoke" in lower_text:
        smoking = "yes"
    if smoking:
        _record("smoking", smoking)

    # --- Role ---
    _probe()
    role_guess = None
    for token in _ROLE_MAP.keys():
        if token in lower_text:
            role_guess = _norm_enum(token, _ROLE_MAP) or token
            break
    if not role_guess:
        if "study" in lower_text or "semester" in lower_text:
            role_guess = "student"
        elif "office" in lower_text or "work" in lower_text:
            role_guess = "professional"
    if role_guess:
        _record("role", role_guess)

    # --- Food preferences ---
    _probe(0.5)
    food_guess = None
    if "vegetarian" in lower_text or "vegan" in lower_text:
        food_guess = "vegetarian"
    elif "halal" in lower_text:
        food_guess = "halal"
    elif "non veg" in lower_text or "non-veg" in lower_text:
        food_guess = "non_veg"
    if food_guess:
        _record("food_pref", food_guess, weight=0.5)

    # --- Language hints ---
    language_hits = []
    for lang, tokens in {
        "ur": ["urdu"],
        "en": ["english"],
        "pa": ["punjabi"],
        "ps": ["pashto"],
    }.items():
        if any(tok in lower_text for tok in tokens):
            language_hits.append(lang)
    if language_hits:
        extracted["languages"] = sorted(set(language_hits))

    # Optional regex enrich hook (e.g., app_patches.profile_reader_patch.regex_enrich)
    regex_hook = _optional_hook("regex_enrich")
    if callable(regex_hook):
        try:
            enriched = regex_hook(dict(extracted))
            if isinstance(enriched, dict):
                extracted.update(enriched)
        except Exception:
            pass

    # Optional ML enrich hook. Skip when running in degraded mode to avoid
    # depending on heavy models or remote services.
    if mode != "degraded":
        ml_hook = _optional_hook("ml_enrich")
        if callable(ml_hook):
            try:
                enriched = ml_hook(dict(extracted))
                if isinstance(enriched, dict):
                    extracted.update(enriched)
            except Exception:
                pass

    normalized = normalize_profile(extracted)

    coverage_fields = [
        "city",
        "budget_pkr",
        "sleep_schedule",
        "cleanliness",
        "noise_tolerance",
        "smoking",
        "guests_freq",
        "role",
        "food_pref",
    ]
    coverage = sum(1 for f in coverage_fields if normalized.get(f))
    coverage_ratio = coverage / len(coverage_fields)
    heur_ratio = heur_hits / heur_total if heur_total else 0.0

    confidence = 0.2 + 0.5 * heur_ratio + 0.3 * coverage_ratio
    if mode == "degraded":
        confidence *= 0.9
    confidence = max(0.0, min(0.99, round(confidence, 3)))

    return normalized, confidence
