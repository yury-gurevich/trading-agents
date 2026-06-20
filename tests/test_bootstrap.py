"""Tests for kernel.bootstrap activate_agent and signature verification."""

from __future__ import annotations

import pytest
from cryptography.exceptions import InvalidSignature

from kernel.bootstrap import _verify_signature, activate_agent
from kernel.crypto import generate_keypair, sign_pss

# ── fake HTTP sender ─────────────────────────────────────────────────────────


def _make_sender(instance_id: str, signature: str = "") -> object:
    captured: list[tuple] = []

    def send(url: str, data: dict) -> dict:
        captured.append((url, data))
        return {
            "instance_id": instance_id,
            "agent_type": data["agent_type"],
            "capability_grants": {},
            "config": {},
            "signature": signature,
        }

    send.captured = captured  # type: ignore[attr-defined]
    return send


# ── activate_agent ───────────────────────────────────────────────────────────


def test_activate_agent_posts_ehlo_to_master() -> None:
    sender = _make_sender("scanner:ts:0")
    activate_agent("http://master:8000", "scanner", _send=sender)
    assert sender.captured[0][0] == "http://master:8000/ehlo"
    body = sender.captured[0][1]
    assert body["agent_type"] == "scanner"
    assert "ephemeral_boot_id" in body
    assert body["capability_declaration"] == {}


def test_activate_agent_returns_payload() -> None:
    sender = _make_sender("analyst:ts:0")
    result = activate_agent("http://master:8000", "analyst", _send=sender)
    assert result["instance_id"] == "analyst:ts:0"
    assert result["agent_type"] == "analyst"


def test_activate_agent_passes_capability_declaration() -> None:
    sender = _make_sender("scanner:ts:0")
    activate_agent(
        "http://master:8000",
        "scanner",
        capability_declaration={"graph": {"operations": ["read"]}},
        _send=sender,
    )
    assert sender.captured[0][1]["capability_declaration"] == {
        "graph": {"operations": ["read"]}
    }


def test_activate_agent_strips_trailing_slash_from_url() -> None:
    sender = _make_sender("scanner:ts:0")
    activate_agent("http://master:8000/", "scanner", _send=sender)
    assert sender.captured[0][0] == "http://master:8000/ehlo"


# ── _http_post URL scheme guard ───────────────────────────────────────────────


def test_http_post_rejects_non_http_scheme() -> None:
    from kernel.bootstrap import _http_post

    with pytest.raises(ValueError, match="http or https"):
        _http_post("ftp://bad:8000/ehlo", {})


# ── signature verification ───────────────────────────────────────────────────


def test_activate_agent_verifies_valid_signature() -> None:
    private, public = generate_keypair()
    instance_id = "scanner:ts:0"
    sig = sign_pss(private, instance_id)
    sender = _make_sender(instance_id, sig)
    activate_agent("http://master:8000", "scanner", public_key_pem=public, _send=sender)


def test_activate_agent_rejects_bad_signature() -> None:
    _, public = generate_keypair()
    sender = _make_sender("scanner:ts:0", "bm90YXNpZ25hdHVyZQ==")
    with pytest.raises(InvalidSignature):
        activate_agent(
            "http://master:8000", "scanner", public_key_pem=public, _send=sender
        )


def test_verify_signature_raises_on_empty_signature() -> None:
    _, public = generate_keypair()
    with pytest.raises(ValueError, match="no signature"):
        _verify_signature({"instance_id": "x", "signature": ""}, public)
