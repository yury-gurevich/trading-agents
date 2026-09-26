"""The dispatcher image's import closure, read from source rather than remembered.

Agent: tooling
Role: name every first-party module a slim image must copy for its entrypoint to run.
External I/O: local Python source reads only.
"""

from __future__ import annotations

import ast
from pathlib import Path


def _runtime_imports(module: ast.Module) -> list[ast.ImportFrom]:
    """Every `from x import y` the module executes — TYPE_CHECKING blocks excluded."""
    type_checking_only: set[int] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.If) and _is_type_checking(node.test):
            type_checking_only.update(id(child) for child in ast.walk(node))
    return [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.ImportFrom) and id(node) not in type_checking_only
    ]


def _is_type_checking(test: ast.expr) -> bool:
    return isinstance(test, ast.Name) and test.id == "TYPE_CHECKING"


def first_party_modules(entrypoints: tuple[str, ...]) -> set[str]:
    """Transitively close the entrypoints over their agents/ and orchestration/ imports.

    kernel/ and contracts/ are copied whole, so only these two trees need naming.
    Importing `a.b.c` also executes `a/__init__.py` and `a/b/__init__.py`, so each
    module's parent packages join the closure (S227: `orchestration/packs/__init__.py`
    imported a module the image did not carry). `from a.b import c` imports the
    submodule `a/b/c.py` when there is one (S234: `from agents.portfolio_manager.domain
    import deployment_floor` named a file this closure never reached).
    """
    seen: set[str] = set()
    queue = list(entrypoints)
    while queue:
        path = queue.pop()
        if path in seen or not Path(path).exists():
            continue
        seen.add(path)
        module = ast.parse(Path(path).read_text(encoding="utf-8"))
        imports = _runtime_imports(module)
        if path.endswith("__init__.py"):  # a lazy __getattr__ import does not run
            imports = [node for node in imports if node in module.body]
        for node in imports:
            if node.module is None or not node.module.startswith(
                ("agents.", "orchestration.")
            ):
                continue
            parts = node.module.split(".")
            queue.append(f"{'/'.join(parts)}.py")
            queue.extend(
                f"{'/'.join(parts[:depth])}/__init__.py"
                for depth in range(1, len(parts) + 1)
            )
            queue.extend(
                f"{'/'.join(parts)}/{alias.name}{suffix}"
                for alias in node.names
                for suffix in (".py", "/__init__.py")
            )
    return seen
