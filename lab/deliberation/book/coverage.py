"""Which keys in the rendered packets have no dictionary entry? (structural keys are listed, not defined)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .entries import ENTRIES

CASES = Path(__file__).parents[1] / "cases" / "synthetic"
# Self-describing or bookkeeping keys: named in the book's preamble, not defined one by one.
STRUCTURAL = {
    "action",
    "ticker",
    "date",
    "open_usd",
    "high_usd",
    "low_usd",
    "close_usd",
    "volume_shares",
    "quantity_shares",
    "est_price_usd",
    "rationale",
    "refs",
    "notes",
    "name",
    "decision",
    "reason",
    "issuer",
    "sector",
    "metrics",
    "features",
    "quant_metrics",
    "requested_tickers",
    "returned_tickers",
    "stale_tickers",
    "anomalous_tickers",
    "used_fallback",
    "universe_tickers",
    "evaluated_tickers",
    "dropped_tickers_by_filter",
    "survived_filters",
    "skipped_filters",
    "filter_fired",
    "bypassed",
    "enforced_by",
    "mode",
    "counterfactual_mode",
    "applied_mode",
    "source",
    "structural_basis",
    "target_basis",
    "comparison",
    "denominator",
    "volatility_present",
    "volatility_fallback",
    "held_issuers",
    "is_new_issuer",
    "existing_issuer_value_usd",
    "existing_sector_issuers",
    "position_value_usd",
    "portfolio_value_usd",
    "deployed_portfolio_usd",
    "cash_buffer_pct",
    "reserved_cash_this_batch_usd",
    "deployment_pct",
    "deployment_floor_pct",
    "stop_pct",
    "target_pct",
    "flat_stop_pct",
    "flat_target_pct",
    "scaled_stop_pct",
    "scaled_target_pct",
    "flat_reward_risk_ratio",
    "scaled_reward_risk_ratio",
    "threshold_available_cash_usd",
    "threshold_cluster_exposure_ratio",
    "threshold_portfolio_ratio",
    "threshold_positions",
    "threshold_reward_risk_ratio",
    "threshold_sector_exposure_ratio",
    "threshold_sector_issuers",
    "threshold_shares",
}


def packet_keys() -> set[str]:
    keys: set[str] = set()
    for f in CASES.glob("*.json"):
        keys |= set(re.findall(r"([A-Za-z_][A-Za-z0-9_/]*)=", json.loads(f.read_text())["context"]))
    return keys


def main() -> None:
    defined = {e.key for e in ENTRIES}
    keys = packet_keys()
    missing = sorted(keys - defined - STRUCTURAL)
    unused = sorted(defined - keys)
    print(f"packet keys {len(keys)}; defined {len(defined & keys)}; structural {len(keys & STRUCTURAL)}")
    print("MISSING (material, undefined):", missing)
    print("defined but absent from these cases:", unused)


if __name__ == "__main__":
    main()
