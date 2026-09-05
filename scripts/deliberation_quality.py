"""The verdict-quality gate: does the veto agree with itself, and with the record.

Agent: tooling
Role: read a replay sweep's verdicts, measure self-agreement and agreement with
      the verdicts the fleet actually recorded, and judge them against a floor.
External I/O: reads the sweep's verdicts.json and the graph. Writes nothing.

Warn-only on its first day. It prints WARN and exits 0 unless --blocking is
passed, because the floor is uncalibrated until Part B's repeats exist.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:  # pragma: no cover - import-path shim
    sys.path.insert(0, str(_ROOT))

from orchestration.quality_gate import evaluate_quality  # noqa: E402
from orchestration.settings import DeliberationQualitySettings  # noqa: E402
from orchestration.verdict_metrics import (  # noqa: E402
    ReplayVerdict,
    agreement_with,
    self_agreement,
)
from orchestration.verdict_sources import (  # noqa: E402
    recorded_as_repeats,
    recorded_verdicts,
)


def load_verdicts(path: Path) -> tuple[ReplayVerdict, ...]:
    """Read a sweep's verdicts.json into the metric's own record type."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return tuple(
        ReplayVerdict(
            pm_run=str(entry["pm_run"]),
            ticker=str(entry["ticker"]),
            arm=str(entry["arm"]),
            repeat=int(entry["repeat"]),
            ruling=entry.get("ruling"),
            failure=entry.get("failure"),
        )
        for entry in raw
    )


def main(argv: list[str] | None = None) -> int:
    """Measure and judge one replay sweep."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--verdicts", help="path to a replay sweep's verdicts.json")
    parser.add_argument(
        "--recorded-run",
        action="append",
        default=[],
        help="measure agreement between recorded DeliberationRuns, by ticker",
    )
    parser.add_argument("--arm", default=None, help="restrict to one arm")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--blocking", action="store_true", help="fail below the floor")
    parser.add_argument(
        "--no-graph", action="store_true", help="skip the recorded-verdict comparison"
    )
    args = parser.parse_args(argv)

    if not args.verdicts and len(args.recorded_run) < 2:
        parser.error("give --verdicts, or two or more --recorded-run ids")

    settings = DeliberationQualitySettings()
    verdicts = (
        load_verdicts(Path(args.verdicts))
        if args.verdicts
        else recorded_as_repeats(_graph(args), args.recorded_run)
    )
    agreement = self_agreement(verdicts, arm=args.arm)
    gate = evaluate_quality(
        agreement,
        floor=settings.self_agreement_floor,
        min_compared=settings.min_compared_pairs,
        warn_only=not args.blocking,
    )
    print(gate.render())

    for arm in sorted({verdict.arm for verdict in verdicts}):
        print(self_agreement(verdicts, arm=arm).detail())
    if not args.no_graph and args.verdicts:
        print(_against_the_record(verdicts, args))
    return gate.exit_code


def _graph(args: object) -> object:
    from dotenv import load_dotenv

    from kernel.graph_env import build_graph_from_env

    load_dotenv(Path(args.env_file), override=False)  # type: ignore[attr-defined]
    return build_graph_from_env()


def _against_the_record(verdicts: tuple[ReplayVerdict, ...], args: object) -> str:
    truth = recorded_verdicts(_graph(args))  # type: ignore[arg-type]
    return agreement_with(
        verdicts,
        truth,
        name="agreement_with_recorded_verdict",
        arm=args.arm,  # type: ignore[attr-defined]
    ).detail()


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
