"""Divergence-flag lifecycle: one episode per occurrence, severity by persistence.

Agent: execution
Role: open a DL-44 divergence episode at `warn` under the snapshot that first saw
      it, escalate it to `critical` only when it survives to the next run start
      (adoption failed), and retire it once its divergence is gone (EXEC-OBS-07).
External I/O: GraphStore reads and writes via the injected backend.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.execution.divergence_episodes import (
    LEGACY_PREFIX,
    PREFIX,
    Episode,
    flag_join,
    open_episodes,
)

if TYPE_CHECKING:
    from agents.execution.reconciliation_store import Divergence
    from kernel import GraphStore, Node

# Flag/FlagResolution keys are supervisor-owned; we never import that module.
# Replicated from agents/supervisor/store.py (_flag_key / _resolution_key):
#   flag:{subject_ref}:{severity}  ·  resolution:flag:{subject_ref}:{severity}
_SUPERSEDED = "superseded by critical"
_GONE = "divergence no longer present"


def subject_ref_for(divergence: Divergence, episode: str) -> str:
    """Return the subject_ref of one divergence episode (DL-254 D1/D2).

    `episode` is the key of the snapshot that first saw the divergence. Flags
    from S178 to S248 carry no episode; they parse to the same (kind, ticker).
    """
    return f"{PREFIX}{divergence.kind}:{divergence.ticker}:{episode}"


def record_divergences(
    graph: GraphStore, *, snapshot: Node, divergences: tuple[Divergence, ...]
) -> None:
    """Write the DL-44 flags for one run-start snapshot (EXEC-OBS-07).

    A divergence with no open episode opens one at `warn`: reconciliation is
    *about to* adopt it, so it must not pin `healthy` to false, whatever the
    ticker's history. An open `warn` still present at a later snapshot was **not**
    adopted and escalates to `critical` on its own subject. An open episode whose
    divergence is gone is retired. Flag and FlagResolution are each read once.
    """
    flags = graph.list_nodes("Flag")
    episodes = open_episodes(flags, graph.list_nodes("FlagResolution"))
    written = {node.key for node in flags}
    for divergence in divergences:
        episode = episodes.pop((divergence.kind, divergence.ticker), {})
        _advance(graph, written, snapshot, divergence, episode)
    for episode in episodes.values():
        for flag in episode.values():
            _close(graph, flag, snapshot, _GONE)


def resolve_legacy_flags(graph: GraphStore, *, reason: str) -> tuple[str, ...]:
    """Retire pre-S178 snapshot-keyed divergence flags; returns subject_refs."""
    resolved: list[str] = []
    for flag in graph.list_nodes("Flag"):
        subject_ref = str(flag.props.get("subject_ref", ""))
        if not subject_ref.startswith(LEGACY_PREFIX):
            continue
        severity = str(flag.props.get("severity", "critical"))
        if _resolve(graph, subject_ref, severity, reason):
            resolved.append(subject_ref)
    return tuple(resolved)


def _advance(
    graph: GraphStore,
    written: set[str],
    snapshot: Node,
    divergence: Divergence,
    episode: Episode,
) -> None:
    warn, critical = episode.get("warn"), episode.get("critical")
    if warn is None:
        if critical is None:
            subject_ref = subject_ref_for(divergence, snapshot.key)
            _write_flag(graph, written, subject_ref, "warn", snapshot, divergence)
        return
    if critical is None and not _escalate(graph, written, snapshot, divergence, warn):
        return
    _close(graph, warn, snapshot, _SUPERSEDED)


def _escalate(
    graph: GraphStore,
    written: set[str],
    snapshot: Node,
    divergence: Divergence,
    warn: Node,
) -> bool:
    subject_ref = str(warn.props["subject_ref"])
    if subject_ref == subject_ref_for(divergence, snapshot.key):
        return False  # the snapshot that opened the episode is no survived run
    return _write_flag(graph, written, subject_ref, "critical", snapshot, divergence)


def _write_flag(
    graph: GraphStore,
    written: set[str],
    subject_ref: str,
    severity: str,
    snapshot: Node,
    divergence: Divergence,
) -> bool:
    key = f"flag:{subject_ref}:{severity}"
    if key in written:
        return False  # EXEC-STA-03: a spent key is never rewritten
    graph.merge_node(
        "Flag",
        key,
        {
            "subject_ref": subject_ref,
            "severity": severity,
            "reason": _reason(snapshot, severity, divergence),
            "status": "pending",
            "created_at": datetime.now(tz=UTC).isoformat(),
        },
    )
    written.add(key)
    return True


def _close(graph: GraphStore, flag: Node, snapshot: Node, reason: str) -> None:
    subject_ref, severity = flag_join(flag)
    _append_resolution(graph, flag, subject_ref, severity, snapshot, reason)


def _resolve(graph: GraphStore, subject_ref: str, severity: str, reason: str) -> bool:
    flag = graph.get_node("Flag", f"flag:{subject_ref}:{severity}")
    if flag is None:
        return False
    if graph.get_node("FlagResolution", f"resolution:{flag.key}") is not None:
        return False
    _append_resolution(graph, flag, subject_ref, severity, None, reason)
    return True


def _append_resolution(
    graph: GraphStore,
    flag: Node,
    subject_ref: str,
    severity: str,
    snapshot: Node | None,
    reason: str,
) -> None:
    """Append a FlagResolution (EXEC-STA-03: append-only; never mutate the Flag)."""
    props: dict[str, object] = {
        "subject_ref": subject_ref,
        "severity": severity,
        "resolved_at": datetime.now(tz=UTC).isoformat(),
        "resolved_by": "run-start-reconciliation",
        "resolution_reason": reason,
    }
    if snapshot is not None:
        props["resolving_snapshot_key"] = snapshot.key
    resolution = graph.merge_node(
        "FlagResolution", f"resolution:flag:{subject_ref}:{severity}", props
    )
    graph.add_edge(resolution, flag, "RESOLVES")


def _reason(snapshot: Node, severity: str, divergence: Divergence) -> str:
    if severity == "warn":
        head = f"Broker position divergence at run start ({snapshot.key})"
        return f"{head}:\n- {divergence.text}"
    head = f"Divergence survived a full run without adoption ({snapshot.key})"
    return f"{head}:\n- {divergence.text}"
