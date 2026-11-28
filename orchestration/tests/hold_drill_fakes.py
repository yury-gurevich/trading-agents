"""Synthetic Bot API for the hold drill.

Agent: orchestration
Role: provide queued presses and injected waiting for DL-330 tooling tests.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from orchestration.hold_drill import Drill
from orchestration.settings import OrchestratorSettings
from orchestration.telegram_client import TelegramClient

TODAY = date(2026, 11, 28)
SAFE_NOW = datetime(2026, 11, 28, 6, 0, tzinfo=UTC)
TEST_BOT_VALUE = "7000000001:test-drill-key"  # pragma: allowlist secret
FLEET_BOT_VALUE = "8000000002:fleet-key"  # pragma: allowlist secret


class FakeBot:
    """Keep sent messages and unread callback updates as the Bot API does."""

    def __init__(
        self, *, send_ok: bool = True, ack_ok: bool = True, confirm_ok: bool = True
    ) -> None:
        self.send_ok = send_ok
        self.ack_ok = ack_ok
        self.confirm_ok = confirm_ok
        self.sent: list[tuple[str, list[str]]] = []
        self.acks: list[str] = []
        self.updates: list[dict[str, Any]] = []
        self._next_id = 501

    def __call__(self, method: str, payload: dict[str, Any], timeout: float) -> object:
        """Answer one synthetic request without contacting Telegram."""
        if method == "sendMessage":
            buttons = [
                button["callback_data"]
                for row in payload.get("reply_markup", {}).get("inline_keyboard", [])
                for button in row
            ]
            self.sent.append((payload["text"], buttons))
            return {
                "ok": self.send_ok,
                "result": {"message_id": 100 + len(self.sent)},
            }
        if method == "getUpdates":
            if "offset" in payload:
                if not self.confirm_ok:
                    return {"ok": False, "description": "confirmation refused"}
                self.updates = [
                    item
                    for item in self.updates
                    if item["update_id"] >= payload["offset"]
                ]
            return {"ok": True, "result": list(self.updates)}
        assert method == "answerCallbackQuery"
        self.acks.append(payload["callback_query_id"])
        return {"ok": self.ack_ok, "result": True}

    def press(self, answer: str, run_id: str) -> None:
        """Queue a new callback with a monotonically increasing update id."""
        update_id = self._next_id
        self._next_id += 1
        self.updates.append(
            {
                "update_id": update_id,
                "callback_query": {
                    "id": f"cb{update_id}",
                    "data": f"{answer}:{run_id}",
                },
            }
        )

    def notices(self) -> list[tuple[str, list[str]]]:
        """Return only messages carrying answer buttons."""
        return [message for message in self.sent if message[1]]


def drill_on(
    bot: FakeBot, presses: list[tuple[str, str]], lines: list[str], *, wait: int = 30
) -> tuple[Drill, list[float]]:
    """Build a real TelegramClient with a fake API and a sleep that presses."""
    slept: list[float] = []
    queued = iter(presses)

    def sleep(seconds: float) -> None:
        slept.append(seconds)
        if (press := next(queued, None)) is not None:
            bot.press(*press)

    return Drill(
        telegram=TelegramClient(api_token=TEST_BOT_VALUE, chat_id="42", sender=bot),
        settings=OrchestratorSettings(_env_file=None),
        poll_seconds=5,
        wait_seconds=wait,
        sleep=sleep,
        report=lines.append,
    ), slept
