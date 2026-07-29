"""Resume append-only semantics tests.

Agent: orchestration
Role: prove resume placement does not overwrite source artifacts.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agents.execution.paper_broker import PaperBroker
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from kernel import InMemoryGraphStore, InProcessBus
from orchestration.local_pipeline import cascade_once
from orchestration.resume import resume_run
from orchestration.start import place_run_request
from orchestration.tests.helpers import source

if TYPE_CHECKING:
    from collections.abc import Mapping

    from kernel import Node


def test_postgres_semantics_never_overwrite_or_delete_original_artifacts() -> None:
    graph = _complete()
    graph.existing_merges = []
    before = dict(graph._nodes)

    resume_run(graph, source_run_id="original", resume_from="monitor")

    assert graph.existing_merges == []
    assert all(graph._nodes[key] == node for key, node in before.items())
    assert not hasattr(graph, "delete_node")


def _complete() -> _PostgresSemanticsGraph:
    graph = _PostgresSemanticsGraph()
    agent = ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source(),
        settings=ProviderSettings(max_staleness_days=7),
    )
    place_run_request(graph, run_id="original", tickers=("AAPL", "MSFT"))
    cascade_once(graph, provider_agent=agent, broker=PaperBroker())
    return graph


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
