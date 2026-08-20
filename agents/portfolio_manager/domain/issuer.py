"""Issuer identity helpers for Portfolio Manager concentration gates.

Agent: portfolio_manager
Role: collapse tickers into issuer keys without importing trading-pack modules.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


def issuer_key(ticker: str, issuer_map: Mapping[str, str]) -> str:
    """Return the issuer key for *ticker*; absent map entries are single-class."""
    symbol = ticker.upper()
    return issuer_map.get(symbol, symbol)
