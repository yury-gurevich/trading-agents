"""Scanner agent contract — universe down to a ranked candidate set.

Agent: scanner
Role: contract — typed boundary (capabilities, owned data, never-do).
External I/O: none.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from contracts.common import Explanation, Provenance, ScanRequest, Ticker, _Frozen
from kernel.contract import AgentContract, Capability


# ── Outbound payloads ───────────────────────────────────────────────────────
class Candidate(_Frozen):
    ticker: Ticker
    rank: int = Field(ge=1)
    score: float
    survived_filters: tuple[str, ...]
    metrics: dict[str, float] = Field(default_factory=dict)
    """Filter inputs worth carrying forward (beta, relative_strength, returns...)."""


class FilterVerdict(_Frozen):
    """Per-ticker scan decision + the features it was judged on.

    The labeled training record for DL-09: every evaluated ticker gets a verdict
    (survived, or dropped by ``filter_fired``) with the ``features`` the filters
    judged. ``bypassed`` is True when a would-be-dropped ticker was let through
    anyway (``bypass_scanner_filter``) so its downstream outcome can be observed.
    """

    ticker: Ticker
    decision: Literal["survived", "dropped"]
    filter_fired: str | None = None
    features: dict[str, float] = Field(default_factory=dict)
    bypassed: bool = False


class FilterTrace(_Frozen):
    """Why the universe shrank — every drop is attributable."""

    universe_size: int = Field(ge=0)
    evaluated: int = Field(ge=0)
    dropped_by_filter: dict[str, int] = Field(default_factory=dict)
    verdicts: tuple[FilterVerdict, ...] = ()
    """Per-ticker decisions + features — the DL-09 filter-quality training record."""


class CandidateSet(_Frozen):
    run_id: str
    candidates: tuple[Candidate, ...]
    filter_trace: FilterTrace
    explanation: Explanation
    provenance: Provenance


CONTRACT = AgentContract(
    name="scanner",
    version="0.2.0",
    mission=(
        "Reduce the full tradable universe to a small, ranked set of candidates "
        "worth deeper analysis, and explain why each survived or was filtered out."
    ),
    consumes=(
        Capability(
            "run_scan",
            "Scan a named universe into a ranked, explained candidate set.",
            request=ScanRequest,
            response=CandidateSet,
            mcp=True,
        ),
        Capability(
            "explain_filter",
            "Explain why a given ticker passed or failed the scan.",
            request=ScanRequest,
            response=Explanation,
            mcp=True,
        ),
    ),
    emits=("scan_completed",),
    owns_graph=("ScanRun", "Candidate"),
    external_io=(),
    depends_on=("provider",),
    mcp_tools=("run_scan", "explain_filter"),
    never=(
        "score or recommend (that is the analyst's job)",
        "call a market-data API directly (request it from provider)",
        "size or approve trades",
    ),
)
