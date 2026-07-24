"""Formatting helpers for graph-pull trace output.

Agent: orchestration
Role: render numeric diagnostics without treating absent evidence as measured zero.
External I/O: none.
"""

from __future__ import annotations

import math


def metric_text(value: object, spec: str) -> str:
    """Format a metric value, preserving unavailable evidence as text."""
    if not isinstance(value, int | float) or not math.isfinite(value):
        return "unavailable"
    return format(float(value), spec)
