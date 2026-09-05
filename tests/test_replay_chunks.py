"""Round-chunking tests.

Agent: tooling
Role: prove a round is split by payload size and comes back whole.
External I/O: none.
"""

from __future__ import annotations

from orchestration.replay_chunks import (
    DEFAULT_CHUNK_BYTES,
    chunk_by_bytes,
    request_bytes,
)
from orchestration.replay_types import BatchRequest


def _request(index: int, user_chars: int = 100) -> BatchRequest:
    return BatchRequest(
        custom_id=f"turn-{index}",
        model="claude-opus-5",
        max_tokens=4096,
        effort="high",
        system="S",
        user="u" * user_chars,
    )


def test_a_small_round_travels_as_one_chunk() -> None:
    """Splitting a round that fits would only add failure modes."""
    requests = [_request(i) for i in range(10)]

    assert chunk_by_bytes(requests) == (tuple(requests),)


def test_a_round_is_split_by_bytes_not_by_request_count() -> None:
    """A judge request is several times a defender request; a count cannot see that."""
    small = [_request(i, user_chars=10) for i in range(4)]
    large = [_request(i + 100, user_chars=400) for i in range(4)]

    assert len(chunk_by_bytes(small, max_bytes=200)) < len(
        chunk_by_bytes(large, max_bytes=200)
    )


def test_every_request_appears_exactly_once_across_the_chunks() -> None:
    """A dropped request silently shrinks the sample; a repeated one double-pays."""
    requests = [_request(i, user_chars=50) for i in range(37)]

    flattened = [
        item for chunk in chunk_by_bytes(requests, max_bytes=200) for item in chunk
    ]

    assert flattened == requests
    assert len({item.custom_id for item in flattened}) == 37


def test_the_original_order_survives_the_split() -> None:
    """Results are matched by custom_id, but a stable order keeps caches readable."""
    requests = [_request(i, user_chars=50) for i in range(9)]

    chunks = chunk_by_bytes(requests, max_bytes=120)

    assert [item.custom_id for chunk in chunks for item in chunk] == [
        f"turn-{i}" for i in range(9)
    ]


def test_one_oversized_request_gets_its_own_chunk_rather_than_being_dropped() -> None:
    """Refusing to send it would shrink the sample without saying so."""
    requests = [_request(0, user_chars=10), _request(1, user_chars=5000)]

    chunks = chunk_by_bytes(requests, max_bytes=100)

    assert [len(chunk) for chunk in chunks] == [1, 1]
    assert chunks[1][0].custom_id == "turn-1"


def test_a_request_cap_bounds_a_chunk_even_when_the_bytes_are_tiny() -> None:
    """Ten thousand one-byte requests is still one implausible POST."""
    requests = [_request(i, user_chars=1) for i in range(2500)]

    chunks = chunk_by_bytes(requests, max_requests=1000)

    assert [len(chunk) for chunk in chunks] == [1000, 1000, 500]


def test_an_empty_round_produces_no_chunks_at_all() -> None:
    """A round with nothing to send must cost nothing, not one empty batch."""
    assert chunk_by_bytes([]) == ()


def test_the_measured_size_counts_both_halves_of_the_prompt() -> None:
    """The system prompt is sent on every request and is not free."""
    assert request_bytes(_request(0, user_chars=100)) == 101


def test_the_default_ceiling_sits_well_under_the_measured_failure() -> None:
    """Round 2's single 74 MB POST died; a chunk must never be the thing tested."""
    assert DEFAULT_CHUNK_BYTES < 74_000_000 / 4
