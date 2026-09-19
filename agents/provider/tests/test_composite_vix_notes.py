"""Composite DataSource regime-note tests.

Agent: provider
Role: verify composite source wrappers drain notes from a distinct regime source.
External I/O: none.
"""

from __future__ import annotations

from agents.provider.composite import CompositeDataSource
from agents.provider.sources import FakeDataSource


class _NotedSource(FakeDataSource):
    def consume_degraded_feed_notes(self) -> tuple[str, ...]:
        return ("vix_degraded",)


def test_composite_drains_distinct_regime_source_notes() -> None:
    price = FakeDataSource()
    funda = FakeDataSource()
    senti = FakeDataSource()
    composite = CompositeDataSource(price, funda, senti, regime_source=_NotedSource())

    assert composite.consume_degraded_feed_notes() == ("vix_degraded",)
