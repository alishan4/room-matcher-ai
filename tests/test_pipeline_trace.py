from app.graph import run_pipeline
from app.services.firestore import fetch_all_profiles, fetch_all_listings


def test_trace_marks_new_vs_notified():
    profiles = fetch_all_profiles()
    listings = fetch_all_listings()

    # Use the first profile as the seeker.
    seeker = profiles[0]

    baseline = run_pipeline(seeker, profiles, listings, top_k=3)
    assert baseline["matches"], "expected at least one baseline match"

    first_match = baseline["matches"][0]["other_profile_id"]

    rerun = run_pipeline(
        seeker,
        profiles,
        listings,
        top_k=3,
        notified_match_ids={first_match},
    )

    match_statuses = {m["other_profile_id"]: m["notification_status"] for m in rerun["matches"] if m.get("other_profile_id")}
    assert match_statuses[first_match] == "notified"

    trace_agents = [step["agent"] for step in rerun["trace"]["steps"]]
    assert "MatchNotifier" in trace_agents

    notifier_step = next(step for step in rerun["trace"]["steps"] if step["agent"] == "MatchNotifier")
    assert notifier_step["outputs"]["previously_notified"] >= 1
