"""Record one verified bounded fleet deployment on the live graph.

Agent: tooling
Role: provide the final append-only step of the deploy-fleet procedure.
External I/O: PostgreSQL from POSTGRES_DSN; GitHub API from GITHUB_TOKEN; stdout.
"""

from __future__ import annotations

import argparse
import os
import sys


def main() -> None:
    """Validate explicit deployment evidence and append its DeployRecord."""
    parser = argparse.ArgumentParser(description="record a verified fleet deployment")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--git-sha", required=True)
    parser.add_argument("--actor", required=True)
    args = parser.parse_args()

    from dotenv import load_dotenv

    load_dotenv()
    if not os.environ.get("POSTGRES_DSN"):
        parser.error("POSTGRES_DSN is required; refusing to record only in memory")

    from kernel.graph_env import build_graph_from_env
    from orchestration.deploy_record import record_deploy
    from orchestration.deploy_verify import DeployVerifyError, verify_build_sha

    graph = build_graph_from_env()
    if type(graph).__name__ == "InMemoryGraphStore":
        print(
            "REFUSING: resolved to the in-memory store, not the spine. "
            "POSTGRES_DSN is unset — run this from a directory with .env.",
            file=sys.stderr,
        )
        sys.exit(2)

    token = os.environ.get("GITHUB_TOKEN", "")
    checker = None
    if token:
        from surfaces.dashboard.github_builds import GitHubActionsReader
        from surfaces.dashboard.settings import DashboardSettings

        settings = DashboardSettings()
        checker = GitHubActionsReader(
            token=token,
            repository=settings.github_repository,
            workflow=settings.github_image_workflow,
            timeout=settings.github_timeout_seconds,
        )

    try:
        sha_verified = verify_build_sha(args.git_sha, checker)
    except DeployVerifyError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    node = record_deploy(
        graph,
        tag=args.tag,
        git_sha=args.git_sha,
        actor=args.actor,
        sha_verified=sha_verified,
    )
    if sha_verified:
        print(f"recorded DeployRecord {node.key} (sha verified against GitHub)")
    else:
        print(
            f"recorded DeployRecord {node.key} "
            "(sha_verified=False — GitHub was unreadable; record is asserted)"
        )


if __name__ == "__main__":
    main()
