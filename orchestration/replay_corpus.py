"""Rebuild the debatable corpus from stored PM runs, without writing anything.

Agent: orchestration
Role: turn every approved order the graph still carries into a proposition the
      replay harness can re-debate, and count what it could not read.
External I/O: reads the injected GraphStore. Writes nothing, by design.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from kernel.deliberation import Proposition
from orchestration.deliberation_replay import order_set_of
from orchestration.replay_types import ReplaySubject
from orchestration.veto_context import build_veto_context

if TYPE_CHECKING:
    from kernel import GraphStore

__all__ = ["Corpus", "build_corpus"]


@dataclass(frozen=True)
class Corpus:
    """The subjects that can be replayed, plus what was skipped and why."""

    subjects: tuple[ReplaySubject, ...]
    pm_runs: int
    unreadable_runs: int

    def detail(self) -> str:
        """State the denominator alongside the corpus size, never alone."""
        return (
            f"pm_runs={self.pm_runs}; unreadable_runs={self.unreadable_runs}; "
            f"subjects={len(self.subjects)}"
        )


def build_corpus(graph: GraphStore, *, run_ids: tuple[str, ...] = ()) -> Corpus:
    """Rebuild one proposition per approved order across the selected PM runs."""
    wanted = frozenset(run_ids)
    subjects: list[ReplaySubject] = []
    pm_runs = 0
    unreadable = 0
    for node in graph.list_nodes("PMRun"):
        if wanted and node.key not in wanted:
            continue
        pm_runs += 1
        order_set = order_set_of(node)
        if order_set is None:
            unreadable += 1
            continue
        subjects.extend(
            ReplaySubject(
                pm_run=node.key,
                ticker=intent.ticker,
                proposition=Proposition(
                    f"{intent.action} {intent.ticker} (qty {intent.quantity})",
                    build_veto_context(graph, node, order_set, intent),
                ),
            )
            for intent in order_set.approved
        )
    return Corpus(subjects=tuple(subjects), pm_runs=pm_runs, unreadable_runs=unreadable)
