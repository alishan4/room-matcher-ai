from typing import List, Dict

def suggest_rooms(city:str, per_person_budget:int, needed_amenities:List[str], listings:List[Dict], mode:str='degraded', limit:int=5):
    city_low = (city or "").lower()
    must = set(a.lower() for a in needed_amenities or [])
    scored = []
    for L in listings:
        if (L.get("availability") or "").lower() != "available":
            continue
        if city_low and (L.get("city","").lower()!=city_low):
            continue
        rent = int(L.get("monthly_rent_PKR") or 0)
        if per_person_budget and rent > per_person_budget*2:  # assume 2 sharing for MVP
            continue
        am = set(a.lower() for a in (L.get("amenities") or []))
        j = len(must & am)
        price_diff = abs(rent - per_person_budget*2)
        score = j*10 - price_diff/1000.0
        scored.append((score, {
            "listing_id": L.get("listing_id"),
            "city": L.get("city"),
            "area": L.get("area"),
            "monthly_rent_PKR": rent,
            "amenities": L.get("amenities"),
            "why_match": f"{L.get('city')}, {L.get('area')} — {j} amenity matches; rent delta {price_diff}"
        }))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in scored[:limit]]
