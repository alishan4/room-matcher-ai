# # import os
# # import requests
# # import streamlit as st

# # API_URL = os.getenv("ROOM_MATCHER_API", "http://127.0.0.1:8080")

# # st.set_page_config(page_title="Room Matcher AI", layout="wide")
# # st.title("🏠 Room Matcher AI — Streamlit Frontend")

# # # Sidebar health check
# # st.sidebar.header("Backend Health")
# # try:
# #     r = requests.get(f"{API_URL}/healthz")
# #     if r.status_code == 200:
# #         health = r.json()
# #         st.sidebar.success(f"Mode: {health.get('mode')} | Firestore: {health.get('firestore_enabled')}")
# #     else:
# #         st.sidebar.error("Backend not reachable")
# # except Exception as e:
# #     st.sidebar.error(f"Error: {e}")

# # st.sidebar.markdown("---")
# # st.sidebar.write(f"API URL: {API_URL}")

# # # Form for profile input
# # st.header("Your Profile")
# # with st.form("profile_form"):
# #     city = st.text_input("City", "Lahore")
# #     budget = st.number_input("Budget (PKR)", 5000, 200000, 18000, step=1000)
# #     sleep = st.selectbox("Sleep Schedule", ["", "night_owl", "early_bird"])
# #     cleanliness = st.selectbox("Cleanliness", ["", "high", "low"])
# #     noise = st.selectbox("Noise Tolerance", ["", "low", "high"])
# #     smoking = st.selectbox("Smoking", ["", "yes", "no"])
# #     guests = st.selectbox("Guests Frequency", ["", "rare", "sometimes", "often"])
# #     raw_text = st.text_area("Optional Free-Text Description (Urdu/English)")
# #     k = st.slider("Top Matches (k)", 1, 10, 5)
# #     submitted = st.form_submit_button("Find Matches")

# # if submitted:
# #     profile = {
# #         "city": city,
# #         "budget_pkr": budget,
# #         "sleep_schedule": sleep,
# #         "cleanliness": cleanliness,
# #         "noise_tolerance": noise,
# #         "smoking": smoking,
# #         "guests_freq": guests,
# #         "raw_text": raw_text
# #     }

# #     # If raw text given, call parse endpoint
# #     if raw_text.strip():
# #         st.subheader("🔍 Parsed Profile")
# #         try:
# #             pr = requests.post(f"{API_URL}/profiles/parse", json={"text": raw_text})
# #             parsed = pr.json()
# #             st.json(parsed)
# #             profile.update(parsed.get("profile", {}))
# #         except Exception as e:
# #             st.error(f"Profile parsing failed: {e}")

# #     # Call match API
# #     st.subheader("🤝 Top Matches")
# #     try:
# #         res = requests.post(f"{API_URL}/match/top", json={"profile": profile, "k": k})
# #         if res.status_code == 200:
# #             data = res.json()
# #             for m in data.get("matches", []):
# #                 with st.container():
# #                     st.markdown(f"**{m['other_profile_id']}** — Score: {m['score']}")
# #                     st.write("Reasons:", m["reasons"])
# #                     st.write("Conflicts:", m["conflicts"])
# #                     st.json(m["subscores"])
# #                     st.info("💡 Tips: " + "; ".join(m.get("tips", [])))

# #             st.subheader("🏘️ Room Suggestions")
# #             for r in data.get("rooms", []):
# #                 st.write(f"- {r['listing_id']} — {r['city']} {r['area']}, Rent PKR {r['monthly_rent_PKR']}")
# #                 st.caption(r["why_match"])

# #             st.subheader("🧭 Agent Trace")
# #             st.json(data.get("trace"))
# #         else:
# #             st.error(res.text)
# #     except Exception as e:
# #         st.error(f"Match request failed: {e}")
# import os, requests, json, time
# import streamlit as st

# st.set_page_config(page_title="Room Matcher AI", page_icon="🏠", layout="wide")
# API_URL = os.getenv("ROOM_MATCHER_API", "http://127.0.0.1:8080")

