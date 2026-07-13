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


def main() -> None:
    """Serve the dashboard on DASHBOARD_PORT (default 8300)."""
    from dotenv import load_dotenv

    from kernel.graph_env import build_graph_from_env
    from surfaces.dashboard.app import build_app
    from surfaces.dashboard.azure_rest import build_azure_reader
    from surfaces.dashboard.chat_binding import bind_dashboard_chat
    from surfaces.dashboard.settings import DashboardSettings

    load_dotenv()
    port = int(os.environ.get("DASHBOARD_PORT", "8300"))
    settings = DashboardSettings()
    graph = build_graph_from_env()
    chat = bind_dashboard_chat(graph)
    app = build_app(graph, build_azure_reader(settings), settings, chat)
    server = make_server("127.0.0.1", port, app, server_class=_ThreadingWSGIServer)
    chat_state = "operator chat connected" if chat else "operator chat not connected"
    sys.stderr.write(f"dashboard: http://127.0.0.1:{port}/  ({chat_state})\n")
    server.serve_forever()


if __name__ == "__main__":
    main()
