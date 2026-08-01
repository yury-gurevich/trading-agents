"""Compatibility wrapper for deliberator evidence rendering.

Agent: orchestration
Role: keep local-pipeline imports stable while the renderer lives with the agent.
External I/O: none.
"""

from agents.deliberator.context import build_veto_context

__all__ = ["build_veto_context"]
