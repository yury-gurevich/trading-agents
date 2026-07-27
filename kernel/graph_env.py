"""Graph store factory from process environment.

Agent: kernel
Role: build a GraphStore from os.environ so agent entrypoints stay thin.
External I/O: reads the vocabulary declaration file when one is configured.
"""

from __future__ import annotations

import base64
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel.graph import GraphStore

GRAPH_VOCABULARY_B64_ENV = "GRAPH_VOCABULARY_B64"
"""Base64 vocabulary content — the deployable form; wins over the path."""

GRAPH_VOCABULARY_PATH_ENV = "GRAPH_VOCABULARY_PATH"
"""Path to the pack's vocabulary declaration; the local-dev fallback."""


def _parse(text: str) -> Mapping[str, object]:
    """Parse a vocabulary declaration, rejecting anything that is not an object."""
    data: object = json.loads(text)
    if not isinstance(data, Mapping):
        raise ValueError("graph vocabulary must be a JSON object")
    return data


def _declaration() -> Mapping[str, object] | None:
    """Resolve the vocabulary: base64 env content -> file path -> None.

    Base64 wins so agent images stay pack-agnostic: no image ships
    ``orchestration/packs/``, so a path can only ever work in local dev. This is
    the delivery shape the master already uses for grants and the secret map
    (S86 / DL-12).
    """
    encoded = os.environ.get(GRAPH_VOCABULARY_B64_ENV, "").strip()
    if encoded:
        return _parse(base64.b64decode(encoded).decode("utf-8"))
    path = os.environ.get(GRAPH_VOCABULARY_PATH_ENV, "").strip()
    if path:
        return _parse(Path(path).read_text(encoding="utf-8"))
    return None


def _guarded(store: GraphStore, *, writer: str = "") -> GraphStore:
    """Wrap *store* in the declared vocabulary when one is configured.

    The vocabulary is pack data, not substrate (ADR-0012) — kernel only loads
    whatever declaration it is handed and never names a label itself.
    """
    declaration = _declaration()
    if declaration is None:
        return store
    from kernel.graph_guarded import GuardedGraphStore
    from kernel.graph_vocabulary import Vocabulary

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
