import os, json, joblib, numpy as np

class ModelRegistry:
    def __init__(self):
        self.profile_cls_dir = os.getenv("PROFILE_CLS_DIR", "models/profile_cls")
        self.emb_model_path = os.getenv("EMB_MODEL_PATH", "")
        self.faiss_index_path = os.getenv("FAISS_INDEX_PATH", "models/faiss/profiles.index")
        self.faiss_meta_path = os.getenv("FAISS_META_PATH", "models/faiss/meta.json")
        self.listing_ranker_dir = os.getenv("LISTING_RANKER_DIR", "models/listing_ranker")

        self._cls = {}
        self._faiss = None
        self._ids = None
        self._emb_model = None
        self._ranker = None
        self._ranker_meta = None

    # --- Profile classifiers ---
    def load_profile_cls(self, name):
        path = os.path.join(self.profile_cls_dir, f"{name}.joblib")
        if os.path.exists(path):
            self._cls[name] = joblib.load(path)
            return self._cls[name]
        return None

    def predict_profile_attr(self, name, text):
        mdl = self._cls.get(name) or self.load_profile_cls(name)
        if not mdl: return None
        try:
            return mdl.predict([text or ""])[0]
        except Exception:
            return None

    # --- Embedding model ---
    def embedding_model(self):
        if self._emb_model is not None:
            return self._emb_model
        from sentence_transformers import SentenceTransformer
        name = self.emb_model_path if self.emb_model_path else "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self._emb_model = SentenceTransformer(name)
        return self._emb_model

    # --- FAISS ---
    def faiss_index(self):
        if self._faiss is not None:
            return self._faiss, self._ids
        import faiss
        if os.path.exists(self.faiss_index_path) and os.path.exists(self.faiss_meta_path):
            index = faiss.read_index(self.faiss_index_path)
            with open(self.faiss_meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            self._faiss = index
            self._ids = meta.get("ids")
            return self._faiss, self._ids
        return None, None

    # --- Listing ranker ---
    def listing_ranker(self):
        if self._ranker is not None:
            return self._ranker, self._ranker_meta
        meta_path = os.path.join(self.listing_ranker_dir, "meta.json")
        gbr = os.path.join(self.listing_ranker_dir, "ranker_gbm.joblib")
        lgbm = os.path.join(self.listing_ranker_dir, "ranker_lgbm.joblib")
        if os.path.exists(lgbm):
            self._ranker = joblib.load(lgbm)
            self._ranker_meta = {"type":"lightgbm"}
        elif os.path.exists(gbr):
            self._ranker = joblib.load(gbr)
            self._ranker_meta = {"type":"sklearn_gbrt"}
        return self._ranker, self._ranker_meta
