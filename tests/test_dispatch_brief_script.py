"""S234: what the dispatcher job prints, and what its faults say, carries no amount.

Agent: tooling
Role: drive the job entrypoint's `main` over the measured run pair (DSP-SEC-02).
External I/O: none; the graph, clock and Telegram transport are replaced in-process.

The job's stdout and stderr go to Log Analytics, an external system (S234 row 16),
so these tests read what `main` printed, not what a helper returned.
"""

from __future__ import annotations

from datetime import datetime, tzinfo

import pytest
import scripts.dispatch_scheduled_run as entrypoint

from kernel import InMemoryGraphStore
from orchestration.tests.daily_brief_fixtures import at
from orchestration.tests.daily_brief_scenarios import (
    A1_TEXT,
    amount_free,
    fault_text,
    seed_pair,
)
from orchestration.tests.scheduled_dispatch_human_helpers import FakeTelegram

# 23:30 is past the action window: the job places nothing, and the brief still goes.
_PRINTED = "skipped sched-2026-09-25 reason=NYSE trading session\n"


class _Clock(datetime):
    @classmethod
    def now(cls, tz: tzinfo | None = None) -> datetime:  # type: ignore[override]
        return at(23, 30)


def _main(monkeypatch: pytest.MonkeyPatch, graph: InMemoryGraphStore) -> int:
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://unused")
    monkeypatch.setattr(entrypoint, "_live_graph", lambda: graph)
    monkeypatch.setattr(entrypoint, "datetime", _Clock)
    return entrypoint.main(["--as-of", "2026-09-25", "--env-file", "missing.env"])


@pytest.mark.parametrize("refused", [False, True], ids=["sent", "port-raised"])
def test_a10_no_amount_leaves_through_the_job_log_or_a_fault(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], refused: bool
) -> None:
    """DSP-SEC-02: amounts leave only in the brief, through the injected port.

    The job prints its usual one line, and when the port raises quoting the text,
    the fault it leaves names no amount either.
    """
    graph = InMemoryGraphStore()
    seed_pair(graph)
    telegram = FakeTelegram(brief_raises=refused)
    monkeypatch.setattr(entrypoint, "TelegramClient", lambda **_: telegram)

    status = _main(monkeypatch, graph)

    printed = capsys.readouterr()
    assert status == 0
    assert telegram.briefs == [A1_TEXT.replace("08:50", "09:30")]
    assert printed.out == _PRINTED
    assert printed.err == ""
    faults = graph.list_nodes("Fault")
    assert len(faults) == int(refused)
    assert all(amount_free(fault_text(fault)) for fault in faults)
