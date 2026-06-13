"""Predictor registry surface tests.

Agent: surfaces
Role: verify cli predictors shows promotion status and cli approve resolves a flag.
External I/O: none.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from kernel import FakeLLMClient, InMemoryGraphStore
from surfaces.cli import main
from surfaces.context import build_test_context
from surfaces.queries.predictors import all_predictors

if TYPE_CHECKING:
    import pytest

_PID = "predictor:exit-timing:exit_trigger:v1"


def _approve_llm() -> FakeLLMClient:
    return FakeLLMClient(
        {
            "approve": json.dumps(
                {"outcome": "intent", "family": "approve", "parameters": {}}
            )
        }
    )


def _seed_predictor(graph: InMemoryGraphStore) -> None:
    graph.merge_node(
        "Predictor",
        _PID,
        {
            "purpose": "exit-timing",
            "target": "exit_trigger",
            "strategy": "majority_class",
            "accuracy": 0.90,
            "sample_size": 10,
            "advisory": True,
        },
    )


def _seed_flag(graph: InMemoryGraphStore) -> None:
    graph.merge_node(
        "Flag",
        f"flag:predictor:{_PID}:info",
        {"subject_ref": f"predictor:{_PID}", "severity": "info"},
    )


def test_view_status_advisory() -> None:
    graph = InMemoryGraphStore()
    _seed_predictor(graph)

    assert all_predictors(graph)[0].promotion_status == "advisory"


def test_view_status_pending_then_load_bearing() -> None:
    graph = InMemoryGraphStore()
    _seed_predictor(graph)
    _seed_flag(graph)
    assert all_predictors(graph)[0].promotion_status == "pending_approval"

    graph.merge_node("PredictorPromotion", f"promotion:{_PID}", {})
    assert all_predictors(graph)[0].promotion_status == "load_bearing"


def test_cli_predictors_shows_status(capsys: pytest.CaptureFixture[str]) -> None:
    graph = InMemoryGraphStore()
    _seed_predictor(graph)
    main(["predictors"], context=build_test_context(graph=graph))

    assert "[advisory]" in capsys.readouterr().out


def test_cli_approve_resolves_predictor_flag(
    capsys: pytest.CaptureFixture[str],
) -> None:
    graph = InMemoryGraphStore()
    ctx = build_test_context(graph=graph, llm=_approve_llm())
    _seed_predictor(graph)
    _seed_flag(graph)

    main(["approve", f"predictor:{_PID}"], context=ctx)
    capsys.readouterr()

    assert (
        graph.get_node("FlagResolution", f"resolution:flag:predictor:{_PID}:info")
        is not None
    )
    assert all_predictors(graph)[0].promotion_status == "advisory"
