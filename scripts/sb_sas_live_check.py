"""CLI wrapper for the controlled Service Bus SAS live check.

Agent: tooling
Role: run the canary SAS proof and print only non-secret evidence.
External I/O: Azure Service Bus and Azure CLI through sb_sas_live_ops.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.sb_sas_live_ops import run_check  # noqa: E402


def main() -> int:
    """Print non-secret JSON evidence for the controlled live SAS check."""
    args = _parser().parse_args()
    try:
        print(
            json.dumps(
                run_check(args.resource_group, args.namespace_name), sort_keys=True
            )
        )
    except Exception as exc:
        sys.stderr.write(f"error sb sas live check failed: {type(exc).__name__}\n")
        return 1
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="controlled Service Bus SAS live check"
    )
    parser.add_argument("--resource-group", required=True)
    parser.add_argument("--namespace-name", required=True)
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
