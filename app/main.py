import json
import logging
import os
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .agents.room_hunter import suggest_rooms
from .graph import run_pipeline
from .services.firestore import fetch_all_listings, fetch_all_profiles

PROJECT_ID = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
SERVICE_NAME = os.getenv("SERVICE_NAME", "room-matcher-ai")
STRUCTURED_LOGGING = os.getenv("ENABLE_STRUCTURED_LOGS", "true").lower() == "true"
ENABLE_STARTUP_WARMUP = os.getenv("ENABLE_STARTUP_WARMUP", "true").lower() == "true"
FAISS_ENV_FLAG = os.getenv("FAISS_ENABLED")
FAISS_ENABLED = (FAISS_ENV_FLAG or "false").lower() == "true"

SERVER_DEFAULT_MODE = os.getenv("MODE", "online").lower()
FIRESTORE_ENABLED = os.getenv("FIRESTORE_ENABLED", "true").lower() == "true"
CACHE_TTL_SEC = int(os.getenv("CACHE_TTL_SEC", "120"))

logger = logging.getLogger("room-matcher")
if not logger.handlers:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(message)s",
    )
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

_profiles_cache: List[Dict[str, Any]] = []
_listings_cache: List[Dict[str, Any]] = []
_cache_at: float = 0.0
LAST_EFFECTIVE_MODE = SERVER_DEFAULT_MODE
_CACHE_LOCK = threading.Lock()
_METRICS_LOCK = threading.Lock()
_REQUEST_METRICS: Dict[str, Any] = {
    "total_requests": 0,
    "total_errors": 0,
    "total_latency_ms": 0.0,
    "max_latency_ms": 0.0,
    "last_request_ts": None,
}
_LAST_WARMUP: float = 0.0
_FAISS_STORE: Optional[Any] = None


def _emit_log(level: int, event: str, trace_id: Optional[str] = None, **payload: Any) -> None:
    entry: Dict[str, Any] = {
        "event": event,
        "service": SERVICE_NAME,
        **{k: v for k, v in payload.items() if v is not None},
    }
    if trace_id:
        entry["trace_id"] = trace_id
        if PROJECT_ID:
            entry["logging.googleapis.com/trace"] = f"projects/{PROJECT_ID}/traces/{trace_id}"
    try:
        if STRUCTURED_LOGGING:
            logger.log(level, json.dumps(entry, default=str))
        else:
            logger.log(level, "%s %s", event, entry)
    except Exception:  # pragma: no cover - fallback safeguard
        logger.log(level, "%s %s", event, entry)


def _record_metrics(duration_ms: float, status_code: int) -> None:
    with _METRICS_LOCK:
        _REQUEST_METRICS["total_requests"] += 1
        _REQUEST_METRICS["total_latency_ms"] += duration_ms
        _REQUEST_METRICS["max_latency_ms"] = max(_REQUEST_METRICS["max_latency_ms"], duration_ms)
        _REQUEST_METRICS["last_request_ts"] = time.time()
        if status_code >= 500:
            _REQUEST_METRICS["total_errors"] += 1


def _metrics_snapshot() -> Dict[str, Any]:
    with _METRICS_LOCK:
        total = _REQUEST_METRICS["total_requests"]
        avg_latency = _REQUEST_METRICS["total_latency_ms"] / total if total else 0.0
        return {
            "total_requests": total,
            "total_errors": _REQUEST_METRICS["total_errors"],
            "avg_latency_ms": round(avg_latency, 2),
            "max_latency_ms": round(_REQUEST_METRICS["max_latency_ms"], 2),
            "last_request_ts": _REQUEST_METRICS["last_request_ts"],
        }


def _warmup_faiss() -> bool:
    global _FAISS_STORE
    if not FAISS_ENABLED:
        return False
    if _FAISS_STORE and getattr(_FAISS_STORE, "ready", lambda: False)():
        return True
    try:
        from .services.faiss_store import FaissStore
    except Exception as exc:  # pragma: no cover - defensive import guard
        _emit_log(logging.WARNING, "faiss_import_failed", error=str(exc))
        return False
    try:
        store = FaissStore()
    except Exception as exc:  # pragma: no cover - FAISS optional
        _emit_log(logging.WARNING, "faiss_initialization_failed", error=str(exc))
        return False
    if store.ready():
        _FAISS_STORE = store
        index_size = getattr(getattr(store, "index", None), "ntotal", None)
        _emit_log(logging.INFO, "faiss_index_warmed", index_size=index_size)
        return True
    _emit_log(logging.WARNING, "faiss_index_unavailable")
    return False


def _load_cached(force: bool = False) -> None:
    global _profiles_cache, _listings_cache, _cache_at
    now = time.time()
    with _CACHE_LOCK:
        if not force and now - _cache_at < CACHE_TTL_SEC and _profiles_cache and _listings_cache:
            return
        _profiles_cache = fetch_all_profiles()
        _listings_cache = fetch_all_listings()
        _cache_at = time.time()


def warmup_caches(force: bool = False) -> Dict[str, Any]:
    global _LAST_WARMUP
    started = time.time()
    _load_cached(force=force)
    faiss_ready = _warmup_faiss()
    duration_ms = (time.time() - started) * 1000.0
    _LAST_WARMUP = time.time()
    snapshot = {
        "duration_ms": round(duration_ms, 2),
        "profiles_cached": len(_profiles_cache),
        "listings_cached": len(_listings_cache),
        "faiss_ready": faiss_ready,
    }
    _emit_log(logging.INFO, "cache_warmup_completed", **snapshot)
    return snapshot


