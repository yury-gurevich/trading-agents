"""Read-only fleet-readiness alert for the dashboard's page-level banner.

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

_HELD = "Tonight's run is held \N{EM DASH} the fleet check is failing"
_HELD_UNKNOWN = "Tonight's run is held \N{EM DASH} no recent fleet check"
_FAILING = "Tonight's run will be held unless the next fleet check passes"


def readiness_override(
    graph: GraphStore, *, now: datetime, max_age_minutes: int
) -> dict[str, object] | None:
    """Return the operator-facing readiness problem, when one is current.

    It describes the fleet *now* and tonight's run, never the selected run, so the
    dashboard shows it as a page banner rather than inside that run's verdict.
    """
    active_holds = [
        node for node in graph.list_nodes("RunHold") if is_active_run_hold(node)
    ]
    if active_holds:
        hold = max(active_holds, key=lambda node: str(node.props.get("as_of", "")))
        failures = _failures(hold.props)
        unknown = hold.props.get("readiness_state") == "unknown"
        headline = _HELD_UNKNOWN if unknown else _HELD
        return _alert("held", headline, failures, "")

    readiness = fleet_readiness(graph, now=now, max_age_minutes=max_age_minutes)
    if readiness.state == "failing":
        return _alert("failing", _FAILING, readiness.failures, readiness.checked_at)
    return None


def _alert(
    state: str, headline: str, failures: tuple[str, ...], checked_at: str
) -> dict[str, object]:
    problems = problem_lines(failures)
    first = problems[0] if problems else "no failure detail recorded"
    return {
        "state": state,
        "summary": f"{headline}: {first}",
        "headline": headline,
        "problems": problems,
        "checked_at": checked_at,
        "failures": list(failures),
    }


def problem_lines(failures: tuple[str, ...]) -> list[str]:
    """Group `<kind>:<agent>:<check>:<reason>` failures into one line per cause.

    Four agents refused on the same credential read as one cause naming four
    agents, not four machine strings. An unparseable failure passes through.
    """
    grouped: dict[tuple[str, str], list[str]] = {}
    raw: list[str] = []
    for failure in failures:
        parts = failure.split(":")
        if len(parts) < 4:
            raw.append(failure)
            continue
        agent, check = parts[1], parts[2]
        grouped.setdefault((check, _reason(parts[3:])), []).append(agent)
    lines = [
        f"{check} {reason} \N{EM DASH} {len(agents)} "
        f"agent{'s' if len(agents) != 1 else ''} can't start: {', '.join(agents)}"
        for (check, reason), agents in grouped.items()
    ]
    return lines + raw


def _reason(parts: list[str]) -> str:
    last = parts[-1]
    return (
        f"answered HTTP {last[5:]}" if last.startswith("http_") else f"failed: {last}"
    )


def _failures(props: object) -> tuple[str, ...]:
    if not hasattr(props, "get"):
        return ()
    value = props.get("failures", ())
    return (
        tuple(str(item) for item in value) if isinstance(value, (list, tuple)) else ()
    )
