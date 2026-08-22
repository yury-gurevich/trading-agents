"""Execution deliberation posture tests for S185.

Agent: execution
Role: prove advisory/binding posture is declared, recorded, and buy-only.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from agents.execution.deliberation_posture import apply_deliberation_posture
from agents.execution.paper_broker import PaperBroker
from agents.execution.poll import execute_pm_node
from agents.execution.settings import ExecutionSettings
from agents.execution.tests.helpers import order, order_set
from kernel import InMemoryGraphStore, Node
from kernel.config import describe

if TYPE_CHECKING:
    from contracts.portfolio_manager import OrderIntent, OrderIntentSet


def _seed_pm_run(graph: InMemoryGraphStore, payload: OrderIntentSet) -> Node:
    return graph.merge_node(
        "PMRun",
        payload.run_id,
        {"order_intent_set": payload.model_dump(mode="json")},
    )


def _sell(ticker: str) -> OrderIntent:
    return order(ticker).model_copy(
        update={"action": "sell", "position_ref": f"position:{ticker}"}
    )


def _execute(
    payload: OrderIntentSet,
    *,
    settings: ExecutionSettings | None = None,
) -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    node = _seed_pm_run(graph, payload)
    execute_pm_node(node, graph=graph, broker=PaperBroker(), settings=settings)
    return graph


def _fault_props(graph: InMemoryGraphStore) -> dict[str, object]:
    (fault,) = graph.list_nodes("Fault")
    return dict(fault.props)


def test_advisory_posture_submits_unvetoed_buy_and_records_warning() -> None:
    """EXEC-OUT-09 / EXEC-OBS-04: advisory no-verdict buys submit as warnings."""
    graph = _execute(
        order_set(order("AAPL")),
        settings=ExecutionSettings(deliberation_posture="advisory"),
    )

    (execution,) = graph.list_nodes("ExecutionRun")
    (fill,) = graph.list_nodes("Fill")
    fault = _fault_props(graph)

    assert fill.props["ticker"] == "AAPL"
    assert execution.props["submitted"] == 1
    assert execution.props["deliberation_status"] == "proceeded_unvetoed"
    assert execution.props["deliberation_posture"] == "advisory"
    assert execution.props["deliberation_blocked_count"] == 0
    assert fault["severity"] == "warning"
    assert "posture=advisory" in str(fault["message"])


def test_binding_posture_blocks_unvetoed_buy_and_records_error() -> None:
    """EXEC-NEV-06 / EXEC-OBS-04: binding no-verdict buys do not reach broker."""
    graph = _execute(
        order_set(order("AAPL")),
        settings=ExecutionSettings(deliberation_posture="binding"),
    )

    (execution,) = graph.list_nodes("ExecutionRun")
    fault = _fault_props(graph)

    assert graph.list_nodes("Fill") == ()
    assert execution.props["submitted"] == 0
    assert execution.props["skipped"] == 1
    assert execution.props["deliberation_posture"] == "binding"
    assert execution.props["deliberation_blocked_count"] == 1
    assert fault["severity"] == "error"
    assert "posture=binding" in str(fault["message"])


def test_binding_posture_does_not_block_sell_only_run() -> None:
    """EXEC-NEV-06: exits never wait or drop because of deliberation posture."""
    direct = order_set(_sell("MSFT"))
    filtered = apply_deliberation_posture(
        direct, status="proceeded_unvetoed", posture="binding"
    )
    graph = _execute(
        order_set(_sell("AAPL")),
        settings=ExecutionSettings(deliberation_posture="binding"),
    )

    assert filtered.order_set is direct
    assert filtered.blocked_count == 0
    (execution,) = graph.list_nodes("ExecutionRun")
    (fill,) = graph.list_nodes("Fill")

    assert fill.props["ticker"] == "AAPL"
    assert fill.props["side"] == "sell"
    assert execution.props["submitted"] == 1
    assert execution.props["deliberation_status"] == "not_required"
    assert execution.props["deliberation_posture"] == "binding"
    assert graph.list_nodes("Fault") == ()


def test_arrived_veto_is_honored_identically_under_both_postures() -> None:
    """EXEC-NEV-01 / EXEC-NEV-06: posture never softens an arrived veto."""
    submitted_by_posture: dict[str, tuple[str, ...]] = {}
    for posture in ("advisory", "binding"):
        payload = order_set(order("AAPL"), order("MSFT"))
        graph = InMemoryGraphStore()
        node = _seed_pm_run(graph, payload)
        delib = graph.merge_node(
            "DeliberationRun", payload.run_id, {"vetoed_tickers": ["AAPL"]}
        )
        graph.add_edge(node, delib, "DELIBERATED_BY")

        execute_pm_node(
            node,
            graph=graph,
            broker=PaperBroker(),
            settings=ExecutionSettings(deliberation_posture=posture),
        )

        submitted_by_posture[posture] = tuple(
            str(fill.props["ticker"]) for fill in graph.list_nodes("Fill")
        )

    assert submitted_by_posture == {
        "advisory": ("MSFT",),
        "binding": ("MSFT",),
    }


def test_default_posture_preserves_fail_open_submission_as_advisory() -> None:
    """EXEC-OUT-09 / EXEC-OBS-04: default posture records expected fail-open."""
    payload = order_set(order("AAPL"))
    graph = InMemoryGraphStore()
    node = _seed_pm_run(graph, payload)
    delib = graph.merge_node(
        "DeliberationRun",
        payload.run_id,
        {"failed_open_tickers": ["AAPL"], "vetoed_tickers": []},
    )
    graph.add_edge(node, delib, "DELIBERATED_BY")

    execute_pm_node(node, graph=graph, broker=PaperBroker())

    (execution,) = graph.list_nodes("ExecutionRun")
    (fill,) = graph.list_nodes("Fill")
    fault = _fault_props(graph)

    assert fill.props["ticker"] == "AAPL"
    assert execution.props["deliberation_status"] == "applied_failed_open"
    assert execution.props["deliberation_posture"] == "advisory"
    assert fault["severity"] == "warning"


def test_deliberation_posture_is_mode_selector_not_tunable() -> None:
    """EXEC-OUT-09: posture validates as policy and is not a tunable dial."""
    docs = {item.name: item for item in describe(ExecutionSettings)}
    posture = docs["deliberation_posture"]

    assert posture.justification == ""
    assert posture.minimum is None
    assert posture.maximum is None
    assert posture.unit is None
    assert ExecutionSettings().deliberation_posture == "advisory"
    with pytest.raises(ValidationError):
        ExecutionSettings.model_validate({"deliberation_posture": "legacy"})
