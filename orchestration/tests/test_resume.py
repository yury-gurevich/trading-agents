"""Resume-from-stage supersession and graph-pull continuation tests.

Agent: orchestration
Role: prove linked upstream lineage, downstream re-derivation, and immutability.
External I/O: none; the graph and broker are in-memory fakes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from agents.analyst import poll as analyst_poll
from agents.execution import poll as execution_poll
from agents.execution.broker import PaperBroker
from agents.monitor import poll as monitor_poll
from agents.portfolio_manager import poll as pm_poll
from agents.provider import ProviderAgent
from agents.provider import poll as provider_poll
from agents.provider.settings import ProviderSettings
from kernel import InMemoryGraphStore, InProcessBus
from orchestration.batch_trace import walk_chain
from orchestration.local_pipeline import cascade_once
from orchestration.resume import resume_run
from orchestration.start import place_run_request
from orchestration.tests.helpers import source

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Any

    from kernel import Node


def _complete(run_id: str = "original") -> tuple[InMemoryGraphStore, ProviderAgent]:
    graph = InMemoryGraphStore()
    agent = ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source(),
        settings=ProviderSettings(max_staleness_days=7),
    )
    place_run_request(graph, run_id=run_id, tickers=("AAPL", "MSFT"))
    cascade_once(graph, provider_agent=agent, broker=PaperBroker())
    return graph, agent


@pytest.mark.parametrize(
    ("stage", "labels", "pending"),
    [
        ("provider", (), provider_poll.find_pending),
        ("analyst", ("MarketData", "ScanRun"), analyst_poll.find_pending),
        (
            "pm",
            ("MarketData", "ScanRun", "AnalystRun"),
            pm_poll.find_pending,
        ),
        (
            "monitor",
            (
                "MarketData",
                "ScanRun",
                "AnalystRun",
                "PMRun",
                "ExecutionRun",
            ),
            monitor_poll.find_pending,
        ),
    ],
)
def test_stage_matrix_links_upstream_and_leaves_selected_stage_pending(
    stage: str, labels: tuple[str, ...], pending: object
) -> None:
    graph, _agent = _complete()
    original = walk_chain(graph, "original")
    original_props = {label: dict(node.props) for label, node in original.items()}

    result = resume_run(graph, source_run_id="original", resume_from=stage)

    child = walk_chain(graph, result.child_run_id)
    assert tuple(child)[1:] == labels
    pending_nodes = pending(graph)  # type: ignore[operator]
    assert any(result.child_run_id in node.key for node in pending_nodes)
    assert {
        label: dict(node.props) for label, node in original.items()
    } == original_props
    child_request = child["RunRequest"]
    resumed = tuple(
        graph.descendants(child_request, max_depth=1, edge_types={"RESUMES"})
    )
    assert resumed == (original["RunRequest"],)


def test_monitor_resume_reaches_seven_of_seven_without_execution() -> None:
    graph, agent = _complete()
    broker = PaperBroker()
    result = resume_run(graph, source_run_id="original", resume_from="monitor")
    linked_execution = walk_chain(graph, result.child_run_id)["ExecutionRun"]

    stages = cascade_once(graph, provider_agent=agent, broker=broker)

    assert set(walk_chain(graph, result.child_run_id)) == {
        "RunRequest",
        "MarketData",
        "ScanRun",
        "AnalystRun",
        "PMRun",
        "ExecutionRun",
        "MonitorRun",
        "Snapshot",
    }
    assert next(row for row in stages if row.name == "execution").processed == 0
    assert graph.get_node("ExecutionRun", linked_execution.key) == linked_execution
    assert broker.order_count == 0


def test_execution_resume_mints_new_order_identity() -> None:
    graph, _agent = _complete()
    result = resume_run(graph, source_run_id="original", resume_from="execution")
    pm_run = walk_chain(graph, result.child_run_id)["PMRun"]
    order_set = pm_run.props["order_intent_set"]
    assert order_set["run_id"] == pm_run.key
    assert pm_run in execution_poll.find_pending(graph)


def test_child_of_child_and_double_resume_are_deterministic() -> None:
    graph, agent = _complete()
    first = resume_run(graph, source_run_id="original", resume_from="monitor")
    cascade_once(graph, provider_agent=agent, broker=PaperBroker())
    same = resume_run(graph, source_run_id="original", resume_from="monitor")
    second = resume_run(graph, source_run_id=first.child_run_id, resume_from="reporter")

    assert same.child_run_id == first.child_run_id
    assert same.created is False
    assert second.child_run_id.startswith(first.child_run_id)
    assert len(graph.list_nodes("RunRequest")) == 3


def test_provider_double_resume_has_no_linked_upstream() -> None:
    graph, _agent = _complete()
    first = resume_run(graph, source_run_id="original", resume_from="provider")
    replay = resume_run(graph, source_run_id="original", resume_from="provider")
    assert first.linked == replay.linked == ()


def test_resume_tolerates_missing_optional_regime_link() -> None:
    graph, _agent = _complete()
    market = walk_chain(graph, "original")["MarketData"]
    graph._nodes.pop(("RegimeContext", f"regime-context:{market.props['run_id']}"))
    result = resume_run(graph, source_run_id="original", resume_from="analyst")
    assert all(not ref.startswith("RegimeContext:") for ref in result.linked)


def test_missing_source_stage_and_invalid_stage_are_refused() -> None:
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="partial", tickers=("AAPL",))
    with pytest.raises(ValueError, match="upstream MarketData is missing"):
        resume_run(graph, source_run_id="partial", resume_from="analyst")
    with pytest.raises(ValueError, match="invalid resume stage"):
        resume_run(graph, source_run_id="partial", resume_from="unknown")
    with pytest.raises(ValueError, match="unknown source run"):
        resume_run(graph, source_run_id="missing", resume_from="provider")


class _PostgresSemanticsGraph(InMemoryGraphStore):
    """Track attempts to merge existing nodes like append-only PostgreSQL."""

    def __init__(self) -> None:
        super().__init__()
        self.existing_merges: list[tuple[str, str]] = []

    def merge_node(
        self,
        label: str,
        key: str,
        props: Mapping[str, Any],
        *,
        schema_version: int = 1,
    ) -> Node:
        if self.get_node(label, key) is not None:
            self.existing_merges.append((label, key))
        return super().merge_node(label, key, props, schema_version=schema_version)


def test_postgres_semantics_never_overwrite_or_delete_original_artifacts() -> None:
    base, _agent = _complete()
    graph = _PostgresSemanticsGraph()
    graph._nodes = dict(base._nodes)
    graph._edges = list(base._edges)
    before = dict(graph._nodes)

    resume_run(graph, source_run_id="original", resume_from="monitor")

    assert graph.existing_merges == []
    assert all(graph._nodes[key] == node for key, node in before.items())
    assert not hasattr(graph, "delete_node")
