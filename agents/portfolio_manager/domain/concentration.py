"""Sector-concentration book for the Portfolio Manager risk gate.

Agent: portfolio_manager
Role: bound correlated-name concentration per sector — both the dollar weight
      (``max_sector_pct``) and the NUMBER of names (``max_names_per_sector``). A
      basket of small correlated names is still one bet, which the dollar cap alone
      misses: five names at 5 % each clear a 30 % cap yet are one exposure. The
      deliberation firewall named this gap (EXP-004..006) after the live book opened
      four correlated semiconductors; this is the "name-correlation penalty" in
      deterministic form.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from contracts.portfolio_manager import RejectedOrder

if TYPE_CHECKING:
    from collections.abc import Iterable

    from contracts.analyst import Recommendation


class SectorBook:
    """Running per-sector dollar deployment and open-name counts."""

    def __init__(self, sectors: dict[str, str], held: Iterable[str]) -> None:
        """Seed the book with the sectors of already-held positions."""
        self._sectors = sectors
        self._held = set(held)
        self._deployed: dict[str, Decimal] = {}
        self._names: dict[str, int] = {}
        for ticker in self._held:
            sector = sectors.get(ticker)
            if sector is not None:
                self._names[sector] = self._names.get(sector, 0) + 1

    def rejection(
        self,
        item: Recommendation,
        cost: Decimal,
        portfolio_value: Decimal,
        *,
        max_sector_pct: Decimal,
        max_names_per_sector: int,
    ) -> RejectedOrder | None:
        """Reject when this order breaches the name-count or the dollar cap."""
        sector = self._sectors.get(item.ticker)
        if sector is None:
            return None
        is_new = item.ticker not in self._held
        names = self._names.get(sector, 0)
        if is_new and 0 < max_names_per_sector <= names:
            return RejectedOrder(ticker=item.ticker, reason="sector_name_count")
        deployed = self._deployed.get(sector, Decimal("0"))
        if deployed + cost > max_sector_pct * portfolio_value:
            return RejectedOrder(ticker=item.ticker, reason="sector_concentration")
        return None

    def record(self, item: Recommendation, cost: Decimal) -> None:
        """Commit an approved order to the running sector totals."""
        sector = self._sectors.get(item.ticker)
        if sector is None:
            return
        self._deployed[sector] = self._deployed.get(sector, Decimal("0")) + cost
        if item.ticker not in self._held:
            self._names[sector] = self._names.get(sector, 0) + 1
            self._held.add(item.ticker)
