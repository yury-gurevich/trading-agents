"""Trace-run CLI exit tests.

Agent: orchestration
Role: prove the operator trace CLI exits from the same stage total the renderer
      uses in its RESULT line.
External I/O: none.
"""

from __future__ import annotations

import sys

import pytest

from agents.execution.paper_broker import PaperBroker
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from kernel import InMemoryGraphStore, InProcessBus
from orchestration.local_pipeline import cascade_once
from orchestration.start import place_run_request
from orchestration.tests.helpers import source


def test_trace_run_exits_zero_for_complete_trace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """LAW-02: a complete 8-stage trace exits 0."""
    graph = _complete_graph()

    assert _trace_exit_code(monkeypatch, graph, "trace-cli") == 0


def test_trace_run_exits_nonzero_for_incomplete_trace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """LAW-02: an incomplete trace exits non-zero."""
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="partial-cli", tickers=("AAPL",))

    assert _trace_exit_code(monkeypatch, graph, "partial-cli") != 0


def test_trace_run_uses_stage_tuple_total(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """LAW-02: the CLI total follows the trace stage tuple, not a literal."""
    import orchestration.batch_trace as batch_trace

    graph = _complete_graph()
    monkeypatch.setattr(
        batch_trace, "_COMPLETE_KEYS", (*batch_trace._COMPLETE_KEYS, "SyntheticStage")
    )

    assert batch_trace.trace_stage_total() == 9
    assert _trace_exit_code(monkeypatch, graph, "trace-cli") != 0


def _complete_graph() -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    provider = ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source(),
        settings=ProviderSettings(max_staleness_days=7),
    )
    place_run_request(graph, run_id="trace-cli", tickers=("AAPL", "MSFT"))
    list(cascade_once(graph, provider_agent=provider, broker=PaperBroker()))
    return graph


def _trace_exit_code(
    monkeypatch: pytest.MonkeyPatch, graph: InMemoryGraphStore, run_id: str
) -> int:
    from scripts import trace_run

    import kernel.graph_env as graph_env

    monkeypatch.setattr(graph_env, "build_graph_from_env", lambda: graph)
    monkeypatch.setattr(sys, "argv", ["trace_run.py", "--run-id", run_id])
    with pytest.raises(SystemExit) as raised:
        trace_run.main()
    code = raised.value.code
    assert isinstance(code, int)
    return code
