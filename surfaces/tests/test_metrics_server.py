"""Metrics HTTP server tests.

Agent: surfaces
Role: verify the WSGI app serves prometheus text from the given registry.
External I/O: none (no real HTTP server started).
"""

from __future__ import annotations

from typing import Any

from prometheus_client import CollectorRegistry, Counter

from surfaces.metrics_server import make_metrics_app


def test_metrics_app_returns_200_with_prometheus_text() -> None:
    registry = CollectorRegistry()
    Counter("test_total", "A test counter", registry=registry).inc(3)
    app = make_metrics_app(registry)

    captured: dict[str, Any] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        captured["status"] = status
        captured["content_type"] = dict(headers).get("Content-Type", "")

    body = b"".join(app({}, start_response)).decode("utf-8")

    assert captured["status"] == "200 OK"
    assert "text/plain" in captured["content_type"]
    assert "test_total 3.0" in body


def test_metrics_app_returns_empty_body_for_empty_registry() -> None:
    registry = CollectorRegistry()
    app = make_metrics_app(registry)

    status_box: list[str] = []
    app({}, lambda s, _h: status_box.append(s))

    assert status_box[0] == "200 OK"
