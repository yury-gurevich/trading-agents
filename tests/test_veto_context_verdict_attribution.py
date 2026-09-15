"""Deliberation veto verdict-attribution tests.

Agent: orchestration
Role: verify rendered debate verdicts name their enforcing checks.
External I/O: none.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from tests.veto_context_fixtures import intent, linked_graph, order_set, recs
from tests.veto_context_provider_fixtures import regime

from contracts.analyst import Recommendation, RecommendationSet, StopTargetEvidence
from contracts.provider import RegimeContext
from kernel import InMemoryGraphStore
from orchestration.veto_context import build_veto_context
from orchestration.veto_context_pm import regime_gate_lines

if TYPE_CHECKING:
    from contracts.portfolio_manager import OrderIntent

_DECLARED_CONTEXT_CHECKS = {"confidence_floor": "analyst"}


def test_no_rendered_verdict_lacks_an_enforcing_check() -> None:
    """DLIB-NEV-08: every rendered verdict names a real enforcing check."""
    graph = InMemoryGraphStore()
    item = intent(stop=0.03, target=0.08)
    orders = order_set(item)
    pm = linked_graph(graph, full=True)

    context = build_veto_context(graph, pm, orders, item)

    assert _unattributed_verdicts(context, item) == []


def test_scaled_mode_renders_no_failed_for_a_preserved_ratio() -> None:
    """DLIB-NEV-08: scaled stop-target basis is descriptive, not a verdict."""
    item = intent()
    rec = _rec_with_stop_evidence(_scaled_stop_target_evidence())
    regime_context = RegimeContext.model_validate(regime()).model_copy(
        update={"base_stop_loss_pct": 0.05, "base_take_profit_pct": 0.10}
    )

    stop_line = regime_gate_lines(regime_context, rec, item)[2]

    assert "stop_target_regime basis:" in stop_line
    assert "mode=scaled" in stop_line
    assert "applied_stop_pct=4.00%; applied_target_pct=8.00%" in stop_line
    assert "flat_stop_pct=5.00%; flat_target_pct=10.00%" in stop_line
    assert "scaled_stop_pct=4.00%; scaled_target_pct=8.00%" in stop_line
    assert "applied_reward_risk_ratio=2.00" in stop_line
    assert "flat_reward_risk_ratio=2.00" in stop_line
    assert "scaled_reward_risk_ratio=2.00" in stop_line
    assert "FAILED" not in stop_line
    assert "PASSED" not in stop_line


def test_stop_basis_renders_zero_stop_ratio_as_unavailable() -> None:
    """DLIB-NEV-08: impossible reward-risk ratios stay descriptive."""
    item = intent()
    evidence = _scaled_stop_target_evidence().model_copy(update={"flat_stop_pct": 0.0})
    rec = _rec_with_stop_evidence(evidence)
    regime_context = RegimeContext.model_validate(regime())

    stop_line = regime_gate_lines(regime_context, rec, item)[2]

    assert "flat_reward_risk_ratio=n/a" in stop_line
    assert "FAILED" not in stop_line
    assert "PASSED" not in stop_line


def test_stop_basis_degrades_without_evidence() -> None:
    """DLIB-NEV-08: missing stop evidence renders unavailable, not a verdict."""
    item = intent(stop=None, target=None)
    regime_context = RegimeContext.model_validate(regime())

    stop_line = regime_gate_lines(regime_context, None, item)[2]

    assert stop_line == (
        "stop_target_regime basis: unavailable: "
        "no analyst stop-target evidence; stop_pct=n/a; target_pct=n/a; "
        "base_stop_loss_pct=3.00%; base_take_profit_pct=8.00%."
    )
    assert "FAILED" not in stop_line
    assert "PASSED" not in stop_line


def test_confidence_floor_names_its_enforcer() -> None:
    """DLIB-NEV-08: a rendered confidence verdict names its enforcing agent."""
    item = intent()
    rec = RecommendationSet.model_validate(recs()).recommendations[0]
    regime_context = RegimeContext.model_validate(regime())

    confidence_line = regime_gate_lines(regime_context, rec, item)[1]

    assert confidence_line == (
        "confidence_floor gate: enforced_by=analyst; "
        "confidence_score=0.620 vs base_min_confidence_score=0.570 -> PASSED"
    )


def _unattributed_verdicts(context: str, item: OrderIntent) -> list[str]:
    pm_gate_names = {gate.name for gate in item.gate_report}
    violations: list[str] = []
    for line in context.splitlines():
        if "-> PASSED" not in line and "-> FAILED" not in line:
            continue
        check_name = _rendered_check_name(line)
        if check_name is None:
            violations.append(f"missing check name: {line}")
            continue
        if check_name in pm_gate_names:
            continue
        expected_enforcer = _DECLARED_CONTEXT_CHECKS.get(check_name)
        if expected_enforcer is None:
            violations.append(f"no enforcing check declared: {check_name}: {line}")
            continue
        if f"enforced_by={expected_enforcer}" not in line:
            violations.append(
                f"missing enforcing agent {expected_enforcer}: {check_name}: {line}"
            )
    return violations


def _rendered_check_name(line: str) -> str | None:
    named = re.search(r"\bname=([a-z_]+)\b", line)
    if named is not None:
        return named.group(1)
    gate_prefix = re.match(r"([a-z_]+) gate\b", line)
    if gate_prefix is not None:
        return gate_prefix.group(1)
    return None


def _rec_with_stop_evidence(evidence: StopTargetEvidence) -> Recommendation:
    rec = RecommendationSet.model_validate(recs()).recommendations[0]
    return rec.model_copy(
        update={
            "suggested_stop_pct": evidence.applied_stop_pct,
            "suggested_target_pct": evidence.applied_target_pct,
            "stop_target_evidence": evidence,
        }
    )


def _scaled_stop_target_evidence() -> StopTargetEvidence:
    return StopTargetEvidence(
        mode="scaled",
        counterfactual_mode="flat",
        atr_pct=2.0,
        volatility_present=True,
        volatility_fallback=False,
        applied_stop_pct=0.04,
        applied_target_pct=0.08,
        counterfactual_stop_pct=0.05,
        counterfactual_target_pct=0.10,
        flat_stop_pct=0.05,
        flat_target_pct=0.10,
        scaled_stop_pct=0.04,
        scaled_target_pct=0.08,
    )
