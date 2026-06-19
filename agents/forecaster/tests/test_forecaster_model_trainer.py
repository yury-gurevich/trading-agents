"""Model trainer split tests — the pure walk-forward logic.

Agent: forecaster
Role: verify split_rows sorts correctly and respects the train_fraction;
      train_and_save is # pragma: no cover so only the pure helpers are tested.
External I/O: none.
"""

from __future__ import annotations

from agents.forecaster.domain.features import FeatureRow
from agents.forecaster.domain.return_labels import LabelRow
from agents.forecaster.model_trainer import TrainingReport, split_rows

_ROW = FeatureRow(0.1, 0.2, 0.3, 0.4, 0.5, 0.6)


def _label(date: str, fwd: float = 0.01) -> LabelRow:
    return LabelRow("AAPL", date, _ROW, fwd)


def test_split_rows_empty_input() -> None:
    train, test = split_rows([], train_fraction=0.7)
    assert train == []
    assert test == []


def test_split_rows_single_row_goes_to_train() -> None:
    rows = [_label("2024-01-01")]
    train, test = split_rows(rows, train_fraction=0.7)
    assert len(train) == 1
    assert len(test) == 0


def test_split_rows_sorts_by_date() -> None:
    rows = [_label("2024-01-03"), _label("2024-01-01"), _label("2024-01-02")]
    train, _ = split_rows(rows, train_fraction=1.0)
    dates = [r.as_of_date for r in train]
    assert dates == sorted(dates)


def test_split_rows_respects_train_fraction() -> None:
    rows = [_label(f"2024-01-{i + 1:02d}") for i in range(10)]
    train, test = split_rows(rows, train_fraction=0.7)
    assert len(train) == 7
    assert len(test) == 3


def test_split_rows_train_contains_earliest_dates() -> None:
    rows = [_label(f"2024-01-{i + 1:02d}") for i in range(10)]
    train, test = split_rows(rows, train_fraction=0.7)
    assert max(r.as_of_date for r in train) < min(r.as_of_date for r in test)


def test_training_report_is_a_frozen_dataclass() -> None:
    report = TrainingReport(train_size=70, test_size=30, oos_ic=0.05)
    assert report.train_size == 70
    assert report.test_size == 30
    assert report.oos_ic == 0.05


def test_training_report_oos_ic_can_be_none() -> None:
    report = TrainingReport(train_size=1, test_size=0, oos_ic=None)
    assert report.oos_ic is None
