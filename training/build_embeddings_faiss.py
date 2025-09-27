import argparse, os, json, numpy as np
from typing import Dict, List
from tqdm import tqdm

def load_json(p):
    import json
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def text_of(p: Dict) -> str:
    bits = [
        p.get("city") or "", f"budget:{p.get('budget_pkr')}",
        p.get("sleep_schedule") or "", p.get("cleanliness") or "",
        p.get("noise_tolerance") or "", p.get("study_habits") or "",
        p.get("food_pref") or "", ("smoke:"+str(p.get("smoking"))) if p.get("smoking") is not None else "",
        p.get("guests_freq") or ""
    ]
    return " | ".join([b for b in bits if b])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profiles", required=True)
    ap.add_argument("--model_dir", default="")  # if empty use base model
    ap.add_argument("--out_dir", required=True)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    data = load_json(args.profiles)

    # load model
    from sentence_transformers import SentenceTransformer
    model_name = args.model_dir if args.model_dir else "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    model = SentenceTransformer(model_name)

    # encode
    texts = [text_of(p) for p in data]
    emb = model.encode(texts, convert_to_numpy=True, show_progress_bar=True, batch_size=64, normalize_embeddings=True)
    ids = [p.get("id") or f"R-{i:04d}" for i,p in enumerate(data,1)]

    # faiss index
    import faiss
    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine via normalized embeddings
    index.add(emb.astype("float32"))

    # save
    faiss_path = os.path.join(args.out_dir, "profiles.index")
    meta_path = os.path.join(args.out_dir, "meta.json")
    npy_path = os.path.join(args.out_dir, "profiles_emb.npy")

    faiss.write_index(index, faiss_path)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"ids": ids}, f)
    np.save(npy_path, emb)

    print(f"[ok] wrote {faiss_path}, {meta_path}, {npy_path}")

if __name__ == "__main__":
    main()
