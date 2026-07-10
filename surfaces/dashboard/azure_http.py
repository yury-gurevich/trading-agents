"""Authenticated JSON send seam for the dashboard's Azure REST reader.

Agent: surfaces
Role: isolate Azure Identity token acquisition and bounded HTTPS JSON transport.
External I/O: Azure Identity credential chain and HTTPS through urllib.
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Any, Literal, Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from surfaces.dashboard.azure_port import AzureReadError

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


class _Token(Protocol):
    token: str


class _Credential(Protocol):
    def get_token(self, scope: str) -> _Token:
        """Return an access token for one Azure resource scope."""
        ...  # pragma: no cover - protocol declaration only.


class JsonSend(Protocol):
    """Injectable authenticated JSON request seam."""

    def __call__(
        self, method: str, url: str, scope: str, body: Mapping[str, object] | None
    ) -> dict[str, object]:
        """Send one request and return a decoded JSON object."""
        ...  # pragma: no cover - protocol declaration only.


class AzureIdentitySend:
    """Thin Azure Identity + urllib JSON sender."""

    def __init__(
        self,
        *,
        timeout: float,
        credential_mode: CredentialMode = "auto",
        credential: _Credential | None = None,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        """Bind a credential and injectable HTTPS opener."""
        self._timeout = timeout
        self._credential = credential or _credential_from_env(credential_mode)
        self._opener = opener

    def __call__(
        self, method: str, url: str, scope: str, body: Mapping[str, object] | None
    ) -> dict[str, object]:
        """Send one bearer-authenticated JSON request with sanitized errors."""
        encoded = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {
            "Authorization": f"Bearer {self._credential.get_token(scope).token}",
            "Accept": "application/json",
        }
        if encoded is not None:
            headers["Content-Type"] = "application/json"
        request = Request(  # noqa: S310 - fixed HTTPS Azure origins are supplied.
            url, data=encoded, headers=headers, method=method
        )
        try:
            with self._opener(request, timeout=self._timeout) as response:
                return cast("dict[str, object]", json.load(response))
        except (HTTPError, URLError, TimeoutError) as exc:
            code = getattr(exc, "code", "transport")
            raise AzureReadError(f"Azure read failed ({code})") from None


CredentialMode = Literal["auto", "default", "cli", "service_principal"]


def _credential_from_env(mode: CredentialMode = "auto") -> _Credential:
    """Prefer the existing local AZURE_SP_* trio, then the default chain."""
    tenant = os.environ.get("AZURE_SP_TENANT_ID")
    client = os.environ.get("AZURE_SP_CLIENT_ID")
    secret = os.environ.get("AZURE_SP_CLIENT_SECRET")
    if mode == "cli":
        from azure.identity import AzureCliCredential

        return cast("_Credential", AzureCliCredential())
    if mode in ("auto", "service_principal") and tenant and client and secret:
        from azure.identity import ClientSecretCredential

        return cast("_Credential", ClientSecretCredential(tenant, client, secret))
    if mode == "service_principal":
        raise AzureReadError("Azure service-principal credential unavailable")
    from azure.identity import DefaultAzureCredential

    return cast("_Credential", DefaultAzureCredential())
