"""AnalystAgent bus, scoring, and degraded-path tests.

Agent: analyst
Role: verify analyst recommendations, rejections, and explainable silence.
External I/O: none.
"""

from __future__ import annotations

from typing import Any

from agents.analyst.tests.helpers import (
    analyze_message,
    bars,
    candidate,
    candidate_set,
    explain_message,
    overbought_bars,
    wire_analyst,
)


def test_analyze_returns_recommendation_with_rationale_and_provenance() -> None:
    scan = candidate_set(candidate())
    bus, graph, sink = wire_analyst(source_bars=bars())
    graph.merge_node("Candidate", "scan-fixture:AAPL", {"ticker": "AAPL"})

    response = bus.request(analyze_message(scan))

    payload = response.payload
    assert response.message_type == "response"
    assert [item["ticker"] for item in payload["recommendations"]] == ["AAPL"]
    assert payload["recommendations"][0]["action"] == "buy"
    assert payload["recommendations"][0]["confidence"] >= 0.6
    assert payload["recommendations"][0]["rationale"]["summary"]
    assert payload["recommendations"][0]["suggested_stop_pct"] == 0.05
    assert payload["rejections"] == []
    assert payload["explanation"]["summary"]
    assert payload["provenance"]["graph_node_id"].startswith("AnalystRun:")
    run_id = payload["run_id"]
    rec = graph.get_node("Recommendation", f"{run_id}:AAPL")
    assert rec is not None
    assert [node.label for node in graph.descendants(rec, max_depth=1)] == ["Candidate"]
    assert sink.faults == []


def test_recommendation_carries_fundamental_score_when_present() -> None:
    scan = candidate_set(candidate())
    bus, _graph, sink = wire_analyst(
        source_bars=bars(),
        fundamentals={"AAPL": {"peTTM": 8.0, "roeTTM": 20.0}},
    )

    response = bus.request(analyze_message(scan))

    rec = response.payload["recommendations"][0]
    assert rec["ticker"] == "AAPL"
    # peTTM 8 -> 80, roeTTM 20 -> 80; mean 80 -> fundamental 0.80.
    assert rec["fundamental_score"] == 0.80
    assert "fundamental score of" in rec["rationale"]["summary"]
    assert sink.faults == []


def test_low_confidence_candidate_becomes_rejection() -> None:
    # A sustained, wide-ranging climb reads as overbought and choppy: the technical
    # composite (0.379 over 12 indicators -- the 60-bar series clears OBV, RSI-2, NW
    # (+3.97% -> 30) and turnaround (monotone climb -> 50) but not the 200-bar golden
    # cross or any geometric pattern) maps to confidence 0.527 (.3f), below the 0.60
    # regime floor -> a deterministic rejection driven by the indicators.
    scan = candidate_set(candidate("LOW", score=0.01))
    bus, _graph, sink = wire_analyst(source_bars=overbought_bars("LOW"))

    response = bus.request(analyze_message(scan))

    assert response.message_type == "response"
    assert response.payload["recommendations"] == []
    assert response.payload["rejections"][0]["ticker"] == "LOW"
    assert "below regime floor" in response.payload["rejections"][0]["reason"]
    assert "0.527" in response.payload["rejections"][0]["reason"]
    assert "No candidates cleared" in response.payload["explanation"]["summary"]
    assert sink.faults == []


def test_degraded_market_data_returns_explained_rejection() -> None:
    scan = candidate_set(candidate())
    bus, _graph, sink = wire_analyst(source_bars=(), fail_ohlcv=True)

    response = bus.request(analyze_message(scan))

    assert response.message_type == "response"
    assert response.payload["recommendations"] == []
    assert (
        response.payload["rejections"][0]["reason"] == "provider market data degraded"
    )
    assert response.payload["provenance"]["incident_refs"] == ["market_data_degraded"]
    assert len(sink.faults) == 1
    assert sink.faults[0].source_module == "agents.analyst.agent"


def test_degraded_regime_returns_explained_rejection() -> None:
    scan = candidate_set(candidate())
    bus, _graph, sink = wire_analyst(source_bars=bars(), fail_regime=True)

    response = bus.request(analyze_message(scan))

    assert response.message_type == "response"
    assert response.payload["recommendations"] == []
    assert (
        response.payload["rejections"][0]["reason"] == "provider regime data degraded"
    )
    assert response.payload["provenance"]["incident_refs"] == ["regime_source_degraded"]
    assert len(sink.faults) == 1


def test_provider_bus_error_returns_explained_rejection() -> None:
    scan = candidate_set(candidate())
    bus, _graph, sink = wire_analyst(register_provider=False)

    response = bus.request(analyze_message(scan))

    assert response.message_type == "response"
    assert response.payload["recommendations"] == []
    assert response.payload["rejections"][0]["reason"] == "provider data unavailable"
    assert len(sink.faults) == 2


def test_empty_candidate_set_returns_explainable_silence() -> None:
    scan = candidate_set()
    bus, _graph, sink = wire_analyst(register_provider=False)

    response = bus.request(analyze_message(scan))

    assert response.message_type == "response"
    assert response.payload["recommendations"] == []
    assert response.payload["rejections"] == []
    assert (
        "scanner produced no candidates" in response.payload["explanation"]["summary"]
    )
    assert sink.faults == []


def test_scoring_failure_returns_explained_rejection(
    monkeypatch: Any,
) -> None:
    def fail_score(*args: object) -> object:
        raise RuntimeError("score failed")

    monkeypatch.setattr("agents.analyst.agent.score_candidate", fail_score)
    scan = candidate_set(candidate())
    bus, _graph, sink = wire_analyst(source_bars=bars())

    response = bus.request(analyze_message(scan))

    assert response.message_type == "response"
    assert response.payload["recommendations"] == []
    assert response.payload["rejections"][0]["reason"] == "analyst scoring failed"
    assert len(sink.faults) == 1


def test_explain_recommendation_returns_grounded_explanation() -> None:
    scan = candidate_set(candidate())
    bus, _graph, _sink = wire_analyst(register_provider=False)

    response = bus.request(explain_message(scan))

    assert response.message_type == "response"
    assert "Analyst confidence blends" in response.payload["summary"]
    assert response.payload["evidence_refs"] == [
        "analyst.technical_score",
        "provider.regime",
    ]
