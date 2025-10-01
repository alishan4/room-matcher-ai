# W = dict(city=10, budget=25, sleep=15, cleanliness=15, noise=10, study=10, smoking=8, guests=7)  # total 100

# def score_pair(a, b):
#     s = {"city":0,"budget":0,"sleep":0,"cleanliness":0,"noise":0,"study":0,"smoking":0,"guests":0}
#     reasons = []

#     if a.get("city") and b.get("city") and a["city"] == b["city"]:
#         s["city"] = W["city"]; reasons.append("Same city")

#     if a.get("budget_pkr") and b.get("budget_pkr"):
#         win = max(2000, int(0.2 * a["budget_pkr"]))
#         if abs(a["budget_pkr"] - b["budget_pkr"]) <= win:
#             s["budget"] = W["budget"]; reasons.append("Budgets align (±20%)")

#     if a.get("sleep_schedule") and b.get("sleep_schedule") and a["sleep_schedule"] == b["sleep_schedule"]:
#         s["sleep"] = W["sleep"]; reasons.append("Similar sleep schedule")

#     if a.get("cleanliness") and b.get("cleanliness") and a["cleanliness"] == b["cleanliness"]:
#         s["cleanliness"] = W["cleanliness"]; reasons.append("Same cleanliness preference")

#     if a.get("noise_tolerance") and b.get("noise_tolerance") and a["noise_tolerance"] == b["noise_tolerance"]:
#         s["noise"] = W["noise"]; reasons.append("Noise tolerance looks compatible")

#     if a.get("study_habits") and b.get("study_habits"):
#         if ("library" in a["study_habits"] and "library" in b["study_habits"]) or                ("home" in a["study_habits"] and "home" in b["study_habits"]):
#             s["study"] = W["study"]; reasons.append("Study habits match")

#     if a.get("smoking") == b.get("smoking"):
#         s["smoking"] = W["smoking"]; reasons.append("Smoking preference aligned")

#     if a.get("guests_freq") and b.get("guests_freq") and a["guests_freq"] == b["guests_freq"]:
#         s["guests"] = W["guests"]; reasons.append("Similar guest frequency")

#     total = sum(s.values())
#     return total, reasons, s


# app/agents/match_scorer.py
from typing import Dict, Tuple, List, Optional, Iterable
from math import radians, sin, cos, sqrt, atan2
from dataclasses import dataclass, field

from ..utils.num import as_int


@dataclass
class MatchScoreConfig:
    """Configuration for the rule-based match scorer."""

    weights: Dict[str, int] = field(
        default_factory=lambda: dict(
            city=10,
            budget=20,
            sleep=12,
            cleanliness=12,
            noise=8,
            study=8,
            smoking=8,
            guests=7,
            role=5,
            anchor=10,
        )
    )
    # Each tuple = (distance_km, multiplier applied to anchor weight)
    anchor_buckets: Tuple[Tuple[float, float], ...] = (
        (2.0, 1.0),
        (5.0, 0.8),
        (20.0, 0.5),
    )


_DEFAULT_MATCH_CONFIG = MatchScoreConfig()
_ACTIVE_MATCH_CONFIG = MatchScoreConfig()


def get_match_config() -> MatchScoreConfig:
    """Return a copy of the active configuration."""

    return MatchScoreConfig(
        weights=dict(_ACTIVE_MATCH_CONFIG.weights),
        anchor_buckets=tuple(_ACTIVE_MATCH_CONFIG.anchor_buckets),
    )


def set_match_config(config: MatchScoreConfig) -> None:
    """Override the active configuration."""

    global _ACTIVE_MATCH_CONFIG
    weights = dict(config.weights)
    anchor_buckets: Iterable[Tuple[float, float]] = config.anchor_buckets
    _ACTIVE_MATCH_CONFIG = MatchScoreConfig(
        weights=weights,
        anchor_buckets=tuple(anchor_buckets),
    )


