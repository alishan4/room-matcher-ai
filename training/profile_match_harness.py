"""Offline evaluation harness for the rule-based matcher.

This script fabricates stress-test scenarios from the JSON fixtures in
``app/data`` so that we can measure how changes to the match scoring weights or
retrieval heuristics impact downstream precision.  It focuses on edge-cases for
role, budget tolerance, and anchor-distance handling.
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from dataclasses import asdict
from itertools import product
from math import cos, radians
from pathlib import Path
from statistics import mean
from typing import Dict, List, Tuple, Any

import sys

REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.graph import run_pipeline
from app.agents.match_scorer import MatchScoreConfig
from app.agents.retrieval import RetrievalConfig

DATA_DIR = REPO_ROOT / "app" / "data"
OUTPUT_DIR = Path(__file__).resolve().parent / "out"


def _load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def _ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _make_variant(base: Dict[str, Any], suffix: str, **updates: Any) -> Dict[str, Any]:
    clone = deepcopy(base)
    clone["id"] = f"{base.get('id', 'profile')}::{suffix}"
    clone["name"] = f"{base.get('name', 'Profile')} ({suffix})"
    clone.update(updates)
    return clone


def _shift_anchor(anchor: Dict[str, Any], km_north: float = 0.0, km_east: float = 0.0) -> Dict[str, Any]:
    try:
        lat = float(anchor.get("lat"))
        lng = float(anchor.get("lng"))
    except (TypeError, ValueError):
        return anchor

    lat += km_north / 111.0
    denom = max(0.00001, 111.0 * cos(radians(lat)))
    lng += km_east / denom
    return {"lat": round(lat, 6), "lng": round(lng, 6)}


class Scenario:
    def __init__(self, name: str, focus: str, query: Dict[str, Any], candidates: List[Dict[str, Any]], labels: Dict[str, int]):
        self.name = name
        self.focus = focus
        self.query = query
        self.candidates = candidates
        self.labels = labels


def _precision_at_k(matches: List[Dict[str, Any]], labels: Dict[str, int], k: int) -> float:
    if not matches:
        return 0.0
    selected = matches[: max(1, min(k, len(matches)))]
    relevant = sum(labels.get(m.get("other_profile_id"), 0) for m in selected)
    return relevant / len(selected)


def _build_scenarios(profiles: List[Dict[str, Any]]) -> List[Scenario]:
    distractors = [deepcopy(p) for p in profiles[:50]]
    scenarios: List[Scenario] = []

    for idx, base in enumerate(profiles[:25]):
        query = deepcopy(base)
        base_pool = [c for c in distractors if c.get("id") != base.get("id")]

        if base.get("role"):
            same_role = _make_variant(base, f"role_match_{idx}")
            other_role = "professional" if base["role"] != "professional" else "student"
            mismatch = _make_variant(base, f"role_conflict_{idx}", role=other_role)
            scenarios.append(
                Scenario(
                    name=f"role_edge_{idx}",
                    focus="role",
                    query=query,
                    candidates=base_pool + [same_role, mismatch],
                    labels={same_role["id"]: 1, mismatch["id"]: 0},
                )
            )

        budget = base.get("budget_pkr") or base.get("budget")
        if isinstance(budget, (int, float)) and budget:
            aligned = _make_variant(base, f"budget_close_{idx}", budget_pkr=int(budget * 1.05))
            clash = _make_variant(base, f"budget_far_{idx}", budget_pkr=int(budget * 1.8))
            scenarios.append(
                Scenario(
                    name=f"budget_edge_{idx}",
                    focus="budget",
                    query=query,
                    candidates=base_pool + [aligned, clash],
                    labels={aligned["id"]: 1, clash["id"]: 0},
                )
            )

        anchor = base.get("anchor_location")
        if isinstance(anchor, dict) and {"lat", "lng"}.issubset(anchor.keys()):
            near = _make_variant(base, f"anchor_near_{idx}", anchor_location=_shift_anchor(anchor, km_north=1))
            far = _make_variant(base, f"anchor_far_{idx}", anchor_location=_shift_anchor(anchor, km_north=80))
            scenarios.append(
                Scenario(
                    name=f"anchor_edge_{idx}",
                    focus="anchor",
                    query=query,
                    candidates=base_pool + [near, far],
                    labels={near["id"]: 1, far["id"]: 0},
                )
            )

    return scenarios


def _evaluate(
    scenarios: Iterable[Scenario],
    listings: List[Dict[str, Any]],
    match_cfg: MatchScoreConfig,
    retrieval_cfg: RetrievalConfig,
    top_k: int,
) -> Dict[str, Any]:
    scenario_results = []
    precisions_1: List[float] = []
    precisions_3: List[float] = []

    for scenario in scenarios:
        result = run_pipeline(
            scenario.query,
            scenario.candidates,
            listings,
            mode="degraded",
            top_k=top_k,
            match_config=match_cfg,
            retrieval_config=retrieval_cfg,
        )

        matches = result.get("matches", [])
        prec1 = _precision_at_k(matches, scenario.labels, k=1)
        prec3 = _precision_at_k(matches, scenario.labels, k=min(3, top_k))
        precisions_1.append(prec1)
        precisions_3.append(prec3)

        scenario_results.append(
            {
                "scenario": scenario.name,
                "focus": scenario.focus,
                "precision@1": prec1,
                "precision@3": prec3,
                "labels": scenario.labels,
                "matches": [
                    {
                        "profile_id": m.get("other_profile_id"),
                        "score": m.get("score"),
                        "subscores": m.get("subscores"),
                        "flags": m.get("conflicts"),
                        "reasons": m.get("reasons"),
                    }
                    for m in matches
                ],
                "trace": result.get("trace"),
            }
        )

    summary = {
        "avg_precision@1": mean(precisions_1) if precisions_1 else 0.0,
        "avg_precision@3": mean(precisions_3) if precisions_3 else 0.0,
    }

    return {"scenarios": scenario_results, "summary": summary}


def _sweep_configs(top_k: int, scenarios: List[Scenario], listings: List[Dict[str, Any]]):
    weight_variants = [
        {},
        {"anchor": 8},
        {"anchor": 12},
        {"budget": 22, "anchor": 12},
    ]
    anchor_buckets_variants = [
        None,
        ((2.0, 1.0), (6.0, 0.7), (25.0, 0.4)),
        ((3.0, 1.0), (10.0, 0.6), (30.0, 0.3)),
    ]
    retrieval_variants = [
        {},
        {"budget_tol": 0.35, "anchor_dist_km": 15.0},
        {"budget_tol": 0.30, "anchor_dist_km": 12.0, "anchor_bonus_steps": ((4.0, 1.0), (15.0, 0.4))},
        {"budget_tol": 0.45, "anchor_dist_km": 25.0, "anchor_bonus_steps": ((6.0, 0.8), (18.0, 0.5))},
    ]

    best_payload = None
    best_score = -1.0
    all_runs = []

    base_retrieval = RetrievalConfig()

    for weight_delta, buckets, retr_delta in product(weight_variants, anchor_buckets_variants, retrieval_variants):
        match_cfg = MatchScoreConfig()
        match_cfg.weights.update(weight_delta)
        if buckets:
            match_cfg.anchor_buckets = tuple(buckets)

        retrieval_cfg = RetrievalConfig(
            budget_tol=retr_delta.get("budget_tol", base_retrieval.budget_tol),
            city_boost=retr_delta.get("city_boost", base_retrieval.city_boost),
            anchor_dist_km=retr_delta.get("anchor_dist_km", base_retrieval.anchor_dist_km),
            anchor_bonus_steps=tuple(retr_delta.get("anchor_bonus_steps", base_retrieval.anchor_bonus_steps)),
        )

        evaluation = _evaluate(scenarios, listings, match_cfg, retrieval_cfg, top_k)
        avg_p3 = evaluation["summary"].get("avg_precision@3", 0.0)

        payload = {
            "match_config": asdict(match_cfg),
            "retrieval_config": asdict(retrieval_cfg),
            "metrics": evaluation["summary"],
        }

        all_runs.append(payload)

        if avg_p3 > best_score:
            best_score = avg_p3
            best_payload = {
                **payload,
                "details": evaluation["scenarios"],
            }

    return best_payload, all_runs


def main():
    parser = argparse.ArgumentParser(description="Evaluate and tune the rule-based matcher.")
    parser.add_argument("--top-k", type=int, default=5, help="How many matches to surface during evaluation.")
    parser.add_argument("--no-sweep", action="store_true", help="Skip config sweep and only evaluate defaults.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="Where to persist reports.")
    args = parser.parse_args()

    profiles = _load_json(DATA_DIR / "profiles_extended.json")
    listings = _load_json(DATA_DIR / "listings_extended.json")
    scenarios = _build_scenarios(profiles)

    _ensure_output_dir(args.output_dir)

    if args.no_sweep:
        match_cfg = MatchScoreConfig()
        retrieval_cfg = RetrievalConfig()
        evaluation = _evaluate(scenarios, listings, match_cfg, retrieval_cfg, args.top_k)
        report_path = args.output_dir / "profile_harness_report.json"
        with report_path.open("w") as f:
            json.dump(
                {
                    "match_config": asdict(match_cfg),
                    "retrieval_config": asdict(retrieval_cfg),
                    "metrics": evaluation["summary"],
                    "details": evaluation["scenarios"],
                },
                f,
                indent=2,
            )
        print(f"Wrote evaluation report to {report_path}")
    else:
        best_payload, all_runs = _sweep_configs(args.top_k, scenarios, listings)
        if not best_payload:
            raise RuntimeError("No evaluation runs executed — check fixtures.")

        best_path = args.output_dir / "profile_harness_best_config.json"
        with best_path.open("w") as f:
            json.dump(best_payload, f, indent=2)

        grid_path = args.output_dir / "profile_harness_grid.json"
        with grid_path.open("w") as f:
            json.dump(all_runs, f, indent=2)

        print(f"Best average precision@3: {best_payload['metrics']['avg_precision@3']:.3f}")
        print(f"Saved best configuration to {best_path}")
        print(f"Saved grid search metrics to {grid_path}")


if __name__ == "__main__":
    main()

