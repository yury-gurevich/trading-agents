"""The barrier test bed rebuilds EXP-011's decisions and scores as EXP-016-018 did.

Agent: tooling
Role: prove the outcome rule, the barriers, the decision cadence, the baselines and
      the scorer on synthetic bars small enough to check by hand.
External I/O: none.
"""

from __future__ import annotations

import numpy as np
import pytest
from scripts import barrier_testbed as tb
from scripts import barrier_testbed_models as md
from scripts import barrier_testbed_score as sc


def _flat(n: int, close: float = 100.0) -> list[tuple[str, float, float, float, float]]:
    """n sessions from 2016-01-01 with a 1 % daily range around a constant close."""
    start = np.datetime64("2016-01-01")
    return [
        (str(start + i), close, close * 1.01, close * 0.99, close) for i in range(n)
    ]


def _arrays(rows):
    return tuple(np.array([r[k] for r in rows]) for k in (2, 3, 4))


def test_outcome_checks_the_low_before_the_high() -> None:
    """A session touching both levels counts as stop first (EXP-011's rule)."""
    rows = _flat(20)
    hi, lo, cl = _arrays(rows)
    lo[6], hi[6] = 90.0, 120.0
    assert tb.outcome(hi, lo, cl, 5, 0.05, 0.05) == 0


def test_outcome_target_first_and_neither() -> None:
    rows = _flat(20)
    hi, lo, cl = _arrays(rows)
    hi[8] = 106.0
    assert tb.outcome(hi, lo, cl, 5, 0.05, 0.05) == 1
    hi, lo, cl = _arrays(rows)
    assert tb.outcome(hi, lo, cl, 5, 0.05, 0.05) == 2


def test_outcome_ignores_the_session_after_the_horizon() -> None:
    rows = _flat(30)
    hi, lo, cl = _arrays(rows)
    lo[5 + tb.H + 1] = 50.0
    assert tb.outcome(hi, lo, cl, 5, 0.05, 0.05) == 2


def test_barriers_clamp_the_stop_and_take_the_median_excursion() -> None:
    rows = _flat(200)
    hi, lo, cl = _arrays(rows)
    stop, target = tb.barriers(hi, lo, cl, 190)
    assert stop == pytest.approx(
        0.04
    )  # true range 2 % of the close, 2 x ATR = 4 %, inside the clamp
    assert target == pytest.approx(0.01)


def test_barriers_cap_a_wild_stop_at_eight_percent() -> None:
    rows = [(d, o, c * 1.2, c * 0.8, c) for d, o, _h, _l, c in _flat(200)]
    hi, lo, cl = _arrays(rows)
    stop, _target = tb.barriers(hi, lo, cl, 190)
    assert stop == pytest.approx(0.08)


def test_decisions_follow_the_cadence_history_and_vix_rules() -> None:
    rows = _flat(700)
    days = [r[0] for r in rows]
    vix = {d: 14.0 for d in days if d != days[400]}
    decisions = tb.build_decisions({"AAA": rows}, vix)
    chosen = [d.day for d in decisions]
    first = days.index(tb.FIRST_DECISION)
    expected = [
        days[i]
        for i in range(first, len(days), tb.STEP)
        if i >= tb.MIN_HISTORY and i + tb.H < len(days) and days[i] in vix
    ]
    assert chosen == expected
    assert all(d.regime == 0 for d in decisions)


def test_regime_labels_follow_the_provider_thresholds() -> None:
    assert [tb.regime_label(v) for v in (12, 15, 18, 20, 25, 35)] == [0, 0, 1, 2, 3, 4]


def test_climatology_uses_only_earlier_years() -> None:
    mk = lambda day, o: tb.Decision("A", day, 0, 0.05, 0.05, o, 0)  # noqa: E731
    early = [mk("2017-01-02", 0)] * 600
    late = [mk("2018-01-02", 1)] * 10
    clim = tb.climatology(early + late)
    assert clim[-1].tolist() == [1.0, 0.0, 0.0]
    assert clim[0].tolist() == [1.0, 0.0, 0.0]  # first year falls back to the first 500


def test_bootstrap_is_seeded_and_sums_to_one() -> None:
    rows = _flat(300)
    a = md.bootstrap_probs(rows, 290, 0.05, 0.05, np.random.default_rng(1), n_paths=200)
    b = md.bootstrap_probs(rows, 290, 0.05, 0.05, np.random.default_rng(1), n_paths=200)
    assert a == b
    assert sum(a) == pytest.approx(1.0)
    assert a == (0.0, 0.0, 1.0)  # a flat 1 % range never reaches a 5 % barrier


def test_bootstrap_hits_the_target_on_a_rising_history() -> None:
    start = np.datetime64("2016-01-01")
    closes = [100 * 1.02**i for i in range(300)]
    rows = [(str(start + i), c, c * 1.01, c * 0.999, c) for i, c in enumerate(closes)]
    probs = md.bootstrap_probs(
        rows, 290, 0.05, 0.02, np.random.default_rng(2), n_paths=100
    )
    assert probs == (0.0, 1.0, 0.0)


def test_scorer_brier_skill_and_calibration() -> None:
    y = np.eye(3)[[0, 1, 2, 1]]
    perfect = y.copy()
    flat = np.full((4, 3), 1 / 3)
    assert sc.brier_losses(perfect, y).tolist() == [0.0, 0.0, 0.0, 0.0]
    assert sc.brier_losses(flat, y).mean() == pytest.approx(2 / 3)
    assert sc.skill(
        sc.brier_losses(perfect, y), sc.brier_losses(flat, y)
    ) == pytest.approx(1.0)
    cells = sc.calibration(
        np.array([0.05, 0.06, 0.95, 0.97]), np.array([0, 0, 1, 1]), min_n=2
    )
    assert cells == [(0.055, 0.0, 2), (0.96, 1.0, 2)]


def test_date_resampled_interval_is_reproducible_and_brackets_the_point() -> None:
    dates = np.array(["d1", "d1", "d2", "d3", "d3", "d4"])
    loss = np.array([0.1, 0.3, 0.2, 0.9, 0.7, 0.4])
    draws = sc.date_draws(dates, 200, seed=7)
    assert len(draws) == 200
    lo, hi = sc.interval(lambda s: loss[s].mean(), draws)
    assert lo <= loss.mean() <= hi
    assert (lo, hi) == sc.interval(
        lambda s: loss[s].mean(), sc.date_draws(dates, 200, seed=7)
    )


def test_reproduce_reports_a_mismatch(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    rows = _flat(700)
    monkeypatch.setattr(
        tb, "_load_cache", lambda: ({r[0]: 14.0 for r in rows}, {"AAA": rows})
    )
    assert tb.main(["--reproduce"]) == 1
    assert "MISMATCH" in capsys.readouterr().out
