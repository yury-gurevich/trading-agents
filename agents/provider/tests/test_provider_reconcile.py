"""Provider law-reconciliation tests (DRIFT-006 benchmark field, DRIFT-007 authz).

Agent: provider
Role: prove the two reconciled provider laws — the benchmark is a requested field
      fetched in isolation, and the capability gate refuses unauthorized callers.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

from agents.provider import ProviderAgent
from agents.provider.sources import FakeDataSource
from contracts.provider import OHLCVBar
from kernel import AgentMessage, InMemoryGraphStore, InProcessBus


def _bar(ticker: str, day: int, *, close: float = 101.0) -> OHLCVBar:
    return OHLCVBar(
        ticker=ticker,
        bar_date=date(2026, 1, day),
        open=100.0,
        high=close + 1.0,
        low=99.0,
        close=close,
        volume=1000,
    )


def _market_payload(**extra: object) -> dict[str, object]:
    return {
        "tickers": ("AAPL",),
        "window": {"start": date(2026, 1, 1), "end": date(2026, 1, 3)},
        **extra,
    }


def _message(sender: str, payload: dict[str, object]) -> AgentMessage:
    return AgentMessage(
        sender=sender,
        recipient="provider",
        message_type="request",
        capability="get_market_data",
        payload=payload,
    )


def test_benchmark_is_served_as_a_field_without_tainting_candidate_quality() -> None:
    """PROV-OUT-01: the benchmark series rides the request as its own field.

    Reconciles DRIFT-006: the benchmark is a requested field (not a side request),
    fetched in isolation so candidate quality stays clean.
    """
    bus = InProcessBus()
    ProviderAgent(
        bus,
        graph=InMemoryGraphStore(),
        source=FakeDataSource(
            bars=(_bar("AAPL", 1), _bar("AAPL", 2), _bar("SPY", 1), _bar("SPY", 2))
        ),
    ).bind()

    payload = _market_payload(fields=("ohlcv", "benchmark"), benchmark_ticker="SPY")
    response = bus.request(_message("analyst", payload))

    assert response.message_type == "response"
    assert {bar["ticker"] for bar in response.payload["benchmark"]} == {"SPY"}
    assert {bar["ticker"] for bar in response.payload["bars"]} == {"AAPL"}
    assert response.payload["quality"]["used_fallback"] is False


def test_unauthorized_caller_is_refused_by_the_capability_gate() -> None:
    """PROV-SEC-07: a caller absent from the capability matrix is refused, unserved."""
    bus = InProcessBus()
    ProviderAgent(
        bus,
        graph=InMemoryGraphStore(),
        source=FakeDataSource(bars=(_bar("AAPL", 1),)),
    ).bind()

    # 'operator' is not in get_market_data's allowed_callers.
    response = bus.request(_message("operator", _market_payload()))

    assert response.message_type == "error"
    assert response.payload["error_type"] == "Unauthorized"
