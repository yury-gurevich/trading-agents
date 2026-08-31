"""Static broker lifecycle invariants.

Agent: contracts
Role: keep execution broker fact lifecycle vocabulary in one contract module.
External I/O: reads source files only.
"""

from __future__ import annotations

import ast
from pathlib import Path

LIFECYCLE_MODULE = Path("contracts/broker_lifecycle.py")
TARGETS = (
    Path("agents/execution/drop_sweep.py"),
    Path("agents/execution/filled_entry_stops.py"),
    Path("agents/execution/reconciliation_store.py"),
    Path("agents/execution/run.py"),
    Path("agents/reporter/domain/trade_outcomes.py"),
)


def test_broker_lifecycle_vocabulary_lives_in_one_module() -> None:
    """EXEC-OBS-05: broker lifecycle status sets have one owner."""
    offenders: list[str] = []
    for path in TARGETS:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if _is_status_set_assignment(node):
                offenders.append(f"{path}:{node.lineno}")
            if _is_inline_terminal_status_set(node):
                offenders.append(f"{path}:{node.lineno}")

    assert LIFECYCLE_MODULE.exists()
    assert offenders == []


def _is_status_set_assignment(node: ast.AST) -> bool:
    if not isinstance(node, ast.Assign):
        return False
    if not any(_target_name(target).endswith("STATUSES") for target in node.targets):
        return False
    return isinstance(node.value, ast.Call) and _call_name(node.value) == "frozenset"


def _is_inline_terminal_status_set(node: ast.AST) -> bool:
    if not isinstance(node, ast.Set):
        return False
    values = {
        value.value.lower()
        for value in node.elts
        if isinstance(value, ast.Constant) and isinstance(value.value, str)
    }
    terminal_terms = {"canceled", "cancelled", "expired", "filled", "rejected"}
    return len(values & terminal_terms) >= 2


def _target_name(target: ast.expr) -> str:
    return target.id if isinstance(target, ast.Name) else ""


def _call_name(call: ast.Call) -> str:
    return call.func.id if isinstance(call.func, ast.Name) else ""
