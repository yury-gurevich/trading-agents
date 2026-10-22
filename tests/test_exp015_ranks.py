"""S289-A5 through A8: ranks, IC and the sessions on each side of a fold.

Agent: tooling
Role: check rank ties, absent sectors, IC eligibility and purged date ranges.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pytest
from scripts.exp015_folds import holdout, walk_forward
from scripts.exp015_ranks import group_ranks, ranked_features, session_ic
from scripts.exp015_spec import FEATURES, LINE_FEATURES
from tests.exp015_fixtures import planted_panel, weekdays


def test_a5_ranks_within_groups():
    """S289-A5: averaged ties scaled to [0,1], NaN and singleton at 0.5."""
    values = np.array([30, 10, 10, 50, np.nan, 7, 8, np.nan])
    groups = np.array(["a", "a", "a", "a", "a", "b", "c", "d"])
    np.testing.assert_allclose(
        group_ranks(values, groups), [2 / 3, 1 / 6, 1 / 6, 1, 0.5, 0.5, 0.5, 0.5]
    )
    np.testing.assert_array_equal(
        group_ranks(np.full(3, np.nan), np.array(["a"] * 3)), [0.5] * 3
    )


def test_a6_twenty_features_and_sector_ranks():
    """S289-A6: literal column order; session ranks, sector ranks, absent sector."""
    panel = planted_panel(weekdays(3), names=8)
    got = ranked_features(panel)
    expected = (
        "ret_5",
        "ret_20",
        "ret_60",
        "ret_120",
        "ret_252_21",
        "dist_252_high",
        "vol_20",
        "vol_60",
        "atr_pct",
        "beta_60",
        "resvol_60",
        "volratio_5_60",
        "volratio_20_120",
        "dollar_volume",
        "rs_120",
        "sector_ret_5",
        "sector_ret_20",
        "sector_ret_60",
        "sector_ret_120",
        "sector_ret_252_21",
    )
    assert expected == FEATURES
    assert got.shape == (24, 20)
    for day in np.unique(panel.sessions):
        rows = np.flatnonzero(panel.sessions == day)
        for k in range(len(LINE_FEATURES)):
            order = rows[np.argsort(panel.features[rows, k])]
            np.testing.assert_allclose(got[order, k], np.arange(8) / 7)
        for sector in ("tech", "health"):
            members = rows[panel.sectors[rows] == sector]
            for k in range(5):
                order = members[np.argsort(panel.features[members, k])]
                np.testing.assert_allclose(got[order, 15 + k], [0, 1])
    np.testing.assert_array_equal(got[panel.sectors == "", 15:], 0.5)


def test_a7_per_session_rank_ic():
    """S289-A7: +1 and -1 orders; nine names and flat predictions have no IC."""
    days = np.repeat(["same", "reverse", "short", "flat"], [12, 12, 9, 12])
    target = np.concatenate([np.arange(n) for n in (12, 12, 9, 12)])
    prediction = np.r_[np.arange(12), np.arange(12)[::-1], np.arange(9), np.ones(12)]
    got = session_ic(prediction, target, days)
    assert got == pytest.approx({"same": 1, "reverse": -1})
    assert session_ic(np.array([np.nan]), np.array([1.0]), np.array(["none"])) == {}


def test_a8_folds_purge_embargo_and_holdout():
    """S289-A8: expanding train stops at test index minus 16; holdout to last."""
    sessions = weekdays(1300)
    folds = walk_forward(sessions, (2018, 2019, 2020))
    for fold in folds:
        start = next(
            i for i, day in enumerate(sessions) if day.isoformat() == fold.test[0]
        )
        assert fold.train == tuple(d.isoformat() for d in sessions[: start - 15])
        assert fold.train[-1] == sessions[start - 16].isoformat()
        assert fold.train[0] == "2016-01-04"
        assert all(d.startswith(fold.name) for d in fold.test)
        assert fold.record()["train_sessions"] == len(fold.train)
    assert len(folds[0].train) < len(folds[1].train) < len(folds[2].train)
    held = holdout(sessions, date(2020, 1, 2))
    assert held.test[0] == "2020-01-02"
    assert held.test[-1] == sessions[-1].isoformat()
    start = sessions.index(date(2020, 1, 2))
    assert held.train[-1] == sessions[start - 16].isoformat()
    with pytest.raises(ValueError, match="no session"):
        walk_forward(sessions, (2025,))
