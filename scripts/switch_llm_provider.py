"""Report, apply and prove the fleet's one declared LLM vendor.

Agent: tooling
Role: coordinate bounded, injected provider-switch operations.
External I/O: Azure CLI, configured Postgres graph and external evidence directory.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.switch_llm_apply import (  # noqa: E402
    apply,
    changed_from_evidence,
    read_values,
)
from scripts.switch_llm_azure import Azure, SwitchOperationError, run_az  # noqa: E402
from scripts.switch_llm_config import (  # noqa: E402
    SwitchSettings,
    evidence_directory,
    load_pack,
    utc_timestamp,
)
from scripts.switch_llm_proof import wait_for_proof  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from scripts.switch_llm_azure import Runner

    from kernel import GraphStore


def main(
    argv: list[str] | None = None,
    *,
    runner: Runner | None = None,
    graph: GraphStore | None = None,
    clock: Callable[[], datetime] | None = None,
    sleep: Callable[[float], None] | None = None,
    environ: Mapping[str, str] | None = None,
    root: Path | None = None,
    emit: Callable[[str], None] = print,
) -> int:
    """Return documented exit codes; inject every external boundary in unit tests."""
    args = _parser().parse_args(argv)
    root = root or _ROOT
    env = os.environ if environ is None else environ

    def write(line: str) -> None:
        emit(line.encode("ascii", "backslashreplace").decode("ascii"))

    clock = clock or (lambda: datetime.now(UTC))
    try:
        pack = load_pack(root)
        timing = SwitchSettings(
            poll_seconds=args.poll_seconds, wait_seconds=args.wait_seconds
        )
        directory = (
            evidence_directory(args.evidence_dir, root)
            if args.apply or args.evidence_dir
            else None
        )
        since = utc_timestamp(args.prove_since) if args.prove_since else None
        if (args.apply or since is not None) and not env.get("POSTGRES_DSN"):
            raise ValueError("POSTGRES_DSN is required for graph proof")
    except (ValueError, KeyError, TypeError, OSError) as exc:
        write(f"configuration refused: {exc}")
        return 2
    try:
        if since is not None:
            changed = (
                changed_from_evidence(directory, pack) if directory else list(pack.apps)
            )
            if directory is None:
                write(
                    "proof-only: all target activations required without apply evidence"
                )
        else:
            azure = Azure(runner or run_az, args.resource_group, args.subscription)
            snapshots, changed = read_values(azure, pack, write)
            if not args.apply:
                return 3 if changed else 0
            if not changed:
                write("nothing to apply: every app already holds the declared value")
                return 0
            assert directory is not None
            code, since = apply(
                azure,
                pack,
                snapshots,
                changed,
                directory,
                even_if_running=args.even_if_running,
                clock=clock,
                emit=write,
            )
            if code:
                return code
        if graph is None:
            from kernel.graph_postgres import PostgresGraphStore
            from kernel.graph_postgres_config import PostgresGraphSettings

            graph = PostgresGraphStore(
                PostgresGraphSettings(postgres_dsn=env["POSTGRES_DSN"])
            )
        return wait_for_proof(
            graph,
            pack,
            changed,
            since,
            clock=clock,
            sleep=sleep or time.sleep,
            poll_seconds=timing.poll_seconds,
            wait_seconds=timing.wait_seconds,
            emit=write,
        )
    except Exception as exc:
        reason = (
            str(exc) if isinstance(exc, SwitchOperationError) else type(exc).__name__
        )
        write(f"switch failed: {reason}")
        return 1


def _parser() -> argparse.ArgumentParser:
    defaults = SwitchSettings()
    parser = argparse.ArgumentParser(
        description="Apply the pack's declared LLM provider and prove it"
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--apply", action="store_true")
    modes.add_argument("--prove-since", default="")
    parser.add_argument("--evidence-dir", default="")
    parser.add_argument("--even-if-running", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=defaults.poll_seconds)
    parser.add_argument("--wait-seconds", type=float, default=defaults.wait_seconds)
    parser.add_argument("--resource-group", default="trading-agents")
    parser.add_argument("--subscription")
    return parser


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
