"""Analyst agent package.

Agent: analyst
Role: expose the analyst boundary agent.
External I/O: none.
"""

from __future__ import annotations

from typing import Any

__all__ = ["AnalystAgent"]


def __getattr__(name: str) -> Any:  # noqa: ANN401 - module export hook.
    """Resolve package convenience exports lazily."""
    if name == "AnalystAgent":
        from agents.analyst.agent import AnalystAgent

        return AnalystAgent
    raise AttributeError(name)  # pragma: no cover
