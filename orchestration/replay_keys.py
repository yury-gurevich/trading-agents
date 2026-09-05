"""Stable identities for one replayed debate turn.

Agent: orchestration
Role: name every replayed turn so a batch result can be matched back to the
      debate, repeat and arm it came from — and so a mismatch is impossible
      rather than merely unlikely.
External I/O: none.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from kernel.llm_ledger import digest_text

__all__ = ["JUDGE_ROUND", "ReplayKey"]

# The Batch API bounds a custom_id by charset and length, so the readable label
# is sanitised and truncated — then made unique again by a digest of the *whole*
# label. Truncation can therefore never silently merge two different turns.
_UNSAFE = re.compile(r"[^A-Za-z0-9_-]")
_SLUG_LIMIT = 48
_DIGEST_CHARS = 12

JUDGE_ROUND = 0


@dataclass(frozen=True)
class ReplayKey:
    """Which debate, which repeat, which arm, and which turn within it."""

    pm_run: str
    ticker: str
    repeat: int
    arm: str
    role: str
    round: int

    @property
    def debate(self) -> tuple[str, str, int, str]:
        """The four fields whose turns share one transcript."""
        return (self.pm_run, self.ticker, self.repeat, self.arm)

    def label(self) -> str:
        """The readable identity, in the shape the sprint spec named."""
        return ":".join(
            (
                self.pm_run,
                self.ticker,
                str(self.repeat),
                self.arm,
                self.role,
                f"r{self.round}",
            )
        )

    def custom_id(self) -> str:
        """The wire-safe batch identity for this turn."""
        label = self.label()
        slug = _UNSAFE.sub("_", label)[:_SLUG_LIMIT]
        return f"{slug}-{digest_text(label)[:_DIGEST_CHARS]}"
