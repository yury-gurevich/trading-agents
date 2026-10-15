"""A11-A12: hold production stop-width calls to the shared-read contract.

Agent: tests
Role: inspect resolver calls and prove the source guard sees both call forms.
External I/O: read Python source; the probe writes only under pytest tmp_path.
"""

from __future__ import annotations

import ast
from pathlib import Path


def resolver_calls(root: Path) -> list[tuple[Path, int, bool]]:
    """Return each production resolver call and whether it supplies fills=."""
    calls = []
    for path in sorted(root.rglob("*.py")):
        if "tests" in path.relative_to(root).parts:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else None
            )
            if name == "decided_stop_pct":
                calls.append(
                    (path, node.lineno, any(kw.arg == "fills" for kw in node.keywords))
                )
    return calls


def test_a11_every_resolver_call_shares_its_pass_read() -> None:
    """EXEC-PERF-02 / MON-PERF-03 / ANLZ-PERF-02: all three calls pass fills=."""
    root = Path(__file__).resolve().parents[1]
    calls = [
        call
        for folder in ("agents", "contracts")
        for call in resolver_calls(root / folder)
    ]

    assert len(calls) == 3, calls
    assert all(shared for _path, _line, shared in calls), calls


def test_a12_the_guard_sees_a_call_without_a_shared_read(tmp_path: Path) -> None:
    """EXEC-PERF-02 / MON-PERF-03 / ANLZ-PERF-02: the reader flags an omission."""
    probe = tmp_path / "probe.py"
    probe.write_text(
        "decided_stop_pct(graph, node)\n"
        "resolver.decided_stop_pct(graph, node, fills=fills)\n",
        encoding="utf-8",
    )
    excluded = tmp_path / "nested" / "tests"
    excluded.mkdir(parents=True)
    (excluded / "fixture.py").write_text(
        "decided_stop_pct(graph, node)\n", encoding="utf-8"
    )

    assert resolver_calls(tmp_path) == [(probe, 1, False), (probe, 2, True)]
