"""The boundary map is self-enforcing.

These checks fail CI the moment the agent contracts drift back toward the
conveyor belt: two agents sharing a table, two agents touching the same external
system, a dangling dependency, or an untyped capability.
"""

from __future__ import annotations

from collections import Counter

import pytest
from pydantic import BaseModel

from contracts import AGENT_MODULES, registry

REG = registry()


def test_all_agents_present():
    assert set(REG) == set(AGENT_MODULES)
    assert len(REG) == 12


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


def test_each_table_has_one_writer():
    owners = Counter(t for c in REG.values() for t in c.owns_tables)
    shared = {t: n for t, n in owners.items() if n > 1}
    assert not shared, f"tables owned by >1 agent (shared schema): {shared}"


def test_each_graph_label_has_one_writer():
    owners = Counter(g for c in REG.values() for g in c.owns_graph)
    shared = {g: n for g, n in owners.items() if n > 1}
    assert not shared, f"graph labels written by >1 agent: {shared}"


@pytest.mark.parametrize("name", AGENT_MODULES)
def test_every_agent_states_its_boundaries(name):
    c = REG[name]
    assert c.mission.strip(), f"{name} has no mission"
    assert c.never, f"{name} declares no hard boundaries (never[])"
    assert c.owns_tables or c.owns_graph, f"{name} owns no data"
