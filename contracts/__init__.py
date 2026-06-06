"""The boundary map — typed messages plus one AgentContract per agent.

Agent: contracts (shared)
Role: the boundary-map registry — loads one AgentContract per agent.
External I/O: none.

Import message types from here, never from another agent. ``registry()`` returns
every agent's contract so tooling (docs, the supervisor gate, MCP binding, tests)
can read the whole boundary map from one place.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel.contract import AgentContract

#: Agent module names, in pipeline-ish order. Each module exposes ``CONTRACT``.
AGENT_MODULES = (
    "provider",
    "scanner",
    "analyst",
    "forecaster",
    "portfolio_manager",
    "execution",
    "monitor",
    "reporter",
    "researcher",
    "curator",
    "operator",
    "supervisor",
)


def registry() -> dict[str, AgentContract]:
    """Load and return every agent's CONTRACT keyed by agent name."""
    import importlib

    out: dict[str, AgentContract] = {}
    for mod_name in AGENT_MODULES:
        module = importlib.import_module(f"contracts.{mod_name}")
        contract: AgentContract = module.CONTRACT
        out[contract.name] = contract
    return out
