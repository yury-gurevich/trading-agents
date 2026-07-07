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
    Postgres and Neo4j paths are only taken when env vars are explicitly set
    (e.g. by _apply_config injecting them from the master's ACTIVATE payload).
    During the dual-backend migration period, POSTGRES_DSN wins over NEO4J_URI.
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
    uri = os.environ.get("NEO4J_URI", "")
    if not uri:
        from kernel.graph_memory import InMemoryGraphStore

        return InMemoryGraphStore()
    from kernel.graph_neo4j import Neo4jGraphStore  # pragma: no cover

    return Neo4jGraphStore()  # pragma: no cover
