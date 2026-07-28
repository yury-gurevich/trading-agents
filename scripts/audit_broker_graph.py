"""Audit broker holdings against graph lineage using code-owned predicates.

Agent: tooling
Role: report broker/graph protection and lineage gaps without writing.
External I/O: PostgreSQL and broker API when run as a CLI.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts._audit_broker_graph_impl import (  # noqa: E402
    AuditReport,
    AuditRow,
    audit_graph,
    print_report,
)

from agents.execution.broker_factory import broker_from_settings  # noqa: E402
from agents.execution.settings import ExecutionSettings  # noqa: E402
from contracts.positions import (  # noqa: E402
    is_active_position_node as is_active_position_node,
)

__all__ = ["AuditReport", "AuditRow", "audit_graph"]

# DL-73 was retracted because an audit reimplemented active-position logic from raw
# props. This script imports the production predicates instead of deriving them.


def main(argv: list[str] | None = None) -> int:
    """Run the audit against configured production-like dependencies."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=".env", help="path to .env")
    args = parser.parse_args(argv)

    from dotenv import load_dotenv

    from kernel.graph_env import build_graph_from_env

    load_dotenv(Path(args.env_file), override=False)
    graph = build_graph_from_env()
    try:
        broker = broker_from_settings(ExecutionSettings())
        report = audit_graph(graph, broker.positions(), broker.fills())
    finally:
        close = getattr(graph, "close", None)
        if close is not None:
            close()
    print_report(report)
    return 1 if report.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
