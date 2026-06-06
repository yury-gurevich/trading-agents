# Analyst Agent

**Mission.** Turn candidates into scored, evidence-backed trade recommendations
with a confidence and a rationale — or explain clearly why none qualify.

## Owns
- Technical indicators and scoring.
- Sentiment and fundamental scoring.
- Recommendation building and the confidence model.

## Boundary — contract: `contracts/analyst.py`
- **Consumes:** `analyze(CandidateSet) -> RecommendationSet`,
  `explain_recommendation(CandidateSet) -> Explanation`.
- **Emits:** `analysis_completed`.
- **Depends on (messages only):** `scanner` (candidates), `provider` (data/regime).

## Data ownership
- **Postgres:** `recommendations`, `analyst_diagnostics`, `analyst_configs`.
- **Graph:** `AnalystRun`, `Recommendation`
  (`Recommendation -[:DERIVED_FROM]-> Candidate`).

## External I/O
- None.

## MCP surface
- `analyze`, `explain_recommendation`.

## Never
- Size positions or compute order quantities.
- Approve, portfolio-reject, or submit orders.
- Call a market-data API directly.
- Import portfolio_manager sizing — **the old cross-agent leak this rebuild removes.**
