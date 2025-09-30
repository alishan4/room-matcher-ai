import os
from typing import List, Dict, Optional
from app.agents.profile_reader import normalize_profile

USE_FIRESTORE = os.getenv("FIRESTORE_ENABLED", "false").lower() == "true"
PROJECT_ID = os.getenv("GCP_PROJECT")

def _client():
    from google.cloud import firestore
    return firestore.Client(project=PROJECT_ID)

def _local_json(rel_path: str) -> List[Dict]:
    import json
    p = os.path.join(os.path.dirname(__file__), "..", "data", rel_path)
    with open(os.path.abspath(p), "r", encoding="utf-8") as f:
        return json.load(f)

# -------------------------------
# Profiles
# -------------------------------
def fetch_all_profiles() -> List[Dict]:
    if not USE_FIRESTORE:
        # degraded: local JSON, but still normalize
        raw = _local_json("profiles_extended.json")
        return [normalize_profile(d) for d in raw]

    db = _client()
    docs = db.collection("profiles").stream()
    raw = [d.to_dict() for d in docs]
    return [normalize_profile(d) for d in raw]

def fetch_by_id(pid: str) -> Optional[Dict]:
    if not USE_FIRESTORE:
        for p in fetch_all_profiles():
            if p.get("id") == pid:
                return p
        return None
    db = _client()
    doc = db.collection("profiles").document(pid).get()
    return normalize_profile(doc.to_dict()) if doc.exists else None

# -------------------------------
# Listings
# -------------------------------
def fetch_all_listings() -> List[Dict]:
    if not USE_FIRESTORE:
        return _local_json("listings_extended.json")

    db = _client()
    docs = db.collection("listings").stream()
    return [d.to_dict() for d in docs]

# -------------------------------
# Local wrapper for degraded mode
# -------------------------------
class LocalDB:
    """Compat wrapper some modules use; returns normalized profiles & listings."""
    def __init__(self):
        self._profiles = fetch_all_profiles()
        self._listings = fetch_all_listings()
    def all_profiles(self): return self._profiles
    def all_listings(self): return self._listings
