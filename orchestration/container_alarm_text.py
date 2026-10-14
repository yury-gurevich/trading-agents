"""The words of a container alarm: one message for the alarms not yet told.

Agent: orchestration
Role: group recorded container events and word the alarm message and the brief's line.
External I/O: none (zone data is read through zoneinfo).

A failure that hits the fleet hits many apps at once (2026-09-25: one cause, 13
apps, 102 exits), so a line is one kind of failure and names its apps. Takes event
properties as the graph holds them and reads no clock. Melbourne time first (DL-216).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from orchestration.container_events import (
    EXIT_ERROR,
    KILLED,
    MEMORY_KILL,
    PLATFORM_ERROR,
    PREEMPTED,
    PROVISION_FAILED,
    SCALER_FAILED,
    START_FAILED,
)
from orchestration.daily_brief_fills import parse_instant
from orchestration.daily_brief_text import local_stamp

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

_WORDS = {
    START_FAILED: "failed to start",
    PROVISION_FAILED: "revision failed to provision",
    SCALER_FAILED: "scale rule refused",
    MEMORY_KILL: "killed for memory",
    KILLED: "killed (exit code 137)",
    PLATFORM_ERROR: "platform error",
    PREEMPTED: "moved off its node by the platform",
}
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
TIMES = chr(0x00D7)  # the multiplication sign of a repeat count
APPS_NAMED = 4
BRIEF_GROUPS = 3


@dataclass(frozen=True)
class AlarmGroup:
    """Events of one kind and exit code: their apps, count, latest time and why."""

    kind: str
    exit_code: int | None
    apps: tuple[str, ...]
    times: int
    last: datetime
    why: str
    why_app: str = ""


def group_events(facts: Iterable[Mapping[str, object]]) -> list[AlarmGroup]:
    """Group event properties by kind and exit code; the newest group first."""
    buckets: dict[tuple[str, int | None], list[Mapping[str, object]]] = {}
    for fact in facts:
        buckets.setdefault((str(fact.get("kind", "")), _code(fact)), []).append(fact)
    groups = [_group(key, items) for key, items in buckets.items()]
    return sorted(groups, key=lambda item: (-item.last.timestamp(), item.kind))


def kind_words(group: AlarmGroup) -> str:
    """Say what happened, in the operator's words."""
    if group.kind == EXIT_ERROR:
        if group.exit_code is None:
            return "exited with an error"
        return f"exited with code {group.exit_code}"
    return _WORDS.get(group.kind, group.kind)


def alarm_message(
    groups: Sequence[AlarmGroup],
    *,
    timezone: str,
    limit: int,
    capped_hours: int | None = None,
) -> str:
    """Return the plain-text alarm: a header, one line per kind, the rest counted."""
    apps = {app for group in groups for app in group.apps}
    kinds = _count(len(groups), "kind")
    lines = [f"Container alarm: {_count(len(apps), 'app')}, {kinds} of failure"]
    for group in groups[:limit]:
        what = f"{kind_words(group)}{_times(group)}"
        lines.append(f"{what}: {_apps(group)} · {_when(group, timezone)}")
        if group.why:
            lines.append(f"  why ({group.why_app}): {group.why}")
    rest = groups[limit:]
    if rest:
        lines.append(f"and {_count(len(rest), 'more kind')} of failure")
    if capped_hours is not None:
        lines.append(
            f"Read only the last {capped_hours} hours; anything earlier is not read."
        )
    return "\n".join(lines)


def brief_summary(groups: Sequence[AlarmGroup]) -> str:
    """Return the brief's short account of the groups, at most three named."""
    named = [
        f"{kind_words(group)}{_times(group)} ({_apps(group)})"
        for group in groups[:BRIEF_GROUPS]
    ]
    rest = len(groups) - BRIEF_GROUPS
    if rest > 0:
        named.append(f"and {rest} more")
    return "; ".join(named)


def _group(
    key: tuple[str, int | None], items: list[Mapping[str, object]]
) -> AlarmGroup:
    # One replica's repeats arrive as rows with a rising count: take its highest.
    peaks: dict[tuple[str, str, str], int] = {}
    for item in items:
        incident = (
            str(item.get("app", "")),
            str(item.get("replica", "")),
            str(item.get("message", "")),
        )
        peaks[incident] = max(peaks.get(incident, 0), _whole(item.get("times")))
    ordered = sorted(items, key=_moment)
    explained = [item for item in ordered if item.get("error_line")]
    latest = explained[-1] if explained else {}
    return AlarmGroup(
        kind=key[0],
        exit_code=key[1],
        apps=tuple(sorted({str(item.get("app", "")) for item in items})),
        times=sum(peaks.values()),
        last=_moment(ordered[-1]),
        why=str(latest.get("error_line", "")),
        why_app=str(latest.get("app", "")),
    )


def _apps(group: AlarmGroup) -> str:
    named = ", ".join(group.apps[:APPS_NAMED])
    rest = len(group.apps) - APPS_NAMED
    return f"{named} and {rest} more" if rest > 0 else named


def _when(group: AlarmGroup, timezone: str) -> str:
    stamp = local_stamp(group.last, timezone)
    if stamp.endswith(" UTC"):
        return stamp
    return f"{stamp} ({group.last.astimezone(UTC):%H:%M} UTC)"


def _times(group: AlarmGroup) -> str:
    return f" {TIMES}{group.times}" if group.times > 1 else ""


def _moment(fact: Mapping[str, object]) -> datetime:
    return parse_instant(fact.get("occurred_at")) or _EPOCH


def _code(fact: Mapping[str, object]) -> int | None:
    value = fact.get("exit_code")
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _whole(value: object) -> int:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return 1


def _count(number: int, noun: str) -> str:
    return f"{number} {noun}{'' if number == 1 else 's'}"