# # ---- Styles ----
# st.markdown(
#     """<style>
#       .result-row { display:flex; gap:10px; align-items:center; padding:10px 12px; border:1px solid #eee; border-radius:12px; margin:8px 0; background:#fff; }
#       .card { border:1px solid #eee; border-radius:12px; padding:12px; margin:6px 0; background:#fff;}
#       .badge { padding:2px 8px; border-radius:999px; background:#eef2ff; color:#3730a3; font-size:12px; }
#       .score { font-weight:700; padding:2px 8px; border-radius:8px; background:#ecfdf5; color:#065f46; }
#       .conflict { padding:2px 8px; border-radius:8px; background:#fff1f2; color:#9f1239; margin-left:6px; }
#       .tip { font-size:13px; color:#065f46; background:#ecfdf5; padding:4px 8px; border-radius:8px; display:inline-block; margin:4px 6px 0 0; }
#       .muted { color:#666; } .pill { font-size:12px; border:1px solid #e5e7eb; padding:2px 8px; border-radius:999px; background:#f9fafb; margin-right:6px; }
#       .mono { font-family: ui-monospace, Menlo, Consolas, monospace; }
#     </style>""", unsafe_allow_html=True
# )

# # ---- Header ----
# left, right = st.columns([0.7,0.3])
# with left:
#     st.title("Room Matcher AI")
#     st.caption("Smarter roommate matching — explainable, fast, and bandwidth-aware.")
# with right:
#     st.text_input("API URL", API_URL, key="api_url")
#     if st.button("Check Health", use_container_width=True):
#         try:
#             h = requests.get(f"{st.session_state.api_url}/healthz", timeout=10).json()
#             st.success(f"OK • Mode: {h.get('mode')}")
#             st.session_state.health = h
#         except Exception as e:
#             st.error(e)

# st.markdown("---")

# # ---- Form ----
# f1,f2,f3,f4 = st.columns([1.5,1.2,1.2,1.2])
# with f1:
#     city = st.text_input("City", "Lahore")
#     k = st.slider("Top K", 1, 20, 7)
# with f2:
#     budget = st.number_input("Budget (PKR)", 0, 300000, 18000, step=500)
#     sleep = st.selectbox("Sleep", ["", "night_owl", "early_bird", "flexible"], index=1)
# with f3:
#     cleanliness = st.selectbox("Cleanliness", ["", "high", "medium", "low"], index=1)
#     noise = st.selectbox("Noise Tolerance", ["", "low", "medium", "high"], index=1)
# with f4:
#     guests = st.selectbox("Guests", ["", "never", "rare", "weekly", "often", "daily"], index=2)
#     smoking = st.selectbox("Smoking", ["", "yes", "no"], index=2)

# st.text_area("Optional mixed Urdu/English ad (auto-parse)", key="raw_text", height=90)

# c1, c2, c3, c4 = st.columns([1,1,1,1])
# with c1:
#     mode_pref = st.selectbox("Preference", ["Auto","Accuracy+","Latency+"], index=0)
# with c2:
#     show_rooms = st.toggle("Suggest rooms", value=True)
# with c3:
#     dedupe_city = st.toggle("Only same city", value=True)
# with c4:
#     show_conflicts = st.toggle("Show conflicts", value=False)

# if st.button("Find Matches 🚀", type="primary", use_container_width=True):
#     prof = {
#         "city": city or None, "budget_pkr": int(budget) if budget else None,
#         "sleep_schedule": sleep or None, "cleanliness": cleanliness or None,
#         "noise_tolerance": noise or None, "guests_freq": guests or None,
#         "smoking": {"yes":"yes","no":"no"}.get(smoking, None),
#         "raw_text": st.session_state.raw_text or None
#     }
#     if (st.session_state.raw_text or "").strip():
#         try:
#             pr = requests.post(f"{st.session_state.api_url}/profiles/parse", json={"text": st.session_state.raw_text}, timeout=15)
#             if pr.ok:
#                 parsed = pr.json().get("profile", {})
#                 for kf, v in parsed.items():
#                     if prof.get(kf) in (None,"",0) and v not in (None,"",0):
#                         prof[kf] = v
#         except Exception as e:
#             st.warning(f"Parse failed: {e}")

