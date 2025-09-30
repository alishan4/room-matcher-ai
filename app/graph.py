# # app/graph.py
# from typing import List, Dict, Any
# from .agents.profile_reader import normalize_profile
# from .agents.retrieval import CandidateRetrieval
# from .agents.match_scorer import score_pair
# from .agents.red_flag import red_flags
# from .agents.wingman import wingman
# from .agents.room_hunter import rank_rooms
# from .utils.num import as_int

# def run_pipeline(
#     input_profile: Dict[str, Any],
#     candidates: List[Dict[str, Any]],
#     listings: List[Dict[str, Any]],
#     mode: str = "degraded",
#     top_k: int = 5
# ) -> Dict[str, Any]:

#     class _MemDS:
#         def __init__(self, profiles: List[Dict[str, Any]]):
#             self._profiles = profiles
#             self.faiss = None
#         def fetch_all_profiles(self) -> List[Dict[str, Any]]:
#             return self._profiles

#     q = normalize_profile(input_profile)
#     ds = _MemDS(candidates)
#     retr = CandidateRetrieval(ds)
#     pool, meta = retr.retrieve(q, top_n=max(top_k * 10, 100), mode=mode)

#     items: List[Dict[str, Any]] = []
#     for c in pool:
#         total, reasons, subscores = score_pair(q, normalize_profile(c))
#         flags = red_flags(q, c)

#         # <- budget from either key:
#         cand_budget = as_int(c.get("budget_pkr") or c.get("budget_PKR") or c.get("budget"))

#         items.append({
#             "other_profile_id": c.get("id"),
#             "other_name": c.get("name"),
#             "score": total,
#             "reasons": reasons,
#             "conflicts": flags,
#             "subscores": subscores,
#             "city": c.get("city"),
#             "budget_pkr": cand_budget,
#             "tips": wingman(reasons, flags),
#         })

#     items.sort(key=lambda x: x["score"], reverse=True)
#     top = items[:top_k]

#     rooms = rank_rooms(q, listings, k=3)

#     # ---- safe flag extraction for trace (no more 500) ----
#     def _flag_label(f):
#         if isinstance(f, dict):
#             return f.get("type")
#         return str(f)

#     trace = {
#         "mode": mode,
#         "steps": [
#             {"agent": "ProfileReader", "inputs": {"fields": list(input_profile.keys())}, "outputs": {"normalized": True}},
#             {"agent": "CandidateRetrieval", "inputs": {"method": meta.get("method")}, "outputs": {"count": len(pool), **({"fallback": meta.get("fallback")} if meta.get("fallback") else {})}},
#         ]
#     }
#     for t in top:
#         trace["steps"].append({
#             "agent": "MatchScorer",
#             "inputs": {"pair": f'{q.get("id","A?")} vs {t["other_profile_id"]}'},
#             "outputs": {"score": t["score"], "flags": [_flag_label(f) for f in (t.get("conflicts") or [])]},
#         })
#     trace["steps"].append({"agent": "RoomHunter", "inputs": {"city": q.get("city"), "budget": q.get("budget_pkr")}, "outputs": {"count": len(rooms)}})

#     return {"mode": mode, "matches": top, "rooms": rooms, "trace": trace}

# app/graph.py
from typing import List, Dict, Any
from .agents.profile_reader import normalize_profile
from .agents.retrieval import CandidateRetrieval
from .agents.match_scorer import score_pair
from .agents.red_flag import red_flags
from .agents.wingman import wingman
from .agents.room_hunter import rank_rooms
from .agents.maps_planner import enrich_with_commute   # 👈 NEW
from .utils.num import as_int


def run_pipeline(
    input_profile: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    listings: List[Dict[str, Any]],
    mode: str = "degraded",
    top_k: int = 5
) -> Dict[str, Any]:

    class _MemDS:
        def __init__(self, profiles: List[Dict[str, Any]]):
            self._profiles = profiles
            self.faiss = None
        def fetch_all_profiles(self) -> List[Dict[str, Any]]:
            return self._profiles

    # ---- Step 1: Normalize profile ----
    q = normalize_profile(input_profile)

    # ---- Step 2: Candidate retrieval ----
    ds = _MemDS(candidates)
    retr = CandidateRetrieval(ds)
    pool, meta = retr.retrieve(q, top_n=max(top_k * 10, 100), mode=mode)

    # ---- Step 3–5: Match scoring, red flags, wingman ----
    items: List[Dict[str, Any]] = []
    for c in pool:
        total, reasons, subscores = score_pair(q, normalize_profile(c))
        flags = red_flags(q, c)
        cand_budget = as_int(c.get("budget_pkr") or c.get("budget_PKR") or c.get("budget"))

        items.append({
            "other_profile_id": c.get("id"),
            "other_name": c.get("name"),
            "score": total,
            "reasons": reasons,
            "conflicts": flags,
            "subscores": subscores,
            "city": c.get("city"),
            "budget_pkr": cand_budget,
            "tips": wingman(reasons, flags, profile=q, other=c),  # 👈 updated call
        })

    items.sort(key=lambda x: x["score"], reverse=True)
    top = items[:top_k]

    # ---- Step 6: Room Hunter ----
    rooms = rank_rooms(q, listings, k=3)

    # ---- Step 7: Maps Planner Agent (commute enrichment) ----
    user_loc = q.get("geo") or q.get("anchor_location")
    if user_loc:
        rooms = enrich_with_commute(user_loc, rooms)

    # ---- Trace (for explainability) ----
    def _flag_label(f):
        if isinstance(f, dict):
            return f.get("type")
        return str(f)

    trace = {
        "mode": mode,
        "steps": [
            {"agent": "ProfileReader", "inputs": {"fields": list(input_profile.keys())}, "outputs": {"normalized": True}},
            {"agent": "CandidateRetrieval", "inputs": {"method": meta.get("method")}, "outputs": {"count": len(pool), **({"fallback": meta.get("fallback")} if meta.get("fallback") else {})}},
        ]
    }
    for t in top:
        trace["steps"].append({
            "agent": "MatchScorer",
            "inputs": {"pair": f'{q.get("id","A?")} vs {t["other_profile_id"]}'},
            "outputs": {"score": t["score"], "flags": [_flag_label(f) for f in (t.get("conflicts") or [])]},
        })
    trace["steps"].append({
        "agent": "RoomHunter",
        "inputs": {"city": q.get("city"), "budget": q.get("budget_pkr")},
        "outputs": {"count": len(rooms)}
    })
    if user_loc:
        trace["steps"].append({
            "agent": "MapsPlanner",
            "inputs": {"user_loc": user_loc},
            "outputs": {"rooms_enriched": len(rooms)}
        })

    return {"mode": mode, "matches": top, "rooms": rooms, "trace": trace}
