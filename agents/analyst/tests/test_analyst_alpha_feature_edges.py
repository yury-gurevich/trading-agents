"""Alpha158 edge-window assertions for mutation hardening.

Agent: analyst
Role: pin feature windows where adjacent return slices differ.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from agents.analyst.domain.alpha_features import compute_alpha_features
from contracts.provider import OHLCVBar


def _bars_from_returns(returns: list[float]) -> tuple[OHLCVBar, ...]:
    closes = [100.0]
    for daily_return in returns:
        closes.append(closes[-1] * (1.0 + daily_return))
    base = datetime.now(tz=UTC).date() - timedelta(days=len(closes))
    return tuple(
        OHLCVBar(
            ticker="TEST",
            bar_date=base + timedelta(days=index),
            open=close,
            high=close,
            low=close,
            close=close,
            volume=1000,
        )
        for index, close in enumerate(closes)
    )


def test_alpha_feature_extrema_use_exact_return_windows() -> None:
    """Kills compute_alpha_features mutmut_14, 16, 128, 130, 132, and 134."""
    returns = [0.01] * 61
    returns[0] = 0.90
    returns[1] = -0.95
    returns[-21] = 0.80
    returns[-11] = 0.70
    returns[-6] = -0.50

    row = compute_alpha_features(_bars_from_returns(returns))

    assert row is not None
    assert row.max_10 == pytest.approx(0.01, abs=1e-12)
    assert row.max_20 == pytest.approx(0.70, abs=1e-12)
    assert row.max_60 == pytest.approx(0.80, abs=1e-12)
    assert row.min_5 == pytest.approx(0.01, abs=1e-12)
    assert row.min_60 == pytest.approx(-0.95, abs=1e-12)
