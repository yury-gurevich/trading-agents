"""Master agent unit tests — handshake and fleet registry.

Agent: master
Role: tests for MasterAgent lifecycle: start, activate, drain.
External I/O: none (InMemoryGraphStore).
"""

from __future__ import annotations

import pytest

from agents.master.agent import MasterAgent
from agents.master.store import write_agent_definition
from agents.master.tests.helpers import trading_policy
from contracts.master import AgentState, EHLOMessage
from kernel import InMemoryGraphStore


@pytest.fixture
def master() -> MasterAgent:
    return MasterAgent(graph=InMemoryGraphStore(), grant_policy=trading_policy())


# ── start ────────────────────────────────────────────────────────────────────


def test_start_writes_session_node(master: MasterAgent) -> None:
    """MST-IDN-01: start() writes a Session node and returns the session_id."""
    session_id = master.start()
    assert session_id.startswith("session:")
    node = master._graph.get_node("Session", session_id)
    assert node is not None
    assert "started_at" in node.props


def test_start_exposes_session_id(master: MasterAgent) -> None:
    """MST-STA-01: session_id is None before start(), non-None after."""
    assert master.session_id is None
    master.start()
    assert master.session_id is not None


# ── activate ─────────────────────────────────────────────────────────────────


def test_activate_returns_activate_message(master: MasterAgent) -> None:
    """MST-OUT-01: EHLO -> ACTIVATE with matching agent_type and instance_id."""
    master.start()
    activate = master.activate(_ehlo("scanner"))
    assert activate.agent_type == "scanner"
    assert activate.instance_id.startswith("scanner:")
    assert activate.capability_grants == trading_policy()["scanner"]


def test_activate_writes_agent_instance_node(master: MasterAgent) -> None:
    """MST-STA-02: activate() writes AgentInstance with state=active."""
    master.start()
    ehlo = EHLOMessage(
        ephemeral_boot_id="boot:abc",
        agent_type="analyst",
        capability_declaration={},
    )
    activate = master.activate(ehlo)
    node = master._graph.get_node("AgentInstance", activate.instance_id)
    assert node is not None
    assert node.props["state"] == AgentState.ACTIVE.value
    assert node.props["agent_type"] == "analyst"
    assert node.props["boot_id"] == "boot:abc"


def test_activate_writes_capability_grant_nodes(master: MasterAgent) -> None:
    """MST-STA-03: activate() writes one CapabilityGrant per capability."""
    master.start()
    ehlo = EHLOMessage(
        ephemeral_boot_id="boot:xyz",
        agent_type="scanner",
        capability_declaration={},
    )
    activate = master.activate(ehlo)
    grants = master._graph.list_nodes("CapabilityGrant")
    instance_grants = [
        g for g in grants if str(g.props["instance_id"]) == activate.instance_id
    ]
    expected_caps = set(trading_policy()["scanner"])
    found_caps = {str(g.props["capability"]) for g in instance_grants}
    assert found_caps == expected_caps


def test_activate_second_instance_of_same_type_gets_unique_id(
    master: MasterAgent,
) -> None:
    """MST-IDM-01: two EHLO from the same agent_type produce distinct instance_ids."""
    master.start()
    ehlo1 = EHLOMessage(
        ephemeral_boot_id="boot:1", agent_type="reporter", capability_declaration={}
    )
    ehlo2 = EHLOMessage(
        ephemeral_boot_id="boot:2", agent_type="reporter", capability_declaration={}
    )
    a1 = master.activate(ehlo1)
    a2 = master.activate(ehlo2)
    assert a1.instance_id != a2.instance_id


def test_activate_unknown_agent_type_raises(master: MasterAgent) -> None:
    """MST-NEV-01: unknown agent_type rejected; no graph write."""
    master.start()
    ehlo = EHLOMessage(
        ephemeral_boot_id="boot:bad",
        agent_type="rogue",
        capability_declaration={},
    )
    with pytest.raises(ValueError, match="unknown agent_type"):
        master.activate(ehlo)
    assert len(master._graph.list_nodes("AgentInstance")) == 0


# ── injected grant policy ────────────────────────────────────────────────────


def _ehlo(agent_type: str) -> EHLOMessage:
    return EHLOMessage(
        ephemeral_boot_id=f"boot:{agent_type}",
        agent_type=agent_type,
        capability_declaration={},
    )


def test_activate_uses_injected_grant_policy() -> None:
    """Master activates only types in the injected policy; a custom 'widget' works."""
    policy: dict[str, dict[str, object]] = {
        "widget": {"messaging": {"operations": ["publish"]}}
    }
    master = MasterAgent(graph=InMemoryGraphStore(), grant_policy=policy)
    master.start()

    activate = master.activate(_ehlo("widget"))
    assert activate.capability_grants == policy["widget"]

    with pytest.raises(ValueError, match="unknown agent_type"):
        master.activate(_ehlo("scanner"))


def test_substrate_default_knows_no_agent_types() -> None:
    """With no injected policy the substrate knows nothing — every type is unknown."""
    master = MasterAgent(graph=InMemoryGraphStore())
    master.start()
    with pytest.raises(ValueError, match="unknown agent_type"):
        master.activate(_ehlo("scanner"))


# ── drain ────────────────────────────────────────────────────────────────────


def test_drain_returns_drain_message(master: MasterAgent) -> None:
    """MST-OUT-02: drain() returns DRAINMessage with matching instance_id."""
    master.start()
    ehlo = EHLOMessage(
        ephemeral_boot_id="boot:d", agent_type="monitor", capability_declaration={}
    )
    activate = master.activate(ehlo)
    msg = master.drain(activate.instance_id)
    assert msg.instance_id == activate.instance_id
    assert msg.reason == "CLEAN"


def test_drain_marks_instance_in_graph(master: MasterAgent) -> None:
    """MST-STA-04: drain() writes drain_reason to AgentInstance node."""
    master.start()
    ehlo = EHLOMessage(
        ephemeral_boot_id="boot:d2", agent_type="monitor", capability_declaration={}
    )
    activate = master.activate(ehlo)
    master.drain(activate.instance_id, reason="UPGRADE")
    node = master._instance_node(activate.instance_id)
    assert node is not None
    assert node.props["drain_reason"] == "UPGRADE"


def test_drain_unknown_instance_raises(master: MasterAgent) -> None:
    """MST-NEV-02: drain on unknown instance_id raises KeyError; no graph write."""
    master.start()
    with pytest.raises(KeyError, match="no AgentInstance"):
        master.drain("nonexistent:id")


# ── store helpers ────────────────────────────────────────────────────────────


def test_write_agent_definition_writes_node(master: MasterAgent) -> None:
    """MST-IDN-02: write_agent_definition upserts an AgentDefinition node."""
    graph = InMemoryGraphStore()
    schema: dict[str, object] = {"messaging": {"operations": ["publish"]}}
    node = write_agent_definition(graph, "scanner", schema)
    assert node is not None
    assert node.props["agent_type"] == "scanner"
    assert "capability_schema" in node.props
