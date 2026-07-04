"""Offline LightGBM booster training (walk-forward split + artifact save).

Agent: forecaster
Role: sort label rows by date, split at a configurable train fraction, train a
      gradient-boosted regressor, and persist the booster artifact; the heavy
      lightgbm call is isolated behind # pragma: no cover so the unit gate never
      loads it.
External I/O: writes a trained booster artifact (lightgbm.Booster.save_model).
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from agents.forecaster.domain.statistics import pearson

if TYPE_CHECKING:
    from agents.forecaster.domain.return_labels import LabelRow

_FEATURE_NAMES = (
    "ret_short",
    "ret_mid",
    "ret_long",
    "volatility",
    "momentum",
    "volume_ratio",
)

_LGB_PARAMS = {
    "objective": "regression",
    "metric": "mae",
    "verbosity": -1,
    "num_leaves": 31,
}
_NUM_ROUNDS = 100


@dataclass(frozen=True)
class TrainingReport:
    """Summary of one offline training run."""

    train_size: int
    test_size: int
    oos_ic: float | None  # None when test set has fewer than 2 rows


def split_rows(
    rows: list[LabelRow], *, train_fraction: float
) -> tuple[list[LabelRow], list[LabelRow]]:
    """Sort by as_of_date (ISO sorts lexicographically) and split at train_fraction.

    At least one row goes into the train split when the list is non-empty.
    """
    if not rows:
        return [], []
    sorted_rows = sorted(rows, key=lambda r: r.as_of_date)
    n_train = max(1, int(len(sorted_rows) * train_fraction))
    return sorted_rows[:n_train], sorted_rows[n_train:]


def train_and_save(  # pragma: no cover
    label_rows: list[LabelRow],
    output_path: str,
    *,
    train_fraction: float = 0.7,
) -> TrainingReport:
    """Train a LightGBM booster on label_rows and save to output_path.

    Requires the optional ``forecaster`` dependency group (lightgbm>=4).
    All lightgbm I/O is in this function; everything else is pure Python.
    """
    lgb = importlib.import_module("lightgbm")
    np = importlib.import_module("numpy")
    train, test = split_rows(label_rows, train_fraction=train_fraction)
    x_train = np.asarray([r.features.as_vector() for r in train], dtype=float)
    y_train = [r.forward_return for r in train]
    x_test = np.asarray([r.features.as_vector() for r in test], dtype=float)
    y_test = [r.forward_return for r in test]
    dataset = lgb.Dataset(x_train, label=y_train, feature_name=list(_FEATURE_NAMES))
    booster = lgb.train(_LGB_PARAMS, dataset, num_boost_round=_NUM_ROUNDS)
    booster.save_model(output_path)
    preds = [float(p) for p in booster.predict(x_test)] if len(x_test) else []
    return TrainingReport(
        train_size=len(train),
        test_size=len(test),
        oos_ic=pearson(preds, y_test),
    )
