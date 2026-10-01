"""The boundary map is self-enforcing.

These checks fail CI the moment the agent contracts drift back toward the
conveyor belt: two agents sharing a graph label, two agents touching the same
external system, a dangling dependency, or an untyped capability.
"""

from __future__ import annotations

from collections import Counter

import pytest
from pydantic import BaseModel

from contracts import AGENT_MODULES, registry

REG = registry()


def test_all_agents_present():
    assert set(REG) == set(AGENT_MODULES)
    assert len(REG) == 13


@pytest.mark.parametrize("name", AGENT_MODULES)
def test_capabilities_are_typed(name):
    contract = REG[name]
    assert contract.consumes, f"{name} exposes no capabilities"
    for cap in contract.consumes:
        assert isinstance(cap.request, type)
        assert issubclass(cap.request, BaseModel)
        assert isinstance(cap.response, type)
        assert issubclass(cap.response, BaseModel)


@pytest.mark.parametrize("name", AGENT_MODULES)
def test_dependencies_resolve(name):
    for dep in REG[name].depends_on:
        assert dep in REG, f"{name} depends on unknown agent {dep!r}"
    assert name not in REG[name].depends_on, f"{name} depends on itself"


def test_external_io_is_exclusive():
    owners = Counter(io for c in REG.values() for io in c.external_io)
    shared = {io: n for io, n in owners.items() if n > 1}
    assert not shared, f"external systems touched by >1 agent: {shared}"


# The one declared exception to single-writer (DRIFT-094, S251): run-start
# reconciliation writes the broker-position divergence family of these two labels.
_DECLARED_SHARED = {
    "Flag": {"execution", "supervisor"},
    "FlagResolution": {"execution", "supervisor"},
}


def test_each_graph_label_has_one_writer():
    """SUP-IDN-02 / EXEC-IDN-04: every graph label has one owning contract, except
    the declared divergence-family pair, shared by exactly those two contracts."""
    owners = Counter(g for c in REG.values() for g in c.owns_graph)
    shared = {g for g, n in owners.items() if n > 1}
    assert shared == set(_DECLARED_SHARED), f"labels written by >1 agent: {shared}"
    for label, writers in _DECLARED_SHARED.items():
        assert {name for name, c in REG.items() if label in c.owns_graph} == writers


@pytest.mark.parametrize("name", AGENT_MODULES)
def test_every_agent_states_its_boundaries(name):
    c = REG[name]
    assert c.mission.strip(), f"{name} has no mission"
    assert c.never, f"{name} declares no hard boundaries (never[])"
    assert c.owns_graph, f"{name} owns no graph labels"
