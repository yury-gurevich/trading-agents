"""S250: with the history rule on, no unheld line short of the bar reaches the pipeline.

Agent: tooling
Role: prove the harness's opt-in history rule against synthetic one-year caches.
External I/O: local tmp files only.
"""

from __future__ import annotations

import json
from filecmp import cmp
from typing import TYPE_CHECKING

from scripts.replay_settings import build_effective_settings
from tests.replay_history_fixtures import (
    COUNTER,
    bars_in_window,
    observe,
    run_window,
    write_cache,
)

from agents.analyst.history_requirements import required_history_bars
from contracts.common import Explanation, Money
from contracts.portfolio_manager import OrderIntent

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

SHORT_FIRST_BAR = 40  # SHORT joins on session 40; LONG has every session of the year.
START, END = 205, 245  # LONG holds the full 203-bar window on every session run.
SPAN = {"start": START, "end": END}


def test_c1_a_line_under_the_required_history_is_not_offered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S250-C1 / PROV-TRG-05: inside its declared window a line needs the bar.

    SHORT's window on session k holds k - 39 bars, so it first holds the 200 bars
    `required_history_bars` asks for on session 239; before that it is withheld and
    each withheld member-session is counted.
    """
    sessions = write_cache(
        tmp_path / "cache", {"LONG": range(252), "SHORT": range(SHORT_FIRST_BAR, 252)}
    )
    seen = observe(monkeypatch)
    required = required_history_bars(build_effective_settings(()).analyst)
    first_offered = SHORT_FIRST_BAR + required - 1
    assert bars_in_window(SHORT_FIRST_BAR, first_offered) == required

    summary = run_window(
        tmp_path / "cache", tmp_path / "out", sessions, **SPAN, require_history=True
    )

    by_day = {day: (tickers, bar_tickers) for day, tickers, bar_tickers in seen}
    for index in range(START, END + 1):
        expected = ("LONG", "SHORT") if index >= first_offered else ("LONG",)
        assert by_day[sessions[index]] == (expected, frozenset(expected)), index
    assert summary["absent_inputs"][COUNTER] == first_offered - START


def test_c2_a_held_line_stays_visible_and_is_not_counted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S250-C2 / PROV-TRG-05: a held line under the bar (a gap) is still offered.

    GAP's bars stop for 120 sessions, so its window holds 83 bars on session 205.
    It is withheld that session (counted once), bought, filled on 206, and from then
    on its ticker and bars are offered and never counted.
    """
    gap = (*range(60), *range(180, 252))
    sessions = write_cache(tmp_path / "cache", {"LONG": range(252), "GAP": gap})
    buy = OrderIntent(
        ticker="GAP",
        action="buy",
        quantity=10,
        est_price=Money(amount=10),
        stop_pct=0.05,
        target_pct=0.1,
        rationale=Explanation(summary="buy", evidence_refs=("fixture",)),
    )
    seen = observe(monkeypatch, {sessions[START]: (buy,)})

    summary = run_window(
        tmp_path / "cache", tmp_path / "out", sessions, **SPAN, require_history=True
    )

    assert seen[0][1:] == (("LONG",), frozenset({"LONG"}))
    for _day, tickers, bar_tickers in seen[1:]:
        assert (tickers, bar_tickers) == (("GAP", "LONG"), frozenset({"GAP", "LONG"}))
    assert summary["absent_inputs"][COUNTER] == 1
    fills = (tmp_path / "out" / "fills.csv").read_text(encoding="utf-8")
    assert f"{sessions[START + 1].isoformat()},GAP" in fills.replace('"', "")


def test_c3_the_rule_off_changes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S250-C3 / RPT-OUT-07: off by default; off writes the bytes it always wrote."""
    sessions = write_cache(
        tmp_path / "cache", {"LONG": range(252), "SHORT": range(SHORT_FIRST_BAR, 252)}
    )
    seen = observe(monkeypatch)

    default = run_window(tmp_path / "cache", tmp_path / "default", sessions, **SPAN)
    explicit = run_window(
        tmp_path / "cache", tmp_path / "off", sessions, **SPAN, require_history=False
    )

    assert all(tickers == ("LONG", "SHORT") for _day, tickers, _bars in seen)
    assert COUNTER not in default["absent_inputs"]
    assert default == explicit
    for name in ("equity.csv", "fills.csv", "sessions.csv", "summary.json"):
        assert cmp(tmp_path / "default" / name, tmp_path / "off" / name, shallow=False)
    stored = json.loads((tmp_path / "off" / "summary.json").read_text("utf-8"))
    assert COUNTER not in stored["absent_inputs"]


def test_c4_the_bar_is_the_analysts_own_number(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S250-C4 / PROV-TRG-05: `ANALYST_SMA_LONG_PERIOD=100` moves the bar to 100 bars.

    LATE joins on session 150, so its window holds 99 bars on session 248 and 100
    on 249 (the override's window still reaches back past session 150). The
    override offers it on 249 and not on 248; the default's bar of 200 withholds
    it on 249. No bar count is written in `scripts/`: the threshold is read from
    `required_history_bars`.
    """
    override = ("ANALYST_SMA_LONG_PERIOD=100",)
    assert required_history_bars(build_effective_settings(override).analyst) == 100
    sessions = write_cache(
        tmp_path / "cache", {"LONG": range(252), "LATE": range(150, 252)}
    )
    seen = observe(monkeypatch)
    on = {"require_history": True}

    run_window(tmp_path / "cache", tmp_path / "a", sessions, start=249, end=249, **on)
    run_window(
        tmp_path / "cache",
        tmp_path / "b",
        sessions,
        start=249,
        end=249,
        overrides=override,
        **on,
    )
    run_window(
        tmp_path / "cache",
        tmp_path / "c",
        sessions,
        start=248,
        end=248,
        overrides=override,
        **on,
    )

    assert [tickers for _day, tickers, _bars in seen] == [
        ("LONG",),
        ("LATE", "LONG"),
        ("LONG",),
    ]
