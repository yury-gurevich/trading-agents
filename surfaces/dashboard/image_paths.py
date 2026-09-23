"""Which repository paths can change what a fleet image runs.

Agent: surfaces
Role: classify changed paths so deploy currency flags only runtime differences.
External I/O: none.
"""

from __future__ import annotations

# The build-images.yml push filter, verbatim: a change anywhere else never
# rebuilds an image. A test pins this tuple to the workflow so they cannot drift.
IMAGE_BUILD_PATHS = (
    "agents/**",
    "kernel/**",
    "contracts/**",
    "orchestration/**",
    "scripts/dispatch_scheduled_run.py",
    "scripts/universe_sp100.txt",
    "pyproject.toml",
    "uv.lock",
    ".github/workflows/build-images.yml",
)
# Rebuilt on every version bump, yet the label alone changes nothing that runs.
VERSIONED_FILES = frozenset({"pyproject.toml", "uv.lock"})
_PROJECT_NAME_LINE = 'name = "trading-agents"'


def builds_image(path: str) -> bool:
    """Return whether a change at path triggers an image build."""
    return any(
        path.startswith(pattern.removesuffix("**"))
        if pattern.endswith("/**")
        else path == pattern
        for pattern in IMAGE_BUILD_PATHS
    )


def runs_in_image(path: str) -> bool:
    """Return whether path is image content that can execute.

    Markdown and test code are copied into images but never run there; a test
    pins that no image code names a markdown file, which keeps this rule true.
    """
    inert = path.endswith(".md") or "tests" in path.split("/")[:-1]
    return builds_image(path) and not inert


def without_project_version(text: str) -> str:
    """Drop the project's own version line; every other line is kept verbatim."""
    lines = text.splitlines()
    return "\n".join(
        line
        for index, line in enumerate(lines)
        if not (
            index
            and lines[index - 1] == _PROJECT_NAME_LINE
            and line.startswith("version = ")
        )
    )
