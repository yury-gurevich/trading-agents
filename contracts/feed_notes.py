"""Provider feed-degradation note vocabulary helpers.

Agent: contracts
Role: normalize degraded-feed note formats shared by providers and consumers.
External I/O: none.
"""

from __future__ import annotations

_DEGRADED_SUFFIX = "_degraded"


def degraded_feed_name(note: object) -> str | None:
    """Return the feed name for bare or attributed ``*_degraded`` notes."""
    raw = str(note)
    head = raw.split(":", 1)[0]
    if not head.endswith(_DEGRADED_SUFFIX):
        return None
    return head.removesuffix(_DEGRADED_SUFFIX)


def is_degraded_feed_note(note: object) -> bool:
    """Whether *note* describes a degraded optional market-data feed."""
    return degraded_feed_name(note) is not None


def format_degraded_feed_note(
    feed: str, tickers: tuple[str, ...], error_label: str, ticker_cap: int
) -> str:
    """Build a bounded attributed feed note.

    Shape: ``<feed>_degraded:<count>:<first-N-tickers>:<error-label>``.
    """
    shown = ",".join(tickers[: max(1, ticker_cap)])
    return f"{feed}_degraded:{len(tickers)}:{shown}:{error_label}"


def consume_degraded_feed_notes(source: object) -> tuple[str, ...]:
    """Drain optional per-ticker feed notes from a source when it supports them."""
    consumer = getattr(source, "consume_degraded_feed_notes", None)
    if not callable(consumer):
        return ()
    return tuple(str(note) for note in consumer())
