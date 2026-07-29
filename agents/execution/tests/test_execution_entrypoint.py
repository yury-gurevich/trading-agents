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
    monkeypatch.setattr(ep, "find_pending_work", lambda graph_arg: ["work-item"])

    def fake_process(
        item: object, *, graph: object, broker: object, settings: object
    ) -> None:
        seen["item"] = item
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
        process_one("work-item")

    monkeypatch.setattr(ep, "process_work_item", fake_process)
    monkeypatch.setattr(ep, "work_loop", fake_work_loop)
    monkeypatch.setenv("EXECUTION_POLL_INTERVAL", "7")

    ep.main()

    assert seen["pending"] == ["work-item"]
    assert seen["item"] == "work-item"
    assert seen["graph"] is graph
    assert seen["broker"] is broker
    assert seen["poll_interval"] == 7
