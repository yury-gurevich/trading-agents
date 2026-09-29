"""The agent's EHLO budget ends loud (S244, DL-249 D1).

Agent: kernel
Role: prove a master that never answers ends in one named error inside the attempt
      cap and the total budget, with one stderr line per failed attempt.
External I/O: none (injected sender, clock, sleep and jitter; no socket).
"""

from __future__ import annotations

import pytest
from tests.ehlo_fakes import URL, FakeTime, Master

from kernel.bootstrap import activate_agent
from kernel.ehlo_retry import EhloBudgetExhaustedError
from kernel.ehlo_settings import EhloSettings


def test_a_spent_attempt_budget_ends_loud(capsys: pytest.CaptureFixture[str]) -> None:
    """MST-FAIL-06 / MST-TRG-01: a master that never answers ends in one named error.

    C4 — at most the attempt cap, inside the budget, one stderr line per failed attempt,
    and the error names the attempts, the elapsed time and the last cause.
    """
    time = FakeTime(jitter=1.0)
    master = Master(time, [TimeoutError("timed out")] * 50)
    settings = EhloSettings()

    with pytest.raises(EhloBudgetExhaustedError) as caught:
        activate_agent(
            URL, "provider", _send=master, _hooks=time.hooks(), _settings=settings
        )

    error = caught.value
    assert error.attempts == len(master.bodies) == settings.ehlo_max_attempts == 6
    assert error.elapsed_seconds == pytest.approx(211.0)  # 6 x 30 s + 1+2+4+8+16 s
    assert error.elapsed_seconds <= settings.ehlo_budget_seconds
    assert isinstance(error.last_cause, TimeoutError)
    assert "6 attempt(s)" in str(error)
    assert "211.0s" in str(error)
    assert "TimeoutError: timed out" in str(error)
    assert len(capsys.readouterr().err.strip().splitlines()) == 6


def test_the_budget_stops_resends_before_the_attempt_cap() -> None:
    """MST-FAIL-06 / MST-TRG-01: the total budget binds before the cap.

    C4 — the last attempt's timeout is clipped to what is left of the budget.
    """
    time = FakeTime(jitter=1.0)
    master = Master(time, [TimeoutError("timed out")] * 50)
    settings = EhloSettings(ehlo_max_attempts=20, ehlo_budget_seconds=100.0)

    with pytest.raises(EhloBudgetExhaustedError) as caught:
        activate_agent(
            URL, "monitor", _send=master, _hooks=time.hooks(), _settings=settings
        )

    assert caught.value.attempts == 4
    assert master.timeouts == [30.0, 30.0, 30.0, 3.0]
    assert caught.value.elapsed_seconds == pytest.approx(100.0)


_BOOT_AGAINST_A_DEAD_MASTER = """
from kernel.bootstrap import activate_agent
from kernel.ehlo_retry import RetryHooks

now = [0.0]

def send(url, data, timeout):
    now[0] += timeout
    raise TimeoutError("timed out")

def sleep(seconds):
    now[0] += seconds

hooks = RetryHooks(clock=lambda: now[0], sleep=sleep, rand=lambda: 1.0)
activate_agent("http://master:8000", "scanner", _send=send, _hooks=hooks)
"""


def test_a_spent_budget_exits_the_process_non_zero() -> None:
    """MST-FAIL-06: an agent process whose budget is spent exits non-zero, loudly.

    No entrypoint catches the activation error, so the boot's last stderr line is
    the named error with attempts, elapsed and last cause (no socket is opened).
    """
    import subprocess
    import sys
    from pathlib import Path

    done = subprocess.run(  # noqa: S603 - fixed interpreter and fixed code.
        [sys.executable, "-c", _BOOT_AGAINST_A_DEAD_MASTER],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=Path(__file__).resolve().parents[1],
        check=False,
    )

    lines = done.stderr.strip().splitlines()
    assert done.returncode != 0
    assert sum(line.startswith("[ehlo] attempt") for line in lines) == 6
    assert lines[-1] == (
        "kernel.ehlo_retry.EhloBudgetExhaustedError: EHLO to "
        "http://master:8000/ehlo failed after 6 attempt(s) in 211.0s; "
        "last cause: TimeoutError: timed out"
    )