#     payload = {"profile": prof, "k": int(k)}
#     if mode_pref == "Latency+": payload["mode"] = "degraded"
#     elif mode_pref == "Accuracy+": payload["mode"] = "online"

#     with st.status("Matching...", expanded=False) as s:
#         try:
#             r = requests.post(f"{st.session_state.api_url}/match/top", json=payload, timeout=40)
#             st.session_state.result = r.json() if r.ok else None
#             s.update(label="Done" if r.ok else "Failed", state="complete" if r.ok else "error")
#         except Exception as e:
#             s.update(label=f"Failed: {e}", state="error")
#             st.session_state.result = None

# res = st.session_state.get("result")
# if res:
#     st.subheader(f"Results • {len(res.get('matches',[]))} matches")
#     st.caption(f"Mode: {res.get('mode')}")

#     matches = res.get("matches", [])
#     if dedupe_city:
#         matches = [m for m in matches if (m.get('city') or '').lower() == (city or '').lower()]

#     # One-line rows
#     for m in matches:
#         parts = []
#         parts.append(f"<span class='score'>⭐ {m.get('score',0)}</span>")
#         parts.append(f"<span class='mono'>{m.get('other_name') or m.get('other_profile_id')}</span>")
#         parts.append(f"<span class='badge'>{m.get('city') or '—'}</span>")
#         if m.get('budget_pkr'): parts.append(f"<span class='pill'>PKR {m.get('budget_pkr')}</span>")
#         rs = m.get('reasons', [])
#         if rs: parts.append(f"<span class='muted'>{'; '.join(rs[:2])}</span>")
#         if show_conflicts and m.get('conflicts'):
#             cf = m['conflicts'] if isinstance(m['conflicts'], list) else [m['conflicts']]
#             for c in cf: parts.append(f"<span class='conflict'>{c}</span>")
#         st.markdown(f"""<div class='result-row'>{' • '.join(parts)}</div>""", unsafe_allow_html=True)
#         tips = m.get('tips') or []
#         if tips:
#             st.markdown(''.join([f"<span class='tip'>💡 {t}</span>" for t in tips]), unsafe_allow_html=True)

#     if show_rooms:
#         st.markdown("### 🛏️ Suggested Rooms")
#         cols = st.columns(3)
#         for i, rinfo in enumerate(res.get("rooms", [])):
#             with cols[i % 3]:
#                 # Fallback "card" without st.container(border=True)
#                 st.markdown("<div class='card'>", unsafe_allow_html=True)
#                 st.write(f"**{rinfo.get('city')}, {rinfo.get('area')}**")
#                 st.write(f"PKR {rinfo.get('monthly_rent_PKR')}")
#                 st.caption(', '.join(rinfo.get('amenities', [])) or '—')
#                 st.write(rinfo.get('why_match'))
#                 st.markdown("</div>", unsafe_allow_html=True)

# frontend/streamlit_app.py
# frontend/streamlit_app.py
# frontend/streamlit_app.py
# frontend/streamlit_app.py
# frontend/streamlit_app.py
import os, json, time, requests, streamlit as st

