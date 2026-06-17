"""Forecaster agent package. Charter: mission.md. Boundary: contracts/forecaster.py.

Agent: forecaster
Role: expose the advisory shadow-ML forecaster boundary agent.
External I/O: none. Imports only `kernel` and `contracts` — never another agent.
"""

from agents.forecaster.agent import ForecasterAgent

__all__ = ["ForecasterAgent"]
