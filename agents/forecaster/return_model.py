"""Return-forecasting model port and deterministic fake.

Agent: forecaster
Role: define the price/return scoring boundary; isolate the heavy gradient-boosted
      model so the unit gate never imports lightgbm.
External I/O: none (the concrete lightgbm client lives in lightgbm_model.py).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable

    from agents.forecaster.domain.features import FeatureRow


class ReturnModel(Protocol):
    """Boundary for a price/return scorer over a feature row."""

    def predict(self, features: FeatureRow) -> float:
        """Return a raw expected-return score for the feature row."""
        ...  # pragma: no cover - protocol declaration only.


class FakeReturnModel:
    """Deterministic return scorer used by the unit gate."""

    def __init__(
        self,
        raw: float = 0.0,
        *,
        fn: Callable[[FeatureRow], float] | None = None,
    ) -> None:
        """Store a fixed raw score, or a function of the feature row."""
        self._raw = raw
        self._fn = fn

    def predict(self, features: FeatureRow) -> float:
        """Return the function's value if one was given, else the fixed score."""
        return self._fn(features) if self._fn is not None else self._raw
