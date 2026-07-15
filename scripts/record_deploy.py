"""Record one verified bounded fleet deployment on the live graph.

Agent: tooling
Role: provide the final append-only step of the deploy-fleet procedure.
External I/O: PostgreSQL from POSTGRES_DSN; stdout.
"""

from __future__ import annotations

import argparse
import os


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

    node = record_deploy(
        build_graph_from_env(), tag=args.tag, git_sha=args.git_sha, actor=args.actor
    )
    print(f"recorded DeployRecord {node.key}")


if __name__ == "__main__":
    main()
