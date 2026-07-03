"""Entrypoint guard tests.

Agent: kernel
Role: ensure agent entrypoints do not retain retired placeholder loop wiring.
External I/O: none.
"""

from __future__ import annotations

from pathlib import Path

import kernel.bootstrap as bootstrap

_ENTRYPOINTS = tuple(Path("agents").glob("*/entrypoint.py"))


def test_no_agent_entrypoint_references_retired_loop() -> None:
    """FORE-TRG-02 / CUR-TRG-02 / RES-TRG-03: no control-plane idle loops."""
    retired_symbol = "idle" + "_loop"
    offenders = [
        path.as_posix()
        for path in _ENTRYPOINTS
        if retired_symbol in path.read_text(encoding="utf-8")
    ]

    assert offenders == []


def test_bootstrap_retired_placeholder_symbol() -> None:
    """PRE-FLIGHT bootstrap no longer exposes a do-nothing control-plane loop."""
    assert not hasattr(bootstrap, "idle" + "_loop")
