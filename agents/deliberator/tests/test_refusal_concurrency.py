"""A4-A5: refusals already in flight follow the process without skipping.

Agent: deliberator
Role: prove monotone advancement and synchronized concurrent requests.
External I/O: none.
"""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from agents.deliberator.tests.refusal_testkit import (
    SECOND,
    Client,
    StatusError,
    chain,
    complete,
    ledger,
)
from kernel import InMemoryGraphStore


def test_a4_already_left_candidate_lands_on_current() -> None:
    """DLIB-FAIL-05: after takes the refused candidate and never moves backward."""
    models = chain(Client("one"), Client("two"), Client("three"))
    first, second, third = models.candidates
    assert models.after(first) is second
    assert models.after(first) is second
    assert models.after(second) is third
    assert models.after(third) is None
    assert models.after(first) is third
    assert models.current() is third


def test_a5_concurrent_refusals_skip_no_candidate() -> None:
    """DLIB-FAIL-05: three requests in flight at FIRST all land on SECOND once."""
    first = Client(StatusError(429), Barrier(3))
    second, third = Client("second answer"), Client("must never answer")
    models, graph = chain(first, second, third), InMemoryGraphStore()

    def request(number: int) -> str:
        return complete(ledger(graph, models, f"concurrent-{number}"))

    with ThreadPoolExecutor(max_workers=3) as executor:
        answers = list(executor.map(request, range(3)))
    assert answers == ["second answer"] * 3
    assert len(first.requests) == len(second.requests) == 3
    assert third.requests == []
    assert models.current().label == SECOND
    assert len(graph.list_nodes("LLMCall")) == 6
