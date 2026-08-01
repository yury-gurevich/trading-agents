"""Regression tests for served-agent image/runtime requirements.

Agent: kernel
Role: keep Service Bus served containers installable in the distributed fleet.
External I/O: reads local Dockerfiles only.
"""

from __future__ import annotations

from pathlib import Path

from kernel.serve_transport import (
    SERVED_AGENT_TYPES,
    image_dir_for_served_agent,
    request_topic,
)


def test_served_agent_images_install_azure_extra() -> None:
    for agent_type in SERVED_AGENT_TYPES:
        directory = image_dir_for_served_agent(agent_type)
        text = Path(f"agents/{directory}/Dockerfile").read_text(encoding="utf-8")
        assert "--extra azure" in text


def test_served_agent_request_routes_are_stable() -> None:
    assert [request_topic(agent) for agent in SERVED_AGENT_TYPES] == [
        "curator.requests",
        "deliberator-proponent.requests",
        "deliberator-opponent.requests",
        "forecaster.requests",
        "operator.requests",
        "researcher.requests",
        "supervisor.requests",
    ]
