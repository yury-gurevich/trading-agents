"""Sector reference-data cache (DRIFT-013 robustness).

Agent: provider
Role: a ticker's sector is slowly-changing REFERENCE data, not market data — fetching
      it live per-ticker from a rate-limited API loses it on a rate-limit (DRIFT-013),
      which silently disables the PM concentration caps. Persist each ticker's sector
      once in the graph and fill the universe's gaps from that cache, so the caps have
      sector data after the first successful fetch — no manual map to keep correct.
External I/O: none directly (the injected GraphStore).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import GraphStore

SECTOR_LABEL = "Sector"


def resolve_sectors(
    graph: GraphStore, live: dict[str, str], universe: tuple[str, ...]
) -> dict[str, str]:
    """Persist newly-seen live sectors, then fill the universe's gaps from the cache.

    First-write-wins: a sector is cached once (sectors essentially never change for an
    established name), so re-ingest never overwrites it — staying clear of the graph's
    append-only immutability (DRIFT-011). Returns ``live`` enriched with cached sectors
    for any requested ticker the live fetch missed.
    """
    for ticker, sector in live.items():
        if graph.get_node(SECTOR_LABEL, f"sector:{ticker}") is None:
            graph.merge_node(
                SECTOR_LABEL, f"sector:{ticker}", {"ticker": ticker, "sector": sector}
            )
    merged = dict(live)
    for ticker in universe:
        if ticker in merged:
            continue
        node = graph.get_node(SECTOR_LABEL, f"sector:{ticker}")
        if node is not None:
            merged[ticker] = str(node.props["sector"])
    return merged
