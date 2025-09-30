# scripts/seed_firestore.py
import os, sys, json
from google.cloud import firestore

PROJECT_ID = os.getenv("GCP_PROJECT")
db = firestore.Client(project=PROJECT_ID)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "data")

def load_json(filename: str):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def clear_collection(name: str):
    """Delete all documents in a collection (batch delete)."""
    docs = db.collection(name).stream()
    count = 0
    for d in docs:
        d.reference.delete()
        count += 1
    print(f"🗑️ Cleared {count} docs from {name}")

def seed_profiles():
    data = load_json("profiles_extended.json")
    for doc in data:
        db.collection("profiles").document(doc["id"]).set(doc)
    print(f"✅ Seeded {len(data)} profiles")

def seed_listings():
    data = load_json("listings_extended.json")
    for doc in data:
        db.collection("listings").document(doc["id"]).set(doc)
    print(f"✅ Seeded {len(data)} listings")

if __name__ == "__main__":
    reset = "--reset" in sys.argv

    if reset:
        clear_collection("profiles")
        clear_collection("listings")

    seed_profiles()
    seed_listings()
    print("🌱 Done seeding Firestore with extended dataset.")
