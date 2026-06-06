"""Contract descriptors — the machine-readable shape of an agent boundary.

Agent: kernel
Role: the descriptor types every agent boundary is declared in.
External I/O: none.

Pure metadata. NO trading logic, NO imports from agents or contracts. An
``AgentContract`` is the single source of truth for what an agent consumes,
emits, owns, may touch externally, exposes over MCP, and must never do. The same
descriptor is bound to the in-process bus, the Celery bus, and the MCP adapter —
declare the boundary once, bind it many ways.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import BaseModel


@dataclass(frozen=True)
class Capability:
    """One request/response capability an agent answers.

    ``request`` and ``response`` are the typed payload classes (from
    ``contracts``). ``allowed_callers`` empty means "any agent"; a non-empty
    tuple restricts who may invoke this capability — enforced by the supervisor
    gate at runtime, declared here so the restriction is auditable from the map.
    """

    name: str
    summary: str
    request: type[BaseModel]
    response: type[BaseModel]
    mcp: bool = False
    allowed_callers: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentContract:
    """The complete boundary declaration for one agent."""

    name: str
    version: str
    mission: str
    # Capabilities this agent answers (its inbound surface).
    consumes: tuple[Capability, ...] = ()
    # Message/topic names this agent publishes unprompted (notifications).
    emits: tuple[str, ...] = ()
    # Neo4j node/edge labels this agent writes into the provenance graph.
    owns_graph: tuple[str, ...] = ()
    # External systems ONLY this agent may touch (broker, data APIs, LLM provider).
    external_io: tuple[str, ...] = ()
    # Other agents this one depends on — reachable ONLY via messages, never imports.
    depends_on: tuple[str, ...] = ()
    # Capability names exposed as MCP tools.
    mcp_tools: tuple[str, ...] = ()
    # Hard boundaries. Things this agent must never do, stated for the record.
    never: tuple[str, ...] = ()

    def capability(self, name: str) -> Capability:
        """Return the named capability or raise if this agent does not answer it."""
        for cap in self.consumes:
            if cap.name == name:
                return cap
        raise KeyError(f"{self.name} has no capability {name!r}")
