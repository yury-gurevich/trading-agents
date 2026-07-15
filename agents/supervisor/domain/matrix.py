"""Supervisor capability matrix.

Agent: supervisor
Role: declare P5 routing availability without executing routed capabilities.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RouteSpec:
    """One intent-family routing entry."""

    agent: str | None
    capability: str | None
    available: bool

    @property
    def routed_to(self) -> str | None:
        """Return the bus target string when the route is available."""
        if self.agent is None or self.capability is None:
            return None
        return f"{self.agent}.{self.capability}"


CAPABILITY_MATRIX: dict[str, RouteSpec] = {
    "status": RouteSpec("reporter", "report", True),
    "explain": RouteSpec("reporter", "narrative", True),
    "run": RouteSpec("orchestration", "execute_run", True),
    "approve": RouteSpec("supervisor", "resolve_flag", True),
    "reject": RouteSpec(None, None, False),
    "modify": RouteSpec(None, None, False),
    "mode": RouteSpec(None, None, False),
    "stage": RouteSpec("execution", "promote_stage", True),
    "pause": RouteSpec(None, None, False),
    "resume": RouteSpec("orchestration", "resume_run", True),
}

BUILD_PHASES = {
    "reject": "P7",
    "modify": "P7",
    "mode": "P8",
    "pause": "P8",
}


def not_available_reason(family: str) -> str:
    """Return the build-phase refusal for an unavailable family."""
    phase = BUILD_PHASES[family]
    return f"not available in current build phase: {family} requires {phase}"
