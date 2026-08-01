"""Vocabulary resolution from the process environment.

Agent: kernel
Role: cover how build_graph_from_env resolves a declared vocabulary — base64
      content first, file path second, unguarded when neither is set.
External I/O: none (tmp_path only).

Base64 exists because none of the 15 images copies orchestration/packs, so
GRAPH_VOCABULARY_PATH can only ever resolve in local dev (S144 / DL-68). It is
the same delivery shape the master uses for grants and the secret map.
"""

from __future__ import annotations

import base64
import json

import pytest

from kernel import InMemoryGraphStore
from kernel.graph_env import (
    GRAPH_VOCABULARY_B64_ENV,
    GRAPH_VOCABULARY_PATH_ENV,
    build_graph_from_env,
)
from kernel.graph_guarded import GuardedGraphStore
from kernel.graph_vocabulary import VocabularyError

_DECLARATION = {
    "labels": ["Run", "Item"],
    "edge_types": ["MADE"],
    "edge_signatures": [["Item", "MADE", "Run"]],
    "owners": {"scanner": ["Item"]},
}


def _encoded(declaration: object = _DECLARATION) -> str:
    return base64.b64encode(json.dumps(declaration).encode()).decode()


def _bare_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear every variable build_graph_from_env consults."""
    for name in (
        GRAPH_VOCABULARY_B64_ENV,
        GRAPH_VOCABULARY_PATH_ENV,
        "POSTGRES_DSN",
        "NEO4J_URI",
    ):
        monkeypatch.delenv(name, raising=False)


def test_factory_is_unguarded_when_no_vocabulary_is_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _bare_env(monkeypatch)
    assert isinstance(build_graph_from_env(), InMemoryGraphStore)


def test_factory_guards_when_a_vocabulary_path_is_configured(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    path = tmp_path / "vocab.json"  # type: ignore[operator]
    path.write_text(json.dumps(_DECLARATION), encoding="utf-8")
    _bare_env(monkeypatch)
    monkeypatch.setenv(GRAPH_VOCABULARY_PATH_ENV, str(path))

    graph = build_graph_from_env()

    assert isinstance(graph, GuardedGraphStore)
    with pytest.raises(VocabularyError):
        graph.merge_node("Postion", "a", {})


def test_factory_guards_from_base64_content_without_any_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The deployable path: no file exists anywhere in an agent image."""
    _bare_env(monkeypatch)
    monkeypatch.setenv(GRAPH_VOCABULARY_B64_ENV, _encoded())

    graph = build_graph_from_env()

    assert isinstance(graph, GuardedGraphStore)
    with pytest.raises(VocabularyError):
        graph.merge_node("Postion", "a", {})


def test_base64_content_wins_over_a_configured_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    path = tmp_path / "vocab.json"  # type: ignore[operator]
    path.write_text(json.dumps({"labels": ["OnlyFromFile"]}), encoding="utf-8")
    _bare_env(monkeypatch)
    monkeypatch.setenv(GRAPH_VOCABULARY_PATH_ENV, str(path))
    monkeypatch.setenv(GRAPH_VOCABULARY_B64_ENV, _encoded())

    graph = build_graph_from_env()

    graph.merge_node("Item", "a", {})
    with pytest.raises(VocabularyError):
        graph.merge_node("OnlyFromFile", "a", {})


def test_a_vocabulary_that_is_not_an_object_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _bare_env(monkeypatch)
    monkeypatch.setenv(GRAPH_VOCABULARY_B64_ENV, _encoded(["not", "an", "object"]))
    with pytest.raises(ValueError, match="must be a JSON object"):
        build_graph_from_env()
