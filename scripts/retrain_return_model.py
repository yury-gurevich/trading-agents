"""Rolling retrain loop for the LightGBM return model.

Agent: tooling
Role: evaluate IC decay, train a challenger, and optionally promote it.
External I/O: reads bars/model files, writes challenger/report files, and only
              mutates model artifacts when --apply is supplied.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# Keep sys.path clean: run from the repo root so the package is importable.
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.evaluate_return_model import DEFAULT_QUANTILES, evaluate_label_rows
from scripts.price_csv import load_price_csv
from scripts.retrain_return_model_helpers import (
    MetricMap,
    build_parser,
    candidate_path_for,
    execute_swap,
    label_rows_for_horizon,
    partition_recent_dates,
    plan_swap,
    render_comparison_table,
    report_payload,
)

from agents.forecaster.domain.retrain_policy import (
    CompareVerdict,
    compare_models,
    should_retrain,
)
from agents.forecaster.lightgbm_model import LightGBMModel
from agents.forecaster.model_trainer import train_and_save
from agents.forecaster.settings import ForecasterSettings

_TRAIN_FRACTION = 0.7


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    """Load bars/model artifacts, report evidence, and optionally promote."""
    args = build_parser().parse_args(argv)
    if args.window_days < 1:
        raise SystemExit("--window-days must be positive")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    settings = ForecasterSettings()
    model_path = Path(args.model)
    rows = label_rows_for_horizon(
        load_price_csv(args.input), horizon=args.horizon, settings=settings
    )
    history, recent = partition_recent_dates(rows, window_days=args.window_days)
    if not history or not recent:
        raise SystemExit("not enough label rows for history and recent partitions")

    incumbent = LightGBMModel(model_path=str(model_path))
    reference = evaluate_label_rows(
        history,
        incumbent,
        train_fraction=_TRAIN_FRACTION,
        quantiles=DEFAULT_QUANTILES,
        include_in_sample=False,
    )
    recent_incumbent = evaluate_label_rows(
        recent,
        incumbent,
        train_fraction=1.0,
        quantiles=DEFAULT_QUANTILES,
        include_in_sample=True,
    )
    decision = should_retrain(
        recent_incumbent,
        reference,
        trigger_fraction=args.trigger_fraction,
        min_cases=args.min_cases,
    )
    print(f"DECISION retrain={decision.retrain} reason={decision.reason}")

    verdict: CompareVerdict | None = None
    recent_challenger: MetricMap | None = None
    candidate_path: Path | None = None
    if decision.retrain or args.force:
        candidate_path = candidate_path_for(model_path, stamp=stamp)
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        train_and_save(history, str(candidate_path), train_fraction=_TRAIN_FRACTION)
        challenger = LightGBMModel(model_path=str(candidate_path))
        recent_challenger = evaluate_label_rows(
            recent,
            challenger,
            train_fraction=1.0,
            quantiles=DEFAULT_QUANTILES,
            include_in_sample=True,
        )
        print(render_comparison_table(recent_incumbent, recent_challenger))
        verdict = compare_models(recent_incumbent, recent_challenger)
        print(f"VERDICT swap={verdict.swap} reason={verdict.reason}")

    if (
        args.apply
        and verdict is not None
        and verdict.swap
        and candidate_path is not None
    ):
        steps = plan_swap(model_path, candidate_path, stamp=stamp)
        execute_swap(steps)
        print(f"PROMOTED archive={steps[0][2]} active={model_path}")
    elif args.apply:
        print("KEPT: apply requested but the challenger did not earn promotion")
    else:
        print("KEPT: dry-run; pass --apply to promote an eligible challenger")

    config = {
        "window_days": args.window_days,
        "trigger_fraction": args.trigger_fraction,
        "horizon": args.horizon,
        "min_cases": args.min_cases,
        "force": args.force,
        "apply": args.apply,
    }
    report = report_payload(
        model_path=model_path,
        generated_at=datetime.now(UTC).isoformat(),
        config=config,
        decision=decision,
        verdict=verdict,
        reference=reference,
        recent_incumbent=recent_incumbent,
        recent_challenger=recent_challenger,
    )
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
