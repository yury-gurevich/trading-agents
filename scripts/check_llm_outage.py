"""Report whether the models answered, from the call ledger alone.

Agent: tooling
Role: name a silent LLM night without waiting for an acceptance run.
External I/O: PostgreSQL when run as a CLI.

Work-queue item 55. Nine nights returned nothing and nobody noticed. S202's gate
now turns a total-outage night red on the *acceptance* run; this answers the same
question on demand, across **every** calling agent rather than deliberation only,
so the operator agent's calls stop being behind no gate at all.

The classification lives in `kernel.llm_outage`, imported rather than
reimplemented here (DL-73: an audit that re-derives production logic from raw
props produced a false red-severity finding that had to be retracted).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from kernel.llm_outage import outage_report  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Print the ledger's verdict; exit non-zero only on a total outage."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", default=".env", help="path to .env")
    args = parser.parse_args(argv)

    from dotenv import load_dotenv

    from kernel.graph_env import build_graph_from_env

    load_dotenv(Path(args.env_file), override=False)
    graph = build_graph_from_env()
    try:
        report = outage_report(graph.list_nodes("LLMCall"))
    finally:
        close = getattr(graph, "close", None)
        if close is not None:
            close()

    print(report.summary())
    if report.agents:
        print(f"agents seen: {', '.join(report.agents)}")
    # Only a TOTAL outage is an error. A partial night is real but expected
    # noise, and a check that exits non-zero on noise is one nobody runs.
    return 1 if report.is_total_outage else 0


if __name__ == "__main__":
    raise SystemExit(main())
