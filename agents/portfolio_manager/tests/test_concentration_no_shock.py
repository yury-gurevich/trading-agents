"""No-shock proof for the deployed-book concentration migration.

Agent: portfolio_manager
Role: prove the S210 denominator swap preserves the recorded pass verdicts.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from agents.portfolio_manager.domain.correlation import CorrelationBook
from agents.portfolio_manager.domain.sector_gate_outcomes import (
    sector_exposure_outcome,
)
from agents.portfolio_manager.tests.s184_helpers import buy
from contracts.portfolio_manager import GateStatus

_EQUITY = Decimal("102208.78")
_DEPLOYED = Decimal("21711.95")
_MAX_POSITION_PCT = Decimal("0.01")
_MAX_NAMES_PER_SECTOR = 3


@pytest.mark.parametrize(
    ("sector", "ratio"),
    [
        ("Banking", Decimal("0.1803")),
        ("Media", Decimal("0.1289")),
        ("Food Products", Decimal("0.0922")),
    ],
)
def test_recorded_sector_verdicts_stay_passed_after_denominator_swap(
    sector: str, ratio: Decimal
) -> None:
    """PM-NEV-06 / PM-NEV-09: S210 sector replay stays under the same cap."""
    outcome = sector_exposure_outcome(
        sector=sector,
        held_value=ratio * _DEPLOYED,
        batch_value=Decimal("0"),
        cost=Decimal("0"),
        equity_value=_EQUITY,
        deployed_value=_DEPLOYED,
        max_sector_pct=Decimal("0.30"),
        max_position_pct=_MAX_POSITION_PCT,
        max_names_per_sector=_MAX_NAMES_PER_SECTOR,
    )

    assert outcome.value == pytest.approx(float(ratio), abs=0.0001)
    assert outcome.outcome == GateStatus.PASSED


@pytest.mark.parametrize(
    ("ticker", "ratio"),
    [("WFC", Decimal("0.0455")), ("MDLZ", Decimal("0.0458"))],
)
def test_recorded_cluster_verdicts_stay_passed_after_denominator_swap(
    ticker: str, ratio: Decimal
) -> None:
    """PM-NEV-08 / PM-NEV-09: S210 cluster replay stays under the same cap."""
    book = CorrelationBook((), {}, 120, 0.70, 0.25, 60)

    outcome = book.outcomes(
        buy(ticker),
        ratio * _DEPLOYED,
        _EQUITY,
        deployed_value=_DEPLOYED,
        max_position_pct=_MAX_POSITION_PCT,
        max_names_per_sector=_MAX_NAMES_PER_SECTOR,
        issuer_values={},
        issuer_tickers={},
    )[0]

    assert outcome.value == pytest.approx(float(ratio), abs=0.0001)
    assert outcome.outcome == GateStatus.PASSED
