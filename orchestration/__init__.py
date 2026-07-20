"""Orchestration — the dispatcher and distributed-bus app.

Routes messages and triggers runs; makes no trading decisions. Sits above agents,
contracts, and kernel in the dependency graph.
"""

from __future__ import annotations

from typing import Any

__all__ = ["Dispatcher", "RunResult", "RunScheduler", "RunTrigger"]


def __getattr__(name: str) -> Any:  # noqa: ANN401 - module export hook.
    """Resolve package convenience exports lazily."""
    if name == "Dispatcher":
        from orchestration.dispatcher import Dispatcher

        return Dispatcher
    if name == "RunScheduler":
        from orchestration.scheduler import RunScheduler

        return RunScheduler
    if name in {"RunResult", "RunTrigger"}:
        from orchestration.trigger import RunResult, RunTrigger

        return {"RunResult": RunResult, "RunTrigger": RunTrigger}[name]
    raise AttributeError(name)  # pragma: no cover
