"""Append-only DeployRecord tests.

Agent: orchestration
Role: prove verified deployment facts append and exact replays dedupe.
External I/O: none; the graph is in memory.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from kernel import InMemoryGraphStore
from orchestration.deploy_record import record_deploy


def test_record_deploy_appends_and_exact_replay_dedupes() -> None:
    graph = InMemoryGraphStore()
    when = datetime(2026, 7, 9, 2, 3, tzinfo=UTC)
    first = record_deploy(
        graph, tag=":s121", git_sha="ABC123", actor="operator", deployed_at=when
    )
    replay = record_deploy(
        graph, tag="s121", git_sha="abc123", actor="operator", deployed_at=when
    )
    later = record_deploy(
        graph,
        tag="s126",
        git_sha="def456",
        actor="operator",
        deployed_at=datetime(2026, 7, 14, tzinfo=UTC),
    )

    assert first == replay
    assert later.key != first.key
    assert len(graph.list_nodes("DeployRecord")) == 2
    assert first.props == {
        "tag": "s121",
        "git_sha": "abc123",
        "deployed_at": "2026-07-09T02:03:00+00:00",
        "actor": "operator",
    }


@pytest.mark.parametrize(
    ("tag", "sha", "actor"), [("", "sha", "a"), ("tag", "", "a"), ("tag", "sha", "")]
)
def test_record_deploy_requires_complete_evidence(
    tag: str, sha: str, actor: str
) -> None:
    with pytest.raises(ValueError, match="required"):
        record_deploy(InMemoryGraphStore(), tag=tag, git_sha=sha, actor=actor)


def test_record_deploy_requires_timezone() -> None:
    with pytest.raises(ValueError, match="timezone"):
        record_deploy(
            InMemoryGraphStore(),
            tag="s126",
            git_sha="abc",
            actor="operator",
            deployed_at=datetime(2026, 7, 14, tzinfo=UTC).replace(tzinfo=None),
        )
