"""Immutable resume-from-stage placement for graph-pull pipeline runs.

Agent: orchestration
Role: supersede one run with a child whose upstream artifacts are provenance links.
External I/O: writes only the injected GraphStore.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from contracts.resume import RESUME_STAGES, ResumePlacement, ResumeRequest, ResumeStage
from orchestration.batch_trace import walk_chain

if TYPE_CHECKING:
    from kernel import GraphStore, MessageBus, Node
_ARTIFACTS = (
    ("MarketData", "INGESTED_BY"),
    ("ScanRun", "SCANNED_BY"),
    ("AnalystRun", "ANALYZED_BY"),
    ("PMRun", "EVALUATED_BY"),
    ("ExecutionRun", "EXECUTED_BY"),
    ("MonitorRun", "MONITORED_BY"),
    ("Snapshot", "REPORTED_BY"),
)


def resume_run(
    graph: GraphStore, *, source_run_id: str, resume_from: str
) -> ResumePlacement:
    """Place an immutable child run, linking stages before ``resume_from``."""
    stage = _stage(resume_from)
    source = graph.get_node("RunRequest", f"run-request:{source_run_id}")
    if source is None:
        raise ValueError(f"unknown source run: {source_run_id}")
    chain = walk_chain(graph, source_run_id)
    required = _ARTIFACTS[: RESUME_STAGES.index(stage)]
    missing = next((label for label, _edge in required if label not in chain), None)
    if missing is not None:
        raise ValueError(f"cannot resume from {stage}: upstream {missing} is missing")

    child_id = f"{source_run_id}-resume-{stage}"
    child_key = f"run-request:{child_id}"
    current = graph.get_node("RunRequest", child_key)
    if current is not None:
        return ResumePlacement(
            child_run_id=child_id,
            node_key=child_key,
            resume_from=stage,
            linked=_linked_refs(graph, current),
            created=False,
        )

    child = graph.merge_node(
        "RunRequest",
        child_key,
        {
            "run_id": child_id,
            "tickers": list(source.props.get("tickers", ())),
            "requested_at": source.props.get("requested_at"),
            "resume_from": stage,
            "source_run_id": source_run_id,
            "resumed_at": datetime.now(tz=UTC).isoformat(),
        },
    )
    graph.add_edge(child, source, "RESUMES")
    linked = _link_upstream(graph, child, chain, required)
    return ResumePlacement(
        child_run_id=child_id,
        node_key=child_key,
        resume_from=stage,
        linked=linked,
        created=True,
    )


def bind_resume_run(bus: MessageBus, graph: GraphStore) -> None:
    """Bind the orchestration-owned primitive for supervisor-only RPC."""

    def handle(payload: dict[str, Any]) -> dict[str, Any]:
        request = ResumeRequest.model_validate(payload)
        result = resume_run(
            graph,
            source_run_id=request.source_run_id,
            resume_from=request.resume_from,
        )
        return result.model_dump(mode="json")

    bus.register("orchestration", "resume_run", handle, ("supervisor",))


def _link_upstream(
    graph: GraphStore,
    child: Node,
    chain: dict[str, Node],
    required: tuple[tuple[str, str], ...],
) -> tuple[str, ...]:
    previous = child
    clones: dict[str, Node] = {}
    refs: list[str] = []
    for label, edge in required:
        source = chain[label]
        clone_key = f"resume-link:{child.props['run_id']}:{label.lower()}"
        props = _linked_props(
            label, source, clone_key, clones, str(child.props["run_id"])
        )
        clone = graph.merge_node(label, clone_key, props)
        graph.add_edge(previous, clone, edge)
        graph.add_edge(clone, source, "LINKED_FROM")
        if label == "ScanRun":
            graph.add_edge(clone, clones["MarketData"], "DERIVED_FROM")
        _link_side_branch(graph, clone, source, label)
        clones[label] = clone
        previous = clone
        refs.append(f"{source.label}:{source.key}")
    _link_regime(graph, clones, chain, str(child.props["run_id"]), refs)
    return tuple(refs)


def _linked_props(
    label: str,
    source: Node,
    clone_key: str,
    clones: dict[str, Node],
    child_id: str,
) -> dict[str, object]:
    props = dict(source.props)
    props.update({"linked_from_key": source.key, "resume_run_id": child_id})
    if label == "MarketData":
        props["run_id"] = child_id
    elif label == "PMRun":
        order_set = dict(props["order_intent_set"])
        order_set["run_id"] = clone_key
        provenance = dict(order_set["provenance"])
        provenance.update({"run_id": clone_key, "graph_node_id": f"PMRun:{clone_key}"})
        order_set["provenance"] = provenance
        props["order_intent_set"] = order_set
    elif label == "ExecutionRun":
        props["source_pm_run_id"] = clones["PMRun"].key
    elif label == "MonitorRun":
        props["source_run_id"] = clones["PMRun"].key
        props["exec_run_id"] = clones["ExecutionRun"].key
    return props


def _link_side_branch(graph: GraphStore, clone: Node, source: Node, label: str) -> None:
    edge = {"AnalystRun": "FORECAST_BY", "PMRun": "DELIBERATED_BY"}.get(label)
    if edge is None:
        return
    side = next(iter(graph.descendants(source, max_depth=1, edge_types={edge})), None)
    if side is not None:
        graph.add_edge(clone, side, edge)


def _link_regime(
    graph: GraphStore,
    clones: dict[str, Node],
    chain: dict[str, Node],
    child_id: str,
    refs: list[str],
) -> None:
    if "MarketData" not in clones:
        return
    original_id = str(chain["MarketData"].props.get("run_id", ""))
    source = graph.get_node("RegimeContext", f"regime-context:{original_id}")
    if source is None:
        return
    props = dict(source.props)
    props.update({"run_id": child_id, "linked_from_key": source.key})
    clone = graph.merge_node("RegimeContext", f"regime-context:{child_id}", props)
    graph.add_edge(clone, source, "LINKED_FROM")
    refs.append(f"{source.label}:{source.key}")


def _linked_refs(graph: GraphStore, child: Node) -> tuple[str, ...]:
    linked = graph.descendants(
        child, max_depth=8, edge_types={edge for _, edge in _ARTIFACTS}
    )
    refs: list[str] = []
    for clone in linked:
        source = next(
            iter(graph.descendants(clone, max_depth=1, edge_types={"LINKED_FROM"})),
            None,
        )
        if source is not None:
            refs.append(f"{source.label}:{source.key}")
    return tuple(refs)


def _stage(value: str) -> ResumeStage:
    if value not in RESUME_STAGES:
        raise ValueError(f"invalid resume stage: {value}")
    return value
