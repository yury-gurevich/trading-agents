"""Broker evidence graph-label ownership tests.

Agent: execution
Role: prove broker-boundary evidence labels are written only by execution code.
External I/O: reads shipped Python sources.
"""

from __future__ import annotations

import ast
from pathlib import Path

from scripts.vocabulary_coverage import parse_all, resolve_strings, string_constants

ROOT = Path(__file__).resolve().parents[3]
EXECUTION_ROOT = ROOT / "agents" / "execution"
EVIDENCE_LABELS = frozenset(
    {"BrokerStopOrder", "BrokerPositionSnapshot", "BrokerOrderStatus"}
)


def test_broker_evidence_labels_have_execution_only_writers() -> None:
    """EXEC-IDN-03: broker evidence labels are merged only from execution code."""
    trees = parse_all(ROOT)
    constants = string_constants(trees)
    seen: set[str] = set()
    offenders: list[str] = []
    for path, tree in trees.items():
        for node in ast.walk(tree):
            label_arg = _node_write_label_arg(node)
            if label_arg is None:
                continue
            labels = resolve_strings(label_arg, constants) & EVIDENCE_LABELS
            if not labels:
                continue
            seen |= labels
            if not path.is_relative_to(EXECUTION_ROOT):
                found = ", ".join(sorted(labels))
                offenders.append(f"{path.relative_to(ROOT).as_posix()} -> {found}")

    assert seen == EVIDENCE_LABELS
    assert offenders == []


def _node_write_label_arg(node: ast.AST) -> ast.expr | None:
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "merge_node"
        and bool(node.args)
    ):
        return node.args[0]
    return None
