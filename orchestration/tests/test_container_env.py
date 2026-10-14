"""A25 and A24 close failure: configure the sensor without changing the fire.

Agent: orchestration
Role: prove env gating, pre-graph failures, reader parameters and bounded closing.
External I/O: none; every factory is replaced.
"""

from __future__ import annotations

import pytest

from kernel import InMemoryGraphStore
from orchestration import container_logs, container_sensor_guard
from orchestration.container_sensor_guard import sense_from_env
from orchestration.tests.container_sensor_helpers import (
    NOW,
    SETTINGS,
    FakeAlarm,
    FakeReader,
)

ENV = {
    "LOG_ANALYTICS_WORKSPACE_ID": "workspace",
    "POSTGRES_DSN": "postgresql://unused",
    "IDENTITY_ENDPOINT": "http://identity.test/token",
    "IDENTITY_HEADER": "fixture",
}


class ClosingGraph(InMemoryGraphStore):
    def __init__(self, *, fails: bool = False) -> None:
        super().__init__()
        self.closed = False
        self.fails = fails

    def close(self) -> None:
        self.closed = True
        if self.fails:
            raise ValueError("synthetic close body")


def test_a25_unconfigured_sensor_builds_nothing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """DSP-TRG-04: absent or whitespace-only workspace is silent and builds nothing."""

    def refuse() -> object:
        raise AssertionError("unconfigured sensor built a port")

    for env in ({}, {"LOG_ANALYTICS_WORKSPACE_ID": " "}):
        assert (
            sense_from_env(
                now=NOW, graph_factory=refuse, port_factory=refuse, environ=env
            )
            is None
        )
    assert capsys.readouterr().out == ""
    assert capsys.readouterr().err == ""


def test_a25_configured_without_dsn_is_a_safe_line() -> None:
    """DSP-TRG-04 / DSP-FAIL-04: no DSN is reported before any graph or port builds."""
    built: list[str] = []
    line = sense_from_env(
        now=NOW,
        graph_factory=lambda: built.append("graph"),
        port_factory=lambda: built.append("port"),
        environ={"LOG_ANALYTICS_WORKSPACE_ID": "workspace"},
    )
    assert line == "error container-sensor not run: POSTGRES_DSN is required"
    assert built == []


def test_a25_graph_factory_failure_exposes_only_type() -> None:
    """DSP-TRG-04 / DSP-FAIL-04 / DSP-SEC-03: a pre-graph failure records nothing."""

    def refuse() -> object:
        raise ValueError("token=" + "synthetic")

    assert (
        sense_from_env(
            now=NOW, graph_factory=refuse, port_factory=FakeAlarm, environ=ENV
        )
        == "error container-sensor not run: ValueError"
    )


@pytest.mark.parametrize("component", ["settings", "reader"])
def test_pre_graph_construction_failures_are_safe(
    monkeypatch: pytest.MonkeyPatch, component: str
) -> None:
    """DSP-FAIL-04 / DSP-SEC-03: settings or reader construction failure names its
    type.
    """

    def refuse(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError("synthetic body")

    if component == "settings":
        monkeypatch.setattr(container_sensor_guard, "OrchestratorSettings", refuse)
    else:
        monkeypatch.setattr(container_logs, "LogAnalyticsReader", refuse)
    built: list[str] = []
    line = sense_from_env(
        now=NOW,
        graph_factory=lambda: built.append("graph"),
        port_factory=FakeAlarm,
        environ=ENV,
    )
    assert line == "error container-sensor not run: RuntimeError"
    assert built == []


@pytest.mark.parametrize("close_fails", [False, True])
def test_a25_configured_reader_and_a24_close(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    close_fails: bool,
) -> None:
    """DSP-TRG-04 / DSP-OBS-03 / DSP-FAIL-04: one read, the identity env, timeout
    and close.
    """
    graph, reader = ClosingGraph(fails=close_fails), FakeReader()
    made: list[tuple[str, dict[str, str], float]] = []

    def factory(
        workspace: str, *, environ: dict[str, str], timeout: float
    ) -> FakeReader:
        made.append((workspace, environ, timeout))
        return reader

    monkeypatch.setattr(container_logs, "LogAnalyticsReader", factory)
    monkeypatch.setattr(
        container_sensor_guard, "OrchestratorSettings", lambda: SETTINGS
    )
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    assert (
        sense_from_env(
            now=NOW, graph_factory=lambda: graph, port_factory=FakeAlarm, environ=None
        )
        == "container-sensor read 0 rows: 0 new events, 0 alarms, told 0"
    )
    assert len(reader.windows) == 1
    assert graph.closed
    workspace, supplied, timeout = made[0]
    assert workspace == "workspace"
    assert timeout == 20.0
    assert all(supplied[key] == value for key, value in ENV.items())
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == (
        "error container-sensor close: ValueError\n" if close_fails else ""
    )


def test_graph_without_close_is_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    """DSP-FAIL-04: a graph without an optional close operation finishes its read."""
    monkeypatch.setattr(
        container_logs, "LogAnalyticsReader", lambda *_args, **_kwargs: FakeReader()
    )
    graph = InMemoryGraphStore()
    assert (
        sense_from_env(
            now=NOW, graph_factory=lambda: graph, port_factory=FakeAlarm, environ=ENV
        )
        == "container-sensor read 0 rows: 0 new events, 0 alarms, told 0"
    )
