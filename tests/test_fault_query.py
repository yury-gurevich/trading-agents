"""Fault timestamp query tests for audit correctness.

Agent: kernel
Role: prove Fault timestamp readers cannot silently query a missing property.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from kernel import InMemoryGraphStore, fault_query
from kernel.fault_graph import FAULT_SUPPRESSION_LABEL
from kernel.fault_query import (
    MissingFaultTimestampPropertyError,
    fault_count_in_window,
    faults_occurred_in_window,
)


def _at(hour: int) -> datetime:
    return datetime(2026, 8, 8, hour, tzinfo=UTC)


def test_fault_count_uses_occurred_at_and_counts_suppressed_volume() -> None:
    """DL-99: a collapsed Fault still counts by its occurred_at window."""
    graph = InMemoryGraphStore()
    graph.merge_node(
        "Fault",
        "fault:usage",
        {
            "source_agent": "deliberator-manager",
            "capability": "review_pm_node",
            "severity": "error",
            "message": "usage limit",
            "occurred_at": _at(7).isoformat(),
        },
    )
    graph.merge_node(
        "Fault",
        "fault:old",
        {"message": "old", "occurred_at": _at(5).isoformat()},
    )
    graph.merge_node(
        FAULT_SUPPRESSION_LABEL,
        "fault-suppression:usage",
        {
            "first_fault_key": "fault:usage",
            "occurrence_count": 5,
            "suppressed_count": 4,
        },
    )

    assert fault_count_in_window(graph, _at(6)) == 5
    assert [item.node.key for item in faults_occurred_in_window(graph, _at(6))] == [
        "fault:usage"
    ]
    assert fault_count_in_window(graph, _at(6), end=_at(8)) == 5
    assert fault_count_in_window(graph, _at(8)) == 0


def test_missing_fault_timestamp_property_raises() -> None:
    """DL-99: a missing Fault timestamp is an audit error, never zero."""
    graph = InMemoryGraphStore()
    graph.merge_node("Fault", "fault:bad", {"message": "missing timestamp"})

    with pytest.raises(MissingFaultTimestampPropertyError, match="occurred_at"):
        fault_count_in_window(graph, _at(6))


def test_created_at_timestamp_plant_raises_instead_of_reporting_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DL-70 / DL-99: the exact created_at/occurred_at typo cannot read green."""
    graph = InMemoryGraphStore()
    graph.merge_node(
        "Fault",
        "fault:usage",
        {"message": "usage limit", "occurred_at": _at(7).isoformat()},
    )
    monkeypatch.setattr(fault_query, "FAULT_TIMESTAMP_PROPERTY", "created_at")

    with pytest.raises(MissingFaultTimestampPropertyError, match="created_at"):
        fault_count_in_window(graph, _at(6))


def test_faults_occurred_in_window_sorts_newest_first() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node("Fault", "fault:older", {"occurred_at": _at(6).isoformat()})
    graph.merge_node(
        "Fault",
        "fault:newer",
        {"occurred_at": (_at(6) + timedelta(minutes=1)).isoformat()},
    )

    rows = faults_occurred_in_window(graph, _at(6))

    assert [row.node.key for row in rows] == ["fault:newer", "fault:older"]
