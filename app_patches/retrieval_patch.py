from typing import List, Dict, Tuple
import numpy as np, os
from .model_registry import ModelRegistry

REG = ModelRegistry()

def encode_profile_for_retrieval(p: Dict) -> str:
    bits = [
        p.get("city") or "", f"budget:{p.get('budget_pkr')}",
        p.get("sleep_schedule") or "", p.get("cleanliness") or "",
        p.get("noise_tolerance") or "", p.get("study_habits") or "",
        p.get("food_pref") or "", ("smoke:"+str(p.get("smoking"))) if p.get("smoking") is not None else "",
        p.get("guests_freq") or ""
    ]
    return " | ".join([b for b in bits if b])

def faiss_search(query_p: Dict, candidates: List[Dict], top_n=40) -> Tuple[List[Dict], Dict]:
    index, ids = REG.faiss_index()
    if index is None:
        # fallback to keyword selection (first N same-city)
        qcity = (query_p.get("city") or "").lower()
        out = [c for c in candidates if (c.get("city") or "").lower()==qcity]
        return out[:top_n], {"method":"keyword", "fallback":"no_faiss"}
    model = REG.embedding_model()
    qtxt = encode_profile_for_retrieval(query_p)
    q = model.encode([qtxt], normalize_embeddings=True)
    import faiss
    D, I = index.search(q.astype("float32"), top_n*2)
    picked = []
    for idx in I[0]:
        if idx < 0 or idx >= len(candidates): continue
        picked.append(candidates[idx])
    return picked[:top_n], {"method":"faiss"}
