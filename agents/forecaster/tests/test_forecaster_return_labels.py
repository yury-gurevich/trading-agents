"""Label-row construction tests — no-lookahead feature/forward-return pairs.

Agent: forecaster
Role: verify build_label_rows produces correct pairs, handles short histories,
      and maintains the no-lookahead invariant.
External I/O: none.
"""

from __future__ import annotations

from agents.forecaster.domain.return_labels import LabelRow, build_label_rows

_HORIZONS = (1, 2, 3)
_VOL = 2
_MOM = 3


def _simple_bars(
    ticker: str, closes: tuple[float, ...], *, vol: float = 1.0
) -> dict[str, list[tuple[str, float, float]]]:
    return {
        ticker: [
            (f"2024-01-{i + 1:02d}", c, vol)
            for i, c in enumerate(closes)
        ]
    }


def test_build_label_rows_produces_correct_forward_return() -> None:
    # 10 bars: enough history; forward_days=1
    closes = tuple(float(i + 1) for i in range(10))
    rows = build_label_rows(
        _simple_bars("AAPL", closes),
        forward_days=1,
        horizons=_HORIZONS,
        volatility_window=_VOL,
        momentum_window=_MOM,
    )
    # At index 3 (the first index with enough history for horizons=(1,2,3) + vol=2 +
    # mom=3 → needed = 4 bars), close=4.0; forward close = 5.0 → return = 0.25
    assert any(abs(row.forward_return - 0.25) < 1e-9 for row in rows)


def test_build_label_rows_stops_before_end_of_bars() -> None:
    # With forward_days=2, the last two bars cannot be labelled.
    closes = tuple(float(i + 1) for i in range(10))
    rows = build_label_rows(
        _simple_bars("AAPL", closes),
        forward_days=2,
        horizons=_HORIZONS,
        volatility_window=_VOL,
        momentum_window=_MOM,
    )
    # No row should have as_of_date beyond index 7 (10 bars, forward_days=2 → max i=7)
    assert all(row.as_of_date <= "2024-01-08" for row in rows)


def test_build_label_rows_returns_empty_on_too_few_bars() -> None:
    # 3 bars: not enough for horizons (need 4)
    rows = build_label_rows(
        _simple_bars("AAPL", (1.0, 2.0, 3.0)),
        forward_days=1,
        horizons=_HORIZONS,
        volatility_window=_VOL,
        momentum_window=_MOM,
    )
    assert rows == []


def test_build_label_rows_accumulates_multiple_tickers() -> None:
    closes = tuple(float(i + 1) for i in range(10))
    ticker_bars = {
        "AAPL": [(f"2024-01-{i + 1:02d}", c, 1.0) for i, c in enumerate(closes)],
        "MSFT": [(f"2024-01-{i + 1:02d}", c, 1.0) for i, c in enumerate(closes)],
    }
    rows = build_label_rows(
        ticker_bars,
        forward_days=1,
        horizons=_HORIZONS,
        volatility_window=_VOL,
        momentum_window=_MOM,
    )
    tickers = {row.ticker for row in rows}
    assert tickers == {"AAPL", "MSFT"}


def test_build_label_rows_label_row_fields_are_set() -> None:
    closes = tuple(float(i + 1) for i in range(10))
    rows = build_label_rows(
        _simple_bars("AAPL", closes),
        forward_days=1,
        horizons=_HORIZONS,
        volatility_window=_VOL,
        momentum_window=_MOM,
    )
    assert rows
    row = rows[0]
    assert isinstance(row, LabelRow)
    assert row.ticker == "AAPL"
    assert row.as_of_date.startswith("2024-01-")
    assert len(row.features.as_vector()) == 6
    assert isinstance(row.forward_return, float)


def test_build_label_rows_empty_input() -> None:
    assert build_label_rows({}, forward_days=1, horizons=_HORIZONS,
                             volatility_window=_VOL, momentum_window=_MOM) == []
