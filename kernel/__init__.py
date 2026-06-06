"""Kernel — pure plumbing shared by every agent. No trading knowledge lives here.

Agent: kernel
Role: expose the contract descriptors, message envelope, in-process bus,
      AgentBase, the justified-tunable config primitive, and the central fault
      channel. Persistence, graph, distributed bus, and MCP adapters join later.
External I/O: none
"""

from kernel.agent import AgentBase
from kernel.bus import InProcessBus, MessageBus
from kernel.config import AgentSettings, TunableDoc, describe, tunable
from kernel.contract import AgentContract, Capability
from kernel.envelope import AgentMessage, MessageType
from kernel.errors import (
    AgentFault,
    CollectingFaultSink,
    FaultCapture,
    FaultSink,
    fault_boundary,
    fault_from_exception,
)

__all__ = [
    "AgentBase",
    "AgentContract",
    "AgentFault",
    "AgentMessage",
    "AgentSettings",
    "Capability",
    "CollectingFaultSink",
    "FaultCapture",
    "FaultSink",
    "InProcessBus",
    "MessageBus",
    "MessageType",
    "TunableDoc",
    "describe",
    "fault_boundary",
    "fault_from_exception",
    "tunable",
]
