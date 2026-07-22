"""Analyst batch-scoring domain tests.

Agent: analyst
Role: pin score_candidates fault metadata and Alpha158 per-ticker plumbing.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any

from agents.analyst.domain import analyze
from agents.analyst.domain.recommend import AnalysisDecision
from agents.analyst.domain.scoring import ScoreBreakdown
from agents.analyst.settings import AnalystSettings
from agents.analyst.tests.helpers import candidate, candidate_set
from contracts.common import Provenance
from contracts.provider import DataQualityTrace, MarketData, OHLCVBar, RegimeContext
from kernel import CollectingFaultSink

if TYPE_CHECKING:
    import pytest


def _bar(ticker: str, close: float = 100.0) -> OHLCVBar:
    return OHLCVBar(
        ticker=ticker,
        bar_date=date(2025, 1, 2),
        open=close,
        high=close + 1.0,
        low=close - 1.0,
        close=close,
        volume=1_000_000,
    )


def _market(*bars: OHLCVBar) -> MarketData:
    return MarketData(
        bars=bars,
        quality=DataQualityTrace(requested=len(bars), returned=len(bars)),
        provenance=Provenance(run_id="provider-run", source_agent="provider"),
    )


def _regime() -> RegimeContext:
    return RegimeContext(
        label="risk_on",
        vix=12.0,
        as_of=datetime.now(tz=UTC),
        base_min_confidence=0.30,
        base_stop_loss_pct=0.05,
        base_take_profit_pct=0.10,
        base_max_holding_days=10,
        provenance=Provenance(run_id="regime-run", source_agent="provider"),
    )


def _score(alpha: float | None = None) -> ScoreBreakdown:
    return ScoreBreakdown(
        technical_score=0.70,
        confidence=0.80,
        metrics={},
        alpha158_score=alpha,
    )


def _decision(_candidate: Any, _score: Any, _regime: Any) -> AnalysisDecision:
    return AnalysisDecision(recommendation=None, rejection=None)


def test_score_candidates_fault_boundary_records_exact_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kills analyze.x_score_candidates mutmut_5, 10, and 12-17."""

    def fail_score(*_args: Any, **_kwargs: Any) -> ScoreBreakdown:
        raise RuntimeError("score exploded")

    monkeypatch.setattr(analyze, "score_candidate", fail_score)
    sink = CollectingFaultSink()

    result = analyze.score_candidates(
        candidate_set(candidate("AAPL")),
        _market(_bar("AAPL")),
        _regime(),
        (),
        AnalystSettings(),
        sink,
    )

    assert result is None
    assert len(sink.faults) == 1
    fault = sink.faults[0]
    assert fault.source_agent == "analyst"
    assert fault.source_module == "agents.analyst.agent"
    assert fault.capability == "analyze"
    assert fault.error_type == "RuntimeError"
    assert fault.message == "score exploded"


def test_score_candidates_alpha_disabled_skips_feature_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kills agents.analyst.domain.analyze.x_score_candidates__mutmut_22."""

    def fail_feature_rows(_bars: tuple[OHLCVBar, ...]) -> object:
        raise AssertionError("alpha feature work should stay off at weight zero")

    monkeypatch.setattr(analyze, "compute_alpha_features", fail_feature_rows)
    monkeypatch.setattr(
        analyze,
        "score_candidate",
        lambda *args, **kwargs: _score(kwargs["alpha_score"]),
    )
    monkeypatch.setattr(analyze, "decide", _decision)
    sink = CollectingFaultSink()

    result = analyze.score_candidates(
        candidate_set(candidate("AAPL")),
        _market(_bar("AAPL")),
        _regime(),
        (),
        AnalystSettings(),
        sink,
    )

    assert result == (AnalysisDecision(recommendation=None, rejection=None),)
    assert sink.faults == []


def test_score_candidates_threads_alpha_score_by_ticker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kills analyze.x_score_candidates mutmut_23, 27, 28, 31, 35, 48, 54,
    61, 63, 65, and 74.
    """

    captured: dict[str, float | None] = {}

    def feature_row(rows: tuple[OHLCVBar, ...]) -> str | None:
        if not rows:
            return None
        assert len(rows) == 1
        return f"row:{rows[0].ticker}"

    def alpha_score(row: str, universe: tuple[str, ...]) -> float:
        assert universe == ("row:AAPL",)
        assert row == "row:AAPL"
        return 77.0

    def score_one(
        scored_candidate: Any,
        bars: tuple[OHLCVBar, ...],
        _fundamentals: dict[str, float],
        _benchmark_bars: tuple[OHLCVBar, ...],
        _news: tuple[str, ...],
        _settings: AnalystSettings,
        *,
        alpha_score: float | None = None,
    ) -> ScoreBreakdown:
        assert scored_candidate is not None
        assert isinstance(bars, tuple)
        captured[scored_candidate.ticker] = alpha_score
        return _score(alpha_score)

    monkeypatch.setattr(analyze, "compute_alpha_features", feature_row)
    monkeypatch.setattr(analyze, "score_alpha158", alpha_score)
    monkeypatch.setattr(analyze, "score_candidate", score_one)
    monkeypatch.setattr(analyze, "decide", _decision)
    scan = candidate_set(candidate("AAPL"), candidate("MSFT"))
    sink = CollectingFaultSink()

    result = analyze.score_candidates(
        scan,
        _market(_bar("AAPL")),
        _regime(),
        (),
        AnalystSettings(alpha158_pillar_weight=0.20),
        sink,
    )

    assert result == (
        AnalysisDecision(recommendation=None, rejection=None),
        AnalysisDecision(recommendation=None, rejection=None),
    )
    assert captured == {"AAPL": 77.0, "MSFT": None}
    assert sink.faults == []
