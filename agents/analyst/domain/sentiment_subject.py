"""Which served headlines are about the ticker's own company, and their sentiment.

Agent: analyst
Role: score only the headlines that name a ticker's company (ANLZ-OUT-11, DL-308).
External I/O: none (reads the company table bundled under domain/data).
"""

from __future__ import annotations

import json
import re
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

from agents.analyst.domain.sentiment_rules import score_sentiment

if TYPE_CHECKING:
    from collections.abc import Mapping

COMPANY_NAMES_FILE = Path(__file__).parent / "data" / "company_names.json"


def load_company_names(path: Path = COMPANY_NAMES_FILE) -> dict[str, tuple[str, ...]]:
    """Read the company table: ticker -> the names headlines use for it."""
    raw: dict[str, list[str]] = json.loads(path.read_text(encoding="utf-8"))
    return {ticker: tuple(names) for ticker, names in raw.items()}


COMPANY_NAMES: dict[str, tuple[str, ...]] = load_company_names()


@cache
def _own_pattern(ticker: str) -> re.Pattern[str] | None:
    """A name from the table, or a ticker mark: ``$T``, ``(T)``, ``NYSE:T``."""
    names = COMPANY_NAMES.get(ticker)
    if names is None:
        return None
    mark = re.escape(ticker)
    named = [
        rf"(?<![A-Za-z0-9$])(?<!Price )(?<!price ){re.escape(name)}(?![a-z])"
        for name in names
    ]
    marks = [rf"\${mark}\b", rf"\({mark}\)", rf"\b[A-Z]{{2,}}:\s?{mark}\b"]
    return re.compile("|".join(named + marks))


def own_headlines(ticker: str, headlines: tuple[str, ...]) -> tuple[str, ...] | None:
    """The headlines naming the ticker's company; None when the table lacks it."""
    pattern = _own_pattern(ticker)
    if pattern is None:
        return None
    return tuple(headline for headline in headlines if pattern.search(headline))


def subject_sentiment(
    ticker: str,
    headlines: tuple[str, ...],
    min_own: int,
    *,
    headline_weights: Mapping[str, float] | None = None,
) -> tuple[float | None, dict[str, float]]:
    """Score the ticker's own headlines; no pillar below ``min_own`` scored ones.

    A ticker the company table does not list is scored on every served headline,
    as before DL-308, and ``sentiment_subject_filtered`` reads 0. Names with no
    served news return ``(None, {})`` exactly as ``score_sentiment`` does.
    """
    if not headlines:
        return None, {}
    own = own_headlines(ticker, headlines)
    scored = headlines if own is None else own
    counts = {
        "sentiment_served_headlines": float(len(headlines)),
        "sentiment_own_headlines": float(len(scored)),
        "sentiment_subject_filtered": 0.0 if own is None else 1.0,
    }
    raw, metrics = score_sentiment(scored, headline_weights=headline_weights)
    if raw is None or (own is not None and metrics["sentiment_articles"] < min_own):
        return None, counts
    return raw, {**metrics, **counts}
