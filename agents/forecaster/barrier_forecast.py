"""forecast_barrier: state how likely a buy's target comes before its stop.

Agent: forecaster
Role: for one ticker and its stop and target, read ~3 years of its own daily bars
      from the BarrierHistory the provider wrote for the run (DL-241 D10), fit
      GARCH(1,1)-t, simulate EXP-018's 10-session paths and record the three
      probabilities as an append-only, advisory BarrierForecast claim. Any refusal
      (malformed barriers, no or a failed history, a ticker the provider dropped,
      short history, a failed fit, a conflicting rerun) records a fault and returns
      the neutral reading; a claim is never fabricated (FORE-FAIL-04).
External I/O: none (the bars are read from the graph; the fitter is injected).
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

import numpy as np

from agents.forecaster.barrier_store import BARRIER_LABEL, BarrierClaim, write_claim
from agents.forecaster.domain.barrier_garch import (
    BARRIER_MODEL_ID,
    accept_fit,
    barrier_seed,
    daily_moves,
    garch_path_probs,
)
from agents.forecaster.domain.features import confidence_from_history
from agents.forecaster.domain.sentiment import NEUTRAL
from contracts.barrier_history import BARRIER_HISTORY_LABEL, BarrierHistory
from contracts.common import Provenance
from contracts.forecaster import ForecastRequest, ShadowPrediction
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from pydantic import BaseModel

    from agents.forecaster.barrier_fit import GarchFitter
    from agents.forecaster.settings import ForecasterSettings
    from contracts.barrier_history import BarRow
    from kernel import FaultSink, GraphStore


class BarrierClaimRefusedError(RuntimeError):
    """No claim is stated for this request; the message says why."""


def forecast_barrier(
    graph: GraphStore,
    sink: FaultSink,
    settings: ForecasterSettings,
    fitter: GarchFitter,
    request: BaseModel,
) -> ShadowPrediction:
    """Return P(target first) as a shadow prediction, or the neutral reading."""
    forecast = ForecastRequest.model_validate(request)
    run_id = f"forecaster-run-{uuid.uuid4().hex}"
    claim: BarrierClaim | None = None
    with fault_boundary(
        sink,
        agent="forecaster",
        module="agents.forecaster.barrier_forecast",
        capability="forecast_barrier",
        reraise=False,
    ) as capture:
        claim = _state_claim(graph, settings, fitter, forecast)
        write_claim(graph, claim)
    if capture.fault is not None or claim is None:
        return ShadowPrediction(
            model_id=BARRIER_MODEL_ID,
            subject_ref=forecast.subject_ref,
            value=NEUTRAL,
            confidence=0.0,
            provenance=Provenance(run_id=run_id, source_agent="forecaster"),
        )
    return ShadowPrediction(
        model_id=BARRIER_MODEL_ID,
        subject_ref=forecast.subject_ref,
        value=claim.probabilities[1],
        confidence=confidence_from_history(
            claim.history_bars, full_confidence_bars=claim.sessions_requested
        ),
        provenance=Provenance(
            run_id=run_id,
            source_agent="forecaster",
            graph_node_id=f"{BARRIER_LABEL}:{claim.key}",
        ),
    )


def _state_claim(
    graph: GraphStore,
    settings: ForecasterSettings,
    fitter: GarchFitter,
    forecast: ForecastRequest,
) -> BarrierClaim:
    """Read, fit and simulate; raise BarrierClaimRefusedError on any refusal."""
    stop, target = _barriers(forecast.features)
    ticker = forecast.subject_ref
    history = _history(graph, forecast.history_ref, ticker)
    rows = history.histories[ticker].bars
    if len(rows) < settings.barrier_min_history_sessions:
        raise BarrierClaimRefusedError(
            f"{ticker}: {len(rows)} bars < barrier_min_history_sessions "
            f"{settings.barrier_min_history_sessions}; no claim"
        )
    r, lh_pct, ll_pct = _moves(rows)
    params = accept_fit(fitter.fit(r))
    if params is None:
        raise BarrierClaimRefusedError(f"{ticker}: GARCH fit failed; no claim")
    as_of = date.fromisoformat(rows[-1][0])
    seed = barrier_seed(ticker, as_of)
    probabilities = garch_path_probs(
        np.random.default_rng(seed),
        params.as_tuple(),
        r,
        lh_pct,
        ll_pct,
        0,
        len(r),
        stop,
        target,
        n_paths=settings.barrier_paths,
    )
    return BarrierClaim(
        ticker=ticker,
        as_of=as_of,
        entry_close=rows[-1][4],
        stop_pct=stop,
        target_pct=target,
        probabilities=probabilities,
        params=params,
        history_bars=len(rows),
        n_paths=settings.barrier_paths,
        seed=seed,
        history_ref=str(forecast.history_ref),
        sessions_requested=history.sessions_requested,
    )


def _history(graph: GraphStore, ref: str | None, ticker: str) -> BarrierHistory:
    """The provider's BarrierHistory for this request, holding this ticker's bars."""
    node = graph.get_node(BARRIER_HISTORY_LABEL, ref) if ref else None
    if node is None:
        raise BarrierClaimRefusedError(
            f"{ticker}: no BarrierHistory {ref!r} in the graph; no claim"
        )
    history = BarrierHistory.model_validate(dict(node.props))
    if ticker in history.dropped:
        raise BarrierClaimRefusedError(
            f"{ticker}: provider dropped: {history.dropped[ticker]}; no claim"
        )
    if ticker not in history.histories:
        raise BarrierClaimRefusedError(
            f"{ticker}: not requested in BarrierHistory {ref!r}; no claim"
        )
    return history


def _barriers(features: dict[str, float]) -> tuple[float, float]:
    """Return ``(stop_pct, target_pct)``, each in (0, 1] (FORE-IN-07)."""
    stop = features.get("stop_pct")
    target = features.get("target_pct")
    if stop is None or target is None or not (0 < stop <= 1 and 0 < target <= 1):
        raise BarrierClaimRefusedError(
            f"barriers must be fractions in (0, 1]: stop_pct={stop} "
            f"target_pct={target}; no claim"
        )
    return stop, target


def _moves(rows: tuple[BarRow, ...]) -> tuple[np.ndarray, ...]:
    """(date, open, high, low, close) rows -> EXP-018's percent moves."""
    return daily_moves(
        np.array([row[2] for row in rows]),
        np.array([row[3] for row in rows]),
        np.array([row[4] for row in rows]),
    )
