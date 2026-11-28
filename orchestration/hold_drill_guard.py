"""Hold-drill refusals: the drill reaches the operator only through its own test bot.

Agent: orchestration
Role: read the two values a hold drill is built from and refuse a start that could reach
      the fleet's Telegram bot or be read as the fleet's own hold (work-queue 120 (a),
      DL-330): a missing value, a test token that is not a bot token, a test bot that is
      the fleet's, or a start inside the fleet's nightly window.
External I/O: none (reads the mappings and the clock it is handed).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC
from typing import TYPE_CHECKING

from orchestration.lane_guard import FLEET_WINDOW_UTC

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import datetime

DRILL_BOT = "TELEGRAM_TEST_BOT_TOKEN"  # pragma: allowlist secret
FLEET_BOT = "TELEGRAM_BOT_TOKEN"  # pragma: allowlist secret
CHAT = "TELEGRAM_CHAT_ID"


class DrillRefusedError(RuntimeError):
    """A hold-drill start was refused; the message names the condition."""


@dataclass(frozen=True)
class DrillValues:
    """The test bot's token and the operator's chat, read from the env file."""

    bot_token: str = field(repr=False)
    chat_id: str = field(repr=False)


def bot_id(token: str) -> str:
    """Return a bot token's public bot id, the digits before its colon, else ''."""
    head, colon, _ = token.partition(":")
    return head if colon and head.isdigit() else ""


def drill_values(
    environ: Mapping[str, str],
    dotenv: Mapping[str, str | None],
    *,
    now: datetime,
) -> DrillValues:
    """Return the drill's two values; raise DrillRefusedError on any unsafe start."""
    _refuse_window(now)
    token = (dotenv.get(DRILL_BOT) or "").strip()
    chat = (dotenv.get(CHAT) or "").strip()
    missing = [name for name, value in ((DRILL_BOT, token), (CHAT, chat)) if not value]
    if missing:
        raise DrillRefusedError(f"missing drill values: {', '.join(missing)}")
    if not bot_id(token):
        raise DrillRefusedError(
            f"{DRILL_BOT} is not a bot token (digits, a colon, a key)"
        )
    fleet = (dotenv.get(FLEET_BOT) or environ.get(FLEET_BOT) or "").strip()
    if fleet and bot_id(fleet) == bot_id(token):
        raise DrillRefusedError(
            f"{DRILL_BOT} is the fleet's bot: a press left unread would reach the "
            "fleet's next hold"
        )
    return DrillValues(bot_token=token, chat_id=chat)


def _refuse_window(now: datetime) -> None:
    start, end = FLEET_WINDOW_UTC
    if start <= now.astimezone(UTC).time() <= end:
        raise DrillRefusedError(
            "inside the fleet's nightly window (22:00 to 24:00 UTC): a drill notice "
            "could be read as the fleet's own hold"
        )
