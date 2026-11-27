"""Test-lane stages — each agent's own work pair, wired as its entrypoint wires it.

Agent: orchestration
Role: build the nine run-path stages a test-lane run drives in one process (DL-328):
      the ``find``/``process`` pair, settings and fault sink each entrypoint gives
      its ``work_loop``; ``lane_debate`` wires the debate.
External I/O: none (delegates to the injected graph, broker and provider agent).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from functools import partial
from typing import TYPE_CHECKING, Any

from agents.analyst.poll import analyze_scan_node
from agents.analyst.poll import find_pending as analyst_pending
from agents.analyst.settings import AnalystSettings
from agents.execution import poll as execution_poll
from agents.execution.settings import ExecutionSettings
from agents.forecaster import work as forecaster_work
from agents.forecaster.entrypoint import build_served_bus as forecaster_bus
from agents.forecaster.poll import DEPLOYED_CAPABILITIES
from agents.monitor import poll as monitor_poll
from agents.monitor.settings import MonitorSettings
from agents.portfolio_manager.issuer_map import load_issuer_map_from_env
from agents.portfolio_manager.poll import evaluate_analyst_node
from agents.portfolio_manager.poll import find_pending as pm_pending
from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.provider import poll as provider_poll
from agents.reporter.poll import find_pending as reporter_pending
from agents.reporter.poll import report_monitor_node
from agents.scanner.poll import find_pending as scanner_pending
from agents.scanner.poll import scan_market_node
from agents.scanner.settings import ScannerSettings
from kernel import CollectingFaultSink
from kernel.fault_graph import GraphFaultSink
from orchestration.lane_debate import debate_pair

if TYPE_CHECKING:
    from collections.abc import Callable

    from agents.execution.broker import Broker
    from agents.provider.agent import ProviderAgent
    from kernel import GraphStore
    from orchestration.lane_debate import DebateModels

STAGE_NAMES = (
    "provider",
    "scanner",
    "analyst",
    "forecaster",
    "portfolio_manager",
    "deliberator",
    "execution",
    "monitor",
    "reporter",
)
"""The run-path agents in the order a run's work flows; each has a fault sink."""


@dataclass(frozen=True)
class LaneStage:
    """One agent's work pair and its fault-sink flush (empty for unsinked loops)."""

    name: str
    find: Callable[[], list[Any]]
    process: Callable[[Any], None]
    flush: Callable[[], None]


def build_stages(
    graph: GraphStore,
    *,
    provider_agent: ProviderAgent,
    broker: Broker,
    models: DebateModels,
) -> tuple[LaneStage, ...]:
    """Return the run-path stages in ``STAGE_NAMES`` order."""
    sink = {name: GraphFaultSink(graph, CollectingFaultSink()) for name in STAGE_NAMES}
    find_debate, debate = debate_pair(graph, models, sink["deliberator"])
    forecast = partial(
        forecaster_work.process_work_item,
        graph=graph,
        bus=forecaster_bus(graph, sink["forecaster"]),
        capabilities=DEPLOYED_CAPABILITIES,
        sink=sink["forecaster"],
    )
    pairs: dict[str, tuple[Callable[[], list[Any]], Callable[[Any], None]]] = {
        "provider": (
            partial(provider_poll.find_current_work, graph),
            partial(provider_poll.process_work_item, agent=provider_agent),
        ),
        "scanner": (
            partial(scanner_pending, graph),
            partial(scan_market_node, graph=graph, settings=ScannerSettings()),
        ),
        "analyst": (
            partial(analyst_pending, graph),
            partial(
                analyze_scan_node,
                graph=graph,
                settings=AnalystSettings(),
                sink=sink["analyst"],
            ),
        ),
        "forecaster": (
            lambda: forecaster_work.find_pending_work(graph, now=datetime.now(tz=UTC)),
            forecast,
        ),
        "portfolio_manager": (
            partial(pm_pending, graph),
            partial(
                evaluate_analyst_node,
                graph=graph,
                settings=PortfolioManagerSettings(),
                issuer_map=load_issuer_map_from_env(),
                sink=sink["portfolio_manager"],
            ),
        ),
        "deliberator": (find_debate, debate),
        "execution": (
            partial(execution_poll.find_pending_work, graph),
            partial(
                execution_poll.process_work_item,
                graph=graph,
                broker=broker,
                settings=ExecutionSettings(),
                sink=sink["execution"],
            ),
        ),
        "monitor": (
            partial(monitor_poll.find_pending_work, graph),
            partial(
                monitor_poll.process_work_item,
                graph=graph,
                settings=MonitorSettings(),
                sink=sink["monitor"],
            ),
        ),
        "reporter": (
            partial(reporter_pending, graph),
            partial(report_monitor_node, graph=graph),
        ),
    }
    return tuple(
        LaneStage(name, *pairs[name], sink[name].flush) for name in STAGE_NAMES
    )
