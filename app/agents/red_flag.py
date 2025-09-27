from typing import Dict, List
from ..utils.lexicons import LEX

def red_flags(a:Dict,b:Dict)->List[Dict]:
    flags: List[Dict] = []

    # Gender preference block (if present)
    gp_a, gp_b = a.get("gender_pref"), b.get("gender_pref")
    if gp_a and gp_b and gp_a!="any" and gp_b!="any":
        if gp_a=="same" and gp_b=="same":
            # unknown genders in data -> skip; demo-friendly: no hard stop here
            pass

    # Sleep vs party/music
    if a.get("sleep_schedule")=="early_bird" and (b.get("guests_freq")=="often" or b.get("noise_tolerance")=="high"):
        flags.append({"type":"sleep_vs_guests","severity":"high","detail":"Early sleeper vs frequent guests/noisy"})
    if b.get("sleep_schedule")=="early_bird" and (a.get("guests_freq")=="often" or a.get("noise_tolerance")=="high"):
        flags.append({"type":"sleep_vs_guests","severity":"high","detail":"Early sleeper vs frequent guests/noisy"})

    # Cleanliness high vs low
    if a.get("cleanliness")=="high" and b.get("cleanliness")=="low":
        flags.append({"type":"cleanliness_mismatch","severity":"medium","detail":"High vs low cleanliness"})
    if b.get("cleanliness")=="high" and a.get("cleanliness")=="low":
        flags.append({"type":"cleanliness_mismatch","severity":"medium","detail":"High vs low cleanliness"})

    # Smoking clash
    if a.get("smoking")=="no" and b.get("smoking")=="yes" or a.get("smoking")=="yes" and b.get("smoking")=="no":
        flags.append({"type":"smoking_clash","severity":"high","detail":"Non-smoker with smoker"})

    return flags
