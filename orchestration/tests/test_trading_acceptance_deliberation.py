"""Trading acceptance tests for the declared deliberation stage.

Agent: orchestration
Role: prove a declared deliberation stage cannot disappear behind a PASS.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.paper_broker import PaperBroker
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from kernel import FakeLLMClient, InMemoryGraphStore, InProcessBus
from orchestration.local_pipeline import cascade_once
from orchestration.packs.trading_acceptance import accept_run, render_acceptance
from orchestration.packs.trading_observatory import observe_run
from orchestration.start import place_run_request
from orchestration.tests.helpers import source

if TYPE_CHECKING:
    from agents.provider.sources import DataSource


def _cascade(
    data_source: DataSource,
    tickers: tuple[str, ...],
    run_id: str,
    *,
    with_deliberation: bool,
) -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    agent = ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=data_source,
        settings=ProviderSettings(max_staleness_days=7),
    )
    place_run_request(graph, run_id=run_id, tickers=tickers)
    if with_deliberation:
        list(
            cascade_once(
                graph,
                provider_agent=agent,
                broker=PaperBroker(),
                deliberation_llm=FakeLLMClient(
                    {"DECISION UNDER TEST": '{"ruling": "uphold", "rationale": "ok"}'}
                ),
            )
        )
    else:
        list(cascade_once(graph, provider_agent=agent, broker=PaperBroker()))
    return graph


def test_clean_cascade_is_accepted_with_deliberation_present() -> None:
    """SUP-OBS-01 / DL-70: full cascade is accepted with deliberation present."""
    graph = _cascade(source(), ("AAPL", "MSFT"), "acc-ok", with_deliberation=True)
    result = accept_run(graph, "acc-ok")
    assert result.passed
    assert result.verdict == "PASS"
    assert len(observe_run(graph, "acc-ok")) == 9
    assert "PASS" in render_acceptance(result)


def test_declared_deliberation_stage_absence_fails_acceptance() -> None:
    """DL-57 / DL-70: a declared stage that writes nothing must fail visibly."""
    graph = _cascade(
        source(), ("AAPL", "MSFT"), "acc-no-delib", with_deliberation=False
    )

    result = accept_run(graph, "acc-no-delib")

    assert result.verdict == "FAIL"
    assert not result.passed
    assert any(
        breach.stage == "deliberation" and breach.detail == "NOT REACHED"
        for breach in result.breaches
    )
