import os, json
from typing import List, Dict, Any
import numpy as np

class EmbeddingIndex:
    def __init__(self, ids: List[str], vectors: np.ndarray):
        self.ids = ids
        self.vectors = vectors
        try:
            import faiss
            self.faiss = faiss
            self.index = faiss.IndexFlatIP(vectors.shape[1])
            self.index.add(vectors.astype('float32'))
        except Exception as e:
            raise RuntimeError(f"FAISS unavailable: {e}")

    @staticmethod
    def _embed_texts(texts: List[str]):
        # sentence-transformers embedding
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        embs = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embs

    @classmethod
    def load_or_build(cls, profiles: List[Dict[str,Any]]):
        ids = [p.get("id") or f"anon-{i}" for i,p in enumerate(profiles)]
        texts = [" ".join([p.get("raw_text",""), p.get("city",""), str(p.get("budget_pkr") or "")]) for p in profiles]
        vecs = cls._embed_texts(texts)
        return cls(ids, vecs)

    def search(self, query: str, k:int=20)->List[str]:
        qv = self._embed_texts([query])
        D,I = self.index.search(qv.astype('float32'), k)
        idxs = I[0].tolist()
        return [self.ids[i] for i in idxs if i>=0]
