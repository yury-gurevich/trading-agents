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

from contracts.portfolio_manager import GateOutcome, RejectedOrder

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
        for outcome in self.outcomes(
            item,
            cost,
            portfolio_value,
            max_sector_pct=max_sector_pct,
            max_names_per_sector=max_names_per_sector,
        ):
            if outcome.name == "max_names_per_sector" and not outcome.passed:
                return RejectedOrder(ticker=item.ticker, reason="sector_name_count")
            if outcome.name == "max_sector_pct" and not outcome.passed:
                return RejectedOrder(ticker=item.ticker, reason="sector_concentration")
        return None

    def outcomes(
        self,
        item: Recommendation,
        cost: Decimal,
        portfolio_value: Decimal,
        *,
        max_sector_pct: Decimal,
        max_names_per_sector: int,
    ) -> tuple[GateOutcome, ...]:
        """Return explicit sector-gate outcomes for this tentative order."""
        sector = self._sectors.get(item.ticker)
        if sector is None:
            return ()
        is_new = item.ticker not in self._held
        names = self._names.get(sector, 0)
        deployed = self._deployed.get(sector, Decimal("0"))
        outcomes = [
            GateOutcome(
                name="max_sector_pct",
                value=_ratio(deployed + cost, portfolio_value),
                threshold=float(max_sector_pct),
                passed=deployed + cost <= max_sector_pct * portfolio_value,
                detail=(
                    f"sector={sector}; deployed={deployed:.2f}; "
                    f"order_cost={cost:.2f}; portfolio_value={portfolio_value:.2f}"
                ),
            )
        ]
        if max_names_per_sector > 0:
            names_after = names + int(is_new)
            outcomes.append(
                GateOutcome(
                    name="max_names_per_sector",
                    value=float(names_after),
                    threshold=float(max_names_per_sector),
                    passed=(not is_new) or names < max_names_per_sector,
                    detail=(
                        f"sector={sector}; existing_sector_names={names}; "
                        f"is_new_position={str(is_new).lower()}"
                    ),
                )
            )
        return tuple(outcomes)

    def record(self, item: Recommendation, cost: Decimal) -> None:
        """Commit an approved order to the running sector totals."""
        sector = self._sectors.get(item.ticker)
        if sector is None:
            return
        self._deployed[sector] = self._deployed.get(sector, Decimal("0")) + cost
        if item.ticker not in self._held:
            self._names[sector] = self._names.get(sector, 0) + 1
            self._held.add(item.ticker)

    def exit_outcomes(
        self, item: Recommendation, max_names_per_sector: int
    ) -> tuple[GateOutcome, ...]:
        """Return concentration evidence for a sell that reduces exposure."""
        sector = self._sectors.get(item.ticker)
        if sector is None:
            return ()
        names = self._names.get(sector, 0)
        outcomes = [
            GateOutcome(
                name="max_sector_pct",
                value=0.0,
                threshold=1.0,
                passed=True,
                detail=f"sector={sector}; sell reduces sector deployment",
            )
        ]
        if max_names_per_sector > 0:
            outcomes.append(
                GateOutcome(
                    name="max_names_per_sector",
                    value=float(max(0, names - 1)),
                    threshold=float(max_names_per_sector),
                    passed=True,
                    detail=f"sector={sector}; sell reduces held sector names",
                )
            )
        return tuple(outcomes)

    def record_exit(self, ticker: str) -> None:
        """Commit an approved exit to the running sector name counts."""
        sector = self._sectors.get(ticker)
        if sector is None or ticker not in self._held:
            return
        self._held.remove(ticker)
        current = self._names.get(sector, 0)
        if current <= 1:
            self._names.pop(sector, None)
        else:
            self._names[sector] = current - 1


def _ratio(numerator: Decimal, denominator: Decimal) -> float:
    if denominator <= 0:
        return 0.0
    return float(numerator / denominator)
