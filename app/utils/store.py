# app/utils/store.py
import os, json
from typing import List, Dict, Any

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def _load_json(name: str) -> List[Dict[str, Any]]:
    p = os.path.join(DATA_DIR, name)
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

class DataStore:
    """Loads the shipped datasets from app/data for degraded/offline use."""
    def __init__(self):
        self.profiles = _load_json("synthetic_roommate_profiles_pakistan_400.json")
        self.listings = _load_json("housing_listings_pakistan_400.json")
