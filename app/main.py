import os
from fastapi import FastAPI, Body, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from .graph import run_pipeline
from .utils.store import DataStore

MODE = os.getenv("MODE", "degraded").lower()

app = FastAPI(title="Room Matcher AI", version="0.1.0")

store = DataStore()  # loads JSON datasets from app/data

class ParseReq(BaseModel):
    text: str
    mode: Optional[str] = None

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
    raw_text: Optional[str] = None

class MatchTopReq(BaseModel):
    profile: Profile
    k: int = 5
    mode: Optional[str] = None

class PairExplainReq(BaseModel):
    a_id: str
    b_id: str
    mode: Optional[str] = None

class RoomSuggestReq(BaseModel):
    city: str
    per_person_budget: int
    needed_amenities: List[str] = []
    mode: Optional[str] = None

@app.get("/healthz")
def health():
    return {"ok": True, "mode": MODE, "profiles": len(store.profiles), "listings": len(store.listings)}

@app.post("/profiles/parse")
def parse_profile(req: ParseReq):
    mode = (req.mode or MODE).lower()
    from .agents.profile_reader import parse_profile_text
    prof, conf = parse_profile_text(req.text, mode=mode)
    return {"profile": prof, "confidence": conf}

@app.post("/match/top")
def match_top(req: MatchTopReq):
    mode = (req.mode or MODE).lower()
    # Run the pipeline against datastore profiles
    result = run_pipeline(input_profile=req.profile.dict(), candidates=store.profiles, listings=store.listings, mode=mode, top_k=req.k)
    return JSONResponse(result)

@app.post("/pair/explain")
def pair_explain(req: PairExplainReq):
    a = next((p for p in store.profiles if p.get("id")==req.a_id), None)
    b = next((p for p in store.profiles if p.get("id")==req.b_id), None)
    if not a or not b:
        return JSONResponse({"error": "profile(s) not found"}, status_code=404)
    from .agents.match_scorer import score_pair
    from .agents.red_flag import red_flags
    from .agents.wingman import explain_and_tips
    score, reasons, subs = score_pair(a,b)
    flags = red_flags(a,b)
    tips = explain_and_tips(a,b,score,reasons,flags)
    return {"score": score, "reasons": reasons, "subscores": subs, "conflicts": flags, "tips": tips}

@app.post("/rooms/suggest")
def rooms_suggest(req: RoomSuggestReq):
    mode = (req.mode or MODE).lower()
    from .agents.room_hunter import suggest_rooms
    listings = suggest_rooms(req.city, req.per_person_budget, req.needed_amenities, store.listings, mode=mode, limit=5)
    return {"listings": listings}