# -------------------- Styling --------------------
def inject_css():
    st.markdown("""
    <style>
      /* Dark page; keep cards white */
      body, .stApp, .main {
        background-color: #0B0B0B !important;
        color: #E5E7EB !important;
      }

      /* White cards */
      .rm-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        padding: 12px 14px;
        margin: 8px 0;
        box-shadow: 0 1px 0 rgba(2,6,23,0.04), 0 8px 24px rgba(2,6,23,0.06);
      }
      .rm-row { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
      .rm-title { font-weight:700; letter-spacing:.2px; color:#0F172A; }  /* dark ink inside white card */
      .rm-muted { color:#64748B; }
      .rm-ink { color:#0F172A; }        /* strong dark ink */
      .rm-strong { color:#000 !important; font-weight:500; }  /* strong black text */
      .small { font-size:12px; }

      .rm-pill {
        display:inline-block;
        background:#F8FAFC;
        border:1px solid #E2E8F0;
        color:#0F172A;
        padding:2px 8px;
        border-radius:999px;
        font-size:12px;
      }
      .rm-good { background:#DCFCE7; color:#166534; border-color:transparent; }
      .rm-bad  { background:#FEE2E2; color:#991B1B; border-color:transparent; }

      /* Score stripes (matches) */
      .rm-score-strong { border-left:6px solid #22C55E; }
      .rm-score-mid    { border-left:6px solid #F59E0B; }
      .rm-score-weak   { border-left:6px solid #EF4444; }

      /* Rent-fit stripes (rooms) */
      .rm-room-good { border-left:6px solid #22C55E; }
      .rm-room-mid  { border-left:6px solid #F59E0B; }
      .rm-room-bad  { border-left:6px solid #EF4444; }

      /* Conflict banner (support both class names) */
      .rm-conf, .rm-alert {
        margin-top: 6px;
        font-weight: 700;
        color: #991B1B;            /* dark red text */
        background: #FEE2E2;       /* light red bg */
        border: 1px solid #fecaca; /* softer red border */
        border-radius: 8px;
        padding: 6px 8px;
        display: inline-block;
      }
    </style>
    """, unsafe_allow_html=True)

# Fix common UTF-8/Windows-1252 artifacts in strings
def _clean_text(s: str) -> str:
    if not isinstance(s, str):
        return ""
    return (s.replace("â€", "—")
             .replace("â€“", "–")
             .replace("â€”", "—")
             .replace("Â±", "±")
             .replace("Â", ""))

def one_line_match(m: dict, q_budget: int | None = None) -> str:
    name = m.get("other_name") or m.get("other_profile_id") or "Candidate"
    pid  = m.get("other_profile_id") or "-"
    city = m.get("city") or "—"
    score = int(m.get("score", 0))
    their_budget = m.get("budget_pkr")
    your_budget  = q_budget

    # Ensure budgets display
    your_txt  = f"PKR {int(your_budget):,}"  if isinstance(your_budget,  (int,float)) and your_budget  else "—"
    their_txt = f"PKR {int(their_budget):,}" if isinstance(their_budget, (int,float)) and their_budget else "—"

    # Build diverse reasons from subscores + API reasons
    api_reasons = [r for r in (m.get("reasons") or []) if isinstance(r, str)]
    subs = m.get("subscores") or {}
    label_map = {
        "city": "Same city",
        "budget": "Budgets align (±20%)",
        "sleep": "Similar sleep schedule",
        "cleanliness": "Same cleanliness preference",
        "noise": "Similar noise tolerance",
        "study": "Similar study habits",
        "smoking": "Smoking preference aligned",
        "guests": "Guests frequency compatible",
    }
    ranked_labels = [label_map[k] for k, v in sorted(subs.items(), key=lambda kv: kv[1], reverse=True)
                     if v and k in label_map][:5]

    merged = []
    for r in (ranked_labels + api_reasons):
        r = _clean_text(r)
        if r not in merged:
            merged.append(r)
    reason_txt = _clean_text(" • ".join(merged[:3]) if merged else "Good overlap")

    # Conflicts (can be list[str] or list[dict])
    conflicts = m.get("conflicts") or []
    conflict_items = []
    for c in conflicts:
        if isinstance(c, str):
            conflict_items.append(_clean_text(c))
        elif isinstance(c, dict):
            t = _clean_text(c.get("type", ""))
            if t:
                conflict_items.append(t)
    clash_html = f"<div class='rm-alert'>⚠️ " + ", ".join(conflict_items) + "</div>" if conflict_items else ""

    # Tips (max 2, cleaned)
    tips = [t for t in (m.get("tips") or []) if isinstance(t, str)]
    tip_txt = "<br>".join([f"💡 {_clean_text(t)}" for t in tips[:2]])

    # Score stripe
    stripe = "rm-score-weak"
    if score >= 70:   stripe = "rm-score-strong"
    elif score >= 50: stripe = "rm-score-mid"

    return f"""
      <div class="rm-card {stripe}">
        <div class="rm-row">
          <span class="rm-title">{name}</span>
          <span class="rm-muted">({city})</span>
          <span class="rm-pill rm-good">Score {score}</span>
          <span class="rm-pill">Your budget: {your_txt}</span>
          <span class="rm-pill">Their budget: {their_txt}</span>
          <span class="rm-pill">Profile: {pid}</span>
        </div>
        <div class="rm-strong small">{reason_txt}</div>
        {clash_html}
        <div class="rm-strong small">{tip_txt}</div>
      </div>
    """

