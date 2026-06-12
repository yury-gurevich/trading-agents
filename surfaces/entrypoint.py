"""Container entrypoint — wires PrometheusMetrics into the bus and starts /metrics.

Agent: surfaces
Role: bootstrap PrometheusMetrics, expose /metrics HTTP server, build metered
      context, then delegate to the CLI main loop.
External I/O: HTTP server on METRICS_PORT (default 8000); Neo4j via paper_context.
"""

from __future__ import annotations

import os
import sys


def main() -> None:  # pragma: no cover
    """Start metrics server then hand off to the CLI with a metered context."""
    from kernel import PrometheusMetrics
    from surfaces.cli import main as cli_main
    from surfaces.context import paper_context
    from surfaces.metrics_server import start_metrics_server

    metrics = PrometheusMetrics()
    port = int(os.environ.get("METRICS_PORT", "8000"))
    start_metrics_server(metrics.registry, port)
    ctx = paper_context(metrics=metrics)
    sys.exit(cli_main(context=ctx))


if __name__ == "__main__":  # pragma: no cover
    main()
