"""Telegram callback parsing for held-run decisions.

Agent: orchestration
Role: convert Telegram update payloads into legal dispatcher answers.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, cast

Answer = Literal["run_now", "skip_today"]
_ANSWERS = frozenset(("run_now", "skip_today"))


@dataclass(frozen=True)
class TelegramAnswer:
    """One valid answer extracted from a Telegram callback update."""

    update_id: int
    answer: Answer
    run_id: str
    callback_query_id: str


def parse_answer(update: object) -> TelegramAnswer | None:
    """Return a legal callback answer, or none for every other update shape."""
    if not isinstance(update, Mapping) or not isinstance(update.get("update_id"), int):
        return None
    callback = update.get("callback_query")
    if not isinstance(callback, Mapping) or not isinstance(callback.get("id"), str):
        return None
    data = callback.get("data")
    if not isinstance(data, str) or ":" not in data:
        return None
    answer, run_id = data.split(":", maxsplit=1)
    if answer not in _ANSWERS or not run_id:
        return None
    return TelegramAnswer(
        update["update_id"], cast("Answer", answer), run_id, callback["id"]
    )
