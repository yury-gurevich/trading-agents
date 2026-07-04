"""Offline return-model evaluation battery over price_cache CSV exports.

Agent: tooling
Role: rebuild LightGBM return predictions from price_cache bars and report a
      multi-horizon signal-evaluation battery.
External I/O: filesystem (CSV/model/report) and optional lightgbm booster load.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

# Keep sys.path clean: run from the repo root so the package is importable.
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.price_csv import load_price_csv

from agents.forecaster.domain.evaluation import (
    DEFAULT_QUANTILES,
    ic_series_metrics,
    rank_autocorrelation,
)
from agents.forecaster.domain.return_labels import build_label_rows
from agents.forecaster.domain.return_scorecard import (
    ReturnObservation,
    return_scorecard_metrics,
)
from agents.forecaster.lightgbm_model import LightGBMModel
from agents.forecaster.model_trainer import split_rows

if TYPE_CHECKING:
    from agents.forecaster.domain.return_labels import LabelRow
    from agents.forecaster.return_model import ReturnModel

MetricMap = dict[str, float]
Report = dict[str, object]

DEFAULT_EVAL_HORIZONS = (1, 5, 10, 20)
_FEATURE_HORIZONS = (1, 5, 20)
_VOLATILITY_WINDOW = 20
_MOMENTUM_WINDOW = 20
_HEADLINE_COLUMNS = (
    ("cases", "complete_cases"),
    ("ic", "ic"),
    ("rank_ic", "rank_ic"),
    ("ic_ir", "ic_ir"),
    ("hit_rate", "hit_rate"),
    ("top_bottom_spread", "top_bottom_spread"),
    ("monotonic_fraction", "monotonic_fraction"),
    ("stability_mean", "stability_mean"),
)


def parse_horizons(raw: str) -> tuple[int, ...]:
    """Parse a comma-separated positive-horizon list."""
    parts = [part.strip() for part in raw.split(",")]
    if not parts or any(part == "" for part in parts):
        raise argparse.ArgumentTypeError("horizons must be comma-separated integers")
    try:
        horizons = tuple(int(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "horizons must be comma-separated integers"
        ) from exc
    if any(horizon <= 0 for horizon in horizons):
        raise argparse.ArgumentTypeError("horizons must be positive")
    return horizons


def build_observations(
    rows: list[LabelRow],
    model: ReturnModel,
) -> list[ReturnObservation]:
    """Score label rows and keep ticker refs for cross-date stability joins."""
    return [
        ReturnObservation(row.ticker, model.predict(row.features), row.forward_return)
        for row in rows
    ]


def group_by_date(
    rows: list[LabelRow],
    observations: list[ReturnObservation],
) -> dict[str, list[ReturnObservation]]:
    """Group scored observations by their label as-of date."""
    grouped: dict[str, list[ReturnObservation]] = {}
    for row, observation in zip(rows, observations, strict=True):
        grouped.setdefault(row.as_of_date, []).append(observation)
    return grouped


def stability_metrics(
    by_period: dict[str, list[ReturnObservation]],
) -> MetricMap:
    """Return mean day-over-day rank autocorrelation across valid date pairs."""
    correlations: list[float] = []
    dates = sorted(by_period)
    for index in range(1, len(dates)):
        prev = {obs.subject_ref: obs.predicted for obs in by_period[dates[index - 1]]}
        curr = {obs.subject_ref: obs.predicted for obs in by_period[dates[index]]}
        correlation = rank_autocorrelation(prev, curr)
        if correlation is not None:
            correlations.append(correlation)
    metrics: MetricMap = {"stability_pairs": float(len(correlations))}
    if correlations:
        metrics["stability_mean"] = sum(correlations) / len(correlations)
    return metrics


def evaluate_label_rows(
    rows: list[LabelRow],
    model: ReturnModel,
    *,
    train_fraction: float,
    quantiles: int,
    include_in_sample: bool,
) -> MetricMap:
    """Evaluate either the test split or the full in-sample row set."""
    train, test = split_rows(rows, train_fraction=train_fraction)
    evaluation_rows = train + test if include_in_sample else test
    observations = build_observations(evaluation_rows, model)
    by_period = group_by_date(evaluation_rows, observations)
    metrics = return_scorecard_metrics(
        observations,
        neutral_prediction=0.0,
        quantiles=quantiles,
    )
    metrics.update(ic_series_metrics(by_period))
    metrics.update(stability_metrics(by_period))
    return metrics


def evaluate_horizon(
    ticker_bars: dict[str, list[tuple[str, float, float]]],
    model: ReturnModel,
    *,
    horizon: int,
    train_fraction: float,
    quantiles: int,
    include_in_sample: bool,
) -> MetricMap:
    """Build label rows for one forward-return horizon and evaluate them."""
    rows = build_label_rows(
        ticker_bars,
        forward_days=horizon,
        horizons=_FEATURE_HORIZONS,
        volatility_window=_VOLATILITY_WINDOW,
        momentum_window=_MOMENTUM_WINDOW,
    )
    return evaluate_label_rows(
        rows,
        model,
        train_fraction=train_fraction,
        quantiles=quantiles,
        include_in_sample=include_in_sample,
    )


def build_report(
    ticker_bars: dict[str, list[tuple[str, float, float]]],
    model: ReturnModel,
    *,
    model_path: str,
    horizons: tuple[int, ...],
    train_fraction: float,
    quantiles: int,
    include_in_sample: bool,
    generated_at: str,
) -> Report:
    """Build the serializable multi-horizon evaluation report."""
    return {
        "model": model_path,
        "generated_at": generated_at,
        "train_fraction": train_fraction,
        "in_sample": include_in_sample,
        "horizons": {
            str(horizon): evaluate_horizon(
                ticker_bars,
                model,
                horizon=horizon,
                train_fraction=train_fraction,
                quantiles=quantiles,
                include_in_sample=include_in_sample,
            )
            for horizon in horizons
        },
    }


def render_markdown_table(report: Report) -> str:
    """Render headline horizon metrics as a markdown table."""
    horizons = cast("dict[str, MetricMap]", report["horizons"])
    headers = ["horizon", *[label for label, _ in _HEADLINE_COLUMNS]]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for horizon, metrics in sorted(horizons.items(), key=lambda item: int(item[0])):
        row = [horizon]
        row.extend(_format_metric(metrics, key) for _, key in _HEADLINE_COLUMNS)
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _format_metric(metrics: MetricMap, key: str) -> str:
    if key not in metrics:
        return "N/A"
    value = metrics[key]
    if key == "complete_cases":
        return str(int(value))
    return f"{value:.4f}"


def build_parser() -> argparse.ArgumentParser:
    """Build the evaluation CLI parser."""
    parser = argparse.ArgumentParser(
        description="Evaluate the LightGBM return model across horizons."
    )
    parser.add_argument("--input", required=True, help="Path to price_cache CSV")
    parser.add_argument(
        "--model",
        default="models/lgbm-return-v1.txt",
        help="Booster artifact path",
    )
    parser.add_argument(
        "--horizons",
        type=parse_horizons,
        default=DEFAULT_EVAL_HORIZONS,
        help="Comma-separated forward-return horizons (default: 1,5,10,20)",
    )
    parser.add_argument(
        "--quantiles",
        type=int,
        default=DEFAULT_QUANTILES,
        help="Number of prediction quantiles for group-return metrics",
    )
    parser.add_argument(
        "--train-fraction",
        type=float,
        default=0.7,
        help="Walk-forward train/test split (0 < f < 1)",
    )
    parser.add_argument("--out", required=True, help="Path to write report JSON")
    parser.add_argument(
        "--include-in-sample",
        action="store_true",
        help="Evaluate all rows, not just the held-out test split",
    )
    return parser


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    """Load CSV/model artifacts, write JSON, and print the headline table."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.quantiles < 2:
        parser.error("--quantiles must be at least 2")
    if not 0.0 < args.train_fraction <= 1.0:
        parser.error("--train-fraction must be in (0, 1]")
    if args.include_in_sample:
        print("WARNING: in-sample evaluation requested; train-split rows included.")

    ticker_bars = load_price_csv(args.input)
    model = LightGBMModel(model_path=args.model)
    report = build_report(
        ticker_bars,
        model,
        model_path=args.model,
        horizons=args.horizons,
        train_fraction=args.train_fraction,
        quantiles=args.quantiles,
        include_in_sample=args.include_in_sample,
        generated_at=datetime.now(UTC).isoformat(),
    )

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(render_markdown_table(report))


if __name__ == "__main__":
    main()
