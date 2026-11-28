"""The hold drill through the real dispatcher and a synthetic Bot API.

Agent: orchestration
Role: prove DL-330 past-session holds, answers, acts and verdicts.
External I/O: none.
"""

from datetime import date

from orchestration.hold_drill import prior_sessions, run_drill, run_round
from orchestration.tests.hold_drill_fakes import TODAY, FakeBot, drill_on

D1, D2 = date(2026, 11, 27), date(2026, 11, 25)
R1, R2 = "sched-2026-11-27", "sched-2026-11-25"


def test_the_two_sessions_are_the_last_before_today() -> None:
    """DL-330 D3: use past NYSE sessions, excluding Thanksgiving and today."""
    assert prior_sessions(TODAY, 2) == (D1, D2)
    assert prior_sessions(D1, 1) == (D2,)


def test_run_now_is_recorded_from_telegram_and_places_the_run() -> None:
    """DL-330 D2, D3, D4: hold, notify, record, acknowledge, confirm and place."""
    bot = FakeBot()
    lines: list[str] = []
    drill, slept = drill_on(bot, [("run_now", R1)], lines)
    assert run_round(drill, as_of=D1, wanted="run_now")
    assert bot.sent[0][0].endswith("Next message: press Run now.")
    assert len(bot.notices()) == 1
    text, buttons = bot.notices()[0]
    assert text.startswith(f"Run {R1} is held. Checks: ")
    assert "transient:execution:alpaca-broker:hold-drill" in text
    assert buttons == [f"run_now:{R1}", f"skip_today:{R1}"]
    assert lines == [
        f"{R1}  held, notice 102: Run now",
        f"{R1}  PASS",
        "  answer    run_now from telegram",
        "  act       placed reason=NYSE trading session, RunRequest 1",
        "  cursor    confirmed",
        "  faults    0",
    ]
    assert bot.acks == ["cb501"]
    assert bot.updates == []
    assert slept == [5]


def test_skip_today_is_recorded_from_telegram_and_skips_the_run() -> None:
    """DL-330 D4: the requested skip is recorded and writes no RunRequest."""
    bot = FakeBot()
    lines: list[str] = []
    drill, _ = drill_on(bot, [("skip_today", R2)], lines)
    assert run_round(drill, as_of=D2, wanted="skip_today")
    assert lines[1:4] == [
        f"{R2}  PASS",
        "  answer    skip_today from telegram",
        "  act       skipped reason=operator, RunRequest 0",
    ]


def test_the_other_button_fails_the_round_and_is_still_acted_on() -> None:
    """DL-330 D4: an effective answer can act while failing the drill ask."""
    bot = FakeBot()
    lines: list[str] = []
    drill, _ = drill_on(bot, [("run_now", R2)], lines)
    assert not run_round(drill, as_of=D2, wanted="skip_today")
    assert lines[1:4] == [
        f"{R2}  FAIL",
        "  answer    run_now from telegram, asked skip_today",
        "  act       placed reason=NYSE trading session, RunRequest 1",
    ]


def test_no_press_fails_the_round_after_the_wait() -> None:
    """DL-330 D4: no press expires at the next poll after the wait budget."""
    bot = FakeBot()
    lines: list[str] = []
    drill, slept = drill_on(bot, [], lines, wait=12)
    assert not run_round(drill, as_of=D1, wanted="run_now")
    assert slept == [5, 5, 5]
    assert lines[-2:] == [f"{R1}  FAIL", "  no answer in 15 s"]
    assert len(bot.notices()) == 1


def test_a_notice_telegram_refuses_fails_the_round_at_once() -> None:
    """DL-330 D4: the unchanged client reports the refused notice fault."""
    bot = FakeBot(send_ok=False)
    lines: list[str] = []
    drill, slept = drill_on(bot, [], lines)
    assert not run_round(drill, as_of=D1, wanted="run_now")
    assert slept == []
    assert lines == [
        f"{R1}  FAIL",
        "  notice not sent (held) (telegram: telegram_message_id_missing)",
    ]


def test_a_press_waiting_before_the_notice_does_not_count() -> None:
    """DL-330 D4: drain an old matching press before the notice, without ack."""
    bot = FakeBot()
    lines: list[str] = []
    bot.press("run_now", R1)
    drill, _ = drill_on(bot, [], lines, wait=5)
    assert not run_round(drill, as_of=D1, wanted="run_now")
    assert lines[-1] == "  no answer in 5 s"
    assert bot.updates == []
    assert bot.acks == []


def test_a_late_acknowledgement_is_a_fault_not_a_failure() -> None:
    """DL-330 D4: print acknowledgement faults without rejecting a sound act."""
    bot = FakeBot(ack_ok=False)
    lines: list[str] = []
    drill, _ = drill_on(bot, [("run_now", R1)], lines)
    assert run_round(drill, as_of=D1, wanted="run_now")
    assert lines[-1] == "  faults    1 (telegram: telegram_response_invalid)"


def test_a_cursor_left_behind_fails_the_round() -> None:
    """DL-330 D4: an unconfirmed answer fails even after placement."""
    bot = FakeBot(confirm_ok=False)
    lines: list[str] = []
    drill, _ = drill_on(bot, [("run_now", R1)], lines)
    assert not run_round(drill, as_of=D1, wanted="run_now")
    assert "  cursor    1 answer(s) still pending" in lines


def test_the_drill_asks_run_now_then_skip_today_and_says_when_done() -> None:
    """DL-330 D4: newer session runs first, older skips, then print completion."""
    bot = FakeBot()
    lines: list[str] = []
    drill, _ = drill_on(bot, [("run_now", R1), ("skip_today", R2)], lines)
    assert run_drill(drill, today=TODAY) == (True, True)
    assert [buttons[0] for _, buttons in bot.notices()] == [
        f"run_now:{R1}",
        f"run_now:{R2}",
    ]
    assert bot.sent[-1] == ("Hold drill done: 2 of 2 rounds passed.", [])
    assert [line for line in lines if line.endswith("  PASS")] == [
        f"{R1}  PASS",
        f"{R2}  PASS",
    ]
