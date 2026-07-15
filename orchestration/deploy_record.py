"""Append-only fleet deployment facts used by the currency judgement.

Agent: orchestration
Role: record one completed bounded fleet deployment after verification.
External I/O: writes only the injected GraphStore.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import GraphStore, Node


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
