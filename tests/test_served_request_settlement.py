"""Settle-on-take proofs for S256.

Agent: kernel
Role: prove served requests are settled before work starts, even on slow turns.
External I/O: none.
"""

from __future__ import annotations

import pytest
from tests.bus_azure_receiver_helpers import response
from tests.served_request_helpers import scene

from kernel import AzureServiceBusSettings
from kernel.serve_loop import serve_once


def test_request_is_settled_before_handling_and_publication() -> None:
    """DLIB-IDM-04: A1 settles a decoded request before its handler and reply."""
    consumer, served, receiver, events = scene(("one",))

    assert serve_once(consumer, served) == 1

    assert events == ["settled", "handled", "one", "published"]
    assert len(receiver.completed) == 1
    assert receiver.abandoned == receiver.dead_lettered == []


def test_one_request_is_taken_per_default_pass() -> None:
    """DLIB-IDM-04: A6 default settings serve three requests one at a time."""
    settings = AzureServiceBusSettings(_env_file=None, connection_string=None)
    assert settings.receive_max_messages == 1
    consumer, served, receiver, events = scene(("one", "two", "three"))

    for remaining, ref in zip((2, 1, 0), ("one", "two", "three"), strict=True):
        assert serve_once(consumer, served) == 1
        assert len(receiver.messages) == remaining
        assert events[-3:] == ["handled", ref, "published"]
    assert serve_once(consumer, served) == 0
    assert len(receiver.completed) == 3


def test_reply_never_touches_the_receiver() -> None:
    """DLIB-IDM-04: B4 replying cannot settle, abandon or dead-letter a take."""
    consumer, _served, receiver, events = scene(("one",))
    (message,) = consumer.poll()
    before = (
        list(receiver.completed),
        list(receiver.abandoned),
        list(receiver.dead_lettered),
    )
    assert len(before[0]) == 1
    consumer.reply(response(message))
    assert (receiver.completed, receiver.abandoned, receiver.dead_lettered) == before
    assert events == ["settled", "published"]


@pytest.mark.parametrize("invalid", [0, 101])
def test_receive_batch_bounds_are_preserved(invalid: int) -> None:
    """DLIB-IDM-04: one-per-pass remains a bounded, overridable tunable."""
    with pytest.raises(ValueError, match="receive_max_messages"):
        AzureServiceBusSettings(_env_file=None, receive_max_messages=invalid)


def test_receive_batch_tunable_can_still_be_raised() -> None:
    """DLIB-IDM-04: an explicit batch override is honored, never hard-coded away."""
    settings = AzureServiceBusSettings(_env_file=None, receive_max_messages=3)
    consumer, served, receiver, events = scene(
        ("one", "two", "three"), settings=settings
    )
    assert serve_once(consumer, served) == 3
    assert len(receiver.completed) == events.count("handled") == 3
    assert receiver.messages == []


def test_a_turn_that_outlives_its_lock_is_served_once() -> None:
    """DLIB-IDM-04: A2 a handler that expires the lock runs and replies once."""
    consumer, served, receiver, events = scene(("slow",))
    receiver.expire_after_handling = True

    assert serve_once(consumer, served) == 1
    assert serve_once(consumer, served) == 0

    assert events.count("handled") == events.count("published") == 1
    assert len(receiver.completed) == 1
    assert receiver.abandoned == receiver.dead_lettered == []
