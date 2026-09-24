"""Reporter trade-narrative result construction.

Agent: reporter
Role: persist typed trade narratives without coupling snapshot assembly size.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.reporter.domain.lineage import run_id_from_position_id
from agents.reporter.store import write_trade_narrative
from contracts.common import Explanation
from contracts.reporter import TradeNarrative

if TYPE_CHECKING:
    from kernel import GraphStore


def degraded_narrative(
    graph: GraphStore, position_id: str, *, max_chars: int
) -> TradeNarrative:
    """Build and persist a non-crashing degraded trade narrative."""
    summary = f"No Position found for {position_id}; trade story data unavailable."
    return narrative_result(
        graph,
        run_id=run_id_from_position_id(position_id),
        position_id=position_id,
        summary=trim_summary(summary, max_chars),
    )


def narrative_result(
    graph: GraphStore, *, run_id: str, position_id: str, summary: str
) -> TradeNarrative:
    """Persist and return one typed trade narrative."""
    provenance = write_trade_narrative(
        graph, run_id=run_id, position_id=position_id, story=summary
    )
    return TradeNarrative(
        position_id=position_id,
        story=Explanation(summary=summary, evidence_refs=("reporter.graph",)),
        provenance=provenance,
    )


def trim_summary(summary: str, max_chars: int) -> str:
    """Trim an operator-facing narrative summary to the configured limit."""
    return summary if len(summary) <= max_chars else summary[:max_chars]
