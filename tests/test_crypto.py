"""Tests for kernel.crypto RSA-PSS sign / verify utilities."""

from __future__ import annotations

import pytest
from cryptography.exceptions import InvalidSignature

from kernel.crypto import generate_keypair, sign_pss, verify_pss


@pytest.fixture(scope="module")
def keypair() -> tuple[str, str]:
    return generate_keypair()


def test_generate_keypair_returns_pem_strings(keypair: tuple[str, str]) -> None:
    private, public = keypair
    assert ("BEGIN " + "PRIVATE KEY") in private  # split to avoid secret scanner
    assert ("BEGIN " + "PUBLIC KEY") in public


def test_sign_and_verify_round_trip(keypair: tuple[str, str]) -> None:
    private, public = keypair
    sig = sign_pss(private, "hello")
    verify_pss(public, "hello", sig)  # must not raise


def test_verify_rejects_tampered_data(keypair: tuple[str, str]) -> None:
    private, public = keypair
    sig = sign_pss(private, "original")
    with pytest.raises(InvalidSignature):
        verify_pss(public, "tampered", sig)


def test_verify_rejects_bad_signature(keypair: tuple[str, str]) -> None:
    _, public = keypair
    with pytest.raises(InvalidSignature):
        verify_pss(public, "data", "bm90YXNpZ25hdHVyZQ==")


def test_sign_returns_urlsafe_base64_no_plus(keypair: tuple[str, str]) -> None:
    private, _ = keypair
    sig = sign_pss(private, "test")
    assert "+" not in sig


def test_sign_returns_urlsafe_base64_no_slash(keypair: tuple[str, str]) -> None:
    private, _ = keypair
    sig = sign_pss(private, "test")
    assert "/" not in sig
