"""Compatibility wrapper for deliberator PM/regime evidence renderers.

Agent: orchestration
Role: keep local-pipeline tests stable while renderers live with the agent.
External I/O: none.
"""

from agents.deliberator.context_pm import (
    order_lines,
    recommendation_line,
    regime_gate_lines,
)

__all__ = ["order_lines", "recommendation_line", "regime_gate_lines"]
