"""FinancialModelingPrep VIX regime source.

Agent: provider
Role: fetch and freshness-classify FMP ^VIX daily bars for regime classification.
External I/O: optional HTTPS calls to financialmodelingprep.com.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from typing import Any

from agents.provider.domain.market_calendar import trading_sessions_between
from agents.provider.sources import RegimeInputs

_VIX_SYMBOL = "^VIX"
_VIX_PATH = "/stable/historical-price-eod/light"
_MEASURED_AGE_SESSIONS = 0
_PRIOR_AGE_SESSIONS = 1


@dataclass(frozen=True)
class _VixBar:
    bar_date: date
    close: float


class FMPVixSource:
    """FMP source that supplies only ^VIX inputs for regime classification."""

    def __init__(self, *, api_key: str, base_url: str, timeout: int) -> None:
        """Create an FMP VIX source from injected settings."""
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def fetch_regime_inputs(self, as_of: date) -> RegimeInputs:
        """Fetch and classify ^VIX freshness without raising source failures."""
        try:
            payload = json.loads(self._download())
        except Exception:
            return _missing(as_of, reason="vix_fetch_failed")
        bars = _parse_bars(payload)
        if not bars:
            return _missing(as_of, reason="invalid_vix_payload")
        return _freshest_input(as_of, bars)

    def _download(self) -> str:  # pragma: no cover - exercised by source tests.
        query = urllib.parse.urlencode({"symbol": _VIX_SYMBOL, "apikey": self._api_key})
        with urllib.request.urlopen(  # noqa: S310 - hardcoded HTTPS FMP endpoint.
            f"{self._base_url}{_VIX_PATH}?{query}", timeout=self._timeout
        ) as resp:
            return str(resp.read().decode("utf-8"))


def _parse_bars(payload: object) -> tuple[_VixBar, ...]:
    rows = _rows(payload)
    bars: list[_VixBar] = []
    for row in rows:
        bar = _bar(row)
        if bar is not None:
            bars.append(bar)
    return tuple(sorted(bars, key=lambda bar: bar.bar_date, reverse=True))


def _rows(payload: object) -> tuple[object, ...]:
    if isinstance(payload, list):
        return tuple(payload)
    if isinstance(payload, dict):
        historical = payload.get("historical")
        if isinstance(historical, list):
            return tuple(historical)
    return ()


def _bar(row: object) -> _VixBar | None:
    if not isinstance(row, dict):
        return None
    try:
        bar_date = date.fromisoformat(str(row["date"]))
        close = _close_value(row)
    except (KeyError, TypeError, ValueError):
        return None
    if close < 0.0:
        return None
    return _VixBar(bar_date=bar_date, close=close)


def _close_value(row: dict[str, Any]) -> float:
    if "price" in row:
        return float(row["price"])
    return float(row["close"])


def _freshest_input(as_of: date, bars: tuple[_VixBar, ...]) -> RegimeInputs:
    eligible = tuple(bar for bar in bars if bar.bar_date <= as_of)
    if not eligible:
        return _missing(as_of, reason="invalid_vix_payload")
    newest = eligible[0]
    age_sessions = trading_sessions_between(after=newest.bar_date, through=as_of)
    if age_sessions == _MEASURED_AGE_SESSIONS:
        return RegimeInputs(
            as_of=as_of,
            vix=newest.close,
            vix_status="measured",
            vix_as_of=newest.bar_date,
        )
    if age_sessions == _PRIOR_AGE_SESSIONS:
        return RegimeInputs(
            as_of=as_of,
            vix=newest.close,
            vix_status="prior_session",
            vix_as_of=newest.bar_date,
            vix_reason="prior_session",
        )
    return _missing(as_of, reason="stale_vix_bar")


def _missing(as_of: date, *, reason: str) -> RegimeInputs:
    return RegimeInputs(
        as_of=as_of,
        vix=None,
        vix_status="missing",
        vix_as_of=None,
        vix_reason=reason,
    )
