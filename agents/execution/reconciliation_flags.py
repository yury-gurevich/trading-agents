"""Divergence-flag lifecycle: severity follows persistence, not first sight.

Agent: execution
Role: raise the DL-44 divergence Flag at `warn`, escalate to `critical` only when
      the same divergence survives to the next run (adoption failed), and retire
      a flag once its divergence is gone.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.execution.reconciliation_store import Divergence
    from kernel import GraphStore, Node

# Flag/FlagResolution keys are supervisor-owned; we never import that module.
# Replicated from agents/supervisor/store.py (_flag_key / _resolution_key):
#   flag:{subject_ref}:{severity}  ·  resolution:flag:{subject_ref}:{severity}
_PREFIX = "broker-position-divergence:"
# Flags written before S178 keyed their subject on the per-run snapshot, so each
# run minted a unique one. They cannot match a live divergence and are retired by
# scripts/sweep_divergence_flags.py, never by a run.
_LEGACY_PREFIX = f"{_PREFIX}broker-position-snapshot:"


def subject_ref_for(divergence: Divergence) -> str:
    """Return the run-stable subject_ref identifying one divergence."""
    return f"{_PREFIX}{divergence.kind}:{divergence.ticker}"


def record_divergences(
    graph: GraphStore, *, snapshot: Node, divergences: tuple[Divergence, ...]
) -> None:
    """Write the DL-44 flags for one run-start snapshot.

    First sight of a divergence is a `warn`: reconciliation is *about to* adopt it,
    so it describes normal operation and must not pin `healthy` to false. A
    divergence still present at the next run start was **not** adopted, and is
    escalated to `critical`. One whose divergence is gone is retired.
    """
    live: set[str] = set()
    for divergence in divergences:
        subject_ref = subject_ref_for(divergence)
        live.add(subject_ref)
        if _flag(graph, subject_ref, "warn") is None:
            _write_flag(graph, subject_ref, "warn", snapshot, divergence)
            continue
        if _flag(graph, subject_ref, "critical") is None:
            _write_flag(graph, subject_ref, "critical", snapshot, divergence)
        _resolve(graph, subject_ref, "warn", snapshot, "superseded by critical")
    _retire_absent(graph, snapshot, live)


def resolve_legacy_flags(graph: GraphStore, *, reason: str) -> tuple[str, ...]:
    """Retire pre-S178 snapshot-keyed divergence flags; returns subject_refs."""
    resolved: list[str] = []
    for flag in graph.list_nodes("Flag"):
        subject_ref = str(flag.props.get("subject_ref", ""))
        if not subject_ref.startswith(_LEGACY_PREFIX):
            continue
        severity = str(flag.props.get("severity", "critical"))
        if _resolve(graph, subject_ref, severity, None, reason):
            resolved.append(subject_ref)
    return tuple(resolved)


def _retire_absent(graph: GraphStore, snapshot: Node, live: set[str]) -> None:
    for flag in graph.list_nodes("Flag"):
        subject_ref = str(flag.props.get("subject_ref", ""))
        if not subject_ref.startswith(_PREFIX):
            continue
        if subject_ref in live or subject_ref.startswith(_LEGACY_PREFIX):
            continue
        severity = str(flag.props.get("severity", "critical"))
        _resolve(graph, subject_ref, severity, snapshot, "divergence no longer present")


def _flag(graph: GraphStore, subject_ref: str, severity: str) -> Node | None:
    return graph.get_node("Flag", f"flag:{subject_ref}:{severity}")


def _write_flag(
    graph: GraphStore,
    subject_ref: str,
    severity: str,
    snapshot: Node,
    divergence: Divergence,
) -> None:
    graph.merge_node(
        "Flag",
        f"flag:{subject_ref}:{severity}",
        {
            "subject_ref": subject_ref,
            "severity": severity,
            "reason": _reason(snapshot, severity, divergence),
            "status": "pending",
            "created_at": datetime.now(tz=UTC).isoformat(),
        },
    )


def _resolve(
    graph: GraphStore,
    subject_ref: str,
    severity: str,
    snapshot: Node | None,
    reason: str,
) -> bool:
    """Append a FlagResolution (EXEC-STA-03: append-only; never mutate the Flag)."""
    flag = _flag(graph, subject_ref, severity)
    if flag is None:
        return False
    key = f"resolution:flag:{subject_ref}:{severity}"
    if graph.get_node("FlagResolution", key) is not None:
        return False
    props: dict[str, object] = {
        "subject_ref": subject_ref,
        "severity": severity,
        "resolved_at": datetime.now(tz=UTC).isoformat(),
        "resolved_by": "run-start-reconciliation",
        "resolution_reason": reason,
    }
    if snapshot is not None:
        props["resolving_snapshot_key"] = snapshot.key
    resolution = graph.merge_node("FlagResolution", key, props)
    graph.add_edge(resolution, flag, "RESOLVES")
    return True


def _reason(snapshot: Node, severity: str, divergence: Divergence) -> str:
    if severity == "warn":
        head = f"Broker position divergence at run start ({snapshot.key})"
        return f"{head}:\n- {divergence.text}"
    head = f"Divergence survived a full run without adoption ({snapshot.key})"
    return f"{head}:\n- {divergence.text}"
