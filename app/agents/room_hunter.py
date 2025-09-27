from typing import List, Dict
from ..utils.num import as_int

def _city(s): 
    return (s or "").strip().lower()

def _is_available(L: Dict) -> bool:
    # accept availability/status variants; default to True if field missing
    val = (L.get("availability") or L.get("status") or "available")
    val = str(val).strip().lower()
    return val not in ("unavailable", "occupied", "closed", "false", "0", "no")

def _rent_val(L: Dict) -> int:
    # try common rent keys
    for k in ("monthly_rent_PKR", "rent_pkr", "rent", "price_pkr", "price"):
        if k in L and L[k] is not None:
            return as_int(L[k])
    return 0

def rank_rooms(q: Dict, listings: List[Dict], k: int = 3) -> List[Dict]:
    qcity = _city(q.get("city"))
    qbud  = as_int(q.get("budget_pkr")) or 0
    scored = []
    for L in listings or []:
        if not _is_available(L):
            continue
        if qcity and _city(L.get("city")) != qcity:
            continue

        rent = _rent_val(L)
        if qbud and rent > max(qbud * 2, qbud + 5000):
            # simple guard: assume 2-sharing or small headroom
            continue

        am = L.get("amenities") or []
        must = set()  # (extend later if you add UI filters)
        j = len(must & set(a.strip().lower() for a in am))

        price_diff = abs(rent - (qbud * 2 if qbud else rent))
        score = j * 10 - (price_diff / 1000.0)

        scored.append((
            score,
            {
                "listing_id": L.get("listing_id") or L.get("id") or "-",
                "city": L.get("city"),
                "area": L.get("area"),
                "monthly_rent_PKR": rent,
                "amenities": am,
                "why_match": f"{L.get('city')}, {L.get('area')} - {j} amenity overlap; rent delta {price_diff}"
            }
        ))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in scored[:k]]
