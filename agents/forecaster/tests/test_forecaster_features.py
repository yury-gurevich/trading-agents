"""Price feature engineering tests.

Agent: forecaster
Role: verify no-lookahead feature construction, the squash, and confidence.
External I/O: none.
"""

from __future__ import annotations

import math

import pytest

from agents.forecaster.domain.features import (
    FeatureRow,
    build_features,
    confidence_from_history,
    squash,
)

_HORIZONS = (1, 2, 3)


def _features(
    closes: tuple[float, ...], volumes: tuple[float, ...]
) -> FeatureRow | None:
    return build_features(
        closes, volumes, horizons=_HORIZONS, volatility_window=2, momentum_window=3
    )


def test_build_features_known_values() -> None:
    closes = (10.0, 10.0, 10.0, 10.0, 10.0, 20.0)
    volumes = (1.0, 1.0, 1.0, 1.0, 1.0, 4.0)
    row = _features(closes, volumes)
    assert row is not None
    assert row.as_vector() == pytest.approx((1.0, 1.0, 1.0, 0.5, 0.5, 1.0))


def test_build_features_returns_none_on_short_history() -> None:
    assert _features((10.0, 10.0, 10.0), (1.0, 1.0, 1.0)) is None


def test_volume_ratio_is_zero_when_recent_volume_is_zero() -> None:
    closes = (10.0, 10.0, 10.0, 10.0, 10.0, 20.0)
    row = _features(closes, (0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    assert row is not None
    assert row.volume_ratio == 0.0


def test_as_vector_preserves_canonical_order() -> None:
    row = FeatureRow(0.1, 0.2, 0.3, 0.4, 0.5, 0.6)
    assert row.as_vector() == (0.1, 0.2, 0.3, 0.4, 0.5, 0.6)


def test_squash_is_centred_and_monotone() -> None:
    assert squash(0.0, scale=0.05) == 0.5
    assert squash(0.1, scale=0.05) > squash(0.0, scale=0.05)
    assert squash(0.0, scale=0.05) > squash(-0.1, scale=0.05)
    assert squash(1.0, scale=1.0) == pytest.approx(1.0 / (1.0 + math.exp(-1.0)))


def test_confidence_from_history_fills_then_caps() -> None:
    assert confidence_from_history(30, full_confidence_bars=60) == 0.5
    assert confidence_from_history(120, full_confidence_bars=60) == 1.0
