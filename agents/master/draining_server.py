"""Threading TCP server that knows how many requests it has in hand.

Agent: master
Role: count each request in before its thread starts and out when it ends, so a
      stopping server can wait a bounded time for the requests in hand.
External I/O: none of its own (the TCP socket belongs to the server it extends).
"""

from __future__ import annotations

import socketserver
import threading
from typing import Any


class DrainingTCPServer(socketserver.ThreadingTCPServer):
    """A thread per request, counted, so ``drain`` can wait for those in hand."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Build the server with no request in hand."""
        super().__init__(*args, **kwargs)
        self._idle = threading.Condition()
        self._in_hand = 0

    def process_request(self, request: Any, client_address: Any) -> None:  # noqa: ANN401
        """Count the request in before its thread starts."""
        with self._idle:
            self._in_hand += 1
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._count_out()
            raise

    def process_request_thread(self, request: Any, client_address: Any) -> None:  # noqa: ANN401
        """Serve the request on its thread, then count it out."""
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._count_out()

    def _count_out(self) -> None:
        with self._idle:
            self._in_hand -= 1
            self._idle.notify_all()

    def drain(self, seconds: float) -> int:
        """Wait up to *seconds* for the requests in hand; return how many are left."""
        with self._idle:
            self._idle.wait_for(lambda: self._in_hand == 0, timeout=max(seconds, 0.0))
            return self._in_hand
