"""A26: every dispatcher attempt runs the sensor afterward with its own status.

Agent: tooling
Role: pin stdout, stderr, ordering and exit codes at the real script entrypoint.
External I/O: none; injected graph, reader, clock and Telegram factories.
"""

from __future__ import annotations

from datetime import datetime, tzinfo

import pytest
import scripts.dispatch_scheduled_run as entrypoint

from kernel import InMemoryGraphStore
from orchestration import container_logs
from orchestration.container_sensor_guard import sense_from_env
from orchestration.tests.container_sensor_helpers import NOW, FakeAlarm, FakeReader

SKIP = "skipped sched-2026-07-04 reason=2026-07-04 is not a NYSE trading session\n"


class _Clock(datetime):
    @classmethod
    def now(cls, tz: tzinfo | None = None) -> datetime:  # type: ignore[override]
        return NOW


@pytest.mark.parametrize("failure", [False, True])
def test_a26_weekend_skip_then_sensor_or_safe_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], failure: bool
) -> None:
    """DSP-TRG-04 / DSP-IDN-05 / DSP-FAIL-04: sensor follows a skip without
    changing it.
    """
    graph, reader = (
        InMemoryGraphStore(),
        FakeReader(failure=ValueError("synthetic") if failure else None),
    )
    monkeypatch.setenv("LOG_ANALYTICS_WORKSPACE_ID", "workspace")
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://unused")
    monkeypatch.setattr(entrypoint, "_live_graph", lambda: graph)
    monkeypatch.setattr(entrypoint, "_telegram", FakeAlarm)
    monkeypatch.setattr(entrypoint, "datetime", _Clock)
    monkeypatch.setattr(
        container_logs, "LogAnalyticsReader", lambda *_args, **_kwargs: reader
    )
    assert entrypoint.main(["--as-of", "2026-07-04", "--env-file", "missing.env"]) == 0
    output = capsys.readouterr()
    if failure:
        assert output.out == SKIP
        assert output.err == "error container-sensor failed: ValueError\n"
        assert len(graph.list_nodes("Fault")) == 1
    else:
        assert (
            output.out
            == SKIP + "container-sensor read 0 rows: 0 new events, 0 alarms, told 0\n"
        )
        assert output.err == ""
    assert len(reader.windows) == 1


@pytest.mark.parametrize(
    ("action", "status"), [("placed", 0), ("skipped", 0), ("held", 0), ("failed", 1)]
)
def test_every_outcome_keeps_dispatch_order_and_status(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    action: str,
    status: int,
) -> None:
    """DSP-TRG-04 / DSP-IDN-05 / DSP-FAIL-04: every outcome senses after dispatch."""
    order: list[str] = []

    def dispatch(_args: list[str] | None) -> int:
        order.append("dispatch")
        print(action)
        return status

    def sensor(**_kwargs: object) -> str:
        order.append("sensor")
        assert order == ["dispatch", "sensor"]
        return "container-sensor read 0 rows: 0 new events, 0 alarms, told 0"

    monkeypatch.setattr(entrypoint, "_dispatch", dispatch)
    monkeypatch.setattr(entrypoint, "sense_from_env", sensor)
    assert entrypoint.main([]) == status
    assert order == ["dispatch", "sensor"]
    assert capsys.readouterr().out.startswith(action + "\ncontainer-sensor")


def test_unconfigured_weekend_stdout_is_unchanged(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """DSP-TRG-04: an unconfigured fire remains silent beyond its original skip line."""
    monkeypatch.delenv("LOG_ANALYTICS_WORKSPACE_ID", raising=False)
    monkeypatch.setattr(entrypoint, "sense_from_env", sense_from_env)
    assert entrypoint.main(["--as-of", "2026-07-04", "--env-file", "missing.env"]) == 0
    output = capsys.readouterr()
    assert (output.out, output.err) == (SKIP, "")
