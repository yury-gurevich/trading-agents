"""Read-only entrypoint roster proof for S272.

Agent: kernel
Role: prove every agent hands its main loop the graph and its identity.
External I/O: reads source files, including the three frozen entrypoints.
"""

from __future__ import annotations

import ast
from pathlib import Path


def test_a15_every_entrypoint_passes_graph_and_agent() -> None:
    """MST-TRG-03: all 13 agent entrypoints wire both resources into 14 loops."""
    root = Path(__file__).resolve().parents[1]
    files = sorted(
        path
        for path in (root / "agents").glob("*/entrypoint.py")
        if path.parent.name != "master"
    )
    assert len(files) == 13
    calls: list[tuple[Path, ast.Call]] = []
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in ("work_loop", "serve_loop")
            ):
                calls.append((path, node))
    assert len(calls) == 14
    for path, call in calls:
        keywords = {keyword.arg for keyword in call.keywords}
        assert {"graph", "agent"} <= keywords, str(path)
