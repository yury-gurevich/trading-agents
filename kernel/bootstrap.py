"""Agent PRE_FLIGHT → ACTIVATE bootstrap over HTTP.

Agent: kernel
Role: send EHLO to the master agent, optionally verify the RSA-PSS signature on
      ACTIVATE, and return the grants payload; shared by all agent entrypoints.
External I/O: master HTTP endpoint (POST /ehlo).
"""

from __future__ import annotations

import json
import urllib.request
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


def activate_agent(
    master_url: str,
    agent_type: str,
    capability_declaration: dict[str, object] | None = None,
    public_key_pem: str | None = None,
    _send: Callable[[str, dict[str, object]], dict[str, object]] | None = None,
) -> dict[str, object]:
    """Send EHLO, verify ACTIVATE signature if public_key_pem given, return payload.

    *_send* is injectable for tests; defaults to a real HTTP POST.
    """
    send = _send or _http_post
    boot_id = uuid.uuid4().hex
    payload = send(
        f"{master_url.rstrip('/')}/ehlo",
        {
            "ephemeral_boot_id": boot_id,
            "agent_type": agent_type,
            "capability_declaration": capability_declaration or {},
        },
    )
    if public_key_pem:
        _verify_signature(payload, public_key_pem)
    return payload


def _verify_signature(payload: dict[str, object], public_key_pem: str) -> None:
    from kernel.crypto import verify_pss

    instance_id = str(payload.get("instance_id", ""))
    signature = str(payload.get("signature", ""))
    if not signature:
        raise ValueError(
            "ACTIVATE carries no signature — "
            "master may be running without RSA signing (MST-SEC-01)"
        )
    verify_pss(public_key_pem, instance_id, signature)


def _http_post(url: str, data: dict[str, object]) -> dict[str, object]:
    """POST JSON to url, return parsed response. Validates http/https scheme."""
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"master_url must be http or https: {url!r}")
    body = json.dumps(data).encode()  # pragma: no cover
    req = urllib.request.Request(  # noqa: S310  # pragma: no cover
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310  # pragma: no cover
        result: dict[str, object] = json.loads(resp.read())  # pragma: no cover
        return result  # pragma: no cover


def idle_loop() -> None:  # pragma: no cover
    """Block indefinitely — placeholder until the agent event loop is wired (S75+)."""
    import time

    while True:
        time.sleep(60)
