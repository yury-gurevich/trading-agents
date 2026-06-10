"""Scanner agent contract — universe down to a ranked candidate set.

Agent: scanner
Role: contract — typed boundary (capabilities, owned data, never-do).
External I/O: none.
"""

from __future__ import annotations

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


class FilterTrace(_Frozen):
    """Why the universe shrank — every drop is attributable."""

    universe_size: int = Field(ge=0)
    evaluated: int = Field(ge=0)
    dropped_by_filter: dict[str, int] = Field(default_factory=dict)


class CandidateSet(_Frozen):
    run_id: str
    candidates: tuple[Candidate, ...]
    filter_trace: FilterTrace
    explanation: Explanation
    provenance: Provenance


CONTRACT = AgentContract(
    name="scanner",
    version="0.1.0",
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
