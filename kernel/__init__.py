"""Kernel — pure plumbing shared by every agent. No trading knowledge lives here.

Agent: kernel
Role: expose the contract descriptors, the message envelope, the justified-tunable
      config primitive, and the central fault channel. Bus, persistence, graph and
      MCP adapters join this package as runtime is wired.
External I/O: none
"""

from kernel.config import AgentSettings, TunableDoc, describe, tunable
from kernel.contract import AgentContract, Capability
from kernel.envelope import AgentMessage, MessageType
from kernel.errors import (
    AgentFault,
    CollectingFaultSink,
    FaultSink,
    fault_boundary,
    fault_from_exception,
)

__all__ = [
    "AgentContract",
    "AgentFault",
    "AgentMessage",
    "AgentSettings",
    "Capability",
    "CollectingFaultSink",
    "FaultSink",
    "MessageType",
    "TunableDoc",
    "describe",
    "fault_boundary",
    "fault_from_exception",
    "tunable",
]
