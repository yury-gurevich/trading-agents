"""Batch-level sentiment headline weights.

Agent: analyst
Role: derive duplicate-headline weights from the already-fetched news batch.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping


def batch_headline_weights(
    news_by_ticker: Mapping[str, Iterable[str]],
) -> dict[str, float]:
    """Return each exact headline's 1/n weight across distinct batch tickers."""
    owners: dict[str, set[str]] = {}
    for ticker, headlines in news_by_ticker.items():
        for headline in headlines:
            owners.setdefault(headline, set()).add(ticker)
    return {headline: 1.0 / len(tickers) for headline, tickers in owners.items()}
