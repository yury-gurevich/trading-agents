"""Execution declares every label its divergence writer writes (S251 D7, DRIFT-094).

Agent: execution
Role: run one divergence episode through the run-start flag writer on a store that
      records each write, and pin that every label written is in the execution
      contract's owns_graph and every Flag or FlagResolution is of the declared family.
External I/O: none (in-memory graph).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.tests.flag_episode_helpers import MDLZ, PREFIX, run
from contracts.execution import CONTRACT
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from kernel import Node
    from kernel.graph_support import Props

_FLAG_LABELS = {"Flag", "FlagResolution"}


class _WriteSpy(InMemoryGraphStore):
    """An in-memory store that remembers the label and props of every node written."""

    def __init__(self) -> None:
        super().__init__()
        self.written: list[tuple[str, dict[str, object]]] = []

    def merge_node(
        self, label: str, key: str, props: Props, *, schema_version: int = 1
    ) -> Node:
        self.written.append((label, dict(props)))
        return super().merge_node(label, key, props, schema_version=schema_version)


def test_every_label_the_divergence_writer_writes_is_declared() -> None:
    """EXEC-IDN-04 / SUP-IDN-02 (DRIFT-094): an episode opened at warn, escalated to
    critical and closed when the divergence is gone writes Flag and FlagResolution
    nodes; both labels are in execution's owns_graph, so every label written is
    declared, and every such node belongs to the broker-position-divergence family."""
    graph = _WriteSpy()

    run(graph, "snap-1", MDLZ)
    run(graph, "snap-2", MDLZ)
    run(graph, "snap-3")

    labels = {label for label, _ in graph.written}
    assert labels == {"BrokerPositionSnapshot", *_FLAG_LABELS}
    assert labels <= set(CONTRACT.owns_graph)
    family = [props for label, props in graph.written if label in _FLAG_LABELS]
    assert labels & _FLAG_LABELS == _FLAG_LABELS
    assert family
    assert all(str(props["subject_ref"]).startswith(PREFIX) for props in family)
