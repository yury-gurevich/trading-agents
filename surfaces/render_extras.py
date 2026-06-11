"""Extended render helpers for incidents and explain output.

Agent: surfaces
Role: render incident and narrative-explain CLI output.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.reporter import TradeNarrative
    from surfaces.queries.faults import FaultView


def render_incidents(faults: tuple[FaultView, ...]) -> str:
    """Render open incidents."""
    if not faults:
        return "no open incidents"
    lines = [f"Open incidents: {len(faults)}"]
    for fault in faults:
        lines.extend(
            (
                f"\n  [{fault.fault_id}] {fault.source_agent} - {fault.capability}",
                f"  severity: {fault.severity}",
                f"  {fault.message}",
                f"  {fault.occurred_at}",
            )
        )
    return "\n".join(lines)


def render_explain(narrative: TradeNarrative) -> str:
    """Render one on-demand trade narrative."""
    lines = [
        f"Narrative - position {narrative.position_id}",
        f"  {narrative.story.summary}",
    ]
    lines.extend(f"    ref: {ref}" for ref in narrative.story.evidence_refs)
    return "\n".join(lines)
