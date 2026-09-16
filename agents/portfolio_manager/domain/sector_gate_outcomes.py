"""Sector concentration gate outcome helpers.

Agent: portfolio_manager
Role: build sector-label gate outcomes that SectorBook wires into decisions.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.portfolio_manager.domain import deployment_floor
from contracts.portfolio_manager import GateOutcome, GateStatus

if TYPE_CHECKING:
    from decimal import Decimal


def not_evaluated_outcomes(
    ticker: str, max_sector_pct: Decimal, max_names_per_sector: int
) -> tuple[GateOutcome, ...]:
    """Return explicit not-evaluated outcomes for a missing sector label."""
    outcomes = [
        GateOutcome(
            name="max_sector_pct",
            value=0.0,
            threshold=float(max_sector_pct),
            outcome=GateStatus.NOT_EVALUATED,
            detail=f"ticker={ticker}; missing_input=sector_label",
        )
    ]
    if max_names_per_sector > 0:
        outcomes.append(
            GateOutcome(
                name="max_names_per_sector",
                value=0.0,
                threshold=float(max_names_per_sector),
                outcome=GateStatus.NOT_EVALUATED,
                detail=f"ticker={ticker}; missing_input=sector_label",
            )
        )
    return tuple(outcomes)


def sector_exposure_outcome(
    *,
    sector: str,
    held_value: Decimal,
    batch_value: Decimal,
    cost: Decimal,
    equity_value: Decimal,
    deployed_value: Decimal,
    max_sector_pct: Decimal,
    max_position_pct: Decimal,
    max_names_per_sector: int,
    denominator_name: str = "deployed_capital",
) -> GateOutcome:
    """Return the held-plus-batch sector exposure outcome."""
    total = held_value + batch_value + cost
    if max_sector_pct < 1 and (
        deployed_value <= 0
        or deployment_floor.is_below_floor(
            deployed_value=deployed_value,
            equity_value=equity_value,
            max_names_per_sector=max_names_per_sector,
            max_position_pct=max_position_pct,
            concentration_cap=max_sector_pct,
        )
    ):
        return GateOutcome(
            name="max_sector_pct",
            value=0.0,
            threshold=float(max_sector_pct),
            outcome=GateStatus.NOT_EVALUATED,
            detail=(
                f"sector={sector}; "
                + deployment_floor.detail(
                    deployed_value=deployed_value,
                    equity_value=equity_value,
                    max_names_per_sector=max_names_per_sector,
                    max_position_pct=max_position_pct,
                    concentration_cap=max_sector_pct,
                    denominator_name=denominator_name,
                )
            ),
        )
    value = ratio(total, deployed_value)
    return GateOutcome(
        name="max_sector_pct",
        value=value,
        threshold=float(max_sector_pct),
        outcome=(
            GateStatus.PASSED if value <= float(max_sector_pct) else GateStatus.FAILED
        ),
        detail=(
            f"sector={sector}; held_sector_value_usd={held_value:.2f}; "
            f"deployed_this_batch_usd={batch_value:.2f}; "
            f"order_cost_usd={cost:.2f}; "
            f"denominator={denominator_name}; "
            f"deployed_portfolio_usd={deployed_value:.2f}; "
            f"portfolio_value_usd={equity_value:.2f}"
        ),
    )


def sector_names_outcome(
    *,
    sector: str,
    issuer: str,
    existing_issuers: int,
    is_new: bool,
    max_names_per_sector: int,
) -> GateOutcome:
    """Return the issuer-count outcome for one sector label."""
    names_after = existing_issuers + int(is_new)
    return GateOutcome(
        name="max_names_per_sector",
        value=float(names_after),
        threshold=float(max_names_per_sector),
        outcome=(
            GateStatus.PASSED
            if (not is_new) or existing_issuers < max_names_per_sector
            else GateStatus.FAILED
        ),
        detail=(
            f"sector={sector}; issuer={issuer}; "
            f"existing_sector_issuers={existing_issuers}; "
            f"is_new_issuer={str(is_new).lower()}"
        ),
    )


def exit_outcomes_for_sector(
    sector: str, issuer_count: int, max_names_per_sector: int
) -> tuple[GateOutcome, ...]:
    """Return concentration evidence for a sell that reduces exposure."""
    outcomes = [
        GateOutcome(
            name="max_sector_pct",
            value=0.0,
            threshold=1.0,
            outcome=GateStatus.PASSED,
            detail=f"sector={sector}; sell reduces sector deployment",
        )
    ]
    if max_names_per_sector > 0:
        outcomes.append(
            GateOutcome(
                name="max_names_per_sector",
                value=float(max(0, issuer_count - 1)),
                threshold=float(max_names_per_sector),
                outcome=GateStatus.PASSED,
                detail=f"sector={sector}; sell reduces held sector issuers",
            )
        )
    return tuple(outcomes)


def ratio(numerator: Decimal, denominator: Decimal) -> float:
    """Return a safe decimal ratio for gate evidence."""
    return 0.0 if denominator <= 0 else float(numerator / denominator)
