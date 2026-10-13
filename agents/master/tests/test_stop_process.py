"""Real master process shutdown proof.

Agent: master
Role: exercise the production entrypoint in an isolated child process.
External I/O: child Python process and a loopback listening socket only.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_CHILD = """
import json
import os
import signal
import threading
from agents.master import entrypoint, http_server

watchdog = threading.Timer(60, lambda: os._exit(99))
watchdog.daemon = True
watchdog.start()
held = {}
real_build = http_server.build_server

def capture_server(*args, **kwargs):
    server = real_build(*args, **kwargs)
    timer = threading.Timer(0.2, lambda: signal.raise_signal(signal.SIGTERM))
    timer.daemon = True
    timer.start()
    return server

def loopback_serve(port, agent, pem, settings, **kwargs):
    held['agent'] = agent
    return http_server.serve(0, agent, pem, settings, host='127.0.0.1', **kwargs)

http_server.build_server = capture_server
entrypoint.serve = loopback_serve
try:
    entrypoint.main()
finally:
    agent = held.get('agent')
    if agent is not None:
        node = agent._graph.get_node('Session', agent.session_id)
        print(json.dumps(dict(node.props)), flush=True)
"""


def test_a1_master_process_ends_cleanly_on_sigterm(tmp_path: Path) -> None:
    """MST-ORD-04 / MST-OUT-03 / MST-OBS-05: real main ends its session and exits 0."""
    env = {
        key: os.environ[key]
        for key in ("PATH", "SYSTEMROOT", "TEMP", "TMP", "HOME")
        if key in os.environ
    }
    env.update(PYTHONPATH=str(_ROOT), MASTER_GRAPH="memory", PYTHONUTF8="1")
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
    props = json.loads(child.stdout.strip())
    assert datetime.fromisoformat(props["ended_at"]) > datetime.fromisoformat(
        props["started_at"]
    )
    assert props["shutdown_reason"] == "SIGTERM"
    assert "[master] stop signal SIGTERM: taking no new work\n" in child.stderr
    assert child.stderr.splitlines()[-1].startswith(
        "[master] stopped on SIGTERM after "
    )
    assert child.stderr.endswith("closed session; exit 0\n")
