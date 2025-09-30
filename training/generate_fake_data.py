import json, random, datetime
from faker import Faker

fake = Faker("en_US")

# Anchor locations (universities + workplaces with lat/lng)
ANCHORS = [
    ("FAST University, Lahore", 31.4811, 74.3035),
    ("LUMS, Lahore", 31.4712, 74.4082),
    ("Punjab University, Lahore", 31.492, 74.3077),
    ("NUST, Islamabad", 33.6426, 72.9906),
    ("IBA, Karachi", 24.9323, 67.1123),
    ("Karachi University", 24.9400, 67.1200),
    ("Blue Area Office, Islamabad", 33.716, 73.065),
    ("Gulberg Business Hub, Lahore", 31.520, 74.356),
    ("Clifton Offices, Karachi", 24.813, 67.030),
    ("Industrial Zone, Faisalabad", 31.418, 73.079),
]

# Cities + areas (rough sample)
CITIES = {
    "Lahore": ["Johar Town", "Model Town", "Gulberg"],
    "Karachi": ["Gulshan", "Clifton", "Nazimabad"],
    "Islamabad": ["Blue Area", "F-10", "G-11"],
    "Rawalpindi": ["Saddar", "Satellite Town"],
    "Faisalabad": ["Peoples Colony", "D Ground"],
}

AMENITIES = [
    "WiFi", "Furnished", "Separate washroom", "AC",
    "Parking", "Mess facility", "Kitchen", "Gym"
]

def random_geo(base_lat, base_lng, jitter=0.01):
    """Slightly jitter coordinates so users/rooms aren’t identical."""
    return {
        "lat": round(base_lat + random.uniform(-jitter, jitter), 6),
        "lng": round(base_lng + random.uniform(-jitter, jitter), 6),
        "source": "gps"
    }

def generate_profiles(n=30):
    profiles = []
    for i in range(1, n+1):
        role = random.choice(["student", "professional"])
        city = random.choice(list(CITIES.keys()))
        area = random.choice(CITIES[city])
        budget = random.choice([15000, 18000, 20000, 22000, 25000, 30000])
        sleep = random.choice(["early_bird","night_owl","flex"])
        clean = random.choice(["low","medium","high"])
        noise = random.choice(["low","medium","high"])
        guests = random.choice(["rare","sometimes","often","daily"])
        smoking = random.choice(["yes","no"])
        anchor = random.choice(ANCHORS)

        profiles.append({
            "id": f"R-{i:04d}",
            "name": fake.first_name(),
            "role": role,
            "city": city,
            "area": area,
            "budget_pkr": budget,
            "sleep_schedule": sleep,
            "cleanliness": clean,
            "noise_tolerance": noise,
            "study_habits": random.choice(["library","home","online_classes"]),
            "food_pref": random.choice(["veg","non-veg","mixed"]),
            "smoking": smoking,
            "guests_freq": guests,
            "languages": random.sample(["Urdu","English","Punjabi","Pashto"], k=2),
            "gender_pref": random.choice(["any","male","female"]),
            "anchor_location": {
                "label": anchor[0],
                "lat": anchor[1],
                "lng": anchor[2]
            },
            "geo": random_geo(anchor[1], anchor[2]),
            "raw_text": fake.sentence(nb_words=10),
            "contact": {
                "phone": f"+92{random.randint(3000000000, 3999999999)}",
                "whatsapp": True,
                "email": fake.email()
            },
            "created_at": datetime.datetime.utcnow().isoformat()
        })
    return profiles

def generate_listings(n=10):
    listings = []
    for i in range(1, n+1):
        city = random.choice(list(CITIES.keys()))
        area = random.choice(CITIES[city])
        rent = random.choice([15000, 18000, 20000, 25000, 30000])
        amenities = random.sample(AMENITIES, k=random.randint(3,5))
        anchor = random.choice(ANCHORS)

        listings.append({
            "id": f"H-{i:04d}",
            "city": city,
            "area": area,
            "monthly_rent_PKR": rent,
            "amenities": amenities,
            "status": "available",
            "rooms_available": random.randint(1,3),
            "reserved_by": [],
            "geo": random_geo(anchor[1], anchor[2]),
            "owner_contact": {
                "phone": f"+92{random.randint(3000000000, 3999999999)}",
                "whatsapp": True,
                "email": fake.email()
            },
            "why_match": fake.sentence(nb_words=8),
            "created_at": datetime.datetime.utcnow().isoformat()
        })
    return listings

if __name__ == "__main__":
    profiles = generate_profiles(30)
    listings = generate_listings(10)

    with open("app/data/profiles_extended.json","w",encoding="utf-8") as f:
        json.dump(profiles,f,indent=2,ensure_ascii=False)

    with open("app/data/listings_extended.json","w",encoding="utf-8") as f:
        json.dump(listings,f,indent=2,ensure_ascii=False)

    print("✅ Generated 30 profiles and 10 listings in data/")
