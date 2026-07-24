"""Trace metric formatting tests.

Agent: orchestration
Role: verify trace metric rendering distinguishes measured and unavailable values.
External I/O: none.
"""

from __future__ import annotations

from orchestration.trace_format import metric_text


def test_metric_text_formats_numbers_and_unavailable_values() -> None:
    assert metric_text(2, ".2f") == "2.00"
    assert metric_text(None, ".2f") == "unavailable"
