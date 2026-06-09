"""Kernel metrics adapter tests with an infra-free Prometheus registry."""

from __future__ import annotations

from typing import Any

from prometheus_client.parser import text_string_to_metric_families
from pydantic import BaseModel

from kernel import (
    AgentBase,
    AgentContract,
    AgentFault,
    AgentMessage,
    Capability,
    CollectingFaultSink,
    InProcessBus,
    MeteredFaultSink,
    NullMetrics,
    PrometheusMetrics,
)


class EchoRequest(BaseModel):
    text: str


class EchoResponse(BaseModel):
    text: str


ECHO_CONTRACT = AgentContract(
    name="echo_agent",
    version="0.1.0",
    mission="echo payloads",
    consumes=(
        Capability(
            name="echo",
            summary="return the request text",
            request=EchoRequest,
            response=EchoResponse,
        ),
    ),
)


class EchoAgent(AgentBase):
    def __init__(self, bus: InProcessBus, *, raise_from_handler: bool = False) -> None:
        super().__init__(ECHO_CONTRACT, bus)
        self.raise_from_handler = raise_from_handler
        self.handlers = {"echo": self._echo}

    def _echo(self, request: BaseModel) -> EchoResponse:
        if self.raise_from_handler:
            raise RuntimeError("handler failed")
        echo_request = EchoRequest.model_validate(request)
        return EchoResponse(text=echo_request.text)


def _request() -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="echo_agent",
        message_type="request",
        capability="echo",
        payload={"text": "hello"},
    )


def _sample_value(
    metrics: PrometheusMetrics, name: str, labels: dict[str, str]
) -> float:
    for family in metrics.registry.collect():
        for sample in family.samples:
            if sample.name == name and dict(sample.labels) == labels:
                return float(sample.value)
    return 0.0


def _fault() -> AgentFault:
    return AgentFault(
        source_agent="scanner",
        source_module="agents.scanner.agent",
        capability="scan",
        severity="warning",
        error_type="RuntimeError",
        message="source failed",
    )


def test_null_metrics_is_safe_and_default_bus_behaviour_is_unchanged() -> None:
    metrics = NullMetrics()
    metrics.record_request("echo_agent", "echo", 0.0, ok=True)
    metrics.record_fault(_fault())

    bus = InProcessBus()
    EchoAgent(bus).bind()

    response = bus.request(_request())

    assert response.message_type == "response"
    assert response.payload == {"text": "hello"}


def test_prometheus_metrics_records_bus_throughput_latency_and_outcomes() -> None:
    metrics = PrometheusMetrics()
    ok_bus = InProcessBus(metrics=metrics)
    error_bus = InProcessBus(metrics=metrics)
    EchoAgent(ok_bus).bind()
    EchoAgent(error_bus, raise_from_handler=True).bind()

    ok_response = ok_bus.request(_request())
    error_response = error_bus.request(_request())

    assert ok_response.message_type == "response"
    assert error_response.message_type == "error"
    assert (
        _sample_value(
            metrics,
            "trading_agents_kernel_requests_total",
            {"agent": "echo_agent", "capability": "echo", "outcome": "ok"},
        )
        == 1.0
    )
    assert (
        _sample_value(
            metrics,
            "trading_agents_kernel_requests_total",
            {"agent": "echo_agent", "capability": "echo", "outcome": "error"},
        )
        == 1.0
    )
    assert (
        _sample_value(
            metrics,
            "trading_agents_kernel_request_latency_seconds_count",
            {"agent": "echo_agent", "capability": "echo"},
        )
        == 2.0
    )


def test_metered_fault_sink_records_faults_and_forwards_to_inner_sink() -> None:
    metrics = PrometheusMetrics()
    inner = CollectingFaultSink()
    sink = MeteredFaultSink(metrics, inner)
    fault = _fault()

    sink.submit(fault)

    assert inner.faults == [fault]
    assert (
        _sample_value(
            metrics,
            "trading_agents_kernel_faults_total",
            {
                "source_agent": "scanner",
                "source_module": "agents.scanner.agent",
                "severity": "warning",
            },
        )
        == 1.0
    )


def test_prometheus_exposition_renders_parseable_text() -> None:
    metrics = PrometheusMetrics()
    metrics.record_request("echo_agent", "echo", 0.01, ok=True)
    metrics.record_fault(_fault())

    text = metrics.exposition().decode("utf-8")
    families: list[Any] = list(text_string_to_metric_families(text))

    assert families
    assert "trading_agents_kernel_requests_total" in text
    assert "trading_agents_kernel_request_latency_seconds_bucket" in text
    assert "trading_agents_kernel_faults_total" in text
