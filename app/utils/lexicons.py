CITIES = {
    "lahore":"lahore","lhr":"lahore","لاہور":"lahore",
    "karachi":"karachi","khi":"karachi","کراچی":"karachi",
    "islamabad":"islamabad","isb":"islamabad","اسلام آباد":"islamabad",
    "rawalpindi":"rawalpindi","pindi":"rawalpindi","راولپنڈی":"rawalpindi",
    "peshawar":"peshawar","quetta":"quetta","multan":"multan","faisalabad":"faisalabad"
}
def NORMALIZE_CITY(x):
    s = (x or "").strip().lower()
    return CITIES.get(s, s)

SLEEP = {
    "night owl":"night_owl","late":"night_owl","رات کو جاگتا":"night_owl","late night":"night_owl",
    "early bird":"early_bird","morning":"early_bird","صبح جلدی":"early_bird","early":"early_bird"
}
def NORMALIZE_SLEEP(x):
    s = (x or "").strip().lower()
    return SLEEP.get(s, s)

CLEAN = {"high":"high","neat":"high","صاف ستھرا":"high","medium":"medium","moderate":"medium","low":"low","chل":"low","chill":"low"}
def NORMALIZE_CLEAN(x):
    s = (x or "").strip().lower()
    return CLEAN.get(s, "medium")

NOISE = {"low":"low","quiet":"low","خاموش":"low","medium":"medium","high":"high","party":"high","شور":"high"}
def NORMALIZE_NOISE(x):
    s = (x or "").strip().lower()
    return NOISE.get(s, "medium")

GUESTS = {"never":"never","rare":"rare","اکثر نہیں":"rare","weekly":"weekly","اکثر":"weekly","often":"often","daily":"daily"}
def NORMALIZE_GUESTS(x):
    s = (x or "").strip().lower()
    return GUESTS.get(s, "rare")
