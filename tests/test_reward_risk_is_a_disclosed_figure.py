"""Reward-risk disclosure and its pinned evidence.

Agent: deliberator
Role: prove disclosure-only figures carry no invented gate verdict.
External I/O: reads ADR-0027 and the trading tunables pack.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from tests.deliberation_fact_probes import keys
from tests.veto_context_fixtures import intent, linked_graph, order_set
from tests.veto_context_gate_fixtures import pm_gate_report

from agents.deliberator.context_pm import REWARD_RISK_RULE, order_lines
from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.portfolio_manager.tests.helpers import cash_portfolio, recommendation
from contracts.common import Money
from contracts.portfolio_manager import GateOutcome, GateStatus, OrderIntent
from kernel import InMemoryGraphStore
from orchestration.veto_context import build_veto_context

_ROOT = Path(__file__).resolve().parents[1]
_DISCLOSED = "target_pct=0.0331; stop_pct=0.0800; comparison=DISCLOSURE_ONLY"


def _order(
    detail: str = _DISCLOSED, outcome: GateStatus = GateStatus.PASSED
) -> OrderIntent:
    gate = GateOutcome(
        name="reward_risk",
        value=0.4132,
        threshold=0.0,
        outcome=outcome,
        detail=detail,
    )
    return intent(gates=(*pm_gate_report(), gate))


def test_a_disclosed_ratio_is_not_a_passed_gate() -> None:
    """DLIB-NEV-08: the figure has exactly its value and detail, no verdict."""
    lines = [line for line in order_lines(_order()) if "name=reward_risk" in line]
    assert lines == [
        "PM disclosed figure, not a gate: name=reward_risk "
        f"value_reward_risk_ratio=0.4132 ({_DISCLOSED})"
    ]


def test_the_rule_is_stated_once_after_the_gates() -> None:
    """DLIB-NEV-08: one rule follows every gate in the order block."""
    lines = order_lines(_order())
    assert lines.count(REWARD_RISK_RULE) == 1
    assert lines[-1] == REWARD_RISK_RULE


@pytest.mark.parametrize(
    "comparison", ["INFORMATIVE", "STRUCTURALLY_DETERMINED", "DISCLOSURE_ONLY_DRAFT"]
)
def test_an_enforced_ratio_keeps_its_verdict(comparison: str) -> None:
    """DLIB-NEV-08: similar or enforced comparisons retain their verdict."""
    lines = order_lines(_order(f"target_pct=0.03; comparison={comparison}"))
    line = next(line for line in lines if "name=reward_risk" in line)
    assert line.startswith("PM gate outcome: name=reward_risk ")
    assert "threshold_reward_risk_ratio=0 -> PASSED" in line
    assert REWARD_RISK_RULE not in lines


@pytest.mark.parametrize(
    ("outcome", "rendered"),
    [(GateStatus.FAILED, "FAILED"), (GateStatus.NOT_EVALUATED, "NOT-EVALUATED")],
)
def test_a_gate_that_did_not_pass_is_never_recast(
    outcome: GateStatus, rendered: str
) -> None:
    """DLIB-NEV-08: failed and unevaluated outcomes stay visible."""
    lines = order_lines(_order(outcome=outcome))
    line = next(line for line in lines if "name=reward_risk" in line)
    assert f"-> {rendered}" in line
    assert REWARD_RISK_RULE not in lines


def test_the_whole_packet_states_the_rule_before_the_pm_run() -> None:
    """DLIB-NEV-08: the assembled packet preserves the disclosure placement."""
    graph = InMemoryGraphStore()
    pm = linked_graph(graph, full=True)
    item = _order()
    lines = build_veto_context(graph, pm, order_set(item), item).splitlines()
    ratio = next(line for line in lines if "name=reward_risk" in line)
    assert "-> PASSED" not in ratio
    assert lines.count(REWARD_RISK_RULE) == 1
    assert lines[lines.index(REWARD_RISK_RULE) + 1].startswith("PM run:")


def test_the_rule_states_what_the_code_does() -> None:
    """DLIB-NEV-09: the default and deployed pack leave the ratio unenforced."""
    floor = PortfolioManagerSettings().min_reward_risk_ratio
    assert floor == 0.0
    pack = json.loads(
        (_ROOT / "orchestration/packs/trading_tunables.json").read_text(
            encoding="utf-8"
        )
    )
    assert not [key for key in keys(pack) if "REWARD_RISK" in key.upper()]
    buy = recommendation().model_copy(
        update={"suggested_stop_pct": 0.08, "suggested_target_pct": 0.02}
    )
    approved, rejected = evaluate_recommendations(
        (buy,),
        {"AAPL": Money(amount=Decimal("50"))},
        cash_portfolio("100000"),
        max_position_pct=Decimal("0.01"),
        max_positions=10,
        cash_buffer_pct=Decimal("0"),
        min_order_quantity=1,
        default_stop_pct=0.08,
        default_target_pct=0.02,
        min_reward_risk_ratio=floor,
    )
    assert rejected == ()
    assert len(approved) == 1
    gate = next(g for g in approved[0].gate_report if g.name == "reward_risk")
    assert "comparison=DISCLOSURE_ONLY" in gate.detail.split("; ")


def test_the_rules_evidence_is_adr_0027s() -> None:
    """DLIB-NEV-09: the rule's measured numbers are exactly ADR-0027's."""
    adr = (
        _ROOT
        / "docs/decisions"
        / "0027-reward-risk-compares-measured-upside-against-measured-downside.md"
    ).read_text(encoding="utf-8")
    for evidence in (
        "47,485 decisions",
        "**+0.03 %**",
        "[95 % CI \u22120.17 %, +0.23 %]",
    ):
        assert evidence in adr
    for evidence in ("47,485 decisions", "+0.03 %", "-0.17 %", "+0.23 %", "0.80"):
        assert evidence in REWARD_RISK_RULE
