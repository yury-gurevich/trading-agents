"""Stop-target proposal evidence persistence tests.

Agent: analyst
Role: prove applied and counterfactual stop/target evidence is durable.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from agents.analyst.domain.recommend import decide
from agents.analyst.domain.scoring import ScoreBreakdown
from agents.analyst.settings import AnalystSettings
from agents.analyst.store import write_analysis
from agents.analyst.tests.helpers import candidate, candidate_set, recommendation
from contracts.analyst import Recommendation
from contracts.common import Provenance
from contracts.provider import RegimeContext
from kernel import InMemoryGraphStore


def test_flat_mode_records_applied_and_counterfactual_stop_target_pairs() -> None:
    """ANLZ-STA-02 / ANLZ-OBS-01 / ADR-0013: flat records both pairs."""
    graph = InMemoryGraphStore()
    rec = _recommendation("flat")

    write_analysis(
        graph,
        candidate_set=candidate_set(candidate("AAPL")),
        recommendations=(rec,),
        rejections=(),
    )

    props = graph.list_nodes("Recommendation")[0].props
    assert props["stop_target_mode"] == "flat"
    assert props["stop_target_counterfactual_mode"] == "scaled"
    assert props["stop_target_applied_stop_pct"] == 0.05
    assert props["stop_target_applied_target_pct"] == 0.10
    assert props["stop_target_counterfactual_stop_pct"] == 0.064
    assert props["stop_target_counterfactual_target_pct"] == 0.128
    assert props["stop_target_atr_pct"] == 3.2


def test_scaled_mode_records_flat_counterfactual_symmetrically() -> None:
    """ANLZ-STA-02 / ANLZ-OBS-01 / ADR-0013: scaled records flat pair."""
    graph = InMemoryGraphStore()
    rec = _recommendation("scaled")

    write_analysis(
        graph,
        candidate_set=candidate_set(candidate("AAPL")),
        recommendations=(rec,),
        rejections=(),
    )

    props = graph.list_nodes("Recommendation")[0].props
    assert props["stop_target_mode"] == "scaled"
    assert props["stop_target_counterfactual_mode"] == "flat"
    assert props["stop_target_applied_stop_pct"] == 0.064
    assert props["stop_target_counterfactual_stop_pct"] == 0.05
    assert props["stop_target_flat_target_pct"] == 0.10
    assert props["stop_target_scaled_target_pct"] == 0.128


def test_stop_target_record_is_append_only_for_repeated_recommendations() -> None:
    """ANLZ-STA-02 / ANLZ-IDM-02: repeated writes append, never rewrite."""
    graph = InMemoryGraphStore()
    rec = _recommendation("scaled")
    payload = candidate_set(candidate("AAPL"))

    write_analysis(graph, candidate_set=payload, recommendations=(rec,), rejections=())
    first_key = graph.list_nodes("Recommendation")[0].key
    write_analysis(graph, candidate_set=payload, recommendations=(rec,), rejections=())

    keys = [node.key for node in graph.list_nodes("Recommendation")]
    assert len(keys) == 2
    assert first_key in keys


def test_stop_target_evidence_is_optional_and_round_trips() -> None:
    """ANLZ-TYP-02: legacy recommendations parse without evidence."""
    legacy = recommendation("AAPL")
    current = _recommendation("scaled")
    graph = InMemoryGraphStore()

    write_analysis(
        graph,
        candidate_set=candidate_set(candidate("AAPL")),
        recommendations=(legacy,),
        rejections=(),
    )

    parsed = Recommendation.model_validate(current.model_dump(mode="json"))

    assert legacy.stop_target_evidence is None
    assert "stop_target_mode" not in graph.list_nodes("Recommendation")[0].props
    assert parsed.stop_target_evidence == current.stop_target_evidence


def _recommendation(mode: Literal["flat", "scaled"]) -> Recommendation:
    decision = decide(
        candidate("AAPL"),
        ScoreBreakdown(
            technical_score=0.72,
            confidence=0.81,
            metrics={"atr_pct": 3.2},
        ),
        _regime(),
        settings=AnalystSettings(stop_target_mode=mode),
    )
    assert decision.recommendation is not None
    return decision.recommendation


def _regime() -> RegimeContext:
    return RegimeContext(
        label="risk_on",
        vix=12.0,
        as_of=datetime.now(tz=UTC),
        base_min_confidence=0.30,
        base_stop_loss_pct=0.05,
        base_take_profit_pct=0.10,
        base_max_holding_days=10,
        provenance=Provenance(run_id="regime-fixture", source_agent="provider"),
    )
