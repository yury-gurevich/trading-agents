"""Sector reference-data cache tests (DRIFT-013).

Agent: provider
Role: verify resolve_sectors persists newly-seen sectors, fills the universe's gaps
      from the cache, and never overwrites a cached sector (first-write-wins).
External I/O: none.
"""

from __future__ import annotations

from agents.provider.sector_cache import SECTOR_LABEL, resolve_sectors
from kernel import InMemoryGraphStore


def test_persists_live_sectors_and_returns_them() -> None:
    graph = InMemoryGraphStore()
    out = resolve_sectors(graph, {"AAPL": "Tech", "JPM": "Financials"}, ("AAPL", "JPM"))
    assert out == {"AAPL": "Tech", "JPM": "Financials"}
    node = graph.get_node(SECTOR_LABEL, "sector:AAPL")
    assert node is not None
    assert node.props["sector"] == "Tech"


def test_fills_missing_tickers_from_cache() -> None:
    graph = InMemoryGraphStore()
    resolve_sectors(graph, {"AAPL": "Tech"}, ("AAPL",))  # warm the cache
    # a later run gets NO live sectors, but the universe still includes AAPL.
    out = resolve_sectors(graph, {}, ("AAPL", "MSFT"))
    assert out == {"AAPL": "Tech"}  # AAPL filled from cache; MSFT unknown → absent


def test_first_write_wins_never_overwrites() -> None:
    graph = InMemoryGraphStore()
    resolve_sectors(graph, {"AAPL": "Tech"}, ("AAPL",))
    # a later fetch with a different value must not re-write the cache (or raise).
    out = resolve_sectors(graph, {"AAPL": "Other"}, ("AAPL",))
    assert out == {"AAPL": "Other"}  # this run's live value is returned
    cached = graph.get_node(SECTOR_LABEL, "sector:AAPL")
    assert cached is not None
    assert cached.props["sector"] == "Tech"  # cache unchanged (first-write-wins)
