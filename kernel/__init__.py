"""Kernel — pure plumbing shared by every agent. No trading knowledge lives here.

Agent: kernel
Role: expose the contract descriptors, message envelope, in-process bus,
      AgentBase, the justified-tunable config primitive, and the central fault
      channel. Distributed bus, observability, and MCP adapters join later.
External I/O: none
"""

from kernel.agent import AgentBase
from kernel.bus import InProcessBus, MessageBus
from kernel.bus_celery import CeleryBus
from kernel.bus_celery_config import CeleryBusSettings
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
from kernel.graph import Edge, GraphStore, Node
from kernel.graph_memory import InMemoryGraphStore
from kernel.graph_neo4j import Neo4jGraphStore
from kernel.graph_neo4j_config import GraphSettings
from kernel.llm import FakeLLMClient, LLMClient
from kernel.market_pack import MarketPack, MarketPackRegistry
from kernel.metrics import MeteredFaultSink, Metrics, NullMetrics
from kernel.metrics_prometheus import MetricsSettings, PrometheusMetrics

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
    "FakeLLMClient",
    "FaultCapture",
    "FaultSink",
    "GraphSettings",
    "GraphStore",
    "InMemoryGraphStore",
    "InProcessBus",
    "LLMClient",
    "MarketPack",
    "MarketPackRegistry",
    "MessageBus",
    "MessageType",
    "MeteredFaultSink",
    "Metrics",
    "MetricsSettings",
    "Neo4jGraphStore",
    "Node",
    "NullMetrics",
    "PrometheusMetrics",
    "TunableDoc",
    "describe",
    "fault_boundary",
    "fault_from_exception",
    "tunable",
]
