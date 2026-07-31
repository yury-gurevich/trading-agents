"""Props-expression resolution — how a merge_node argument becomes key names.

Agent: tooling
Role: resolve the expression passed as merge_node's props argument to the
      property names it can carry, tracking whether that resolution was total.
External I/O: none — callers supply already-parsed trees.

Split from vocabulary_properties so the scan stays readable: this module is the
engine, that one is the sweep. Resolution follows the props-builder idiom this
repo actually uses — an initial literal, conditional ``props[...] = ...``,
``props.update(helper())`` — plus one interprocedural hop for arguments bound to
parameters and for a dataclass field carrying a props dict through a return.

Totality is conjunctive and pessimistic: anything not understood makes the whole
resolution partial. That is the point. A resolver that silently returned the
names it happened to recognise would report "no undeclared properties" for a
call site it never read (DL-57).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

type Function = ast.FunctionDef | ast.AsyncFunctionDef
type Strings = dict[str, frozenset[str]]
type Bindings = Mapping[str, "Resolved"]


@dataclass(frozen=True)
class Resolved:
    """Property names recovered from one expression, and whether that was total."""

    names: frozenset[str]
    total: bool

    def merge(self, other: Resolved) -> Resolved:
        """Combine two partial resolutions; totality is conjunctive."""
        return Resolved(self.names | other.names, self.total and other.total)


NOTHING = Resolved(frozenset(), total=False)
EMPTY = Resolved(frozenset(), total=True)


def _subscript_index(target: ast.expr, name: str) -> ast.expr | None:
    """Return the index of a ``name[...] = ...`` assignment, else None."""
    if (
        isinstance(target, ast.Subscript)
        and isinstance(target.value, ast.Name)
        and target.value.id == name
    ):
        return target.slice
    return None


def _is_update_of(stmt: ast.AST, name: str) -> bool:
    """Return True for a ``name.update(<expr>)`` call."""
    return (
        isinstance(stmt, ast.Call)
        and isinstance(stmt.func, ast.Attribute)
        and stmt.func.attr == "update"
        and isinstance(stmt.func.value, ast.Name)
        and stmt.func.value.id == name
        and bool(stmt.args)
    )


class Resolver:
    """Resolve props expressions against every function in the scan."""

    def __init__(self, trees: dict[Path, ast.Module], constants: Strings) -> None:
        self._constants = constants
        self._functions: dict[str, list[Function]] = {}
        for tree in trees.values():
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    self._functions.setdefault(node.name, []).append(node)

    def expression(
        self,
        node: ast.expr,
        scope: Function | None,
        seen: frozenset[str],
        bindings: Bindings | None = None,
    ) -> Resolved:
        """Resolve one expression used as a props argument."""
        bindings = {} if bindings is None else bindings
        if isinstance(node, ast.Dict):
            return self._mapping(node, scope, seen, bindings)
        if isinstance(node, ast.Name):
            if node.id in bindings:
                return bindings[node.id]
            return self._local(node.id, scope, seen, bindings)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "dict":
                return self._builtin_dict(node, scope, seen, bindings)
            return self._call(node, scope, seen, bindings)
        if isinstance(node, ast.Attribute):
            return self._field(node, scope, seen, bindings)
        return NOTHING

    def _mapping(
        self, node: ast.Dict, scope: Function | None, seen: frozenset[str], b: Bindings
    ) -> Resolved:
        """Resolve a dict literal, following ``{**other}`` spreads."""
        found = EMPTY
        for key, value in zip(node.keys, node.values, strict=True):
            if key is None:
                found = found.merge(self.expression(value, scope, seen, b))
            else:
                found = found.merge(self.key(key))
        return found

    def _builtin_dict(
        self, node: ast.Call, scope: Function | None, seen: frozenset[str], b: Bindings
    ) -> Resolved:
        """Resolve ``dict(other)`` / ``dict(**other)`` / ``dict(a=1)``.

        The copy idiom is how the fill attempt chain clones a props dict before
        stamping its own keys onto it; without this the chain reads unresolved.
        """
        found = EMPTY
        for arg in node.args:
            found = found.merge(self.expression(arg, scope, seen, b))
        for keyword in node.keywords:
            if keyword.arg is None:
                found = found.merge(self.expression(keyword.value, scope, seen, b))
            else:
                found = found.merge(Resolved(frozenset({keyword.arg}), total=True))
        return found

    def key(self, node: ast.expr) -> Resolved:
        """Resolve one mapping key or subscript index to its literal names."""
        if isinstance(node, ast.Constant):
            return (
                Resolved(frozenset({node.value}), total=True)
                if isinstance(node.value, str)
                else NOTHING
            )
        if isinstance(node, ast.Name | ast.Attribute):
            attr = node.id if isinstance(node, ast.Name) else node.attr
            names = self._constants.get(attr, frozenset())
            return Resolved(names, total=bool(names))
        return NOTHING

    def _local(
        self, name: str, scope: Function | None, seen: frozenset[str], b: Bindings
    ) -> Resolved:
        """Resolve a local props dict from every statement that builds it."""
        if scope is None:
            return NOTHING
        found, bound = EMPTY, False
        for stmt in ast.walk(scope):
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                target = stmt.targets[0]
                if isinstance(target, ast.Name) and target.id == name:
                    found = found.merge(self.expression(stmt.value, scope, seen, b))
                    bound = True
                else:
                    index = _subscript_index(target, name)
                    if index is not None:
                        found = found.merge(self.key(index))
            elif (
                isinstance(stmt, ast.AnnAssign)
                and isinstance(stmt.target, ast.Name)
                and stmt.target.id == name
                and stmt.value is not None
            ):
                found = found.merge(self.expression(stmt.value, scope, seen, b))
                bound = True
            elif _is_update_of(stmt, name) and isinstance(stmt, ast.Call):
                found = found.merge(self.expression(stmt.args[0], scope, seen, b))
        return found if bound else NOTHING

    def _bind(
        self,
        func: Function,
        call: ast.Call,
        caller: Bindings,
        scope: Function | None,
        seen: frozenset[str],
    ) -> dict[str, Resolved]:
        """Bind a call's actual arguments to the callee's parameter names."""
        names = [arg.arg for arg in func.args.posonlyargs + func.args.args]
        bound: dict[str, Resolved] = {}
        for name, node in zip(names, call.args, strict=False):
            bound[name] = self.expression(node, scope, seen, caller)
        allowed = set(names) | {arg.arg for arg in func.args.kwonlyargs}
        for keyword in call.keywords:
            if keyword.arg in allowed:
                bound[keyword.arg] = self.expression(keyword.value, scope, seen, caller)
        return bound

    def _call(
        self, node: ast.Call, scope: Function | None, seen: frozenset[str], b: Bindings
    ) -> Resolved:
        """Resolve a call by unioning the props every ``return`` can produce."""
        assert isinstance(node.func, ast.Name)  # narrowed by the caller
        name = node.func.id
        if name in seen or name not in self._functions:
            return NOTHING
        inner = seen | {name}
        found, returned = EMPTY, False
        for func in self._functions[name]:
            bound = self._bind(func, node, b, scope, seen)
            for stmt in ast.walk(func):
                if isinstance(stmt, ast.Return) and stmt.value is not None:
                    found = found.merge(self.expression(stmt.value, func, inner, bound))
                    returned = True
        return found if returned else NOTHING

    def _field(
        self,
        node: ast.Attribute,
        scope: Function | None,
        seen: frozenset[str],
        b: Bindings,
    ) -> Resolved:
        """Resolve ``local.field`` where *local* came from a constructing call.

        This is the passthrough the execution fill path uses: a props dict is
        handed to a helper, stored on a frozen dataclass, and merged from the
        attribute. Without this hop the whole chain reads as unresolved.
        """
        if not isinstance(node.value, ast.Name) or scope is None:
            return NOTHING
        source = self._assigned_call(node.value.id, scope)
        if source is None or not isinstance(source.func, ast.Name):
            return NOTHING
        name = source.func.id
        if name in seen or name not in self._functions:
            return NOTHING
        inner = seen | {name}
        found, matched = EMPTY, False
        for func in self._functions[name]:
            bound = self._bind(func, source, b, scope, seen)
            for stmt in ast.walk(func):
                if not isinstance(stmt, ast.Return) or not isinstance(
                    stmt.value, ast.Call
                ):
                    continue
                for keyword in stmt.value.keywords:
                    if keyword.arg == node.attr:
                        found = found.merge(
                            self.expression(keyword.value, func, inner, bound)
                        )
                        matched = True
        return found if matched else NOTHING

    @staticmethod
    def _assigned_call(name: str, scope: Function) -> ast.Call | None:
        """Return the single call assigned to *name* in *scope*, if there is one."""
        calls = [
            stmt.value
            for stmt in ast.walk(scope)
            if isinstance(stmt, ast.Assign)
            and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name)
            and stmt.targets[0].id == name
            and isinstance(stmt.value, ast.Call)
        ]
        return calls[0] if len(calls) == 1 else None
