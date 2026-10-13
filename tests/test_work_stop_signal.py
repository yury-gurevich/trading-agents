"""Real signal proof for a container's graph-pull loop.

Agent: kernel
Role: keep the default-action SIGTERM red proof outside pytest itself.
External I/O: an isolated child Python process only.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
from pathlib import Path

from kernel import InMemoryGraphStore
from kernel.work_loop import work_loop

_ROOT = Path(__file__).resolve().parents[1]
_CHILD = """
import os
import signal
import threading
from kernel.work_loop import work_loop

class Graph:
    closes = 0
    def close(self):
        self.closes += 1

watchdog = threading.Timer(60, lambda: os._exit(99))
watchdog.daemon = True
watchdog.start()
graph = Graph()
timer = threading.Timer(0.2, lambda: signal.raise_signal(signal.SIGTERM))
timer.daemon = True
timer.start()
work_loop(lambda: [], lambda item: None, graph=graph, poll_interval=60)
print('closes=' + str(graph.closes), flush=True)
"""


def test_a2_graph_pull_process_listens_for_sigterm(tmp_path: Path) -> None:
    """MST-TRG-03: an unbounded loop installs its handler, closes once and returns."""
    env = {
        key: os.environ[key]
        for key in ("PATH", "SYSTEMROOT", "TEMP", "TMP", "HOME")
        if key in os.environ
    }
    env.update(PYTHONPATH=str(_ROOT), PYTHONUTF8="1")
    child = subprocess.run(  # noqa: S603 - fixed interpreter and literal child program.
        [sys.executable, "-c", _CHILD],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=70,
        check=False,
    )
    assert child.returncode == 0, (child.returncode, child.stdout, child.stderr)
    assert child.stdout == "closes=1\n"
    assert child.stderr.splitlines()[0] == (
        "[agent] stop signal SIGTERM: taking no new work"
    )
    assert len(child.stderr.splitlines()) == 2
    assert child.stderr.endswith("closed graph; exit 0\n")


def test_a2_unbounded_loop_installs_in_the_main_process(capfd) -> None:
    """MST-TRG-03: the same unbounded signal path is observable inside coverage."""

    class Graph(InMemoryGraphStore):
        closes = 0

        def close(self):
            self.closes += 1

    graph = Graph()
    previous = signal.getsignal(signal.SIGTERM)
    timer = threading.Timer(0.2, lambda: signal.raise_signal(signal.SIGTERM))
    timer.start()
    try:
        results = work_loop(list, lambda item: None, graph=graph, poll_interval=60)
    finally:
        timer.cancel()
        timer.join(timeout=2)
        signal.signal(signal.SIGTERM, previous)
    assert len(results) == 1
    assert graph.closes == 1
    lines = capfd.readouterr().err.splitlines()
    assert len(lines) == 2
    assert lines[0] == "[agent] stop signal SIGTERM: taking no new work"
    assert lines[-1].endswith("closed graph; exit 0")
