"""Provider agent package.

Agent: provider
Role: expose the provider boundary agent.
External I/O: none.
"""

from __future__ import annotations

from typing import Any

__all__ = ["ProviderAgent"]


def __getattr__(name: str) -> Any:  # noqa: ANN401 - module export hook.
    """Resolve package convenience exports lazily."""
    if name == "ProviderAgent":
        from agents.provider.agent import ProviderAgent

        return ProviderAgent
    raise AttributeError(name)  # pragma: no cover
