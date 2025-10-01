from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.graph import run_pipeline
from app.services.firestore import (
    fetch_all_listings,
    fetch_all_profiles,
    fetch_notified_matches,
    fetch_watcher_config,
    store_notified_matches,
)
from app.services.notifier import NotificationPayload, Notifier
from app.services.task_queue import celery_app
from app.agents.match_scorer import MatchScoreConfig


LOGGER = logging.getLogger(__name__)


def _default_cadence() -> int:
    return int(os.getenv("AUTO_HUNT_DEFAULT_CADENCE_SEC", "900"))


def _default_min_score() -> int:
    return int(os.getenv("AUTO_HUNT_DEFAULT_MIN_SCORE", "55"))


def _default_top_k() -> int:
    return int(os.getenv("AUTO_HUNT_DEFAULT_TOP_K", "5"))


def _default_channels() -> List[str]:
    raw = os.getenv("AUTO_HUNT_DEFAULT_CHANNELS", "email")
    return [c.strip() for c in raw.split(",") if c.strip()]


def _use_async() -> bool:
    if os.getenv("AUTO_HUNT_FORCE_SYNC", "false").lower() == "true":
        return False
    return bool(os.getenv("CELERY_BROKER_URL"))


def _scope_from_profile(user_profile: Dict[str, Any], institution_id: Optional[str]) -> str:
    return (
        institution_id
        or user_profile.get("institution_id")
        or user_profile.get("campus")
        or user_profile.get("organization")
        or "default"
    )


def profile_key(user_profile: Dict[str, Any]) -> str:
    """Stable identifier for watcher state storage."""

    for field in ("id", "profile_id", "email", "phone", "phone_number"):
        if user_profile.get(field):
            return str(user_profile[field])
    digest = hashlib.sha1(str(sorted(user_profile.items())).encode("utf-8")).hexdigest()
    return f"anon-{digest}"


@dataclass
class WatcherConfig:
    cadence_sec: int = field(default_factory=_default_cadence)
    min_score: int = field(default_factory=_default_min_score)
    top_k: int = field(default_factory=_default_top_k)
    channels: List[str] = field(default_factory=_default_channels)
    partner_webhooks: List[str] = field(default_factory=list)
    match_config: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "WatcherConfig":
        if not payload:
            return cls()
        return cls(
            cadence_sec=int(payload.get("cadence_sec", _default_cadence())),
            min_score=int(payload.get("min_score", _default_min_score())),
            top_k=int(payload.get("top_k", _default_top_k())),
            channels=list(payload.get("channels") or _default_channels()),
            partner_webhooks=list(payload.get("partner_webhooks", []) or []),
            match_config=payload.get("match_config"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cadence_sec": self.cadence_sec,
            "min_score": self.min_score,
            "top_k": self.top_k,
            "channels": list(self.channels),
            "partner_webhooks": list(self.partner_webhooks),
            "match_config": self.match_config,
        }


def get_watcher_config(user_profile: Dict[str, Any], institution_id: Optional[str] = None) -> WatcherConfig:
    scope = _scope_from_profile(user_profile, institution_id)
    overrides = fetch_watcher_config(scope)
    return WatcherConfig.from_dict(overrides)


def _build_match_config(config: Optional[Dict[str, Any]]) -> Optional[MatchScoreConfig]:
    if not config:
        return None
    weights = config.get("weights")
    anchor_buckets = config.get("anchor_buckets")
    kwargs: Dict[str, Any] = {}
    if weights:
        kwargs["weights"] = dict(weights)
    if anchor_buckets:
        kwargs["anchor_buckets"] = tuple(tuple(bucket) for bucket in anchor_buckets)
    return MatchScoreConfig(**kwargs)


def _run_auto_hunt_cycle(
    user_profile: Dict[str, Any],
    scope: str,
    config: WatcherConfig,
) -> Dict[str, Any]:
    profiles = fetch_all_profiles()
    listings = fetch_all_listings()

    key = profile_key(user_profile)
    previously_notified = set(fetch_notified_matches(scope, key))

    pipeline_result = run_pipeline(
        user_profile,
        profiles,
        listings,
        mode="online",
        top_k=config.top_k,
        match_config=_build_match_config(config.match_config),
        notified_match_ids=previously_notified,
    )

    matches = pipeline_result.get("matches", [])
    new_matches = [m for m in matches if m.get("is_new") and (m.get("score") or 0) >= config.min_score]

    notifier = Notifier()
    payload = NotificationPayload(
        scope=scope,
        user_profile=user_profile,
        matches=new_matches,
        rooms=pipeline_result.get("rooms", []),
        trace=pipeline_result.get("trace", {}),
        metadata={"min_score": config.min_score, "top_k": config.top_k},
    )

    channel_results: Dict[str, Any] = {}
    if new_matches:
        LOGGER.info("Dispatching notifications for %s (scope=%s)", key, scope)
        channel_results = notifier.dispatch(payload, config.channels, config.partner_webhooks)
        previously_notified.update(m.get("other_profile_id") for m in new_matches if m.get("other_profile_id"))
        store_notified_matches(scope, key, sorted(previously_notified))
    else:
        LOGGER.info("No new matches for %s (scope=%s)", key, scope)

    return {
        "config": config.to_dict(),
        "result": pipeline_result,
        "new_matches": new_matches,
        "notifications": channel_results,
        "scope": scope,
        "profile_key": key,
    }


@celery_app.task(name="watcher.auto_hunt", bind=True)
def run_auto_hunt_task(self, user_profile: Dict[str, Any], scope: str, config_override: Optional[Dict[str, Any]] = None, reschedule: bool = True) -> Dict[str, Any]:
    config = WatcherConfig.from_dict(config_override)
    outcome = _run_auto_hunt_cycle(user_profile, scope, config)

    if reschedule and config.cadence_sec > 0:
        LOGGER.debug("Scheduling next auto-hunt run for %s in %s seconds", outcome["profile_key"], config.cadence_sec)
        run_auto_hunt_task.apply_async(
            kwargs={
                "user_profile": user_profile,
                "scope": scope,
                "config_override": config.to_dict(),
            },
            countdown=config.cadence_sec,
        )

    return outcome


def auto_hunt(
    user_profile: Dict[str, Any],
    institution_id: Optional[str] = None,
    reschedule: bool = True,
) -> Any:
    """Schedule the auto-hunt background job for a user.

    When a Celery broker is configured, the job is enqueued asynchronously.  In
    development (or tests) without Celery the pipeline runs synchronously to
    preserve backwards compatibility.
    """

    scope = _scope_from_profile(user_profile, institution_id)
    config = get_watcher_config(user_profile, institution_id)

    if _use_async():
        LOGGER.info("Queueing auto-hunt task for scope=%s profile=%s", scope, profile_key(user_profile))
        result = run_auto_hunt_task.apply_async(
            kwargs={
                "user_profile": user_profile,
                "scope": scope,
                "config_override": config.to_dict(),
                "reschedule": reschedule,
            }
        )
        return result.id

    LOGGER.info("Running auto-hunt synchronously for scope=%s profile=%s", scope, profile_key(user_profile))
    return run_auto_hunt_task.run(
        user_profile=user_profile,
        scope=scope,
        config_override=config.to_dict(),
        reschedule=reschedule,
    )


__all__ = [
    "auto_hunt",
    "get_watcher_config",
    "profile_key",
    "run_auto_hunt_task",
    "WatcherConfig",
]
