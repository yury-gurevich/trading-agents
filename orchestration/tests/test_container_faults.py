"""A24: contain sensor failures and preserve their safe audit trail.

Agent: orchestration
Role: prove workspace, module and graph faults cannot escape into a fire.
External I/O: none.
"""

from __future__ import annotations

import sys
from datetime import timedelta
from typing import TYPE_CHECKING

import pytest

from kernel import InMemoryGraphStore
from orchestration.container_queries import ContainerLogReadError
from orchestration.container_sensor_graph import last_read_until
from orchestration.container_sensor_guard import sense_safely
from orchestration.tests.container_sensor_helpers import (
    MEASURED,
    NOW,
    SETTINGS,
    FakeAlarm,
    FakeReader,
)

if TYPE_CHECKING:
    from kernel import Node
    from kernel.graph_support import Props


@pytest.mark.parametrize(
    ("failure", "safe"),
    [
        (ContainerLogReadError("403"), "ContainerLogReadError (403)"),
        (ValueError("token=" + "synthetic"), "ValueError"),
    ],
)
def test_a24_read_failure_is_one_fault_and_failed_read(
    failure: Exception, safe: str
) -> None:
    """DSP-FAIL-04 / DSP-SEC-03: a failed read keeps its type/status, never its text."""
    graph = InMemoryGraphStore()
    line = sense_safely(
        graph, FakeReader(failure=failure), FakeAlarm(), now=NOW, settings=SETTINGS
    )
    assert line == f"error container-sensor failed: {safe}"
    (read,) = graph.list_nodes("ContainerSensorRead")
    (fault,) = graph.list_nodes("Fault")
    assert dict(read.props) == {
        "read_until": NOW.isoformat(),
        "outcome": "failed",
        "error": safe,
        "created_at": NOW.isoformat(),
    }
    assert fault.props["message"] == f"container sensor did not read: {safe}"
    assert "Traceback (most recent call last):" in str(fault.props["traceback"])
    assert "ContainerSensorFailedError" in str(fault.props["traceback"])
    assert "synthetic" not in str(fault.props)
    assert last_read_until(graph) is None
    reader = FakeReader()
    sense_safely(
        graph, reader, FakeAlarm(), now=NOW + timedelta(minutes=10), settings=SETTINGS
    )
    assert reader.windows == [
        (NOW + timedelta(minutes=10) - timedelta(hours=24), NOW + timedelta(minutes=10))
    ]


def test_a24_missing_sensor_module_is_contained(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DSP-FAIL-04: an image missing the sensor leaves a fault and failed read."""
    graph = InMemoryGraphStore()
    monkeypatch.setitem(sys.modules, "orchestration.container_sensor", None)
    assert (
        sense_safely(graph, FakeReader(), FakeAlarm(), now=NOW, settings=SETTINGS)
        == "error container-sensor failed: ModuleNotFoundError"
    )
    assert (
        len(graph.list_nodes("Fault"))
        == len(graph.list_nodes("ContainerSensorRead"))
        == 1
    )


def test_a24_refusing_port_records_one_fault_and_no_told_edge() -> None:
    """DSP-FAIL-04 / DSP-IDM-04: a port refusing an alarm is a fault and stays
    untold.
    """
    graph = InMemoryGraphStore()
    line = sense_safely(
        graph,
        FakeReader([MEASURED["killed"]]),
        FakeAlarm(sent=False, last_error="telegram_response_invalid"),
        now=NOW,
        settings=SETTINGS,
    )
    assert (
        line == "container-sensor read 1 rows: 1 new events, 1 alarms, told 0, "
        "send failed (telegram_response_invalid)"
    )
    (fault,) = graph.list_nodes("Fault")
    assert (
        fault.props["message"] == "container alarm not sent: telegram_response_invalid"
    )
    assert graph.keys_without_edge("ContainerEvent", "TOLD", downstream=False) == (
        graph.list_nodes("ContainerEvent")[0].key,
    )


class _Refusing(InMemoryGraphStore):
    def merge_node(
        self, label: str, key: str, props: Props, *, schema_version: int = 1
    ) -> Node:
        raise ValueError("synthetic write body")


def test_a24_graph_refusing_all_writes_still_never_raises(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """DSP-FAIL-04 / DSP-SEC-03: refused audit writes are safe stderr lines, not
    raises.
    """
    graph = _Refusing()
    assert (
        sense_safely(
            graph,
            FakeReader([MEASURED["killed"]]),
            FakeAlarm(),
            now=NOW,
            settings=SETTINGS,
        )
        == "error container-sensor failed: ValueError"
    )
    output = capsys.readouterr()
    assert "error container-sensor read not recorded: ValueError\n" in output.err
    assert "synthetic" not in output.err
    assert graph.list_nodes("ContainerSensorRead") == graph.list_nodes("Fault") == ()


def test_a24_failure_status_is_used_only_when_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DSP-SEC-03 / DSP-FAIL-04: non-text status metadata cannot enter the failure
    line.
    """
    failure = ValueError("synthetic")
    monkeypatch.setattr(failure, "status", 403, raising=False)
    line = sense_safely(
        InMemoryGraphStore(),
        FakeReader(failure=failure),
        FakeAlarm(),
        now=NOW,
        settings=SETTINGS,
    )
    assert line == "error container-sensor failed: ValueError"
