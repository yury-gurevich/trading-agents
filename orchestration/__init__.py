"""Orchestration — the dispatcher and distributed-bus app.

Routes messages and triggers runs; makes no trading decisions. Sits above agents,
contracts, and kernel in the dependency graph.
"""

from orchestration.dispatcher import Dispatcher
from orchestration.trigger import RunResult, RunTrigger

__all__ = ["Dispatcher", "RunResult", "RunTrigger"]
