"""Market-pack query projections.

Agent: surfaces
Role: project registered market packs into display-ready views.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import MarketPackRegistry


@dataclass(frozen=True)
class PackView:
    """Operator-facing view of one registered market pack."""

    name: str
    exchange: str
    universe_name: str
    max_stage: str
    ready: bool
    ready_reason: str


def all_packs(registry: MarketPackRegistry) -> tuple[PackView, ...]:
    """Return display-ready views for all registered market packs."""
    return tuple(
        PackView(
            name=pack.name,
            exchange=pack.exchange,
            universe_name=pack.universe_name,
            max_stage=pack.max_stage,
            ready=ready,
            ready_reason=reason,
        )
        for pack in registry.all_packs()
        for ready, reason in (pack.is_ready(),)
    )
