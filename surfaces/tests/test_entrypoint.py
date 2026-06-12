"""Entrypoint module smoke tests.

Agent: surfaces
Role: verify the entrypoint module is importable and exposes the expected callable.
External I/O: none.
"""

from __future__ import annotations

import surfaces.entrypoint as entrypoint_module


def test_entrypoint_main_is_callable() -> None:
    assert callable(entrypoint_module.main)
