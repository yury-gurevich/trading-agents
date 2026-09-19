"""ProviderAgent regime VIX freshness tests.

Agent: provider
Role: verify regime VIX shortfalls are warnings, not run-halting degradation.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

from agents.provider import ProviderAgent
from agents.provider.sources import FakeDataSource, RegimeInputs
from contracts.provider import RegimeContext
from kernel import AgentMessage, CollectingFaultSink, InMemoryGraphStore, InProcessBus
from kernel.fault_graph import GraphFaultSink


class _RegimeOnlySource(FakeDataSource):
    def __init__(self, inputs: RegimeInputs) -> None:
        super().__init__()
        self._inputs = inputs

    def fetch_regime_inputs(self, as_of: date) -> RegimeInputs:
        assert as_of == self._inputs.as_of
        return self._inputs


def _message(capability: str, payload: dict[str, object]) -> AgentMessage:
    return AgentMessage(
        sender="analyst",
        recipient="provider",
        message_type="request",
        capability=capability,
        payload=payload,
    )


def test_prior_session_vix_warns_without_regime_incident_ref() -> None:
    """PROV-OUT-02 / PROV-OUT-03 / PROV-NEV-01: prior-session ^VIX is explicit
    warning evidence, not run-halting provider degradation."""
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    inner = CollectingFaultSink()
    sink = GraphFaultSink(graph, inner)
    ProviderAgent(
        bus,
        graph=graph,
        source=_RegimeOnlySource(
            RegimeInputs(
                as_of=date(2026, 9, 14),
                vix=21.0,
                vix_status="prior_session",
                vix_as_of=date(2026, 9, 11),
                vix_reason="prior_session",
            )
        ),
        sink=sink,
    ).bind()

    response = bus.request(_message("get_regime", {"as_of": date(2026, 9, 14)}))

    assert response.message_type == "response"
    assert response.payload["label"] == "risk_off"
    assert response.payload["vix_status"] == "prior_session"
    assert response.payload["vix_as_of"] == "2026-09-11"
    assert response.payload["provenance"]["incident_refs"] == []
    assert len(inner.faults) == 1
    fault = inner.faults[0]
    assert fault.severity == "warning"
    assert fault.error_type == "RegimeVixShortfall"
    assert fault.context["vix_status"] == "prior_session"
    assert fault.context["vix_as_of"] == "2026-09-11"
    fault_node = graph.list_nodes("Fault")[0]
    assert fault_node.props["context"]["vix_status"] == "prior_session"


def test_missing_vix_warns_and_keeps_regime_usable() -> None:
    """PROV-OUT-02 / PROV-OUT-03 / PROV-NEV-01: missing ^VIX is flagged while the
    regime still returns neutral defaults and no incident ref."""
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    ProviderAgent(
        bus,
        graph=graph,
        source=_RegimeOnlySource(
            RegimeInputs(
                as_of=date(2026, 9, 14),
                vix=None,
                vix_status="missing",
                vix_as_of=None,
                vix_reason="stale_vix_bar",
            )
        ),
        sink=sink,
    ).bind()

    response = bus.request(_message("get_regime", {"as_of": date(2026, 9, 14)}))

    assert response.message_type == "response"
    assert response.payload["label"] == "neutral"
    assert response.payload["vix"] is None
    assert response.payload["vix_status"] == "missing"
    assert response.payload["vix_as_of"] is None
    assert response.payload["provenance"]["incident_refs"] == []
    assert len(sink.faults) == 1
    assert sink.faults[0].severity == "warning"
    assert sink.faults[0].context["reason"] == "stale_vix_bar"


def test_old_regime_context_snapshot_defaults_vix_freshness_fields() -> None:
    """PROV-OUT-02 / PROV-TYP-01: historical RegimeContext snapshots remain readable
    and default new ^VIX freshness fields to missing."""
    context = RegimeContext.model_validate(
        {
            "label": "neutral",
            "vix": None,
            "as_of": "2026-09-14T00:00:00+00:00",
            "base_min_confidence": 0.6,
            "base_stop_loss_pct": 0.05,
            "base_take_profit_pct": 0.1,
            "base_max_holding_days": 10,
            "provenance": {
                "run_id": "provider-regime-old",
                "source_agent": "provider",
                "graph_node_id": "Regime:provider-regime-old",
                "incident_refs": [],
            },
        }
    )

    assert context.vix_status == "missing"
    assert context.vix_as_of is None
