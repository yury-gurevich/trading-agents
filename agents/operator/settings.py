"""Operator settings and justified LLM tunables.

Agent: operator
Role: own operator model and evidence-window defaults.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from typing import Literal

from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable
from kernel.llm_factory import default_model_for


class OperatorSettings(AgentSettings):
    """Settings for bounded operator intent parsing and explanations."""

    llm_provider: str = tunable(
        "anthropic",
        why="Operator-declared LLM vendor; never an automatic fallback.",
    )
    model: str = tunable(
        "",
        why="Empty resolves the declared provider's model; explicit values win.",
    )
    effort: Literal["low", "medium", "high", "xhigh", "max"] = tunable(
        "max",
        why=(
            "Provider reasoning effort. 'max' buys the deepest reasoning "
            "per call; the literal mirrors the API's own ladder so an operator "
            "override cannot send a value the model rejects."
        ),
    )
    max_tokens: int = tunable(
        4096,
        why=(
            "Caps thinking plus structured output together. On models where "
            "thinking is on by default the old 512 ceiling is spent reasoning "
            "before any tool call is emitted, so the parse returns refused."
        ),
        ge=64,
        le=4096,
        unit="tokens",
    )
    explain_max_evidence_nodes: int = tunable(
        20,
        why="Bound graph evidence included in explanation prompts.",
        ge=1,
        le=100,
        unit="nodes",
    )
    system_prompt: str = tunable(
        "",
        why=(
            "Champion slot for the DSPy-compiled interpret system prompt "
            "(ADR-0010). Empty = use the dynamic build_interpret_system() "
            "construction; non-empty = DSPy-promoted static override."
        ),
    )

    model_config = SettingsConfigDict(env_prefix="OPERATOR_", frozen=True)

    @property
    def resolved_model(self) -> str:
        """Resolve the declared vendor's model unless explicitly overridden."""
        return self.model or default_model_for(self.llm_provider)
