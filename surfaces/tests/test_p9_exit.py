"""P9 exit criterion: request AND fault metrics flow to Prometheus.

Agent: surfaces
Role: prove the metered pipeline emits request and fault metric families.
External I/O: none.
"""

from __future__ import annotations

from typing import cast

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
