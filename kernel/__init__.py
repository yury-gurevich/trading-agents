"""Kernel — pure plumbing shared by every agent. No trading knowledge lives here.

Agent: kernel
Role: expose the contract descriptors, message envelope, in-process bus,
      AgentBase, the justified-tunable config primitive, and the central fault
      channel. Distributed bus, observability, and MCP adapters join later.
External I/O: none
"""

from kernel.agent import AgentBase
from kernel.bus import EventHandler, InProcessBus, MessageBus
from kernel.bus_azure import AzureServiceBusBus
from kernel.bus_azure_config import AzureServiceBusSettings
from kernel.bus_celery import CeleryBus
from kernel.bus_celery_config import CeleryBusSettings
from kernel.claim_check import ReadyEvent, claim_check_read, claim_check_write
from kernel.config import AgentSettings, TunableDoc, describe, tunable
from kernel.contract import AgentContract, Capability
from kernel.deliberation import (
    DebateResult,
    Proposition,
    Turn,
    Verdict,
    deliberate,
)
from kernel.deliberation_eval import (
    EvalCase,
    EvalScore,
    LLMJudgeScorer,
    pass_rate,
    run_debates,
    run_eval,
    score_debate,
)
from kernel.deliberation_gate import (
    BaselineCheck,
    check_baseline,
    check_robust,
    pass_fractions,
    passing_names,
    robust_passing,
)
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
    "AzureServiceBusBus",
    "AzureServiceBusSettings",
    "BaselineCheck",
    "Capability",
    "CeleryBus",
    "CeleryBusSettings",
    "CollectingFaultSink",
    "DebateResult",
    "Edge",
    "EvalCase",
    "EvalScore",
    "EventHandler",
    "FakeLLMClient",
    "FaultCapture",
    "FaultSink",
    "GraphSettings",
    "GraphStore",
    "InMemoryGraphStore",
    "InProcessBus",
    "LLMClient",
    "LLMJudgeScorer",
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
    "Proposition",
    "ReadyEvent",
    "TunableDoc",
    "Turn",
    "Verdict",
    "check_baseline",
    "check_robust",
    "claim_check_read",
    "claim_check_write",
    "deliberate",
    "describe",
    "fault_boundary",
    "fault_from_exception",
    "pass_fractions",
    "pass_rate",
    "passing_names",
    "robust_passing",
    "run_debates",
    "run_eval",
    "score_debate",
    "tunable",
]
