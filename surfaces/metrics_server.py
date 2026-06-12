"""Metrics HTTP server — exposes /metrics for Prometheus scraping.

Agent: surfaces
Role: serve a PrometheusMetrics registry over HTTP on a configurable port.
External I/O: HTTP server on 0.0.0.0:PORT.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from prometheus_client import CollectorRegistry


def make_metrics_app(registry: CollectorRegistry) -> Callable[..., Any]:
    """Return a WSGI app that serves the registry in Prometheus text format."""
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    def _app(
        environ: dict[str, Any], start_response: Callable[..., Any]
    ) -> list[bytes]:
        del environ
        output = generate_latest(registry)
        start_response("200 OK", [("Content-Type", CONTENT_TYPE_LATEST)])
        return [output]

    return _app


def start_metrics_server(
    registry: CollectorRegistry, port: int = 8000
) -> threading.Thread:  # pragma: no cover
    """Start a daemon thread serving /metrics on PORT. Returns the thread."""
    from wsgiref.simple_server import make_server

    server = make_server("", port, make_metrics_app(registry))
    t = threading.Thread(
        target=server.serve_forever, daemon=True, name="metrics-server"
    )
    t.start()
    return t
