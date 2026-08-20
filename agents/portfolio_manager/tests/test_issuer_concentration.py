"""Issuer and sector concentration tests.

Agent: portfolio_manager
Role: prove one issuer is one exposure and held sector dollars count.
External I/O: none.
"""

from __future__ import annotations

import base64
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.issuer_map import (
    ISSUER_MAP_B64_ENV,
    ISSUER_MAP_PATH_ENV,
    load_issuer_map_from_env,
    parse_issuer_map,
)
from agents.portfolio_manager.tests.helpers import cash_portfolio
from agents.portfolio_manager.tests.s184_helpers import ISSUERS, SECTORS, buy, gate
from contracts.common import Money

if TYPE_CHECKING:
    from pathlib import Path


def test_dual_class_order_counts_existing_issuer_exposure() -> None:
    """PM-NEV-06 / PM-NEV-07: GOOGL makes GOOG the same issuer exposure."""
    portfolio = cash_portfolio(
        "10000.00",
        {"GOOGL": 10},
        position_values={"GOOGL": Money(amount=Decimal("1000.00"))},
    )

    approved, rejected = evaluate_recommendations(
        (buy("GOOG"),),
        {"GOOG": Money(amount=Decimal("100.00"))},
        portfolio,
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
        sectors=SECTORS,
        max_sector_pct=Decimal("1.00"),
        max_names_per_sector=1,
        issuer_map=ISSUERS,
    )

    sizing = gate(rejected[0], "sizing")
    assert approved == ()
    assert rejected[0].reason == "sizing"
    assert sizing.value == 0.20
    assert sizing.outcome == "failed"
    assert "issuer=alphabet" in sizing.detail
    assert "existing_issuer_value_usd=1000.00" in sizing.detail


def test_absent_issuer_map_entry_is_own_issuer_pass() -> None:
    """PM-NEV-07: an unmapped ticker is evaluated as its own issuer, not skipped."""
    portfolio = cash_portfolio(
        "10000.00",
        {"AAPL": 10},
        position_values={"AAPL": Money(amount=Decimal("1000.00"))},
    )

    approved, rejected = evaluate_recommendations(
        (buy("MSFT"),),
        {"MSFT": Money(amount=Decimal("100.00"))},
        portfolio,
        max_position_pct=Decimal("0.10"),
        max_positions=2,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
        sectors=SECTORS,
        max_sector_pct=Decimal("1.00"),
        max_names_per_sector=3,
        issuer_map={"GOOG": "alphabet"},
    )

    sizing = next(item for item in approved[0].gate_report if item.name == "sizing")
    assert rejected == ()
    assert approved[0].ticker == "MSFT"
    assert sizing.outcome == "passed"
    assert "issuer=MSFT" in sizing.detail


def test_missing_sector_label_is_not_evaluated() -> None:
    """PM-NEV-09: missing sector label emits NOT-EVALUATED, never a silent pass."""
    approved, rejected = evaluate_recommendations(
        (buy("AAPL"),),
        {"AAPL": Money(amount=Decimal("100.00"))},
        cash_portfolio("10000.00"),
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
        sectors={},
        max_sector_pct=Decimal("0.30"),
        max_names_per_sector=3,
    )

    sector = gate(rejected[0], "max_sector_pct")
    names = gate(rejected[0], "max_names_per_sector")
    assert approved == ()
    assert rejected[0].reason == "sector_not_evaluated"
    assert sector.outcome == "not_evaluated"
    assert names.outcome == "not_evaluated"
    assert "missing_input=sector_label" in sector.detail


def test_held_sector_dollars_count_toward_sector_cap() -> None:
    """DRIFT-045: held position dollars count toward max_sector_pct."""
    portfolio = cash_portfolio(
        "10000.00",
        {"AAPL": 25},
        position_values={"AAPL": Money(amount=Decimal("2500.00"))},
    )

    approved, rejected = evaluate_recommendations(
        (buy("MSFT"),),
        {"MSFT": Money(amount=Decimal("100.00"))},
        portfolio,
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
        sectors={"AAPL": "Technology", "MSFT": "Technology"},
        max_sector_pct=Decimal("0.30"),
        max_names_per_sector=0,
    )

    sector = gate(rejected[0], "max_sector_pct")
    assert approved == ()
    assert rejected[0].reason == "sector_concentration"
    assert sector.outcome == "failed"
    assert sector.value == 0.35
    assert "held_sector_value_usd=2500.00" in sector.detail


def test_issuer_map_parser_normalizes_ticker_keys() -> None:
    """PM-NEV-07: pack data can identify share classes regardless of key case."""
    parsed = parse_issuer_map('{"goog": "alphabet", "GOOGL": "alphabet"}')

    assert parsed == {"GOOG": "alphabet", "GOOGL": "alphabet"}


def test_issuer_map_parser_rejects_invalid_pack_shape() -> None:
    """PM-NEV-07: malformed issuer pack data fails closed before evaluation."""
    with pytest.raises(ValueError, match="JSON object"):
        parse_issuer_map('["GOOG"]')
    with pytest.raises(ValueError, match="string -> string"):
        parse_issuer_map('{"GOOG": 1}')


def test_issuer_map_loader_prefers_b64_then_path_then_empty(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """PM-NEV-07: deployed pack data can arrive by env payload or local path."""
    encoded = base64.b64encode(b'{"goog": "alphabet"}').decode("ascii")
    path = tmp_path / "issuer-map.json"
    path.write_text('{"brk.b": "berkshire-hathaway"}', encoding="utf-8")

    monkeypatch.setenv(ISSUER_MAP_B64_ENV, encoded)
    monkeypatch.setenv(ISSUER_MAP_PATH_ENV, str(path))
    assert load_issuer_map_from_env() == {"GOOG": "alphabet"}

    monkeypatch.delenv(ISSUER_MAP_B64_ENV)
    assert load_issuer_map_from_env() == {"BRK.B": "berkshire-hathaway"}

    monkeypatch.setenv(ISSUER_MAP_PATH_ENV, str(tmp_path / "missing.json"))
    assert load_issuer_map_from_env() == {}
