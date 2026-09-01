"""Sector and issuer concentration book for Portfolio Manager.

Agent: portfolio_manager
Role: track held and tentative issuer exposure for sector-label gates.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.issuer import issuer_key
from agents.portfolio_manager.domain.sector_gate_outcomes import (
    exit_outcomes_for_sector,
    not_evaluated_outcomes,
    sector_exposure_outcome,
    sector_names_outcome,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from contracts.analyst import Recommendation
    from contracts.common import Money
    from contracts.portfolio_manager import GateOutcome

_ZERO = Decimal("0")


class SectorBook:
    """Running per-sector dollar deployment and open-issuer counts."""

    def __init__(
        self,
        sectors: Mapping[str, str],
        held: Iterable[str],
        *,
        held_values: Mapping[str, Money] | None = None,
        issuer_map: Mapping[str, str] | None = None,
    ) -> None:
        """Seed the book with sectors and values of already-held positions."""
        self._sectors = {ticker.upper(): sector for ticker, sector in sectors.items()}
        self._issuer_map = issuer_map or {}
        self._held_tickers = {ticker.upper() for ticker in held}
        self._held_values: dict[str, Decimal] = {}
        self._batch_values: dict[str, Decimal] = {}
        self._sector_issuers: dict[str, set[str]] = {}
        self._issuer_tickers: dict[str, set[str]] = {}
        self._issuer_values: dict[str, Decimal] = {}
        self._ticker_values: dict[str, Decimal] = {}
        for ticker in self._held_tickers:
            value = _value(held_values, ticker)
            issuer = self.issuer_for(ticker)
            self._ticker_values[ticker] = value
            self._issuer_values[issuer] = self._issuer_values.get(issuer, _ZERO) + value
            self._issuer_tickers.setdefault(issuer, set()).add(ticker)
            sector = self._sector(ticker)
            if sector is not None:
                self._held_values[sector] = self._held_values.get(sector, _ZERO) + value
                self._sector_issuers.setdefault(sector, set()).add(issuer)

    def issuer_for(self, ticker: str) -> str:
        """Return the issuer key used by every concentration gate."""
        return issuer_key(ticker, self._issuer_map)

    def issuer_value(self, issuer: str) -> Decimal:
        """Return held plus tentative exposure for one issuer."""
        return self._issuer_values.get(issuer, _ZERO)

    def issuer_values(self) -> dict[str, Decimal]:
        """Return issuer exposures visible to correlation gates."""
        return dict(self._issuer_values)

    def issuer_tickers(self) -> dict[str, tuple[str, ...]]:
        """Return held/tentative tickers grouped by issuer."""
        return {
            issuer: tuple(sorted(tickers))
            for issuer, tickers in self._issuer_tickers.items()
        }

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
        sector = self._sector(item.ticker)
        if (
            sector is None
            and max_sector_pct >= Decimal("1")
            and max_names_per_sector <= 0
        ):
            return ()
        if sector is None:
            return not_evaluated_outcomes(
                item.ticker,
                max_sector_pct,
                max_names_per_sector,
            )
        issuer = self.issuer_for(item.ticker)
        issuers = self._sector_issuers.get(sector, set())
        is_new = issuer not in issuers
        held_value = self._held_values.get(sector, _ZERO)
        batch_value = self._batch_values.get(sector, _ZERO)
        outcomes = [
            sector_exposure_outcome(
                sector=sector,
                held_value=held_value,
                batch_value=batch_value,
                cost=cost,
                portfolio_value=portfolio_value,
                max_sector_pct=max_sector_pct,
            )
        ]
        if max_names_per_sector > 0:
            outcomes.append(
                sector_names_outcome(
                    sector=sector,
                    issuer=issuer,
                    existing_issuers=len(issuers),
                    is_new=is_new,
                    max_names_per_sector=max_names_per_sector,
                )
            )
        return tuple(outcomes)

    def record(self, item: Recommendation, cost: Decimal) -> None:
        """Commit an approved order to running sector and issuer totals."""
        ticker = item.ticker.upper()
        issuer = self.issuer_for(ticker)
        self._issuer_values[issuer] = self._issuer_values.get(issuer, _ZERO) + cost
        self._issuer_tickers.setdefault(issuer, set()).add(ticker)
        self._ticker_values[ticker] = self._ticker_values.get(ticker, _ZERO) + cost
        sector = self._sector(ticker)
        if sector is None:
            return
        self._batch_values[sector] = self._batch_values.get(sector, _ZERO) + cost
        self._sector_issuers.setdefault(sector, set()).add(issuer)
        self._held_tickers.add(ticker)

    def exit_outcomes(
        self, item: Recommendation, max_names_per_sector: int
    ) -> tuple[GateOutcome, ...]:
        """Return concentration evidence for a sell that reduces exposure."""
        sector = self._sector(item.ticker)
        if sector is None:
            return ()
        issuers = self._sector_issuers.get(sector, set())
        return exit_outcomes_for_sector(sector, len(issuers), max_names_per_sector)

    def record_exit(self, ticker: str) -> None:
        """Commit an approved exit to running sector and issuer totals."""
        symbol = ticker.upper()
        issuer = self.issuer_for(symbol)
        value = self._ticker_values.pop(symbol, _ZERO)
        self._held_tickers.discard(symbol)
        self._issuer_values[issuer] = max(
            _ZERO, self._issuer_values.get(issuer, _ZERO) - value
        )
        self._issuer_tickers.get(issuer, set()).discard(symbol)
        if not self._issuer_tickers.get(issuer):
            self._issuer_tickers.pop(issuer, None)
            self._issuer_values.pop(issuer, None)
        sector = self._sector(symbol)
        if sector is None:
            return
        self._held_values[sector] = max(
            _ZERO, self._held_values.get(sector, _ZERO) - value
        )
        if issuer not in self._issuer_tickers:
            self._sector_issuers.get(sector, set()).discard(issuer)

    def _sector(self, ticker: str) -> str | None:
        return self._sectors.get(ticker.upper())


def _value(held_values: Mapping[str, Money] | None, ticker: str) -> Decimal:
    if held_values is None:
        return _ZERO
    money = held_values.get(ticker) or held_values.get(ticker.upper())
    return _ZERO if money is None else money.amount
