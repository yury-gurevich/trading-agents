"""BarrierSettlement write path: what happened to one claim, recorded once.

Agent: forecaster
Role: persist a claim's settlement as its own append-only node, keyed from the
      claim and linked BarrierForecast -SETTLED_BY-> BarrierSettlement, carrying
      the claim's three-class Brier (absent for a void); and read the ledger back
      for one model (S241, DL-243). The claim itself is never written to: it is a
      record of what was said, and what happened is a later fact of its own.
External I/O: GraphStore reads and writes via the injected backend.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.forecaster.barrier_store import BARRIER_LABEL
from agents.forecaster.domain.barrier_settlement import VOID, brier

if TYPE_CHECKING:
    from agents.forecaster.domain.barrier_settlement import Settlement
    from kernel import GraphStore, Node

SETTLEMENT_LABEL = "BarrierSettlement"
#: BarrierForecast -SETTLED_BY-> BarrierSettlement.
SETTLED_EDGE = "SETTLED_BY"


def settlement_key(claim_key: str) -> str:
    """One settlement per claim: ``settlement:{claim key}``."""
    return f"settlement:{claim_key}"


def settled_claim_keys(graph: GraphStore) -> set[str]:
    """The keys of every claim that already has a settlement."""
    return {str(node.props["claim_key"]) for node in graph.list_nodes(SETTLEMENT_LABEL)}


def write_settlement(
    graph: GraphStore,
    claim: Node,
    settlement: Settlement,
    *,
    settling_ref: str | None,
) -> Node:
    """Record ``settlement`` for ``claim`` and link it from the claim.

    Only the Brier reads the claim's probabilities; the outcome was decided from
    the bars alone. Written once: the pass settles open claims only (FORE-IDM-05).
    """
    probabilities = (
        float(claim.props["p_stop_first"]),
        float(claim.props["p_target_first"]),
        float(claim.props["p_neither"]),
    )
    void = settlement.outcome == VOID
    props: dict[str, object] = {
        "claim_key": claim.key,
        "model_id": claim.props["model_id"],
        "ticker": claim.props["ticker"],
        "as_of": claim.props["as_of"],
        "outcome": settlement.outcome,
        "void_reason": settlement.void_reason,
        "settled_on": settlement.settled_on.isoformat(),
        "settling_ref": settling_ref,
        "entry_close_settling": settlement.entry_close_settling,
        "entry_ratio": settlement.entry_ratio,
        "brier": None if void else brier(probabilities, settlement.outcome),
        "created_at": datetime.now(tz=UTC).isoformat(),
    }
    node = graph.merge_node(SETTLEMENT_LABEL, settlement_key(claim.key), props)
    graph.add_edge(claim, node, SETTLED_EDGE)
    return node


def model_ledger(
    graph: GraphStore, model_id: str
) -> tuple[dict[str, Node], dict[str, Node]]:
    """One model's claims and settlements, each keyed by claim key.

    Two listings of the forecaster's own labels; never a MarketData.
    """
    claims = {
        node.key: node
        for node in graph.list_nodes(BARRIER_LABEL)
        if node.props.get("model_id") == model_id
    }
    settlements = {
        str(node.props["claim_key"]): node
        for node in graph.list_nodes(SETTLEMENT_LABEL)
        if node.props.get("claim_key") in claims
    }
    return claims, settlements
