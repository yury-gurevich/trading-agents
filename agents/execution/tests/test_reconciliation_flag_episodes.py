"""Divergence-flag episode tests — critical only when it survived a run (S248).

Agent: execution
Role: prove every occurrence of a divergence is its own episode: `warn` at first
      sight whatever the ticker's history, `critical` only after a survived run.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.tests.flag_episode_helpers import (
    BAC,
    MDLZ,
    open_flags,
    open_summary,
    run,
)
from kernel import InMemoryGraphStore


def test_a_second_episodes_first_sighting_is_warn() -> None:
    """EXEC-OBS-07: a divergence seen again after its episode closed is `warn`."""
    graph = InMemoryGraphStore()
    run(graph, "s1", MDLZ)
    run(graph, "s2")

    run(graph, "s3", MDLZ)

    severities = [str(n.props["severity"]) for n in open_flags(graph)]
    assert severities == ["warn"]


def test_a_third_episode_is_flagged_and_escalates_when_it_survives() -> None:
    """EXEC-OBS-07: no ticker's history spends its keys; survival is critical."""
    graph = InMemoryGraphStore()
    for key, present in (("s1", True), ("s2", False), ("s3", True), ("s4", False)):
        run(graph, key, *((MDLZ,) if present else ()))

    run(graph, "s5", MDLZ)
    assert [str(n.props["severity"]) for n in open_flags(graph)] == ["warn"]

    run(graph, "s6", MDLZ)
    open_ = open_flags(graph)
    assert [str(n.props["severity"]) for n in open_] == ["critical"]
    assert "survived a full run" in str(open_[0].props["reason"])


# Five episodes for two tickers: MDLZ present 1, 2 and 4 runs; BAC 4 and 1 runs.
_SCHEDULE = (
    ("s1", (MDLZ,)),
    ("s2", (BAC,)),
    ("s3", (MDLZ, BAC)),
    ("s4", (MDLZ, BAC)),
    ("s5", (BAC,)),
    ("s6", (MDLZ,)),
    ("s7", (MDLZ, BAC)),
    ("s8", (MDLZ,)),
    ("s9", (MDLZ,)),
    ("s10", ()),
)


def test_a_live_divergence_always_has_exactly_one_open_flag() -> None:
    """EXEC-OBS-07: one open Flag per live divergence, none for an absent one."""
    graph = InMemoryGraphStore()
    streak: dict[str, int] = {}
    for key, live in _SCHEDULE:
        run(graph, key, *live)

        tickers = {divergence.ticker for divergence in live}
        streak = {t: streak.get(t, 0) + 1 for t in tickers}
        expected = sorted(
            (t, "warn" if n == 1 else "critical") for t, n in streak.items()
        )
        assert open_summary(graph) == expected, key


def test_nothing_already_written_is_rewritten() -> None:
    """EXEC-STA-03 / EXEC-OBS-07: every earlier Flag and resolution keeps its props."""
    graph = InMemoryGraphStore()
    for key, live in _SCHEDULE:
        before = {
            (label, node.key): dict(node.props)
            for label in ("Flag", "FlagResolution")
            for node in graph.list_nodes(label)
        }

        run(graph, key, *live)

        for (label, node_key), props in before.items():
            node = graph.get_node(label, node_key)
            assert node is not None, (key, node_key)
            assert dict(node.props) == props, (key, node_key)
