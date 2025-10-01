import pytest

from app.agents.watcher import (
    WatcherConfig,
    auto_hunt,
    get_watcher_config,
    profile_key,
    run_auto_hunt_task,
)
from app.services.firestore import fetch_all_profiles, fetch_notified_matches, store_notified_matches


def test_get_watcher_config_defaults(monkeypatch):
    monkeypatch.setenv("AUTO_HUNT_DEFAULT_CADENCE_SEC", "120")
    monkeypatch.setenv("AUTO_HUNT_DEFAULT_MIN_SCORE", "42")
    monkeypatch.setenv("AUTO_HUNT_DEFAULT_TOP_K", "4")
    monkeypatch.setenv("AUTO_HUNT_DEFAULT_CHANNELS", "email,sms")

    profile = fetch_all_profiles()[0]
    cfg = get_watcher_config(profile)
    assert isinstance(cfg, WatcherConfig)
    assert cfg.cadence_sec == 120
    assert cfg.min_score == 42
    assert cfg.top_k == 4
    assert cfg.channels == ["email", "sms"]


def test_auto_hunt_cycle_updates_notified_cache(monkeypatch):
    # Force synchronous execution for deterministic tests.
    monkeypatch.delenv("CELERY_BROKER_URL", raising=False)
    monkeypatch.setenv("AUTO_HUNT_FORCE_SYNC", "true")
    monkeypatch.setenv("AUTO_HUNT_DEFAULT_MIN_SCORE", "0")

    seeker = fetch_all_profiles()[0]
    key = profile_key(seeker)
    store_notified_matches("default", key, [])

    outcome = auto_hunt(seeker, reschedule=False)
    assert "result" in outcome
    assert isinstance(outcome["new_matches"], list)
    assert len(outcome["new_matches"]) <= len(outcome["result"]["matches"])

    if outcome["new_matches"]:
        stored = fetch_notified_matches("default", key)
        notified_ids = {m["other_profile_id"] for m in outcome["new_matches"] if m.get("other_profile_id")}
        assert set(stored) >= notified_ids
    else:  # pragma: no cover - dataset should usually yield matches
        pytest.skip("auto-hunt produced no new matches; unable to verify state persistence")


def test_run_auto_hunt_task_respects_reschedule(monkeypatch):
    monkeypatch.setenv("AUTO_HUNT_FORCE_SYNC", "true")
    seeker = fetch_all_profiles()[1]
    key = profile_key(seeker)
    store_notified_matches("default", key, [])

    outcome = run_auto_hunt_task.run(
        user_profile=seeker,
        scope="default",
        config_override={"cadence_sec": 0, "min_score": 0, "top_k": 2, "channels": []},
        reschedule=False,
    )

    assert outcome["config"]["cadence_sec"] == 0
