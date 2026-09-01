"""Scanner filter gate attestation helpers.

Agent: scanner
Role: evaluate scanner gates while reporting passed and skipped gate names.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.scanner.settings import ScannerSettings


def evaluate_filters(
    features: dict[str, float], settings: ScannerSettings
) -> tuple[str | None, tuple[str, ...], tuple[str, ...]]:
    """Return (drop filter | None, passed gates, skipped gates)."""
    passed: list[str] = []
    skipped: list[str] = []
    if features["latest_close"] < settings.min_price:
        return "min_price", tuple(passed), tuple(skipped)
    passed.append("min_price")
    if features["average_volume"] < settings.min_average_volume:
        return "min_average_volume", tuple(passed), tuple(skipped)
    passed.append("min_average_volume")
    if features["relative_strength"] < settings.min_relative_strength:
        return "min_relative_strength", tuple(passed), tuple(skipped)
    passed.append("min_relative_strength")
    if "beta" in features:
        if features["beta"] > settings.max_beta:
            return "max_beta", tuple(passed), tuple(skipped)
        passed.append("max_beta")
    else:
        skipped.append("max_beta")
    if "days_to_earnings" in features:
        if 0 <= features["days_to_earnings"] <= settings.earnings_exclusion_days:
            return "earnings_window", tuple(passed), tuple(skipped)
        passed.append("earnings_window")
    else:
        skipped.append("earnings_window")
    return None, tuple(passed), tuple(skipped)
