"""A8-A10: a replica's why is selected by shape and made safe.

Agent: orchestration
Role: prove shape precedence, inclusive console windows, masking and length limits.
External I/O: none.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from orchestration.container_lines import choose_line, safe_line
from orchestration.tests.container_sensor_helpers import NOW

EXCEPTION = "urllib.error.HTTPError: HTTP Error 404: Not Found"
CLOSING = "[provider] stopped on SIGTERM after 2s; exit 1"
SIGNAL = "[provider] stop signal SIGTERM: draining"


def test_a8_traceback_order_and_shape_precedence() -> None:
    """DSP-IN-05: failed closing outranks exception, which outranks a stop signal."""
    traceback = [
        (NOW, text)
        for text in (
            "Traceback (most recent call last):",
            '  File "x.py", line 1',
            EXCEPTION,
            "    get_data()",
        )
    ]
    assert choose_line(traceback, NOW) == EXCEPTION
    assert (
        choose_line([(NOW, SIGNAL), (NOW, EXCEPTION), (NOW, CLOSING)], NOW) == CLOSING
    )
    assert choose_line([(NOW, SIGNAL), (NOW, EXCEPTION)], NOW) == EXCEPTION
    assert choose_line([(NOW, SIGNAL)], NOW) == SIGNAL
    assert (
        choose_line(
            [
                (NOW, "[provider] stopped on SIGTERM after 2s; exit 0"),
                (NOW, "Request URL: https://example.test"),
            ],
            NOW,
        )
        == ""
    )
    assert (
        choose_line(
            [(NOW - timedelta(seconds=1), EXCEPTION), (NOW, "ValueError: newest")], NOW
        )
        == "ValueError: newest"
    )


@pytest.mark.parametrize(
    ("seconds", "inside"), [(-900, True), (60, True), (-901, False), (61, False)]
)
def test_a9_console_window(seconds: int, inside: bool) -> None:
    """DSP-IN-05: only lines within 15 minutes before to one minute after explain."""
    text = choose_line([(NOW + timedelta(seconds=seconds), EXCEPTION)], NOW)
    assert text == (EXCEPTION if inside else "")


def test_a10_credentials_and_amounts_are_masked() -> None:
    """DSP-SEC-03 / DSP-SEC-02: URL, bearer, named and long secrets and amounts mask."""
    plant = "synthetic"
    candidates = [
        (f"https://user:{plant}@example.test/path", "https://***@example.test/path"),
        (f"Bearer {plant}", "Bearer ***"),
        (f"password={plant}", "password=***"),
        (f"SharedAccessKey={plant}", "SharedAccessKey=***"),
        (f"token: {plant}", "token: ***"),
        ("a" * 40, "***"),
        ("$101,976.32 and 25000.00 and 101,976", "# and # and #"),
    ]
    for raw, expected in candidates:
        assert safe_line(raw) == expected
    assert safe_line(" ValueError:\n  folded\twords ") == "ValueError: folded words"
    long = safe_line("ValueError: " + "word " * 100)
    assert len(long) == 160
    assert long.endswith("…")
