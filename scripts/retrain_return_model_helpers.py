"""Pure helpers for the rolling return-model retrain CLI.

Agent: tooling
Role: partition evidence windows, format champion tables, and build the parser
      and report payload. The artifact swap lives in `retrain_return_model_swap.py`.
External I/O: none.
"""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from agents.forecaster.domain.return_labels import build_label_rows
from agents.forecaster.settings import ForecasterSettings

if TYPE_CHECKING:
    from pathlib import Path

    from agents.forecaster.domain.retrain_policy import CompareVerdict, RetrainDecision
    from agents.forecaster.domain.return_labels import LabelRow

MetricMap = dict[str, float]

_COMPARISON_COLUMNS = (
    "complete_cases",
    "rank_ic",
    "ic_ir",
    "ic",
    "hit_rate",
    "top_bottom_spread",
)


def partition_recent_dates(
    rows: list[LabelRow], *, window_days: int
) -> tuple[list[LabelRow], list[LabelRow]]:
    """Split rows into history and the trailing distinct-date evaluation window."""
    if window_days < 1:
        raise ValueError("window_days must be positive")
    dates = sorted({row.as_of_date for row in rows})
    recent_dates = set(dates[-window_days:])
    history = [row for row in rows if row.as_of_date not in recent_dates]
    recent = [row for row in rows if row.as_of_date in recent_dates]
    return history, recent


def label_rows_for_horizon(
    bars: dict[str, list[tuple[str, float, float]]],
    *,
    horizon: int,
    settings: ForecasterSettings,
) -> list[LabelRow]:
    """Build label rows for the configured retrain horizon."""
    return build_label_rows(
        bars,
        forward_days=horizon,
        horizons=(
            settings.return_short_horizon,
            settings.return_mid_horizon,
            settings.return_long_horizon,
        ),
        volatility_window=settings.volatility_window,
        momentum_window=settings.momentum_window,
    )


def render_comparison_table(incumbent: MetricMap, challenger: MetricMap) -> str:
    """Render incumbent-vs-challenger headline metrics as markdown."""
    lines = [
        "| metric | incumbent | challenger | delta |",
        "| --- | --- | --- | --- |",
    ]
    for key in _COMPARISON_COLUMNS:
        lines.append(
            "| "
            + " | ".join(
                (
                    key,
                    _format_metric(incumbent, key),
                    _format_metric(challenger, key),
                    _format_delta(incumbent, challenger, key),
                )
            )
            + " |"
        )
    return "\n".join(lines)


def decision_to_dict(decision: RetrainDecision) -> dict[str, object]:
    return {
        "retrain": decision.retrain,
        "reason": decision.reason,
        "recent": decision.recent,
        "reference": decision.reference,
    }


def verdict_to_dict(verdict: CompareVerdict | None) -> dict[str, object] | None:
    if verdict is None:
        return None
    return {
        "swap": verdict.swap,
        "reason": verdict.reason,
        "primary_delta": verdict.primary_delta,
        "secondary_delta": verdict.secondary_delta,
    }


def build_parser(settings: ForecasterSettings | None = None) -> argparse.ArgumentParser:
    """Build the retrain CLI parser."""
    defaults = settings or ForecasterSettings()
    parser = argparse.ArgumentParser(
        description="Run the rolling return-model retrain loop."
    )
    parser.add_argument("--input", required=True, help="Path to bars CSV")
    parser.add_argument("--model", default=defaults.return_model_path)
    parser.add_argument("--window-days", type=int, default=defaults.retrain_window_days)
    parser.add_argument(
        "--trigger-fraction",
        type=float,
        default=defaults.retrain_trigger_fraction,
    )
    parser.add_argument("--horizon", type=int, default=defaults.retrain_horizon_days)
    parser.add_argument("--min-cases", type=float, default=defaults.retrain_min_cases)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--out", required=True, help="Path to write report JSON")
    return parser


def report_payload(
    *,
    model_path: Path,
    generated_at: str,
    config: dict[str, object],
    decision: RetrainDecision,
    verdict: CompareVerdict | None,
    reference: MetricMap,
    recent_incumbent: MetricMap,
    recent_challenger: MetricMap | None,
) -> dict[str, object]:
    """Build the JSON-serializable retrain report payload."""
    return {
        "model": str(model_path),
        "generated_at": generated_at,
        "config": config,
        "decision": decision_to_dict(decision),
        "verdict": verdict_to_dict(verdict),
        "reference": reference,
        "recent_incumbent": recent_incumbent,
        "recent_challenger": recent_challenger,
    }


def _format_metric(metrics: MetricMap, key: str) -> str:
    if key not in metrics:
        return "N/A"
    value = metrics[key]
    if key == "complete_cases":
        return str(int(value))
    return f"{value:.4f}"


def _format_delta(incumbent: MetricMap, challenger: MetricMap, key: str) -> str:
    if key not in incumbent or key not in challenger:
        return "N/A"
    return f"{challenger[key] - incumbent[key]:.4f}"
