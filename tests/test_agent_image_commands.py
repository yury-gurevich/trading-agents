"""Regression tests for agent image entrypoint commands.

Agent: tooling
Role: keep branch-built Container Apps images pointed at importable Python modules.
External I/O: reads local Dockerfiles only.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

AGENT_DOCKERFILES = tuple(Path("agents").glob("*/Dockerfile"))


def _cmd_module(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("CMD "):
            cmd = json.loads(line.removeprefix("CMD ").strip())
            module_flag = cmd.index("-m")
            return str(cmd[module_flag + 1])
    raise AssertionError(f"{path} has no CMD")


def test_agent_dockerfile_cmd_modules_are_importable() -> None:
    modules = [_cmd_module(path) for path in AGENT_DOCKERFILES]

    assert modules
    assert all(importlib.util.find_spec(module) is not None for module in modules)
