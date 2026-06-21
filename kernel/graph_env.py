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
    """Return Neo4jGraphStore when NEO4J_URI is set, else InMemoryGraphStore.

    The in-memory store is the correct default for local dev and CI; the
    Neo4j path is only taken when the env var is explicitly set (e.g. by
    _apply_config injecting it from the master's ACTIVATE payload).
    """
    uri = os.environ.get("NEO4J_URI", "")
    if not uri:
        from kernel.graph_memory import InMemoryGraphStore

        return InMemoryGraphStore()
    from kernel.graph_neo4j import Neo4jGraphStore  # pragma: no cover

    return Neo4jGraphStore()  # pragma: no cover
