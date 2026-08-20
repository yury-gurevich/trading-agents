"""Gate-report fixtures for deliberation veto context tests.

Agent: orchestration
Role: provide compact PM gate outcomes for veto renderer tests.
External I/O: none.
"""

from __future__ import annotations

from contracts.portfolio_manager import GateOutcome, GateStatus


def pm_gate_report() -> tuple[GateOutcome, ...]:
    """Return representative passed PM risk-gate outcomes."""
    return (
        GateOutcome(
            name="sizing",
            value=0.0812,
            threshold=0.10,
            outcome=GateStatus.PASSED,
            detail=(
                "quantity_shares=7; position_value_usd=812.00; "
                "portfolio_value_usd=10000.00"
            ),
        ),
        GateOutcome(
            name="max_sector_pct",
            value=0.0812,
            threshold=0.30,
            outcome=GateStatus.PASSED,
            detail=(
                "sector=Technology; held_sector_value_usd=0.00; "
                "deployed_this_batch_usd=0.00; order_cost_usd=812.00"
            ),
        ),
        GateOutcome(
            name="max_names_per_sector",
            value=2.0,
            threshold=3.0,
            outcome=GateStatus.PASSED,
            detail="sector=Technology; existing_sector_issuers=1",
        ),
    )
