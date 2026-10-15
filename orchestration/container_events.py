"""The platform's container events, read as alarms, reports, or nothing.

Agent: orchestration
Role: classify Azure Container Apps system-log rows for the container sensor (DL-301).
External I/O: none.

A row is one record of the workspace's `ContainerAppSystemLogs_CL`. A row the platform
marks `error` or `Warning` is an alarm unless it is one of the warnings measured as
a deploy's or a wake's by-product on the workspace's 30 days (2026-10-15, DL-301
amendment 7); a reason not named here and not so marked is ignored.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

START_FAILED = "start-failed"
PROVISION_FAILED = "provision-failed"
SCALER_FAILED = "scaler-failed"
MEMORY_KILL = "memory-kill"
KILLED = "killed"
EXIT_ERROR = "exit-error"
PLATFORM_ERROR = "platform-error"
PREEMPTED = "preempted"
REVISION_FAILED = "revision-failed"
AUTOSCALER_FAILED = "autoscaler-failed"
PLATFORM_WARNING = "platform-warning"

ALARM_KINDS = frozenset(
    {
        START_FAILED,
        PROVISION_FAILED,
        SCALER_FAILED,
        MEMORY_KILL,
        KILLED,
        EXIT_ERROR,
        PLATFORM_ERROR,
        REVISION_FAILED,
        AUTOSCALER_FAILED,
        PLATFORM_WARNING,
    }
)
PLATFORM_KINDS = frozenset({REVISION_FAILED, AUTOSCALER_FAILED, PLATFORM_WARNING})

EXIT_REASON = "Error"  # the platform's reason for every exit; the code says which
_BY_REASON = {
    "ContainerBackOff": START_FAILED,
    "KEDAScaleTargetActivationFailed": START_FAILED,
    "KEDAScalerFailed": SCALER_FAILED,
    "OOMKilled": MEMORY_KILL,
    "Preempted": PREEMPTED,
    "ScaleDown": PREEMPTED,
    "RevisionFailure": REVISION_FAILED,
    "FailedGetScale": AUTOSCALER_FAILED,
    "FailedUpdateStatus": AUTOSCALER_FAILED,
}
SENSED_REASONS = (*_BY_REASON, EXIT_REASON)  # the query's filter is built from this
WARNING = "Warning"
BENIGN_WARNINGS = (  # each one ends by itself: measured 2026-10-15 (DL-301 amendment 7)
    "AssigningReplicaFailed",
    "Completed",
    "ReplicaUnhealthy",
    "ScaledObjectCheckFailed",
    "ScaledObjectDeleted",
)
_KEY_FIELDS = (
    "TimeGenerated",
    "time_t",
    "ContainerAppName_s",
    "JobName_s",
    "RevisionName_s",
    "ReplicaName_s",
    "Reason_s",
    "Level",
    "Log_s",
    "Count_d",
)
_EXIT_CODE = re.compile(r"exit code '(-?\d+)'")
_REVISION_SUFFIX = re.compile(r"--[a-z0-9]+$")
_PROVISIONING = "Error provisioning revision"
_GONE = " not found"  # the autoscaler asked for a revision a deploy had just removed
_KILL_CODE = 137
MESSAGE_LIMIT = 300


@dataclass(frozen=True)
class ContainerEvent:
    """One platform row the sensor keeps: which app, what happened, and when."""

    key: str
    app: str
    revision: str
    replica: str
    kind: str
    reason: str
    exit_code: int | None
    message: str
    times: int
    occurred_at: str

    @property
    def alarm(self) -> bool:
        """Whether the operator is told of this event."""
        return self.kind in ALARM_KINDS


def classify(row: Mapping[str, object]) -> ContainerEvent | None:
    """Return the row as an event the sensor keeps, or None for one it ignores."""
    reason = _text(row, "Reason_s")
    message = _text(row, "Log_s")
    code = _exit_code(message)
    kind = _kind(reason, _text(row, "Level"), _text(row, "Type_s"), message, code)
    if kind is None:
        return None
    revision = _text(row, "RevisionName_s")
    app = (
        _text(row, "ContainerAppName_s")
        or _text(row, "JobName_s")
        or _REVISION_SUFFIX.sub("", revision)
    )
    return ContainerEvent(
        key=event_key(row),
        app=app or "unknown",
        revision=revision,
        replica=_text(row, "ReplicaName_s"),
        kind=kind,
        reason=reason,
        exit_code=code,
        message=message[:MESSAGE_LIMIT],
        times=_times(row.get("Count_d")),
        occurred_at=_text(row, "time_t") or _text(row, "TimeGenerated"),
    )


def event_key(row: Mapping[str, object]) -> str:
    """Name one platform row, so a row read twice is recorded once."""
    joined = "\x1f".join(_text(row, name) for name in _KEY_FIELDS)
    return f"container-event:{hashlib.sha256(joined.encode()).hexdigest()[:32]}"


def _kind(
    reason: str, level: str, marked: str, message: str, code: int | None
) -> str | None:
    if reason == EXIT_REASON:
        if code == 0:
            return None
        return KILLED if code == _KILL_CODE else EXIT_ERROR
    if _BY_REASON.get(reason) == AUTOSCALER_FAILED and message.endswith(_GONE):
        return None
    if reason in _BY_REASON:
        return _BY_REASON[reason]
    if level.lower() == "error":
        return PROVISION_FAILED if message.startswith(_PROVISIONING) else PLATFORM_ERROR
    if marked == WARNING and reason not in BENIGN_WARNINGS:
        return PLATFORM_WARNING
    return None


def _exit_code(message: str) -> int | None:
    found = _EXIT_CODE.search(message)
    return int(found.group(1)) if found else None


def _times(value: object) -> int:
    # The platform folds repeats of one event into a count; it is absent on some rows.
    try:
        count = int(float(str(value)))
    except (ValueError, OverflowError):
        return 1
    return max(count, 1)


def _text(row: Mapping[str, object], name: str) -> str:
    value = row.get(name)
    return "" if value is None else str(value)
