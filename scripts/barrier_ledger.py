"""Print the barrier ledger from the live graph: the scorecard and every settlement.

Agent: tooling
Role: let the planner read the forecaster's settlement ledger (S241) without writing
      anything: `barrier_scorecard` for one model and one line per BarrierSettlement,
      composed with the forecaster's own code, so what it prints is what the
      capability reports.
External I/O: environment, PostgreSQL graph (reads only), stdout/stderr.

Run it:
  PYTHONPATH=. python scripts/barrier_ledger.py [--model-id barrier-garch-v1]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv  # noqa: E402

from agents.forecaster.barrier_scorecard import barrier_scorecard  # noqa: E402
from agents.forecaster.domain.barrier_garch import BARRIER_MODEL_ID  # noqa: E402
from agents.forecaster.domain.barrier_settlement import OUTCOMES  # noqa: E402
from agents.forecaster.settlement_store import model_ledger  # noqa: E402
from contracts.forecaster import BarrierScorecardRequest  # noqa: E402

if TYPE_CHECKING:
    from kernel import GraphStore, Node


def main(argv: list[str] | None = None) -> int:
    """Print one model's ledger and return a process status."""
    parser = argparse.ArgumentParser(description="print the barrier settlement ledger")
    parser.add_argument("--model-id", default=BARRIER_MODEL_ID, help="barrier model")
    parser.add_argument(
        "--env-file",
        default=".env",
        help="optional .env file to load before connecting to Postgres",
    )
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    load_dotenv(Path(args.env_file), override=False)
    if not os.environ.get("POSTGRES_DSN"):
        print("error barrier ledger: POSTGRES_DSN is required", file=sys.stderr)
        return 1
    graph = _live_graph()
    try:
        lines = render(graph, args.model_id)
    finally:
        close = getattr(graph, "close", None)
        if callable(close):
            close()
    print("\n".join(lines))
    return 0


def render(graph: GraphStore, model_id: str) -> list[str]:
    """The scorecard's counts and scores, then one line per settlement."""
    metrics = barrier_scorecard(
        graph, BarrierScorecardRequest(model_id=model_id)
    ).metrics
    lines = [
        f"barrier ledger {model_id}: settled {metrics['settled']:.0f}  "
        f"void {metrics['void']:.0f}  open {metrics['open']:.0f}",
        *_score_lines(metrics),
    ]
    _claims, settlements = model_ledger(graph, model_id)
    ordered = sorted(
        settlements.values(),
        key=lambda node: (str(node.props["as_of"]), str(node.props["claim_key"])),
    )
    return [*lines, *(_settlement_line(node) for node in ordered)]


def _score_lines(metrics: dict[str, float]) -> list[str]:
    """Brier, skill and its interval, then realised and declared per outcome."""
    if "brier_model" not in metrics:
        return ["no settled claim yet"]
    interval = (
        f"[{100 * metrics['skill_lo']:+.2f}, {100 * metrics['skill_hi']:+.2f}] %"
        if "skill_lo" in metrics
        else "(no interval: fewer than 2 settled dates)"
    )
    return [
        f"brier_model {metrics['brier_model']:.4f}  brier_climatology "
        f"{metrics['brier_climatology']:.4f}  skill {100 * metrics['skill']:+.2f} % "
        + interval,
        *(
            f"{name:<8} realised {metrics[f'realised_{name}']:.3f}  "
            f"declared {metrics[f'declared_{name}']:.3f}"
            for name in OUTCOMES
        ),
    ]


def _settlement_line(node: Node) -> str:
    props = node.props
    outcome = str(props["outcome"])
    if props.get("void_reason"):
        outcome = f"{outcome} ({props['void_reason']})"
    brier = props.get("brier")
    return (
        f"{props['as_of']}  {props['ticker']:<6} {outcome:<34} "
        f"settled {props['settled_on']}  ratio {props['entry_ratio']}  "
        f"brier {'-' if brier is None else f'{brier:.4f}'}  {props['settling_ref']}"
    )


def _live_graph() -> GraphStore:
    from kernel.graph_env import build_graph_from_env

    return build_graph_from_env()


if __name__ == "__main__":
    raise SystemExit(main())
