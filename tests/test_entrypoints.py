"""Parametrized smoke tests for idle-loop trading-agent entrypoints.

Each entrypoint must:
  - import without error
  - call activate_agent with the correct agent_type when main() runs
  - call idle_loop() after activate

Note: the provider entrypoint runs a real ingest loop and the scanner/analyst/PM/
execution/monitor/reporter run graph-pull work loops (not idle_loop); the supervisor
and operator now serve over serve_loop (S98). All of those are tested separately under
their own agents/<name>/tests/ packages (e.g. build_served_bus). Only the still-idle
control-plane stubs remain here.
"""

from __future__ import annotations

import importlib

import pytest

_AGENTS = [
    ("agents.forecaster.entrypoint", "forecaster"),
    ("agents.curator.entrypoint", "curator"),
    ("agents.researcher.entrypoint", "researcher"),
]


@pytest.mark.parametrize(("module_path", "agent_type"), _AGENTS)
def test_entrypoint_calls_activate_with_correct_agent_type(
    module_path: str, agent_type: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each entrypoint passes its own agent_type string to activate_agent."""
    calls: list[tuple] = []
    mod = importlib.import_module(module_path)
    monkeypatch.setattr(mod, "activate_agent", lambda *a, **kw: calls.append(a) or {})
    monkeypatch.setattr(mod, "idle_loop", lambda: None)
    mod.main()
    assert len(calls) == 1, f"{module_path}: activate_agent not called"
    assert calls[0][1] == agent_type, (
        f"{module_path}: expected {agent_type!r}, got {calls[0][1]!r}"
    )


@pytest.mark.parametrize(("module_path", "_"), _AGENTS)
def test_entrypoint_calls_idle_loop_after_activate(
    module_path: str, _: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """idle_loop() is called after activate_agent() (blocks until S75 wires loop)."""
    idle_called: list[bool] = []
    mod = importlib.import_module(module_path)
    monkeypatch.setattr(mod, "activate_agent", lambda *a, **kw: {})
    monkeypatch.setattr(mod, "idle_loop", lambda: idle_called.append(True))
    mod.main()
    assert idle_called, f"{module_path}: idle_loop() not called"
