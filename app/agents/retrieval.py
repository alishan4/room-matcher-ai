# # app/agents/retrieval.py
# from typing import List, Dict, Tuple
# import os
# from ..utils.keyword_filter import normalize_city

# TOP_N_ONLINE = 120
# TOP_N_DEGRADED = 120          # pull a lot, then scorer sorts
# BUDGET_TOL = 0.40             # ±40% in degraded
# CITY_BOOST = 1.0

# def _pct_diff(a, b):
#     if not a or not b:
#         return 1.0
#     return abs(a - b) / max(a, b)

# def budget_close(a, b, tol=BUDGET_TOL):
#     if not a or not b:
#         return True
#     return _pct_diff(a, b) <= tol

# class CandidateRetrieval:
#     def __init__(self, datastore):
#         self.ds = datastore

#     def _p_budget(self, p: Dict):
#         # Firestore may store "budget_PKR" (capital) — support both
#         return p.get("budget_pkr") or p.get("budget_PKR") or p.get("budget")

#     def retrieve(self, query: Dict, top_n: int = 50, mode: str = None) -> Tuple[List[Dict], Dict]:
#         """Returns (candidates, meta)."""
#         mode = (mode or os.getenv("MODE", "degraded")).lower()
#         profiles = list(self.ds.fetch_all_profiles())  # list of dicts
#         meta = {"method": "degraded_keyword"}

#         q_city = normalize_city(query.get("city") or "")
#         q_budget = query.get("budget_pkr")

#         if mode == "online" and hasattr(self.ds, "faiss") and self.ds.faiss is not None:
#             meta["method"] = "faiss"
#             try:
#                 ids = self.ds.faiss_search(query, k=TOP_N_ONLINE)
#                 cands = [p for p in profiles if p.get("id") in ids]
#                 return cands[:top_n], meta
#             except Exception as e:
#                 meta["fallback"] = f"faiss_error:{e}"

#         # ---- DEGRADED: two-pass broadened retrieval ----
#         pass1 = []
#         for p in profiles:
#             pc = normalize_city(p.get("city") or "")
#             pb = self._p_budget(p)
#             if q_city and pc == q_city and budget_close(q_budget, pb):
#                 pass1.append(p)

#         if not pass1:
#             pass2 = []
#             for p in profiles:
#                 pc = normalize_city(p.get("city") or "")
#                 pb = self._p_budget(p)
#                 if (q_city and pc == q_city) or budget_close(q_budget, pb):
#                     pass2.append(p)
#             if pass2:
#                 meta["fallback"] = "broadened_city_or_budget"
#                 pass1 = pass2

#         if not pass1:
#             meta["fallback"] = "pool_any"
#             pass1 = profiles[:TOP_N_DEGRADED]

#         def rank_key(p):
#             city_score = CITY_BOOST if (q_city and normalize_city(p.get("city") or "") == q_city) else 0.0
#             bud_pen = _pct_diff(q_budget, self._p_budget(p))
#             return (city_score, -bud_pen)

#         pass1.sort(key=rank_key, reverse=True)
#         return pass1[:min(top_n, TOP_N_DEGRADED)], meta

# app/agents/retrieval.py
from typing import List, Dict, Tuple, Optional
import os
from math import radians, sin, cos, sqrt, atan2
from dataclasses import dataclass

from ..utils.keyword_filter import normalize_city

TOP_N_ONLINE = 120
TOP_N_DEGRADED = 120          # pull a lot, then scorer sorts


@dataclass
class RetrievalConfig:
    budget_tol: float = 0.40             # ±40% in degraded
    city_boost: float = 1.0
    anchor_dist_km: float = 20.0         # max km for anchor closeness filter
    # For ranking bonus -> (distance_km, bonus)
    anchor_bonus_steps: Tuple[Tuple[float, float], ...] = (
        (5.0, 1.0),
        (20.0, 0.5),
    )


_DEFAULT_RETRIEVAL_CONFIG = RetrievalConfig()
_ACTIVE_RETRIEVAL_CONFIG = RetrievalConfig()


def get_retrieval_config() -> RetrievalConfig:
    return RetrievalConfig(
        budget_tol=_ACTIVE_RETRIEVAL_CONFIG.budget_tol,
        city_boost=_ACTIVE_RETRIEVAL_CONFIG.city_boost,
        anchor_dist_km=_ACTIVE_RETRIEVAL_CONFIG.anchor_dist_km,
        anchor_bonus_steps=tuple(_ACTIVE_RETRIEVAL_CONFIG.anchor_bonus_steps),
    )


