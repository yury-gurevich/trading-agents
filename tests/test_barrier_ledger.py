"""S241: the barrier ledger script prints the scorecard and each settlement, only.

Agent: tooling
Role: prove `scripts/barrier_ledger.py` on in-memory graphs shaped like the live one:
      it composes with the forecaster's own scorecard, prints one line per settlement,
      prints an empty ledger without error, and never writes.
External I/O: none; the graph is replaced in-process.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

import scripts.barrier_ledger as ledger

from agents.forecaster.domain.barrier_settlement import (
    NO_SETTLING_BARS,
    VOID,
    Settlement,
)
from agents.forecaster.settlement_store import write_settlement
from agents.forecaster.tests.settlement_helpers import seed_claim
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from collections.abc import Mapping

    import pytest

    from kernel import Node


class _SealedGraph(InMemoryGraphStore):
    """A graph that refuses every write once sealed: the script may only read."""

    sealed = False

    def merge_node(
        self,
        label: str,
        key: str,
        props: Mapping[str, object],
        *,
        schema_version: int = 1,
    ) -> Node:
        assert not self.sealed, f"the ledger wrote {label}"
        return super().merge_node(label, key, props, schema_version=schema_version)

    def add_edge(
        self,
        parent: Node,
        child: Node,
        edge_type: str,
        props: Mapping[str, object] | None = None,
    ) -> None:
        assert not self.sealed, f"the ledger linked {edge_type}"
        super().add_edge(parent, child, edge_type, props)


def _run(monkeypatch: pytest.MonkeyPatch, graph: object, *args: str) -> int:
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://unused")
    monkeypatch.setattr(ledger, "_live_graph", lambda: graph)
    return ledger.main(["--env-file", "missing.env", *args])


def test_the_ledger_prints_the_scorecard_and_each_settlement(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Two settled claims on two dates, one void and one open: the counts, the scores
    and one line per settlement, from a graph that refuses every write."""
    graph = _SealedGraph()
    first, second = date(2026, 9, 28), date(2026, 9, 29)
    for ticker, day, outcome in (("AAPL", first, "target"), ("MSFT", second, "stop")):
        claim = seed_claim(graph, ticker=ticker, as_of=day)
        write_settlement(
            graph,
            claim,
            Settlement(outcome, None, day + timedelta(days=14), 101.0, 1.01),
            settling_ref="market-data:sched-2026-10-12",
        )
    void = seed_claim(graph, ticker="NVDA", as_of=first)
    write_settlement(
        graph,
        void,
        Settlement(VOID, NO_SETTLING_BARS, first + timedelta(days=45), None, None),
        settling_ref=None,
    )
    seed_claim(graph, ticker="AMZN", as_of=second)
    graph.sealed = True

    status = _run(monkeypatch, graph)

    out = capsys.readouterr().out
    assert status == 0
    assert "settled 2  void 1  open 1" in out
    assert "brier_model" in out
    assert "skill" in out
    lines = [line for line in out.splitlines() if line.startswith("2026-")]
    assert len(lines) == 3
    assert "AAPL" in lines[0]
    assert "target" in lines[0]
    assert "void (no_settling_bars)" in lines[1]
    assert "MSFT" in lines[2]


def test_an_empty_ledger_prints_zero_settled(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """F3's shape: no claim yet prints an empty ledger and exits 0."""
    graph = _SealedGraph()
    graph.sealed = True

    status = _run(monkeypatch, graph, "--model-id", "barrier-garch-v1")

    out = capsys.readouterr().out
    assert status == 0
    assert "settled 0  void 0  open 0" in out
    assert "no settled claim yet" in out


def test_the_ledger_needs_a_postgres_dsn(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Without POSTGRES_DSN the script says so and exits 1, reading nothing."""
    monkeypatch.delenv("POSTGRES_DSN", raising=False)

    status = ledger.main(["--env-file", "missing.env"])

    assert status == 1
    assert "POSTGRES_DSN is required" in capsys.readouterr().err