# -------------------- HTTP helpers --------------------
DEFAULT_TIMEOUT = 60
def _with_retries(func, *args, retries=2, backoff=1.5, **kwargs):
    last_err = None
    for i in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_err = e
            time.sleep(backoff ** i)
    raise last_err

def get(url: str, timeout=DEFAULT_TIMEOUT):
    def _do():
        r = requests.get(url, timeout=timeout); r.raise_for_status(); return r.json()
    return _with_retries(_do)

def post(url: str, payload: dict, timeout=DEFAULT_TIMEOUT):
    def _do():
        r = requests.post(
            url,
            data=json.dumps(payload),
            headers={"Content-Type":"application/json"},
            timeout=timeout
        )
        r.raise_for_status(); return r.json()
    return _with_retries(_do)

def api_health(api_base: str):
    try:
        return get(f"{api_base}/healthz")
    except Exception as e:
        return {"error": str(e)}

# Rent fitness stripe (compare room rent vs per-person budget * 2)
def room_fit_class(monthly_rent: int | float, user_budget_pp: int | float | None) -> str:
    if not monthly_rent or not user_budget_pp:
        return "rm-room-mid"
    target = float(user_budget_pp) * 2.0
    if target <= 0:
        return "rm-room-mid"
    delta = abs(monthly_rent - target) / target
    if delta <= 0.10:
        return "rm-room-good"
    if delta <= 0.25:
        return "rm-room-mid"
    return "rm-room-bad"

# -------------------- App --------------------
st.set_page_config(page_title="Room Matcher AI", page_icon="🧭", layout="centered")
inject_css()
st.title("Room Matcher AI")
st.caption("Smarter roommate matching — explainable, fast, and bandwidth-aware.")

with st.sidebar:
    st.subheader("Settings")
    api_base = st.text_input("API URL", os.getenv("ROOM_MATCHER_API", "http://127.0.0.1:8080"))
    mode_choice = st.radio("Engine Mode", ["Degraded (offline/low bw)", "Live (FAISS/ML)"], index=0)
    pref_choice = st.radio("Preference", ["Accuracy+", "Speed+"], index=0)
    show_rooms = st.checkbox("Show room suggestions", value=True)
    if st.button("Check API"): st.session_state["api_info"] = api_health(api_base)

if "api_info" not in st.session_state:
    st.session_state["api_info"] = api_health(api_base)

api_info = st.session_state["api_info"]
if "error" in api_info:
    st.warning(f"API not reachable yet: {api_info['error']}")
else:
    backend_mode = api_info.get("last_effective_mode") or api_info.get("server_default_mode")
    st.caption(f"Backend default: {backend_mode}")

