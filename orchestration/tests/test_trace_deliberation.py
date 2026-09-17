"""Trace deliberation rendering tests.

Agent: orchestration
Role: prove traces explain deliberation-withheld orders from recorded graph facts.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from types import MappingProxyType
from typing import TYPE_CHECKING

from contracts.common import Explanation, Money, Provenance
from contracts.portfolio_manager import OrderIntent, OrderIntentSet
from kernel import InMemoryGraphStore, Node
from orchestration.batch_trace import print_trace

if TYPE_CHECKING:
    import pytest


def test_fully_vetoed_trace_explains_withheld_orders(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """DLIB-OUT-02 / EXEC-OUT-09 / LAW-02: vetoed buys explain zero submitted."""
    _patch_nodes(
        monkeypatch,
        approved=("USB", "WFC", "AMZN", "MDLZ"),
        verdicts=MappingProxyType(
            {"USB": "revise", "WFC": "revise", "AMZN": "revise", "MDLZ": "revise"}
        ),
        vetoed=("USB", "WFC", "AMZN", "MDLZ"),
        submitted=0,
    )

    print_trace(InMemoryGraphStore(), "trace-delib")
    out = capsys.readouterr().out
    assert out.index("[pm]") < out.index("[deliberation]") < out.index("[execution]")
    assert "reviewed=4  vetoed=4  status=applied" in out
    assert "tickers=USB,WFC,AMZN,MDLZ" in out
    assert "withheld=4 by deliberation veto" in out


def test_partial_veto_trace_explains_only_matching_gap(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """DLIB-OUT-02 / EXEC-OUT-09 / LAW-02: partial vetoes reconcile by ticker."""
    _patch_nodes(
        monkeypatch,
        approved=("USB", "AMZN", "WFC"),
        verdicts={"USB": "revise", "AMZN": "revise", "WFC": "uphold"},
        vetoed=["USB", "AMZN"],
        submitted=1,
    )

    print_trace(InMemoryGraphStore(), "trace-delib")
    out = capsys.readouterr().out
    assert "reviewed=3  vetoed=2  status=applied" in out
    assert "tickers=USB,AMZN" in out
    assert "withheld=2 by deliberation veto" in out


def test_trace_does_not_invent_veto_cause(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """DLIB-OUT-02 / LAW-02: an unexplained submitted gap gets no veto claim."""
    _patch_nodes(
        monkeypatch,
        approved=("USB", "WFC", "AMZN", "MDLZ"),
        verdicts={"USB": "uphold", "WFC": "uphold", "AMZN": "uphold", "MDLZ": "uphold"},
        vetoed=(),
        submitted=0,
    )

    print_trace(InMemoryGraphStore(), "trace-delib")
    out = capsys.readouterr().out
    assert "vetoed=0" in out
    assert "withheld=" not in out


def test_old_deliberation_row_renders_unknowns(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """DLIB-OUT-02 / LAW-02: missing historical props render without raising."""
    _patch_nodes(
        monkeypatch,
        approved=("USB",),
        verdicts=None,
        vetoed=None,
        submitted=0,
    )

    print_trace(InMemoryGraphStore(), "trace-delib")
    out = capsys.readouterr().out
    assert "reviewed=?  vetoed=?  status=applied" in out
    assert "withheld=" not in out


def test_trace_without_deliberation_keeps_existing_shape(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """LAW-02: a run with no DeliberationRun prints no deliberation section."""
    _patch_nodes(
        monkeypatch,
        approved=("USB",),
        verdicts=None,
        vetoed=None,
        submitted=1,
        include_deliberation=False,
    )

    print_trace(InMemoryGraphStore(), "trace-delib")
    out = capsys.readouterr().out
    assert "[deliberation]" not in out
    assert "[pm]" in out
    assert "[execution]" in out
    assert "approved=1  rejected=0" in out
    assert "submitted=1  rejected=0" in out


def _patch_nodes(
    monkeypatch: pytest.MonkeyPatch,
    *,
    approved: tuple[str, ...],
    verdicts: object,
    vetoed: object,
    submitted: int,
    include_deliberation: bool = True,
) -> None:
    import orchestration.batch_trace as batch_trace

    monkeypatch.setattr(
        batch_trace,
        "walk_chain",
        lambda _graph, _run_id: _trace_nodes(
            approved=approved,
            verdicts=verdicts,
            vetoed=vetoed,
            submitted=submitted,
            include_deliberation=include_deliberation,
        ),
    )


def _trace_nodes(
    *,
    approved: tuple[str, ...],
    verdicts: object,
    vetoed: object,
    submitted: int,
    include_deliberation: bool,
) -> dict[str, Node]:
    nodes = {
        "RunRequest": Node("RunRequest", "run-request:td", {"requested_at": "now"}),
        "PMRun": Node(
            "PMRun",
            "pm-run-trace",
            {"order_intent_set": _order_set(approved).model_dump(mode="json")},
        ),
        "ExecutionRun": Node(
            "ExecutionRun",
            "exec-run-trace",
            {"submitted": submitted, "rejected": 0, "deliberation_status": "applied"},
        ),
    }
    if include_deliberation:
        props = {}
        if verdicts is not None:
            props["verdicts"] = verdicts
        if vetoed is not None:
            props["vetoed_tickers"] = vetoed
        nodes["DeliberationRun"] = Node("DeliberationRun", "delib-run-trace", props)
    return nodes


def _order_set(tickers: tuple[str, ...]) -> OrderIntentSet:
    return OrderIntentSet(
        run_id="pm-run-trace",
        approved=tuple(_intent(ticker) for ticker in tickers),
        rejected=(),
        explanation=Explanation(summary="fixture"),
        provenance=Provenance(run_id="pm-run-trace", source_agent="portfolio_manager"),
    )


def _intent(ticker: str) -> OrderIntent:
    return OrderIntent(
        ticker=ticker,
        action="buy",
        quantity=1,
        est_price=Money(amount=Decimal("100.00")),
        rationale=Explanation(summary="fixture"),
    )
