"""PostgreSQL GraphStore infrastructure settings.

Agent: kernel
Role: declare configurable PostgreSQL connection values for the graph backend.
External I/O: none.
"""

from __future__ import annotations

from kernel.config import AgentSettings, tunable


class PostgresGraphSettings(AgentSettings):
    """Infrastructure settings for the PostgreSQL graph store."""

    postgres_dsn: str = tunable(
        "",
        why="PostgreSQL connection string for the graph spine; empty disables PG.",
    )
    postgres_connect_timeout_seconds: float = tunable(
        30.0,
        why=(
            "Allow Neon scale-to-zero cold starts without making bad DSNs hang forever."
        ),
        ge=10.0,
        le=120.0,
        unit="seconds",
    )
