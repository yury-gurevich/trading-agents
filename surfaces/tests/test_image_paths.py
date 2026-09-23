"""Image-path classification tests, pinned to the build workflow and Dockerfiles.

Agent: surfaces
Role: prove which changed files can alter what a fleet image runs.
External I/O: reads committed workflow, Dockerfile, and source files only.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from surfaces.dashboard.image_paths import (
    IMAGE_BUILD_PATHS,
    builds_image,
    runs_in_image,
    without_project_version,
)

_ROOT = Path(__file__).parents[2]
_IMAGE_CODE_ROOTS = ("kernel", "contracts", "agents", "orchestration")


@pytest.mark.parametrize(
    ("path", "builds", "runs"),
    [
        ("kernel/graph.py", True, True),
        ("agents/analyst/domain/rules.py", True, True),
        ("agents/analyst/data/lexicon.json", True, True),
        ("scripts/dispatch_scheduled_run.py", True, True),
        ("uv.lock", True, True),
        (".github/workflows/build-images.yml", True, True),
        ("kernel/tests.py", True, True),
        ("agents/analyst/laws/laws.md", True, False),
        ("agents/analyst/tests/test_rules.py", True, False),
        ("kernel/tests/test_graph.py", True, False),
        ("surfaces/dashboard/app.py", False, False),
        ("scripts/check_module_size.py", False, False),
        ("docs/STATE.md", False, False),
        ("pyproject.toml.bak", False, False),
        ("agentsx/rules.py", False, False),
    ],
)
def test_changed_path_classification(path: str, builds: bool, runs: bool) -> None:
    assert builds_image(path) is builds
    assert runs_in_image(path) is runs


def test_image_paths_are_the_build_workflow_trigger_verbatim() -> None:
    """A path the workflow rebuilds on but currency ignored would hide drift."""
    workflow = _ROOT / ".github" / "workflows" / "build-images.yml"
    lines = workflow.read_text(encoding="utf-8").splitlines()
    start = lines.index("    paths:") + 1
    trigger: list[str] = []
    for line in lines[start:]:
        if not line.startswith("      - "):
            break
        trigger.append(line.removeprefix("      - ").strip('"'))

    assert tuple(trigger) == IMAGE_BUILD_PATHS


def test_every_dockerfile_copy_source_triggers_an_image_build() -> None:
    dockerfiles = [
        *_ROOT.glob("agents/*/Dockerfile"),
        _ROOT / "orchestration/Dockerfile",
    ]
    sources = {
        source
        for dockerfile in dockerfiles
        for line in dockerfile.read_text(encoding="utf-8").splitlines()
        if line.startswith(("COPY ", "ADD ")) and "--from=" not in line
        for source in line.split()[1:-1]
    }

    assert len(dockerfiles) > 10
    assert {"pyproject.toml", "kernel/", "scripts/universe_sp100.txt"} <= sources
    assert sorted(source for source in sources if not builds_image(source)) == []


def test_no_image_code_names_a_markdown_file() -> None:
    """Markdown counts as inert for currency only while no image code reads it."""
    offenders = [
        f"{path.relative_to(_ROOT)}:{line}"
        for path in _image_code()
        for line, text in _code_strings(path)
        if ".md" in text
    ]

    assert offenders == []


def test_only_the_projects_own_version_line_is_dropped() -> None:
    text = (
        '[project]\nname = "trading-agents"\nversion = "0.109.02"\n'
        '[[package]]\nname = "httpx"\nversion = "0.28.1"\n'
    )

    assert without_project_version(text) == (
        '[project]\nname = "trading-agents"\n'
        '[[package]]\nname = "httpx"\nversion = "0.28.1"'
    )


def _image_code() -> list[Path]:
    files = [
        path
        for root in _IMAGE_CODE_ROOTS
        for path in (_ROOT / root).rglob("*.py")
        if "tests" not in path.relative_to(_ROOT).parts
    ]
    return [*files, _ROOT / "scripts" / "dispatch_scheduled_run.py"]


def _code_strings(path: Path) -> list[tuple[int, str]]:
    """Every string literal in a module except docstrings, which never execute."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        )
        and node.body
        and isinstance(node.body[0], ast.Expr)
    }
    return [
        (node.lineno, node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
    ]
