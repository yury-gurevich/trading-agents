"""RSA-PSS sign / verify utilities shared by master signing and agent bootstrap.

Agent: kernel
Role: sign and verify RSA-PSS signatures; generate dev keypairs.
External I/O: none.
"""

from __future__ import annotations

import base64

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

_PSS = padding.PSS(
    mgf=padding.MGF1(hashes.SHA256()),
    salt_length=padding.PSS.MAX_LENGTH,
)


def generate_keypair() -> tuple[str, str]:
    """Return (private_pem, public_pem). For dev / testing only."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = (
        key.public_key()
        .public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    return private_pem, public_pem


def sign_pss(private_pem: str, data: str) -> str:
    """Sign *data* with the RSA private key; return URL-safe base64 signature."""
    key = serialization.load_pem_private_key(private_pem.encode(), password=None)
    assert isinstance(key, RSAPrivateKey)
    raw = key.sign(data.encode(), _PSS, hashes.SHA256())
    return base64.urlsafe_b64encode(raw).decode()


def verify_pss(public_pem: str, data: str, signature: str) -> None:
    """Verify *signature* over *data*; raises InvalidSignature on mismatch."""
    key = serialization.load_pem_public_key(public_pem.encode())
    assert isinstance(key, RSAPublicKey)
    raw = base64.urlsafe_b64decode(signature.encode())
    key.verify(raw, data.encode(), _PSS, hashes.SHA256())
