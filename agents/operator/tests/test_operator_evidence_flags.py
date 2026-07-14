"""Run-grounded operator evidence includes outstanding flags.

Agent: operator
Role: prove selected-run explanations include unresolved operator attention.
External I/O: none; graph is in-memory.
"""

from agents.operator.domain.evidence import gather_evidence
from kernel import InMemoryGraphStore, Node


def test_selected_run_evidence_includes_only_pending_flags() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node("RunRequest", "request:a", {"run_id": "run-a"})
    graph.merge_node(
        "Flag", "flag:pending", {"status": "pending", "severity": "critical"}
    )
    graph.merge_node("Flag", "flag:closed", {"status": "resolved"})

    evidence = gather_evidence(graph, "Selected run: run-a", 10)

    assert [row["key"] for row in evidence] == ["request:a", "flag:pending"]


def test_selected_run_evidence_tolerates_graph_without_flag_api() -> None:
    graph = _NoFlagAPI()
    graph.merge_node("RunRequest", "request:a", {"run_id": "run-a"})
    assert gather_evidence(graph, "Selected run: run-a", 10)[0]["key"] == "request:a"


class _NoFlagAPI(InMemoryGraphStore):
    def list_nodes(self, label: str) -> tuple[Node, ...]:
        if label == "Flag":
            raise AttributeError
        return super().list_nodes(label)
