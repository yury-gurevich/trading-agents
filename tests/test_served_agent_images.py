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


def test_every_agent_dockerfile_is_in_the_build_matrix() -> None:
    """DL-46 family: a Dockerfile nothing builds is an image that never ships.

    S153 added `agents/deliberator/Dockerfile` and taught `deploy-agents.ps1` to
    expect 15 images, but never added the deliberator to `build-images.yml`. The
    image was therefore never built, and the gap surfaced only when a deploy was
    already underway. Nothing tied "a Dockerfile exists" to "it gets built" --
    this test is that tie.
    """
    workflow = Path(".github/workflows/build-images.yml").read_text(encoding="utf-8")
    missing = [
        dockerfile.parent.name
        for dockerfile in sorted(Path("agents").glob("*/Dockerfile"))
        if f"dockerfile: {dockerfile.as_posix()}" not in workflow
    ]

    assert not missing, f"agent Dockerfiles absent from the build matrix: {missing}"


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
