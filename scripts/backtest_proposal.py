"""Generate walk-forward evidence for one bounded researcher proposal.

Agent: tooling
Role: compose price CSV bars, analyst signal builders, and researcher backtest output.
External I/O: filesystem (reads CSV, writes evidence JSON).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.backtest_proposal_report import render_table
from scripts.price_csv import load_price_csv

from agents.analyst.domain import indicators
from agents.analyst.domain.technical_rules import score_bollinger, score_rsi
from agents.analyst.settings import AnalystSettings
from agents.researcher.domain.backtest import run_walkforward, to_evidence
from agents.researcher.settings import ResearcherSettings

Bars = dict[str, list[tuple[str, float, float]]]
Closes = dict[str, list[tuple[str, float]]]
Scores = dict[str, dict[str, float]]
ScoreBuilder = Callable[[Bars, float], Scores]


def build_scores(parameter: str, value: float, bars: Bars) -> Scores | None:
    """Dispatch a vetted signal builder, or return None for fail-open evidence."""
    builder = CATALOGUE.get(parameter)
    if builder is None:
        return None
    return builder(bars, value)


def close_series(bars: Bars) -> Closes:
    """Drop volume for the pure backtest harness."""
    return {
        ticker: [(bar_date, close) for bar_date, close, _ in rows]
        for ticker, rows in bars.items()
    }


def run(args: argparse.Namespace) -> int:
    """Run incumbent-vs-proposed evidence generation."""
    bars = load_price_csv(args.input)
    current_scores = build_scores(args.parameter, args.current, bars)
    proposed_scores = build_scores(args.parameter, args.proposed, bars)
    if current_scores is None or proposed_scores is None:
        print(f"no signal builder for {args.parameter} — evidence not generated")
        return 0
    closes = close_series(bars)
    incumbent = run_walkforward(
        current_scores,
        closes,
        top_k=args.top_k,
        slippage_bps=args.slippage_bps,
        holdout_fraction=args.holdout_fraction,
    )
    proposed = run_walkforward(
        proposed_scores,
        closes,
        top_k=args.top_k,
        slippage_bps=args.slippage_bps,
        holdout_fraction=args.holdout_fraction,
    )
    table = render_table(incumbent, proposed)
    print(table)
    evidence = to_evidence(proposed, slippage_bps=args.slippage_bps)
    Path(args.out).write_text(
        json.dumps(evidence.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


def build_parser(settings: ResearcherSettings | None = None) -> argparse.ArgumentParser:
    """Build the CLI parser."""
    defaults = settings or ResearcherSettings()
    parser = argparse.ArgumentParser(
        description="Backtest one catalogue-backed parameter proposal."
    )
    parser.add_argument("--parameter", required=True)
    parser.add_argument("--current", required=True, type=float)
    parser.add_argument("--proposed", required=True, type=float)
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--top-k", type=int, default=defaults.backtest_top_k)
    parser.add_argument(
        "--slippage-bps", type=float, default=defaults.backtest_slippage_bps
    )
    parser.add_argument(
        "--holdout-fraction",
        type=float,
        default=defaults.backtest_holdout_fraction,
    )
    return parser


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(args)


def _rsi_scores(bars: Bars, value: float) -> Scores:
    settings = AnalystSettings(rsi_period=_period(value))
    scores: Scores = {}
    for ticker, rows in bars.items():
        closes = [close for _, close, _ in rows]
        dates = [bar_date for bar_date, _, _ in rows]
        for index, score_date in enumerate(dates):
            rsi = indicators.rsi(closes[: index + 1], settings.rsi_period)
            if rsi is not None:
                scores.setdefault(score_date, {})[ticker] = score_rsi(rsi)
    return scores


def _bollinger_scores(bars: Bars, value: float) -> Scores:
    settings = AnalystSettings(bollinger_window=_period(value))
    scores: Scores = {}
    for ticker, rows in bars.items():
        closes = [close for _, close, _ in rows]
        dates = [bar_date for bar_date, _, _ in rows]
        for index, score_date in enumerate(dates):
            position = indicators.bollinger_position(
                closes[: index + 1],
                settings.bollinger_window,
                settings.bollinger_sigma,
            )
            if position is not None:
                scores.setdefault(score_date, {})[ticker] = score_bollinger(position)
    return scores


def _period(value: float) -> int:
    period = int(value)
    if value != period or period <= 0:
        raise ValueError("catalogue window parameters must be positive integers")
    return period


CATALOGUE: dict[str, ScoreBuilder] = {
    "analyst.rsi_period": _rsi_scores,
    "analyst.bollinger_window": _bollinger_scores,
}


if __name__ == "__main__":
    raise SystemExit(main())
