"""Hold-drill start refusals.

Agent: orchestration
Role: prove DL-330 test-bot isolation and the fleet-window refusal.
External I/O: none.
"""

from datetime import UTC, datetime

import pytest

from orchestration.hold_drill_guard import (
    DrillRefusedError,
    DrillValues,
    bot_id,
    drill_values,
)
from orchestration.tests.hold_drill_fakes import (
    FLEET_BOT_VALUE,
    SAFE_NOW,
    TEST_BOT_VALUE,
)

GOOD = {"TELEGRAM_TEST_BOT_TOKEN": f" {TEST_BOT_VALUE} ", "TELEGRAM_CHAT_ID": " 42 "}


def test_each_missing_drill_value_is_named() -> None:
    """DL-330 D1: name every absent or blank drill value."""
    with pytest.raises(
        DrillRefusedError, match="TELEGRAM_TEST_BOT_TOKEN, TELEGRAM_CHAT_ID"
    ):
        drill_values({}, {"TELEGRAM_TEST_BOT_TOKEN": " "}, now=SAFE_NOW)
    with pytest.raises(
        DrillRefusedError, match=r"missing drill values: TELEGRAM_CHAT_ID$"
    ):
        drill_values({}, {**GOOD, "TELEGRAM_CHAT_ID": None}, now=SAFE_NOW)


@pytest.mark.parametrize("value", ["no-colon", ":key", "abc:key", "12 3:key"])
def test_a_value_that_is_not_a_bot_token_is_refused(value: str) -> None:
    """DL-330 D1: only a bot id made of digits before a colon is accepted."""
    assert bot_id(value) == ""
    with pytest.raises(DrillRefusedError, match="is not a bot token"):
        drill_values({}, {**GOOD, "TELEGRAM_TEST_BOT_TOKEN": value}, now=SAFE_NOW)


@pytest.mark.parametrize("in_file", [True, False])
def test_the_fleets_bot_is_refused_under_any_key(in_file: bool) -> None:
    """DL-330 D1: compare bot ids, including a regenerated fleet key."""
    environ = {} if in_file else {"TELEGRAM_BOT_TOKEN": TEST_BOT_VALUE}
    values = (
        {**GOOD, "TELEGRAM_BOT_TOKEN": "7000000001:a-regenerated-key"}
        if in_file
        else GOOD
    )
    with pytest.raises(DrillRefusedError, match="is the fleet's bot"):
        drill_values(environ, values, now=SAFE_NOW)


@pytest.mark.parametrize(
    ("hour", "minute", "second", "refused"),
    [(21, 59, 59, False), (22, 0, 0, True), (23, 59, 59, True), (0, 0, 0, False)],
)
def test_a_start_inside_the_fleets_window_is_refused(
    hour: int, minute: int, second: int, refused: bool
) -> None:
    """DL-330 D5: refuse exactly the fleet window, retaining safe boundaries."""
    now = datetime(2026, 11, 27, hour, minute, second, tzinfo=UTC)
    environ = {"TELEGRAM_BOT_TOKEN": FLEET_BOT_VALUE}
    if refused:
        with pytest.raises(DrillRefusedError, match="fleet's nightly window"):
            drill_values(environ, GOOD, now=now)
    else:
        assert drill_values(environ, GOOD, now=now) == DrillValues(TEST_BOT_VALUE, "42")


def test_the_values_never_print_the_token() -> None:
    """DL-330 D1: trim values and expose only the public id, never a repr secret."""
    values = drill_values({}, GOOD, now=SAFE_NOW)
    assert (values.bot_token, values.chat_id) == (TEST_BOT_VALUE, "42")
    assert repr(values) == "DrillValues()"
    assert bot_id(values.bot_token) == "7000000001"