def set_retrieval_config(config: RetrievalConfig) -> None:
    global _ACTIVE_RETRIEVAL_CONFIG
    _ACTIVE_RETRIEVAL_CONFIG = RetrievalConfig(
        budget_tol=config.budget_tol,
        city_boost=config.city_boost,
        anchor_dist_km=config.anchor_dist_km,
        anchor_bonus_steps=tuple(config.anchor_bonus_steps),
    )


def reset_retrieval_config() -> None:
    set_retrieval_config(_DEFAULT_RETRIEVAL_CONFIG)


def _pct_diff(a, b):
    if not a or not b:
        return 1.0
    return abs(a - b) / max(a, b)


def budget_close(a, b, tol):
    if not a or not b:
        return True
    return _pct_diff(a, b) <= tol

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

class CandidateRetrieval:
    def __init__(self, datastore, config: Optional[RetrievalConfig] = None):
        self.ds = datastore
        self.config = config or _ACTIVE_RETRIEVAL_CONFIG

    def _p_budget(self, p: Dict):
        return p.get("budget_pkr") or p.get("budget_PKR") or p.get("budget")

    def retrieve(self, query: Dict, top_n: int = 50, mode: str = None) -> Tuple[List[Dict], Dict]:
        """Returns (candidates, meta)."""
        mode = (mode or os.getenv("MODE", "degraded")).lower()
        profiles = list(self.ds.fetch_all_profiles())
        meta = {"method": "degraded_keyword"}

        q_city = normalize_city(query.get("city") or "")
        q_budget = query.get("budget_pkr")
        q_role = query.get("role")
        q_anchor = query.get("anchor_location")

        # ---------------- Online (FAISS) ----------------
        if mode == "online" and hasattr(self.ds, "faiss") and self.ds.faiss is not None:
            meta["method"] = "faiss"
            try:
                ids = self.ds.faiss_search(query, k=TOP_N_ONLINE)
                cands = [p for p in profiles if p.get("id") in ids]
                return cands[:top_n], meta
            except Exception as e:
                meta["fallback"] = f"faiss_error:{e}"

        # ---------------- Degraded mode ----------------
        pass1 = []
        for p in profiles:
            pc = normalize_city(p.get("city") or "")
            pb = self._p_budget(p)
            prole = p.get("role")
            panchor = p.get("anchor_location")

            # City + budget filter
            if q_city and pc == q_city and budget_close(q_budget, pb, tol=self.config.budget_tol):
                # Role check (prefer same role)
                if not q_role or (q_role and prole == q_role):
                    # Anchor proximity check
                    if q_anchor and panchor:
                        d = haversine_km(q_anchor, panchor)
                        if d <= self.config.anchor_dist_km:
                            pass1.append(p)
                        else:
                            continue
                    else:
                        pass1.append(p)

        # Broaden if nothing found
        if not pass1:
            pass2 = []
            for p in profiles:
                pc = normalize_city(p.get("city") or "")
                pb = self._p_budget(p)
                if (q_city and pc == q_city) or budget_close(q_budget, pb, tol=self.config.budget_tol):
                    pass2.append(p)
            if pass2:
                meta["fallback"] = "broadened_city_or_budget"
                pass1 = pass2

        # Last resort
        if not pass1:
            meta["fallback"] = "pool_any"
            pass1 = profiles[:TOP_N_DEGRADED]

        # ---------------- Ranking ----------------
        def rank_key(p):
            city_score = self.config.city_boost if (q_city and normalize_city(p.get("city") or "") == q_city) else 0.0
            bud_pen = _pct_diff(q_budget, self._p_budget(p))
            role_bonus = 0.5 if (q_role and p.get("role") == q_role) else 0.0
            anchor_bonus = 0.0
            if q_anchor and p.get("anchor_location"):
                d = haversine_km(q_anchor, p["anchor_location"])
                for threshold, bonus in self.config.anchor_bonus_steps:
                    if d <= threshold:
                        anchor_bonus = bonus
                        break
            return (city_score + role_bonus + anchor_bonus, -bud_pen)

        pass1.sort(key=rank_key, reverse=True)
        return pass1[:min(top_n, TOP_N_DEGRADED)], meta
