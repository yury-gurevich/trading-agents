"""Predictor-registry evidence gate and promotion-status derivation.

Agent: curator
Role: decide promotion eligibility from frozen evidence; derive promotion status.
External I/O: GraphStore reads.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.curator.settings import CuratorSettings
    from kernel import GraphStore, Node

# Flag/FlagResolution keys are supervisor-owned; we never import that module.
# Replicated from agents/supervisor/store.py (_flag_key / _resolution_key):
#   flag:{subject_ref}:{severity}  ·  resolution:flag:{subject_ref}:{severity}
_SEVERITY = "info"  # matches the severity of the flag the promotion flow raises


def check_promotion_evidence(
    predictor: Node, settings: CuratorSettings
) -> tuple[bool, str]:
    """Return (ok, reason) from the predictor's frozen accuracy + sample_size."""
    accuracy = float(predictor.props.get("accuracy", 0.0))
    sample_size = int(predictor.props.get("sample_size", 0))
    floor = settings.min_promotion_accuracy
    if accuracy < floor:
        return False, f"accuracy {accuracy:.2f} below {floor:.2f}"
    minimum = settings.min_promotion_sample_size
    if sample_size < minimum:
        return False, f"sample_size {sample_size} below {minimum}"
    return True, "evidence gate passed"


def is_promoted(graph: GraphStore, predictor_id: str) -> bool:
    """True iff a load_bearing PredictorPromotion exists for this predictor."""
    return graph.get_node("PredictorPromotion", f"promotion:{predictor_id}") is not None


def promotion_status(graph: GraphStore, predictor_id: str) -> str:
    """Derive 'load_bearing' | 'pending_approval' | 'advisory' for a predictor."""
    if is_promoted(graph, predictor_id):
        return "load_bearing"
    subject = f"predictor:{predictor_id}"
    flag = graph.get_node("Flag", f"flag:{subject}:{_SEVERITY}")
    resolution = graph.get_node(
        "FlagResolution", f"resolution:flag:{subject}:{_SEVERITY}"
    )
    if flag is not None and resolution is None:
        return "pending_approval"
    return "advisory"
