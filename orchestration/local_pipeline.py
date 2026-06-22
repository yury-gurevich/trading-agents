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
from agents.monitor import poll as monitor_poll
from agents.portfolio_manager import poll as pm_poll
from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.provider import poll as provider_poll
from agents.reporter import poll as reporter_poll
from agents.scanner import poll as scanner_poll
from agents.scanner.settings import ScannerSettings
from kernel.work_loop import run_once

if TYPE_CHECKING:
    from agents.execution.broker import Broker
    from agents.provider.agent import ProviderAgent
    from kernel import GraphStore


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
    pm_settings: PortfolioManagerSettings | None = None,
) -> tuple[StageResult, ...]:
    """Run one graph-pull pass over every stage in dependency order."""
    scanner_settings = ScannerSettings()
    analyst_settings = AnalystSettings()
    pm_settings = pm_settings or PortfolioManagerSettings()
    execution_settings = ExecutionSettings()
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
            "portfolio_manager",
            partial(pm_poll.find_pending, graph),
            partial(pm_poll.evaluate_analyst_node, graph=graph, settings=pm_settings),
        ),
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
