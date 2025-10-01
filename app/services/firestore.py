import os
import threading
from typing import List, Dict, Optional, Tuple, Any
from app.agents.profile_reader import normalize_profile

USE_FIRESTORE = os.getenv("FIRESTORE_ENABLED", "false").lower() == "true"
PROJECT_ID = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
_CREDENTIALS_PATH = os.getenv("FIRESTORE_CREDENTIALS")

if _CREDENTIALS_PATH and os.path.exists(_CREDENTIALS_PATH):
    # Surface the secret-based credentials to the Google client libraries.  When
    # Cloud Run injects a secret via --set-secrets the environment variable
    # points to a file path containing the JSON payload.
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", _CREDENTIALS_PATH)

_CONFIG_LOCK = threading.Lock()
_LOCAL_CONFIG_CACHE: Dict[str, Dict[str, Any]] = {}
_LOCAL_NOTIFIED_CACHE: Dict[Tuple[str, str], List[str]] = {}

def _client():
    from google.cloud import firestore
    return firestore.Client(project=PROJECT_ID)

def _local_json(rel_path: str) -> List[Dict]:
    import json
    p = os.path.join(os.path.dirname(__file__), "..", "data", rel_path)
    with open(os.path.abspath(p), "r", encoding="utf-8") as f:
        return json.load(f)

# -------------------------------
# Profiles
# -------------------------------
def fetch_all_profiles() -> List[Dict]:
    if not USE_FIRESTORE:
        # degraded: local JSON, but still normalize
        raw = _local_json("profiles_extended.json")
        return [normalize_profile(d) for d in raw]

    db = _client()
    docs = db.collection("profiles").stream()
    raw = [d.to_dict() for d in docs]
    return [normalize_profile(d) for d in raw]

def fetch_by_id(pid: str) -> Optional[Dict]:
    if not USE_FIRESTORE:
        for p in fetch_all_profiles():
            if p.get("id") == pid:
                return p
        return None
    db = _client()
    doc = db.collection("profiles").document(pid).get()
    return normalize_profile(doc.to_dict()) if doc.exists else None

# -------------------------------
# Listings
# -------------------------------
def fetch_all_listings() -> List[Dict]:
    if not USE_FIRESTORE:
        return _local_json("listings_extended.json")

    db = _client()
    docs = db.collection("listings").stream()
    return [d.to_dict() for d in docs]


# -------------------------------
# Watcher configuration + state
# -------------------------------

def fetch_watcher_config(scope: str) -> Dict[str, Any]:
    """Return watcher configuration for a tenant/institution scope."""

    if not scope:
        scope = "default"

    if not USE_FIRESTORE:
        with _CONFIG_LOCK:
            return dict(_LOCAL_CONFIG_CACHE.get(scope, {}))

    db = _client()
    doc = db.collection("watcher_configs").document(scope).get()
    return doc.to_dict() if doc.exists else {}


def upsert_watcher_config(scope: str, data: Dict[str, Any]) -> None:
    """Persist watcher configuration overrides."""

    if not scope:
        scope = "default"

    if not USE_FIRESTORE:
        with _CONFIG_LOCK:
            existing = dict(_LOCAL_CONFIG_CACHE.get(scope, {}))
            existing.update(data)
            _LOCAL_CONFIG_CACHE[scope] = existing
        return

    db = _client()
    db.collection("watcher_configs").document(scope).set(data, merge=True)


def fetch_notified_matches(scope: str, profile_key: str) -> List[str]:
    """Read the set of previously notified match ids for a profile."""

    scope = scope or "default"
    profile_key = profile_key or "unknown"

    if not USE_FIRESTORE:
        with _CONFIG_LOCK:
            return list(_LOCAL_NOTIFIED_CACHE.get((scope, profile_key), []))

    db = _client()
    doc = (
        db.collection("watcher_state")
        .document(scope)
        .collection("profiles")
        .document(profile_key)
        .get()
    )
    if not doc.exists:
        return []
    payload = doc.to_dict() or {}
    return list(payload.get("notified_match_ids", []))


def store_notified_matches(scope: str, profile_key: str, match_ids: List[str]) -> None:
    """Persist the deduplicated list of match ids already notified."""

    scope = scope or "default"
    profile_key = profile_key or "unknown"
    deduped = sorted(set(filter(None, match_ids)))

    if not USE_FIRESTORE:
        with _CONFIG_LOCK:
            if deduped:
                _LOCAL_NOTIFIED_CACHE[(scope, profile_key)] = deduped
            else:
                _LOCAL_NOTIFIED_CACHE.pop((scope, profile_key), None)
        return

    db = _client()
    doc_ref = (
        db.collection("watcher_state")
        .document(scope)
        .collection("profiles")
        .document(profile_key)
    )

    if not deduped:
        doc_ref.delete()
        return

    # Lazy import to avoid requiring Firestore when running locally.
    from google.cloud import firestore as firestore_sdk

    doc_ref.set(
        {
            "notified_match_ids": deduped,
            "updated_at": firestore_sdk.SERVER_TIMESTAMP,
        },
        merge=True,
    )

# -------------------------------
# Local wrapper for degraded mode
# -------------------------------
class LocalDB:
    """Compat wrapper some modules use; returns normalized profiles & listings."""
    def __init__(self):
        self._profiles = fetch_all_profiles()
        self._listings = fetch_all_listings()
    def all_profiles(self): return self._profiles
    def all_listings(self): return self._listings
