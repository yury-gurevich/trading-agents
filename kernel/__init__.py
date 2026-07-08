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
from kernel.bus_azure_receiver import AzureServiceBusRequestConsumer
from kernel.bus_celery import CeleryBus
from kernel.bus_celery_config import CeleryBusSettings
from kernel.claim_check import ReadyEvent, claim_check_read, claim_check_write
from kernel.config import AgentSettings, TunableDoc, describe, tunable
from kernel.contract import AgentContract, Capability
from kernel.deliberation import (
    CHALLENGER_SYSTEM,
    DEFAULT_DELIBERATION_PROMPTS,
    DEFENDER_SYSTEM,
    JUDGE_SYSTEM,
    DebateResult,
    DeliberationPrompts,
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
from kernel.deliberation_prompt_artifacts import (
    DELIBERATION_ROLE_FILENAMES,
    DELIBERATION_ROLE_TASKS,
    DELIBERATION_ROLES,
    ensure_deliberation_artifact,
    load_deliberation_prompt_artifact,
    load_deliberation_prompt_artifacts,
    load_prompt_artifact,
    parse_prompt_artifact,
    prompts_from_artifacts,
)
from kernel.deliberation_understanding import (
    ParameterTruth,
    UnderstandingScore,
    misread_parameters,
    score_understanding,
    understanding_rate,
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
from kernel.graph_postgres import PostgresGraphStore
from kernel.graph_postgres_config import PostgresGraphSettings
from kernel.llm import FakeLLMClient, LLMClient
from kernel.market_pack import MarketPack, MarketPackRegistry
from kernel.metrics import MeteredFaultSink, Metrics, NullMetrics
from kernel.metrics_prometheus import MetricsSettings, PrometheusMetrics
from kernel.optimizer import PromptArtifact, PromptExample, PromptOptimizer

__all__ = [
    "CHALLENGER_SYSTEM",
    "DEFAULT_DELIBERATION_PROMPTS",
    "DEFENDER_SYSTEM",
    "DELIBERATION_ROLES",
    "DELIBERATION_ROLE_FILENAMES",
    "DELIBERATION_ROLE_TASKS",
    "JUDGE_SYSTEM",
    "AgentBase",
    "AgentContract",
    "AgentFault",
    "AgentMessage",
    "AgentSettings",
    "AzureServiceBusBus",
    "AzureServiceBusRequestConsumer",
    "AzureServiceBusSettings",
    "BaselineCheck",
    "Capability",
    "CeleryBus",
    "CeleryBusSettings",
    "CollectingFaultSink",
    "DebateResult",
    "DeliberationPrompts",
    "Edge",
    "EvalCase",
    "EvalScore",
    "EventHandler",
    "FakeLLMClient",
    "FaultCapture",
    "FaultSink",
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
    "Node",
    "NullMetrics",
    "ParameterTruth",
    "PostgresGraphSettings",
    "PostgresGraphStore",
    "PrometheusMetrics",
    "PromptArtifact",
    "PromptExample",
    "PromptOptimizer",
    "Proposition",
    "ReadyEvent",
    "TunableDoc",
    "Turn",
    "UnderstandingScore",
    "Verdict",
    "check_baseline",
    "check_robust",
    "claim_check_read",
    "claim_check_write",
    "deliberate",
    "describe",
    "ensure_deliberation_artifact",
    "fault_boundary",
    "fault_from_exception",
    "load_deliberation_prompt_artifact",
    "load_deliberation_prompt_artifacts",
    "load_prompt_artifact",
    "misread_parameters",
    "parse_prompt_artifact",
    "pass_fractions",
    "pass_rate",
    "passing_names",
    "prompts_from_artifacts",
    "robust_passing",
    "run_debates",
    "run_eval",
    "score_debate",
    "score_understanding",
    "tunable",
    "understanding_rate",
]
