"""S234: the brief preview prints what a fire would send, and sends and writes nothing.

Agent: tooling
Role: prove `scripts/brief_preview.py` on in-memory graphs shaped like the live one.
External I/O: none; the graph and clock are replaced in-process.
"""

from __future__ import annotations

from datetime import datetime, tzinfo
from typing import TYPE_CHECKING

import scripts.brief_preview as preview

from kernel import InMemoryGraphStore
from orchestration.tests.daily_brief_fixtures import at, seed_run
from orchestration.tests.daily_brief_scenarios import A1_TEXT, run_request, seed_pair

if TYPE_CHECKING:
    from collections.abc import Mapping

    import pytest

    from kernel import Node


class _SealedGraph(InMemoryGraphStore):
    """A graph that refuses every write once sealed: the preview may only read."""

    sealed = False

    def merge_node(
        self,
        label: str,
        key: str,
        props: Mapping[str, object],
        *,
        schema_version: int = 1,
    ) -> Node:
        assert not self.sealed, f"the preview wrote {label}"
        return super().merge_node(label, key, props, schema_version=schema_version)

    def add_edge(
        self,
        parent: Node,
        child: Node,
        edge_type: str,
        props: Mapping[str, object] | None = None,
    ) -> None:
        assert not self.sealed, f"the preview linked {edge_type}"
        super().add_edge(parent, child, edge_type, props)


class _Clock(datetime):
    @classmethod
    def now(cls, tz: tzinfo | None = None) -> datetime:  # type: ignore[override]
        return at(22, 50)


def _refuse_port(*_: object, **__: object) -> None:
    raise AssertionError("the preview built a Telegram port")


def _preview(monkeypatch: pytest.MonkeyPatch, graph: object, run_id: str) -> int:
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://unused")
    monkeypatch.setattr(preview, "_live_graph", lambda: graph)
    monkeypatch.setattr(preview, "datetime", _Clock)
    monkeypatch.setattr("orchestration.telegram_client.TelegramClient", _refuse_port)
    return preview.main(["--run-id", run_id, "--env-file", "missing.env"])


def test_a13_the_preview_prints_the_brief_and_sends_and_writes_nothing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """DSP-OUT-06 / DSP-IDM-03: the preview prints A1's brief, and only prints it.

    It composes with the dispatcher's own code, builds no Telegram port, writes no
    fact and leaves no marker, so the next fire still sends.
    """
    graph = _SealedGraph()
    seed_pair(graph)
    graph.sealed = True

    status = _preview(monkeypatch, graph, "sched-2026-09-25")

    assert status == 0
    assert capsys.readouterr().out == A1_TEXT + "\n"
    assert "brief_sent_at" not in run_request(graph).props


def test_the_preview_shows_the_red_brief_and_names_what_it_cannot_find(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """DSP-TRG-03: an unfinished run previews as RED; an unknown run is an error."""
    graph = InMemoryGraphStore()
    seed_run(graph, pm_created="2026-09-25T22:41:00+00:00", through="MonitorRun")

    red = _preview(monkeypatch, graph, "sched-2026-09-25")
    red_out = capsys.readouterr().out
    unknown = _preview(monkeypatch, graph, "sched-2026-01-02")

    assert red == 0
    assert red_out.splitlines()[:2] == [
        "\U0001f534 NOT FINISHED · sched-2026-09-25 · Sat 26 Sep 08:50",
        "Last stage finished: monitor",
    ]
    assert unknown == 1
    assert "no RunRequest for sched-2026-01-02" in capsys.readouterr().err


def test_the_preview_needs_the_graph(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """S234: with no POSTGRES_DSN the preview stops before touching any graph."""
    monkeypatch.delenv("POSTGRES_DSN", raising=False)

    status = preview.main(["--run-id", "sched-2026-09-25", "--env-file", "missing.env"])

    assert status == 1
    assert "POSTGRES_DSN is required" in capsys.readouterr().err
