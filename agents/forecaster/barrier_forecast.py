"""forecast_barrier: state how likely a buy's target comes before its stop.

Agent: forecaster
Role: for one ticker and its stop and target, fetch ~3 years of its own daily
      bars from the provider over the bus, fit GARCH(1,1)-t, simulate EXP-018's
      10-session paths and record the three probabilities as an append-only,
      advisory BarrierForecast claim. Any refusal (malformed barriers, a provider
      error, short history, a failed fit, a conflicting rerun) records a fault and
      returns the neutral reading; a claim is never fabricated (FORE-FAIL-04).
External I/O: none directly (the provider answers over the bus; the fitter and
              the graph are injected).
"""

from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime, timedelta
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
from agents.forecaster.provider_client import request_prices
from contracts.common import Provenance, Window
from contracts.forecaster import ForecastRequest, ShadowPrediction
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from pydantic import BaseModel

    from agents.forecaster.barrier_fit import GarchFitter
    from agents.forecaster.settings import ForecasterSettings
    from contracts.provider import OHLCVBar
    from kernel import FaultSink, GraphStore, MessageBus

#: Calendar days asked per session: 250 a year is below the exchange's 251-253,
#: so the window always over-asks (EXP-018: 752 sessions in 1,097 days).
_DAYS_PER_SESSION = 365.25 / 250
#: Slack for a holiday cluster, a non-session end day, a session not yet served.
_WINDOW_MARGIN_DAYS = 14


class BarrierClaimRefusedError(RuntimeError):
    """No claim is stated for this request; the message says why."""


def forecast_barrier(
    graph: GraphStore,
    bus: MessageBus,
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
        claim = _state_claim(bus, sink, settings, fitter, forecast)
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
            claim.history_bars, full_confidence_bars=settings.barrier_history_sessions
        ),
        provenance=Provenance(
            run_id=run_id,
            source_agent="forecaster",
            graph_node_id=f"{BARRIER_LABEL}:{claim.key}",
        ),
    )


def _state_claim(
    bus: MessageBus,
    sink: FaultSink,
    settings: ForecasterSettings,
    fitter: GarchFitter,
    forecast: ForecastRequest,
) -> BarrierClaim:
    """Fetch, fit and simulate; raise BarrierClaimRefusedError on any refusal."""
    stop, target = _barriers(forecast.features)
    ticker = forecast.subject_ref
    fetched = request_prices(
        bus, sink, ticker, _window(settings), capability="forecast_barrier"
    )
    bars = fetched[-settings.barrier_history_sessions :]
    if len(bars) < settings.barrier_min_history_sessions:
        raise BarrierClaimRefusedError(
            f"{ticker}: {len(bars)} bars < barrier_min_history_sessions "
            f"{settings.barrier_min_history_sessions}; no claim"
        )
    r, lh_pct, ll_pct = _moves(bars)
    params = accept_fit(fitter.fit(r))
    if params is None:
        raise BarrierClaimRefusedError(f"{ticker}: GARCH fit failed; no claim")
    as_of = bars[-1].bar_date
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
        entry_close=bars[-1].close,
        stop_pct=stop,
        target_pct=target,
        probabilities=probabilities,
        params=params,
        history_bars=len(bars),
        n_paths=settings.barrier_paths,
        seed=seed,
    )


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


def _moves(bars: tuple[OHLCVBar, ...]) -> tuple[np.ndarray, ...]:
    return daily_moves(
        np.array([bar.high for bar in bars]),
        np.array([bar.low for bar in bars]),
        np.array([bar.close for bar in bars]),
    )


def _window(settings: ForecasterSettings) -> Window:
    """A calendar window holding at least ``barrier_history_sessions`` sessions."""
    end = datetime.now(tz=UTC).date()
    days = math.ceil(settings.barrier_history_sessions * _DAYS_PER_SESSION)
    return Window(start=end - timedelta(days=days + _WINDOW_MARGIN_DAYS), end=end)
