"""Small helpers for the replay session loop.

Agent: tooling
Role: render progress and value held replay positions.
External I/O: progress lines to stderr.
"""

from __future__ import annotations

import sys
import time
from decimal import Decimal
from typing import TYPE_CHECKING

from contracts.common import Money

if TYPE_CHECKING:
    from datetime import date

    from scripts.replay_broker import ReplayPosition
    from scripts.sp500_bars import BarRow


def position_values(
    positions: dict[str, ReplayPosition],
    line_bars: dict[str, tuple[BarRow, ...]],
    session: date,
) -> dict[str, Money]:
    """Return held market values from the latest visible close per line."""
    values: dict[str, Money] = {}
    for line, position in positions.items():
        close = _latest_close(line_bars.get(line, ()), session)
        if close is None:
            continue
        price_cents = round(close * 100 * position.price_scale)
        amount = Decimal(position.quantity * price_cents) / Decimal("100")
        values[line] = Money(amount=amount)
    return values


def progress_line(
    session: str,
    count: int,
    total: int,
    equity_cents: int,
    started: float,
    every: int,
) -> None:
    """Print the configured progress line to stderr."""
    if total == 0 or every <= 0:
        return
    if count != total and count % every != 0:
        return
    elapsed = time.perf_counter() - started
    print(
        f"replay progress {session} {count}/{total} "
        f"elapsed={elapsed:.1f}s equity_cents={equity_cents}",
        file=sys.stderr,
    )


def _latest_close(rows: tuple[BarRow, ...], session: date) -> float | None:
    close = None
    for row in rows:
        if row.date > session:
            break
        close = row.close
    return close
