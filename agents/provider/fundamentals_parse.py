"""Finnhub response parsers — pure, never-raising JSON extractors.

Agent: provider
Role: extract metrics, sector, headlines, and next-earnings date from Finnhub JSON.
External I/O: none.
"""

from __future__ import annotations

import json
from datetime import date

# Fixed Finnhub /stock/metric field names (the union of primary + fallback keys the
# analyst reads). These are API field identifiers, not tunable policy.
_FUNDAMENTAL_KEYS: tuple[str, ...] = (
    "peBasicExclExtraTTM",
    "peTTM",
    "roeTTM",
    "netProfitMarginTTM",
    "currentRatioQuarterly",
    "pbQuarterly",
    "pbAnnual",
    "totalDebt/totalEquityQuarterly",
    "totalDebt/totalEquityAnnual",
    "epsGrowthTTMYoy",
    "revenueGrowthTTMYoy",
)


def _parse_metrics(raw_json: str) -> dict[str, float]:
    """Extract float-coercible target keys from a Finnhub metric response."""
    payload = json.loads(raw_json)
    metric = payload.get("metric") if isinstance(payload, dict) else None
    if not isinstance(metric, dict):
        return {}
    out: dict[str, float] = {}
    for key in _FUNDAMENTAL_KEYS:
        value = metric.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        out[key] = float(value)
    return out


def _parse_sector(raw_json: str) -> str | None:
    """Extract ``finnhubIndustry`` from a /stock/profile2 response; None if absent.

    Never raises; returns None for any malformed, empty, or non-string payload.
    """
    try:
        payload = json.loads(raw_json)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    industry = payload.get("finnhubIndustry")
    if not isinstance(industry, str) or not industry:
        return None
    return industry


def _parse_next_earnings(raw_json: str, on_or_after: date) -> date | None:
    """Return the earliest earnings date on/after ``on_or_after``, or None.

    Parses a Finnhub ``/calendar/earnings`` response. Never raises; returns None for
    any malformed/empty payload or when no upcoming date is present.
    """
    try:
        payload = json.loads(raw_json)
    except (json.JSONDecodeError, ValueError):
        return None
    calendar = payload.get("earningsCalendar") if isinstance(payload, dict) else None
    if not isinstance(calendar, list):
        return None
    upcoming: list[date] = []
    for item in calendar:
        if not isinstance(item, dict):
            continue
        parsed = _parse_iso_date(item.get("date"))
        if parsed is not None and parsed >= on_or_after:
            upcoming.append(parsed)
    return min(upcoming) if upcoming else None


def _parse_iso_date(value: object) -> date | None:
    """Coerce an ISO ``YYYY-MM-DD`` string to a date; None on anything else."""
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_news(raw_json: str, cap: int) -> tuple[str, ...]:
    """Extract headline strings from a Finnhub /company-news response array.

    Never raises; returns an empty tuple for any malformed or empty payload.
    Newest-first order is preserved (Finnhub returns articles newest-first).
    """
    try:
        payload = json.loads(raw_json)
    except (json.JSONDecodeError, ValueError):
        return ()
    if not isinstance(payload, list):
        return ()
    headlines: list[str] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        headline = item.get("headline")
        if not isinstance(headline, str) or not headline:
            continue
        headlines.append(str(headline))
        if len(headlines) >= cap:
            break
    return tuple(headlines)
