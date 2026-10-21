"""Sprint 288 A1-A3: literal return arithmetic and EXP-018's frozen paths.

Agent: forecaster
Role: pin first touches, the unbarriered tail and unchanged probabilities.
External I/O: reads the frozen experiment through its existing local oracle.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from agents.forecaster.domain import barrier_garch
from agents.forecaster.tests import test_barrier_garch_oracle as oracle
from agents.forecaster.tests.test_barrier_garch_oracle import experiment as experiment


def test_the_figures_are_the_return_to_the_first_barrier_or_the_tenth_close() -> None:
    """FORE-OUT-11: the four paths yield -0.005, tail -0.064 and sessions 5/2.5."""
    from agents.forecaster.domain.barrier_returns import barrier_returns

    prev = np.ones((4, 10))
    high, low = np.full((4, 10), 1.01), np.full((4, 10), 0.99)
    low[0, 2] = 0.94
    high[1, 4] = 1.07
    high[2, 1], low[2, 1] = 1.07, 0.94
    last = np.array([0.93, 1.07, 0.97, 1.02])

    figures = barrier_returns((prev, high, low, last), 0.05, 0.06)

    assert figures.expected_return == pytest.approx((-0.05 + 0.06 - 0.05 + 0.02) / 4)
    assert figures.sessions_to_stop == 2.5
    assert figures.sessions_to_target == 5.0
    assert figures.close_return_p05 == pytest.approx(-0.07 + 0.15 * 0.04)


def test_with_no_touch_a_barriers_sessions_are_absent() -> None:
    """FORE-OUT-11: quiet paths average -0.01; untouched sessions are None."""
    from agents.forecaster.domain.barrier_returns import barrier_returns

    figures = barrier_returns(
        (
            np.ones((2, 10)),
            np.full((2, 10), 1.01),
            np.full((2, 10), 0.99),
            np.array([1.01, 0.97]),
        ),
        0.05,
        0.06,
    )
    assert figures.sessions_to_target is None
    assert figures.sessions_to_stop is None
    assert figures.expected_return == pytest.approx(-0.01)


@pytest.mark.parametrize(
    "case", oracle.GOLDEN, ids=["full-760", "capped-like", "lo-t-slice"]
)
def test_the_paths_are_exp018s_own(
    case: tuple[Any, ...],
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FORE-OUT-07 / FORE-OUT-11: all four arrays and golden probabilities match."""
    count, drift, params, stop, target, seed, lo, trim, golden = case
    source = oracle._experiment_source()
    final = "return barrier_probs(prev_all, hh, llw, stop, target)"
    assert source.count(final) == 1
    source = source.replace(final, "return prev_all, hh, llw, level")
    monkeypatch.setattr(oracle, "_experiment_source", lambda: source)
    reference = request.getfixturevalue("experiment")
    r, lh, ll = oracle._inputs(count, drift)
    t = len(r) - trim
    theirs = reference.garch_path_probs(
        np.random.default_rng(seed), params, r, lh, ll, lo, t, stop, target
    )
    ours = barrier_garch.garch_paths(
        np.random.default_rng(seed), params, r, lh, ll, lo, t, n_paths=1000
    )
    assert len(ours) == len(theirs) == 4
    for actual, expected in zip(ours, theirs, strict=True):
        assert np.array_equal(actual, expected)
    assert barrier_garch.barrier_probs(*ours[:3], stop, target) == golden
    assert (
        barrier_garch.garch_path_probs(
            np.random.default_rng(seed),
            params,
            r,
            lh,
            ll,
            lo,
            t,
            stop,
            target,
            n_paths=1000,
        )
        == golden
    )