def reset_match_config() -> None:
    """Restore the default configuration."""

    set_match_config(_DEFAULT_MATCH_CONFIG)

# ---------------- Helpers ----------------
def haversine_km(loc1: Dict, loc2: Dict) -> float:
    """Distance in km between two lat/lng dicts."""
    try:
        lat1, lon1 = float(loc1["lat"]), float(loc1["lng"])
        lat2, lon2 = float(loc2["lat"]), float(loc2["lng"])
    except Exception:
        return 9999  # invalid coords = far away

    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

# ---------------- Core Scorer ----------------
def score_pair(
    a: Dict,
    b: Dict,
    config: Optional[MatchScoreConfig] = None,
) -> Tuple[int, List[str], Dict[str, int]]:
    cfg = config or _ACTIVE_MATCH_CONFIG
    weights = cfg.weights

    s = {k: 0 for k in weights}
    reasons = []

    # --- City ---
    if a.get("city") and b.get("city") and a["city"] == b["city"]:
        s["city"] = weights.get("city", 0); reasons.append("Same city")

    # --- Budget ---
    ab, bb = as_int(a.get("budget_pkr")), as_int(b.get("budget_pkr"))
    if ab and bb:
        win = max(2000, int(0.2 * ab))
        if abs(ab - bb) <= win:
            s["budget"] = weights.get("budget", 0); reasons.append("Budgets align (±20%)")

    # --- Sleep ---
    if a.get("sleep_schedule") and b.get("sleep_schedule") and a["sleep_schedule"] == b["sleep_schedule"]:
        s["sleep"] = weights.get("sleep", 0); reasons.append("Similar sleep schedule")

    # --- Cleanliness ---
    if a.get("cleanliness") and b.get("cleanliness") and a["cleanliness"] == b["cleanliness"]:
        s["cleanliness"] = weights.get("cleanliness", 0); reasons.append("Same cleanliness preference")

    # --- Noise ---
    if a.get("noise_tolerance") and b.get("noise_tolerance") and a["noise_tolerance"] == b["noise_tolerance"]:
        s["noise"] = weights.get("noise", 0); reasons.append("Noise tolerance looks compatible")

    # --- Study habits ---
    if a.get("study_habits") and b.get("study_habits"):
        if ("library" in a["study_habits"] and "library" in b["study_habits"]) or \
           ("home" in a["study_habits"] and "home" in b["study_habits"]):
            s["study"] = weights.get("study", 0); reasons.append("Study habits match")

    # --- Smoking ---
    if a.get("smoking") and b.get("smoking") and a["smoking"] == b["smoking"]:
        s["smoking"] = weights.get("smoking", 0); reasons.append("Smoking preference aligned")

    # --- Guests ---
    if a.get("guests_freq") and b.get("guests_freq") and a["guests_freq"] == b["guests_freq"]:
        s["guests"] = weights.get("guests", 0); reasons.append("Similar guest frequency")

    # --- Role (student/professional) ---
    if a.get("role") and b.get("role") and a["role"] == b["role"]:
        s["role"] = weights.get("role", 0); reasons.append(f"Both are {a['role']}s")

    # --- Anchor location (distance-based) ---
    if a.get("anchor_location") and b.get("anchor_location"):
        d = haversine_km(a["anchor_location"], b["anchor_location"])
        anchor_weight = weights.get("anchor", 0)
        matched_bucket = None
        for threshold, multiplier in cfg.anchor_buckets:
            if d <= threshold:
                matched_bucket = (threshold, multiplier)
                break

        if matched_bucket:
            threshold, multiplier = matched_bucket
            s["anchor"] = int(round(anchor_weight * multiplier))
            if threshold <= 2:
                reasons.append("Same anchor location")
            elif threshold <= 5:
                reasons.append(f"Anchors very close (≤{threshold:g} km)")
            else:
                reasons.append(f"Anchors nearby (≤{threshold:g} km)")
        else:
            reasons.append("Anchors far apart")

    total = sum(s.values())
    return total, reasons, s
