"""Deliberation challenger-veto stage tests (DL-31 Part B).

Agent: orchestration
Role: prove the opt-in veto runs between PM and execution, that a non-uphold verdict
      SUBTRACTS an order (execution honours it, EXEC-NEV-01) while the judge can never
      add one, that it is fail-open on an LLM outage, and that omitting the LLM leaves
      the deterministic cascade unchanged.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.broker import PaperBroker
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from kernel import FakeLLMClient, InMemoryGraphStore, InProcessBus
from orchestration import veto
from orchestration.local_pipeline import cascade_once
from orchestration.start import place_run_request
from orchestration.tests.helpers import node_count, source

_OVERTURN = '{"ruling": "overturn", "rationale": "too concentrated"}'
_UPHOLD = '{"ruling": "uphold", "rationale": "clears the guardrails"}'


class _RaisingLLM:
    """An LLM that always errors — to prove the veto fails OPEN (never blocks)."""

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        raise RuntimeError("LLM unavailable")


def _provider(graph: InMemoryGraphStore) -> ProviderAgent:
    return ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source(),
        settings=ProviderSettings(max_staleness_days=7),
    )


def _run(graph: InMemoryGraphStore, llm: object | None) -> None:
    place_run_request(graph, run_id="veto", tickers=("AAPL", "MSFT"))
    cascade_once(
        graph,
        provider_agent=_provider(graph),
        broker=PaperBroker(),
        deliberation_llm=llm,  # type: ignore[arg-type]
    )


def _submitted(graph: InMemoryGraphStore) -> int:
    return sum(int(n.props["submitted"]) for n in graph.list_nodes("ExecutionRun"))


def test_uphold_all_submits_normally_and_records_no_vetoes() -> None:
    """A clean review vetoes nothing — the baseline trade count flows through."""
    graph = InMemoryGraphStore()
    _run(graph, FakeLLMClient({"review": _UPHOLD}))
    (delib,) = graph.list_nodes("DeliberationRun")
    assert not delib.props["vetoed_tickers"]
    assert _submitted(graph) >= 1  # orders still executed


def test_overturn_subtracts_every_order_execution_honours_it() -> None:
    """FORE-NEV-02 analogue / EXEC-NEV-01: a non-uphold verdict drops the order; the
    judge only subtracts — nothing is submitted that the PM did not approve."""
    graph = InMemoryGraphStore()
    _run(graph, FakeLLMClient({"review": _OVERTURN}))
    (delib,) = graph.list_nodes("DeliberationRun")
    assert delib.props["vetoed_tickers"]  # at least one order was vetoed
    assert _submitted(graph) == 0  # execution honoured the veto


def test_veto_is_fail_open_on_llm_outage() -> None:
    """An LLM error upholds (never blocks trading) — the trade still flows."""
    graph = InMemoryGraphStore()
    _run(graph, _RaisingLLM())
    (delib,) = graph.list_nodes("DeliberationRun")
    assert not delib.props["vetoed_tickers"]
    assert _submitted(graph) >= 1


def test_no_llm_means_no_veto_stage() -> None:
    """Omitting the LLM leaves the cascade unchanged — no DeliberationRun."""
    graph = InMemoryGraphStore()
    _run(graph, None)
    assert node_count(graph, "DeliberationRun") == 0
    assert _submitted(graph) >= 1


def test_find_pending_gates_on_the_deliberation_marker() -> None:
    graph = InMemoryGraphStore()
    pm_run = graph.merge_node("PMRun", "pm-1", {})
    assert [n.key for n in veto.find_pending(graph)] == ["pm-1"]
    marker = graph.merge_node(veto.DELIBERATION_RUN_LABEL, "pm-1", {})
    graph.add_edge(pm_run, marker, veto.DELIBERATED_EDGE)
    assert veto.find_pending(graph) == []
