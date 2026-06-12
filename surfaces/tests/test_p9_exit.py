"""P9 exit criterion: request AND fault metrics flow to Prometheus.

Agent: surfaces
Role: prove the metered pipeline emits request and fault metric families.
External I/O: none.
"""

from __future__ import annotations

from typing import cast

from agents.analyst.tests.helpers import analyze_message, candidate, candidate_set
from agents.execution.broker import PaperBroker
from agents.provider.sources import FakeDataSource
from kernel import (
    AgentMessage,
    FakeLLMClient,
    InMemoryGraphStore,
    InProcessBus,
    PrometheusMetrics,
    fault_from_exception,
)
from surfaces.context import paper_context


def test_p9_exit_metrics_cover_request_and_fault() -> None:
    """P9 exit: request metrics AND fault metrics flow to Prometheus registry."""
    metrics = PrometheusMetrics()
    ctx = paper_context(
        source=FakeDataSource(),
        broker=PaperBroker(),
        graph=InMemoryGraphStore(),
        llm=FakeLLMClient({}),
        metrics=metrics,
    )

    # Drive a successful request — covers request throughput + latency metrics.
    ctx.bus.request(
        AgentMessage(
            sender="test",
            recipient="supervisor",
            message_type="request",
            capability="system_status",
            payload={},
        )
    )

    # Inject a fault — covers fault-rate metrics via MeteredFaultSink.
    fault = fault_from_exception(
        ValueError("probe"),
        agent="test",
        module="surfaces.tests.test_p9_exit",
        severity="warning",
    )
    cast("InProcessBus", ctx.bus).sink.submit(fault)

    text = metrics.exposition().decode("utf-8")
    assert "trading_agents_kernel_requests_total" in text
    assert "trading_agents_kernel_request_latency_seconds" in text
    assert "trading_agents_kernel_faults_total" in text


def test_p9_exit_agent_internal_fault_is_metered() -> None:
    """P9 exit: a fault raised inside an agent's own boundary reaches the meter."""
    metrics = PrometheusMetrics()
    # fail_ohlcv degrades provider data, so the analyst's analyze handler hits its
    # own fault_boundary(reraise=False) — an agent-internal fault that historically
    # bypassed the bus meter. The request itself still returns normally (no bus error).
    ctx = paper_context(
        source=FakeDataSource(fail_ohlcv=True),
        broker=PaperBroker(),
        graph=InMemoryGraphStore(),
        llm=FakeLLMClient({}),
        metrics=metrics,
    )

    ctx.bus.request(analyze_message(candidate_set(candidate())))

    text = metrics.exposition().decode("utf-8")
    assert "trading_agents_kernel_faults_total{" in text
    assert 'source_agent="analyst"' in text
