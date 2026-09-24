"""Reporter agent public API.

Agent: reporter
Role: expose the agent lazily without coupling pure domain imports to I/O.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.reporter.agent import ReporterAgent


def __getattr__(name: str) -> type[ReporterAgent]:
    """Load the runtime agent only when its public symbol is requested."""
    if name != "ReporterAgent":
        raise AttributeError(name)
    from agents.reporter.agent import ReporterAgent

    return ReporterAgent


__all__ = ["ReporterAgent"]
