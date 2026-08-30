"""Scanner settings law-contract tests.

Agent: scanner
Role: prove scanner settings stay aligned with locked scanner PARAM law rows.
External I/O: none; tests in-memory Pydantic settings metadata.
"""

from __future__ import annotations

from agents.analyst.settings import AnalystSettings
from agents.scanner.settings import ScannerSettings
from kernel import describe


def test_benchmark_ticker_is_registered_tunable_with_rationale() -> None:
    """SCAN-PARAM: benchmark_ticker obeys the S187 PARAM YES declaration."""
    scanner_field = ScannerSettings.model_fields["benchmark_ticker"]
    analyst_field = AnalystSettings.model_fields["benchmark_ticker"]

    scanner_doc = next(
        item for item in describe(ScannerSettings) if item.name == "benchmark_ticker"
    )

    assert ScannerSettings().benchmark_ticker == "SPY"
    assert scanner_doc.env_var == "SCANNER_BENCHMARK_TICKER"
    assert scanner_doc.default == "SPY"
    assert scanner_doc.minimum is None
    assert scanner_doc.maximum is None
    assert scanner_field.description
    assert "Relative-strength benchmark" in scanner_field.description
    assert analyst_field.description
