"""Dashboard composition root — `uv run python -m surfaces.dashboard`.

Agent: surfaces
Role: build the graph from the environment and serve the dashboard locally.
External I/O: HTTP server on 127.0.0.1:PORT; graph backend per POSTGRES_DSN.
"""

from __future__ import annotations

import os
import sys
from wsgiref.simple_server import make_server


def main() -> None:
    """Serve the dashboard on DASHBOARD_PORT (default 8300)."""
    from dotenv import load_dotenv

    from kernel.graph_env import build_graph_from_env
    from surfaces.dashboard.app import build_app

    load_dotenv()
    port = int(os.environ.get("DASHBOARD_PORT", "8300"))
    server = make_server("127.0.0.1", port, build_app(build_graph_from_env()))
    sys.stderr.write(f"dashboard: http://127.0.0.1:{port}/  (read-only)\n")
    server.serve_forever()


if __name__ == "__main__":
    main()
