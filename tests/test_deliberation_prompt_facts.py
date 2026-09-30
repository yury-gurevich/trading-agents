"""Every fact the referee is told about our code is pinned to the code (S245).

Agent: tooling
Role: pin each distinction and each Class-1 worked example in the champion
      challenger and judge prompts to the code it describes (DLIB-NEV-09), and
      prove the registry of pins is complete (DL-251 D2).
External I/O: reads agent sources and the trading tunables pack.
"""

from __future__ import annotations

import inspect
import json
import re
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from scripts.deliberation_eval import _CLASS1, _CLASS2
from tests.deliberation_fact_probes import (
    anomalous,
    buy,
    distinctions,
    keys,
    reads_forecaster,
)

from agents.analyst.settings import AnalystSettings
from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.domain.sizing import size_quantity
from agents.portfolio_manager.tests.helpers import cash_portfolio
from contracts.common import Money
from kernel.deliberation_prompts import CHALLENGER_SYSTEM, JUDGE_SYSTEM

if TYPE_CHECKING:
    from collections.abc import Callable

_ROOT = Path(__file__).resolve().parents[1]
_LIVE_DECISION = ("scanner", "analyst", "portfolio_manager", "deliberator", "execution")
_CASE = re.compile(r'"case": "([^"]+)"')


def test_pooled_sigma_is_one_sessions_cross_section() -> None:
    """DLIB-NEV-09 / PROV-OUT-09 (A3, read-only): the guard pools one session's
    open-to-close moves across every name, so a lone +9 % among 98 names at
    +/-1.5 % (5.1 sigma) passes and a -30 % (8.9 sigma) is excluded by name, at
    the default ProviderSettings(). Judged per name, neither would be flagged."""
    assert anomalous(109.0) == ()
    assert anomalous(70.0) == ("X",)


def test_sizing_is_a_fixed_fraction_not_volatility_adjusted() -> None:
    """DLIB-NEV-09 / PM-IDN-01 / PM-NEV-05 (A4, read-only): a buy's quantity is
    portfolio value x max_position_pct / price, floored to whole shares, and no
    volatility, beta or stop input exists to adjust it."""
    budget = {"portfolio_value": Decimal(100000), "max_position_pct": Decimal("0.01")}
    parameters = set(inspect.signature(size_quantity).parameters)

    assert size_quantity(**budget, est_price=Decimal(50)) == 20
    assert size_quantity(**budget, est_price=Decimal(333)) == 3
    assert parameters == {"portfolio_value", "max_position_pct", "est_price"}


def test_a_high_beta_buy_gets_the_same_size_as_a_low_beta_one() -> None:
    """DLIB-NEV-09 / PM-IDN-01 (A4, PM level): two buys at one price, beta 0.5
    and atr_pct 1.0 against beta 2.5 and atr_pct 6.0, get the same quantity."""
    approved, rejected = evaluate_recommendations(
        (buy("CALM", beta=0.5, atr_pct=1.0), buy("WILD", beta=2.5, atr_pct=6.0)),
        {"CALM": Money(amount=Decimal(50)), "WILD": Money(amount=Decimal(50))},
        cash_portfolio("100000"),
        max_position_pct=Decimal("0.01"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.00"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=0.0,
    )

    quantities = {order.ticker: order.quantity for order in approved}

    assert rejected == ()
    assert quantities == {"CALM": 20, "WILD": 20}


def test_alpha158_contributes_nothing() -> None:
    """DLIB-NEV-09 / ANLZ-IDN-01 (A5, read-only): the Alpha158 pillar's weight is
    0.0 by default and the tunables pack sets no ALPHA158 key for any app."""
    pack_path = _ROOT / "orchestration" / "packs" / "trading_tunables.json"
    pack = json.loads(pack_path.read_text(encoding="utf-8"))

    assert AnalystSettings().alpha158_pillar_weight == 0.0
    assert [key for key in keys(pack) if "ALPHA158" in key.upper()] == []


def test_lightgbm_does_not_feed_the_live_decision() -> None:
    """DLIB-NEV-09 / FORE-NEV-02 (A6, read-only): no non-test module of the five
    agents on the order path imports the forecaster contract or names its
    ShadowPrediction, so no LightGBM output can reach a live decision."""
    readers = sorted(
        str(path.relative_to(_ROOT))
        for agent in _LIVE_DECISION
        for path in (_ROOT / "agents" / agent).rglob("*.py")
        if "tests" not in path.relative_to(_ROOT).parts
        and reads_forecaster(path.read_text(encoding="utf-8"))
    )

    assert readers == []


# The registry (DL-251 D2): each stated fact maps to the test that pins it.
DISTINCTION_PINS: dict[str, Callable[[], None]] = {
    "pooled cross-sectional sigma is not per-name volatility": (
        test_pooled_sigma_is_one_sessions_cross_section
    ),
    "fixed-fraction sizing is not volatility-adjusted": (
        test_sizing_is_a_fixed_fraction_not_volatility_adjusted
    ),
    "Alpha158 weight 0.00 contributes nothing": test_alpha158_contributes_nothing,
    "LightGBM shadow output does not feed the live decision": (
        test_lightgbm_does_not_feed_the_live_decision
    ),
}
CASE_PINS: dict[str, Callable[[], None]] = {
    "pooled-sigma": test_pooled_sigma_is_one_sessions_cross_section,
    "fixed-fraction-size": test_a_high_beta_buy_gets_the_same_size_as_a_low_beta_one,
    "alpha158-weight-zero": test_alpha158_contributes_nothing,
    "lightgbm-shadow": test_lightgbm_does_not_feed_the_live_decision,
}


@pytest.mark.parametrize(
    "prompt", [CHALLENGER_SYSTEM, JUDGE_SYSTEM], ids=["challenger", "judge"]
)
def test_every_stated_fact_has_a_pin(prompt: str) -> None:
    """DLIB-NEV-09 (A7): the distinctions the prompt states are exactly the pinned
    ones, every worked example is a Class-2 hypothetical or a pinned Class-1 case,
    every Class-1 case is pinned, and every pin is a test in this module."""
    class1 = {str(case[0]) for case in _CLASS1}
    class2 = {str(case[0]) for case in _CLASS2}

    assert distinctions(prompt) == set(DISTINCTION_PINS)
    assert set(CASE_PINS) == class1
    assert set(_CASE.findall(prompt)) <= class2 | set(CASE_PINS)
    pins = [*DISTINCTION_PINS.values(), *CASE_PINS.values()]
    assert all(globals().get(pin.__name__) is pin for pin in pins)
    assert all(pin.__name__.startswith("test_") for pin in pins)
