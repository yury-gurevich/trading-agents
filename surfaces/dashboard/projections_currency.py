"""Deploy-currency judgement over graph facts, fleet tags, and main builds.

Agent: surfaces
Role: compare only recorded deploy evidence with observed read-only evidence.
External I/O: injected GitHubReader calls only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from surfaces.dashboard.github_builds import GitHubReadError

if TYPE_CHECKING:
    from kernel import GraphStore, Node
    from surfaces.dashboard.github_builds import GitHubReader

# Enough changed paths to show what moved; the count carries the full size.
_CHANGE_SAMPLE = 20


def deploy_currency_projection(
    graph: GraphStore,
    containers: list[dict[str, Any]],
    github: GitHubReader | None,
    *,
    azure_verified: bool,
) -> dict[str, object]:
    """Judge current/behind/unverified from explicit comparisons.

    A newer main build alone is not "behind": version bumps and law or test
    edits rebuild images without changing what runs, so the two commits'
    runtime files are compared before the fleet is called behind.
    """
    tags = sorted({str(row["image_tag"]) for row in containers if row.get("image")})
    record = _latest_record(graph)
    evidence: dict[str, object] = {
        "running_tags": tags,
        "deploy_record": _record_evidence(record),
        "latest_main_build": None,
        "fleet_matches_record": None,
        "main_matches_record": None,
        "runtime_changes": None,
        "runtime_change_count": None,
    }
    if not azure_verified or not tags:
        return _result(
            "unverified", "Fleet image tags could not be verified.", evidence
        )
    if record is None:
        return _result(
            "unverified", "No verified deployment record is available.", evidence
        )
    if github is None:
        return _result(
            "unverified", "GitHub build evidence is not configured.", evidence
        )
    try:
        build = github.latest_main_image_build()
    except GitHubReadError as exc:
        return _result("unverified", str(exc), evidence)
    evidence["latest_main_build"] = {
        "git_sha": build.git_sha,
        "run_id": build.run_id,
        "url": build.url,
    }
    tag = str(record.props["tag"])
    sha = str(record.props["git_sha"])
    evidence["fleet_matches_record"] = tags == [tag]
    evidence["main_matches_record"] = sha == build.git_sha
    if not evidence["fleet_matches_record"]:
        return _result("behind", "Fleet images are behind or mixed.", evidence)
    if evidence["main_matches_record"]:
        return _result(
            "current", "Fleet matches the newest main image build.", evidence
        )
    return _judge_rebuilt_main(github, sha, build.git_sha, evidence)


def _judge_rebuilt_main(
    github: GitHubReader, deployed_sha: str, main_sha: str, evidence: dict[str, object]
) -> dict[str, object]:
    """Main was rebuilt after the deploy: behind only if code the fleet runs moved."""
    try:
        changed = github.runtime_changes(deployed_sha, main_sha)
    except GitHubReadError as exc:
        return _result(
            "unverified",
            f"Main was rebuilt after the deploy; what changed could not be read: {exc}",
            evidence,
        )
    evidence["runtime_changes"] = list(changed[:_CHANGE_SAMPLE])
    evidence["runtime_change_count"] = len(changed)
    if changed:
        return _result(
            "behind",
            f"Main changed {len(changed)} file(s) the fleet runs since the deploy.",
            evidence,
        )
    return _result(
        "current",
        "Fleet runs the code on main; later commits changed only documents, "
        "tests or the version number.",
        evidence,
    )


def _latest_record(graph: GraphStore) -> Node | None:
    rows = graph.list_nodes("DeployRecord")
    return max(
        rows, key=lambda row: str(row.props.get("deployed_at", "")), default=None
    )


def _record_evidence(record: Node | None) -> dict[str, object] | None:
    if record is None:
        return None
    return {
        "key": record.key,
        "tag": record.props.get("tag"),
        "git_sha": record.props.get("git_sha"),
        "deployed_at": record.props.get("deployed_at"),
        "actor": record.props.get("actor"),
    }


def _result(
    status: str, message: str, evidence: dict[str, object]
) -> dict[str, object]:
    return {"status": status, "message": message, "evidence": evidence}
