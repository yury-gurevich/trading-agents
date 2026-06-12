"""Market-pack protocol and registry.

Agent: kernel
Role: define pack shape and registry plumbing without trading knowledge.
External I/O: none.
"""

from __future__ import annotations

from typing import Protocol


class MarketPack(Protocol):
    """One tradeable universe plus source mapping and stage ceiling."""

    name: str
    exchange: str
    universe_name: str
    data_source_key: str
    max_stage: str

    def is_ready(self) -> tuple[bool, str]:
        """Return readiness and an operator-readable reason."""
        ...  # pragma: no cover - protocol declaration only.


class MarketPackRegistry:
    """Mutable registry of named market packs."""

    def __init__(self) -> None:
        """Create an empty pack registry."""
        self._packs: dict[str, MarketPack] = {}

    def register(self, pack: MarketPack) -> None:
        """Register a pack, replacing any existing pack with the same name."""
        self._packs[pack.name] = pack

    def get(self, name: str) -> MarketPack | None:
        """Return a registered pack by name, if present."""
        return self._packs.get(name)

    def all_packs(self) -> tuple[MarketPack, ...]:
        """Return all registered packs in insertion order."""
        return tuple(self._packs.values())