def _mode(req_mode: Optional[str], header_mode: Optional[str]) -> str:
    global LAST_EFFECTIVE_MODE
    m = (req_mode or header_mode or SERVER_DEFAULT_MODE).lower()
    if m not in ("online", "degraded"):
        m = SERVER_DEFAULT_MODE
    LAST_EFFECTIVE_MODE = m
    return m


app = FastAPI(title="Room Matcher AI", version="0.5.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    request_id = uuid.uuid4().hex
    request.state.request_id = request_id
    start = time.perf_counter()
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as exc:
        duration_ms = (time.perf_counter() - start) * 1000.0
        _record_metrics(duration_ms, 500)
        _emit_log(
            logging.ERROR,
            "request_failed",
            request_id=request_id,
            path=request.url.path,
            method=request.method,
            duration_ms=round(duration_ms, 2),
            error=str(exc),
            user_agent=request.headers.get("user-agent"),
        )
        raise
    duration_ms = (time.perf_counter() - start) * 1000.0
    _record_metrics(duration_ms, status_code)
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
    _emit_log(
        logging.INFO,
        "request_completed",
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        status_code=status_code,
        duration_ms=round(duration_ms, 2),
        mode=LAST_EFFECTIVE_MODE,
        user_agent=request.headers.get("user-agent"),
    )
    return response


@app.on_event("startup")
async def on_startup() -> None:
    if not ENABLE_STARTUP_WARMUP:
        _emit_log(logging.INFO, "startup_warmup_skipped")
        return
    try:
        warmup_caches(force=True)
    except Exception as exc:  # pragma: no cover - startup defensive log
        _emit_log(logging.ERROR, "startup_warmup_failed", error=str(exc))


class Profile(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    city: Optional[str] = None
    budget_pkr: Optional[int] = None
    sleep_schedule: Optional[str] = None
    cleanliness: Optional[str] = None
    noise_tolerance: Optional[str] = None
    study_habits: Optional[str] = None
    food_pref: Optional[str] = None
    smoking: Optional[str] = None
    guests_freq: Optional[str] = None
    gender_pref: Optional[str] = None
    languages: Optional[List[str]] = None
    role: Optional[str] = None
    anchor_location: Optional[Dict[str, Any]] = None
    geo: Optional[Dict[str, float]] = None
    raw_text: Optional[str] = None


class ParseReq(BaseModel):
    text: str
    mode: Optional[str] = None


class MatchTopReq(BaseModel):
    profile: Profile
    k: int = 5
    mode: Optional[str] = None


class RoomSuggestReq(BaseModel):
    city: str
    per_person_budget: int
    needed_amenities: List[str] = []
    mode: Optional[str] = None
    anchor_location: Optional[Dict[str, Any]] = None
    geo: Optional[Dict[str, Any]] = None


@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "server_default_mode": SERVER_DEFAULT_MODE,
        "last_effective_mode": LAST_EFFECTIVE_MODE,
        "firestore_enabled": FIRESTORE_ENABLED,
        "project": PROJECT_ID,
        "profiles_cached": len(_profiles_cache),
        "listings_cached": len(_listings_cache),
        "cache_age_sec": max(0, int(time.time() - _cache_at)) if _cache_at else None,
        "cache_ttl_sec": CACHE_TTL_SEC,
        "metrics": _metrics_snapshot(),
        "last_warmup_at": _LAST_WARMUP or None,
        "faiss_enabled": FAISS_ENABLED,
    }


@app.post("/profiles/parse")
def parse_profile(req: ParseReq, request: Request, x_mode: Optional[str] = Header(None)):
    """Parse freeform roommate text into structured attributes."""
    mode = _mode(req.mode, x_mode)
    from .agents.profile_reader import parse_profile_text

    prof, conf = parse_profile_text(req.text, mode=mode)
    _emit_log(
        logging.INFO,
        "profile_parsed",
        request_id=getattr(request.state, "request_id", None),
        mode=mode,
        confidence=round(conf, 4),
    )
    return {"profile": prof, "confidence": conf, "mode_used": mode}


@app.post("/match/top")
def match_top(req: MatchTopReq, request: Request, x_mode: Optional[str] = Header(None)):
    """Full pipeline returning matches and enriched room suggestions."""
    mode = _mode(req.mode, x_mode)
    _load_cached()
    result = run_pipeline(
        input_profile=req.profile.dict(),
        candidates=_profiles_cache,
        listings=_listings_cache,
        mode=mode,
        top_k=req.k,
    )
    trace_id = (result.get("trace") or {}).get("trace_id")
    _emit_log(
        logging.INFO,
        "pipeline_completed",
        request_id=getattr(request.state, "request_id", None),
        mode=mode,
        matches=len(result.get("matches", [])),
        rooms=len(result.get("rooms", [])),
        trace_id=trace_id,
    )
    return JSONResponse(result)


@app.post("/rooms/suggest")
def rooms_suggest(req: RoomSuggestReq, request: Request, x_mode: Optional[str] = Header(None)):
    mode = _mode(req.mode, x_mode)
    _load_cached()
    out = suggest_rooms(
        req.city,
        req.per_person_budget,
        req.needed_amenities,
        _listings_cache,
        mode=mode,
        limit=5,
        anchor_location=req.anchor_location,
        user_geo=req.geo,
    )
    _emit_log(
        logging.INFO,
        "room_suggestions_completed",
        request_id=getattr(request.state, "request_id", None),
        mode=mode,
        listings=len(out),
    )
    return {"listings": out, "mode_used": mode}


@app.post("/__internal/warmup")
def manual_warmup(request: Request):
    stats = warmup_caches(force=True)
    _emit_log(
        logging.INFO,
        "manual_warmup_triggered",
        request_id=getattr(request.state, "request_id", None),
        **stats,
    )
    return {"status": "ok", **stats}
