"""Celery application wiring for background workers.

This module keeps the Celery instance in a single place so that tasks can
import it without triggering circular imports.  Celery is optional – when the
``CELERY_BROKER_URL`` environment variable is missing the broker falls back to
the in-memory transport which is suitable for unit tests.  Production
deployments should set the broker/backend explicitly (e.g. Redis, Cloud Tasks
via ``celery-cloud-tasks`` or RabbitMQ).
"""

from __future__ import annotations

import os
from celery import Celery


def _default_backend() -> str:
    backend = os.getenv("CELERY_RESULT_BACKEND")
    if backend:
        return backend
    # ``cache+memory://`` keeps things lightweight for local execution and
    # avoids an RPC backend dependency.
    return "cache+memory://"


celery_app = Celery(
    "room_matcher",
    broker=os.getenv("CELERY_BROKER_URL", "memory://"),
    backend=_default_backend(),
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone=os.getenv("CELERY_TIMEZONE", "UTC"),
    enable_utc=True,
)

__all__ = ["celery_app"]

