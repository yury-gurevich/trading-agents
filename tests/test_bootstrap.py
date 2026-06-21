"""Tests for kernel.bootstrap activate_agent and signature verification."""

from __future__ import annotations

import pytest
from cryptography.exceptions import InvalidSignature

from kernel.bootstrap import (
    _pem_from_env,
    _verify_signature,
    activate_agent,
    master_private_key_from_env,
    master_public_key_from_env,
)
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


# ── env PEM resolution (raw or base64) ────────────────────────────────────────


def test_pem_from_env_prefers_raw(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAW_K", "-----BEGIN PUBLIC KEY-----\nabc\n-----END")
    monkeypatch.delenv("B64_K", raising=False)
    assert _pem_from_env("RAW_K", "B64_K").startswith("-----BEGIN PUBLIC KEY-----")


def test_pem_from_env_decodes_base64(monkeypatch: pytest.MonkeyPatch) -> None:
    import base64

    pem = "-----BEGIN PUBLIC KEY-----\nxyz\n-----END"
    monkeypatch.delenv("RAW_K", raising=False)
    monkeypatch.setenv("B64_K", base64.b64encode(pem.encode()).decode())
    assert _pem_from_env("RAW_K", "B64_K") == pem


def test_pem_from_env_none_when_neither(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RAW_K", raising=False)
    monkeypatch.delenv("B64_K", raising=False)
    assert _pem_from_env("RAW_K", "B64_K") is None


def test_master_key_helpers_read_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MASTER_PUBLIC_KEY_PEM", "pub-pem")
    monkeypatch.setenv("MASTER_PRIVATE_KEY_PEM", "priv-pem")
    assert master_public_key_from_env() == "pub-pem"
    assert master_private_key_from_env() == "priv-pem"
