# 🏠 Room Matcher AI — National Agentic AI Hackathon Prototype

Smarter roommate matching — explainable, fast, and bandwidth-aware.  
Built for the **National Agentic AI Hackathon** to help students across Pakistan
find compatible roommates and safe housing.

---

## 🌍 Problem Statement

Finding a compatible roommate is a **stressful and time-consuming process** for students:

- Reliance on Facebook groups, WhatsApp forwards, or word-of-mouth  
- Leads to **poor matches**, **lifestyle clashes**, and sometimes **unsafe housing**  
- No transparent way to understand *why* someone is a good/bad match

**Students need a smarter, trustworthy, and autonomous way** to find roommates and housing.

---

## 💡 Our Solution

Room Matcher AI is a **multi-agent AI system** that:

- Parses messy Urdu/English roommate ads into structured profiles  
- Rates compatibility between students across multiple lifestyle attributes  
- Explains *why* two students are (or are not) a good match  
- Flags conflicts before they become a problem  
- Suggests real housing listings within budget in the right city  

All in a **transparent, explainable, and bandwidth-aware way** — working **online with Firestore** or **offline in degraded mode**.

---

## 🗂️ Database & Data Sources

We use two datasets (in Firestore + JSON fallback):

1. **Profiles Collection (`profiles`)**
   - ~400 synthetic roommate entries
   - Each profile includes:
     - `id`, `city`, `budget_pkr`
     - Lifestyle attributes: `sleep_schedule`, `cleanliness`, `noise_tolerance`, `study_habits`, `food_pref`, `smoking`, `guests_freq`
     - Free-text ad (`raw_profile_text`)
   - Example:
     ```json
     {
       "id": "R-010",
       "city": "Rawalpindi",
       "area": "Satellite Town",
       "budget_pkr": 22000,
       "sleep_schedule": "Early riser",
       "cleanliness": "Messy",
       "study_habits": "Online classes",
       "food_pref": "Non-veg",
       "noise_tolerance": "Moderate",
       "raw_profile_text": "Room share Rawalpindi Satellite Town. Rent 22k..."
     }
     ```

2. **Listings Collection (`listings`)**
   - ~400 housing entries
   - Each listing includes:
     - `id`, `city`, `area`, `monthly_rent_PKR`
     - `amenities`, `rooms_available`, `status`
   - Example:
     ```json
     {
       "id": "H-0256",
       "city": "Lahore",
       "area": "Johar Town",
       "monthly_rent_PKR": 17839,
       "amenities": ["WiFi", "Mess facility", "Furnished", "Separate washroom"],
       "status": "available"
     }
     ```

---

## 🧠 Multi-Agent System

### 1. Profile Reader Agent  
Parses **messy Urdu/English roommate ads** into structured attributes.  
✔ Handles free text like *"Need roomie in Lahore, budget 18k, night owl, no smoking please"*  

### 2. Match Scorer Agent  
Rates compatibility across attributes:  
- Sleep schedule  
- Cleanliness  
- Noise tolerance  
- Study habits  
- Smoking preference  
- Guests frequency  
- Budget alignment  

### 3. Red Flag Agent  
Detects **conflicts** such as:  
- "Early riser" vs "Night owl"  
- "Quiet study" vs "Tabla practice at night"  
- "No smoking" vs "Smoker"  

### 4. Wingman Agent  
Explains **why the match works (or not)**:  
- 💡 "You're in the same city – logistics are easy."  
- 💡 "Budgets align – split rent fairly and track utilities."  
- ⚠️ "Conflict: one prefers silence, the other has daily guests."  

### 5. Room Hunter Agent  
Suggests **real housing listings**:  
- Within the user’s budget ± tolerance  
- In the right city/area  
- Ranked by **amenity overlap**

---

## ⚙️ Modes of Operation

### 🔹 Online Mode (Live / Firestore + FAISS)
- Reads **profiles** and **listings** from Firestore  
- Uses FAISS embeddings for **semantic retrieval** (smarter search)  
- Best for production use  

### 🔹 Degraded Mode (Offline / JSON + Keyword)
- Reads from **local JSON files**  
- Rule-based retrieval (city + budget + keyword)  
- Lightweight, works in **low bandwidth** or **offline environments**  

Both modes return **the same schema**, so frontend works seamlessly.

---

## 🚀 Running Locally

### 1. Backend (FastAPI)

Install deps:
```bash
pip install -r requirements.txt
