"""Service Bus SAS planner tests.

Agent: tooling
Role: prove the Service Bus SAS matrix is derived from source topology.
External I/O: local source reads only; no live Azure.
"""

from __future__ import annotations

import pytest
from scripts import sb_sas_plan as plan
from scripts.sb_sas_scan import SourceText


def test_repo_plan_derives_expected_topics_without_cap_violations() -> None:
    grants = plan.plan_from_repo()

    assert plan.SasGrant("scanner", "run.trigger", ("Listen",)) in grants
    assert plan.SasGrant("scanner", "scan.candidates.ready", ("Send",)) in grants
    assert plan.SasGrant("dispatcher", "run.trigger", ("Send",)) in grants
    assert plan.SasGrant("supervisor", "supervisor.requests", ("Listen",)) in grants
    assert plan.SasGrant("researcher", "supervisor.requests", ("Send",)) in grants
    assert "master" not in plan.grants_by_target(grants)
    assert plan.cap_violations(grants) == {}


def test_plan_from_sources_collects_pubsub_and_served_rpc_topics() -> None:
    sources = (
        SourceText(
            "agents/scanner/agent.py",
            """
def bind(bus):
    bus.subscribe("input.topic", handle)
    bus.publish("direct.topic", {})
    claim_check_write(bus, graph, topic="ready.topic")
""",
        ),
        SourceText(
            "agents/researcher/agent.py",
            """
def flag(bus):
    bus.request(AgentMessage(
        sender="researcher",
        recipient="supervisor",
        message_type="request",
        capability="flag_for_human",
        payload={},
    ))
""",
        ),
    )

    grants = plan.plan_from_sources(sources)

    assert plan.SasGrant("scanner", "input.topic", ("Listen",)) in grants
    assert plan.SasGrant("scanner", "direct.topic", ("Send",)) in grants
    assert plan.SasGrant("scanner", "ready.topic", ("Send",)) in grants
    assert plan.SasGrant("researcher", "supervisor.requests", ("Send",)) in grants
    assert plan.SasGrant("researcher", "researcher.reply", ("Listen",)) in grants
    assert plan.SasGrant("supervisor", "researcher.reply", ("Send",)) in grants


def test_names_normalize_app_shapes_and_reject_ops() -> None:
    assert plan.authorization_rule_name("portfolio-manager") == "ta-portfolio-manager"
    assert plan.target_secret_name("portfolio_manager") == (
        "servicebus-connection-string-portfolio-manager"
    )
    assert plan.target_bundle_secret_name("portfolio_manager") == (
        "servicebus-connection-strings-portfolio-manager"
    )

    with pytest.raises(ValueError, match="ops is not a Service Bus fleet target"):
        plan.target_secret_name("ops")
