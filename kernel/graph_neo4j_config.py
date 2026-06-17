"""Neo4j GraphStore infrastructure settings.

Agent: kernel
Role: declare configurable Neo4j connection values for the graph backend.
External I/O: none.
"""

from __future__ import annotations

from kernel.config import AgentSettings, tunable


class GraphSettings(AgentSettings):
    """Infrastructure settings for the Neo4j graph store."""

    neo4j_uri: str = tunable(
        "bolt://localhost:7687", why="Default local Neo4j graph endpoint."
    )
    neo4j_user: str = tunable(
        "neo4j", why="Conventional local bootstrap user keeps setup predictable."
    )
    neo4j_password: str = tunable(
        "", why="Provided out-of-band; empty supports unauthenticated tests."
    )
    neo4j_database: str = tunable(
        "neo4j",
        why="Target database name. Aura/Community expose only 'neo4j'; a local "
        "Desktop/Enterprise instance may use a named db (e.g. trading-agent).",
    )
    neo4j_connection_timeout_seconds: float = tunable(
        30.0,
        why="Fail a broken graph connection promptly while allowing local startup lag.",
        ge=1.0,
        le=120.0,
        unit="seconds",
    )
