import argparse, os, json, random, math
from typing import List, Dict
from sentence_transformers import SentenceTransformer, InputExample, losses
from sentence_transformers import models as st_models
from torch.utils.data import DataLoader
from tqdm import tqdm

def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def text_of(p: Dict) -> str:
    # Compact representation for encoding
    bits = [
        p.get("city") or "", f"budget:{p.get('budget_pkr')}",
        p.get("sleep_schedule") or "", p.get("cleanliness") or "",
        p.get("noise_tolerance") or "", p.get("study_habits") or "",
        p.get("food_pref") or "", ("smoke:"+str(p.get("smoking"))) if p.get("smoking") is not None else "",
        p.get("guests_freq") or ""
    ]
    return " | ".join([b for b in bits if b])

def compat_score(a,b):
    # Simple rule to craft positives/negatives
    s = 0
    if a.get("city") and b.get("city") and a["city"].lower()==b["city"].lower(): s+=2
    if a.get("sleep_schedule") and a.get("sleep_schedule")==b.get("sleep_schedule"): s+=2
    if a.get("cleanliness")==b.get("cleanliness"): s+=1
    if a.get("noise_tolerance")==b.get("noise_tolerance"): s+=1
    if a.get("smoking")==b.get("smoking"): s+=1
    # budget closeness
    ba, bb = a.get("budget_pkr"), b.get("budget_pkr")
    if ba and bb:
        if abs(ba-bb)/max(ba,bb) <= 0.2: s+=2
    return s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profiles", required=True)
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--batch_size", type=int, default=32)
    ap.add_argument("--out_dir", required=True)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    data = load_json(args.profiles)

    # Build pairs
    pos, neg = [], []
    for i,a in enumerate(data):
        # find some positives
        cand = random.sample(data, k=min(20, len(data)))
        for b in cand:
            if a is b: continue
            v = compat_score(a,b)
            if v >= 5:
                pos.append(InputExample(texts=[text_of(a), text_of(b)]))
            elif v <= 1:
                neg.append(InputExample(texts=[text_of(a), text_of(b)]))
    random.shuffle(pos); random.shuffle(neg)
    # balance
    k = min(len(pos), len(neg))
    samples = pos[:k] + neg[:k]

    print(f"Training with {len(samples)} pairs (pos={len(pos[:k])}, neg={len(neg[:k])})")

    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    train_dataloader = DataLoader(samples, shuffle=True, batch_size=args.batch_size)
    train_loss = losses.MultipleNegativesRankingLoss(model)

    warmup = min(1000, int(0.1*len(train_dataloader)))
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=args.epochs,
        warmup_steps=warmup,
        output_path=args.out_dir
    )
    print(f"[ok] saved model to {args.out_dir}")

if __name__ == "__main__":
    main()
