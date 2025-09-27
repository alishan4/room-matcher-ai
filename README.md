# Room Matcher AI (Hackathon Prototype)

Smarter student living: agentic, explainable roommate matching with optional housing suggestions.
Works **online** with embeddings retrieval and **degraded/offline** with rule-first matching.

## Features
- Profile Reader Agent: Urdu/English "Urglish" parsing via regex + lexicons.
- Match Scorer Agent: interpretable 100-point compatibility scoring with subscores.
- Red Flag Agent: lifestyle conflicts and deal-breakers with severity.
- Wingman Agent: human-friendly reasons and compromise tips.
- Room Hunter Agent (optional): shortlist available listings by budget/city/amenities.
- Agent Trace: JSON trace/log for transparency.
- Mode switch: `MODE=online` uses embeddings+FAISS; `MODE=degraded` is token-free, offline.

## Quickstart (Local, Degraded Mode)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export MODE=degraded
uvicorn app.main:app --reload --port 8000
# Open http://127.0.0.1:8000/docs
```
## Online Mode (Embeddings Retrieval)
```bash
export MODE=online
uvicorn app.main:app --reload --port 8000
```

## Endpoints
- `POST /profiles/parse` {text} → normalized profile + confidences
- `POST /match/top` {profile, k?} → top matches with reasons, conflicts, trace
- `POST /pair/explain` {a_id, b_id} → reasons, conflicts, tips
- `POST /rooms/suggest` {city, per_person_budget, needed_amenities[]} → listings
- `GET /healthz`

## Deploy (Cloud Run, optional)
See `Dockerfile` and `cloudbuild.yaml` in README bottom.
