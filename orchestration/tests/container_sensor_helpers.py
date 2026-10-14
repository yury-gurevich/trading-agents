"""Measured platform rows and injected ports for Sprint 275.

Agent: orchestration
Role: provide synthetic log rows and recording ports for container sensor tests.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from orchestration.settings import OrchestratorSettings

if TYPE_CHECKING:
    from collections.abc import Sequence

    from orchestration.container_queries import Row

NOW = datetime(2026, 10, 14, 22, 30, tzinfo=UTC)
SETTINGS = OrchestratorSettings()


def row(reason: str, *, app: str = "provider", **props: object) -> Row:
    """Build one platform-shaped row without any live configuration."""
    return {
        "TimeGenerated": (NOW - timedelta(minutes=2)).isoformat(),
        "time_t": NOW.isoformat(),
        "ContainerAppName_s": app,
        "JobName_s": "",
        "RevisionName_s": f"{app}--0000174" if app else "",
        "ReplicaName_s": "",
        "Reason_s": reason,
        "Level": "warning",
        "Log_s": reason,
        "Count_d": 1.0,
    } | props


MEASURED = {
    "exit-error": row(
        "Error", Log_s="Container 'provider' was terminated with exit code '1'"
    ),
    "killed": row(
        "Error",
        app="master",
        Log_s="Container 'master' was terminated with exit code '137'",
    ),
    "memory-kill": row("OOMKilled", app="analyst"),
    "start-failed": row("ContainerBackOff", app="scanner"),
    "scale-up-failed": row("KEDAScaleTargetActivationFailed", app="forecaster"),
    "scaler-failed": row("KEDAScalerFailed", app="dispatcher-cron"),
    "provision-failed": row(
        "",
        app="",
        RevisionName_s="researcher--0000174",
        Level="error",
        Log_s="Error provisioning revision researcher--0000174",
    ),
    "preempted": row("Preempted", app="reporter"),
}
IGNORED = [
    row(reason)
    for reason in ("ReplicaUnhealthy", "AssigningReplicaFailed", "StoppingContainer")
]
IGNORED.append(
    row("Error", Log_s="Container 'provider' was terminated with exit code '0'")
)


@dataclass
class FakeReader:
    """Record read windows and supply canned system and console rows."""

    rows: list[Row] = field(default_factory=list)
    lines: list[Row] = field(default_factory=list)
    failure: Exception | None = None
    windows: list[tuple[datetime, datetime]] = field(default_factory=list)
    line_windows: list[tuple[tuple[str, ...], datetime, datetime]] = field(
        default_factory=list
    )

    def events(self, start: datetime, until: datetime) -> list[Row]:
        """Record a window, then either return the rows or raise the planted fault."""
        self.windows.append((start, until))
        if self.failure is not None:
            raise self.failure
        return self.rows

    def error_lines(
        self, replicas: Sequence[str], start: datetime, until: datetime
    ) -> list[Row]:
        """Return candidate lines after recording which replicas were requested."""
        self.line_windows.append((tuple(replicas), start, until))
        return self.lines


@dataclass
class FakeAlarm:
    """An alarm port that can refuse, raise or send without any transport."""

    alarms: list[str] = field(default_factory=list)
    sent: bool = True
    failure: Exception | None = None
    last_error: str = ""

    def send_alarm(self, *, text: str) -> int | None:
        """Capture exactly the message the sensor tried to send."""
        self.alarms.append(text)
        if self.failure is not None:
            raise self.failure
        return 301 if self.sent else None


def fact(kind: str, *, app: str = "provider", **props: object) -> dict[str, object]:
    """Build the facts a recorded alarm supplies to the text composer."""
    return {
        "app": app,
        "replica": app + "-replica",
        "kind": kind,
        "alarm": True,
        "message": kind,
        "times": 1,
        "occurred_at": NOW.isoformat(),
        "created_at": NOW.isoformat(),
        "error_line": "",
    } | props
