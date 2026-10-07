"""Image installation and accepted-advisory premises (S254 B4/B5).

Agent: tooling
Role: keep the optimizer in one image and diskcache outside every installation.
External I/O: reads tracked Dockerfiles; evaluates synthetic audit findings.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from scripts.check_dependency_audit import tracked_dockerfiles
from scripts.dependency_audit_rules import evaluate, extras_installed_by, sync_commands

ROOT = Path(__file__).resolve().parents[1]
REPORT = {
    "dependencies": [
        {
            "name": "diskcache",
            "version": "5.6.3",
            "vulns": [{"id": "PYSEC-2026-2447", "aliases": [], "fix_versions": []}],
        }
    ]
}


def test_only_deliberator_installs_optimizer_with_exact_exclusions() -> None:
    """DLIB-DEP-03: ADR-0032 changes only the deliberator image's dependencies (B4)."""
    dockerfiles = tracked_dockerfiles(ROOT)
    assert len(dockerfiles) == 15
    assert extras_installed_by(dockerfiles)["optimizer"] == [
        "agents/deliberator/Dockerfile"
    ]
    (command,) = sync_commands(dockerfiles["agents/deliberator/Dockerfile"])
    assert set(re.findall(r"--no-install-package[=\s]+([\w.-]+)", command)) == {
        "diskcache",
        "litellm",
    }
    # DSPy is in the dev group too (CI runs it), so no image may install that group.
    assert all(
        "--no-dev" in command.split()
        for text in dockerfiles.values()
        for command in sync_commands(text)
    )


@pytest.mark.parametrize(
    "command",
    [
        "RUN uv sync --extra optimizer --no-install-package diskcache\n",
        "RUN uv sync --extra=optimizer \\\n      --no-install-package=diskcache\n",
    ],
)
def test_optimizer_installation_with_diskcache_excluded_preserves_acceptance(
    command: str,
) -> None:
    """DLIB-DEP-03: DL-184 / DL-199 acceptance survives exclusion by name (B5)."""
    errors, notes = evaluate(
        REPORT,
        {"peer/Dockerfile": command, "other/Dockerfile": "RUN uv sync --no-dev"},
    )
    assert errors == []
    assert len(notes) == 1
    assert "installed by 1 of 2 Dockerfiles" in notes[0]
    assert "each installing command excludes diskcache by name" in notes[0]
    assert "the dev group carries it too" in notes[0]


@pytest.mark.parametrize(
    "command",
    [
        "RUN uv sync --extra optimizer\n",
        "RUN uv sync --extra optimizer # --no-install-package diskcache\n",
        "RUN uv sync --extra optimizer\nRUN uv sync --no-install-package diskcache\n",
        "RUN uv sync --extra optimizer; uv sync --no-install-package diskcache\n",
        "RUN uv sync --extra optimizer --no-install-package diskcache\n"
        + "RUN uv sync --extra optimizer\n",
        "RUN uv sync --extra optimizer --no-install-package litellm\n",
        # The dev group carries DSPy as well: a sync that installs it owes the same.
        "RUN uv sync --frozen --extra runtime\n",
        "RUN uv sync --extra runtime --no-install-package litellm\n",
        "RUN uv sync --extra runtime --no-dev\nRUN uv sync --extra runtime\n",
        "RUN uv sync --extra runtime # --no-dev\n",
    ],
)
def test_any_optimizer_command_without_diskcache_exclusion_voids_acceptance(
    command: str,
) -> None:
    """DLIB-DEP-03: exclusion in a comment or a different command cannot count (B5)."""
    errors, notes = evaluate(REPORT, {"unsafe/Dockerfile": command})
    assert notes == []
    assert len(errors) == 1
    assert "unsafe/Dockerfile" in errors[0]
    assert "reaches a deployed container" in errors[0]


def test_each_installer_must_exclude_the_package_and_comments_install_nothing() -> None:
    """DLIB-DEP-03: the premise is universal over actual installing commands (B5)."""
    safe = "RUN uv sync --extra optimizer --no-install-package diskcache\n"
    unsafe = "RUN uv sync --extra optimizer\n"
    errors, notes = evaluate(
        REPORT, {"safe/Dockerfile": safe, "unsafe/Dockerfile": unsafe}
    )
    assert notes == []
    assert len(errors) == 1
    assert "unsafe/Dockerfile" in errors[0]
    assert "safe/Dockerfile," not in errors[0]
    assert extras_installed_by({"comment": "# RUN uv sync --extra optimizer\n"}) == {}
