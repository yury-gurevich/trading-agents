"""No substrate module names a pack agent.

Agent: kernel
Role: prove the substrate (kernel/ and agents/master/, tests excluded) holds
      no string literal, outside docstrings, equal to a pack agent type —
      neither a trading_grants.json key nor a served-roster role/image name.
External I/O: reads local source files.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

_PACK_AGENT_TYPES = frozenset(
    json.loads(
        Path("orchestration/packs/trading_grants.json").read_text(encoding="utf-8")
    ).keys()
) | {"deliberator"}


def _production_modules() -> list[Path]:
    modules = sorted(Path("kernel").glob("*.py"))
    modules += sorted(
        path for path in Path("agents/master").glob("*.py") if "tests" not in path.parts
    )
    return modules


def _docstring_node(node: ast.AST) -> ast.Constant | None:
    body = getattr(node, "body", None)
    if not body:
        return None
    first = body[0]
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        return first.value
    return None


def _string_literals_excluding_docstrings(tree: ast.Module) -> set[tuple[str, int]]:
    docstring_bearing = (
        ast.Module,
        ast.ClassDef,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
    )
    docstring_ids = set()
    for node in ast.walk(tree):
        if isinstance(node, docstring_bearing):
            doc_node = _docstring_node(node)
            if doc_node is not None:
                docstring_ids.add(id(doc_node))
    return {
        (node.value, node.lineno)
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstring_ids
    }


def _pack_literal_hits() -> list[str]:
    hits: list[str] = []
    for path in _production_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for value, lineno in sorted(
            _string_literals_excluding_docstrings(tree), key=lambda item: item[1]
        ):
            if value in _PACK_AGENT_TYPES:
                hits.append(f"{path}:{lineno}: {value!r}")
    return hits


def test_no_substrate_module_names_a_pack_agent() -> None:
    """MST-DEP-05: the substrate holds no pack agent-type string literal."""
    assert _pack_literal_hits() == []
