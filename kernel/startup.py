"""Startup connectivity guard — fail safe, never crash-loop.

Agent: kernel
Role: probe the graph once at startup and, on persistent failure, log and HALT
      (block) instead of raising. A raising startup crashes the process; the
      container manager then restarts it in a tight loop, and every restart
      re-attempts the Neo4j login — an auth "frenzy" that locked the Aura account
      (observed 2026-07, forced an instance recreate). Bounded retries absorb a
      transient blip; then we stop trying. Correct credentials are the real fix
      (deploy wiring); this guard makes a *mis*configuration fail safe, not fatal.
External I/O: one read against the graph store (the reachability probe).
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from kernel.graph import GraphStore

_log = logging.getLogger("startup")
_PROBE_LABEL = "_Reachability"
_PROBE_KEY = "_probe"


def graph_reachable(graph: GraphStore) -> bool:
    """Return True if the graph answers a cheap read; False (logged) on any error."""
    try:
        graph.get_node(_PROBE_LABEL, _PROBE_KEY)
    except Exception as exc:  # any failure to reach the graph means "not reachable".
        _log.error("graph unreachable: %s: %s", type(exc).__name__, exc)
        return False
    return True


def ensure_reachable_or_halt(
    graph: GraphStore,
    *,
    attempts: int = 3,
    backoff_seconds: float = 5.0,
    sleeper: Callable[[float], None] = time.sleep,
    halt: Callable[[], None] | None = None,
) -> None:
    """Probe the graph; return on success. On persistent failure, HALT — never raise.

    Raising here crashes the process, which the container manager restarts in a tight
    loop; each restart re-attempts the login, hammering Neo4j auth until the account
    locks. So on persistent failure we log a fatal line and block. ``attempts`` and
    ``backoff_seconds`` absorb a transient blip without ever becoming a frenzy.
    """
    for attempt in range(1, attempts + 1):
        if graph_reachable(graph):
            return
        if attempt < attempts:
            sleeper(backoff_seconds)
    _log.error(
        "FATAL: graph unreachable after %d attempt(s) — halting to avoid an "
        "auth-retry storm that can lock the account. Check POSTGRES_DSN or "
        "NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD / NEO4J_DATABASE. Not restarting.",
        attempts,
    )
    (halt or _block_forever)()


def _block_forever() -> None:  # pragma: no cover - blocks; a test injects its own halt.
    while True:
        time.sleep(3600)
