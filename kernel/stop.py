"""Stop signal for a container's main loop.

Agent: kernel
Role: turn the platform's stop signal (SIGTERM) into a flag a serving loop asks
      and sleeps on, and write the two lines a stop leaves in the console log:
      one when the signal arrives, one when what the loop held is closed.
External I/O: installs a process signal handler; writes to stderr.
"""

from __future__ import annotations

import os
import signal
import sys
import threading
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    Step = tuple[str, Callable[[], object]]

UNNAMED = "agent"
_WAKE_SECONDS = 1.0


class StopSignal:
    """Set once when the process is told to stop; a loop asks it and sleeps on it."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        """Start unrequested; *clock* times the stop for the closing line."""
        self._event = threading.Event()
        self._clock = clock
        self._requested_at = 0.0
        self.reason = ""

    def request(self, reason: str = "request") -> None:
        """Ask the loop to stop; the first reason and its time are kept."""
        if not self._event.is_set():
            self.reason = reason
            self._requested_at = self._clock()
            self._event.set()

    @property
    def requested(self) -> bool:
        """Whether a stop has been asked for."""
        return self._event.is_set()

    def wait(self, seconds: float) -> None:
        """Sleep up to *seconds*; return within a second of a stop being asked for.

        The sleep is taken in slices: the interpreter runs a signal handler only
        when the main thread is back in Python code, and a signal the platform
        hands to another thread does not end a single long wait.
        """
        deadline = time.monotonic() + max(seconds, 0.0)
        while not self._event.is_set():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            self._event.wait(min(remaining, _WAKE_SECONDS))

    def seconds_since_request(self) -> float:
        """Seconds since the stop was asked for (0.0 before one is)."""
        return self._clock() - self._requested_at if self.requested else 0.0

    def seconds_left(self, budget: float) -> float:
        """Seconds of *budget* not yet spent since the stop was asked for."""
        return max(budget - self.seconds_since_request(), 0.0)


def _write_raw(line: str) -> None:
    # A handler can interrupt the main thread inside a buffered write to stderr,
    # and a second buffered write there raises; a raw write to the descriptor cannot.
    os.write(2, line.encode())


def _write_line(line: str) -> None:
    sys.stderr.write(line)
    sys.stderr.flush()


def install(
    stop: StopSignal, *, agent: str, write: Callable[[str], None] = _write_raw
) -> bool:
    """Route SIGTERM to *stop*; return False, installing nothing, off the main thread.

    The interpreter runs a handler on the main thread only and refuses to install
    one from another. The handler sets the flag and writes one line, so a process
    killed later still shows in its log that it was told to stop and when.
    """
    if threading.current_thread() is not threading.main_thread():
        return False

    def handle(signum: int, _frame: object) -> None:
        name = signal.Signals(signum).name
        stop.request(name)
        write(f"[{agent}] stop signal {name}: taking no new work\n")

    signal.signal(signal.SIGTERM, handle)
    return True


def closing_steps(
    *,
    faults: Callable[[], object] | None = None,
    requests: object = None,
    graph: object = None,
) -> tuple[Step, ...]:
    """Name what a loop holds that can be closed, in the order it is closed."""
    steps: list[Step] = []
    if faults is not None:
        steps.append(("faults", faults))
    for name, held in (("requests", requests), ("graph", graph)):
        close = getattr(held, "close", None)
        if callable(close):
            steps.append((name, close))
    return tuple(steps)


def finish(
    stop: StopSignal,
    *,
    agent: str,
    steps: Sequence[Step],
    unfinished: Sequence[str] = (),
    write: Callable[[str], None] | None = None,
) -> bool:
    """Run every closing step on its own, write the closing line, say whether clean.

    A step that raises does not keep the next from running. The line names each
    step and, for a failed one, the error's type alone (its text can hold a
    connection string). *unfinished* names work the caller had to leave; a stop
    is clean only when nothing was left and no step failed.
    """
    done: list[str] = []
    failed: list[str] = []
    for name, step in steps:
        try:
            step()
        except Exception as exc:
            failed.append(f"{name} ({type(exc).__name__})")
        else:
            done.append(name)
    parts: list[str] = []
    if unfinished:
        parts.append("left " + ", ".join(unfinished))
    if done:
        parts.append("closed " + ", ".join(done))
    if failed:
        parts.append("NOT closed " + ", ".join(failed))
    problems = len(unfinished) + len(failed)
    detail = "; ".join(parts) or "nothing to close"
    (write or _write_line)(
        f"[{agent}] stopped on {stop.reason} after "
        f"{stop.seconds_since_request():.1f} s: {detail}; exit {min(problems, 1)}\n"
    )
    return problems == 0


def end_loop(stop: StopSignal, *, agent: str, steps: Sequence[Step]) -> None:
    """Close what a stopped loop held; a failed step ends the process with status 1."""
    if not finish(stop, agent=agent, steps=steps):
        raise SystemExit(1)
