"""Read-only reproducibility measurement for recorded debate turns.

Agent: tooling
Role: rebuild each recorded defender:r1 prompt from graph state and compare its
      digest against the prompt_hash the live run stored.
External I/O: graph reads when run as a CLI. Writes nothing, by design.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:  # pragma: no cover - import-path shim
    sys.path.insert(0, str(_ROOT))

from orchestration.deliberation_replay import (  # noqa: E402
    order_set_of,
    replayed_prompt_digest,
)

if TYPE_CHECKING:
    from contracts.portfolio_manager import OrderIntent, OrderIntentSet
    from kernel import GraphStore, Node

# Only the first defender turn is a pure function of graph state: every later turn
# needs the transcript, and LLMCall stores a hash of the reply rather than its text.
_ROLE = "defender"
_ROUND = "r1"


@dataclass(frozen=True)
class ReproReport:
    """What was compared, and what it proved."""

    pm_runs: int
    unreadable_runs: int
    orders: int
    outcomes: Counter[str] = field(default_factory=Counter)

    @property
    def compared(self) -> int:
        """Turns where a stored hash existed to compare against."""
        return self.outcomes["matched"] + self.outcomes["mismatched"]


def measure_reproducibility(
    graph: GraphStore, *, run_ids: tuple[str, ...] = ()
) -> ReproReport:
    """Compare every replayable defender:r1 turn against its recorded hash."""
    wanted = frozenset(run_ids)
    hashes = _recorded_hashes(graph)
    pm_runs = 0
    unreadable = 0
    orders = 0
    outcomes: Counter[str] = Counter()
    for node in graph.list_nodes("PMRun"):
        if wanted and node.key not in wanted:
            continue
        pm_runs += 1
        order_set = order_set_of(node)
        if order_set is None:
            unreadable += 1
            continue
        for intent in order_set.approved:
            orders += 1
            outcomes[_compare(graph, node, order_set, intent, hashes)] += 1
    return ReproReport(
        pm_runs=pm_runs, unreadable_runs=unreadable, orders=orders, outcomes=outcomes
    )


def render_report(report: ReproReport) -> str:
    """Render the report with its denominator stated, never a bare percentage."""
    lines = [
        f"pm_runs\t{report.pm_runs}",
        f"unreadable_runs\t{report.unreadable_runs}",
        f"approved_orders\t{report.orders}",
        f"turns_compared\t{report.compared}",
    ]
    lines += [f"{name}\t{count}" for name, count in sorted(report.outcomes.items())]
    if report.compared:
        rate = report.outcomes["matched"] / report.compared * 100
        lines.append(f"reproducible_pct\t{rate:.2f}\t(of {report.compared} compared)")
    else:
        lines.append("reproducible_pct\tn/a\t(nothing was compared)")
    return "\n".join(lines)


def _compare(
    graph: GraphStore,
    node: Node,
    order_set: OrderIntentSet,
    intent: OrderIntent,
    hashes: dict[str, str],
) -> str:
    recorded = hashes.get(f"{node.key}:{intent.ticker}:{_ROLE}:{_ROUND}")
    if recorded is None:
        return "no_recorded_turn"
    rebuilt = replayed_prompt_digest(graph, node, order_set, intent)
    return "matched" if rebuilt == recorded else "mismatched"


def _recorded_hashes(graph: GraphStore) -> dict[str, str]:
    found: dict[str, str] = {}
    for call in graph.list_nodes("LLMCall"):
        corr = call.props.get("correlation_id")
        digest = call.props.get("prompt_hash")
        if isinstance(corr, str) and isinstance(digest, str):
            found[corr] = digest
    return found


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - CLI wiring
    """Print the reproducibility report for the configured graph."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=".env", help="path to .env")
    parser.add_argument(
        "--run-id", action="append", default=[], help="PMRun key; repeat to narrow"
    )
    args = parser.parse_args(argv)

    from dotenv import load_dotenv

    from kernel.graph_env import build_graph_from_env

    load_dotenv(Path(args.env_file), override=False)
    graph = build_graph_from_env()
    print(render_report(measure_reproducibility(graph, run_ids=tuple(args.run_id))))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
