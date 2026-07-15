"""Dashboard composition root — `uv run python -m surfaces.dashboard`.

Agent: surfaces
Role: build the graph from the environment and serve the dashboard locally.
External I/O: HTTP server on 127.0.0.1:PORT; graph backend per POSTGRES_DSN.
"""

from __future__ import annotations

import os
import sys
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, make_server


class _ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    """Thread-per-request server: one slow Azure/graph read must not wedge the UI."""

    daemon_threads = True
    # A taken port must fail loudly. With the reuse default, a second instance
    # silently double-binds on Windows and a stale process keeps answering the
    # browser (fixpack item 5, 2026-07-14).
    allow_reuse_address = False


def main() -> None:
    """Serve the dashboard on DASHBOARD_PORT (default 8300)."""
    from dotenv import load_dotenv

    from kernel.graph_env import build_graph_from_env
    from surfaces.dashboard.app import build_app
    from surfaces.dashboard.azure_rest import build_azure_reader
    from surfaces.dashboard.chat_binding import bind_dashboard_chat
    from surfaces.dashboard.github_builds import build_github_reader
    from surfaces.dashboard.settings import DashboardSettings

    load_dotenv()
    port = int(os.environ.get("DASHBOARD_PORT", "8300"))
    settings = DashboardSettings()
    graph = build_graph_from_env()
    chat = bind_dashboard_chat(graph)
    app = build_app(
        graph,
        build_azure_reader(settings),
        settings,
        chat,
        github=build_github_reader(settings),
    )
    try:
        server = make_server("127.0.0.1", port, app, server_class=_ThreadingWSGIServer)
    except OSError:
        sys.stderr.write(
            f"dashboard: port {port} is already in use — another dashboard "
            "instance is running; stop it first (or set DASHBOARD_PORT).\n"
        )
        raise SystemExit(1) from None
    chat_state = "operator chat connected" if chat else "operator chat not connected"
    sys.stderr.write(f"dashboard: http://127.0.0.1:{port}/  ({chat_state})\n")
    server.serve_forever()


if __name__ == "__main__":
    main()
