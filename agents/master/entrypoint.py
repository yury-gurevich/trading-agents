"""Master bootstrap agent entrypoint.

Agent: master
Role: load RSA private key and secret store from env, start HTTP server on :8000.
External I/O: Neo4j (via GraphStore), Azure Key Vault (optional), TCP port 8000 (HTTP).
"""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING

from agents.master.agent import MasterAgent
from agents.master.grants import load_grant_policy, parse_grant_policy
from agents.master.http_server import serve
from agents.master.secret_map import load_secret_map, parse_secret_map
from agents.master.settings import MasterSettings
from kernel.crypto import generate_keypair

if TYPE_CHECKING:
    from collections.abc import Callable

    from agents.master.grants import GrantPolicy
    from agents.master.key_vault import SecretStore
    from agents.master.secret_map import SecretMap
    from kernel import GraphStore


def _resolve_pack[T](
    b64: str,
    path: str,
    parse: Callable[[str], T],
    load: Callable[[str], T],
) -> T | None:
    """Resolve pack data: base64 env content (cloud) -> file path (local) -> None.

    b64 wins so the master image stays pack-agnostic — the pack is injected at
    deploy time, never baked into the image.
    """
    if b64:
        return parse(base64.b64decode(b64).decode("utf-8"))
    if path:
        return load(path)
    return None


def select_graph_store(graph_kind: str) -> GraphStore:
    """Pick the master's graph store.

    ``memory`` runs the operational registry in-process (rebuilt on boot). ``auto``
    follows the shared fleet selector: ``POSTGRES_DSN`` wins, ``NEO4J_URI`` remains
    the rollback backend, and neither falls back to memory for local development.
    """
    if graph_kind == "memory":
        from kernel import InMemoryGraphStore

        return InMemoryGraphStore()
    if graph_kind == "neo4j":
        from kernel.graph_neo4j import Neo4jGraphStore  # pragma: no cover

        return Neo4jGraphStore()  # pragma: no cover
    if graph_kind in ("", "auto", "postgres"):
        from kernel.graph_env import build_graph_from_env

        return build_graph_from_env()
    raise ValueError(f"unknown MASTER_GRAPH {graph_kind!r}")


def build_app(
    graph: GraphStore,
    private_key_pem: str,
    settings: MasterSettings | None = None,
    secret_store: SecretStore | None = None,
) -> tuple[MasterAgent, str]:
    """Create and start MasterAgent; return (agent, private_key_pem). Testable.

    The trading grant policy and secret map are injected from pack data — base64 env
    content (cloud) or a file path (local) — so the substrate itself ships no
    agent-type or secret knowledge.
    """
    settings = settings or MasterSettings()
    grant_policy: GrantPolicy | None = _resolve_pack(
        settings.grant_policy_b64,
        settings.grant_policy_path,
        parse_grant_policy,
        load_grant_policy,
    )
    secret_map: SecretMap | None = _resolve_pack(
        settings.secret_map_b64,
        settings.secret_map_path,
        parse_secret_map,
        load_secret_map,
    )
    agent = MasterAgent(
        graph=graph,
        settings=settings,
        secret_store=secret_store,
        grant_policy=grant_policy,
        secret_map=secret_map,
    )
    agent.start()
    return agent, private_key_pem


def main() -> None:  # pragma: no cover
    """Load config from env and start the master HTTP server."""
    import logging
    import os

    from agents.master.key_vault import (
        AzureKeyVaultSecretStore,
        CachingSecretStore,
        EnvVarSecretStore,
    )
    from kernel.bootstrap import master_private_key_from_env

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log = logging.getLogger("master")

    pem = master_private_key_from_env() or ""
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

    settings = MasterSettings()
    secret_store = CachingSecretStore(secret_store, settings.secret_cache_ttl_minutes)
    log.info("[master] secret cache TTL: %d min", settings.secret_cache_ttl_minutes)

    graph_kind = os.environ.get("MASTER_GRAPH", "auto")
    graph = select_graph_store(graph_kind)
    log.info("[master] graph store: %s", graph_kind)
    # Fail SAFE, not fatal: a bad Neo4j connection here must not crash the process,
    # or the container manager restarts us in a loop and hammers auth until Aura
    # locks the account (observed 2026-07). Halt instead, loudly. See kernel.startup.
    from kernel.startup import ensure_reachable_or_halt

    ensure_reachable_or_halt(graph)
    log.info("[master] graph reachable")
    agent, key_pem = build_app(graph, pem, settings=settings, secret_store=secret_store)
    log.info("[master] session=%s — serving on :8000", agent.session_id)
    serve(8000, agent, key_pem)


if __name__ == "__main__":  # pragma: no cover
    main()
