"""Agent PRE_FLIGHT → ACTIVATE bootstrap over HTTP.

Agent: kernel
Role: send EHLO to the master agent (resent within a bounded budget with one boot
      id, kernel.ehlo_retry), optionally verify the RSA-PSS signature on ACTIVATE,
      and return the grants payload; shared by all agent entrypoints.
External I/O: master HTTP endpoint (POST /ehlo).
"""

from __future__ import annotations

import base64
import json
import os
import urllib.request
import uuid
from typing import TYPE_CHECKING

from kernel.ehlo_retry import RetryHooks, send_with_retry
from kernel.ehlo_settings import EhloSettings

if TYPE_CHECKING:
    from collections.abc import Callable


def _pem_from_env(raw_var: str, b64_var: str) -> str | None:
    """PEM from *raw_var* (verbatim) or *b64_var* (base64-decoded); None if neither.

    Base64 avoids the multi-line-PEM problem when passing keys as Container Apps
    env vars / az CLI args.
    """
    raw = os.environ.get(raw_var)
    if raw:
        return raw
    encoded = os.environ.get(b64_var)
    if encoded:
        return base64.b64decode(encoded).decode()
    return None


def master_public_key_from_env() -> str | None:
    """Master public key PEM from env (raw or base64); None if absent (no verify)."""
    return _pem_from_env("MASTER_PUBLIC_KEY_PEM", "MASTER_PUBLIC_KEY_PEM_B64")


def master_private_key_from_env() -> str | None:
    """Master private key PEM from env (raw or base64); None if absent (dev keypair)."""
    return _pem_from_env("MASTER_PRIVATE_KEY_PEM", "MASTER_PRIVATE_KEY_PEM_B64")


def activate_agent(
    master_url: str,
    agent_type: str,
    capability_declaration: dict[str, object] | None = None,
    public_key_pem: str | None = None,
    _send: Callable[[str, dict[str, object], float], dict[str, object]] | None = None,
    _hooks: RetryHooks | None = None,
    _settings: EhloSettings | None = None,
) -> dict[str, object]:
    """Send EHLO, verify ACTIVATE signature if public_key_pem given, return payload.

    One boot id for every attempt: a transport failure is resent inside the
    ``EhloSettings`` budget and master replays the resend (MST-TRG-01, MST-IDM-03);
    a 4xx or a bad signature is final. *_send* (url, body, timeout), *_hooks* and
    *_settings* are injectable for tests; the default sender is a real HTTP POST.
    """
    body: dict[str, object] = {
        "ephemeral_boot_id": uuid.uuid4().hex,
        "agent_type": agent_type,
        "capability_declaration": capability_declaration or {},
    }
    payload = send_with_retry(
        _send or _http_post,
        f"{master_url.rstrip('/')}/ehlo",
        body,
        _settings or EhloSettings(),
        _hooks or RetryHooks(),
    )
    if public_key_pem:
        _verify_signature(payload, public_key_pem)
    _apply_config(payload)
    return payload


def _apply_config(payload: dict[str, object]) -> None:
    """Apply the master-provided config (secrets/endpoints) to the process env.

    The master resolves per-agent secrets and returns them in ACTIVATE.config;
    this writes each string value into os.environ so the agent's settings pick
    them up. (Config keys must match the settings' env-var names — see
    docs/design-log.md DL-07.)
    """
    config = payload.get("config")
    if isinstance(config, dict):
        for key, value in config.items():
            if isinstance(value, str):
                os.environ[key] = value


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


def _http_post(
    url: str, data: dict[str, object], timeout: float = 30.0
) -> dict[str, object]:
    """POST JSON to url, return parsed response. Validates http/https scheme."""
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"master_url must be http or https: {url!r}")
    body = json.dumps(data).encode()
    req = urllib.request.Request(  # noqa: S310 - scheme checked above.
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        result: dict[str, object] = json.loads(resp.read())
        return result
