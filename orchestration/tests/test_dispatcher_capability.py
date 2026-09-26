"""The dispatcher reads, writes and sends only what its law book's CAP declares.

Agent: orchestration
Role: make the dispatcher's CAP block a checked declaration, not a remembered one.
External I/O: reads orchestration/laws/dispatcher/laws.md.

DL-70: a declaration no code reads is indistinguishable from a live one. This test
records what real fires touch and holds it against the JSON the law book states.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

from kernel import InMemoryGraphStore
from orchestration.tests.daily_brief_fixtures import at, fire, seed_run
from orchestration.tests.daily_brief_scenarios import seed_pair
from orchestration.tests.scheduled_dispatch_human_helpers import (
    FakeAnswer,
    FakeTelegram,
    preflight,
)

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from kernel import Node

_LAWS = Path(__file__).resolve().parents[1] / "laws" / "dispatcher" / "laws.md"
_LLM_ONLY = ("unrecoverable:operator:anthropic:unrecoverable:http_400",)


class _Recording(InMemoryGraphStore):
    """An in-memory graph that remembers which labels a fire read and wrote."""

    def __init__(self) -> None:
        super().__init__()
        self.recording = False
        self.read: set[str] = set()
        self.written: set[str] = set()

    def get_node(self, label: str, key: str) -> Node | None:
        self._saw(self.read, label)
        return super().get_node(label, key)

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        self._saw(self.read, label)
        return super().list_nodes(label)

    def ancestors(
        self, node: Node, *, max_depth: int, edge_types: set[str] | None = None
    ) -> Iterator[Node]:
        found = list(
            super().ancestors(node, max_depth=max_depth, edge_types=edge_types)
        )
        for item in found:
            self._saw(self.read, item.label)
        return iter(found)

    def descendants(
        self, node: Node, *, max_depth: int, edge_types: set[str] | None = None
    ) -> Iterator[Node]:
        found = list(
            super().descendants(node, max_depth=max_depth, edge_types=edge_types)
        )
        for item in found:
            self._saw(self.read, item.label)
        return iter(found)

    def merge_node(
        self,
        label: str,
        key: str,
        props: Mapping[str, object],
        *,
        schema_version: int = 1,
    ) -> Node:
        self._saw(self.written, label)
        return super().merge_node(label, key, props, schema_version=schema_version)

    def _saw(self, into: set[str], label: str) -> None:
        if self.recording:
            into.add(label)


def _declared() -> dict[str, dict[str, list[str]]]:
    section = _LAWS.read_text(encoding="utf-8").split("(`CAP`)", 1)[1]
    match = re.search(r"```json\n(.*?)\n```", section, re.DOTALL)
    assert match is not None
    return dict(json.loads(match.group(1)))


def _operations(telegram: FakeTelegram) -> set[str]:
    used = {
        "send_notice": bool(telegram.sent or telegram.degraded_sent),
        "poll_answer": bool(telegram.polls),
        "ack_answer": bool(telegram.acknowledgements),
        "confirm_offset": bool(telegram.confirmations),
        "send_brief": bool(telegram.briefs),
    }
    return {name for name, seen in used.items() if seen}


def test_every_fire_stays_inside_the_declared_capability() -> None:
    """CAP / DSP-DEP-01 (graph and port halves): what fires touch is declared.

    A placement that briefs, a RED brief, a held run answered `run_now`, a degraded
    placement, and a brief that fails into a fault together use every declared
    Telegram operation; every label they read, write or send through is in CAP.
    """
    finished, red, held, degraded, failed = (_Recording() for _ in range(5))
    seed_pair(finished)
    seed_run(red, pm_created="2026-09-25T22:41:00+00:00", through="ExecutionRun")
    preflight(held, passed=False, checked_at=at(22, 25))
    preflight(degraded, passed=False, checked_at=at(22, 25), failures=_LLM_ONLY)
    seed_pair(failed)
    answer = FakeAnswer(5, "run_now", "sched-2026-09-25", "cb-5")
    telegram = FakeTelegram()
    fires = (
        (finished, telegram, at(22, 50)),
        (red, telegram, at(23, 50)),
        (held, telegram, at(22, 30)),
        (held, FakeTelegram(answers=(answer,)), at(22, 40)),
        (degraded, telegram, at(22, 30)),
        (failed, FakeTelegram(brief_raises=True), at(22, 50)),
    )
    operations: set[str] = set()
    for graph, port, now in fires:
        graph.recording = True
        fire(graph, port, now)
        operations |= _operations(port)
    graphs = (finished, red, held, degraded, failed)
    cap = _declared()

    written = {label for graph in graphs for label in graph.written}
    read = {label for graph in graphs for label in graph.read}
    assert operations == set(cap["telegram"]["operations"])
    assert written <= set(cap["graph"]["labels_written"])
    assert read <= set(cap["graph"]["labels_read"])
