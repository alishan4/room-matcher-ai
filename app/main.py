# # app/main.py
# import os, time
# from typing import List, Optional, Dict, Any
# from fastapi import FastAPI, Header
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from .graph import run_pipeline
# from .services.firestore import fetch_all_profiles, fetch_all_listings

# SERVER_DEFAULT_MODE = os.getenv("MODE", "online").lower()
# FIRESTORE_ENABLED = os.getenv("FIRESTORE_ENABLED", "true").lower() == "true"

# CACHE_TTL_SEC = int(os.getenv("CACHE_TTL_SEC", "120"))
# _profiles_cache: List[Dict[str, Any]] = []
# _listings_cache: List[Dict[str, Any]] = []
# _cache_at: float = 0.0
# LAST_EFFECTIVE_MODE = SERVER_DEFAULT_MODE

# def _load_cached() -> None:
#     global _profiles_cache, _listings_cache, _cache_at
#     now = time.time()
#     if now - _cache_at < CACHE_TTL_SEC and _profiles_cache and _listings_cache:
#         return
#     # Read once (normalized inside fetch_all_*)
#     _profiles_cache = fetch_all_profiles()
#     _listings_cache = fetch_all_listings()
#     _cache_at = now

# def _mode(req_mode: Optional[str], header_mode: Optional[str]) -> str:
#     global LAST_EFFECTIVE_MODE
#     m = (req_mode or header_mode or SERVER_DEFAULT_MODE).lower()
#     if m not in ("online", "degraded"):
#         m = SERVER_DEFAULT_MODE
#     LAST_EFFECTIVE_MODE = m
#     return m

# app = FastAPI(title="Room Matcher AI", version="0.3.0")
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=False,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# class Profile(BaseModel):
#     id: Optional[str] = None
#     name: Optional[str] = None
#     city: Optional[str] = None
#     budget_pkr: Optional[int] = None
#     sleep_schedule: Optional[str] = None
#     cleanliness: Optional[str] = None
#     noise_tolerance: Optional[str] = None
#     study_habits: Optional[str] = None
#     food_pref: Optional[str] = None
#     smoking: Optional[str] = None
#     guests_freq: Optional[str] = None
#     gender_pref: Optional[str] = None
#     languages: Optional[List[str]] = None
#     raw_text: Optional[str] = None

# class ParseReq(BaseModel):
#     text: str
#     mode: Optional[str] = None

# class MatchTopReq(BaseModel):
#     profile: Profile
#     k: int = 5
#     mode: Optional[str] = None

# class RoomSuggestReq(BaseModel):
#     city: str
#     per_person_budget: int
#     needed_amenities: List[str] = []
#     mode: Optional[str] = None

# @app.get("/healthz")
# def healthz():
#     return {
#         "status": "ok",
#         "server_default_mode": SERVER_DEFAULT_MODE,
#         "last_effective_mode": LAST_EFFECTIVE_MODE,
#         "firestore_enabled": FIRESTORE_ENABLED,
#         "project": os.getenv("GCP_PROJECT"),
#         "profiles_cached": len(_profiles_cache),
#         "listings_cached": len(_listings_cache),
#         "cache_age_sec": max(0, int(time.time() - _cache_at)) if _cache_at else None,
#         "cache_ttl_sec": CACHE_TTL_SEC,
#     }

# @app.post("/profiles/parse")
# def parse_profile(req: ParseReq, x_mode: Optional[str] = Header(None)):
#     mode = _mode(req.mode, x_mode)

#     from .agents.profile_reader import parse_profile_text
#     prof, conf = parse_profile_text(req.text, mode=mode)
#     return {"profile": prof, "confidence": conf, "mode_used": mode}

#     try:
#         from .agents.profile_reader import parse_profile_text
#         prof, conf = parse_profile_text(req.text or "", mode=mode)
#         return {"profile": prof, "confidence": conf, "mode_used": mode}
#     except Exception as e:
#         # Prevent crash, return fallback
#         fallback = {
#             "city": None,
#             "budget_pkr": None,
#             "sleep_schedule": None,
#             "cleanliness": None,
#             "noise_tolerance": None,
#             "smoking": None,
#             "guests_freq": None,
#             "raw_text": req.text or ""
#         }
#         return {
#             "profile": fallback,
#             "confidence": 0.0,
#             "mode_used": mode,
#             "warning": f"parse_error: {str(e)}"
#         }



# @app.post("/match/top")
# def match_top(req: MatchTopReq, x_mode: Optional[str] = Header(None)):
#     mode = _mode(req.mode, x_mode)
#     _load_cached()
#     result = run_pipeline(
#         input_profile=req.profile.dict(),
#         candidates=_profiles_cache,
#         listings=_listings_cache,
#         mode=mode,
#         top_k=req.k
#     )
#     return JSONResponse(result)

