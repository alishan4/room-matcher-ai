from typing import Dict, List, Tuple
import numpy as np
from .model_registry import ModelRegistry

REG = ModelRegistry()

def features(profile: Dict, listing: Dict):
    pb = profile.get("budget_pkr") or 0
    rent = listing.get("monthly_rent_PKR") or listing.get("monthly_rent_pkr") or 0
    amen = set([x.lower() for x in listing.get("amenities") or []])
    # naive amen from profile (optional)
    pam = set([x.lower() for x in (profile.get("amenities") or [])])
    inter = len(amen & pam); uni = len(amen | pam) or 1
    j = inter/uni
    same_city = 1.0 if (profile.get("city") and listing.get("city") and profile["city"].lower()==listing["city"].lower()) else 0.0
    price_ratio = (rent / (pb*2)) if pb else 1.5
    return np.array([float(pb), float(rent), float(j), float(same_city), float(price_ratio)], dtype="float32")

def score_listing(profile: Dict, listing: Dict) -> float:
    mdl, meta = REG.listing_ranker()
    if mdl is None:
        # fallback rule
        rent = listing.get("monthly_rent_PKR") or 0
        pb = profile.get("budget_pkr") or 0
        price_pen = abs(rent - pb*2)
        return -(price_pen/1000.0)
    x = features(profile, listing).reshape(1,-1)
    try:
        if meta and meta.get("type")=="lightgbm":
            return float(mdl.predict(x))
        else:
            return float(mdl.predict(x)[0])
    except Exception:
        return 0.0
