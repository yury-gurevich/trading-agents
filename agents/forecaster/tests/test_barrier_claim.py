"""S239 A4 / A6: a successful forecast_barrier call records one complete claim.

Agent: forecaster
Role: prove the BarrierForecast node carries every field sprint B settles from,
      the response is a shadow prediction of P(target first), the claim passes the
      pack's fail-closed vocabulary guard, and the same bars give the same claim,
      merged into the same node, in this process and in a fresh one.
External I/O: runs one child Python process (no network) for the seed check.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pytest

from agents.forecaster.barrier_fit import FakeGarchFitter
from agents.forecaster.domain.barrier_garch import barrier_seed, daily_moves
from agents.forecaster.tests.barrier_helpers import (
    ACCEPTED,
    HISTORY_KEY,
    barrier_bars,
    barrier_message,
    wire_barrier,
)
from contracts.forecaster import ShadowPrediction
from kernel import InMemoryGraphStore
from kernel.graph_guarded import GuardedGraphStore
from kernel.graph_vocabulary import Vocabulary

_ROOT = Path(__file__).resolve().parents[3]
_PACK = _ROOT / "orchestration" / "packs" / "trading_graph_vocabulary.json"
_CLAIM_FIELDS = {
    "ticker",
    "as_of",
    "entry_close",
    "horizon_sessions",
    "stop_pct",
    "target_pct",
    "p_stop_first",
    "p_target_first",
    "p_neither",
    "model_id",
    "model_version",
    "history_bars",
    "n_paths",
    "seed",
    "history_ref",
    "fit_status",
    "garch_mu",
    "garch_omega",
    "garch_alpha",
    "garch_beta",
    "created_at",
    "shadow",
}


def test_a_successful_call_writes_one_complete_claim() -> None:
    """FORE-OUT-07 / FORE-IDN-02 / FORE-IN-07 / FORE-NEV-04: one BarrierForecast
    with every settlement field, shadow true, fitted on exactly the 760 bars the
    provider's BarrierHistory holds (named in the request, never fetched over the
    bus); the response is a shadow prediction of P(target first); no
    ShadowPrediction node."""
    bars = barrier_bars("AAPL", 780)
    fitter = FakeGarchFitter(ACCEPTED)
    bus, graph, sink = wire_barrier(bars=bars, fitter=fitter)

    response = ShadowPrediction.model_validate(
        bus.request(barrier_message("AAPL", stop_pct=0.05, target_pct=0.06)).payload
    )

    [claim] = graph.list_nodes("BarrierForecast")
    props = claim.props
    last = bars[-1]
    assert set(props) == _CLAIM_FIELDS
    assert claim.key == f"barrier-garch-v1:AAPL:{last.bar_date.isoformat()}"
    assert (props["ticker"], props["as_of"]) == ("AAPL", last.bar_date.isoformat())
    assert props["entry_close"] == last.close
    assert (props["horizon_sessions"], props["history_bars"], props["n_paths"]) == (
        10,
        760,
        1000,
    )
    assert (props["stop_pct"], props["target_pct"]) == (0.05, 0.06)
    assert props["p_stop_first"] + props["p_target_first"] + props["p_neither"] == (
        pytest.approx(1.0, abs=1e-12)
    )
    assert (props["model_id"], props["model_version"]) == ("barrier-garch-v1", "1.0.0")
    assert props["seed"] == barrier_seed("AAPL", last.bar_date)
    assert props["history_ref"] == HISTORY_KEY
    assert props["fit_status"] == "accepted"
    assert (
        props["garch_mu"],
        props["garch_omega"],
        props["garch_alpha"],
        props["garch_beta"],
    ) == (ACCEPTED.mu, ACCEPTED.omega, ACCEPTED.alpha, ACCEPTED.beta)
    assert datetime.fromisoformat(props["created_at"]).tzinfo is not None
    assert props["shadow"] is True

    kept = bars[-760:]
    expected_moves = daily_moves(
        np.array([bar.high for bar in kept]),
        np.array([bar.low for bar in kept]),
        np.array([bar.close for bar in kept]),
    )[0]
    [fitted] = fitter.calls
    assert np.array_equal(fitted, expected_moves)

    assert response.model_id == "barrier-garch-v1"
    assert response.subject_ref == "AAPL"
    assert response.value == props["p_target_first"]
    assert response.confidence == 1.0
    assert response.shadow is True
    assert response.provenance.graph_node_id == f"BarrierForecast:{claim.key}"
    assert graph.list_nodes("ShadowPrediction") == ()
    assert sink.faults == []
    assert [m.capability for m in bus.requests] == ["forecast_barrier"]


def test_the_claim_passes_the_packs_vocabulary_guard() -> None:
    """FORE-IDN-02 / FORE-OUT-07: the label and every claim property are declared in
    the trading pack, so the fail-closed guard admits the write (DL-85)."""
    vocabulary = Vocabulary.from_mapping(json.loads(_PACK.read_text(encoding="utf-8")))
    guarded = GuardedGraphStore(InMemoryGraphStore(), vocabulary)
    bus, graph, sink = wire_barrier(bars=barrier_bars("MSFT", 760), graph=guarded)

    bus.request(barrier_message("MSFT"))

    assert sink.faults == []
    assert len(graph.list_nodes("BarrierForecast")) == 1


def test_the_same_bars_give_the_same_claim_merged_into_one_node() -> None:
    """FORE-IDM-04: a second call on the same last bar states the same
    probabilities from the same seed and merges into the same node."""
    bars = barrier_bars("NVDA", 760, drift=0.0004)
    bus, graph, sink = wire_barrier(bars=bars)

    first = bus.request(barrier_message("NVDA")).payload
    [before] = graph.list_nodes("BarrierForecast")
    second = bus.request(barrier_message("NVDA")).payload
    [after] = graph.list_nodes("BarrierForecast")

    assert first["value"] == second["value"]
    assert before == after
    assert sink.faults == []


def test_a_different_claim_for_the_same_last_bar_is_refused() -> None:
    """FORE-IDM-04 / FORE-STA-02 (barrier leg): a rerun that would state a different
    claim under the same key is refused with a fault; the first claim stands."""
    bus, graph, sink = wire_barrier(bars=barrier_bars("AMD", 760))

    bus.request(barrier_message("AMD", stop_pct=0.05, target_pct=0.06))
    [first] = graph.list_nodes("BarrierForecast")
    refused = ShadowPrediction.model_validate(
        bus.request(barrier_message("AMD", stop_pct=0.04, target_pct=0.06)).payload
    )

    assert graph.list_nodes("BarrierForecast") == (first,)
    assert (refused.value, refused.confidence) == (0.5, 0.0)
    [fault] = sink.faults
    assert fault.error_type == "ValueError"
    assert "'stop_pct' cannot be overwritten" in fault.message


def test_the_seed_is_stable_across_processes() -> None:
    """FORE-IDM-04: the seed is a stable hash of (ticker, as_of), never Python's
    per-process salted hash(): a fresh interpreter derives the same number."""
    as_of = date(2026, 9, 25)
    code = (
        "from datetime import date\n"
        "from agents.forecaster.domain.barrier_garch import barrier_seed\n"
        "print(barrier_seed('AAPL', date(2026, 9, 25)))\n"
    )
    child = subprocess.run(  # noqa: S603 - a fixed interpreter and fixed code
        [sys.executable, "-c", code],
        capture_output=True,
        check=True,
        cwd=_ROOT,
        env={"PYTHONPATH": str(_ROOT), "PYTHONHASHSEED": "random"},
        text=True,
    )
    assert int(child.stdout.strip()) == barrier_seed("AAPL", as_of)
    assert barrier_seed("AAPL", as_of) == 3333665949
