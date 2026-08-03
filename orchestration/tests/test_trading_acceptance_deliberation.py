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
    from kernel import LLMClient


class _RaisingLLM:
    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del system, user, tool_schema
        raise RuntimeError("LLM unavailable")


class _TickerFailingLLM:
    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del system, tool_schema
        if "ticker=AAPL" in user:
            raise RuntimeError("AAPL peer unavailable")
        return '{"ruling": "uphold", "rationale": "ok"}'


def _cascade(
    data_source: DataSource,
    tickers: tuple[str, ...],
    run_id: str,
    *,
    with_deliberation: bool,
    deliberation_llm: LLMClient | None = None,
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
                deliberation_llm=deliberation_llm
                or FakeLLMClient(
                    {"DECISION UNDER TEST": '{"ruling": "uphold", "rationale": "ok"}'}
                ),
            )
        )
    else:
        list(cascade_once(graph, provider_agent=agent, broker=PaperBroker()))
    return graph


def test_clean_cascade_is_accepted_with_deliberation_present() -> None:
    """D2 SUP-OBS-01 / DL-70: real deliberation still passes acceptance."""
    graph = _cascade(source(), ("AAPL", "MSFT"), "acc-ok", with_deliberation=True)
    result = accept_run(graph, "acc-ok")
    assert result.passed
    assert result.verdict == "PASS"
    assert len(observe_run(graph, "acc-ok")) == 9
    assert "PASS" in render_acceptance(result)


def test_all_fail_open_deliberation_run_fails_acceptance() -> None:
    """D1 DLIB-NEV-06 / DL-70: 2026-08-02 inert veto shape is FAIL."""
    graph = _cascade(
        source(),
        ("AAPL",),
        "acc-fail-open",
        with_deliberation=True,
        deliberation_llm=_RaisingLLM(),
    )

    result = accept_run(graph, "acc-fail-open")

    assert result.verdict == "FAIL"
    assert not result.passed
    assert any(
        breach.stage == "deliberation" and breach.key == "debate_coverage"
        for breach in result.breaches
    )
    assert any(
        breach.stage == "deliberation" and breach.key == "failed_open_count"
        for breach in result.breaches
    )


def test_mixed_fail_open_deliberation_run_fails_acceptance() -> None:
    """D3 DLIB-NEV-06 / DL-70: any failed-open ticker keeps the gate red."""
    graph = _cascade(
        source(),
        ("AAPL", "MSFT"),
        "acc-mixed-fail-open",
        with_deliberation=True,
        deliberation_llm=_TickerFailingLLM(),
    )

    result = accept_run(graph, "acc-mixed-fail-open")

    assert result.verdict == "FAIL"
    assert any(
        breach.stage == "deliberation" and breach.key == "failed_open_count"
        for breach in result.breaches
    )
    rendered = "\n".join(
        line
        for stage in observe_run(graph, "acc-mixed-fail-open")
        for line in stage.outputs
    )
    assert "failed_open_tickers=AAPL" in rendered


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