# @app.post("/rooms/suggest")
# def rooms_suggest(req: RoomSuggestReq, x_mode: Optional[str] = Header(None)):
#     mode = _mode(req.mode, x_mode)
#     _load_cached()
#     from .agents.room_hunter import suggest_rooms
#     out = suggest_rooms(req.city, req.per_person_budget, req.needed_amenities, _listings_cache, mode=mode, limit=5)
#     return {"listings": out, "mode_used": mode}

# app/main.py

import os, time
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .graph import run_pipeline
from .services.firestore import fetch_all_profiles, fetch_all_listings


SERVER_DEFAULT_MODE = os.getenv("MODE", "online").lower()
FIRESTORE_ENABLED = os.getenv("FIRESTORE_ENABLED", "true").lower() == "true"

CACHE_TTL_SEC = int(os.getenv("CACHE_TTL_SEC", "120"))
_profiles_cache: List[Dict[str, Any]] = []
_listings_cache: List[Dict[str, Any]] = []
_cache_at: float = 0.0
LAST_EFFECTIVE_MODE = SERVER_DEFAULT_MODE


# ---------------- Cache helpers ----------------
def _load_cached() -> None:
    global _profiles_cache, _listings_cache, _cache_at
    now = time.time()
    if now - _cache_at < CACHE_TTL_SEC and _profiles_cache and _listings_cache:
        return
    _profiles_cache = fetch_all_profiles()
    _listings_cache = fetch_all_listings()
    _cache_at = now


def _mode(req_mode: Optional[str], header_mode: Optional[str]) -> str:
    global LAST_EFFECTIVE_MODE
    m = (req_mode or header_mode or SERVER_DEFAULT_MODE).lower()
    if m not in ("online", "degraded"):
        m = SERVER_DEFAULT_MODE
    LAST_EFFECTIVE_MODE = m
    return m


# ---------------- FastAPI app ----------------
app = FastAPI(title="Room Matcher AI", version="0.4.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- Models ----------------
class Profile(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    city: Optional[str] = None
    budget_pkr: Optional[int] = None
    sleep_schedule: Optional[str] = None
    cleanliness: Optional[str] = None
    noise_tolerance: Optional[str] = None
    study_habits: Optional[str] = None
    food_pref: Optional[str] = None
    smoking: Optional[str] = None
    guests_freq: Optional[str] = None
    gender_pref: Optional[str] = None
    languages: Optional[List[str]] = None
    role: Optional[str] = None
    anchor_location: Optional[Dict[str, Any]] = None
    geo: Optional[Dict[str, float]] = None
    raw_text: Optional[str] = None


class ParseReq(BaseModel):
    text: str
    mode: Optional[str] = None


class MatchTopReq(BaseModel):
    profile: Profile
    k: int = 5
    mode: Optional[str] = None


class RoomSuggestReq(BaseModel):
    city: str
    per_person_budget: int
    needed_amenities: List[str] = []
    mode: Optional[str] = None


# ---------------- Endpoints ----------------
@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "server_default_mode": SERVER_DEFAULT_MODE,
        "last_effective_mode": LAST_EFFECTIVE_MODE,
        "firestore_enabled": FIRESTORE_ENABLED,
        "project": os.getenv("GCP_PROJECT"),
        "profiles_cached": len(_profiles_cache),
        "listings_cached": len(_listings_cache),
        "cache_age_sec": max(0, int(time.time() - _cache_at)) if _cache_at else None,
        "cache_ttl_sec": CACHE_TTL_SEC,
    }


@app.post("/profiles/parse")
def parse_profile(req: ParseReq, x_mode: Optional[str] = Header(None)):
    mode = _mode(req.mode, x_mode)
    from .agents.profile_reader import parse_profile_text
    prof, conf = parse_profile_text(req.text, mode=mode)
    return {"profile": prof, "confidence": conf, "mode_used": mode}


@app.post("/match/top")
def match_top(req: MatchTopReq, x_mode: Optional[str] = Header(None)):
    """
    Full pipeline: parse profile → retrieval → scoring → red flags → wingman → room hunter → maps planner
    Returns matches + enriched room suggestions.
    """
    mode = _mode(req.mode, x_mode)
    _load_cached()
    result = run_pipeline(
        input_profile=req.profile.dict(),
        candidates=_profiles_cache,
        listings=_listings_cache,
        mode=mode,
        top_k=req.k
    )
    return JSONResponse(result)


@app.post("/rooms/suggest")
def rooms_suggest(req: RoomSuggestReq, x_mode: Optional[str] = Header(None)):
    mode = _mode(req.mode, x_mode)
    _load_cached()
    from .agents.room_hunter import suggest_rooms
    out = suggest_rooms(req.city, req.per_person_budget, req.needed_amenities, _listings_cache, mode=mode, limit=5)
    return {"listings": out, "mode_used": mode}
