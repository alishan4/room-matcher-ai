import argparse, json, csv, os, re
from collections import defaultdict

def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def norm(s):
    return (s or "").strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profiles", required=True)
    ap.add_argument("--out", default="training/out/profiles_labeled.csv")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    data = load_json(args.profiles)
    # Normalize keys we expect
    fields = [
        "id","name","city","area","budget_pkr","sleep_schedule","cleanliness",
        "noise_tolerance","study_habits","food_pref","smoking","guests_freq",
        "gender_pref","languages","raw_text"
    ]
    # Accept alternate key spellings
    def g(d, k):
        alts = [k, k.lower(), k.upper(), k.replace("pkr","PKR")]
        for a in alts:
            if a in d: return d[a]
        return None

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for r in data:
            row = []
            for k in fields:
                v = g(r, k)
                # Harmonize smoking to yes/no/None
                if k == "smoking":
                    if v in (True, "true", "yes", "Yes", "smoker"): v = "yes"
                    elif v in (False, "false", "no", "No", "non-smoker"): v = "no"
                    else: v = (v or None)
                row.append(v)
            w.writerow(row)
    print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()
