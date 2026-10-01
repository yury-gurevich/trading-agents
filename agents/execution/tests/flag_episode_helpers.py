"""Shared fixtures for the divergence-flag episode tests (S248).

Agent: execution
Role: run one run-start reconciliation's flag step, and read which divergence
      Flags are open by the (subject_ref, severity) join every reader uses.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.reconciliation_flags import record_divergences
from agents.execution.reconciliation_store import Divergence

if TYPE_CHECKING:
    from kernel import GraphStore, Node

PREFIX = "broker-position-divergence:"
LEGACY_PREFIX = f"{PREFIX}broker-position-snapshot:"
MDLZ = Divergence("extra_graph_position", "MDLZ", "graph_qty=16")
BAC = Divergence("missing_graph_position", "BAC", "broker_qty=40")


def snapshot(graph: GraphStore, key: str) -> Node:
    """Write a run-start snapshot node the flags can name."""
    return graph.merge_node("BrokerPositionSnapshot", key, {"holding_count": 0})


def run(graph: GraphStore, key: str, *divergences: Divergence) -> None:
    """Record the flags of one run-start reconciliation at snapshot `key`."""
    record_divergences(graph, snapshot=snapshot(graph, key), divergences=divergences)


def identity(subject_ref: str) -> tuple[str, str]:
    """Return (kind, ticker), the first two fields after the family prefix."""
    kind, _, rest = subject_ref.removeprefix(PREFIX).partition(":")
    return kind, rest.split(":", 1)[0]


def open_flags(graph: GraphStore) -> list[Node]:
    """Return the unresolved divergence Flags, as health and surfaces read them."""
    resolved = {
        (n.props.get("subject_ref"), n.props.get("severity"))
        for n in graph.list_nodes("FlagResolution")
    }
    return [
        n
        for n in graph.list_nodes("Flag")
        if str(n.props.get("subject_ref", "")).startswith(PREFIX)
        and (n.props.get("subject_ref"), n.props.get("severity")) not in resolved
    ]


def open_summary(graph: GraphStore) -> list[tuple[str, str]]:
    """Return sorted (ticker, severity) pairs for every open divergence Flag."""
    return sorted(
        (identity(str(n.props["subject_ref"]))[1], str(n.props["severity"]))
        for n in open_flags(graph)
    )
