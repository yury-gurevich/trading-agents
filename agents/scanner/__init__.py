"""Scanner agent package.

Agent: scanner
Role: expose the scanner boundary agent.
External I/O: none.
"""

from __future__ import annotations

from typing import Any

__all__ = ["ScannerAgent"]


def __getattr__(name: str) -> Any:  # noqa: ANN401 - module export hook.
    """Resolve package convenience exports lazily."""
    if name == "ScannerAgent":
        from agents.scanner.agent import ScannerAgent

        return ScannerAgent
    raise AttributeError(name)  # pragma: no cover
