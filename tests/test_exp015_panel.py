"""S289-A18 through A20: compare synthetic panel rows with the replay's own calls.

Agent: tooling
Role: prove all scanner survivors, the actual baseline and row alignment.
External I/O: none.
"""

from __future__ import annotations

import numpy as np
import pytest
from scripts.exp015_features import line_features
from scripts.exp015_panel import build_panel
from scripts.exp015_spec import LINE_FEATURES
from scripts.replay_day import ReplayDayInputs, run_replay_day
from scripts.replay_history import offer_lines, visible_window
from scripts.replay_series import (
    bars_by_line,
    benchmark_window,
    contract_bars,
    members_on,
)
from tests.exp015_fixtures import replay_fixture

from agents.scanner.domain.filters import apply_filters


def offered_on(context, settings, session):
    by_line = bars_by_line(context.universe.bars)
    members = members_on(context.universe, session)
    window = visible_window(settings, by_line, members, session)
    return offer_lines(settings, members, window, ())


def test_a18_primary_is_every_scanner_survivor():
    """S289-A18 / SCAN-IDM-01: primary equals uncapped filters on offered bars."""
    context, settings, days = replay_fixture()
    panel, _ = build_panel(
        context, settings, bars_by_line(context.universe.bars), {}, days
    )
    assert (~panel.primary).any()
    for day in days:
        offered = offered_on(context, settings, day)
        survivors, _ = apply_filters(
            offered.members,
            contract_bars(offered.bars),
            benchmark_window(context.benchmark, day, offered.bars),
            {},
            day,
            settings.scanner,
            earnings_horizon_days=None,
        )
        expected = {s.ticker for s in survivors}
        assert len(expected) > settings.scanner.candidate_cap
        mask = (panel.sessions == day.isoformat()) & panel.primary
        assert set(panel.lines[mask]) == expected
        assert "L31" not in panel.lines[panel.sessions == day.isoformat()]


def test_a19_baseline_is_the_replays_technical_score():
    """S289-A19 / ANLZ-IDM-01 / ANLZ-OUT-02: replay recommendations are the oracle."""
    context, settings, days = replay_fixture()
    panel, _ = build_panel(
        context, settings, bars_by_line(context.universe.bars), {}, days
    )
    checked = 0
    for day in days:
        offered = offered_on(context, settings, day)
        inputs = ReplayDayInputs(
            run_id="synthetic-s289",
            session=day,
            tickers=offered.members,
            bars=contract_bars(offered.bars),
            benchmark_bars=benchmark_window(context.benchmark, day, offered.bars),
            vix=18.0,
            equity_cents=10_000_000,
            held=(),
            held_stops=(),
            active_broker_stop_refs=frozenset(),
            sectors=context.sectors,
        )
        result = run_replay_day(inputs, settings)
        assert result.recommendations.recommendations
        for rec in result.recommendations.recommendations:
            mask = (panel.sessions == day.isoformat()) & (panel.lines == rec.ticker)
            assert mask.sum() == 1
            assert panel.baseline[mask][0] == pytest.approx(rec.technical_score)
            assert rec.technical_score != pytest.approx(rec.confidence)
            checked += 1
    assert checked > 0


def test_a20_secondary_features_masks_and_sectors():
    """S289-A20: own 253 bars, exact raw feature row, L03 mask and absent sectors."""
    context, settings, days = replay_fixture()
    by_line = bars_by_line(context.universe.bars)
    move = days[2]
    panel, counts = build_panel(context, settings, by_line, {"L03": (move,)}, days)
    assert counts["rows_without_sector"] == int((panel.sectors == "").sum()) > 0
    assert panel.secondary.any()
    assert (~panel.secondary).any()
    for line in np.unique(panel.lines):
        bars = by_line[line]
        columns = [
            np.array([getattr(b, n) for b in bars])
            for n in ("high", "low", "close", "volume")
        ]
        expected = line_features(
            *columns, np.array([context.spy_closes[b.date] for b in bars])
        )
        for row in np.flatnonzero(panel.lines == line):
            day = panel.sessions[row]
            pos = next(i for i, b in enumerate(bars) if b.date.isoformat() == day)
            assert panel.secondary[row] == (pos + 1 >= 253)
            if line == "L03" and day >= move.isoformat():
                assert np.isnan(panel.features[row]).all()
            else:
                np.testing.assert_allclose(
                    panel.features[row],
                    [expected[n][pos] for n in LINE_FEATURES],
                    equal_nan=True,
                )
            if line == "L03" and day < move.isoformat():
                assert np.isnan(panel.returns[row]).all()
