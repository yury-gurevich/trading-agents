"""Master bootstrap agent entrypoint.

Agent: master
Role: load RSA private key and secret store from env, start HTTP server on :8000.
External I/O: Neo4j (via GraphStore), Azure Key Vault (optional), TCP port 8000 (HTTP).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.master.agent import MasterAgent
from agents.master.http_server import serve
from kernel.crypto import generate_keypair

if TYPE_CHECKING:
    from agents.master.key_vault import SecretStore
    from agents.master.settings import MasterSettings
    from kernel import GraphStore


def build_app(
    graph: GraphStore,
    private_key_pem: str,
    settings: MasterSettings | None = None,
    secret_store: SecretStore | None = None,
) -> tuple[MasterAgent, str]:
    """Create and start MasterAgent; return (agent, private_key_pem). Testable."""
    agent = MasterAgent(graph=graph, settings=settings, secret_store=secret_store)
    agent.start()
    return agent, private_key_pem


def main() -> None:  # pragma: no cover
    """Load config from env and start the master HTTP server."""
    import logging
    import os

    from agents.master.key_vault import AzureKeyVaultSecretStore, EnvVarSecretStore
    from kernel.graph_neo4j import Neo4jGraphStore

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log = logging.getLogger("master")

    pem = os.environ.get("MASTER_PRIVATE_KEY_PEM") or ""
    if not pem:
        pem, pub = generate_keypair()
        log.info("[master] no MASTER_PRIVATE_KEY_PEM — generated dev keypair")
        log.info("[master] MASTER_PUBLIC_KEY_PEM=%s", pub)

    kv_url = os.environ.get("MASTER_KEY_VAULT_URL") or ""
    if kv_url:
        secret_store: SecretStore = AzureKeyVaultSecretStore(kv_url)
        log.info("[master] Key Vault: %s", kv_url)
    else:
        secret_store = EnvVarSecretStore()
        log.info("[master] no MASTER_KEY_VAULT_URL — secrets from env vars")

    graph = Neo4jGraphStore()
    agent, key_pem = build_app(graph, pem, secret_store=secret_store)
    log.info("[master] session=%s — serving on :8000", agent.session_id)
    serve(8000, agent, key_pem)


if __name__ == "__main__":  # pragma: no cover
    main()
