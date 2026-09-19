"""FMP VIX regime source tests.

Agent: provider
Role: verify FMP ^VIX parsing, freshness, failure containment, and credential hygiene.
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from types import MethodType

import pytest

from agents.provider.fmp_vix import FMPVixSource


def _stub(payload: str | BaseException) -> FMPVixSource:
    source = FMPVixSource(api_key="k", base_url="https://fmp.test", timeout=10)

    def fake_download(_self: FMPVixSource) -> str:
        if isinstance(payload, BaseException):
            raise payload
        return payload

    source._download = MethodType(fake_download, source)  # type: ignore[method-assign]
    return source


def test_fmp_vix_uses_same_session_bar_as_measured() -> None:
    """PROV-OUT-02: same-session FMP ^VIX close is MEASURED regime evidence."""
    inputs = _stub(
        '[{"date":"2026-09-14","price":14.3},{"date":"2026-09-13","price":99.0}]'
    ).fetch_regime_inputs(date(2026, 9, 14))

    assert inputs.vix == 14.3
    assert inputs.vix_status == "measured"
    assert inputs.vix_as_of == date(2026, 9, 14)
    assert inputs.vix_reason is None


def test_fmp_vix_marks_one_session_old_bar_as_prior_session() -> None:
    """PROV-OUT-02 / PROV-OUT-03: one-session-old ^VIX is explicit DEGRADED input."""
    inputs = _stub('[{"date":"2026-09-11","price":21.0}]').fetch_regime_inputs(
        date(2026, 9, 14)
    )

    assert inputs.vix == 21.0
    assert inputs.vix_status == "prior_session"
    assert inputs.vix_as_of == date(2026, 9, 11)
    assert inputs.vix_reason == "prior_session"


def test_fmp_vix_marks_multi_session_old_bar_as_missing() -> None:
    """PROV-OUT-03 / PROV-NEV-01: stale ^VIX is flagged missing, not clean data."""
    inputs = _stub('[{"date":"2026-09-10","price":22.0}]').fetch_regime_inputs(
        date(2026, 9, 14)
    )

    assert inputs.vix is None
    assert inputs.vix_status == "missing"
    assert inputs.vix_as_of is None
    assert inputs.vix_reason == "stale_vix_bar"


def test_fmp_vix_ignores_future_bars() -> None:
    """PROV-OUT-02 / PROV-NEV-07: future ^VIX bars never become present evidence."""
    inputs = _stub(
        '[{"date":"2026-09-15","price":99.0},{"date":"2026-09-14","price":14.0}]'
    ).fetch_regime_inputs(date(2026, 9, 14))

    assert inputs.vix == 14.0
    assert inputs.vix_status == "measured"
    assert inputs.vix_as_of == date(2026, 9, 14)


def test_fmp_vix_historical_payload_filters_bad_rows_and_future_only() -> None:
    """PROV-OUT-02 / PROV-NEV-07: historical payloads are parsed without invention."""
    inputs = _stub(
        '{"historical":["bad",{"date":"2026-09-14","close":-1.0},'
        '{"date":"2026-09-15","close":19.0}]}'
    ).fetch_regime_inputs(date(2026, 9, 14))

    assert inputs.vix is None
    assert inputs.vix_status == "missing"
    assert inputs.vix_reason == "invalid_vix_payload"


def test_fmp_vix_historical_payload_accepts_close_field() -> None:
    """PROV-OUT-02: FMP historical payloads may name the VIX close as `close`."""
    inputs = _stub(
        '{"historical":[{"date":"2026-09-14","close":14.8}]}'
    ).fetch_regime_inputs(date(2026, 9, 14))

    assert inputs.vix == 14.8
    assert inputs.vix_status == "measured"


def test_fmp_vix_counts_holidays_as_non_sessions() -> None:
    """PROV-OUT-02: freshness uses trading sessions, excluding NYSE holidays."""
    inputs = _stub('[{"date":"2026-09-04","price":18.0}]').fetch_regime_inputs(
        date(2026, 9, 8)
    )

    assert inputs.vix == 18.0
    assert inputs.vix_status == "prior_session"
    assert inputs.vix_as_of == date(2026, 9, 4)


@pytest.mark.parametrize(
    "payload",
    [
        RuntimeError("HTTP 500"),
        "not-json",
        "42",
        '{"historical":{}}',
        "[]",
        '[{"date":"2026-09-14","price":"n/a"}]',
    ],
)
def test_fmp_vix_failures_return_missing_without_raising(
    payload: str | BaseException,
) -> None:
    """PROV-FAIL-01 / PROV-OUT-03: FMP ^VIX failures degrade in-band."""
    inputs = _stub(payload).fetch_regime_inputs(date(2026, 9, 14))

    assert inputs.vix is None
    assert inputs.vix_status == "missing"
    assert inputs.vix_as_of is None
    assert inputs.vix_reason in {"vix_fetch_failed", "invalid_vix_payload"}


def test_fmp_vix_failure_reason_does_not_expose_api_key() -> None:
    """PROV-NEV-04 / PROV-SEC-02: FMP ^VIX failure output never leaks credentials."""
    token = "super-secret-fmp-token"  # noqa: S105 - fake leak sentinel.
    source = FMPVixSource(api_key=token, base_url="https://fmp.test", timeout=10)

    def fake_download(_self: FMPVixSource) -> str:
        raise RuntimeError(f"https://fmp.test/path?apikey={token}")

    source._download = MethodType(fake_download, source)  # type: ignore[method-assign]

    inputs = source.fetch_regime_inputs(date(2026, 9, 14))

    assert inputs.vix_status == "missing"
    assert token not in str(inputs)
