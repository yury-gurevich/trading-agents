"""Execution entrypoint import smoke test.

Agent: execution
Role: ensure the graph-pull entrypoint module imports and exposes main().
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import agents.execution.entrypoint as ep

if TYPE_CHECKING:
    from collections.abc import Callable

    import pytest


def test_entrypoint_exposes_main() -> None:
    assert callable(ep.main)


def test_main_uses_settings_broker_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    graph = object()
    broker = object()
    seen = {}

    monkeypatch.setattr(ep, "activate_agent", lambda *args, **kwargs: None)
    monkeypatch.setattr(ep, "master_public_key_from_env", lambda: "pub")
    monkeypatch.setattr(ep, "build_graph_from_env", lambda: graph)
    monkeypatch.setattr(ep, "broker_from_settings", lambda settings: broker)
    monkeypatch.setattr(ep, "find_pending", lambda graph_arg: ["pm-node"])

    def fake_execute(
        node: object, *, graph: object, broker: object, settings: object
    ) -> None:
        seen["node"] = node
        seen["graph"] = graph
        seen["broker"] = broker
        seen["settings"] = settings

    def fake_work_loop(
        find_pending: Callable[[], list[str]],
        process_one: Callable[[str], None],
        *,
        poll_interval: int,
    ) -> None:
        seen["pending"] = find_pending()
        seen["poll_interval"] = poll_interval
        process_one("pm-node")

    monkeypatch.setattr(ep, "execute_pm_node", fake_execute)
    monkeypatch.setattr(ep, "work_loop", fake_work_loop)
    monkeypatch.setenv("EXECUTION_POLL_INTERVAL", "7")

    ep.main()

    assert seen["pending"] == ["pm-node"]
    assert seen["node"] == "pm-node"
    assert seen["graph"] is graph
    assert seen["broker"] is broker
    assert seen["poll_interval"] == 7
