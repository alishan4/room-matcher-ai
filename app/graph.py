import os
from typing import List, Dict, Any
from .agents.profile_reader import normalize_profile
from .utils.retrieval import retrieve_candidates
from .agents.match_scorer import score_pair
from .agents.red_flag import red_flags
from .agents.wingman import explain_and_tips
from .agents.room_hunter import suggest_rooms
from .utils.trace import Trace

MODE = os.getenv("MODE", "degraded").lower()

def run_pipeline(input_profile: Dict[str,Any], candidates: List[Dict[str,Any]], listings: List[Dict[str,Any]], mode:str=MODE, top_k:int=5) -> Dict[str,Any]:
    trace = Trace(mode=mode)
    # 1) Normalize/validate profile (if coming from UI form, it's already structured but we enforce defaults)
    a = normalize_profile(input_profile)
    trace.add_step("ProfileReader", {"input_fields": list(input_profile.keys())}, {"normalized": True})
    # 2) Candidate retrieval (FAISS if online; keyword/rule if degraded)
    cands = retrieve_candidates(a, candidates, top_n=40 if mode=="online" else 20, mode=mode, trace=trace)
    results = []
    # 3) Score + Red Flags
    for b in cands:
        score, reasons, subs = score_pair(a,b)
        flags = red_flags(a,b)
        results.append({
            "other_profile_id": b.get("id"),
            "other_name": b.get("name"),
            "score": score,
            "reasons": reasons,
            "conflicts": flags,
            "subscores": subs,
            "city": b.get("city"),
            "budget_pkr": b.get("budget_pkr")
        })
        trace.add_step("MatchScorer", {"pair": f"{a.get('id','A?')} vs {b.get('id','B?')}"}, {"score": score, "flags": [f['type'] for f in flags]})
    # sort
    results.sort(key=lambda x: x["score"], reverse=True)
    top = results[:top_k]
    # 4) Wingman explanations
    for r in top:
        b = next((p for p in candidates if p.get("id")==r["other_profile_id"]), None)
        r["tips"] = explain_and_tips(a,b,r["score"],r["reasons"],r["conflicts"])
    # 5) Optional room suggestions for the #1 match (demo sweetener)
    room_recs = []
    if top:
        best = top[0]
        city = best.get("city") or a.get("city")
        # per-person budget: min of the two budgets
        per_person_budget = min((a.get("budget_pkr") or 0), (best.get("budget_pkr") or 0))
        room_recs = suggest_rooms(city, per_person_budget, [], listings, mode=mode, limit=3)
        trace.add_step("RoomHunter", {"city": city, "budget": per_person_budget}, {"count": len(room_recs)})
    return {"mode": mode, "matches": top, "rooms": room_recs, "trace": trace.to_dict()}
