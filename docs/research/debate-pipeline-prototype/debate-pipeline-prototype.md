# Research: Quant Trading Debate Pipeline Prototype — the document as received

**Status:** Filed as received · **Date:** 2026-10-06 · **Author:** supplied by the operator; origin not stated
**Audience:** Product owner, planning agents, coding agents
**Source:** the operator's file `quant_trading_debate_pipeline.md`, 2026-10-06

Formatting repaired only: the code fences, the headings, and the two formulas written on one line. The
content is unchanged. The planner's reading of it is in [INDEX.md](INDEX.md).

## Overview

This document outlines a multi-agent debate pipeline for quant trading strategy evaluation. It includes Proponent, Opponent, and Judge modules, iterative refinement, risk calculations, and final verdict generation.

## Parameter Ingestion

Parameters are provided as a JSON object containing up to 60 quant trading configuration fields. Example:

```json
{
  "strategy_name": "MeanReversionX",
  "universe": ["AAPL", "MSFT", "SPY"],
  "lookback_days": 20,
  "entry_zscore": 2.0,
  "exit_zscore": 0.5,
  "position_size_pct": 0.02,
  "max_leverage": 2.0,
  "stop_loss_pct": 0.03,
  "take_profit_pct": 0.06,
  "slippage_bps": 5,
  "commission_per_share": 0.001,
  "vol_target": 0.08,
  "correlation_threshold": 0.9,
  "max_drawdown_limit": 0.12,
  "expected_annual_return": 0.12,
  "confidence_var": 0.95,
  "var_horizon_days": 10,
  "es_confidence": 0.975,
  "rebalance_freq_days": 1,
  "data_source": "tick+1min",
  "latency_ms": 50,
  "order_type": "limit",
  "min_trade_size": 100,
  "max_trade_size": 100000,
  "risk_budget_pct": 0.10,
  "beta_target": 0.0,
  "hedge_instruments": ["SPY"],
  "execution_algo": "TWAP",
  "slippage_model": "linear",
  "market_open_buffer_min": 5,
  "market_close_buffer_min": 10,
  "overnight_exposure_allowed": true,
  "news_filter": "headline_sentiment",
  "max_positions": 30,
  "min_positions": 3,
  "liquidity_threshold": 100000,
  "implied_vol_threshold": 0.5,
  "option_overlay": false,
  "margin_rate": 0.05,
  "funding_cost_pct": 0.02,
  "stress_scenario": "2008-like",
  "stress_return_scale": -0.4,
  "correlation_shift": 0.2,
  "scenario_prob": 0.01,
  "backtest_period_years": 5,
  "walkforward_window_days": 90,
  "seed": 42,
  "reporting_freq_days": 7,
  "alert_thresholds": {"drawdown": 0.08, "var": 0.05},
  "compliance_rules": ["no_penny_stocks", "no_short_on_blacklist"],
  "model_update_freq_days": 30,
  "feature_set": ["price", "volume", "volatility", "sentiment"],
  "ml_model": "xgboost",
  "hyperparam_grid": {"max_depth": [3, 5, 7], "eta": [0.01, 0.1]},
  "explainability_required": true,
  "notes": "user-specified constraints and preferences"
}
```

## Agent Prompts

### Proponent

Produces a trading plan based on parameters.

```text
You are Proponent. Produce a concise trading plan using the parameters below.
Return JSON: {proposal_id, summary, trades: [...], rationale, risk_estimates}.
Goal: maximize risk-adjusted return while respecting constraints.
Parameters: <params>
```

### Opponent

Critiques the Proponent's plan.

```text
You are Opponent. Critique the Proponent's proposal.
Focus on hidden risks, parameter conflicts, execution issues.
Return JSON: {proposal_id, critique, suggested_changes: [...], severity_score}.
```

### Judge

Evaluates proposal and critique.

```text
You are Judge. Evaluate both proposal and critique.
Tasks:
1) Compute risk metrics (VaR, ES, max drawdown, leverage).
2) Decide if proposal aligns with constraints.
3) Issue corrective directives if needed.
Return JSON: {proposal_id, verdict, risk_metrics:{...}, directives:[...], confidence}.
```

## Risk Calculations

### Parametric VaR

```text
VaR_α = μ_T + σ_T · z_α
```

### Expected Shortfall

```text
ES_α = μ_T + σ_T · φ(z_α) / (1 − α)
```

### Max Drawdown

Largest peak-to-trough drop in equity curve.

### Leverage Usage

Gross exposure divided by equity.

## Iteration Loop

```python
def debate_cycle(params, max_rounds=4):
    round = 0
    current_proposal = None
    judge_directives = None

    while round < max_rounds:
        round += 1

        if current_proposal is None:
            proposal = Proponent(params)
        else:
            proposal = Proponent({**params, "directives": judge_directives})

        critique = Opponent(params, proposal)
        judge = Judge(params, proposal, critique)

        if judge["verdict"] == "accept":
            return {"final": proposal, "judge": judge, "rounds": round}

        judge_directives = judge["directives"]
        current_proposal = proposal

    final_judge = Judge(params, current_proposal, Opponent(params, current_proposal))
    return {"final": current_proposal, "judge": final_judge, "rounds": round}
```

## Final Verdict Example

```json
{
  "proposal_id": "p-20261006-001",
  "verdict": "accept",
  "final_plan": {},
  "supporting_arguments": ["reduced position size lowers VaR", "hedge reduces tail risk"],
  "risk_metrics": {"VaR_95": -0.032, "ES_975": -0.048, "max_drawdown": 0.095, "leverage": 1.15},
  "mitigations": ["limit order execution", "weekly rebalancing"],
  "judge_confidence": 0.86
}
```
