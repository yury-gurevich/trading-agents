"""Deliberator agent bundle.

Agent: deliberator
Role: expose the fleet-native debate roles for live PM order review.
External I/O: none.
"""

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.settings import DeliberatorSettings

__all__ = ["DeliberatorAgent", "DeliberatorSettings"]
