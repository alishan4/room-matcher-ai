import argparse, os, joblib, pandas as pd, numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

TARGETS = ["sleep_schedule","cleanliness","noise_tolerance","guests_freq","smoking"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out_dir", required=True)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    df = pd.read_csv(args.csv)
    df["text"] = (df.get("raw_text").fillna("") + " " + df.get("city").fillna("") + " " + df.get("area").fillna("")).str.strip()

    reports = {}
    for tgt in TARGETS:
        y_raw = df[tgt].fillna("")
        has = y_raw != ""
        X = df.loc[has, "text"].astype(str).values
        y = y_raw[has].astype(str).values
        if len(set(y)) <= 1:
            print(f"[skip] {tgt}: only one class.")
            continue
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        # Char+word TF-IDF to catch Roman-Urdu variants
        vec = TfidfVectorizer(ngram_range=(3,5), analyzer="char", min_df=2)
        clf = LogisticRegression(max_iter=200, class_weight="balanced", n_jobs=None)
        pipe = Pipeline([("vec", vec), ("clf", clf)])
        pipe.fit(Xtr, ytr)
        yp = pipe.predict(Xte)
        rep = classification_report(yte, yp, output_dict=True, zero_division=0)
        reports[tgt] = rep
        joblib.dump(pipe, os.path.join(args.out_dir, f"{tgt}.joblib"))
        print(f"[ok] {tgt} -> {os.path.join(args.out_dir, f'{tgt}.joblib')}")

    with open(os.path.join(args.out_dir, "reports.json"), "w", encoding="utf-8") as f:
        import json; json.dump(reports, f, indent=2)
    print("[done] profile classifiers saved.")

if __name__ == "__main__":
    main()
