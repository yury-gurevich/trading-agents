"""EXP-018's barrier model, pure: GARCH(1,1)-t filtered historical simulation.

Agent: forecaster
Role: turn a stock's daily history, a stop, a target, fitted GARCH parameters and a
      seed into P(stop first), P(target first), P(neither) within 10 sessions, and
      apply EXP-018's fit-acceptance rule. Copied from the experiment's
      `exp018_sim.py` (EXP-018 Appendix S), not rewritten: the one change is that
      the variance filter is the same first-order recursion written as a loop,
      because the unit gate has no scipy (DL-241 D7: bit-identical to `lfilter`).
External I/O: none.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import numpy as np

if TYPE_CHECKING:
    from datetime import date

    from numpy.typing import NDArray

    Floats = NDArray[np.float64]

#: EXP-018's horizon `H`: the claim is about the next 10 sessions (the model's
#: definition, not a setting: another horizon is another model).
HORIZON_SESSIONS = 10
#: EXP-018's `PERSISTENCE_CAP`: alpha + beta above it is scaled down to it.
PERSISTENCE_CAP = 0.999
#: EXP-018's boundary tolerance: a fit fails only above alpha + beta = 1 + this.
BOUNDARY_TOLERANCE = 1e-9
BARRIER_MODEL_ID = "barrier-garch-v1"
#: Bumped when this module's arithmetic changes under the same model id.
BARRIER_MODEL_VERSION = "1.0.0"

FitStatus = Literal["accepted", "capped"]


@dataclass(frozen=True)
class RawGarchFit:
    """What the optimiser returned, before EXP-018's acceptance rule."""

    mu: float
    omega: float
    alpha: float
    beta: float
    converged: bool


@dataclass(frozen=True)
class GarchParams:
    """Parameters the rule accepted, as the simulation uses them."""

    mu: float
    omega: float
    alpha: float
    beta: float
    status: FitStatus

    def as_tuple(self) -> tuple[float, float, float, float]:
        """Return ``(mu, omega, alpha, beta)``, the experiment's ``params``."""
        return (self.mu, self.omega, self.alpha, self.beta)


def accept_fit(raw: RawGarchFit) -> GarchParams | None:
    """EXP-018's `garch_fit` rule: accepted, capped, or ``None`` (failed)."""
    mu, omega, alpha, beta = raw.mu, raw.omega, raw.alpha, raw.beta
    if (
        not raw.converged
        or omega <= 0
        or alpha < 0
        or beta < 0
        or alpha + beta > 1 + BOUNDARY_TOLERANCE
    ):
        return None
    if alpha + beta > PERSISTENCE_CAP:
        scale = PERSISTENCE_CAP / (alpha + beta)
        return GarchParams(mu, omega, alpha * scale, beta * scale, "capped")
    return GarchParams(mu, omega, alpha, beta, "accepted")


def daily_moves(
    highs: Floats, lows: Floats, closes: Floats
) -> tuple[Floats, Floats, Floats]:
    """Return ``(r, lh_pct, ll_pct)``, exactly as EXP-018's `run_name` built them.

    Each day's close, high and low as a percent log distance from the prior close.
    """
    rh, rl, rc = (
        highs[1:] / closes[:-1],
        lows[1:] / closes[:-1],
        closes[1:] / closes[:-1],
    )
    return 100 * np.log(rc), 100 * np.log(rh), 100 * np.log(rl)


def barrier_probs(
    prev: Floats, lh: Floats, ll: Floats, stop: float, target: float
) -> tuple[float, float, float]:
    """EXP-018's `barrier_probs`: first-touch shares, the low checked first."""
    hit_s = prev * ll <= 1 - stop
    hit_t = prev * lh >= 1 + target
    fs = np.where(hit_s.any(1), hit_s.argmax(1), HORIZON_SESSIONS)
    ft = np.where(hit_t.any(1), hit_t.argmax(1), HORIZON_SESSIONS)
    p_stop = float(np.mean((fs < HORIZON_SESSIONS) & (fs <= ft)))
    p_target = float(np.mean((ft < HORIZON_SESSIONS) & (ft < fs)))
    return (p_stop, p_target, 1 - p_stop - p_target)


def garch_path_probs(
    rng: np.random.Generator,
    params: tuple[float, float, float, float],
    r: Floats,
    lh_pct: Floats,
    ll_pct: Floats,
    lo: int,
    t: int,
    stop: float,
    target: float,
    *,
    n_paths: int,
) -> tuple[float, float, float]:
    """EXP-018's `garch_path_probs`, with `N_PATHS` as ``n_paths``."""
    mu, omega, alpha, beta = params
    seg = r[lo:t]
    s2_0 = seg.var()
    s2 = np.concatenate([[s2_0], _variance_filter(seg, mu, omega, alpha, beta, s2_0)])
    sig = np.sqrt(s2[:-1])
    z = (seg - mu) / sig
    uh, ul = lh_pct[lo:t] / sig, ll_pct[lo:t] / sig
    s2_next = np.full(n_paths, s2[-1])
    level = np.ones(n_paths)
    prev_all, hh, llw = (np.empty((n_paths, HORIZON_SESSIONS)) for _ in range(3))
    for k in range(HORIZON_SESSIONS):
        j = rng.integers(0, len(seg), n_paths)
        s = np.sqrt(s2_next)
        rr = mu + s * z[j]
        prev_all[:, k] = level
        hh[:, k] = np.exp(np.maximum(s * uh[j], rr) / 100)
        llw[:, k] = np.exp(np.minimum(s * ul[j], rr) / 100)
        level = level * np.exp(rr / 100)
        s2_next = omega + alpha * (rr - mu) ** 2 + beta * s2_next
    return barrier_probs(prev_all, hh, llw, stop, target)


def _variance_filter(
    seg: Floats, mu: float, omega: float, alpha: float, beta: float, s2_0: float
) -> Floats:
    """The experiment's ``lfilter`` call as a loop: y[n] = x[n] + beta * y[n-1].

    ``lfilter([1.0], [1.0, -beta], omega + alpha * (seg - mu) ** 2,
    zi=[beta * s2_0])[0]``, with y[-1] = s2_0; same operations in the same order.
    """
    x = omega + alpha * (seg - mu) ** 2
    out = np.empty(len(x))
    prev = s2_0
    for n, xn in enumerate(x):
        prev = xn + beta * prev
        out[n] = prev
    return out


def barrier_seed(ticker: str, as_of: date) -> int:
    """A seed stable across processes and machines, from ``ticker:as_of``.

    The first four bytes of its sha-256 (never Python's per-process salted ``hash``).
    """
    digest = hashlib.sha256(f"{ticker}:{as_of.isoformat()}".encode()).digest()
    return int.from_bytes(digest[:4], "big")
