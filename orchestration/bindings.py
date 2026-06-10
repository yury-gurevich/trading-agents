"""Dispatcher agent binding helpers.

Agent: orchestration
Role: bind the seven paper-loop agents onto an injected message bus.
External I/O: optional provider source and broker ports injected by caller.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.analyst import AnalystAgent
from agents.execution import ExecutionAgent
from agents.execution.broker import PaperBroker
from agents.monitor import MonitorAgent
from agents.portfolio_manager import PortfolioManagerAgent
from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import StooqDataSource
from agents.reporter import ReporterAgent
from agents.scanner import ScannerAgent
from agents.scanner.universe import StaticUniverse

if TYPE_CHECKING:
    from agents.execution.broker import Broker
    from agents.provider.sources import DataSource
    from agents.scanner.universe import UniverseSource
    from kernel import FaultSink, GraphStore, MessageBus
    from orchestration.settings import OrchestratorSettings


def bind_paper_loop_agents(
    bus: MessageBus,
    graph: GraphStore,
    *,
    settings: OrchestratorSettings,
    source: DataSource | None,
    broker: Broker | None,
    universe_source: UniverseSource | None,
    sink: FaultSink,
) -> None:
    """Bind provider through reporter to the injected bus."""
    ProviderAgent(
        bus,
        graph=graph,
        source=source or StooqDataSource(),
        settings=ProviderSettings(
            max_staleness_days=settings.provider_max_staleness_days
        ),
        sink=sink,
    ).bind()
    ScannerAgent(
        bus,
        graph=graph,
        universe=universe_source or StaticUniverse(),
    ).bind()
    AnalystAgent(bus, graph=graph, sink=sink).bind()
    PortfolioManagerAgent(
        bus,
        graph=graph,
        settings=PortfolioManagerSettings(starting_cash=settings.pm_starting_cash),
        sink=sink,
    ).bind()
    ExecutionAgent(
        bus,
        graph=graph,
        broker=broker or PaperBroker(),
        sink=sink,
    ).bind()
    MonitorAgent(bus, graph=graph, sink=sink).bind()
    ReporterAgent(bus, graph=graph, sink=sink).bind()
