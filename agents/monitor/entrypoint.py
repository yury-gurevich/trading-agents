"""Monitor agent entrypoint -- PRE_FLIGHT bootstrap.

Agent: monitor
Role: EHLO to master, verify the signed ACTIVATE, then idle.
External I/O: master HTTP endpoint (POST /ehlo).
"""

from __future__ import annotations

import os

from kernel.bootstrap import activate_agent, idle_loop, master_public_key_from_env


def main() -> None:
    """Send EHLO to master, receive signed ACTIVATE, verify it, then idle."""
    master_url = os.environ.get("MASTER_URL", "http://master:8000")
    pubkey = master_public_key_from_env()
    activate_agent(master_url, "monitor", public_key_pem=pubkey)
    idle_loop()


if __name__ == "__main__":  # pragma: no cover
    main()
