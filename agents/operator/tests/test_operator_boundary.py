"""Operator contract-boundary tests.

Agent: operator
Role: pin which graph labels the operator claims as a single writer.
External I/O: none.
"""

from __future__ import annotations

from contracts.operator import CONTRACT


def test_operator_boundary_claims_graph_labels_once() -> None:
    """OPR-IDN-02: operator exclusively owns CommandAudit, Intent.

    Single-writer rule.
    """
    assert CONTRACT.owns_graph == ("CommandAudit", "Intent")


def test_operator_does_not_claim_llmcall_as_a_single_writer_label() -> None:
    """OPR-IDN-02 / ADR-0020: LLMCall is substrate, multi-writer by design.

    Pinned separately from the positive assertion so that re-adding LLMCall to
    ``owns_graph`` fails against a test that names the reason, rather than
    looking like an ordinary tuple edit. The operator still *writes* LLMCall —
    it no longer claims exclusivity, because every LLM-calling agent writes
    into the same shared cost ledger.
    """
    assert "LLMCall" not in CONTRACT.owns_graph
