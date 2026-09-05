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
    features: dict[str, float],
    settings: ScannerSettings,
    earnings_horizon_days: int | None = None,
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
    elif _absence_is_an_answer(settings, earnings_horizon_days):
        # No date inside a horizon that covers the exclusion window is a fact:
        # this ticker has no earnings due. Recording it as skipped told consumers
        # "unverified" when the gate had actually answered.
        passed.append("earnings_window")
    else:
        skipped.append("earnings_window")
    return None, tuple(passed), tuple(skipped)


def _absence_is_an_answer(
    settings: ScannerSettings, earnings_horizon_days: int | None
) -> bool:
    """Whether a missing earnings date proves no earnings inside the window.

    Only when the producer declared a horizon that *strictly exceeds* the exclusion
    window. An equal horizon leaves the boundary day unproven, and an unknown horizon
    proves nothing at all.
    """
    if earnings_horizon_days is None:
        return False
    return earnings_horizon_days > settings.earnings_exclusion_days
