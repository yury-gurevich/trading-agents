"""The repo's own .importlinter catches a leak into or out of the substrate.

Agent: kernel
Role: prove the repo's `.importlinter` contracts, run against a fixture tree
      mirroring the 5 root packages and the 14 agents, reject a substrate/pack
      leak and an agent-to-agent leak, and pass a clean tree.
External I/O: writes a temporary package tree; spawns a subprocess.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

_ROOTS = ("kernel", "contracts", "agents", "orchestration", "surfaces")
_AGENTS = (
    "provider",
    "scanner",
    "analyst",
    "forecaster",
    "portfolio_manager",
    "execution",
    "monitor",
    "reporter",
    "researcher",
    "curator",
    "operator",
    "supervisor",
    "deliberator",
    "master",
)
_CONFIG_PATH = Path(".importlinter").resolve()


def _build_fixture(root: Path, *, plants: bool) -> None:
    for name in _ROOTS:
        (root / name).mkdir(parents=True, exist_ok=True)
        (root / name / "__init__.py").write_text("", encoding="utf-8")
    for agent in _AGENTS:
        agent_dir = root / "agents" / agent
        agent_dir.mkdir(parents=True, exist_ok=True)
        content = ""
        if plants and agent == "master":
            content = "import agents.scanner\nimport contracts\n"
        elif plants and agent == "deliberator":
            content = "import agents.execution\n"
        (agent_dir / "__init__.py").write_text(content, encoding="utf-8")


def _run_lint_imports(root: Path) -> subprocess.CompletedProcess[str]:
    exe = shutil.which("lint-imports")
    assert exe is not None, "lint-imports must be installed (import-linter)"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root)
    return subprocess.run(  # noqa: S603 - fixed lint-imports executable, no shell.
        [exe, "--config", str(_CONFIG_PATH), "--no-cache"],
        capture_output=True,
        text=True,
        cwd=root,
        env=env,
        check=False,
    )


def test_planted_leaks_are_caught_by_the_repos_own_config() -> None:
    """MST-NEV-05/MST-DEP-03/MST-DEP-05/DLIB-NEV-05: the wall catches each plant."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _build_fixture(root, plants=True)
        result = _run_lint_imports(root)
        assert result.returncode == 1, result.stdout
        assert "agents.master -> agents.scanner" in result.stdout
        assert "agents.master -> contracts" in result.stdout
        assert "agents.deliberator -> agents.execution" in result.stdout


def test_clean_fixture_tree_passes_the_repos_own_config() -> None:
    """The same fixture with no plants exits 0 — the contracts are not too strict."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _build_fixture(root, plants=False)
        result = _run_lint_imports(root)
        assert result.returncode == 0, result.stdout
