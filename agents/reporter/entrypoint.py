"""Reporter agent entrypoint — PRE_FLIGHT bootstrap.

Agent: reporter
Role: send EHLO to master, wait for ACTIVATE, then idle until event loop wired (S75+).
External I/O: master HTTP endpoint (POST /ehlo).
"""

from __future__ import annotations

import os

from kernel.bootstrap import activate_agent, idle_loop


def main() -> None:
    """Send EHLO to master, receive ACTIVATE, then idle."""
    master_url = os.environ.get("MASTER_URL", "http://master:8000")
    public_key_pem = os.environ.get("MASTER_PUBLIC_KEY_PEM") or None
    activate_agent(master_url, "reporter", public_key_pem=public_key_pem)
    idle_loop()


if __name__ == "__main__":  # pragma: no cover
    main()
