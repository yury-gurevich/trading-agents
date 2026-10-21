"""Sprint 288 return fixtures and independent claim replay assertions.

Agent: forecaster
Role: wire guarded stores, replay a recorded claim and seed the three return cases.
External I/O: reads the local vocabulary pack; no network.
"""

from __future__ import annotations

import json
from dataclasses import asdict, replace
from datetime import date, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from agents.forecaster.domain import barrier_garch
from agents.forecaster.domain.barrier_settlement import Settlement
from agents.forecaster.settlement_store import write_settlement
from agents.forecaster.tests.settlement_helpers import seed_claim
from kernel import InMemoryGraphStore
from kernel.graph_guarded import GuardedGraphStore
from kernel.graph_vocabulary import Vocabulary

if TYPE_CHECKING:
    from contracts.provider import OHLCVBar
    from kernel import GraphStore, Node

RETURN_FIELDS = (
    "expected_return",
    "close_return_p05",
    "sessions_to_target",
    "sessions_to_stop",
)
RETURN_SCORES = {
    "return_settled",
    "declared_return",
    "realised_return",
    "return_bias",
    "return_bias_lo",
    "return_bias_hi",
    "close_below_p05",
}
RETURN_ROWS = (
    ("AAPL", "2026-10-21", 0.010, -0.08, "target", 0.07, 0.05),
    ("MSFT", "2026-10-21", 0.004, -0.06, "stop", -0.05, -0.09),
    ("NVDA", "2026-10-22", 0.006, -0.07, "neither", 0.01, 0.01),
)


def guarded_graph() -> GuardedGraphStore:
    """The actual pack's guard over a fresh in-memory store."""
    pack = (
        Path(__file__).resolve().parents[3]
        / "orchestration/packs/trading_graph_vocabulary.json"
    )
    return GuardedGraphStore(
        InMemoryGraphStore(),
        Vocabulary.from_mapping(json.loads(pack.read_text("utf-8"))),
    )


def assert_claim_figures(claim: Node, bars: tuple[OHLCVBar, ...]) -> None:
    """Re-run the stored seed and parameters on the claim's own bars and barriers."""
    from agents.forecaster.domain.barrier_returns import barrier_returns

    p = claim.props
    moves = barrier_garch.daily_moves(
        np.array([b.high for b in bars]),
        np.array([b.low for b in bars]),
        np.array([b.close for b in bars]),
    )
    params = tuple(
        float(p[f"garch_{name}"]) for name in ("mu", "omega", "alpha", "beta")
    )
    mu, omega, alpha, beta = params
    paths = barrier_garch.garch_paths(
        np.random.default_rng(int(p["seed"])),
        (mu, omega, alpha, beta),
        *moves,
        0,
        len(moves[0]),
        n_paths=int(p["n_paths"]),
    )
    stop, target = float(p["stop_pct"]), float(p["target_pct"])
    assert tuple(
        p[name] for name in ("p_stop_first", "p_target_first", "p_neither")
    ) == (barrier_garch.barrier_probs(*paths[:3], stop, target))
    assert {name: p[name] for name in RETURN_FIELDS} == asdict(
        barrier_returns(paths, stop, target)
    )


def write_return_case(
    graph: GraphStore,
    *,
    ticker: str,
    as_of: str,
    declared: float,
    p05: float,
    outcome: str,
    realised: float,
    close: float,
    held: bool = False,
    claim_figures: bool = True,
    settlement_figures: bool = True,
) -> None:
    """Seed one case, optionally with either side's pre-S288 field shape."""
    day = date.fromisoformat(as_of)
    base = InMemoryGraphStore() if held else graph
    claim = seed_claim(base, ticker=ticker, as_of=day)
    if held:
        claim = graph.merge_node(
            "BarrierForecast",
            f"barrier-garch-v1:held:{ticker}:{as_of}",
            {**claim.props, "subject_kind": "position"},
        )
    if claim_figures:
        claim = graph.merge_node(
            claim.label,
            claim.key,
            dict(zip(RETURN_FIELDS, (declared, p05, 5.0, 3.0), strict=True)),
        )
    settlement = Settlement(outcome, None, day + timedelta(days=14), 100.0, 1.0)
    if settlement_figures:
        settlement = replace(
            settlement,
            realised_return=realised,
            close_return=close,
            outcome_session=None,
        )
    write_settlement(graph, claim, settlement, settling_ref=f"market-data:{as_of}")


def write_return_ledger(graph: GraphStore, *, held: bool = False) -> None:
    """A10's three literal cases, as buys or held claims."""
    for ticker, as_of, declared, p05, outcome, realised, close in RETURN_ROWS:
        write_return_case(
            graph,
            ticker=ticker,
            as_of=as_of,
            declared=declared,
            p05=p05,
            outcome=outcome,
            realised=realised,
            close=close,
            held=held,
        )
