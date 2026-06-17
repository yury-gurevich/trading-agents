"""Finnhub response parsers — pure, never-raising JSON extractors.

Agent: provider
Role: extract metrics, sector, and headlines from Finnhub JSON payloads.
External I/O: none.
"""

from __future__ import annotations

import json

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
