from typing import Dict, Tuple
from .model_registry import ModelRegistry

REG = ModelRegistry()

def ml_enrich(profile: Dict) -> Dict:
    text = (profile.get("raw_text") or "") + " " + (profile.get("city") or "") + " " + (profile.get("area") or "")
    for name in ["sleep_schedule","cleanliness","noise_tolerance","guests_freq","smoking"]:
        if not profile.get(name):
            v = REG.predict_profile_attr(name, text)
            if v: profile[name] = v
    return profile
