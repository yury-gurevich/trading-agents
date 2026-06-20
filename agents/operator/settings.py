"""Operator settings and justified LLM tunables.

Agent: operator
Role: own operator model and evidence-window defaults.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable


class OperatorSettings(AgentSettings):
    """Settings for bounded operator intent parsing and explanations."""

    model: str = tunable(
        "claude-sonnet-4-6",
        why="Production default for structured human-command intent parsing.",
    )
    max_tokens: int = tunable(
        512,
        why="Intent parsing needs short structured output; cap controls cost.",
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
