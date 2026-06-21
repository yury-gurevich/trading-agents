"""Secret store abstractions for Key Vault and local-dev fallback.

Agent: master
Role: resolve per-agent secrets from Azure Key Vault (prod) or env vars (dev).
External I/O: Azure Key Vault (AzureKeyVaultSecretStore only).
"""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable


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
