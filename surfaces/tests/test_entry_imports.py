"""Each surface entry module imports on its own, in a fresh interpreter.

Agent: surfaces
Role: catch import cycles the test session hides by importing modules in a lucky order.
External I/O: runs `python -c "import ..."` subprocesses.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "module",
    ["surfaces.mcp_tools", "surfaces.mcp_server", "surfaces.cli", "surfaces.dashboard"],
)
def test_entry_module_imports_first(module: str) -> None:
    """SRF-TRG-02 / SRF-DEP-02: the MCP server and CLI load when imported first.

    `surfaces.performance_tool` once imported `surfaces.dashboard.projections`, whose
    package `__init__` pulls in the chat, which imports `mcp_tools` half-loaded: the
    MCP server could not start, while every in-process test passed (DL-225).
    """
    done = subprocess.run(  # noqa: S603 - fixed interpreter and module list
        [sys.executable, "-c", f"import {module}"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert done.returncode == 0, done.stderr[-600:]
