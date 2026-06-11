"""P4 scheduler tests.

Agent: orchestration
Role: prove triggers are factories and agents stay idle until a run is messaged.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from agents.execution.broker import PaperBroker
from agents.provider.sources import FakeDataSource
from kernel import InMemoryGraphStore, InProcessBus
from orchestration import Dispatcher, RunScheduler
from orchestration.settings import OrchestratorSettings
from orchestration.tests.helpers import fixture_universe


def test_run_scheduler_make_trigger_uses_settings_and_date() -> None:
    scheduler = RunScheduler(settings=OrchestratorSettings(universe="fixture"))
    trigger = scheduler.make_trigger("daily-2026-06-11", date(2026, 6, 11))
    assert trigger.run_id == "daily-2026-06-11"
    assert trigger.universe == "fixture"
    assert trigger.as_of == date(2026, 6, 11)


def test_run_scheduler_default_date_is_today() -> None:
    trigger = RunScheduler().make_trigger("daily-today")
    assert trigger.as_of == datetime.now(tz=UTC).date()


def test_dispatcher_construction_leaves_agents_idle_until_messaged() -> None:
    graph = InMemoryGraphStore()
    Dispatcher(
        InProcessBus(),
        graph,
        source=FakeDataSource(),
        broker=PaperBroker(),
        universe_source=fixture_universe(),
    )
    assert graph._nodes == {}
