"""Celery bus and both-backends parity tests."""

from __future__ import annotations

import os

import pytest
from pydantic import BaseModel

from kernel import (
    AgentBase,
    AgentContract,
    AgentMessage,
    Capability,
    CeleryBus,
    CeleryBusSettings,
    CollectingFaultSink,
    InProcessBus,
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
    def __init__(self, bus, *, raise_from_handler: bool = False) -> None:
        super().__init__(ECHO_CONTRACT, bus)
        self.raise_from_handler = raise_from_handler
        self.handlers = {"echo": self._echo}

    def _echo(self, request: BaseModel) -> EchoResponse:
        if self.raise_from_handler:
            raise RuntimeError("handler failed")
        echo_request = EchoRequest.model_validate(request)
        return EchoResponse(text=echo_request.text)


def _request(capability: str = "echo", payload: dict[str, object] | None = None):
    return AgentMessage(
        sender="tester",
        recipient="echo_agent",
        message_type="request",
        capability=capability,
        payload=payload or {"text": "hello"},
    )


def test_celery_round_trip_returns_echoed_response() -> None:
    sink = CollectingFaultSink()
    bus = CeleryBus(sink=sink)
    EchoAgent(bus).bind()

    request = _request(payload={"text": "ping"})
    response = bus.request(request)

    assert response.message_type == "response"
    assert response.correlation_id == request.id
    assert response.payload == {"text": "ping"}
    assert sink.faults == []


def test_celery_inbound_validation_returns_error_and_records_fault() -> None:
    sink = CollectingFaultSink()
    bus = CeleryBus(sink=sink)
    EchoAgent(bus).bind()

    response = bus.request(_request(payload={"wrong": "shape"}))

    assert response.message_type == "error"
    assert response.payload["error_type"] == "ValidationError"
    assert len(sink.faults) == 1
    assert sink.faults[0].source_agent == "echo_agent"
    assert sink.faults[0].source_module == "kernel.bus_celery"
    assert sink.faults[0].capability == "echo"


def test_celery_handler_exception_returns_error_and_records_fault() -> None:
    sink = CollectingFaultSink()
    bus = CeleryBus(sink=sink)
    EchoAgent(bus, raise_from_handler=True).bind()

    response = bus.request(_request())

    assert response.message_type == "error"
    assert response.payload == {
        "error_type": "RuntimeError",
        "message": "handler failed",
    }
    assert len(sink.faults) == 1
    assert sink.faults[0].source_module == "kernel.bus_celery"
    assert sink.faults[0].error_type == "RuntimeError"


def test_celery_unknown_capability_returns_error_without_exception() -> None:
    request = _request(capability="missing")

    response = CeleryBus().request(request)

    assert response.message_type == "error"
    assert response.correlation_id == request.id
    assert response.payload == {
        "error_type": "UnknownCapability",
        "message": "No handler registered for echo_agent.missing",
    }


def test_celery_unauthorized_caller_is_rejected() -> None:
    bus = CeleryBus()
    bus.register("echo_agent", "echo", lambda payload: payload, ("trusted",))

    response = bus.request(
        AgentMessage(
            sender="intruder",
            recipient="echo_agent",
            message_type="request",
            capability="echo",
            payload={"text": "hi"},
        )
    )

    assert response.message_type == "error"
    assert response.payload["error_type"] == "Unauthorized"


def test_celery_worker_missing_handler_returns_task_error() -> None:
    bus = CeleryBus()
    EchoAgent(bus).bind()
    bus._handlers.clear()

    result = bus._dispatch(_request())

    assert result == {
        "error": {
            "error_type": "UnknownCapability",
            "message": "No handler registered for echo_agent.echo",
        }
    }


@pytest.mark.parametrize("bus_factory", [InProcessBus, CeleryBus])
def test_echo_agent_answers_identically_over_both_backends(bus_factory) -> None:
    sink = CollectingFaultSink()
    bus = bus_factory(sink)
    EchoAgent(bus).bind()
    request = _request(payload={"text": "parity"})

    response = bus.request(request)

    assert response.message_type == "response"
    assert response.correlation_id == request.id
    assert response.sender == "echo_agent"
    assert response.recipient == "tester"
    assert response.capability == "echo"
    assert response.payload == {"text": "parity"}


@pytest.mark.integration
def test_celery_real_broker_round_trip() -> None:
    broker_url = os.getenv("CELERY_BROKER_URL")
    if not broker_url:
        pytest.skip("CELERY_BROKER_URL is not set")
    from celery.contrib.testing.worker import start_worker

    settings = CeleryBusSettings(
        celery_broker_url=broker_url,
        celery_result_backend=os.getenv("CELERY_RESULT_BACKEND", broker_url),
        celery_task_always_eager=False,
        celery_request_timeout_seconds=5.0,
    )
    bus = CeleryBus(settings=settings)
    EchoAgent(bus).bind()

    with start_worker(bus._app, perform_ping_check=False):
        response = bus.request(_request(payload={"text": "broker"}))

    assert response.message_type == "response"
    assert response.payload == {"text": "broker"}
