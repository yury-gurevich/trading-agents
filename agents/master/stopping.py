"""Master's stop — end the session, close the graph, write the closing line.

Agent: master
Role: once the EHLO server has stopped, wait for a fleet check in hand, record
      the end of the boot session, close the graph connection and return the
      process exit code.
External I/O: graph database via the injected GraphStore; writes to stderr.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from kernel.stop import closing_steps, finish

if TYPE_CHECKING:
    from collections.abc import Callable
    from threading import Thread

    from agents.master.agent import MasterAgent
    from agents.master.settings import MasterSettings
    from kernel import GraphStore
    from kernel.graph import Node
    from kernel.stop import Step, StopSignal


def end_session(graph: GraphStore, session_id: str, *, reason: str) -> Node:
    """Record on the boot session that master stopped when asked (MST-OUT-03)."""
    return graph.merge_node(
        "Session",
        session_id,
        {"ended_at": datetime.now(UTC).isoformat(), "shutdown_reason": reason},
    )


def shut_down(
    agent: MasterAgent,
    graph: GraphStore,
    stop: StopSignal,
    *,
    activations_left: int,
    preflight: Thread,
    settings: MasterSettings,
    write: Callable[[str], None] | None = None,
) -> int:
    """Finish a stopped master; return 0 only when nothing was left and nothing failed.

    The session end is written even when an activation was left, because master
    did stop when asked; the exit code and the closing line carry what was left.
    """
    unfinished: list[str] = []
    if activations_left:
        unfinished.append(f"{activations_left} activation(s)")
    preflight.join(stop.seconds_left(settings.stop_drain_seconds))
    if preflight.is_alive():
        unfinished.append("the fleet check")
    steps: list[Step] = []
    session_id = agent.session_id
    if session_id is not None:
        steps.append(
            ("session", lambda: end_session(graph, session_id, reason=stop.reason))
        )
    steps.extend(closing_steps(graph=graph))
    clean = finish(
        stop, agent="master", steps=steps, unfinished=unfinished, write=write
    )
    return 0 if clean else 1
