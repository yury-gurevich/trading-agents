"""Reporter settings and justified narrative tunables.

Agent: reporter
Role: own reporter output limits without adding external dependencies.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable


class ReporterSettings(AgentSettings):
    """Settings for graph-backed reporter outputs."""

    model_config = SettingsConfigDict(env_prefix="REPORTER_", frozen=True)

    max_narrative_length_chars: int = tunable(
        2000,
        why=(
            "P3 narratives are short deterministic summaries; this future-proofs "
            "dashboard rendering if a later graph adds more evidence legs."
        ),
        ge=200,
        le=10000,
        unit="chars",
    )
