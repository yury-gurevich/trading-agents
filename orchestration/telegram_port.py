"""Minimal Telegram operations required by the scheduled dispatcher.

Agent: orchestration
Role: type the injected Telegram boundary.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from orchestration.telegram_updates import TelegramAnswer


class TelegramPort(Protocol):
    """Operations used to announce, read, and settle a held-run answer."""

    def send_hold_notice(
        self, *, run_id: str, failures: tuple[str, ...], act_by: str
    ) -> int | None:
        """Send the two-choice notification for one newly held run."""
        ...  # pragma: no cover - protocol declaration only.

    def poll_answers(self) -> tuple[TelegramAnswer, ...]:
        """Return valid callback answers awaiting local recording."""
        ...  # pragma: no cover - protocol declaration only.

    def ack_button(self, *, callback_query_id: str, text: str) -> bool:
        """Acknowledge one callback in Telegram's user interface."""
        ...  # pragma: no cover - protocol declaration only.

    def confirm(self, *, up_to_update_id: int) -> bool:
        """Advance the remote update cursor through one handled update."""
        ...  # pragma: no cover - protocol declaration only.
