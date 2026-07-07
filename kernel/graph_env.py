"""Graph store factory from process environment.

Agent: kernel
Role: build a GraphStore from os.environ so agent entrypoints stay thin.
External I/O: none.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel.graph import GraphStore


def build_graph_from_env() -> GraphStore:
    """Return the configured live GraphStore, else InMemoryGraphStore.

    The in-memory store is the correct default for local dev and CI; the
    PostgreSQL path is taken only when POSTGRES_DSN is explicitly set (e.g. by
    _apply_config injecting it from the master's ACTIVATE payload).
    """
    postgres_dsn = os.environ.get("POSTGRES_DSN", "")
    if postgres_dsn:
        from kernel.graph_postgres import PostgresGraphStore  # pragma: no cover
        from kernel.graph_postgres_config import (  # pragma: no cover
            PostgresGraphSettings,
        )

        return PostgresGraphStore(
            PostgresGraphSettings(postgres_dsn=postgres_dsn)
        )  # pragma: no cover
    if os.environ.get("NEO4J_URI", ""):
        raise RuntimeError(
            "NEO4J_URI is no longer a runtime backend after ADR-0014. "
            "Set POSTGRES_DSN for the PostgreSQL system of record, or unset "
            "NEO4J_URI for local in-memory development."
        )
    from kernel.graph_memory import InMemoryGraphStore

    return InMemoryGraphStore()
