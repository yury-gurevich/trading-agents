"""Celery bus settings and task payload shapes.

Agent: kernel
Role: keep Celery infrastructure configuration separate from dispatch mechanics.
External I/O: none.
"""

from __future__ import annotations

from typing import Any, TypedDict

from kernel.config import AgentSettings, tunable


class CeleryBusSettings(AgentSettings):
    """Infrastructure settings for the Celery message bus."""

    celery_broker_url: str = tunable(
        "memory://", why="Default broker keeps local tests infra-free in eager mode."
    )
    celery_result_backend: str = tunable(
        "cache+memory://",
        why="In-memory result backend is enough for eager tests; override for Redis.",
    )
    celery_task_always_eager: bool = tunable(
        True,
        why="Default to synchronous local dispatch so the unit gate needs no broker.",
    )
    celery_task_eager_propagates: bool = tunable(
        False,
        why="Let the bus convert task faults into error envelopes like InProcessBus.",
    )
    celery_request_timeout_seconds: float = tunable(
        30.0,
        why="Bound distributed waits while leaving room for local worker startup lag.",
        ge=1.0,
        le=300.0,
        unit="seconds",
    )


class TaskError(TypedDict):
    """Serialized task error payload."""

    error_type: str
    message: str


class TaskResult(TypedDict, total=False):
    """Serialized task result payload."""

    ok: dict[str, Any]
    error: TaskError
