"""Monitor entrypoint import smoke test.

Agent: monitor
Role: ensure the graph-pull entrypoint module imports and exposes main().
External I/O: none.
"""

from __future__ import annotations

import agents.monitor.entrypoint as ep


def test_entrypoint_exposes_main() -> None:
    assert callable(ep.main)
