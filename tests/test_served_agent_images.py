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


def test_every_agent_image_follows_the_s130_hardened_pattern() -> None:
    """R005/S130: every agent image is two-stage DHI with no runtime uv or shell.

    S153's deliberator Dockerfile shipped on `python:3.13-slim` — the base S130
    deliberately migrated away from — single-stage, and running `uv run` at
    runtime, which cannot work because the DHI runtime image has no shell. It
    was never built, so nothing caught it. S130 bought a near-zero CVE baseline
    with an empty `.trivyignore`; one off-pattern image quietly gives that back.
    """
    offenders: dict[str, list[str]] = {}
    for dockerfile in sorted(Path("agents").glob("*/Dockerfile")):
        text = dockerfile.read_text(encoding="utf-8")
        problems = []
        if "dhi.io/python" not in text:
            problems.append("not on the DHI base")
        if "AS build" not in text:
            problems.append("not a two-stage build")
        if '"uv"' in text or 'CMD ["uv' in text:
            problems.append("runs uv at runtime (DHI runtime has no shell)")
        if problems:
            offenders[dockerfile.parent.name] = problems

    assert not offenders, f"agent images off the S130 pattern: {offenders}"


def test_deliberator_image_installs_the_llm_extra() -> None:
    """DL-80: the deliberator resolves the Anthropic SDK lazily, via importlib.

    A missing `anthropic` therefore fails at the first debate turn, not at
    import — the agent would deploy, activate, poll, and produce no
    `DeliberationRun`, which is indistinguishable from the stranded harness this
    agent was built to replace. Pinned because no other agent image needs it and
    the omission is invisible until a live debate runs.
    """
    text = Path("agents/deliberator/Dockerfile").read_text(encoding="utf-8")

    assert "--extra llm" in text


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
