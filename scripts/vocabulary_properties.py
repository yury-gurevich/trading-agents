"""Static property recovery — the vocabulary dimension a label check cannot reach.

Agent: tooling
Role: recover, per node label, the property names shipped code can write at a
      merge_node call site, and name every site it could not resolve.
External I/O: reads .py sources via vocabulary_coverage.parse_all.

S149 taught the guard to enforce declared node properties, but the completeness
suite proved supersets for labels, edge types and signatures only. A pack that
under-declares one property therefore reads green here and raises
VocabularyError on the first real write — S143's trailing-indicator lesson one
level down, this time on a fail-closed write path.

Unresolved sites are reported rather than skipped. A scan that resolves nothing
yields an empty undeclared set, which is indistinguishable from a scan that
looked and found nothing (DL-57); only a named blind spot tells the two apart.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING

from vocabulary_coverage import PACKAGES, parse_all, resolve_strings, string_constants
from vocabulary_resolution import Resolver

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

_NODE_WRITE = "merge_node"
_PROPS_ARG = 2


@dataclass(frozen=True)
class WrittenProps:
    """Per-label property names the scanned code is able to write."""

    properties: Mapping[str, frozenset[str]]
    """label -> every property name recoverable at a merge_node call site."""

    unresolved: Mapping[str, frozenset[str]]
    """label -> functions whose props argument could not be fully resolved."""


def _merge_call(node: ast.AST) -> ast.Call | None:
    """Return *node* when it is a ``merge_node(label, key, props)`` call."""
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == _NODE_WRITE
        and len(node.args) > _PROPS_ARG
    ):
        return node
    return None


def properties(root: Path, packages: tuple[str, ...] = PACKAGES) -> WrittenProps:
    """Return the property names, per label, the scanned code is able to write."""
    trees = parse_all(root, packages)
    constants = string_constants(trees)
    resolver = Resolver(trees, constants)
    found: dict[str, set[str]] = {}
    blind: dict[str, set[str]] = {}
    for tree in trees.values():
        for scope in ast.walk(tree):
            if not isinstance(scope, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            for node in ast.walk(scope):
                call = _merge_call(node)
                if call is None:
                    continue
                resolved = resolver.expression(
                    call.args[_PROPS_ARG], scope, frozenset()
                )
                for label in resolve_strings(call.args[0], constants):
                    found.setdefault(label, set()).update(resolved.names)
                    if not resolved.total:
                        blind.setdefault(label, set()).add(scope.name)
    return WrittenProps(
        properties={label: frozenset(v) for label, v in found.items()},
        unresolved={label: frozenset(v) for label, v in blind.items()},
    )
