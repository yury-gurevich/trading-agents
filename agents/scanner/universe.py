"""Scanner universe sources.

Agent: scanner
Role: provide configured, non-network universe membership to the scanner.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from contracts.common import Ticker

_DEFAULT_UNIVERSE = ("AAPL", "MSFT", "NVDA", "SPY")


class UniverseSource(Protocol):
    """Configured universe membership source."""

    def members(self, universe: str) -> tuple[Ticker, ...]:
        """Return tickers belonging to a named universe."""
        ...  # pragma: no cover - protocol declaration only.


class StaticUniverse:
    """Static configured universe source for local runs."""

    def __init__(self, universes: dict[str, tuple[Ticker, ...]] | None = None) -> None:
        """Create a source with an optional map of named universes."""
        self._universes = universes or {"sp500": _DEFAULT_UNIVERSE}

    def members(self, universe: str) -> tuple[Ticker, ...]:
        """Return configured members for a named universe."""
        return self._universes.get(universe, ())


class FakeUniverse(StaticUniverse):
    """Explicit test universe source."""
