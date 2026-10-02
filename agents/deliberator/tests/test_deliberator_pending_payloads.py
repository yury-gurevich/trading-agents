"""S252 A5: orderless pending PM runs retain their accepted per-poll fetch cost.

Agent: deliberator
Role: prove the order-property filter without fetching completed deliberation
      transcripts.
External I/O: none (in-memory graph).
"""

from __future__ import annotations

from tests.poll_payload_remaining import seed_deliberator
from tests.poll_payload_support import PayloadSpy

from agents.deliberator.store import find_pending


def test_an_orderless_pm_run_is_fetched_but_never_returned() -> None:
    """DLIB-TRG-01: missing order_intent_set stays a candidate, not review work,
    on each poll.
    """
    graph = PayloadSpy()
    seed_deliberator(graph)
    graph.arm("PMRun", "DELIBERATED_BY")

    for _ in range(2):
        graph.fetched.clear()
        assert [node.key for node in find_pending(graph)] == ["c", "a"]
        assert graph.fetched == ["c", "a", "no-orders"]
