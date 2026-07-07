"""Scanner universe sources.

Agent: scanner
Role: provide configured, non-network universe membership to the scanner.
External I/O: none.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from contracts.common import Ticker

_DEFAULT_UNIVERSE = ("AAPL", "MSFT", "NVDA", "SPY")
_DEFAULT_FILE_UNIVERSES = {"sp500": Path("scripts/universe_sp100.txt")}


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


class FileUniverse:
    """Universe source backed by committed newline-delimited ticker files."""

    def __init__(self, universes: dict[str, Path] | None = None) -> None:
        """Create a source with optional name-to-file mappings."""
        self._universes = universes or _DEFAULT_FILE_UNIVERSES

    def members(self, universe: str) -> tuple[Ticker, ...]:
        """Return configured members for a named file-backed universe."""
        path = self._universes.get(universe)
        return () if path is None else load_universe_file(path)


def load_universe_file(path: str | Path) -> tuple[Ticker, ...]:
    """Read a newline-delimited ticker file, skipping blanks and comments."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    syms = tuple(
        s.strip().upper() for s in lines if s.strip() and not s.lstrip().startswith("#")
    )
    if not syms:
        raise ValueError(f"universe file {path} has no tickers")
    return syms
