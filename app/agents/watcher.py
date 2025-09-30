import time
from app.services.firestore import fetch_all_profiles, fetch_all_listings
from app.graph import run_pipeline

def auto_hunt(user_profile: dict, interval: int = 300):
    """
    Periodically re-run pipeline for a user and print/notify new matches.
    In production: hook into Gmail/Calendar APIs for notifications.
    """
    while True:
        print("⏳ Auto-Hunt running...")
        profiles = fetch_all_profiles()
        listings = fetch_all_listings()
        result = run_pipeline(user_profile, profiles, listings, mode="online", top_k=5)
        print("Top match:", result["matches"][0] if result["matches"] else "None")
        time.sleep(interval)
