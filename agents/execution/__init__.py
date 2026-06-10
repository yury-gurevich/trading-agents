"""Execution agent package.

Agent: execution
Role: expose the execution boundary agent.
External I/O: injected Broker and GraphStore backends.
"""

from agents.execution.agent import ExecutionAgent

__all__ = ["ExecutionAgent"]
