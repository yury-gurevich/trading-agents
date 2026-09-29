"""The agent's EHLO resend envelope: what is resent and what is final (S244).

Agent: kernel
Role: prove activate_agent resends transient failures with one boot id (DL-249 D2)
      and never resends a final answer.
External I/O: none (injected sender, clock, sleep and jitter; no socket).
"""

from __future__ import annotations

import http.client
import socket
import urllib.error

import pytest
from cryptography.exceptions import InvalidSignature
from tests.ehlo_fakes import URL, FakeTime, Master, activate_body, http_error

from kernel.bootstrap import activate_agent
from kernel.crypto import generate_keypair
from kernel.ehlo_settings import EhloSettings


def test_a_timed_out_ehlo_is_resent_with_one_boot_id(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """MST-TRG-01 / MST-ORD-02: a transient failure is resent, same boot id each time.

    C1 — a master that times out twice (asleep, then busy) still activates the agent
    on its third send, and every send carries the one boot id.
    """
    time = FakeTime(jitter=0.5)
    master = Master(time, [TimeoutError("timed out"), TimeoutError("timed out")])

    payload = activate_agent(
        URL, "scanner", _send=master, _hooks=time.hooks(), _settings=EhloSettings()
    )

    assert payload["instance_id"] == "scanner:ts:0"
    assert len(master.bodies) == 3
    assert len({body["ephemeral_boot_id"] for body in master.bodies}) == 1
    assert time.sleeps == [0.5, 1.0]  # full jitter: U(0,1) * min(30, 1 * 2^(n-1))
    assert master.timeouts == [30.0, 30.0, 30.0]
    assert len(capsys.readouterr().err.strip().splitlines()) == 2


_TRANSIENT: list[BaseException] = [
    TimeoutError("timed out"),
    ConnectionRefusedError(111, "refused"),
    ConnectionResetError(104, "reset"),
    ConnectionAbortedError(103, "aborted"),
    http.client.RemoteDisconnected("closed without response"),
    urllib.error.URLError(ConnectionRefusedError(111, "refused")),
    urllib.error.URLError(TimeoutError("timed out")),
    http_error(502),
    http_error(503),
    http_error(504),
]


@pytest.mark.parametrize("failure", _TRANSIENT, ids=repr)
def test_each_transient_failure_is_resent(failure: BaseException) -> None:
    """MST-TRG-01 / MST-ORD-02: a starting or busy master's failures are all resent.

    C2 — each transport class is resent once and the second send activates.
    """
    time = FakeTime()
    master = Master(time, [failure])

    activate_agent(URL, "analyst", _send=master, _hooks=time.hooks())

    assert len(master.bodies) == 2


_FINAL: list[BaseException] = [
    http_error(400),
    http_error(404),
    http_error(422),
    http_error(500),
    urllib.error.URLError(socket.gaierror(-2, "Name or service not known")),
    ValueError("master_url must be http or https"),
    BrokenPipeError(32, "broken pipe"),
]


@pytest.mark.parametrize("failure", _FINAL, ids=repr)
def test_a_final_answer_is_never_resent(failure: BaseException) -> None:
    """MST-TRG-01: a 4xx (400/404/422), a 500 or a non-transport error is final.

    C3 — exactly one send, and the original exception reaches the caller at once.
    """
    time = FakeTime()
    master = Master(time, [failure])

    with pytest.raises(type(failure)):
        activate_agent(URL, "scanner", _send=master, _hooks=time.hooks())

    assert len(master.bodies) == 1
    assert time.sleeps == []


def test_a_bad_signature_is_never_resent() -> None:
    """MST-TRG-01 / MST-SEC-01: a bad signature on ACTIVATE is final, one send.

    C3 — the signature is verified on the final answer, outside the resend loop.
    """
    _, public = generate_keypair()
    sends: list[dict[str, object]] = []

    def send(url: str, data: dict[str, object], timeout: float) -> dict[str, object]:
        sends.append(data)
        return activate_body(data, signature="bm90YXNpZ25hdHVyZQ==")

    with pytest.raises(InvalidSignature):
        activate_agent(
            URL,
            "scanner",
            public_key_pem=public,
            _send=send,
            _hooks=FakeTime().hooks(),
        )

    assert len(sends) == 1
