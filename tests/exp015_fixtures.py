"""Synthetic inputs for EXP-015; no market cache or fitted model is read.

Agent: tooling
Role: seed bars, replay context, panels and a deterministic injected booster.
External I/O: none.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
from scripts.exp015_spec import FEATURES, LINE_FEATURES
from scripts.exp015_store import Panel
from scripts.replay_cache import ReplayContext
from scripts.replay_settings import build_effective_settings
from scripts.replay_universe_cache import Universe
from scripts.sp500_bars import BarRow
from scripts.sp500_membership import Episode

from contracts.provider import OHLCVBar


def weekdays(count, start=date(2016, 1, 4)):
    days = []
    while len(days) < count:
        if start.weekday() < 5:
            days.append(start)
        start += timedelta(days=1)
    return tuple(days)


def price_walk(count=300):
    rng = np.random.default_rng(289)
    close = 100 * np.exp(np.cumsum(rng.normal(0.001, 0.015, count)))
    high = close * (1 + rng.uniform(0.005, 0.04, count))
    low = close * (1 - rng.uniform(0.005, 0.04, count))
    volume = rng.integers(500_000, 2_000_000, count).astype(float)
    spy = 200 * np.exp(np.cumsum(rng.normal(0.0005, 0.01, count)))
    return high, low, close, volume, spy


class SignalBooster:
    def predict(self, data):
        return 7 * data[:, 0] + 3

    def feature_importance(self, importance_type):
        assert importance_type == "gain"
        return np.arange(len(FEATURES), dtype=float)


def trainer(x, y):
    assert len(x) == len(y) > 0
    assert np.isfinite(x).all()
    assert np.isfinite(y).all()
    return SignalBooster()


def planted_panel(days=None, names=16):
    if days is None:
        days = weekdays(60)
    rng = np.random.default_rng(289)
    size = len(days) * names
    features = rng.normal(size=(size, len(LINE_FEATURES)))
    signal = features[:, 0]
    target = 0.03 * signal + rng.normal(0, 0.001, size)
    returns = np.column_stack((target * 0.5, target, target * 2)) + 0.001
    return Panel(
        np.repeat([d.isoformat() for d in days], names),
        np.tile([f"L{i:02}" for i in range(names)], len(days)),
        np.tile(["tech", "health", "", ""] * ((names + 3) // 4), len(days))[:size],
        np.ones(size, dtype=bool),
        np.ones(size, dtype=bool),
        rng.normal(size=size),
        features,
        returns,
        np.full((size, 3), 0.001),
    )


def stage_panel():
    days = tuple(
        day for year in range(2016, 2021) for day in weekdays(80, date(year, 1, 4))
    )
    return planted_panel(days)


def replay_fixture():
    sessions = weekdays(300)
    rng = np.random.default_rng(289)
    spy_close = 200 * np.exp(np.cumsum(rng.normal(0.0002, 0.003, len(sessions))))
    benchmark = {
        day: OHLCVBar(
            ticker="SPY",
            bar_date=day,
            open=float(c * 0.998),
            high=float(c * 1.01),
            low=float(c * 0.99),
            close=float(c),
            volume=5_000_000,
        )
        for day, c in zip(sessions, spy_close, strict=True)
    }
    rows, episodes = [], []
    for i in range(32):
        line = f"L{i:02}"
        first = 3 if i == 2 else 150 if i == 31 else 0
        closes = (2 if i == 1 else 50 + i) * np.exp(
            np.cumsum(rng.normal(0.001, 0.0004, len(sessions)))
        )
        episodes.append(
            Episode(
                line,
                line,
                sessions[252] if i == 29 else sessions[0],
                sessions[253] if i == 30 else sessions[-1],
            )
        )
        rows.extend(
            BarRow(
                line,
                line,
                day,
                float(c * 0.998),
                float(c * 1.01),
                float(c * 0.99),
                float(c),
                10 if i == 0 else 2_000_000,
            )
            for day, c in zip(sessions[first:], closes[first:], strict=True)
        )
    universe = Universe(sessions, tuple(episodes), tuple(rows), {})
    sectors = {f"L{i:02}": "tech" for i in range(32) if i != 4}
    context = ReplayContext(
        universe, benchmark, {d: b.close for d, b in benchmark.items()}, {}, sectors
    )
    return context, build_effective_settings(()), sessions[250:256]


def fold_record(name, difference, count=30):
    days = [f"{int(name) + 2010}-01-{i + 1:02}" for i in range(count)]
    return {
        "ic": {
            "ensemble": dict.fromkeys(days, difference),
            "baseline": dict.fromkeys(days, 0.0),
        },
        "top_decile": {
            "ensemble": {"net_return": 0.1},
            "baseline": {"net_return": 0.0},
        },
    }
