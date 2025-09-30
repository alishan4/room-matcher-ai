from typing import Dict, List
from math import radians, sin, cos, sqrt, atan2

def haversine_km(loc1: Dict, loc2: Dict) -> float:
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

def enrich_with_commute(user_loc: Dict, rooms: List[Dict]) -> List[Dict]:
    """Add distance_km and eta_minutes to each room. 
    TODO: swap haversine with Google Routes API if available."""
    enriched = []
    for r in rooms:
        if user_loc and r.get("geo"):
            dist = haversine_km(user_loc, r["geo"])
            r["distance_km"] = round(dist, 1)
            # crude estimate: 30 km/h → minutes
            r["eta_minutes"] = int((dist / 30.0) * 60)
        enriched.append(r)
    return enriched
