"""Read-only fleet-readiness overrides for the dashboard verdict hero.

Agent: surfaces
Role: project dispatcher holds and master fleet-check failures for operators.
External I/O: reads the injected GraphStore only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from orchestration.fleet_readiness import fleet_readiness, is_active_run_hold

if TYPE_CHECKING:
    from datetime import datetime

    from kernel import GraphStore


def readiness_override(
    graph: GraphStore, *, now: datetime, max_age_minutes: int
) -> dict[str, object] | None:
    """Return the operator-facing readiness problem, when one is current."""
    active_holds = [
        node for node in graph.list_nodes("RunHold") if is_active_run_hold(node)
    ]
    if active_holds:
        hold = max(active_holds, key=lambda node: str(node.props.get("as_of", "")))
        return _override("held", "Tonight's run is held", _failures(hold.props))

    readiness = fleet_readiness(graph, now=now, max_age_minutes=max_age_minutes)
    if readiness.state == "failing":
        return _override(
            "failing",
            "Fleet check failing",
            readiness.failures,
            suffix="; next check in about an hour",
        )
    return None


def _override(
    state: str, prefix: str, failures: tuple[str, ...], suffix: str = ""
) -> dict[str, object]:
    first = failures[0] if failures else "no failure detail recorded"
    if state == "held":
        summary = f"{prefix}: {len(failures)} check(s) failing \N{EM DASH} {first}"
    else:
        summary = f"{prefix} ({len(failures)}) \N{EM DASH} {first}{suffix}"
    return {"state": state, "summary": summary, "failures": list(failures)}


def _failures(props: object) -> tuple[str, ...]:
    if not hasattr(props, "get"):
        return ()
    value = props.get("failures", ())
    return (
        tuple(str(item) for item in value) if isinstance(value, (list, tuple)) else ()
    )
