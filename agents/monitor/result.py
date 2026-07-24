"""Monitor response explanation helpers.

Agent: monitor
Role: build stop-observation and run-level explanations.
External I/O: none.
"""

from __future__ import annotations

from contracts.common import Explanation


def run_explanation(positions_checked: int, stop_breaches: int) -> Explanation:
    """Return a run-level monitor explanation."""
    return Explanation(
        summary=(
            f"Monitor checked {positions_checked} positions; "
            f"{stop_breaches} stop breaches surfaced."
        ),
        evidence_refs=("contracts.stop_rule", "provider.get_market_data"),
    )
