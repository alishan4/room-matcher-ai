import json, os
from google.cloud import firestore

ROOT = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(ROOT, "app", "data")

def load_json(name):
    with open(os.path.join(DATA, name), "r", encoding="utf-8") as f:
        return json.load(f)

def upsert(col, items, id_field):
    db = firestore.Client()  # uses your gcloud auth/project
    batch = db.batch()
    for i, item in enumerate(items, 1):
        _id = item.get(id_field) or f"{col[:1].upper()}-{i:04d}"
        ref = db.collection(col).document(_id)
        batch.set(ref, {**item, id_field: _id})
        if i % 400 == 0:
            batch.commit()
            batch = db.batch()
    batch.commit()
    print(f"Upserted {len(items)} into {col}")

if __name__ == "__main__":
    profiles = load_json("synthetic_roommate_profiles_pakistan_400.json")
    listings = load_json("housing_listings_pakistan_400.json")
    upsert("profiles", profiles, "id")
    upsert("listings", listings, "listing_id")
