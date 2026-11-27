"""Run one pipeline pass on the test lane: the test paper account and the lane's graph.

Agent: tooling
Role: the test run beside the fleet (work-queue 136 option A, DL-328): read the env
      file without loading it, refuse an unsafe start, rewrite this process's
      environment so only the lane's endpoints remain, then drive one lane run
      through the nine run-path stages and print each round and the acceptance verdict.
External I/O: reads the env file; the lane's PostgreSQL (LANE_POSTGRES_DSN); the test
      Alpaca paper account (orders, positions, account); market-data feeds; stdout.

Run it from the main checkout, which holds the only .env:
  uv run python scripts/run_lane.py                       # the fleet's universe
  uv run python scripts/run_lane.py --tickers AAPL,MSFT,KO
Exit code: 0 when the acceptance verdict passes, 1 when it does not, 2 when refused.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from orchestration.lane_guard import LaneRefusedError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Refuse or isolate, then run one lane run and print what it did."""
    args = _parser().parse_args(argv)
    from dotenv import dotenv_values

    from orchestration.lane_env import isolate_lane, load_tunables_pack

    now = _now()
    try:
        isolate_lane(
            os.environ,
            dotenv_values(args.env_file),
            now=now,
            pack=load_tunables_pack(),
        )
        return _run(args, now)
    except LaneRefusedError as refused:
        print(f"REFUSED: {refused}")
        return 2


def _run(args: argparse.Namespace, now: datetime) -> int:
    from agents.execution.broker_factory import broker_from_settings
    from agents.execution.settings import ExecutionSettings
    from agents.provider.entrypoint import build_agent
    from agents.provider.settings import ProviderSettings
    from kernel.graph_env import build_graph_from_env
    from orchestration.lane_debate import fake_debate_models
    from orchestration.lane_run import lane_run_id, last_closed_session, run_lane
    from orchestration.lane_stages import build_stages
    from orchestration.packs.trading_acceptance import render_acceptance

    graph = build_graph_from_env()
    stages = build_stages(
        graph,
        provider_agent=build_agent(ProviderSettings(), graph),
        broker=broker_from_settings(ExecutionSettings()),
        models=fake_debate_models(),
    )
    tickers = _tickers(args.tickers)
    print(f"LANE RUN  {len(tickers)} tickers, at most {args.max_rounds} rounds")
    as_of = last_closed_session(now)
    result = run_lane(
        graph,
        stages,
        tickers=tickers,
        run_id=lane_run_id(now),
        as_of=as_of,
        max_rounds=args.max_rounds,
    )
    print(f"  run id   {result.run_id}  (session {as_of.isoformat()})")
    for report in result.rounds:
        moved = ", ".join(f"{k} {v}" for k, v in report.advanced.items() if v)
        broke = ", ".join(f"{k} {v}" for k, v in report.failed.items() if v)
        print(f"  round {report.number:>2}  advanced: {moved or '-'}")
        print(f"            failed:   {broke or '-'}")
    print(render_acceptance(result.acceptance))
    return 0 if result.acceptance.passed else 1


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _tickers(raw: str) -> tuple[str, ...]:
    if raw:
        return tuple(t.strip().upper() for t in raw.split(",") if t.strip())
    from agents.scanner.universe import FileUniverse
    from orchestration.settings import OrchestratorSettings

    return FileUniverse().members(OrchestratorSettings().universe)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="one run on the test lane")
    parser.add_argument("--env-file", default=".env", help="the env file to read")
    parser.add_argument(
        "--tickers", default="", help="comma-separated tickers; default the fleet's"
    )
    parser.add_argument("--max-rounds", type=int, default=12, help="round limit")
    return parser


if __name__ == "__main__":
    sys.exit(main())
