"""Shared support for the real-socket EHLO server tests (S244).

Agent: master
Role: build a master whose activation is deliberately slow, run a built server on
      a background thread, and make plain HTTP requests to it on loopback.
External I/O: a loopback TCP socket on an OS-assigned port (no other network).
"""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from typing import TYPE_CHECKING

from agents.master.agent import MasterAgent
from agents.master.credential_test import CredentialTest
from agents.master.tests.helpers import trading_policy
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from collections.abc import Iterator
    from socketserver import BaseServer

ACTIVATION_SECONDS = 0.5


def slow_master(delay: float = ACTIVATION_SECONDS) -> MasterAgent:
    """A started master whose every activation runs one *delay*-second probe."""

    def slow(_config: object) -> bool:
        time.sleep(delay)
        return True

    agent = MasterAgent(
        graph=InMemoryGraphStore(),
        grant_policy=trading_policy(),
        credential_tests=(CredentialTest(name="slow", run=slow),),
    )
    agent.start()
    return agent


@contextmanager
def running(server: BaseServer) -> Iterator[str]:
    """Serve *server* on a daemon thread; yield its base URL; shut it down."""
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    address = server.server_address
    assert isinstance(address, tuple)
    host, port = address[0], address[1]
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def request(url: str, method: str, body: bytes | None = None) -> tuple[int, object]:
    """One plain HTTP request; return (status, parsed JSON body)."""
    req = urllib.request.Request(url, data=body, method=method)  # noqa: S310
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())
