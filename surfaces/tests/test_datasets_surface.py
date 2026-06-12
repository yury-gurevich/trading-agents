"""Datasets surface tests.

Agent: surfaces
Role: verify dataset projections and the read-only cli datasets command.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kernel import InMemoryGraphStore
from surfaces.cli import main
from surfaces.context import build_test_context
from surfaces.queries.datasets import all_datasets

if TYPE_CHECKING:
    import pytest


def _seed_dataset(graph: InMemoryGraphStore) -> None:
    graph.merge_node(
        "Dataset",
        "dataset:exit-timing:v1",
        {
            "purpose": "exit-timing",
            "version": 1,
            "example_count": 10,
            "train_count": 8,
            "validation_count": 1,
            "test_count": 1,
        },
    )


def test_all_datasets_empty() -> None:
    assert all_datasets(InMemoryGraphStore()) == ()


def test_all_datasets_projects_counts() -> None:
    graph = InMemoryGraphStore()
    _seed_dataset(graph)

    views = all_datasets(graph)

    assert len(views) == 1
    assert views[0].dataset_id == "dataset:exit-timing:v1"
    assert views[0].train_count == 8


def test_cli_datasets_empty(capsys: pytest.CaptureFixture[str]) -> None:
    graph = InMemoryGraphStore()
    main(["datasets"], context=build_test_context(graph=graph))

    assert capsys.readouterr().out.strip() == "no datasets built"


def test_cli_datasets_lists_dataset(capsys: pytest.CaptureFixture[str]) -> None:
    graph = InMemoryGraphStore()
    _seed_dataset(graph)
    main(["datasets"], context=build_test_context(graph=graph))

    out = capsys.readouterr().out
    assert "dataset:exit-timing:v1" in out
    assert "(8/1/1)" in out
