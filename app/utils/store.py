import json, os
from typing import List, Dict, Any

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

class DataStore:
    def __init__(self):
        self.profiles: List[Dict[str,Any]] = self._load_json("synthetic_roommate_profiles_pakistan_400.json")
        self.listings: List[Dict[str,Any]] = self._load_json("housing_listings_pakistan_400.json")

    def _load_json(self, name:str)->List[Dict[str,Any]]:
        path = os.path.join(DATA_DIR, name)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Ensure IDs for profiles
        if name.startswith("synthetic_roommate"):
            for i,p in enumerate(data):
                if "id" not in p or not p["id"]:
                    p["id"] = f"U-{i:04d}"
        if name.startswith("housing_listings"):
            for i,p in enumerate(data):
                if "listing_id" not in p or not p["listing_id"]:
                    p["listing_id"] = f"H-{i:04d}"
        return data
