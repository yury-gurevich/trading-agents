"""Cross-cutting value objects shared by every agent's payloads.

Agent: kernel
Role: the shared value vocabulary every message is built from.
External I/O: none.

These are the lingua franca: small, stable, logic-free types that appear in many
messages. Keeping them here (not in any one agent) is what lets agents share a
vocabulary without importing each other.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class Provenance(_Frozen):
    """The link back into the provenance graph. Travels on every decision payload.

    Lets an auditor answer "what did this rely on?" deterministically and lets the
    reporter stitch scan→exit narratives from message lineage alone.
    """

    run_id: str
    source_agent: str
    correlation_id: str | None = None
    graph_node_id: str | None = None
    incident_refs: tuple[str, ...] = ()
    """Open-incident ids active when this artifact was produced (degraded-data flag)."""


class Explanation(_Frozen):
    """Evidence-grounded, plain-language justification for an outcome.

    Carried by every decision AND every non-decision (why no candidate, why no
    trade) so explainable-silence is a contract obligation, not an afterthought.
    """

    summary: str
    evidence_refs: tuple[str, ...] = ()
