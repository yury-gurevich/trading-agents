"""Evaluation CLI helper tests.

Agent: tooling
Role: verify the pure helper surface behind scripts/evaluate_return_model.py.
External I/O: temporary CSV fixture only.
"""

from __future__ import annotations

import argparse

import pytest
from scripts.evaluate_return_model import (
    build_report,
    evaluate_label_rows,
    parse_horizons,
    render_markdown_table,
)
from scripts.price_csv import load_price_csv

from agents.forecaster.domain.features import FeatureRow
from agents.forecaster.domain.return_labels import LabelRow


class _FeatureScoreModel:
    def predict(self, features):
        return features.ret_short


def _label(
    ticker: str,
    date: str,
    score: float,
    forward_return: float,
) -> LabelRow:
    features = FeatureRow(score, 0.0, 0.0, 0.0, 0.0, 0.0)
    return LabelRow(ticker, date, features, forward_return)


def _rows() -> list[LabelRow]:
    return [
        _label("A", "2024-01-01", -0.2, -0.01),
        _label("B", "2024-01-01", 0.2, 0.01),
        _label("A", "2024-01-02", -0.2, -0.01),
        _label("B", "2024-01-02", 0.2, 0.01),
        _label("A", "2024-01-03", -0.2, -0.01),
        _label("B", "2024-01-03", 0.2, 0.01),
        _label("A", "2024-01-04", -0.2, -0.01),
        _label("B", "2024-01-04", 0.2, 0.01),
    ]


def test_parse_horizons_accepts_comma_lists() -> None:
    assert parse_horizons("1, 5,10") == (1, 5, 10)


@pytest.mark.parametrize("raw", ["", "1,,5", "0,5", "x"])
def test_parse_horizons_rejects_invalid_lists(raw: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        parse_horizons(raw)


def test_load_price_csv_sorts_each_ticker(tmp_path) -> None:
    csv_path = tmp_path / "price_cache.csv"
    csv_path.write_text(
        "date,ticker,close,volume\n"
        "2024-01-02,AAPL,11,100\n"
        "2024-01-01,AAPL,10,90\n"
        "2024-01-01,MSFT,20,50\n"
    )

    bars = load_price_csv(str(csv_path))

    assert bars["AAPL"] == [("2024-01-01", 10.0, 90.0), ("2024-01-02", 11.0, 100.0)]
    assert bars["MSFT"] == [("2024-01-01", 20.0, 50.0)]


def test_evaluate_label_rows_defaults_to_test_split_only() -> None:
    metrics = evaluate_label_rows(
        _rows(),
        _FeatureScoreModel(),
        train_fraction=0.5,
        quantiles=2,
        include_in_sample=False,
    )

    assert metrics["complete_cases"] == 4.0
    assert metrics["hit_rate"] == 1.0
    assert metrics["stability_pairs"] == 1.0
    assert metrics["stability_mean"] == pytest.approx(1.0)
    assert "ic_ir" not in metrics


def test_evaluate_label_rows_can_loudly_include_in_sample_rows() -> None:
    metrics = evaluate_label_rows(
        _rows(),
        _FeatureScoreModel(),
        train_fraction=0.5,
        quantiles=2,
        include_in_sample=True,
    )

    assert metrics["complete_cases"] == 8.0
    assert metrics["stability_pairs"] == 3.0


def test_build_report_assembles_horizon_payload() -> None:
    bars = {
        "A": [(f"2024-01-{i + 1:02d}", 100.0 + i, 100.0) for i in range(25)],
        "B": [(f"2024-01-{i + 1:02d}", 200.0 + i, 100.0) for i in range(25)],
    }

    report = build_report(
        bars,
        _FeatureScoreModel(),
        model_path="models/lgbm-return-v1.txt",
        horizons=(1,),
        train_fraction=0.5,
        quantiles=2,
        include_in_sample=False,
        generated_at="2026-07-04T00:00:00+00:00",
    )

    assert report["model"] == "models/lgbm-return-v1.txt"
    assert report["in_sample"] is False
    assert report["generated_at"] == "2026-07-04T00:00:00+00:00"
    assert report["horizons"]["1"]["complete_cases"] == 4.0


def test_render_markdown_table_formats_headline_metrics() -> None:
    text = render_markdown_table(
        {
            "horizons": {
                "5": {
                    "complete_cases": 3.0,
                    "ic": 0.123456,
                    "hit_rate": 1.0,
                }
            }
        }
    )

    assert "| horizon | cases | ic | rank_ic |" in text
    assert "| 5 | 3 | 0.1235 | N/A | N/A | 1.0000 |" in text
