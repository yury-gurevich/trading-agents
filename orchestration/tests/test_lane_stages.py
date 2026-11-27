"""Lane work-pair identity and actual in-process choreography.

Agent: orchestration
Role: prove DL-328 D1/D6 with agents' own functions and counting fake models.
External I/O: none; all clients are deterministic and in memory.
"""

import importlib
import os
from datetime import UTC, datetime
from functools import partial

import pytest

from agents.execution.paper_broker import PaperBroker
from orchestration.lane_debate import (
    FAKE_JUDGE_RULING,
    DebateModels,
    fake_debate_models,
)
from orchestration.lane_env import isolate_lane, load_tunables_pack
from orchestration.lane_run import run_lane
from orchestration.lane_stages import STAGE_NAMES, build_stages
from orchestration.tests.lane_fixtures import (
    LANE,
    SAFE_NOW,
    CountingFake,
    guarded_graph,
    provider,
)
from orchestration.tests.lane_fixtures import (
    preserve_environment as preserve_environment,
)


@pytest.fixture(autouse=True)
def lane_environment(preserve_environment: None) -> None:
    """DL-328 D3: settings used in the pipeline come from the isolated pack."""
    os.environ.clear()
    isolate_lane(os.environ, LANE, now=SAFE_NOW, pack=load_tunables_pack())


def test_each_stage_drives_the_function_its_entrypoint_hands_work_loop() -> None:
    """DL-328 D1 / EXEC-IDN-01: lane stages use each deployed work pair unchanged."""
    graph = guarded_graph()
    stages = build_stages(
        graph,
        provider_agent=provider(graph),
        broker=PaperBroker(),
        models=fake_debate_models(),
    )
    assert (
        tuple(s.name for s in stages)
        == STAGE_NAMES
        == (
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
    )
    expected = {
        "provider": ("agents.provider.poll", "find_current_work", "process_work_item"),
        "scanner": ("agents.scanner.entrypoint", "find_pending", "scan_market_node"),
        "analyst": ("agents.analyst.entrypoint", "find_pending", "analyze_scan_node"),
        "portfolio_manager": (
            "agents.portfolio_manager.entrypoint",
            "find_pending",
            "evaluate_analyst_node",
        ),
        "deliberator": ("agents.deliberator.poll", "find_pending", "review_pm_node"),
        "execution": (
            "agents.execution.entrypoint",
            "find_pending_work",
            "process_work_item",
        ),
        "monitor": (
            "agents.monitor.entrypoint",
            "find_pending_work",
            "process_work_item",
        ),
        "reporter": (
            "agents.reporter.entrypoint",
            "find_pending",
            "report_monitor_node",
        ),
    }
    for stage in stages:
        if stage.name == "forecaster":
            module = importlib.import_module("agents.forecaster.entrypoint")
            assert isinstance(stage.process, partial)
            assert stage.process.func is vars(module)["process_work_item"]
            assert (
                stage.process.keywords["capabilities"]
                == vars(module)["DEPLOYED_CAPABILITIES"]
            )
        else:
            path, find, process = expected[stage.name]
            module = importlib.import_module(path)
            assert isinstance(stage.find, partial)
            assert isinstance(stage.process, partial)
            assert stage.find.func is vars(module)[find]
            assert stage.process.func is vars(module)[process]


def test_a_lane_run_passes_acceptance_with_real_debates() -> None:
    """DL-328 D1/D5/D6 / DLIB-OUT-01 / DLIB-OUT-02: real reviews, fake models."""
    graph = guarded_graph()
    models = (
        CountingFake("test lane: defend"),
        CountingFake("test lane: challenge"),
        CountingFake(FAKE_JUDGE_RULING),
    )
    stages = build_stages(
        graph,
        provider_agent=provider(graph),
        broker=PaperBroker(),
        models=DebateModels(*models),
    )
    result = run_lane(
        graph,
        stages,
        tickers=("AAPL", "MSFT"),
        run_id="lane-test",
        as_of=datetime.now(tz=UTC).date(),
        max_rounds=12,
    )
    assert result.acceptance.passed
    assert not any(result.rounds[-1].advanced.values())
    assert len(result.rounds) < 12
    debates = graph.list_nodes("DeliberationRun")
    assert len(debates) == 1
    assert debates[0].props["verdicts"] == {"AAPL": "uphold", "MSFT": "uphold"}
    assert debates[0].props["real_debate_count"] == 2
    assert debates[0].props["failed_open_count"] == 0
    assert (
        len(graph.list_nodes("ExecutionRun")) == len(graph.list_nodes("Snapshot")) == 1
    )
    assert all(model.calls > 0 for model in models)
