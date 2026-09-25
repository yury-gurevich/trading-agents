"""Dashboard hold-answer route validation tests.

Agent: surfaces
Role: prove malformed dashboard commands cannot append an answer fact.
External I/O: none; uses an in-memory graph and byte streams.
"""

from __future__ import annotations

from datetime import date

from kernel import InMemoryGraphStore
from surfaces.dashboard.hold_answer_route import _as_of, _json_body, handle_hold_answer


def test_route_rejects_wrong_method_invalid_payload_and_missing_hold() -> None:
    """SRF-IN-02: dashboard answers require POST, legal data, and a live hold."""
    graph = InMemoryGraphStore()
    assert handle_hold_answer({}, graph, now=None) == (405, {"error": "POST only"})
    assert handle_hold_answer({"REQUEST_METHOD": "POST"}, graph, now=None) == (
        400,
        {"error": "run_id and answer are required"},
    )
    assert handle_hold_answer(
        {
            "REQUEST_METHOD": "POST",
            "CONTENT_LENGTH": "42",
            "wsgi.input": _Input(b'{"run_id":"run","answer":"run_now"}'),
        },
        graph,
        now=None,
    ) == (404, {"error": "no active hold"})


def test_json_and_date_helpers_fail_closed() -> None:
    """S219: malformed request bodies and dates resolve to harmless defaults."""
    fallback = date(2026, 7, 8)

    assert _json_body({}) == {}
    assert _as_of("not-a-date", fallback) == fallback


class _Input:
    def __init__(self, value: bytes) -> None:
        self._value = value

    def read(self, _size: int) -> bytes:
        return self._value
