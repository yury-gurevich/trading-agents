"""The container sensor's two workspace queries, and how a reply is read.

Agent: orchestration
Role: word the Log Analytics queries the sensor sends and parse their result table.
External I/O: none.

Only instants and replica names are put into a query. A replica name is checked
against the platform's naming rule before it is, so no text a row carries can change
what a query asks (DL-301).
"""

from __future__ import annotations

import re
from datetime import UTC
from typing import TYPE_CHECKING

from orchestration.container_events import BENIGN_WARNINGS, SENSED_REASONS, WARNING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from datetime import datetime

EVENT_ROWS_MAX = 5000
LINE_ROWS_MAX = 500
REPLICA_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,99}$")
_LINE_FILTER = (
    "| where Log_s contains '] stop' or Log_s matches regex "
    r"@'^\s*[A-Za-z_][A-Za-z0-9_.]*(Error|Exception)\b'"
)

Row = dict[str, object]


class ContainerLogReadError(RuntimeError):
    """A workspace read failed; ``status`` is a word safe to print and record."""

    def __init__(self, status: str) -> None:
        """Keep the status word; the message repeats it and nothing else."""
        super().__init__(f"read failed ({status})")
        self.status = status


def events_query(start: datetime, until: datetime) -> str:
    """Return the query for the sensed rows ingested after ``start`` up to ``until``."""
    reasons = ", ".join(f"'{reason}'" for reason in SENSED_REASONS)
    benign = ", ".join(f"'{reason}'" for reason in BENIGN_WARNINGS)
    return (
        "ContainerAppSystemLogs_CL\n"
        f"| where ingestion_time() > {kql_time(start)}"
        f" and ingestion_time() <= {kql_time(until)}\n"
        f"| where Reason_s in ({reasons}) or Level =~ 'error'"
        f" or (Type_s == '{WARNING}' and Reason_s !in ({benign}))\n"
        "| project TimeGenerated, time_t, ContainerAppName_s, JobName_s, "
        "RevisionName_s, ReplicaName_s, Reason_s, Type_s, Level, Log_s, Count_d\n"
        "| order by TimeGenerated asc\n"
        f"| take {EVENT_ROWS_MAX}"
    )


def lines_query(replicas: Sequence[str], start: datetime, until: datetime) -> str:
    """Return the query for the stderr lines that can explain an alarm."""
    names = ", ".join(f"'{name}'" for name in replicas if REPLICA_NAME.match(name))
    return (
        "ContainerAppConsoleLogs_CL\n"
        f"| where TimeGenerated between ({kql_time(start)} .. {kql_time(until)})\n"
        f"| where ContainerGroupName_s in ({names}) and Stream_s == 'stderr'\n"
        f"{_LINE_FILTER}\n"
        "| project TimeGenerated, ContainerGroupName_s, Log_s\n"
        "| order by TimeGenerated desc\n"
        f"| take {LINE_ROWS_MAX}"
    )


def kql_time(moment: datetime) -> str:
    """Render an aware instant as a query-language UTC literal."""
    return f"datetime({moment.astimezone(UTC):%Y-%m-%dT%H:%M:%S.%fZ})"


def table_rows(payload: Mapping[str, object]) -> list[Row]:
    """Return the first result table as one dict per row."""
    tables = payload.get("tables")
    if not isinstance(tables, list) or not tables or not isinstance(tables[0], dict):
        raise ContainerLogReadError("shape")
    columns = tables[0].get("columns")
    rows = tables[0].get("rows")
    if not isinstance(columns, list) or not isinstance(rows, list):
        raise ContainerLogReadError("shape")
    try:
        names = [str(column["name"]) for column in columns]
        return [dict(zip(names, row, strict=True)) for row in rows]
    except (KeyError, TypeError, ValueError):
        raise ContainerLogReadError("shape") from None
