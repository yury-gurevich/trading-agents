"""Deliberator approved-order review batching.

Agent: deliberator
Role: run independent order reviews with bounded fan-out and PM-order assembly.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from agents.deliberator.review_record import (
    OrderReview,
    debate_record,
    transcript_records,
)
from contracts.portfolio_manager import OrderIntent

type ReviewOne = Callable[[OrderIntent], OrderReview]


@dataclass(frozen=True)
class ReviewBatch:
    """Durable DeliberationRun fields assembled in PM-approved order."""

    verdicts: dict[str, str]
    vetoed_tickers: list[str]
    debates: dict[str, object]
    transcript: list[dict[str, object]]
    llm_call_keys: list[str]
    real_debate_count: int
    failed_open_tickers: list[str]
    failed_open_reasons: list[str]


def review_approved_orders(
    approved: tuple[OrderIntent, ...],
    *,
    concurrency: int,
    review_one: ReviewOne,
) -> ReviewBatch:
    """Review approved orders concurrently, then rebuild PM-order fields."""
    reviews = _ordered_reviews(approved, concurrency=concurrency, review_one=review_one)
    return _assemble(tuple(zip(approved, reviews, strict=True)))


def _ordered_reviews(
    approved: tuple[OrderIntent, ...],
    *,
    concurrency: int,
    review_one: ReviewOne,
) -> tuple[OrderReview, ...]:
    if concurrency <= 1 or len(approved) <= 1:
        return tuple(review_one(intent) for intent in approved)
    workers = min(concurrency, len(approved))
    with ThreadPoolExecutor(
        max_workers=workers,
        thread_name_prefix="deliberator-order",
    ) as pool:
        futures = [pool.submit(review_one, intent) for intent in approved]
        return tuple(future.result() for future in futures)


def _assemble(
    ordered: tuple[tuple[OrderIntent, OrderReview], ...],
) -> ReviewBatch:
    verdicts: dict[str, str] = {}
    vetoed: list[str] = []
    debates: dict[str, object] = {}
    transcript: list[dict[str, object]] = []
    llm_call_keys: list[str] = []
    real_debate_count = 0
    failed_open_tickers: list[str] = []
    failed_open_reasons: list[str] = []
    for intent, review in ordered:
        verdicts[intent.ticker] = review.verdict
        debates[intent.ticker] = debate_record(review)
        transcript.extend(transcript_records(intent.ticker, review.turns))
        llm_call_keys.extend(review.llm_call_keys)
        if review.turns:
            real_debate_count += 1
        if review.failed_open:
            failed_open_tickers.append(intent.ticker)
            failed_open_reasons.append(review.failed_open_reason)
        if review.verdict != "uphold":
            vetoed.append(intent.ticker)
    return ReviewBatch(
        verdicts,
        vetoed,
        debates,
        transcript,
        llm_call_keys,
        real_debate_count,
        failed_open_tickers,
        failed_open_reasons,
    )
