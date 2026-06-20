"""Master bootstrap agent entrypoint.

Agent: master
Role: load RSA private key from env, create MasterAgent, start HTTP server on :8000.
External I/O: Neo4j (via GraphStore), TCP port 8000 (HTTP).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.master.agent import MasterAgent
from agents.master.http_server import serve
from kernel.crypto import generate_keypair

if TYPE_CHECKING:
    from agents.master.settings import MasterSettings
    from kernel import GraphStore


def build_app(
    graph: GraphStore,
    private_key_pem: str,
    settings: MasterSettings | None = None,
) -> tuple[MasterAgent, str]:
    """Create and start MasterAgent; return (agent, private_key_pem). Testable."""
    agent = MasterAgent(graph=graph, settings=settings)
    agent.start()
    return agent, private_key_pem


def main() -> None:  # pragma: no cover
    """Load config from env and start the master HTTP server."""
    import logging
    import os

    from kernel.graph_neo4j import Neo4jGraphStore

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log = logging.getLogger("master")

    pem = os.environ.get("MASTER_PRIVATE_KEY_PEM") or ""
    if not pem:
        pem, pub = generate_keypair()
        log.info("[master] no MASTER_PRIVATE_KEY_PEM — generated dev keypair")
        log.info("[master] MASTER_PUBLIC_KEY_PEM=%s", pub)

    graph = Neo4jGraphStore()
    agent, key_pem = build_app(graph, pem)
    log.info("[master] session=%s — serving on :8000", agent.session_id)
    serve(8000, agent, key_pem)


if __name__ == "__main__":  # pragma: no cover
    main()
