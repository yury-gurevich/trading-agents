"""Derived deployment floor for concentration gates.

Agent: portfolio_manager
Role: derive when deployed-book concentration ratios are meaningful.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

_ZERO = Decimal("0")
_ONE = Decimal("1")


def floor_pct(
    *,
    max_names_per_sector: int,
    max_position_pct: Decimal,
    concentration_cap: Decimal | float,
) -> Decimal:
    """Return the derived deployment floor share of equity."""
    cap = _decimal(concentration_cap)
    if max_names_per_sector <= 0 or max_position_pct <= _ZERO or cap <= _ZERO:
        return _ZERO
    return Decimal(max_names_per_sector) * max_position_pct / cap


def deployment_pct(deployed_value: Decimal, equity_value: Decimal) -> Decimal:
    """Return deployed capital as a share of equity."""
    if equity_value <= _ZERO:
        return _ZERO
    return deployed_value / equity_value


def is_below_floor(
    *,
    deployed_value: Decimal,
    equity_value: Decimal,
    max_names_per_sector: int,
    max_position_pct: Decimal,
    concentration_cap: Decimal | float,
) -> bool:
    """Return whether a concentration gate should be not-evaluated."""
    floor = floor_pct(
        max_names_per_sector=max_names_per_sector,
        max_position_pct=max_position_pct,
        concentration_cap=concentration_cap,
    )
    return floor > _ZERO and deployment_pct(deployed_value, equity_value) < floor


def detail(
    *,
    deployed_value: Decimal,
    equity_value: Decimal,
    max_names_per_sector: int,
    max_position_pct: Decimal,
    concentration_cap: Decimal | float,
    denominator_name: str = "deployed_capital",
) -> str:
    """Return a stable detail fragment for floor-suppressed gates."""
    floor = floor_pct(
        max_names_per_sector=max_names_per_sector,
        max_position_pct=max_position_pct,
        concentration_cap=concentration_cap,
    )
    deployed = deployment_pct(deployed_value, equity_value)
    return (
        f"denominator={denominator_name}; reason=deployment_below_floor; "
        f"deployed_portfolio_usd={deployed_value:.2f}; "
        f"portfolio_value_usd={equity_value:.2f}; "
        f"deployment_pct={deployed:.4f}; deployment_floor_pct={floor:.4f}"
    )


def _decimal(value: Decimal | float) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