with st.form("query"):
    c1, c2 = st.columns(2)
    with c1:
        city = st.selectbox("City", ["", "Lahore", "Karachi", "Islamabad", "Peshawar", "Quetta"], index=1)
        budget = st.number_input("Budget (PKR)", min_value=0, step=500, value=17500)
        sleep = st.selectbox("Sleep", ["", "early_bird", "night_owl", "flex"], index=2)
    with c2:
        cleanliness = st.selectbox("Cleanliness", ["", "low", "medium", "high"], index=2)
        noise_tol = st.selectbox("Noise Tolerance", ["", "low", "medium", "high"], index=1)
        guests = st.selectbox("Guests", ["", "rare", "sometimes", "often", "daily"], index=3)
    smoking = st.selectbox("Smoking", ["", "no", "yes"], index=1)

    ad_text = st.text_area(
        "Optional mixed Urdu/English ad (auto-parse)",
        height=90,
        placeholder="e.g., Need roomie in Lahore, budget 18k, mostly study at night, please no smoking..."
    )

    top_k = 10 if pref_choice == "Accuracy+" else 5
    submit = st.form_submit_button("Find matches", use_container_width=True)

if submit:
    profile = {
        "city": city or None,
        "budget_pkr": int(budget) if budget else None,
        "sleep_schedule": sleep or None,
        "cleanliness": cleanliness or None,
        "noise_tolerance": noise_tol or None,
        "guests_freq": guests or None,
        "smoking": smoking or None,
        "raw_text": ad_text or None,
    }
    api_mode = "degraded" if "Degraded" in mode_choice else "online"

    # Optional parse/enrich
    if ad_text.strip():
        try:
            parsed = post(f"{api_base}/profiles/parse", {"text": ad_text, "mode": api_mode})
            prof2 = parsed.get("profile", {})
            for k, v in prof2.items():
                if k in profile and (profile[k] in (None, "")) and v:
                    profile[k] = v
        except Exception as e:
            st.warning(f"Parse failed (continuing): {e}")

    try:
        with st.spinner("Matching…"):
            payload = {"profile": profile, "k": top_k, "mode": api_mode}
            resp = post(f"{api_base}/match/top", payload)
            matches = resp.get("matches", [])
            rooms = resp.get("rooms", [])
            mode = resp.get("mode", api_mode)

        st.caption(f"Mode: {mode}")

        # Sort on client too (defensive)
        matches = sorted(matches, key=lambda mm: mm.get("score", 0), reverse=True)

        # Matches (white cards with score stripe + budgets)
        if matches:
            limit = 5 if pref_choice == "Accuracy+" else min(5, top_k)
            for m in matches[:limit]:
                st.markdown(
                    one_line_match(m, q_budget=int(budget) if budget else None),
                    unsafe_allow_html=True
                )
        else:
            st.info("Showing best available candidates (fallback).")

        # Suggested rooms with rent-fit stripes
        if show_rooms and rooms:
            st.subheader("🛏️ Suggested Rooms")
            user_budget_pp = int(budget) if budget else None
            for r in rooms:
                rent  = int(r.get("monthly_rent_PKR") or 0)
                klass = room_fit_class(rent, user_budget_pp)
                city_area = f"{r.get('city')}, {r.get('area')}"
                am = ", ".join(r.get("amenities") or [])
                why = _clean_text(r.get("why_match",""))
                lid = r.get("listing_id","-")
                st.markdown(
                    f'''
                    <div class="rm-card {klass}">
                      <div class="rm-row">
                        <b class="rm-ink">{city_area}</b>
                        <span class="rm-ink">— PKR {rent:,}</span>
                        <span class="rm-pill">Listing: {lid}</span>
                      </div>
                      <div class="rm-muted small">{am}</div>
                      <div class="small"><span class="rm-pill">{why}</span></div>
                    </div>
                    ''',
                    unsafe_allow_html=True
                )

    except requests.HTTPError as e:
        st.error(f"API error: {e.response.text}")
    except Exception as e:
        st.error(f"Request failed: {e}")
