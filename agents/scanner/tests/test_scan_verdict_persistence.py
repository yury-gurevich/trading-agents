"""Scanner filter-trace persistence tests (DL-09).

Agent: scanner
Role: prove a ScanRun keeps the per-ticker verdicts it decided on, so a drop
      can be scored against what actually happened.
External I/O: none.
"""

from __future__ import annotations

from agents.scanner.store import write_scan
from contracts.scanner import FilterTrace, FilterVerdict
from kernel import InMemoryGraphStore

_OWNED_LABELS = frozenset({"ScanRun", "Candidate"})


def _trace() -> FilterTrace:
    """Return a trace shaped like a real run: survivor, drop, bypassed drop."""
    return FilterTrace(
        universe_size=3,
        evaluated=3,
        dropped_by_filter={"min_average_volume": 1, "min_relative_strength": 1},
        verdicts=(
            FilterVerdict(
                ticker="AAPL", decision="survived", features={"average_volume": 9.0}
            ),
            FilterVerdict(
                ticker="KHC",
                decision="dropped",
                filter_fired="min_average_volume",
                features={"average_volume": 1.0},
            ),
            FilterVerdict(
                ticker="DOW",
                decision="dropped",
                filter_fired="min_relative_strength",
                features={"relative_strength": -0.4},
                bypassed=True,
            ),
        ),
    )


def _written(graph: InMemoryGraphStore, provenance_node_id: str) -> FilterTrace:
    scan_key = provenance_node_id.split(":", 1)[1]
    scan = graph.get_node("ScanRun", scan_key)
    assert scan is not None
    return FilterTrace.model_validate(scan.props["filter_trace"])


def test_scan_run_keeps_a_verdict_for_every_evaluated_ticker() -> None:
    """SCAN-OBS-01 / SCAN-OUT-02: the ScanRun reconstructs its FilterTrace.

    The scalars alone are a summary; without the verdicts a drop leaves no
    record and DL-09 cannot score it against what actually happened.
    """
    graph = InMemoryGraphStore()

    provenance = write_scan(
        graph,
        universe="fixture",
        candidates=(),
        trace=_trace(),
        provider_graph_node_id=None,
    )

    assert provenance.graph_node_id is not None
    written = _written(graph, provenance.graph_node_id)
    assert len(written.verdicts) == written.evaluated == 3
    assert {verdict.ticker for verdict in written.verdicts} == {"AAPL", "KHC", "DOW"}


def test_a_dropped_ticker_records_which_filter_bound_it() -> None:
    """SCAN-OUT-02: each dropped ticker is attributed to one filter."""
    graph = InMemoryGraphStore()

    provenance = write_scan(
        graph,
        universe="fixture",
        candidates=(),
        trace=_trace(),
        provider_graph_node_id=None,
    )

    assert provenance.graph_node_id is not None
    written = _written(graph, provenance.graph_node_id)
    by_ticker = {v.ticker: v for v in written.verdicts}
    assert by_ticker["KHC"].filter_fired == "min_average_volume"
    assert by_ticker["KHC"].features["average_volume"] == 1.0
    assert by_ticker["AAPL"].filter_fired is None


def test_a_bypassed_drop_is_not_laundered_into_a_survivor() -> None:
    """SCAN-OUT-02 / DL-09: the counterfactual keeps its original decision."""
    graph = InMemoryGraphStore()

    provenance = write_scan(
        graph,
        universe="fixture",
        candidates=(),
        trace=_trace(),
        provider_graph_node_id=None,
    )

    assert provenance.graph_node_id is not None
    written = _written(graph, provenance.graph_node_id)
    by_ticker = {v.ticker: v for v in written.verdicts}
    assert by_ticker["DOW"].bypassed is True
    assert by_ticker["DOW"].decision == "dropped"
    assert by_ticker["DOW"].filter_fired == "min_relative_strength"
    assert by_ticker["AAPL"].bypassed is False


def test_persisting_the_trace_writes_no_label_the_scanner_does_not_own() -> None:
    """SCAN-NEV-04 / SCAN-IDN-02: scanner owns only ScanRun and Candidate.

    The verdicts ride on the scanner's own ScanRun rather than a new label,
    which SCAN-IDN-02's closed enumeration would forbid.
    """
    graph = InMemoryGraphStore()

    write_scan(
        graph,
        universe="fixture",
        candidates=(),
        trace=_trace(),
        provider_graph_node_id=None,
    )

    written_labels = {node.label for node in graph.list_nodes("ScanRun")}
    for label in ("FilterVerdict", "Verdict", "FilterTrace"):
        assert graph.list_nodes(label) == (), f"{label} is not scanner-owned"
    assert written_labels <= _OWNED_LABELS
