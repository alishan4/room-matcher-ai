"""Utility to warm Room Matcher AI caches after deployment.

Usage::

    python scripts/warm_cache.py --url https://<service-url>

The script hits the internal warmup endpoint and emits a summary that can be
captured by Cloud Build or run manually by operators.
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict

import requests

DEFAULT_TIMEOUT = 30


def _log(message: str, payload: Dict[str, Any]) -> None:
    print(f"{message}: {json.dumps(payload, default=str)}")


def warm_cache(base_url: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    start = time.time()
    endpoint = base_url.rstrip("/") + "/__internal/warmup"
    response = requests.post(endpoint, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    payload["roundtrip_ms"] = round((time.time() - start) * 1000, 2)
    return payload


def main(argv: Any = None) -> int:
    parser = argparse.ArgumentParser(description="Warm Room Matcher AI caches")
    parser.add_argument("--url", default=os.getenv("ROOM_MATCHER_URL"), help="Base URL for the deployed service")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="HTTP timeout in seconds")
    args = parser.parse_args(argv)

    if not args.url:
        print("error: service URL must be provided via --url or ROOM_MATCHER_URL", file=sys.stderr)
        return 2

    try:
        summary = warm_cache(args.url, timeout=args.timeout)
    except requests.HTTPError as exc:
        print(f"warmup failed with status {exc.response.status_code}: {exc}", file=sys.stderr)
        if exc.response is not None:
            print(exc.response.text, file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - network variability
        print(f"warmup failed: {exc}", file=sys.stderr)
        return 1

    _log("warmup_succeeded", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
