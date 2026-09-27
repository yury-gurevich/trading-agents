"""Scorecard settings — the window, the autonomy goals and the dispatcher's tick.

Agent: surfaces
Role: declare the unattended scorecard's tunables once, for the tile and the tool.
External I/O: process environment and the repo .env file.

This lives outside `surfaces.dashboard` on purpose: the MCP tool imports it, and
importing anything under `surfaces.dashboard` runs that package's `__init__`, which
imports the chat and so `surfaces.mcp_tools` half-built (DL-225). `DashboardSettings`
inherits this class, so the surfaces `PARAM` table still meets every field (DL-235).
"""

from pydantic_settings import SettingsConfigDict

from kernel.config import AgentSettings, tunable


class ScorecardSettings(AgentSettings):
    """Tunables of the unattended scorecard, shared by the tile and the MCP tool."""

    model_config = SettingsConfigDict(
        env_prefix="dashboard_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    dispatcher_fire_utc: str = tunable(
        "22:30", why="The dispatcher's first placing tick, _ACTION_START (test-pinned)."
    )
    scorecard_window_days: int = tunable(
        30,
        why=(
            "PRD section 10 measures G1 over a rolling 30 days. Every unbriefed run in "
            "the window is judged once per process, about 3 s each, so 90 days caps "
            "the first read near three minutes."
        ),
        ge=1,
        le=90,
        unit="days",
    )
    scorecard_g1_target: float = tunable(
        0.95,
        why="PRD section 10, G1: at least 95 % of scheduled cycles complete.",
        gt=0,
        le=1,
        unit="share of sessions",
    )
    scorecard_g3_target: float = tunable(
        0.20,
        why="PRD section 10, G3: intervention on fewer than 20 % of healthy days.",
        gt=0,
        le=1,
        unit="share of healthy sessions",
    )
    scorecard_clock_sessions: int = tunable(
        20,
        why="P19's exit: 20 consecutive sessions with no human command but reading.",
        ge=1,
        le=60,
        unit="sessions",
    )
