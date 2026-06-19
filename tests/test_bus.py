"""In-process bus and AgentBase runtime tests."""

from __future__ import annotations

from pydantic import BaseModel

from kernel import (
    AgentBase,
    AgentContract,
    AgentMessage,
    Capability,
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
    def __init__(self, bus: InProcessBus, *, raise_from_handler: bool = False) -> None:
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


def test_round_trip_returns_echoed_response():
    sink = CollectingFaultSink()
    bus = InProcessBus(sink)
    EchoAgent(bus).bind()

    request = _request(payload={"text": "ping"})
    response = bus.request(request)

    assert response.message_type == "response"
    assert response.correlation_id == request.id
    assert response.payload == {"text": "ping"}
    assert sink.faults == []


def test_inbound_validation_returns_error_and_records_fault():
    sink = CollectingFaultSink()
    bus = InProcessBus(sink)
    EchoAgent(bus).bind()

    response = bus.request(_request(payload={"wrong": "shape"}))

    assert response.message_type == "error"
    assert response.payload["error_type"] == "ValidationError"
    assert len(sink.faults) == 1
    assert sink.faults[0].source_agent == "echo_agent"
    assert sink.faults[0].source_module == "kernel.bus"
    assert sink.faults[0].capability == "echo"


def test_handler_exception_returns_error_and_records_fault():
    sink = CollectingFaultSink()
    bus = InProcessBus(sink)
    EchoAgent(bus, raise_from_handler=True).bind()

    response = bus.request(_request())

    assert response.message_type == "error"
    assert response.payload == {
        "error_type": "RuntimeError",
        "message": "handler failed",
    }
    assert len(sink.faults) == 1
    assert sink.faults[0].source_module == "kernel.bus"
    assert sink.faults[0].error_type == "RuntimeError"


def test_unknown_capability_returns_error_without_exception():
    request = _request(capability="missing")

    response = InProcessBus().request(request)

    assert response.message_type == "error"
    assert response.correlation_id == request.id
    assert response.payload == {
        "error_type": "UnknownCapability",
        "message": "No handler registered for echo_agent.missing",
    }


def test_unauthorized_caller_is_rejected_and_allowed_caller_passes():
    bus = InProcessBus()
    bus.register("echo_agent", "echo", lambda payload: payload, ("trusted",))

    blocked = bus.request(
        AgentMessage(
            sender="intruder",
            recipient="echo_agent",
            message_type="request",
            capability="echo",
            payload={"text": "hi"},
        )
    )
    assert blocked.message_type == "error"
    assert blocked.payload["error_type"] == "Unauthorized"

    allowed = bus.request(
        AgentMessage(
            sender="trusted",
            recipient="echo_agent",
            message_type="request",
            capability="echo",
            payload={"text": "hi"},
        )
    )
    assert allowed.message_type == "response"
