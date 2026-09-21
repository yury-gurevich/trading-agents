"""Correlation-ramp tests for Portfolio Manager concentration checks.

Agent: portfolio_manager
Role: prove graded correlated-issuer contributions are reproducible and bounded.
External I/O: reads the deployed tunables pack in one static-pack test.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from agents.portfolio_manager.domain.correlation import CorrelationBook
from agents.portfolio_manager.tests.s184_helpers import buy

if TYPE_CHECKING:
    from contracts.portfolio_manager import GateOutcome

_DEPLOYED = Decimal("10000.00")
_PACK = Path(__file__).parents[3] / "orchestration" / "packs" / "trading_tunables.json"


def test_ceiling_correlation_counts_a_held_issuer_in_full() -> None:
    """PM-NEV-08 / PM-OBS-03: correlation above the ceiling applies weight one."""
    outcome = _outcome({"MSFT": 0.95}, {"MSFT": Decimal("1000.00")})

    assert outcome.value == 0.11
    assert "correlated_issuers=MSFT:0.9500:w1.0000" in outcome.detail
    assert "cluster_weight_total=1.0000" in outcome.detail


@pytest.mark.parametrize(
    ("correlation", "rendered"),
    [(None, "MSFT:unmeasured"), (0.45, "MSFT:0.4500")],
)
def test_unmeasured_or_below_floor_issuer_counts_nothing_but_is_disclosed(
    correlation: float | None, rendered: str
) -> None:
    """PM-NEV-08 / PM-OBS-03: a zero-weight issuer stays visible outside the cluster."""
    outcome = _outcome({"MSFT": correlation}, {"MSFT": Decimal("1000.00")})

    assert outcome.value == 0.01
    assert "correlated_issuers=none" in outcome.detail
    assert f"below_threshold_top={rendered}" in outcome.detail
    assert "cluster_weight_total=0.0000" in outcome.detail


def test_cluster_ratio_is_recomputable_from_rendered_weights() -> None:
    """PM-NEV-08 / PM-OBS-03: rendered weights exactly reproduce cluster arithmetic."""
    issuer_values = {"AAA": Decimal("1000.00"), "BBB": Decimal("2000.00")}
    outcome = _outcome({"AAA": 0.70, "BBB": 0.80}, issuer_values)
    fields = dict(field.split("=", 1) for field in outcome.detail.split("; "))
    weights = {
        entry.split(":")[0]: Decimal(entry.split(":w", 1)[1])
        for entry in fields["correlated_issuers"].split(",")
    }
    rendered_value = Decimal(fields["cluster_value_usd"])

    assert Decimal(fields["cluster_weight_total"]) == sum(weights.values())
    assert rendered_value == Decimal("100.00") + sum(
        issuer_values[issuer] * weight for issuer, weight in weights.items()
    )
    assert outcome.value == float(rendered_value / _DEPLOYED)


def test_staples_near_misses_are_weighted_without_failing_the_cap() -> None:
    """PM-NEV-08 / PM-OBS-03: the EXP-008 staples complex is no longer invisible."""
    outcome = _outcome(
        {"KO": 0.6397, "KHC": 0.6097, "MO": 0.5811},
        {issuer: Decimal("1000.00") for issuer in ("KO", "KHC", "MO")},
    )

    assert outcome.outcome == "passed"
    assert (
        "correlated_issuers=KO:0.6397:w0.3492,KHC:0.6097:w0.2742,MO:0.5811:w0.2028"
        in outcome.detail
    )
    assert "cluster_weight_total=0.8262" in outcome.detail
    assert outcome.value <= outcome.threshold


def test_degenerate_ramp_is_binary_at_the_floor_and_declared() -> None:
    """PM-NEV-08 / PM-OBS-03: a degenerate pack value remains explicit and safe."""
    outcome = _outcome(
        {"ABOVE": 0.70, "BELOW": 0.69},
        {"ABOVE": Decimal("1000.00"), "BELOW": Decimal("1000.00")},
        floor=0.70,
        ceiling=0.70,
    )

    assert "correlation_ramp=0.7000..0.7000:degenerate" in outcome.detail
    assert "correlated_issuers=ABOVE:0.7000:w1.0000" in outcome.detail
    assert "below_threshold_top=BELOW:0.6900" in outcome.detail


@pytest.mark.parametrize("ticker", ["WFC", "MDLZ"])
def test_recorded_cluster_fixture_verdicts_remain_passed_under_ramp(
    ticker: str,
) -> None:
    """PM-NEV-08 / PM-NEV-09: historical pass fixtures stay passed under the ramp."""
    outcome = _outcome(
        {"HELD": 0.70},
        {"HELD": Decimal("1000.00")},
        candidate_ticker=ticker,
        cost=Decimal("986.86"),
    )

    assert outcome.outcome == "passed"
    assert outcome.value <= outcome.threshold


def test_deployed_tunables_pack_declares_the_ramp_endpoints() -> None:
    """PM-NEV-08: the deployed pack carries ordered ramp endpoints."""
    tunables = json.loads(_PACK.read_text(encoding="utf-8"))["apps"]
    portfolio_manager = tunables["portfolio-manager"]
    floor = float(portfolio_manager["PORTFOLIO_MANAGER_CORRELATION_THRESHOLD"])
    ceiling = float(portfolio_manager["PORTFOLIO_MANAGER_CORRELATION_CEILING"])

    assert floor == 0.50
    assert ceiling == 0.90
    assert floor < ceiling


def _outcome(
    correlations: dict[str, float | None],
    issuer_values: dict[str, Decimal],
    *,
    candidate_ticker: str = "AMZN",
    cost: Decimal = Decimal("100.00"),
    floor: float = 0.50,
    ceiling: float = 0.90,
) -> GateOutcome:
    book = CorrelationBook((), {}, 120, floor, 0.25, 60, ceiling)
    for issuer, correlation in correlations.items():
        candidate = candidate_ticker.upper()
        held = issuer.upper()
        key: tuple[str, str] = (
            (candidate, held) if candidate <= held else (held, candidate)
        )
        book._pair_cache[key] = (correlation, 120)
    return book.outcomes(
        buy(candidate_ticker),
        cost,
        _DEPLOYED,
        deployed_value=_DEPLOYED,
        issuer_values=issuer_values,
        issuer_tickers={issuer: (issuer,) for issuer in issuer_values},
    )[0]
