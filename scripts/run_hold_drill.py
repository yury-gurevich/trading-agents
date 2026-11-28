"""Run the hold drill: a held run asks the operator on a test bot and acts on the press.

Agent: tooling
Role: work-queue 120 (a) (DL-330): read the env file without loading it, refuse an
      unsafe start, then run two rounds of the dispatcher's own fire on an in-memory
      graph (Run now, then Skip today) and print what each round sent, recorded and did.
External I/O: reads the env file; Telegram's Bot API as the test bot; stdout.

Run it from the main checkout, which holds the only .env:
  .venv/Scripts/python.exe scripts/run_hold_drill.py
  .venv/Scripts/python.exe scripts/run_hold_drill.py --poll-seconds 300
The second form answers a press as late as the fleet's ten-minute fires can.
Exit code: 0 when both rounds pass, 1 when one does not, 2 when refused.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from orchestration.hold_drill_guard import (  # noqa: E402
    DrillRefusedError,
    bot_id,
    drill_values,
)


def main(argv: list[str] | None = None) -> int:
    """Refuse, or run both rounds and print each one's verdict."""
    args = _parser().parse_args(argv)
    from dotenv import dotenv_values

    now = _now()
    try:
        values = drill_values(os.environ, dotenv_values(args.env_file), now=now)
    except DrillRefusedError as refused:
        print(f"REFUSED: {refused}")
        return 2
    from orchestration.hold_drill import Drill, run_drill
    from orchestration.settings import OrchestratorSettings
    from orchestration.telegram_client import TelegramClient

    print(
        f"HOLD DRILL  test bot {bot_id(values.bot_token)}, a poll every "
        f"{args.poll_seconds} s, at most {args.wait_minutes} min a round"
    )
    drill = Drill(
        telegram=TelegramClient(api_token=values.bot_token, chat_id=values.chat_id),
        settings=OrchestratorSettings(_env_file=None),
        poll_seconds=args.poll_seconds,
        wait_seconds=args.wait_minutes * 60,
        sleep=_sleep,
        report=print,
    )
    passed = run_drill(drill, today=now.date())
    print(f"HOLD DRILL  {sum(passed)} of {len(passed)} rounds passed")
    return 0 if all(passed) else 1


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _sleep(seconds: float) -> None:
    time.sleep(seconds)


def _bounded(low: int, high: int) -> Callable[[str], int]:
    def parse(raw: str) -> int:
        value = int(raw)
        if not low <= value <= high:
            raise argparse.ArgumentTypeError(f"must be {low} to {high}")
        return value

    return parse


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="the hold drill on a test bot")
    parser.add_argument("--env-file", default=".env", help="the env file to read")
    parser.add_argument(
        "--poll-seconds", type=_bounded(1, 600), default=5, help="seconds between polls"
    )
    parser.add_argument(
        "--wait-minutes", type=_bounded(1, 30), default=10, help="wait for each press"
    )
    return parser


if __name__ == "__main__":
    sys.exit(main())
