"""Deliberator fail-open reason tests.

Agent: deliberator
Role: prove fail-open reviews preserve the real captured failure cause.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.poll import review_pm_node
from agents.deliberator.review_record import failed_open_reason
from agents.deliberator.store import DELIBERATION_RUN_LABEL
from agents.deliberator.tests.test_deliberator_agent import _pm_node, _settings
from kernel import FakeLLMClient, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from agents.deliberator.settings import DeliberatorSettings
    from contracts.deliberator import DebateTurnReply, DebateTurnRequest

_UPHOLD = '{"ruling": "uphold", "rationale": "clears review"}'


class _FailingPeerClient:
    def __init__(self, message: str = "peer unavailable") -> None:
        self.message = message

    def preflight(self, recipients: tuple[str, ...]) -> None:
        del recipients

    def debate_turn(
        self, recipient: str, request: DebateTurnRequest
    ) -> DebateTurnReply:
        del recipient, request
        raise RuntimeError(self.message)


def _manager(graph: InMemoryGraphStore) -> tuple[DeliberatorAgent, DeliberatorSettings]:
    settings = _settings("manager")
    manager = DeliberatorAgent(
        InProcessBus(),
        graph=graph,
        llm=FakeLLMClient({"DECISION UNDER TEST": _UPHOLD}),
        settings=settings,
    )
    return manager, settings


def test_manager_fail_open_records_visible_rationale() -> None:
    """DLIB-FAIL-01 / DLIB-NEV-06 / DLIB-OBS-03: fail-open names why."""
    graph = InMemoryGraphStore()
    pm = _pm_node(graph, "pm-fail")
    manager, settings = _manager(graph)

    review_pm_node(
        pm,
        graph=graph,
        manager=manager,
        peer_client=_FailingPeerClient(),
        settings=settings,
    )

    (run,) = graph.list_nodes(DELIBERATION_RUN_LABEL)
    assert run.props["verdicts"] == {"AAPL": "uphold"}
    assert run.props["vetoed_tickers"] == ()
    assert run.props["real_debate_count"] == 0
    assert run.props["failed_open_count"] == 1
    assert run.props["failed_open_tickers"] == ("AAPL",)
    assert run.props["failed_open_reason"] == "RuntimeError: peer unavailable"
    assert run.props["debates"]["AAPL"]["failed_open"] is True
    assert run.props["debates"]["AAPL"]["rationale"] == (
        "fail-open: RuntimeError: peer unavailable"
    )
    assert "llm unavailable" not in run.props["narrative"]
    assert "fail-open" in run.props["narrative"]


def test_manager_fail_open_records_usage_limit_reason() -> None:
    """DLIB-FAIL-01 / DLIB-OBS-03: API usage limits stay fail-open and named."""
    graph = InMemoryGraphStore()
    pm = _pm_node(graph, "pm-usage-limit")
    manager, settings = _manager(graph)
    message = (
        "Error code: 400 - invalid_request_error "
        '"You have reached your specified API usage limits. '
        'You will regain access on 2026-09-01 at 00:00 UTC."'
    )

    review_pm_node(
        pm,
        graph=graph,
        manager=manager,
        peer_client=_FailingPeerClient(message),
        settings=settings,
    )

    (run,) = graph.list_nodes(DELIBERATION_RUN_LABEL)
    reason = str(run.props["failed_open_reason"])
    assert run.props["verdicts"] == {"AAPL": "uphold"}
    assert run.props["failed_open_count"] == 1
    assert reason.startswith("RuntimeError: Error code: 400")
    assert "2026-09-01" in reason


def test_failed_open_reason_truncates_long_message() -> None:
    reason = failed_open_reason("RuntimeError", "x" * 600)

    assert len(reason) == 500
    assert reason.endswith("...")
