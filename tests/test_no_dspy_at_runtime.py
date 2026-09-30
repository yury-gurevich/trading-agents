"""No DSPy at run time: not imported, not loaded, not installed (S246 B8).

Agent: kernel
Role: prove the guided turn reproduces DSPy without it: no module under
      `kernel/`, `contracts/` or `agents/` imports `dspy`, the deliberator never
      loads it, and no image installs the `optimizer` extra (DL-184, DL-252).
External I/O: reads source files and Dockerfiles; runs one Python subprocess.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ("kernel", "contracts", "agents")
#: ADR-0010's offline port: it imports DSPy by name, only when `compile_prompt`
#: runs, and only `scripts/` calls it. Nothing on the deliberator's path does.
OFFLINE_PORT = "kernel/dspy_optimizer.py"


def _runtime_sources() -> list[Path]:
    return sorted(path for top in RUNTIME for path in (ROOT / top).rglob("*.py"))


def _imports_dspy(node: ast.AST) -> bool:
    if isinstance(node, ast.Import):
        return any(alias.name.split(".")[0] == "dspy" for alias in node.names)
    if isinstance(node, ast.ImportFrom):
        return (node.module or "").split(".")[0] == "dspy"
    return False


def _names_dspy_dynamically(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and any(
            isinstance(arg, ast.Constant) and arg.value == "dspy" for arg in node.args
        )
        and getattr(node.func, "attr", getattr(node.func, "id", ""))
        in {"import_module", "__import__"}
    )


def test_no_runtime_module_imports_dspy() -> None:
    """DLIB-OUT-06: the runtime renders and parses DSPy's format without DSPy."""
    static: list[str] = []
    dynamic: list[str] = []
    for path in _runtime_sources():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        name = path.relative_to(ROOT).as_posix()
        if any(_imports_dspy(node) for node in ast.walk(tree)):
            static.append(name)
        if any(_names_dspy_dynamically(node) for node in ast.walk(tree)):
            dynamic.append(name)

    assert static == []
    assert dynamic == [OFFLINE_PORT]


def test_a_guided_turn_never_loads_dspy() -> None:
    """DLIB-OUT-06: serving a guided turn loads neither DSPy nor the offline port."""
    result = subprocess.run(
        [sys.executable, "tests/dspy_free_probe.py"],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "reasoning=True loaded=[]"


def test_no_image_installs_the_optimizer_extra() -> None:
    """DL-184: `dspy` stays out of every image, so the accepted advisory holds."""
    dockerfiles = sorted(
        path for path in ROOT.rglob("Dockerfile*") if ".venv" not in path.parts
    )

    assert len(dockerfiles) >= 15
    offenders = [
        path.relative_to(ROOT).as_posix()
        for path in dockerfiles
        if "optimizer" in path.read_text(encoding="utf-8")
        or "dspy" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []
