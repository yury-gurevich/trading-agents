"""S241 C5 / C6: a settlement records what the ledger needs, once.

Agent: forecaster
Role: prove one pass over a run whose MarketData covers a claim writes one complete
      BarrierSettlement linked from the claim, with the claim's three-class Brier,
      through the pack's fail-closed vocabulary guard; and that a second pass over
      the same run, or a later run covering the same claim, writes nothing new.
External I/O: reads the trading pack's vocabulary (orchestration/packs).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from agents.forecaster.settlement_pass import (
    find_pending_settlement,
    settle_analyst_node,
)
from agents.forecaster.tests.settlement_helpers import seed_claim, seed_run
from agents.forecaster.tests.settlement_paths import AS_OF, ohlcv, path
from kernel import CollectingFaultSink, InMemoryGraphStore
from kernel.graph_guarded import GuardedGraphStore
from kernel.graph_vocabulary import Vocabulary
from kernel.work_loop import run_once

if TYPE_CHECKING:
    from kernel import Node

_PACK = Path(__file__).resolve().parents[3] / "orchestration/packs"
_VOCABULARY = _PACK / "trading_graph_vocabulary.json"
_CLAIM_KEY = f"barrier-garch-v1:AAPL:{AS_OF.isoformat()}"
#: session 2's high reaches the target (107) first.
_TARGET_PATH = path(events={2: (108.0, 99.0)})
_SETTLED_ON = _TARGET_PATH[-1].day


def test_a_settlement_records_every_field_the_ledger_needs() -> None:
    """FORE-OUT-08 / FORE-IDN-02 / FORE-NEV-04: one pass writes one settlement with
    every field, linked BarrierForecast -SETTLED_BY-> BarrierSettlement, from bars
    read off the run's provider-written MarketData; brier is the three-class Brier
    of (0.3, 0.5, 0.2) against the target: 0.3^2 + 0.5^2 + 0.2^2 = 0.38."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    claim = seed_claim(graph)
    run = seed_run(graph, "run-a", bars=ohlcv("AAPL", _TARGET_PATH))

    settle_analyst_node(run, graph=graph, sink=sink)

    [settlement] = graph.list_nodes("BarrierSettlement")
    props = dict(settlement.props)
    created = datetime.fromisoformat(str(props.pop("created_at")))
    assert settlement.key == f"settlement:{_CLAIM_KEY}"
    assert props == {
        "claim_key": _CLAIM_KEY,
        "model_id": "barrier-garch-v1",
        "ticker": "AAPL",
        "as_of": AS_OF.isoformat(),
        "outcome": "target",
        "void_reason": None,
        "settled_on": _SETTLED_ON.isoformat(),
        "settling_ref": "market-data:run-a",
        "entry_close_settling": 100.0,
        "entry_ratio": 1.0,
        "brier": pytest.approx(0.38, abs=1e-12),
    }
    assert created.tzinfo is not None
    assert list(graph.descendants(claim, max_depth=1, edge_types={"SETTLED_BY"})) == [
        settlement
    ]
    [done] = graph.list_nodes("BarrierSettlementPass")
    assert done.key == "settlement-pass:run-a"
    assert (done.props["settled"], done.props["voided"], done.props["open"]) == (
        1,
        0,
        0,
    )
    assert done.props["settling_ref"] == "market-data:run-a"
    assert sink.faults == []


def test_a_split_settles_void_with_no_brier() -> None:
    """FORE-FAIL-05 / FORE-OUT-08: a 2:1 split in the window is recorded void,
    suspected_corporate_action, with no Brier; the settling close is kept."""
    graph = InMemoryGraphStore()
    seed_claim(graph)
    split = path(closes={4: 50.0}, events={4: (50.5, 49.5)})
    run = seed_run(
        graph,
        "run-split",
        bars=ohlcv("AAPL", split),
        created=AS_OF + timedelta(days=20),
    )

    settle_analyst_node(run, graph=graph)

    [settlement] = graph.list_nodes("BarrierSettlement")
    assert settlement.props["outcome"] == "void"
    assert settlement.props["void_reason"] == "suspected_corporate_action"
    assert settlement.props["brier"] is None
    assert settlement.props["settled_on"] == (AS_OF + timedelta(days=20)).isoformat()
    assert settlement.props["entry_close_settling"] == 100.0


def test_the_settlement_passes_the_packs_vocabulary_guard() -> None:
    """FORE-IDN-02 / FORE-OUT-08: both new labels, their properties, both edges and
    their signatures are declared, so the fail-closed guard admits the pass."""
    vocabulary = Vocabulary.from_mapping(
        json.loads(_VOCABULARY.read_text(encoding="utf-8"))
    )
    graph = GuardedGraphStore(InMemoryGraphStore(), vocabulary)
    sink = CollectingFaultSink()
    seed_claim(graph)
    run = seed_run(graph, "run-guarded", bars=ohlcv("AAPL", _TARGET_PATH))

    settle_analyst_node(run, graph=graph, sink=sink)

    assert sink.faults == []
    assert len(graph.list_nodes("BarrierSettlement")) == 1
    assert len(graph.list_nodes("BarrierSettlementPass")) == 1


def test_a_claim_is_settled_once() -> None:
    """FORE-IDM-05: two loop passes over the same run, a direct second call, then a
    later run whose bars also cover the claim (and would say stop): one settlement,
    whose settling_ref names the first covering run; each run is passed once, and
    no pass so much as tries to settle the claim again (no fault)."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    seed_claim(graph)
    seed_run(graph, "run-a", bars=ohlcv("AAPL", _TARGET_PATH))
    loop = partial(
        run_once,
        partial(find_pending_settlement, graph),
        partial(settle_analyst_node, graph=graph, sink=sink),
    )

    first = loop()
    assert find_pending_settlement(graph) == []
    second = loop()
    run_a = graph.get_node("AnalystRun", "run-a")
    assert run_a is not None
    settle_analyst_node(run_a, graph=graph)
    stop_path = path(events={2: (100.5, 90.0)})
    seed_run(graph, "run-b", bars=ohlcv("AAPL", stop_path))
    third = loop()

    assert (first.advanced, second.found, third.advanced) == (1, 0, 1)
    [settlement] = graph.list_nodes("BarrierSettlement")
    assert settlement.props["settling_ref"] == "market-data:run-a"
    assert settlement.props["outcome"] == "target"
    passes = {
        node.key: node.props["settled"]
        for node in graph.list_nodes("BarrierSettlementPass")
    }
    assert passes == {"settlement-pass:run-a": 1, "settlement-pass:run-b": 0}
    assert find_pending_settlement(graph) == []
    assert sink.faults == []


class _NoMarketListing(InMemoryGraphStore):
    """A graph that refuses to list MarketData: a pass may read one, by lineage."""

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        assert label != "MarketData", "the pass listed every MarketData"
        return super().list_nodes(label)


def test_the_pass_reads_only_its_own_runs_market_data() -> None:
    """FORE-TRG-01 / FORE-NEV-04: the pass reads its own run's MarketData through
    the lineage and never lists them; another run's MarketData covering the claim
    is not read, so a run without lineage settles nothing and says so."""
    graph = _NoMarketListing()
    seed_claim(graph)
    seed_run(graph, "run-other", bars=ohlcv("AAPL", _TARGET_PATH))
    bare = seed_run(graph, "run-bare", lineage=False)

    settle_analyst_node(bare, graph=graph)

    assert graph.list_nodes("BarrierSettlement") == ()
    done = graph.get_node("BarrierSettlementPass", "settlement-pass:run-bare")
    assert done is not None
    assert (done.props["settling_ref"], done.props["open"]) == (None, 1)
    other = graph.get_node("AnalystRun", "run-other")
    assert other is not None
    settle_analyst_node(other, graph=graph)
    [settlement] = graph.list_nodes("BarrierSettlement")
    assert settlement.props["settling_ref"] == "market-data:run-other"
