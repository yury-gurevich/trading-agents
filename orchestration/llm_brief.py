"""The daily brief's LLM line: which roles ran on a later candidate, and why.

Agent: orchestration
Role: say in one line when an LLM role was activated on anything but its first
      working candidate in the last day, or passed a candidate over, or switched to
      a later candidate during the run (DL-289 P2, P3).
External I/O: reads the injected GraphStore.

No line when every role ran on its first candidate, so a quiet night briefs as
before. The master records the choice on each `AgentInstance` it activates; the
deliberator records a switch during the run on the run's `DeliberationRun`.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from orchestration.daily_brief_fills import parse_instant

if TYPE_CHECKING:
    from datetime import datetime

    from kernel import GraphStore, Node

BRIEF_WINDOW = timedelta(hours=24)
_SEP = " · "


def llm_line(
    graph: GraphStore, *, now: datetime, deliberation: Node | None = None
) -> str | None:
    """Return the brief's LLM line, or None when no candidate was passed over."""
    since = now - BRIEF_WINDOW
    groups: dict[tuple[str, tuple[str, ...]], set[str]] = {}
    for node in graph.list_nodes("AgentInstance"):
        started = parse_instant(node.props.get("started_at"))
        over = node.props.get("llm_passed_over")
        stale = started is None or started < since
        if stale or not isinstance(over, (list, tuple)) or not over:
            continue
        chosen = str(node.props.get("llm_candidate", ""))
        key = (chosen, tuple(str(line) for line in over))
        groups.setdefault(key, set()).add(str(node.props.get("agent_type", "")))
    parts = [
        f"{', '.join(sorted(types))} on {chosen} (passed over {'; '.join(over)})"
        for (chosen, over), types in sorted(groups.items())
    ]
    switches = deliberation.props.get("llm_switches") if deliberation else None
    if isinstance(switches, (list, tuple)):
        parts.extend(f"{line} during the run" for line in map(str, switches))
    return f"LLM: {_SEP.join(parts)}" if parts else None
