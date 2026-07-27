"""Static vocabulary coverage — what the code can write vs what the pack declares.

Agent: tooling
Role: extract every node label and edge type reachable as a literal or module
      constant in shipped code, so the declared vocabulary can be proven a
      superset of what the code is able to write.
External I/O: reads .py sources under the scanned packages.

A vocabulary derived from the live graph is a trailing indicator: it can only
contain what has already happened. Broker-native stops (ADR-0015 section 3)
shipped with two edges no run had ever produced, so the pack did not declare
them — enabling the guard would have raised VocabularyError on the first real
stop (S144). This check moves that discovery to `make ci`.

Deliberately an over-approximation of constants and an under-approximation of
computed arguments: a label built at runtime is invisible here, so this is a
floor on coverage, not a ceiling.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

_NODE_WRITE = "merge_node"
_EDGE_WRITE = "add_edge"
_EDGE_TYPE_ARG = 2
_SKIP_PARTS = frozenset({"tests", "mutants", "__pycache__"})

PACKAGES = ("agents", "contracts", "kernel", "orchestration", "surfaces", "scripts")


@dataclass(frozen=True)
class Written:
    """The labels and edge types the scanned code is able to write."""

    labels: frozenset[str]
    edge_types: frozenset[str]


def source_files(root: Path, packages: tuple[str, ...] = PACKAGES) -> tuple[Path, ...]:
    """Return shipped (non-test) .py files under *packages*, sorted."""
    found: list[Path] = []
    for package in packages:
        base = root / package
        if not base.is_dir():
            continue
        found.extend(
            path
            for path in sorted(base.rglob("*.py"))
            if not _SKIP_PARTS & set(path.parts)
        )
    return tuple(found)


def string_constants(trees: dict[Path, ast.Module]) -> dict[str, frozenset[str]]:
    """Map every module-level ``NAME = "value"`` across the scan to its values.

    Resolution is global rather than per-module because the label constants are
    defined in `contracts/` and used in `agents/` (e.g. BROKER_STOP_ORDER_LABEL).
    """
    values: dict[str, set[str]] = {}
    for tree in trees.values():
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            value = node.value
            if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    values.setdefault(target.id, set()).add(value.value)
    return {name: frozenset(found) for name, found in values.items()}


def resolve_strings(
    node: ast.expr, constants: dict[str, frozenset[str]]
) -> frozenset[str]:
    """Resolve one call argument to the string values it can take."""
    if isinstance(node, ast.Constant):
        return frozenset({node.value}) if isinstance(node.value, str) else frozenset()
    if isinstance(node, ast.Name):
        return constants.get(node.id, frozenset())
    if isinstance(node, ast.Attribute):
        return constants.get(node.attr, frozenset())
    return frozenset()


def parse_all(
    root: Path, packages: tuple[str, ...] = PACKAGES
) -> dict[Path, ast.Module]:
    """Parse every scanned source file once."""
    return {
        path: ast.parse(path.read_text(encoding="utf-8"))
        for path in source_files(root, packages)
    }


def scan(root: Path, packages: tuple[str, ...] = PACKAGES) -> Written:
    """Return the labels and edge types written anywhere in the scanned code."""
    trees = parse_all(root, packages)
    constants = string_constants(trees)
    labels: set[str] = set()
    edge_types: set[str] = set()
    for tree in trees.values():
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr == _NODE_WRITE and node.args:
                labels |= resolve_strings(node.args[0], constants)
            elif node.func.attr == _EDGE_WRITE and len(node.args) > _EDGE_TYPE_ARG:
                edge_types |= resolve_strings(node.args[_EDGE_TYPE_ARG], constants)
    return Written(labels=frozenset(labels), edge_types=frozenset(edge_types))
