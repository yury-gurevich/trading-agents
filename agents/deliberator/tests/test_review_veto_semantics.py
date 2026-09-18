"""Deliberator verdict-to-veto semantics tests.

Agent: deliberator
Role: prove only overturn verdicts enter the execution-blocking veto list.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import cast

from agents.deliberator.review_batch import ReviewBatch, review_approved_orders
from agents.deliberator.review_record import OrderReview
from contracts.common import Explanation, Money
from contracts.portfolio_manager import OrderIntent


def test_revise_records_finding_without_vetoing_order() -> None:
    """DLIB-OUT-02 / DLIB-OUT-04: revise is recorded but does not veto."""
    batch = _batch({"USB": "revise", "WFC": "revise", "AMZN": "uphold"})
    usb_debate = cast("dict[str, object]", batch.debates["USB"])
    wfc_debate = cast("dict[str, object]", batch.debates["WFC"])

    assert batch.vetoed_tickers == []
    assert batch.verdicts == {"USB": "revise", "WFC": "revise", "AMZN": "uphold"}
    assert usb_debate["rationale"] == "USB rationale"
    assert wfc_debate["verdict"] == "revise"


def test_overturn_still_vetoes_order() -> None:
    """DLIB-OUT-02 / DLIB-OUT-04: overturn remains the blocking verdict."""
    batch = _batch({"USB": "overturn", "WFC": "uphold"})

    assert batch.vetoed_tickers == ["USB"]
    assert batch.verdicts == {"USB": "overturn", "WFC": "uphold"}


def test_mixed_verdicts_veto_only_overturned_ticker() -> None:
    """DLIB-OUT-02 / DLIB-OUT-04: revise stays visible outside vetoed_tickers."""
    batch = _batch({"USB": "overturn", "WFC": "revise", "AMZN": "uphold"})

    assert batch.vetoed_tickers == ["USB"]
    assert batch.verdicts["WFC"] == "revise"
    assert "WFC" not in batch.vetoed_tickers


def _batch(verdicts: dict[str, str]) -> ReviewBatch:
    approved = tuple(_intent(ticker) for ticker in verdicts)

    def review_one(intent: OrderIntent) -> OrderReview:
        return OrderReview(
            verdicts[intent.ticker], f"{intent.ticker} rationale", (), ()
        )

    return review_approved_orders(approved, concurrency=1, review_one=review_one)


def _intent(ticker: str) -> OrderIntent:
    return OrderIntent(
        ticker=ticker,
        action="buy",
        quantity=1,
        est_price=Money(amount=Decimal("100.00")),
        rationale=Explanation(summary=f"{ticker} fixture"),
    )
