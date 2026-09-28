"""S239 A1 / A3: the barrier simulation and EXP-018's fit-acceptance rule, pure.

Agent: forecaster
Role: prove the three probabilities sum to 1 and point the right way on rising,
      falling and flat histories, that a session touching both barriers counts as
      the stop, and that a fit is accepted, capped or failed exactly as EXP-018 did.
External I/O: none.
"""

from __future__ import annotations

import numpy as np
import pytest

from agents.forecaster.domain.barrier_garch import (
    HORIZON_SESSIONS,
    PERSISTENCE_CAP,
    GarchParams,
    RawGarchFit,
    accept_fit,
    barrier_probs,
    garch_path_probs,
)


def _moves(mean: float, count: int = 759) -> tuple[np.ndarray, ...]:
    """Daily moves in percent around ``mean`` with a small bounded wiggle."""
    wiggle = 0.3 * np.sin(np.arange(count) * 1.37)
    r = mean + wiggle
    return r, np.maximum(r, 0.0) + 0.2, np.minimum(r, 0.0) - 0.2


def _simulate(mean: float, stop: float, target: float) -> tuple[float, float, float]:
    r, lh, ll = _moves(mean)
    params = (mean, 0.01, 0.05, 0.90)
    return garch_path_probs(
        np.random.default_rng(7),
        params,
        r,
        lh,
        ll,
        0,
        len(r),
        stop,
        target,
        n_paths=1000,
    )


def test_a_rising_history_reaches_the_target_first() -> None:
    """FORE-OUT-07: +1 %/day drift, a 3 % target and a 5 % stop: target first."""
    p_stop, p_target, p_neither = _simulate(1.0, stop=0.05, target=0.03)
    assert p_target == pytest.approx(1.0, abs=0.01)
    assert p_stop + p_target + p_neither == pytest.approx(1.0, abs=1e-12)


def test_a_falling_history_reaches_the_stop_first() -> None:
    """FORE-OUT-07: -1 %/day drift, a 3 % stop and a 20 % target: stop first."""
    p_stop, p_target, p_neither = _simulate(-1.0, stop=0.03, target=0.20)
    assert p_stop == pytest.approx(1.0, abs=0.01)
    assert p_stop + p_target + p_neither == pytest.approx(1.0, abs=1e-12)


def test_a_flat_history_with_wide_barriers_reaches_neither() -> None:
    """FORE-OUT-07: no drift, tiny variance, 20 % barriers: neither within 10."""
    p_stop, p_target, p_neither = _simulate(0.0, stop=0.20, target=0.20)
    assert p_neither == pytest.approx(1.0, abs=0.01)
    assert (p_stop, p_target) == (0.0, 0.0)


def test_a_session_touching_both_barriers_counts_as_the_stop() -> None:
    """FORE-OUT-07: the low is checked before the high within a session."""
    shape = (4, HORIZON_SESSIONS)
    prev = np.ones(shape)
    high = np.ones(shape)
    low = np.ones(shape)
    high[:, 2] = 1.10  # every path touches +10 % on its third session ...
    low[:, 2] = 0.90  # ... and -10 % on the same session
    assert barrier_probs(prev, high, low, 0.05, 0.05) == (1.0, 0.0, 0.0)


def test_the_earlier_session_wins_whichever_barrier_it_is() -> None:
    """FORE-OUT-07: a target on session 1 beats a stop on session 2."""
    shape = (2, HORIZON_SESSIONS)
    prev, high, low = np.ones(shape), np.ones(shape), np.ones(shape)
    high[:, 1] = 1.06
    low[:, 2] = 0.94
    assert barrier_probs(prev, high, low, 0.05, 0.05) == (0.0, 1.0, 0.0)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            RawGarchFit(mu=0.01, omega=0.05, alpha=0.05, beta=0.90, converged=True),
            GarchParams(0.01, 0.05, 0.05, 0.90, "accepted"),
        ),
        (
            RawGarchFit(mu=0.01, omega=0.05, alpha=0.1, beta=0.9, converged=True),
            GarchParams(0.01, 0.05, 0.1 * 0.999, 0.9 * 0.999, "capped"),
        ),
        (
            RawGarchFit(mu=0.0, omega=0.02, alpha=0.3, beta=0.6995, converged=True),
            GarchParams(
                0.0,
                0.02,
                0.3 * (0.999 / (0.3 + 0.6995)),
                0.6995 * (0.999 / (0.3 + 0.6995)),
                "capped",
            ),
        ),
    ],
)
def test_a_fit_is_accepted_or_capped_as_exp018_did(
    raw: RawGarchFit, expected: GarchParams
) -> None:
    """FORE-FAIL-04 / FORE-OUT-07: alpha + beta <= 1 is accepted; above 0.999 both
    scale in proportion so they sum to 0.999 (status capped), as in EXP-018."""
    params = accept_fit(raw)
    assert params == expected
    assert params is not None
    assert params.alpha + params.beta <= PERSISTENCE_CAP + 1e-12


def test_the_boundary_tolerance_is_exp018s() -> None:
    """FORE-FAIL-04: EXP-018 failed a fit only above alpha + beta = 1 + 1e-9."""
    inside = RawGarchFit(mu=0.0, omega=0.1, alpha=0.2, beta=0.8 + 5e-10, converged=True)
    outside = RawGarchFit(mu=0.0, omega=0.1, alpha=0.2, beta=0.8 + 1e-8, converged=True)
    capped = accept_fit(inside)
    assert capped is not None
    assert capped.status == "capped"
    assert accept_fit(outside) is None


@pytest.mark.parametrize(
    "raw",
    [
        RawGarchFit(mu=0.0, omega=0.05, alpha=0.2, beta=0.85, converged=True),
        RawGarchFit(mu=0.0, omega=0.05, alpha=0.05, beta=0.90, converged=False),
        RawGarchFit(mu=0.0, omega=0.0, alpha=0.05, beta=0.90, converged=True),
        RawGarchFit(mu=0.0, omega=-0.1, alpha=0.05, beta=0.90, converged=True),
        RawGarchFit(mu=0.0, omega=0.05, alpha=-0.01, beta=0.90, converged=True),
        RawGarchFit(mu=0.0, omega=0.05, alpha=0.05, beta=-0.01, converged=True),
    ],
    ids=[
        "persistence-above-1",
        "not-converged",
        "omega-0",
        "omega-neg",
        "alpha-neg",
        "beta-neg",
    ],
)
def test_every_other_fit_fails(raw: RawGarchFit) -> None:
    """FORE-FAIL-04: not converged, omega <= 0, a negative alpha or beta, or
    alpha + beta above 1 is a failed fit: no parameters come back."""
    assert accept_fit(raw) is None


def test_the_simulation_reads_only_the_segment_it_is_given() -> None:
    """FORE-OUT-07: moves outside [lo, t) never enter the simulation."""
    r, lh, ll = _moves(0.1, count=120)
    poisoned = r.copy()
    poisoned[:10] = 50.0
    poisoned[-5:] = -50.0
    params = (0.1, 0.02, 0.05, 0.9)
    clean = garch_path_probs(
        np.random.default_rng(3), params, r, lh, ll, 10, 115, 0.04, 0.04, n_paths=500
    )
    dirty = garch_path_probs(
        np.random.default_rng(3),
        params,
        poisoned,
        lh,
        ll,
        10,
        115,
        0.04,
        0.04,
        n_paths=500,
    )
    assert clean == dirty
