"""Counters for the S235/S237 replay outputs.

Agent: tooling
Role: derive replay summary and per-session counters from day results.
External I/O: none.
"""

from __future__ import annotations

from collections import Counter
from typing import Any


def initial_absent_inputs() -> dict[str, Any]:
    """Return the stable absent-input counter set used by replay summaries."""
    return {
        "fundamentals": 0,
        "news": 0,
        "sentiment": 0,
        "earnings": 0,
        "deliberator": 0,
        "pillars_present": ["technical", "relative_strength"],
        "member_sessions_without_sector": 0,
        "sessions_without_vix": 0,
        "gap_marks": 0,
        "adjustment_error_rebases": 0,
        "data_end_exits": 0,
        "membership_end_exits": 0,
        "expired_no_bar": 0,
        "buy_without_stop": 0,
    }


def replay_day_counts(members: tuple[str, ...], result: object) -> dict[str, int]:
    """Count one session's pipeline outputs from a ReplayDayResult-like object."""
    recommendations = tuple(
        getattr(getattr(result, "recommendations", None), "recommendations", ())
    )
    approved = tuple(getattr(result, "approved", ()))
    rejected = tuple(getattr(result, "rejected", ()))
    actions = Counter(str(getattr(item, "action", "")) for item in recommendations)
    approved_actions = Counter(str(getattr(item, "action", "")) for item in approved)
    candidates = getattr(getattr(result, "candidates", None), "candidates", ())
    row = {
        "members": len(members),
        "candidates": len(candidates),
        "recommendations_buy": actions["buy"],
        "recommendations_hold": actions["hold"],
        "recommendations_sell": actions["sell"],
        "approved_buy": approved_actions["buy"],
        "approved_sell": approved_actions["sell"],
    }
    for item in rejected:
        reason = str(getattr(item, "reason", "unknown")).strip() or "unknown"
        row[f"rejected_{reason}"] = row.get(f"rejected_{reason}", 0) + 1
    return row


def zero_absent_reasons(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    """Give every session each rejection-reason column seen in the run, 0 if absent."""
    reasons = {key for row in rows for key in row if key.startswith("rejected_")}
    return tuple({**dict.fromkeys(sorted(reasons), 0), **row} for row in rows)
