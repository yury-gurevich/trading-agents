"""Read-only recommendation shadow-book scorecard CLI.

Agent: tooling
Role: load the live graph and print forward returns by action, confidence, and
      recorded PM disposition without persisting derived data.
External I/O: PostgreSQL (POSTGRES_DSN from .env); stdout.
"""

from __future__ import annotations

import os
import sys


def main() -> None:
    """Load the configured Postgres graph and print the shadow-book scorecard."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    from dotenv import load_dotenv

    load_dotenv()
    if not os.environ.get("POSTGRES_DSN", "").strip():
        raise RuntimeError(
            "POSTGRES_DSN is not set; run from the repository root with its .env"
        )

    from kernel.graph_env import build_graph_from_env
    from orchestration.shadow_book import derive_shadow_book
    from orchestration.shadow_book_render import render_scorecard
    from orchestration.shadow_book_settings import ShadowBookSettings

    settings = ShadowBookSettings()
    graph = build_graph_from_env()
    outcomes = derive_shadow_book(graph, settings.horizons)
    print(
        render_scorecard(
            outcomes,
            settings.horizons,
            confidence_bucket_width=settings.confidence_bucket_width,
        )
    )


if __name__ == "__main__":
    main()
