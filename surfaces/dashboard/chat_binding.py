"""Dashboard composition helper for the in-process operator chat binding.

Agent: surfaces
Role: bind the existing operator surface only when live graph and LLM config exist.
External I/O: process environment; selected-vendor calls occur later via the operator.
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from agents.operator.settings import OperatorSettings
from kernel.llm_anthropic import ConfigurationError as AnthropicConfigurationError
from kernel.llm_factory import (
    ModelProviderMismatchError,
    UnknownProviderError,
    build_operator_llm,
    key_env_var,
)
from kernel.llm_openai import ConfigurationError as OpenAIConfigurationError
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
    if graph is None or not env.get("POSTGRES_DSN", ""):
        return None
    settings = OperatorSettings()
    try:
        api_key = env.get(key_env_var(settings.llm_provider), "")
        if not api_key:
            return None
        llm = build_operator_llm(
            settings.llm_provider,
            api_key=api_key,
            model=settings.resolved_model,
            max_tokens=settings.max_tokens,
            effort=settings.resolved_effort,
        )
    except ModelProviderMismatchError as exc:
        sys.stderr.write(f"dashboard: operator chat not connected: {exc}\n")
        return None
    except (
        UnknownProviderError,
        AnthropicConfigurationError,
        OpenAIConfigurationError,
    ):
        return None
    return paper_context(graph=graph, llm=llm)
