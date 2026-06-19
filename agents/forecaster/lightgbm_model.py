"""LightGBM-backed return model (heavy ML, optional, lazily imported).

Agent: forecaster
Role: real price/return scoring via a trained gradient-boosted booster behind the
      ReturnModel port.
External I/O: loads a trained lightgbm Booster artifact (the optional ``forecaster``
              dependency group); imported lazily so the unit gate never pulls in
              lightgbm or numpy.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.forecaster.domain.features import FeatureRow


class ConfigurationError(RuntimeError):
    """Raised when the LightGBM model cannot be constructed."""


class LightGBMModel:
    """A trained lightgbm Booster behind the return-model port."""

    def __init__(self, *, model_path: str) -> None:
        """Load the trained booster, failing early if lightgbm is absent."""
        try:
            lightgbm = importlib.import_module("lightgbm")
        except ModuleNotFoundError as exc:
            raise ConfigurationError("lightgbm is not installed") from exc
        self._booster = lightgbm.Booster(model_file=model_path)  # pragma: no cover

    def predict(self, features: FeatureRow) -> float:
        """Score the feature row with the trained booster."""
        prediction = self._booster.predict(  # pragma: no cover
            [list(features.as_vector())]
        )
        return float(prediction[0])  # pragma: no cover
