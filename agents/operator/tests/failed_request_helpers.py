"""Offline fixtures for failed operator model requests.

Agent: operator
Role: expose independent bus faults, linked audits, and request failures.
External I/O: none; synthetic clients and in-memory graph only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.operator.agent import OperatorAgent
from agents.operator.settings import OperatorSettings
from agents.operator.tests.cutoff_helpers import CompletionStub
from contracts.operator import HumanCommand
from kernel import CollectingFaultSink, InMemoryGraphStore, InProcessBus
from kernel.llm_outage import is_silent_call

if TYPE_CHECKING:
    from kernel import LLMClient, Node


def build_agent(
    llm: LLMClient, graph: InMemoryGraphStore | None = None
) -> tuple[OperatorAgent, InMemoryGraphStore, InProcessBus, CollectingFaultSink]:
    """Bind an operator whose sink is separate from the bus's own sink."""
    graph = graph if graph is not None else InMemoryGraphStore()
    sink = CollectingFaultSink()
    bus = InProcessBus(sink=CollectingFaultSink())
    agent = OperatorAgent(
        bus,
        graph=graph,
        llm=llm,
        sink=sink,
        settings=OperatorSettings(_env_file=None, llm_provider="anthropic"),
    )
    agent.bind()
    return agent, graph, bus, sink


def command(text: str = "What happened in this run?") -> HumanCommand:
    """Make a dashboard question without depending on environment settings."""
    return HumanCommand(text=text, actor="operator", channel="dashboard")


def assert_failed_row(row: Node) -> None:
    """A request that failed has no reply metadata and still reads silent."""
    assert row.props["stop_reason"] == "unknown"
    assert row.props["tokens_out"] == 0
    assert row.props.get("token_source") == "estimated"
    assert is_silent_call(row)


def assert_audit(graph: InMemoryGraphStore, outcome: str) -> None:
    """Assert one audit linked to the one failed call, with no intent."""
    (row,) = graph.list_nodes("LLMCall")
    (audit,) = graph.list_nodes("CommandAudit")
    assert_failed_row(row)
    assert audit.props["outcome"] == outcome
    assert tuple(graph.descendants(audit, max_depth=1, edge_types={"PRODUCED_BY"})) == (
        row,
    )
    assert not graph.list_nodes("Intent")


class RequestFailure(CompletionStub):
    """Fail with the caller's error before any completion metadata exists."""

    def __init__(self, error: Exception) -> None:
        super().__init__()
        self.error = error

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        self.requests.append((system, user, tool_schema))
        raise self.error
