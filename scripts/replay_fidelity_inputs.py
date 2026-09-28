"""Rebuild one exported S237 session's live inputs as the fleet's contract objects.

Agent: tooling
Role: load an export file, refuse stored replay outputs, and rebuild the book the live
      analyst and PM read through the fleet's own graph readers.
External I/O: reads exported JSON files.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from functools import cache
from typing import TYPE_CHECKING, Any

from scripts.replay_fidelity_facts import ExportedFacts
from scripts.replay_settings import build_effective_settings

from agents.portfolio_manager.graph_portfolio import portfolio_from_graph
from contracts.analyst import RecommendationSet
from contracts.positions import open_positions
from contracts.provider import MarketData, RegimeContext
from contracts.scanner import CandidateSet
from kernel.graph import Node

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.replay_settings import ReplaySettings

    from agents.portfolio_manager.portfolio import PortfolioState
    from contracts.positions import OpenPosition

# Replay outputs are computed, never read (R1): an export carrying one is refused.
REFUSED_KEYS = ("replay", "layer2")


@dataclass(frozen=True)
class SessionInputs:
    """One scheduled run's live inputs and outputs, as the stages read them."""

    session: str
    run_id: str
    payload: dict[str, Any]
    market: MarketData | None
    tickers: tuple[str, ...]
    window_end: date | None
    regime: RegimeContext | None
    candidate_set: CandidateSet | None
    recommendation_set: RecommendationSet | None
    portfolio: PortfolioState
    held: tuple[OpenPosition, ...]
    not_persisted: frozenset[str]


@cache
def effective_settings() -> ReplaySettings:
    """Code defaults plus the pack's tunables, the same for every session."""
    return build_effective_settings(())


def load_sessions(export: Path) -> tuple[SessionInputs, ...]:
    """Load every `sched-*.json`, refusing all of them if one carries a replay."""
    paths = sorted(export.glob("sched-*.json"))
    return tuple(load_session(path) for path in paths)


def load_session(path: Path) -> SessionInputs:
    """Rebuild one session's stage inputs from its export file."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    refused = [key for key in REFUSED_KEYS if key in payload]
    if refused:
        raise ValueError(
            f"{path.name} carries {', '.join(refused)}: replay is computed"
        )
    market = _block(payload, "market")
    run_id = str(market.get("run_id") or payload["run_id"])
    portfolio, held = _book(payload, run_id)
    return SessionInputs(
        session=str(payload["session"]),
        run_id=run_id,
        payload=payload,
        market=_model(MarketData, market.get("snapshot")),
        tickers=tuple(str(item) for item in market.get("tickers") or ()),
        window_end=date.fromisoformat(str(market["window_end"]))
        if market.get("window_end")
        else None,
        regime=_model(RegimeContext, payload.get("regime")),
        candidate_set=_model(
            CandidateSet, _block(payload, "scanner").get("candidate_set")
        ),
        recommendation_set=_model(
            RecommendationSet, _block(payload, "analyst").get("recommendation_set")
        ),
        portfolio=portfolio,
        held=held,
        not_persisted=frozenset(str(item) for item in payload.get("not_persisted", ())),
    )


def _book(
    payload: dict[str, Any], run_id: str
) -> tuple[PortfolioState, tuple[OpenPosition, ...]]:
    """Read the book with the fleet's readers, over only the facts the export holds."""
    book = _block(payload, "book")
    facts = [
        Node("Position", str(item["key"]), item["props"])
        for item in payload.get("positions") or ()
    ]
    if book:
        facts.append(Node("BrokerPositionSnapshot", str(book["key"]), book["props"]))
    view = ExportedFacts(tuple(facts))
    starting_cash = effective_settings().portfolio.starting_cash
    return portfolio_from_graph(view, starting_cash, run_id=run_id), open_positions(
        view
    )


def _block(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _model[ModelT: (MarketData, RegimeContext, CandidateSet, RecommendationSet)](
    model: type[ModelT], value: object
) -> ModelT | None:
    return model.model_validate(value) if value else None
