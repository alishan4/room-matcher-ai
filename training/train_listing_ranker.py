import argparse, os, json, numpy as np, joblib, math, random
from typing import Dict, List
from tqdm import tqdm

def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def jaccard(a: List[str], b: List[str]) -> float:
    sa, sb = set([x.lower() for x in a or []]), set([x.lower() for x in b or []])
    if not sa and not sb: return 0.0
    inter = len(sa & sb); union = len(sa | sb) or 1
    return inter / union

def feat(profile: Dict, listing: Dict) -> List[float]:
    pb = profile.get("budget_pkr") or 0
    rent = listing.get("monthly_rent_PKR") or listing.get("monthly_rent_pkr") or 0
    amen = jaccard(profile.get("amenities") or [], listing.get("amenities") or [])
    same_city = 1.0 if (profile.get("city") and listing.get("city") and profile["city"].lower()==listing["city"].lower()) else 0.0
    price_ratio = (rent / (pb*2)) if pb else 1.5
    return [float(pb), float(rent), float(amen), float(same_city), float(price_ratio)]

def pseudo_label(profile: Dict, listing: Dict) -> float:
    # Distill your rule: higher amenity overlap, closer price, same city wins
    a = jaccard(profile.get("amenities") or [], listing.get("amenities") or [])
    pb = profile.get("budget_pkr") or 0
    rent = listing.get("monthly_rent_PKR") or listing.get("monthly_rent_pkr") or 0
    price_pen = abs(rent - (pb*2)) / max(1, (pb*2))
    same = 1.0 if (profile.get("city") and listing.get("city") and profile["city"].lower()==listing["city"].lower()) else 0.0
    score = 0.6*a + 0.3*(1-price_pen) + 0.1*same
    return max(0.0, min(1.0, score))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profiles", required=True)
    ap.add_argument("--listings", required=True)
    ap.add_argument("--out_dir", required=True)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    profiles = load_json(args.profiles)
    listings = load_json(args.listings)

    X, y = [], []
    # Sample pairs
    random.seed(42)
    for p in profiles:
        # Create a "fake" desired amenity set from profile text (optional).
        p["amenities"] = p.get("amenities") or []
        cand = random.sample(listings, k=min(40, len(listings)))
        for L in cand:
            if (L.get("availability") or "").lower() not in ("available","yes","true","open",""):
                continue
            X.append(feat(p, L))
            y.append(pseudo_label(p, L))

    # Try LightGBM, else fallback
    try:
        import lightgbm as lgb
        dtrain = lgb.Dataset(np.array(X), label=np.array(y))
        params = {"objective":"regression","metric":"l2","learning_rate":0.05,"num_leaves":31}
        model = lgb.train(params, dtrain, num_boost_round=200)
        joblib.dump(model, os.path.join(args.out_dir, "ranker_lgbm.joblib"))
        meta = {"features": ["pb","rent","amen_jaccard","same_city","price_ratio"], "type":"lightgbm"}
    except Exception as e:
        from sklearn.ensemble import GradientBoostingRegressor
        model = GradientBoostingRegressor(random_state=42)
        model.fit(np.array(X), np.array(y))
        joblib.dump(model, os.path.join(args.out_dir, "ranker_gbm.joblib"))
        meta = {"features": ["pb","rent","amen_jaccard","same_city","price_ratio"], "type":"sklearn_gbrt"}

    with open(os.path.join(args.out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("[ok] saved ranker to", args.out_dir)

if __name__ == "__main__":
    main()
