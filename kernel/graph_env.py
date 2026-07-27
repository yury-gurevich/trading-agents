"""Graph store factory from process environment.

Agent: kernel
Role: build a GraphStore from os.environ so agent entrypoints stay thin.
External I/O: reads the vocabulary declaration file when one is configured.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel.graph import GraphStore

GRAPH_VOCABULARY_PATH_ENV = "GRAPH_VOCABULARY_PATH"
"""Path to the pack's vocabulary declaration; unset means no write checking."""


def _guarded(store: GraphStore, *, writer: str = "") -> GraphStore:
    """Wrap *store* in the declared vocabulary when one is configured.

    The vocabulary is pack data, not substrate (ADR-0012) — kernel only loads
    whatever file it is pointed at and never names a label itself.
    """
    path = os.environ.get(GRAPH_VOCABULARY_PATH_ENV, "").strip()
    if not path:
        return store
    from kernel.graph_guarded import GuardedGraphStore
    from kernel.graph_vocabulary import Vocabulary

    declaration = json.loads(Path(path).read_text(encoding="utf-8"))
    return GuardedGraphStore(store, Vocabulary.from_mapping(declaration), writer=writer)


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

        return _guarded(  # pragma: no cover
            PostgresGraphStore(PostgresGraphSettings(postgres_dsn=postgres_dsn))
        )
    if os.environ.get("NEO4J_URI", ""):
        raise RuntimeError(
            "NEO4J_URI is no longer a runtime backend after ADR-0014. "
            "Set POSTGRES_DSN for the PostgreSQL system of record, or unset "
            "NEO4J_URI for local in-memory development."
        )
    from kernel.graph_memory import InMemoryGraphStore

    return _guarded(InMemoryGraphStore())
