import os
from typing import List, Dict, Any, Optional
from .faiss_index import EmbeddingIndex
from .trace import Trace

MODE = os.getenv("MODE","degraded").lower()

def retrieve_candidates(a:Dict[str,Any], candidates:List[Dict[str,Any]], top_n:int=20, mode:str=MODE, trace:Optional[Trace]=None):
    # Online: try embeddings index on raw_text + key fields
    if mode=="online":
        try:
            idx = EmbeddingIndex.load_or_build(candidates)
            q = " ".join([a.get("raw_text",""), a.get("city",""), str(a.get("budget_pkr") or "")])
            ids = idx.search(q, top_n)
            # map ids to profiles
            idset = set(ids)
            result = [c for c in candidates if c.get("id") in idset]
            if trace: trace.add_step("CandidateRetrieval", {"method":"faiss","top_n":top_n}, {"count": len(result)})
            return result
        except Exception as e:
            if trace: trace.add_step("CandidateRetrieval", {"method":"faiss","error":str(e)}, {"fallback":"keywords"})
    # Degraded or fallback: keyword/rule filter
    city = (a.get("city") or "").lower()
    budget = a.get("budget_pkr")
    out = []
    for c in candidates:
        if city and (c.get("city","").lower()!=city): continue
        b2 = c.get("budget_pkr")
        if budget and b2:
            gap = abs(budget-b2)/max(budget,b2)
            if gap>0.25: continue
        out.append(c)
    if trace: trace.add_step("CandidateRetrieval", {"method":"keyword","top_n":top_n}, {"count": len(out)})
    return out[:top_n]
