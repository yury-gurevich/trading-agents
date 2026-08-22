"""Researcher contract value validation tests.

Agent: contracts (shared)
Role: verify optional researcher evidence payloads round-trip.
External I/O: none.
"""

from __future__ import annotations

from contracts.common import Explanation, Provenance
from contracts.researcher import (
    CONTRACT,
    BacktestEvidence,
    FactorProposal,
    ParameterChangeProposal,
    ProposedFactor,
)


def test_researcher_backtest_evidence_round_trips_optionally() -> None:
    evidence = _backtest()
    proposal = ParameterChangeProposal(
        proposal_id="bt",
        changes=(),
        rationale=Explanation(summary="fixture"),
        provenance=Provenance(run_id="bt", source_agent="researcher"),
        backtest=evidence,
    )

    parsed = ParameterChangeProposal.model_validate(proposal.model_dump(mode="json"))

    assert CONTRACT.version == "0.3.0"
    assert parsed.backtest == evidence


def test_researcher_factor_proposal_round_trips_optionally() -> None:
    evidence = _backtest()
    proposal = FactorProposal(
        proposal_id="factor",
        factor=ProposedFactor(
            name="momentum",
            params=(("lookback", 20.0),),
            rationale=Explanation(summary="bounded catalogue member"),
        ),
        provenance=Provenance(run_id="factor", source_agent="researcher"),
        backtest=evidence,
    )

    parsed = FactorProposal.model_validate(proposal.model_dump(mode="json"))

    assert parsed.factor.params == (("lookback", 20.0),)
    assert parsed.backtest == evidence


def _backtest() -> BacktestEvidence:
    return BacktestEvidence(
        sharpe=1.2,
        ic_mean=0.03,
        max_drawdown=-0.10,
        turnover=0.25,
        n_days=120,
        window_start="2024-01-01",
        window_end="2024-06-30",
        holdout_sharpe=0.8,
        holdout_ic_mean=0.02,
        slippage_bps=10.0,
    )
