"""Key Vault secret writes for Service Bus SAS tooling.

Agent: tooling
Role: store generated connection strings without putting values on CLI argv.
External I/O: Azure CLI access-token lookup and Key Vault HTTPS API.
"""

from __future__ import annotations

import json
from urllib.parse import quote
from urllib.request import Request, urlopen

from scripts.sb_sas_cli import az_cli

KEY_VAULT_RESOURCE = "https://vault.azure.net"
KEY_VAULT_API_VERSION = "7.4"
KEY_VAULT_TIMEOUT_SECONDS = 30


def set_secret(vault_name: str, secret_name: str, value: str) -> None:
    """Set one Key Vault secret using an in-memory HTTPS request body."""
    token = _access_token()
    url = (
        f"https://{vault_name}.vault.azure.net/secrets/"
        f"{quote(secret_name)}?api-version={KEY_VAULT_API_VERSION}"
    )
    body = json.dumps({"value": value}).encode("utf-8")
    request = Request(  # noqa: S310 - fixed https Key Vault URL.
        url,
        data=body,
        method="PUT",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urlopen(  # noqa: S310 - fixed https Key Vault URL.
        request, timeout=KEY_VAULT_TIMEOUT_SECONDS
    ) as response:
        response.read()


def _access_token() -> str:
    token = az_cli(
        [
            "account",
            "get-access-token",
            "--resource",
            KEY_VAULT_RESOURCE,
            "--query",
            "accessToken",
            "-o",
            "tsv",
        ],
        capture=True,
    ).strip()
    if not token:
        raise RuntimeError("Azure CLI did not return a Key Vault token")
    return token
