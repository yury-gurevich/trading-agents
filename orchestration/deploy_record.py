"""Append-only fleet deployment facts used by the currency judgement.

Agent: orchestration
Role: record one completed bounded fleet deployment after verification.
External I/O: writes only the injected GraphStore.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from kernel import GraphStore, Node


class DeployRecordVerificationError(ValueError):
    """A deployment record could not be verified against build evidence."""


class BuildEvidence(Protocol):
    """Successful image-build evidence carrying the workflow head SHA."""

    @property
    def git_sha(self) -> str:
        """Return the workflow head SHA."""
        ...  # pragma: no cover - protocol declaration only.


class BuildReader(Protocol):
    """Read-only source for the image build a deploy record claims."""

    def image_builds_for_tag(
        self, tag: str, git_sha: str | None = None
    ) -> tuple[BuildEvidence, ...]:
        """Return successful image builds that produced tag."""
        ...  # pragma: no cover - protocol declaration only.


def record_deploy(
    graph: GraphStore,
    *,
    tag: str,
    git_sha: str,
    actor: str,
    deployed_at: datetime | None = None,
) -> Node:
    """Append one verified deployment fact without changing earlier records."""
    clean_tag = tag.removeprefix(":").strip()
    clean_sha = git_sha.strip().lower()
    clean_actor = actor.strip()
    if not clean_tag or not clean_sha or not clean_actor:
        raise ValueError("tag, git sha, and actor are required")
    when = deployed_at or datetime.now(tz=UTC)
    if when.tzinfo is None:
        raise ValueError("deployed_at must include a timezone")
    timestamp = when.astimezone(UTC).isoformat()
    key = f"deploy:{timestamp}:{clean_tag}:{clean_sha}"
    return graph.merge_node(
        "DeployRecord",
        key,
        {
            "tag": clean_tag,
            "git_sha": clean_sha,
            "deployed_at": timestamp,
            "actor": clean_actor,
        },
    )


def record_verified_deploy(
    graph: GraphStore,
    *,
    tag: str,
    git_sha: str,
    actor: str,
    build_reader: BuildReader | None,
    deployed_at: datetime | None = None,
) -> Node:
    """Verify the claimed SHA against image-build evidence, then append."""
    clean_tag = tag.removeprefix(":").strip()
    clean_sha = git_sha.strip().lower()
    expected_shas = _built_git_shas_for_tag(build_reader, clean_tag, clean_sha)
    if clean_sha not in expected_shas:
        expected = ", ".join(expected_shas) if expected_shas else f"tag {clean_tag}"
        raise DeployRecordVerificationError(
            "deploy git sha does not match a successful image build for tag "
            f"{clean_tag}: given {clean_sha}; expected {expected}"
        )
    return record_deploy(
        graph, tag=tag, git_sha=git_sha, actor=actor, deployed_at=deployed_at
    )


def _built_git_shas_for_tag(
    build_reader: BuildReader | None, clean_tag: str, clean_sha: str
) -> tuple[str, ...]:
    if build_reader is None:
        raise DeployRecordVerificationError(
            "GitHub build evidence is required before recording a deploy"
        )
    try:
        builds = build_reader.image_builds_for_tag(clean_tag, clean_sha)
    except RuntimeError as exc:
        raise DeployRecordVerificationError(
            f"GitHub build evidence is required before recording a deploy: {exc}"
        ) from None
    expected_shas = _build_git_shas(builds)
    if expected_shas:
        return expected_shas
    try:
        expected_shas = _build_git_shas(build_reader.image_builds_for_tag(clean_tag))
    except RuntimeError:
        expected_shas = ()
    if not expected_shas:
        raise DeployRecordVerificationError(
            "GitHub build evidence is required before recording a deploy"
        )
    return expected_shas


def _build_git_shas(builds: tuple[BuildEvidence, ...]) -> tuple[str, ...]:
    return tuple(
        build.git_sha.strip().lower() for build in builds if build.git_sha.strip()
    )
