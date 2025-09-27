import os, json
import numpy as np

SNAPSHOT_PATH = os.getenv("FAISS_SNAPSHOT","/tmp/faiss_profiles.idx")
META_PATH = os.getenv("FAISS_META","/tmp/faiss_profiles_meta.json")
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

class FaissStore:
    def __init__(self, model_name: str = MODEL_NAME):
        try:
            from sentence_transformers import SentenceTransformer
            import faiss
            self.faiss = faiss
            self.model = SentenceTransformer(model_name)
            self.index, self.meta = self._load_or_build()
        except Exception:
            self.model = None
            self.index = None
            self.meta = None

    def ready(self):
        return self.index is not None and self.model is not None

    def _load_or_build(self):
        import os, json
        from app.services.firestore import fetch_all_profiles
        if os.path.exists(SNAPSHOT_PATH) and os.path.exists(META_PATH):
            index = self.faiss.read_index(SNAPSHOT_PATH)
            with open(META_PATH,"r",encoding="utf-8") as f: meta=json.load(f)
            return index, meta
        profiles = fetch_all_profiles()
        texts = [self._profile_text(p) for p in profiles]
        X = self.model.encode(texts, batch_size=64, show_progress_bar=False, normalize_embeddings=True)
        index = self.faiss.IndexFlatIP(X.shape[1])
        index.add(np.array(X, dtype="float32"))
        self.faiss.write_index(index, SNAPSHOT_PATH)
        with open(META_PATH,"w",encoding="utf-8") as f: json.dump({"ids":[p.get("id") for p in profiles]}, f)
        return index, {"ids":[p.get("id") for p in profiles]}

    def search_profile(self, q, k=50):
        if not self.ready(): return []
        qtext = self._profile_text(q)
        qv = self.model.encode([qtext], normalize_embeddings=True)
        D, I = self.index.search(np.array(qv, dtype="float32"), k)
        out=[]
        ids = self.meta["ids"]
        from app.services.firestore import fetch_by_id
        for i in I[0]:
            if i == -1: continue
            pid = ids[i]
            p = fetch_by_id(pid)
            if p: out.append(p)
        return out

    def _profile_text(self, p):
        return " ".join([
            str(p.get("city","")),
            f'budget {p.get("budget_pkr") or ""}',
            str(p.get("sleep_schedule","")),
            str(p.get("cleanliness","")),
            str(p.get("noise_tolerance","")),
            str(p.get("study_habits","")),
            str(p.get("food_pref","")),
            "smoker" if p.get("smoking") else "non-smoker",
            str(p.get("guests_freq",""))
        ])
