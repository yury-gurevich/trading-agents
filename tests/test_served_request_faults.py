"""Failure-path proofs for S256 served requests.

Agent: kernel
Role: prove reply faults persist and failed takes never reach handlers.
External I/O: none.
"""

from __future__ import annotations

import json

import pytest
from tests.bus_azure_receiver_helpers import RawMessage
from tests.served_request_helpers import LockLostError, scene

from kernel import CollectingFaultSink, InMemoryGraphStore
from kernel.fault_graph import GraphFaultSink
from kernel.serve_loop import serve_loop, serve_once


def test_failed_replies_leave_a_fault_and_serve_the_next_request() -> None:
    """DLIB-IDM-04 / DLIB-NEV-06: A3 failed replies do not redeliver or stop."""
    consumer, served, receiver, events = scene(("one", "two"), publish_fails=True)
    graph = InMemoryGraphStore()
    inner = CollectingFaultSink()
    sink = GraphFaultSink(graph, inner)

    assert serve_once(consumer, served, sink=sink) == 1
    assert serve_once(consumer, served, sink=sink) == 1
    assert serve_once(consumer, served, sink=sink) == 0

    assert events == ["settled", "handled", "one", "settled", "handled", "two"]
    assert len(receiver.completed) == 2
    assert receiver.abandoned == receiver.dead_lettered == []
    (fault,) = graph.list_nodes("Fault")
    assert fault.props["source_module"] == "kernel.serve_loop"
    assert fault.props["source_agent"] == "echo"
    assert fault.props["capability"] == "echo"
    assert fault.props["severity"] == "error"
    assert fault.props["error_type"] == "RuntimeError"
    assert fault.props["message"] == "publish unavailable"
    assert len(inner.faults) == 2
    assert not graph.list_nodes("FaultSuppression")


@pytest.mark.parametrize("at_limit", [False, True])
def test_an_unresolved_request_is_refused_and_never_completed(at_limit: bool) -> None:
    """DLIB-IDM-04 / DLIB-NEV-06: A4 no decoded request means no settlement."""
    consumer, served, receiver, events = scene(())
    raw = RawMessage(
        17
        if at_limit
        else json.dumps(
            {"topic": "echo.requests", "label": "AgentMessage", "ref": "missing"}
        ),
        delivery_count=5 if at_limit else 1,
    )
    receiver.messages.append(raw)

    assert serve_once(consumer, served) == 0
    assert receiver.completed == []
    assert events == []
    if at_limit:
        assert receiver.dead_lettered == [(raw, "S100ReceiverFailure")]
        assert receiver.abandoned == []
    else:
        assert receiver.abandoned == [raw]
        assert receiver.dead_lettered == []


def test_failed_settlement_propagates_before_any_handler_or_reply() -> None:
    """DLIB-IDM-04: A5 a failed take is not a served or swallowed request."""
    consumer, served, receiver, events = scene(("one",))
    receiver.fail_take = True
    sink = CollectingFaultSink()

    with pytest.raises(LockLostError, match="message lock expired"):
        serve_once(consumer, served, sink=sink)
    assert events == []
    assert receiver.completed == receiver.abandoned == receiver.dead_lettered == []
    assert sink.faults == []


def test_serve_loop_forwards_the_given_fault_sink(monkeypatch) -> None:
    """DLIB-IDM-04 / DLIB-NEV-06: the loop keeps serving on its graph sink."""
    consumer, served, receiver, events = scene(("one", "two"), publish_fails=True)
    graph = InMemoryGraphStore()
    inner = CollectingFaultSink()
    sink = GraphFaultSink(graph, inner)
    poll = consumer.poll

    def finite_poll():
        if not receiver.messages:
            raise StopIteration("test end")
        return poll()

    monkeypatch.setattr(consumer, "poll", finite_poll)
    with pytest.raises(StopIteration, match="test end"):
        serve_loop(consumer, served, poll_interval=0, sink=sink)

    assert len(receiver.completed) == events.count("handled") == 2
    assert len(graph.list_nodes("Fault")) == 1
    assert len(inner.faults) == 2


def test_reply_faults_are_contained_with_the_default_sink() -> None:
    """DLIB-IDM-04 / DLIB-NEV-06: the optional sink preserves caller compatibility."""
    consumer, served, receiver, _events = scene(("one",), publish_fails=True)
    assert serve_once(consumer, served) == 1
    assert len(receiver.completed) == 1
    assert receiver.abandoned == receiver.dead_lettered == []
