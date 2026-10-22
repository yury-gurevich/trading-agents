"""EXP-015's folds: expanding train, purge and embargo before each test (S289).

Agent: tooling
Role: name each fold's train and test sessions from the panel's calendar, the train
      window ending PURGE + EMBARGO sessions before the test begins.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from scripts.exp015_spec import EMBARGO_SESSIONS, PURGE_SESSIONS

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True)
class Fold:
    name: str
    train: tuple[str, ...]  # ISO sessions
    test: tuple[str, ...]

    def record(self) -> dict[str, object]:
        """The fold's date ranges and sizes, as the results record them."""
        return {
            "name": self.name,
            "train_first": self.train[0] if self.train else None,
            "train_last": self.train[-1] if self.train else None,
            "train_sessions": len(self.train),
            "test_first": self.test[0] if self.test else None,
            "test_last": self.test[-1] if self.test else None,
            "test_sessions": len(self.test),
        }


def fold(name: str, sessions: Sequence[date], first: date, last: date) -> Fold:
    """Test on [first, last]; train on every earlier session but purge and embargo."""
    test = [day for day in sessions if first <= day <= last]
    if not test:
        raise ValueError(f"fold {name}: no session in {first}..{last}")
    start = list(sessions).index(test[0])
    gap = PURGE_SESSIONS + EMBARGO_SESSIONS
    train = sessions[: max(start - gap, 0)]
    return Fold(
        name, tuple(d.isoformat() for d in train), tuple(d.isoformat() for d in test)
    )


def walk_forward(sessions: Sequence[date], years: Sequence[int]) -> tuple[Fold, ...]:
    """One annual test fold per year, each with its own expanding train window."""
    return tuple(
        fold(str(year), sessions, date(year, 1, 1), date(year, 12, 31))
        for year in years
    )


def holdout(sessions: Sequence[date], start: date) -> Fold:
    """The holdout: `start` to the last session, trained on everything before it."""
    return fold("holdout", sessions, start, sessions[-1])
