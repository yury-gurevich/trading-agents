"""Divergence-flag episodes: the upgrade path, subject shape and read bound (S248).

Agent: execution
Role: prove an open suffix-less Flag is the open episode, spent keys never touch
      a new one, the subject is deterministic, and each call reads each label once.
External I/O: none.
"""

from __future__ import annotations

from collections import Counter

from agents.execution.reconciliation_flags import subject_ref_for
from agents.execution.reconciliation_store import Divergence
from agents.execution.tests.flag_episode_helpers import (
    BAC,
    LEGACY_PREFIX,
    MDLZ,
    PREFIX,
    identity,
    open_flags,
    open_summary,
    run,
)
from kernel import GraphStore, InMemoryGraphStore, Node

_LIVE_KEY = "broker-position-snapshot:sched-2026-09-30:2026-09-30T22:32:22+00:00"


def _suffixless(graph: GraphStore, divergence: Divergence, severity: str) -> str:
    subject = f"{PREFIX}{divergence.kind}:{divergence.ticker}"
    props = {"subject_ref": subject, "severity": severity, "status": "pending"}
    graph.merge_node("Flag", f"flag:{subject}:{severity}", props)
    return subject


def _resolve(graph: GraphStore, subject: str, severity: str) -> None:
    props = {"subject_ref": subject, "severity": severity}
    graph.merge_node("FlagResolution", f"resolution:flag:{subject}:{severity}", props)


def _reason(graph: GraphStore, subject: str, severity: str) -> str:
    node = graph.get_node("FlagResolution", f"resolution:flag:{subject}:{severity}")
    assert node is not None
    return str(node.props["resolution_reason"])


def test_an_open_suffixless_flag_is_the_open_episode() -> None:
    """EXEC-OBS-07: an open S178-format warn escalates or retires as before."""
    graph = InMemoryGraphStore()
    mdlz = _suffixless(graph, MDLZ, "warn")
    bac = _suffixless(graph, BAC, "warn")

    run(graph, "s9", MDLZ)

    assert [n.props["subject_ref"] for n in open_flags(graph)] == [mdlz]
    assert open_summary(graph) == [("MDLZ", "critical")]
    assert len(graph.list_nodes("Flag")) == 3
    assert _reason(graph, mdlz, "warn") == "superseded by critical"
    assert _reason(graph, bac, "warn") == "divergence no longer present"


def test_spent_suffixless_keys_do_not_touch_a_new_episode() -> None:
    """EXEC-OBS-07: the live shape of the 12 tickers opens a fresh `warn`."""
    graph = InMemoryGraphStore()
    for severity in ("warn", "critical"):
        _resolve(graph, _suffixless(graph, MDLZ, severity), severity)

    run(graph, "s9", MDLZ)

    assert [n.props["subject_ref"] for n in open_flags(graph)] == [
        subject_ref_for(MDLZ, "s9")
    ]
    assert open_summary(graph) == [("MDLZ", "warn")]


def test_the_subject_is_deterministic_and_well_formed() -> None:
    """EXEC-OBS-07: the episode is named by its first-sight snapshot, nothing else."""
    subjects = []
    for key in (_LIVE_KEY, _LIVE_KEY, "broker-position-snapshot:sched-2:t1"):
        graph = InMemoryGraphStore()
        run(graph, key, MDLZ)
        (flag,) = open_flags(graph)
        subjects.append(str(flag.props["subject_ref"]))

    assert subjects[0] == subjects[1] == subject_ref_for(MDLZ, _LIVE_KEY)
    assert subjects[2] != subjects[0]
    for subject in subjects:
        assert subject.startswith(PREFIX)
        assert not subject.startswith(LEGACY_PREFIX)
        assert identity(subject) == ("extra_graph_position", "MDLZ")


def test_a_repeated_call_for_one_snapshot_is_not_a_survived_run() -> None:
    """EXEC-OBS-07: critical only at the *next* run-start reconciliation."""
    graph = InMemoryGraphStore()
    run(graph, "s1", MDLZ)

    run(graph, "s1", MDLZ)

    assert open_summary(graph) == [("MDLZ", "warn")]
    assert len(graph.list_nodes("Flag")) == 1


def test_an_open_critical_supersedes_a_stray_open_warn() -> None:
    """EXEC-OBS-07: a live divergence keeps exactly one open Flag."""
    graph = InMemoryGraphStore()
    warn = _suffixless(graph, MDLZ, "warn")
    _suffixless(graph, MDLZ, "critical")

    run(graph, "s9", MDLZ)

    assert open_summary(graph) == [("MDLZ", "critical")]
    assert _reason(graph, warn, "warn") == "superseded by critical"
    assert len(graph.list_nodes("Flag")) == 2


def test_a_spent_critical_key_is_never_rewritten() -> None:
    """EXEC-STA-03 / EXEC-OBS-07: no escalation onto a spent key (DL-254 D4)."""
    graph = InMemoryGraphStore()
    _suffixless(graph, MDLZ, "warn")
    critical = _suffixless(graph, MDLZ, "critical")
    _resolve(graph, critical, "critical")

    run(graph, "s9", MDLZ)

    node = graph.get_node("Flag", f"flag:{critical}:critical")
    assert node is not None
    assert "reason" not in node.props
    assert open_summary(graph) == [("MDLZ", "warn")]


class _CountingStore(InMemoryGraphStore):
    """Count the reads one `record_divergences` call makes."""

    def __init__(self) -> None:
        super().__init__()
        self.reads: Counter[str] = Counter()

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        self.reads[label] += 1
        return super().list_nodes(label)

    def get_node(self, label: str, key: str) -> Node | None:
        self.reads[f"get:{label}"] += 1
        return super().get_node(label, key)


def test_each_call_reads_flag_and_resolution_once() -> None:
    """EXEC-OBS-07: 30 live divergences cost one read of each label per call."""
    graph = _CountingStore()
    live = tuple(
        Divergence("qty_mismatch", f"T{i:02d}", "graph_qty=1") for i in range(30)
    )
    for key, divergences in (("s1", live), ("s2", live), ("s3", ())):
        graph.reads.clear()

        run(graph, key, *divergences)

        assert graph.reads == Counter({"Flag": 1, "FlagResolution": 1}), key
