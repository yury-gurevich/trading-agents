"""EXP-015's three models and their ensemble, at fixed settings (S289).

Agent: tooling
Role: fit the rank composite, the ridge and the LightGBM regressor on a train fold's
      ranked features, predict a test fold, and average the three ranks per session.
External I/O: none; LightGBM is imported only when the real trainer runs.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np
from scripts.exp015_ranks import group_ranks, session_ic
from scripts.exp015_spec import FEATURES, LGBM_PARAMS, LGBM_ROUNDS, RIDGE_LAMBDA


class Booster(Protocol):
    def predict(self, data: np.ndarray) -> np.ndarray: ...
    def feature_importance(self, importance_type: str) -> np.ndarray: ...


Trainer = Callable[[np.ndarray, np.ndarray], Booster]


@dataclass(frozen=True)
class Fitted:
    signs: np.ndarray  # the composite's sign per feature, by its train IC
    ridge_mean: np.ndarray
    ridge_beta: np.ndarray
    booster: Booster

    def predict(self, x: np.ndarray, sessions: np.ndarray) -> dict[str, np.ndarray]:
        """Each model's prediction, and the ensemble: the three ranks' mean."""
        models = {
            "composite": (x - 0.5) @ self.signs / len(self.signs),
            "ridge": (x - self.ridge_mean) @ self.ridge_beta,
            "lightgbm": np.asarray(self.booster.predict(x), dtype=float),
        }
        ranks = [group_ranks(value, sessions) for value in models.values()]
        return models | {"ensemble": np.mean(ranks, axis=0)}

    def importances(self) -> dict[str, float]:
        gains = self.booster.feature_importance("gain")
        return {name: float(gain) for name, gain in zip(FEATURES, gains, strict=True)}


def fit(
    x: np.ndarray, target: np.ndarray, sessions: np.ndarray, trainer: Trainer
) -> Fitted:
    """Fit the three on rows with a target; ridge and LightGBM learn its rank."""
    usable = np.isfinite(target)
    x, target, sessions = x[usable], target[usable], sessions[usable]
    signs = np.array([_sign(x[:, k], target, sessions) for k in range(x.shape[1])])
    y = group_ranks(target, sessions)
    mean = x.mean(axis=0)
    centred = x - mean
    gram = centred.T @ centred + RIDGE_LAMBDA * np.eye(x.shape[1])
    beta = np.linalg.solve(gram, centred.T @ (y - y.mean()))
    return Fitted(signs, mean, beta, trainer(x, y))


def _sign(feature: np.ndarray, target: np.ndarray, sessions: np.ndarray) -> float:
    """+1 when the feature's mean train IC is at least 0, else -1 (DL-313 D8)."""
    ics = list(session_ic(feature, target, sessions).values())
    return 1.0 if not ics or float(np.mean(ics)) >= 0.0 else -1.0


def lightgbm_trainer(x: np.ndarray, y: np.ndarray) -> Booster:
    """LightGBM's native API at LGBM_PARAMS for LGBM_ROUNDS rounds (no scikit-learn)."""
    import lightgbm  # the forecaster extra: CI never installs it, so import it here

    params: dict[str, Any] = dict(LGBM_PARAMS)
    dataset = lightgbm.Dataset(x, label=y, params={"verbosity": -1})
    booster: Booster = lightgbm.train(params, dataset, num_boost_round=LGBM_ROUNDS)
    return booster
