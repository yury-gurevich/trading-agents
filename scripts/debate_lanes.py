"""Report production debate lanes over memory or disposable live topics.

Agent: tooling
Role: run one JSON report per configuration, followed by the D9 verdict and exit code.
External I/O: none by default; Azure Service Bus only with --transport live.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.debate_lanes_scene import run

from agents.deliberator.settings import DeliberatorSettings
from kernel import AzureServiceBusSettings


class ArgumentError(ValueError):
    """A command argument that cannot be run."""


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ArgumentError(message)


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def nonnegative_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("must be finite and nonnegative")
    return number


def parser() -> Parser:
    result = Parser(description=__doc__)
    result.add_argument("--transport", choices=("memory", "live"), default="memory")
    result.add_argument(
        "--concurrency", type=positive_int, nargs="+", default=[1, 2, 3, 4]
    )
    result.add_argument("--replicas", type=positive_int)
    result.add_argument("--orders", type=positive_int, default=8)
    result.add_argument("--rounds", type=positive_int, default=2)
    result.add_argument("--turn-seconds", type=nonnegative_float, default=0.5)
    result.add_argument("--wait-seconds", type=nonnegative_float, default=5.0)
    result.add_argument("--replica-start-delay", type=nonnegative_float, default=0.0)
    result.add_argument("--requests-a-pass", type=positive_int)
    return result


def main(argv: list[str] | None = None) -> int:
    """Return 0 for clean runs, 1 for counted loss, 2 if a run cannot be made."""
    try:
        args = parser().parse_args(argv)
        if args.wait_seconds <= 0:
            raise ArgumentError("--wait-seconds must be greater than zero")
        # Validate against the production fields before live creates any topic.
        for concurrency in args.concurrency:
            DeliberatorSettings(
                _env_file=None, max_rounds=args.rounds, debate_concurrency=concurrency
            )
        if args.requests_a_pass is not None:
            AzureServiceBusSettings(
                _env_file=None,
                connection_string=None,
                connection_strings_json=None,
                receive_max_messages=args.requests_a_pass,
            )
        failed = []
        for concurrency in args.concurrency:
            report = run(
                transport=args.transport,
                concurrency=concurrency,
                replicas=args.replicas,
                orders=args.orders,
                rounds=args.rounds,
                turn_seconds=args.turn_seconds,
                wait_seconds=args.wait_seconds,
                replica_start_delay=args.replica_start_delay,
                requests_a_pass=args.requests_a_pass,
            )
            print(json.dumps(report), flush=True)
            if not report["clean"]:
                failed.append(concurrency)
        if failed:
            print("LANES NOT CLEAN: " + " ".join(map(str, failed)))
            return 1
        print("LANES CLEAN")
    except (ArgumentError, ValueError) as exc:
        print(f"LANES COULD NOT RUN: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"LANES COULD NOT RUN: {type(exc).__name__}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
