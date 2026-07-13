"""Dashboard composition helper for the in-process operator chat binding.

Agent: surfaces
Role: bind the existing operator surface only when live graph and LLM config exist.
External I/O: reads process environment; Anthropic calls occur later via the operator.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from agents.operator.llm_anthropic import AnthropicLLMClient, ConfigurationError
from agents.operator.settings import OperatorSettings
from surfaces.context import paper_context

if TYPE_CHECKING:
    from collections.abc import Mapping

    from kernel import GraphStore
    from surfaces.context import SurfaceContext


def bind_dashboard_chat(
    graph: GraphStore | None, environ: Mapping[str, str] | None = None
) -> SurfaceContext | None:
    """Bind the operator in-process, or return None for an honest empty state."""
    env = os.environ if environ is None else environ
    api_key = env.get("ANTHROPIC_API_KEY", "")
    if graph is None or not env.get("POSTGRES_DSN", "") or not api_key:
        return None
    settings = OperatorSettings()
    try:
        llm = AnthropicLLMClient(
            api_key=api_key,
            model=settings.model,
            max_tokens=settings.max_tokens,
        )
    except ConfigurationError:
        return None
    return paper_context(graph=graph, llm=llm)
