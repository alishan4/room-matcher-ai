# from typing import List, Dict
# from ..utils.num import as_int

# def _city(s): 
#     return (s or "").strip().lower()

# def _is_available(L: Dict) -> bool:
#     # accept availability/status variants; default to True if field missing
#     val = (L.get("availability") or L.get("status") or "available")
#     val = str(val).strip().lower()
#     return val not in ("unavailable", "occupied", "closed", "false", "0", "no")

# def _rent_val(L: Dict) -> int:
#     # try common rent keys
#     for k in ("monthly_rent_PKR", "rent_pkr", "rent", "price_pkr", "price"):
#         if k in L and L[k] is not None:
#             return as_int(L[k])
#     return 0

# def rank_rooms(q: Dict, listings: List[Dict], k: int = 3) -> List[Dict]:
#     qcity = _city(q.get("city"))
#     qbud  = as_int(q.get("budget_pkr")) or 0
#     scored = []
#     for L in listings or []:
#         if not _is_available(L):
#             continue
#         if qcity and _city(L.get("city")) != qcity:
#             continue

#         rent = _rent_val(L)
#         if qbud and rent > max(qbud * 2, qbud + 5000):
#             # simple guard: assume 2-sharing or small headroom
#             continue

#         am = L.get("amenities") or []
#         must = set()  # (extend later if you add UI filters)
#         j = len(must & set(a.strip().lower() for a in am))

#         price_diff = abs(rent - (qbud * 2 if qbud else rent))
#         score = j * 10 - (price_diff / 1000.0)

#         scored.append((
#             score,
#             {
#                 "listing_id": L.get("listing_id") or L.get("id") or "-",
#                 "city": L.get("city"),
#                 "area": L.get("area"),
#                 "monthly_rent_PKR": rent,
#                 "amenities": am,
#                 "why_match": f"{L.get('city')}, {L.get('area')} - {j} amenity overlap; rent delta {price_diff}"
#             }
#         ))
#     scored.sort(key=lambda x: x[0], reverse=True)
#     return [x[1] for x in scored[:k]]


# app/agents/room_hunter.py
from typing import List, Dict, Any, Optional
from math import radians, sin, cos, sqrt, atan2
from ..utils.num import as_int

def _city(s: str) -> str:
    return (s or "").strip().lower()

def _is_available(L: Dict) -> bool:
    """Check listing status + rooms availability."""
    status = (L.get("availability") or L.get("status") or "available").strip().lower()
    if status in ("unavailable", "occupied", "closed", "false", "0", "no"):
        return False
    if L.get("rooms_available") is not None and as_int(L.get("rooms_available")) <= 0:
        return False
    return True

def _rent_val(L: Dict) -> int:
    for k in ("monthly_rent_PKR", "rent_pkr", "rent", "price_pkr", "price"):
        if k in L and L[k] is not None:
            return as_int(L[k])
    return 0

def _haversine_km(loc1: Dict, loc2: Dict) -> float:
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

def rank_rooms(q: Dict, listings: List[Dict[str, Any]], k: int = 3) -> List[Dict]:
    qcity = _city(q.get("city"))
    qbud  = as_int(q.get("budget_pkr")) or 0
    qgeo  = q.get("geo") or q.get("anchor_location")

    scored = []
    for L in listings or []:
        if not _is_available(L):
            continue
        if qcity and not qgeo:
            if _city(L.get("city")) != qcity:
                continue

        rent = _rent_val(L)
        if qbud and rent > max(qbud * 2, qbud + 5000):
            continue

        am = L.get("amenities") or []
        must = set()  # (future UI filters)
        j = len(must & set(a.strip().lower() for a in am))

        price_diff = abs(rent - (qbud * 2 if qbud else rent))
        score = j * 10 - (price_diff / 1000.0)

        # ---------------- Distance scoring ----------------
        dist_km, eta_minutes = None, None
        if qgeo and L.get("geo"):
            dist_km = _haversine_km(qgeo, L["geo"])
            score -= dist_km / 2.0  # penalize far rooms
            # placeholder: eta_minutes will be filled by Maps Planner Agent
            eta_minutes = None

        out = {
            "listing_id": L.get("listing_id") or L.get("id") or "-",
            "city": L.get("city"),
            "area": L.get("area"),
            "monthly_rent_PKR": rent,
            "amenities": am,
            "why_match": f"{L.get('city')}, {L.get('area')} - {j} amenity overlap; rent delta {price_diff}",
            "rooms_available": L.get("rooms_available", 1),
            "reserved_by": L.get("reserved_by", []),
            "geo": L.get("geo"),
        }

        if dist_km is not None:
            out["distance_km"] = round(dist_km, 1)
            out["eta_minutes"] = eta_minutes  # placeholder for Maps Planner

        scored.append((score, out))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in scored[:k]]


def suggest_rooms(
    city: Optional[str],
    per_person_budget: Optional[int],
    needed_amenities: Optional[List[str]],
    listings: Optional[List[Dict[str, Any]]],
    *,
    mode: str = "degraded",
    limit: int = 5,
    anchor_location: Optional[Dict[str, Any]] = None,
    user_geo: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Lightweight helper for the `/rooms/suggest` endpoint.

    The implementation deliberately reuses :func:`rank_rooms` so that the
    availability, budget, and geo guards stay in sync with the matchmaking
    pipeline.  Additional request-level filters (e.g. amenities) are handled
    prior to ranking, after which we optionally enrich the results with
    commute estimates when a user anchor is available.
    """

    effective_mode = (mode or "degraded").lower()
    if effective_mode not in ("online", "degraded"):
        effective_mode = "degraded"

    top_k = max(1, int(limit) if limit else 1)

    q: Dict[str, Any] = {
        "city": city,
        "budget_pkr": as_int(per_person_budget) if per_person_budget is not None else None,
    }
    q["mode"] = effective_mode

    if anchor_location:
        q["anchor_location"] = anchor_location
    if user_geo:
        q["geo"] = user_geo

    required = {
        str(a).strip().lower()
        for a in (needed_amenities or [])
        if a is not None and str(a).strip()
    }

    pool: List[Dict[str, Any]] = []
    for listing in listings or []:
        if required:
            amenities = {
                str(a).strip().lower()
                for a in (listing.get("amenities") or [])
                if a is not None and str(a).strip()
            }
            if not required.issubset(amenities):
                continue
        pool.append(listing)

    ranked = rank_rooms(q, pool, k=top_k)

    user_loc = q.get("geo") or q.get("anchor_location")
    if user_loc and effective_mode == "online":
        try:
            from .maps_planner import enrich_with_commute

            ranked = enrich_with_commute(user_loc, ranked)
        except Exception:
            # Never fail the suggestion endpoint if enrichment is unavailable.
            # The base ranking already returns useful matches; commute data is
            # a best-effort add-on that depends on optional geo libraries.
            pass

    return ranked
