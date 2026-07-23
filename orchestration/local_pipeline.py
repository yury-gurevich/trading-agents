"""In-process graph-pull cascade — one pass over every agent's poll.

Agent: orchestration
Role: run each agent's `find_pending → process` once, in dependency order, against a
      shared graph. Demonstrates that after the dispatcher's single RunRequest, every
      agent wakes itself off its prerequisite gate with no direct agent-to-agent calls.
      The container fleet does this continuously, one agent per process; this is the
      same logic collapsed into one process for tests and the local demonstrator.
External I/O: none (delegates to the injected provider agent, broker, and graph).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING

from agents.analyst import poll as analyst_poll
from agents.analyst.settings import AnalystSettings
from agents.execution import poll as execution_poll
from agents.execution.settings import ExecutionSettings
from agents.forecaster import poll as forecaster_poll
from agents.forecaster.agent import ForecasterAgent
from agents.monitor import poll as monitor_poll
from agents.portfolio_manager import poll as pm_poll
from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.provider import poll as provider_poll
from agents.reporter import poll as reporter_poll
from agents.scanner import poll as scanner_poll
from agents.scanner.settings import ScannerSettings
from kernel.work_loop import run_once
from orchestration import veto

if TYPE_CHECKING:
    from agents.execution.broker import Broker
    from agents.provider.agent import ProviderAgent
    from kernel import GraphStore, LLMClient


@dataclass(frozen=True)
class StageResult:
    """How many pending items one agent processed in a cascade pass."""

    name: str
    processed: int


def cascade_once(
    graph: GraphStore,
    *,
    provider_agent: ProviderAgent,
    broker: Broker,
    analyst_settings: AnalystSettings | None = None,
    pm_settings: PortfolioManagerSettings | None = None,
    forecaster_agent: ForecasterAgent | None = None,
    deliberation_llm: LLMClient | None = None,
    deliberation_judge_llm: LLMClient | None = None,
) -> tuple[StageResult, ...]:
    """Run one graph-pull pass over every stage in dependency order.

    The forecaster is an RPC agent (FORE-TRG-01), not a pure graph-pull stage: it is
    bound to the provider's bus so its advisory `forecast` reaches `get_market_data`,
    and the forecaster stage triggers it per recommendation. Its shadow predictions are
    a side branch — they never enter the conservation/PM path.

    When ``deliberation_llm`` is given, an **opt-in** challenger-veto stage runs between
    the PM and execution (DL-31 Part B): it debates each approved order and records the
    vetoed (subtracted) set, which execution honours. ``deliberation_judge_llm`` may
    separate the debate Judge from the arguing model. Omitted → no veto stage at all,
    so the deterministic cascade is unchanged.
    """
    scanner_settings = ScannerSettings()
    analyst_settings = analyst_settings or AnalystSettings()
    pm_settings = pm_settings or PortfolioManagerSettings()
    execution_settings = ExecutionSettings()
    bus = provider_agent.bus
    provider_agent.bind()  # so the forecaster's advisory RPC can reach the provider
    forecaster_agent = forecaster_agent or ForecasterAgent(bus, graph=graph)
    forecaster_agent.bind()
    veto_stages = (
        (
            (
                "deliberation",
                partial(veto.find_pending, graph),
                partial(
                    veto.deliberate_pm_node,
                    graph=graph,
                    llm=deliberation_llm,
                    judge_llm=deliberation_judge_llm,
                ),
            ),
        )
        if deliberation_llm is not None
        else ()
    )
    stages = (
        (
            "provider",
            partial(provider_poll.find_pending, graph),
            partial(provider_poll.ingest_run_node, agent=provider_agent),
        ),
        (
            "scanner",
            partial(scanner_poll.find_pending, graph),
            partial(
                scanner_poll.scan_market_node, graph=graph, settings=scanner_settings
            ),
        ),
        (
            "analyst",
            partial(analyst_poll.find_pending, graph),
            partial(
                analyst_poll.analyze_scan_node, graph=graph, settings=analyst_settings
            ),
        ),
        (
            "forecaster",
            partial(forecaster_poll.find_pending, graph),
            partial(forecaster_poll.forecast_analyst_node, graph=graph, bus=bus),
        ),
        (
            "portfolio_manager",
            partial(pm_poll.find_pending, graph),
            partial(pm_poll.evaluate_analyst_node, graph=graph, settings=pm_settings),
        ),
        *veto_stages,
        (
            "execution",
            partial(execution_poll.find_pending, graph),
            partial(
                execution_poll.execute_pm_node,
                graph=graph,
                broker=broker,
                settings=execution_settings,
            ),
        ),
        (
            "monitor",
            partial(monitor_poll.find_pending, graph),
            partial(monitor_poll.monitor_pm_node, graph=graph),
        ),
        (
            "reporter",
            partial(reporter_poll.find_pending, graph),
            partial(reporter_poll.report_monitor_node, graph=graph),
        ),
    )
    return tuple(
        StageResult(name, run_once(find, process)) for name, find, process in stages
    )
