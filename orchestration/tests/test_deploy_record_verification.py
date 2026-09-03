"""Verified DeployRecord tests.

Agent: orchestration
Role: prove deploy records verify tag-specific image-build evidence.
External I/O: none; the graph and build reader are fakes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import NoReturn

import pytest

from kernel import InMemoryGraphStore
from orchestration.deploy_record import (
    BuildEvidence,
    BuildReader,
    DeployRecordVerificationError,
    record_verified_deploy,
)

_REAL_S179_SHA = "4c8eeb0505bc65c081be3d1fe71049f7d88e0e43"  # pragma: allowlist secret
_WRONG_S179_SHA = "8fbf3a41339d0a31aa9a057952fe5e6401280ac1"  # pragma: allowlist secret
_S194_SHA = "e0a144fc08b1d5fd8bc219f4ed48fef74fa8d120"  # pragma: allowlist secret
_S194_NEWER_SHA = "75027b62a8d45a67be0b8a3aaf66108f22ffc228"  # pragma: allowlist secret


@dataclass(frozen=True)
class _BuildEvidence:
    git_sha: str


class _BuildReader(BuildReader):
    def __init__(self, builds_by_tag: dict[str, tuple[str, ...]]) -> None:
        self._builds_by_tag = builds_by_tag
        self.calls: list[tuple[str, str | None]] = []

    def image_builds_for_tag(
        self, tag: str, git_sha: str | None = None
    ) -> tuple[BuildEvidence, ...]:
        self.calls.append((tag, git_sha))
        shas = self._builds_by_tag.get(tag, ())
        if git_sha is not None:
            shas = tuple(sha for sha in shas if sha.strip().lower() == git_sha)
        return tuple(_BuildEvidence(sha) for sha in shas)


class _UnreadableBuildReader(BuildReader):
    def image_builds_for_tag(self, tag: str, git_sha: str | None = None) -> NoReturn:
        raise RuntimeError("GitHub build read failed (test)")


class _MissingThenUnreadableBuildReader(BuildReader):
    def image_builds_for_tag(
        self, tag: str, git_sha: str | None = None
    ) -> tuple[BuildEvidence, ...]:
        if git_sha is not None:
            return ()
        raise RuntimeError("GitHub build read failed (test)")


def test_record_verified_deploy_refuses_mismatched_built_commit() -> None:
    graph = InMemoryGraphStore()

    with pytest.raises(DeployRecordVerificationError) as caught:
        record_verified_deploy(
            graph,
            tag="s179",
            git_sha=_WRONG_S179_SHA,
            actor="operator",
            build_reader=_BuildReader({"s179": (_REAL_S179_SHA,)}),
            deployed_at=datetime(2026, 8, 18, 7, 56, 29, tzinfo=UTC),
        )

    message = str(caught.value)
    assert _WRONG_S179_SHA in message
    assert _REAL_S179_SHA in message
    assert not graph.list_nodes("DeployRecord")


def test_record_verified_deploy_accepts_the_real_s179_built_commit() -> None:
    graph = InMemoryGraphStore()

    node = record_verified_deploy(
        graph,
        tag=":s179",
        git_sha=_REAL_S179_SHA,
        actor="operator",
        build_reader=_BuildReader({"s179": (_REAL_S179_SHA,)}),
        deployed_at=datetime(2026, 8, 18, 7, 56, 29, tzinfo=UTC),
    )

    assert node.props["tag"] == "s179"
    assert node.props["git_sha"] == _REAL_S179_SHA
    assert len(graph.list_nodes("DeployRecord")) == 1


def test_record_verified_deploy_accepts_s194_when_newer_build_exists() -> None:
    graph = InMemoryGraphStore()
    reader = _BuildReader({"s194": (_S194_NEWER_SHA, _S194_SHA)})

    node = record_verified_deploy(
        graph,
        tag="s194",
        git_sha=_S194_SHA,
        actor="operator",
        build_reader=reader,
        deployed_at=datetime(2026, 8, 18, 7, 56, 29, tzinfo=UTC),
    )

    assert node.props["tag"] == "s194"
    assert node.props["git_sha"] == _S194_SHA
    assert len(graph.list_nodes("DeployRecord")) == 1
    assert reader.calls == [("s194", _S194_SHA)]


@pytest.mark.parametrize("build_reader", [None, _UnreadableBuildReader()])
def test_record_verified_deploy_refuses_unreadable_build_evidence(
    build_reader: BuildReader | None,
) -> None:
    graph = InMemoryGraphStore()

    with pytest.raises(DeployRecordVerificationError, match="build evidence"):
        record_verified_deploy(
            graph,
            tag="s179",
            git_sha=_REAL_S179_SHA,
            actor="operator",
            build_reader=build_reader,
            deployed_at=datetime(2026, 8, 18, 7, 56, 29, tzinfo=UTC),
        )

    assert not graph.list_nodes("DeployRecord")


def test_record_verified_deploy_refuses_empty_build_evidence() -> None:
    graph = InMemoryGraphStore()

    with pytest.raises(DeployRecordVerificationError, match="build evidence"):
        record_verified_deploy(
            graph,
            tag="s179",
            git_sha=_REAL_S179_SHA,
            actor="operator",
            build_reader=_BuildReader({"s179": ()}),
            deployed_at=datetime(2026, 8, 18, 7, 56, 29, tzinfo=UTC),
        )

    assert not graph.list_nodes("DeployRecord")


def test_record_verified_deploy_refuses_missing_then_unreadable_evidence() -> None:
    graph = InMemoryGraphStore()

    with pytest.raises(DeployRecordVerificationError, match="build evidence"):
        record_verified_deploy(
            graph,
            tag="s179",
            git_sha=_REAL_S179_SHA,
            actor="operator",
            build_reader=_MissingThenUnreadableBuildReader(),
            deployed_at=datetime(2026, 8, 18, 7, 56, 29, tzinfo=UTC),
        )

    assert not graph.list_nodes("DeployRecord")
