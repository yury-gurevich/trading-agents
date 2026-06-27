"""Trading parameter answer key — ground truth for the deliberation understanding gate.

Agent: orchestration
Role: the trading PACK's answer key (kept out of kernel per the platform/pack wall).
      Each entry encodes how a parameter ACTUALLY behaves in our code plus the known
      misreading the model makes, sourced from
      `docs/research/quant-methods/llm-interpretation-deltas.md` (EXP-001/003). The
      kernel scorer grades a debate's parameter definitions against these (DL-31).
External I/O: none.
"""

from __future__ import annotations

from kernel import ParameterTruth

#: The Class-1 (implementation misread) + Class-2 (assumed-guardrail) deltas the
#: deliberation must get right. Markers are case-insensitive substrings.
TRADING_PARAMETER_TRUTHS: tuple[ParameterTruth, ...] = (
    ParameterTruth(
        name="max_daily_move_sigma",
        # Actual: a POOLED CROSS-SECTIONAL z-score across all tickers' intraday
        # returns — a data-integrity gate, not a per-stock vol filter (the DL-17 bug).
        correct_markers=(
            "pooled",
            "cross-sectional",
            "cross sectional",
            "all tickers",
            "across the batch",
            "data-integrity",
            "data integrity",
            "whole universe",
        ),
        misread_markers=(
            "that stock's",
            "per-stock",
            "per stock",
            "its own volatility",
            "in that stock",
            "the stock's volatility",
        ),
    ),
    ParameterTruth(
        name="base_min_confidence",
        # Actual: a seed default the REGIME + confidence modulate (tightens risk-off),
        # not a fixed/absolute threshold.
        correct_markers=("regime", "modulat", "seed default", "tighten", "baseline"),
        misread_markers=("fixed threshold", "absolute threshold", "constant threshold"),
    ),
    ParameterTruth(
        name="max_sector_pct",
        # Actual: a SECTOR concentration cap — NOT a name-correlation penalty (we
        # opened 4 semis under it). The dangerous Class-2 over-claim.
        correct_markers=(
            "sector concentration",
            "per-sector",
            "per sector",
            "sector cap",
            "sector exposure",
        ),
        misread_markers=(
            "correlated holdings",
            "name correlation",
            "name-correlation",
            "hidden concentration from correlated",
        ),
    ),
    ParameterTruth(
        name="signal_diversity_slack",
        # Actual: slack to surface a signal from an UNUSED pillar in the rationale
        # (diversity of explanation), NOT tolerance for correlated signals.
        correct_markers=(
            "unused pillar",
            "rationale",
            "explanation",
            "different pillar",
        ),
        misread_markers=(
            "correlated signal",
            "tolerance for correlated",
            "correlation",
        ),
    ),
)
