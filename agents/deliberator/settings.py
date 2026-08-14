"""Deliberator settings and justified role/model tunables.

Agent: deliberator
Role: own deliberator role identity, debate round count, and per-role models.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from typing import Literal

from pydantic_settings import SettingsConfigDict

from agents.deliberator.llm_factory import default_model_for
from kernel import AgentSettings, tunable

Effort = Literal["low", "medium", "high", "xhigh", "max"]
DebateRole = Literal["defender", "challenger"]
DeliberatorRole = Literal["manager", "proponent", "opponent"]


class DeliberatorSettings(AgentSettings):
    """Settings for the one-image, three-role deliberator deployment."""

    role: DeliberatorRole = tunable(
        "manager",
        why=(
            "One image is deployed as three bounded instances; this selects "
            "whether the process pulls PMRun work or serves peer debate turns."
        ),
    )
    instance_name: str = tunable(
        "",
        why=(
            "Optional concrete bus identity. Empty derives deliberator-<role>, "
            "matching the fleet app names."
        ),
    )
    max_rounds: int = tunable(
        2,
        why=(
            "Manager-driven debate must show more than one round in live proof, "
            "while staying bounded before execution."
        ),
        ge=1,
        le=5,
    )
    llm_provider: str = tunable(
        default="anthropic",
        why=(
            "Which vendor answers deliberation calls. A tunable, not an automatic "
            "fallback: a silent switch would make 'which model reviewed this order' "
            "unanswerable afterwards. Switching is an operator act (DL-99)."
        ),
    )
    defender_model: str = tunable(
        "",
        why=(
            "Model for the proponent/defender turn role. Empty resolves the "
            "provider's own default, so switching provider is one switch."
        ),
    )
    challenger_model: str = tunable(
        "",
        why=(
            "Model for the opponent/challenger turn role. Empty resolves the "
            "provider's own default, so switching provider is one switch."
        ),
    )
    judge_model: str = tunable(
        "",
        why=(
            "Model for the manager/judge verdict role. Empty resolves the "
            "provider's own default, so switching provider is one switch."
        ),
    )
    effort: Effort = tunable(
        "max",
        why="Anthropic output_config effort for deliberation calls.",
    )
    max_tokens: int = tunable(
        4096,
        why="Caps each role's reasoning and answer payload.",
        ge=64,
        le=4096,
        unit="tokens",
    )
    request_timeout_seconds: float = tunable(
        30.0,
        why="Bounds manager wait time for served proponent/opponent replies.",
        ge=1.0,
        le=120.0,
        unit="seconds",
    )
    poll_interval_seconds: int = tunable(
        60,
        why="Graph-pull idle wait for the manager loop.",
        ge=1,
        le=300,
        unit="seconds",
    )
    proponent_identity: str = tunable(
        "deliberator-proponent",
        why="Served peer identity the manager asks for defender turns.",
    )
    opponent_identity: str = tunable(
        "deliberator-opponent",
        why="Served peer identity the manager asks for challenger turns.",
    )

    model_config = SettingsConfigDict(env_prefix="DELIBERATOR_", frozen=True)

    @property
    def identity(self) -> str:
        """Return the concrete bus identity for this instance."""
        return self.instance_name or f"deliberator-{self.role}"

    @property
    def peer_role(self) -> DebateRole | None:
        """Return the debate role served by this instance, if it is a peer."""
        if self.role == "proponent":
            return "defender"
        if self.role == "opponent":
            return "challenger"
        return None

    def model_for_role(self, role: DebateRole | Literal["judge"]) -> str:
        """Return the resolved model for one debate role.

        An unset tunable resolves the *provider's* default rather than a literal
        vendor name, so `llm_provider` is the whole switch (DL-100). An explicit
        setting still wins. Callers must record what this returns, never the
        tunable: a `role_models` entry reading `""` is a worse audit record than
        the wrong-but-populated one it replaces.
        """
        if role == "defender":
            configured = self.defender_model
        elif role == "challenger":
            configured = self.challenger_model
        else:
            configured = self.judge_model
        return configured or default_model_for(self.llm_provider)
