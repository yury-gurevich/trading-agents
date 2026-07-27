"""Static edge-signature recovery — the dimension a label check cannot reach.

Agent: tooling
Role: recover (parent_label, edge_type, child_label) triples from shipped code
      by following Node-valued locals back to the merge_node that produced them.
External I/O: reads .py sources via vocabulary_coverage.parse_all.

Both labels and both edge types of the broker-native stop path were declared;
only the *signatures* were missing. A label-level check therefore read green
while the guard would still have raised on the first real stop (S144).
Signatures are the dimension that actually bit, so they get their own check.

Resolution is intra-function, plus one hop through helpers whose return value is
a merge_node call. Anything else stays unresolved and is simply not reported:
this is a floor on what the code can write, never a claim of completeness.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from vocabulary_coverage import PACKAGES, parse_all, resolve_strings, string_constants

if TYPE_CHECKING:
    from pathlib import Path

Signature = tuple[str, str, str]
"""``(parent_label, edge_type, child_label)`` recovered from a call site."""

_NODE_WRITE = "merge_node"
_EDGE_WRITE = "add_edge"
_EDGE_TYPE_ARG = 2
type _Function = ast.FunctionDef | ast.AsyncFunctionDef
type _Strings = dict[str, frozenset[str]]
type _Assigned = dict[str, tuple[tuple[int, frozenset[str]], ...]]


def _merge_call(node: ast.expr) -> ast.Call | None:
    """Return *node* when it is a ``<something>.merge_node(...)`` call."""
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == _NODE_WRITE
        and node.args
    ):
        return node
    return None


def _edge_call(node: ast.AST) -> ast.Call | None:
    """Return *node* when it is an ``<something>.add_edge(p, c, type)`` call."""
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == _EDGE_WRITE
        and len(node.args) > _EDGE_TYPE_ARG
    ):
        return node
    return None


def _functions(trees: dict[Path, ast.Module]) -> tuple[_Function, ...]:
    """Return every function definition across the parsed sources."""
    return tuple(
        node
        for tree in trees.values()
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    )


def _returned_labels(trees: dict[Path, ast.Module], constants: _Strings) -> _Strings:
    """Map a helper's name to the labels it returns via a direct merge_node."""
    returns: dict[str, set[str]] = {}
    for func in _functions(trees):
        for stmt in ast.walk(func):
            if not isinstance(stmt, ast.Return) or stmt.value is None:
                continue
            call = _merge_call(stmt.value)
            if call is not None:
                returns.setdefault(func.name, set()).update(
                    resolve_strings(call.args[0], constants)
                )
    return {name: frozenset(found) for name, found in returns.items()}


def _locals_in(func: _Function, constants: _Strings, returns: _Strings) -> _Assigned:
    """Map each local variable to its (line, labels) assignments in *func*.

    Assignments are kept per line rather than collapsed, because one name is
    routinely rebound to a different label inside the same function — the PM
    store binds ``node`` to OrderIntent, then to Rejection. Collapsing them
    invents edges that no call site writes.
    """
    known: dict[str, list[tuple[int, frozenset[str]]]] = {}
    for stmt in ast.walk(func):
        if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
            continue
        target = stmt.targets[0]
        if not isinstance(target, ast.Name):
            continue
        call = _merge_call(stmt.value)
        if call is not None:
            found = resolve_strings(call.args[0], constants)
        elif isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name):
            found = returns.get(stmt.value.func.id, frozenset())
        else:
            continue
        if found:
            known.setdefault(target.id, []).append((stmt.lineno, found))
    return {name: tuple(sorted(rows)) for name, rows in known.items()}


def _labels_of(
    node: ast.expr, known: _Assigned, constants: _Strings, lineno: int
) -> frozenset[str]:
    """Resolve one add_edge endpoint to the labels it may carry at *lineno*.

    The binding in force is the nearest assignment above the call site.
    """
    if isinstance(node, ast.Name):
        prior = [row for row in known.get(node.id, ()) if row[0] <= lineno]
        return prior[-1][1] if prior else frozenset()
    call = _merge_call(node)
    return resolve_strings(call.args[0], constants) if call is not None else frozenset()


def signatures(
    root: Path, packages: tuple[str, ...] = PACKAGES
) -> frozenset[Signature]:
    """Return every edge signature statically recoverable from the code."""
    trees = parse_all(root, packages)
    constants = string_constants(trees)
    returns = _returned_labels(trees, constants)
    found: set[Signature] = set()
    for func in _functions(trees):
        known = _locals_in(func, constants, returns)
        for node in ast.walk(func):
            call = _edge_call(node)
            if call is None:
                continue
            parents = _labels_of(call.args[0], known, constants, call.lineno)
            children = _labels_of(call.args[1], known, constants, call.lineno)
            edges = resolve_strings(call.args[_EDGE_TYPE_ARG], constants)
            found |= {
                (parent, edge, child)
                for parent in parents
                for edge in edges
                for child in children
            }
    return frozenset(found)
