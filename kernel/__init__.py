"""Kernel — pure plumbing shared by every agent. No trading knowledge lives here.

Agent: kernel
Role: expose the contract descriptors, message envelope, in-process bus,
      AgentBase, the justified-tunable config primitive, and the central fault
      channel. Distributed bus, observability, and MCP adapters join later.
External I/O: none
"""

from kernel.agent import AgentBase
from kernel.bus import InProcessBus, MessageBus
from kernel.bus_celery import CeleryBus, CeleryBusSettings
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
from kernel.graph import Edge, GraphStore, InMemoryGraphStore, Node
from kernel.graph_neo4j import GraphSettings, Neo4jGraphStore

__all__ = [
    "AgentBase",
    "AgentContract",
    "AgentFault",
    "AgentMessage",
    "AgentSettings",
    "Capability",
    "CeleryBus",
    "CeleryBusSettings",
    "CollectingFaultSink",
    "Edge",
    "FaultCapture",
    "FaultSink",
    "GraphSettings",
    "GraphStore",
    "InMemoryGraphStore",
    "InProcessBus",
    "MessageBus",
    "MessageType",
    "Neo4jGraphStore",
    "Node",
    "TunableDoc",
    "describe",
    "fault_boundary",
    "fault_from_exception",
    "tunable",
]
