"""Curator agent. See mission.md and contracts/curator.py.

Agent: curator
Role: out-of-band data engineering — curate graph-collected data into training-
      ready datasets. Runs alongside trading; never in the decision path.
External I/O: dataset_store

Imports only `kernel` and `contracts` — never another agent.
"""

from agents.curator.agent import CuratorAgent

__all__ = ["CuratorAgent"]
