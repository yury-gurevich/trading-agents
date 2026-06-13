"""Predictors surface tests.

Agent: surfaces
Role: verify predictor projections and the read-only cli predictors command.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kernel import InMemoryGraphStore
from surfaces.cli import main
from surfaces.context import build_test_context
from surfaces.queries.predictors import all_predictors

if TYPE_CHECKING:
    import pytest


def _seed_predictor(graph: InMemoryGraphStore) -> None:
    graph.merge_node(
        "Predictor",
        "predictor:exit-timing:exit_trigger:v1",
        {
            "purpose": "exit-timing",
            "target": "exit_trigger",
            "strategy": "majority_class",
            "accuracy": 0.75,
            "sample_size": 4,
            "advisory": True,
        },
    )


def test_all_predictors_empty() -> None:
    assert all_predictors(InMemoryGraphStore()) == ()


def test_all_predictors_projects_fields() -> None:
    graph = InMemoryGraphStore()
    _seed_predictor(graph)

    views = all_predictors(graph)

    assert len(views) == 1
    assert views[0].predictor_id == "predictor:exit-timing:exit_trigger:v1"
    assert views[0].strategy == "majority_class"
    assert views[0].accuracy == 0.75
    assert views[0].advisory is True


def test_cli_predictors_empty(capsys: pytest.CaptureFixture[str]) -> None:
    graph = InMemoryGraphStore()
    main(["predictors"], context=build_test_context(graph=graph))

    assert capsys.readouterr().out.strip() == "no predictors trained"


def test_cli_predictors_lists_predictor(capsys: pytest.CaptureFixture[str]) -> None:
    graph = InMemoryGraphStore()
    _seed_predictor(graph)
    main(["predictors"], context=build_test_context(graph=graph))

    out = capsys.readouterr().out
    assert "predictor:exit-timing:exit_trigger:v1" in out
    assert "acc=" in out
