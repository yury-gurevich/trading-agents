"""First-poll startup and competing memory receivers.

Agent: tooling
Role: prove D8's real first-poll condition and the Appendix's transport semantics.
External I/O: none.
"""

from __future__ import annotations

import threading

import pytest
from scripts import debate_lanes_scene as scene
from scripts.debate_lanes_memory import MemoryBroker, MemoryTransport


def test_manager_starts_after_every_replica_finishes_one_poll(monkeypatch):
    """DL-279 D8: a warm start waits for every actual first poll."""
    factory = MemoryTransport.consumer
    review = scene.review_pm_node
    completed = set()
    lock = threading.Lock()

    def consumer(self, graph, identity):
        inner = factory(self, graph, identity)
        poll = inner.poll

        def observed_poll():
            result = poll()
            with lock:
                completed.add(id(inner))
            return result

        inner.poll = observed_poll
        return inner

    def checked_review(*args, **kwargs):
        assert len(completed) == 4
        return review(*args, **kwargs)

    monkeypatch.setattr(MemoryTransport, "consumer", consumer)
    monkeypatch.setattr(scene, "review_pm_node", checked_review)
    assert scene.run(concurrency=2, orders=1, rounds=1, turn_seconds=0)["clean"] is True


def test_memory_delivery_competes_and_respects_the_requested_batch_size():
    """DL-279 D5: a queued message goes to one receiver and batches are bounded."""
    broker = MemoryBroker()
    for index in range(4):
        broker.publish("topic", {"index": index})
    first = broker.take("topic", 1, 0)
    remaining = broker.take("topic", 10, 0)
    assert len(first) == 1
    assert len(remaining) == 3
    assert len({id(raw) for raw in [*first, *remaining]}) == 4
    assert broker.take("topic", 1, 0) == []


def test_a_manager_identity_override_is_refused(monkeypatch):
    """DL-279 D5 / DLIB-DEP-02: the scene keeps the authorized manager identity."""
    monkeypatch.setenv("DELIBERATOR_INSTANCE_NAME", "unrelated-manager")
    with pytest.raises(ValueError, match="the manager must be deliberator-manager"):
        scene.run(concurrency=1, orders=1, rounds=1, turn_seconds=0)
