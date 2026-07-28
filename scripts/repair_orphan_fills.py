"""Adopt broker-known orders that have no Fill chain.

Agent: tooling
Role: repair append-only Fill lineage from broker state without forging ExecutionRun.
External I/O: PostgreSQL and broker API when run as a CLI.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from pydantic_settings import SettingsConfigDict

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts._repair_orphan_fills_impl import (  # noqa: E402
    RepairReport,
    RepairRow,
    parse_time,
    repair_graph,
)

from agents.execution.broker_factory import broker_from_settings  # noqa: E402
from agents.execution.settings import ExecutionSettings  # noqa: E402
from kernel import AgentSettings, tunable  # noqa: E402

__all__ = ["RepairReport", "RepairRow", "repair_graph"]


class OrphanFillRepairSettings(AgentSettings):
    """Settings for the repair CLI's bounded default lookback."""

    model_config = SettingsConfigDict(
        env_prefix="REPAIR_ORPHAN_FILLS_", frozen=True, populate_by_name=True
    )
    since_days: int = tunable(
        14,
        why="Bound the default broker-order scan for orphan Fill repair.",
        ge=1,
        le=90,
        unit="days",
    )


def main(argv: list[str] | None = None) -> int:
    """Run the repair against the configured graph and broker."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write missing Fill nodes")
    parser.add_argument("--since", help="UTC ISO timestamp lower bound")
    parser.add_argument("--env-file", default=".env", help="path to .env")
    args = parser.parse_args(argv)

    from dotenv import load_dotenv

    from kernel.graph_env import build_graph_from_env

    load_dotenv(Path(args.env_file), override=False)
    since = _since(args.since, OrphanFillRepairSettings())
    graph = build_graph_from_env()
    try:
        broker = broker_from_settings(ExecutionSettings())
        report = repair_graph(graph, broker.fills(), apply=args.apply, since=since)
    finally:
        close = getattr(graph, "close", None)
        if close is not None:
            close()
    _print_report(report, apply=args.apply, since=since)
    return 0


def _since(raw: str | None, settings: OrphanFillRepairSettings) -> datetime:
    if raw:
        return parse_time(raw) or datetime.fromisoformat(raw).astimezone(UTC)
    return datetime.now(tz=UTC) - timedelta(days=settings.since_days)


def _print_report(report: RepairReport, *, apply: bool, since: datetime) -> None:
    print(f"mode={'apply' if apply else 'dry-run'} since={since.isoformat()}")
    print("client_order_id\tticker\tside\tquantity\tstatus\tverdict\treason")
    for row in report.rows:
        print(
            f"{row.client_order_id}\t{row.ticker}\t{row.side}\t{row.quantity}\t"
            f"{row.status}\t{row.verdict}\t{row.reason}"
        )
    print(
        "totals "
        f"candidates={len(report.rows)} "
        f"would_record={report.would_record} "
        f"recorded={report.recorded} "
        f"already_recorded={report.already_recorded} "
        f"ignored={report.ignored}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
