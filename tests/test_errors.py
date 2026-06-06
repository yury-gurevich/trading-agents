"""Central fault channel tests — provenance capture and redirection."""

from __future__ import annotations

import pytest

from kernel import CollectingFaultSink, fault_boundary, fault_from_exception


def test_fault_carries_source_provenance():
    fault = fault_from_exception(
        ValueError("bad input"), agent="analyst", module="analyst.scoring"
    )
    assert fault.source_agent == "analyst"
    assert fault.source_module == "analyst.scoring"
    assert fault.error_type == "ValueError"
    assert "bad input" in fault.message
    assert fault.traceback is not None


def test_boundary_redirects_and_reraises():
    sink = CollectingFaultSink()
    with (
        pytest.raises(ValueError, match="boom"),
        fault_boundary(sink, agent="scanner", module="scanner.filters"),
    ):
        raise ValueError("boom")
    assert len(sink.faults) == 1
    assert sink.faults[0].source_module == "scanner.filters"


def test_boundary_can_swallow_when_asked():
    sink = CollectingFaultSink()
    with fault_boundary(sink, agent="monitor", module="monitor.exit", reraise=False):
        raise RuntimeError("degraded but continue")
    assert sink.faults[0].error_type == "RuntimeError"


def test_boundary_passes_clean_blocks_through():
    sink = CollectingFaultSink()
    with fault_boundary(sink, agent="reporter", module="reporter.metrics"):
        result = 1 + 1
    assert result == 2
    assert sink.faults == []
