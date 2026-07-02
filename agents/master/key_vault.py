"""Secret store abstractions for Key Vault and local-dev fallback.

Agent: master
Role: resolve per-agent secrets from Azure Key Vault (prod) or env vars (dev).
External I/O: Azure Key Vault (AzureKeyVaultSecretStore only).
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import Callable


@runtime_checkable
class SecretStore(Protocol):
    """Protocol for resolving named secrets."""

    def get_secret(self, name: str) -> str:
        """Return the secret value, or empty string if not found."""
        ...  # pragma: no cover


class NullSecretStore:
    """Returns empty string for every secret. Default when no store is configured."""

    def get_secret(self, _name: str) -> str:
        """Always return empty string."""
        return ""


class EnvVarSecretStore:
    """Reads secrets from environment variables — local-dev fallback.

    Converts kebab-case secret names to UPPER_SNAKE env vars:
    ``tiingo-api-key`` → ``TIINGO_API_KEY``.
    """

    def get_secret(self, name: str) -> str:
        """Look up env var derived from *name*; return '' if not set."""
        return os.environ.get(name.upper().replace("-", "_"), "")


class CachingSecretStore:
    """Cache secrets fetched from an inner store for repeated references (DL-36).

    A Key Vault round-trip on every repeated reference is wasteful — the master
    fetches the same secrets for many agents. Cache each fetched value for
    ``ttl_minutes`` (0 = never expires). Only non-empty fetches are cached, so a
    missing secret is re-fetched and a newly-seeded one is picked up.
    """

    def __init__(
        self,
        inner: SecretStore,
        ttl_minutes: int,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Wrap *inner*; cache fetched secrets for *ttl_minutes* (0 = never expires)."""
        self._inner = inner
        self._ttl = timedelta(minutes=ttl_minutes)
        self._never = ttl_minutes == 0
        self._clock = clock or (lambda: datetime.now(UTC))
        self._cache: dict[str, tuple[str, datetime]] = {}

    def get_secret(self, name: str) -> str:
        """Return the cached value if fresh, else fetch from the inner store."""
        hit = self._cache.get(name)
        if hit is not None:
            value, fetched_at = hit
            if self._never or (self._clock() - fetched_at) < self._ttl:
                return value
        value = self._inner.get_secret(name)
        if value:
            self._cache[name] = (value, self._clock())
        return value


class AzureKeyVaultSecretStore:  # pragma: no cover
    """Reads secrets from Azure Key Vault using DefaultAzureCredential."""

    def __init__(self, vault_url: str) -> None:
        """Connect to the Key Vault at *vault_url* using DefaultAzureCredential."""
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        self._client = SecretClient(
            vault_url=vault_url, credential=DefaultAzureCredential()
        )

    def get_secret(self, name: str) -> str:
        """Fetch *name* from Key Vault; return '' on not-found or empty value.

        Matches Null/EnvVar stores: a missing secret is skipped, not an error
        (resolve_config omits empty values), so unseeded entitlements are fine.
        """
        from azure.core.exceptions import ResourceNotFoundError

        try:
            value = self._client.get_secret(name).value
        except ResourceNotFoundError:
            return ""
        return value or ""
