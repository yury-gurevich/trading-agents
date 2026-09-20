"""Bounded Telegram notices and callback polling for dispatcher holds.

Agent: orchestration
Role: send held-run notices and read only legal callback answers.
External I/O: Telegram HTTPS through an injected sender.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from functools import partial

from orchestration.telegram_http import send_request
from orchestration.telegram_updates import TelegramAnswer, parse_answer

Sender = Callable[[str, dict[str, object], float], object]


class TelegramClient:
    """Small Telegram port that turns boundary failures into falsy results."""

    def __init__(
        self,
        *,
        api_token: str,
        chat_id: str,
        sender: Sender | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        """Store boundary configuration and an optional test sender."""
        self._api_token = api_token
        self._chat_id = chat_id
        self._sender = sender or partial(send_request, self._api_token)
        self._timeout_seconds = timeout_seconds
        self.last_error = ""

    def send_hold_notice(
        self, *, run_id: str, failures: tuple[str, ...], act_by: str
    ) -> int | None:
        """Send one held-run notice with the two legal answers."""
        failures_text = "; ".join(failures) or "no failure detail recorded"
        text = (
            f"Run {run_id} is held. Checks: {failures_text}. "
            f"Choose Run now by {act_by}. Your answer is checked every 10 minutes. "
            f"After {act_by}, it is recorded but cannot start a run today."
        )
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "Run now", "callback_data": f"run_now:{run_id}"},
                    {"text": "Skip today", "callback_data": f"skip_today:{run_id}"},
                ]
            ]
        }
        response = self._request(
            "sendMessage",
            {"chat_id": self._chat_id, "text": text, "reply_markup": reply_markup},
        )
        result = response.get("result") if response else None
        message_id = result.get("message_id") if isinstance(result, Mapping) else None
        if not isinstance(message_id, int):
            self.last_error = "telegram_message_id_missing"
            return None
        return message_id

    def poll_answers(self) -> tuple[TelegramAnswer, ...]:
        """Return valid callback answers while ignoring all other update shapes."""
        response = self._request("getUpdates", {})
        updates = response.get("result") if response else ()
        if not isinstance(updates, list):
            return ()
        answers = (parse_answer(update) for update in updates)
        return tuple(answer for answer in answers if answer is not None)

    def confirm(self, *, up_to_update_id: int) -> bool:
        """Advance Telegram's cursor without creating local mutable state."""
        return self._request("getUpdates", {"offset": up_to_update_id + 1}) is not None

    def ack_button(self, *, callback_query_id: str, text: str) -> bool:
        """Acknowledge one callback so Telegram stops showing a pending control."""
        return (
            self._request(
                "answerCallbackQuery",
                {"callback_query_id": callback_query_id, "text": text},
            )
            is not None
        )

    def _request(
        self, method: str, payload: dict[str, object]
    ) -> Mapping[str, object] | None:
        self.last_error = ""
        try:
            response = self._sender(method, payload, self._timeout_seconds)
        except Exception as exc:
            self.last_error = type(exc).__name__
            return None
        if not isinstance(response, Mapping) or response.get("ok") is not True:
            self.last_error = "telegram_response_invalid"
            return None
        return response
