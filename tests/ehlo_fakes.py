"""Fakes for the EHLO resend tests: a clock that moves only when waited on.

Agent: kernel
Role: provide an injectable fake time and a scripted master for kernel.ehlo_retry
      tests, so no test sleeps or touches a socket.
External I/O: none.
"""

from __future__ import annotations

import urllib.error
from email.message import Message

from kernel.ehlo_retry import RetryHooks

URL = "http://master:8000"


class FakeTime:
    """A monotonic clock that only moves when the code under test waits."""

    def __init__(self, jitter: float = 0.5) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []
        self._jitter = jitter

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds

    def hooks(self) -> RetryHooks:
        return RetryHooks(
            clock=lambda: self.now, sleep=self.sleep, rand=lambda: self._jitter
        )


def activate_body(data: dict[str, object], signature: str = "") -> dict[str, object]:
    return {
        "instance_id": f"{data['agent_type']}:ts:0",
        "agent_type": data["agent_type"],
        "capability_grants": {},
        "config": {},
        "signature": signature,
    }


def http_error(status: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(URL, status, "status", Message(), None)


class Master:
    """Fails with the planted exceptions in order, then answers ACTIVATE."""

    def __init__(self, time: FakeTime, failures: list[BaseException]) -> None:
        self.time = time
        self.failures = list(failures)
        self.bodies: list[dict[str, object]] = []
        self.timeouts: list[float] = []

    def __call__(
        self, url: str, data: dict[str, object], timeout: float
    ) -> dict[str, object]:
        assert url == f"{URL}/ehlo"
        self.bodies.append(dict(data))
        self.timeouts.append(timeout)
        if self.failures:
            failure = self.failures.pop(0)
            if isinstance(failure, TimeoutError):
                self.time.now += timeout
            raise failure
        return activate_body(data)
