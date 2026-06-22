"""Scanner per-ticker verdict + bypass tests (DL-09 collection side).

Agent: scanner
Role: cover the FilterVerdict record (decision + features per ticker) and the
      bypass_scanner_filter counterfactual that lets a dropped ticker flow downstream.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from agents.scanner.domain.filters import apply_filters
from agents.scanner.settings import ScannerSettings
from contracts.provider import OHLCVBar


def _bar(ticker: str, days_ago: int, close: float) -> OHLCVBar:
    day = datetime.now(tz=UTC).date() - timedelta(days=days_ago)
    open_ = close * 0.99
    return OHLCVBar(
        ticker=ticker,
        bar_date=day,
        open=open_,
        high=max(open_, close) + 1.0,
        low=min(open_, close) - 1.0,
        close=close,
        volume=1_000_000,
    )


def _series(ticker: str, closes: list[float]) -> tuple[OHLCVBar, ...]:
    count = len(closes)
    return tuple(_bar(ticker, count - 1 - i, c) for i, c in enumerate(closes))


def _as_of() -> date:
    return datetime.now(tz=UTC).date()


# WIN rises +16% -> survives; LOSS falls -10% -> dropped by min_relative_strength.
_WIN_LOSS = (*_series("WIN", [100.0, 116.0]), *_series("LOSS", [100.0, 90.0]))


def test_verdicts_record_decision_and_features_per_ticker() -> None:
    survivors, trace = apply_filters(
        ("WIN", "LOSS"), _WIN_LOSS, (), {}, _as_of(), ScannerSettings()
    )
    assert {s.ticker for s in survivors} == {"WIN"}
    by = {v.ticker: v for v in trace.verdicts}
    assert by["WIN"].decision == "survived"
    assert by["WIN"].filter_fired is None
    assert by["WIN"].features["relative_strength"] > 0
    assert by["LOSS"].decision == "dropped"
    assert by["LOSS"].filter_fired == "min_relative_strength"
    assert by["LOSS"].bypassed is False
    # The dropped ticker's features are still recorded — the training input.
    assert by["LOSS"].features["relative_strength"] < 0


def test_bypass_lets_dropped_ticker_flow_with_a_bypassed_verdict() -> None:
    settings = ScannerSettings(bypass_scanner_filter=True)
    survivors, trace = apply_filters(
        ("WIN", "LOSS"), _WIN_LOSS, (), {}, _as_of(), settings
    )
    # Both flow downstream now, but LOSS's verdict still records the real drop.
    assert {s.ticker for s in survivors} == {"WIN", "LOSS"}
    by = {v.ticker: v for v in trace.verdicts}
    assert by["LOSS"].decision == "dropped"
    assert by["LOSS"].filter_fired == "min_relative_strength"
    assert by["LOSS"].bypassed is True
    # The drop is still counted even though the ticker flowed through.
    assert trace.dropped_by_filter == {"min_relative_strength": 1}


def test_missing_history_ticker_gets_a_dropped_verdict_and_no_bypass() -> None:
    settings = ScannerSettings(bypass_scanner_filter=True)
    survivors, trace = apply_filters(
        ("ONE",), _series("ONE", [100.0]), (), {}, _as_of(), settings
    )
    assert survivors == ()  # bypass cannot rescue a ticker with no history
    verdict = trace.verdicts[0]
    assert verdict.ticker == "ONE"
    assert verdict.decision == "dropped"
    assert verdict.filter_fired == "missing_history"
    assert verdict.features == {}
