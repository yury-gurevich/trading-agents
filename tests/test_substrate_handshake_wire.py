"""The moved types are the same objects, and the wire does not move.

Agent: kernel
Role: prove `kernel.payload` and `contracts.common` share one frozen base and
      the same `Provenance`/`Explanation` classes (not copies), and that the
      handshake and evidence payloads still serialise to the same JSON bytes
      after the move (ADR-0012, DL-12, S232).
External I/O: none.
"""

from __future__ import annotations

import contracts.common as common
import kernel.payload as payload
from contracts.scanner import CandidateSet, FilterTrace
from kernel.handshake import ACTIVATEMessage, EHLOMessage


def test_the_frozen_base_and_evidence_types_are_the_same_objects() -> None:
    """MST-TYP-01: no second frozen base — contracts.common re-exports kernel's."""
    assert common._Frozen is payload._Frozen
    assert common.Provenance is payload.Provenance
    assert common.Explanation is payload.Explanation


def test_the_ehlo_dict_kernel_bootstrap_sends_still_parses() -> None:
    """The shape kernel/bootstrap.py posts to /ehlo still validates unchanged."""
    ehlo_dict = {
        "ephemeral_boot_id": "boot:abc123",
        "agent_type": "scanner",
        "capability_declaration": {"graph": {"operations": ["append_write"]}},
    }
    ehlo = EHLOMessage.model_validate(ehlo_dict)

    assert (
        ehlo.model_dump_json()
        == '{"ephemeral_boot_id":"boot:abc123","agent_type":"scanner",'
        '"capability_declaration":{"graph":{"operations":["append_write"]}}}'
    )


def test_the_activate_message_wire_shape_is_unchanged() -> None:
    activate = ACTIVATEMessage(
        instance_id="scanner:20260620T090000:0",
        agent_type="scanner",
        capability_grants={"graph": {"operations": ["append_write"]}},
        config={},
        signature="",
    )

    assert activate.model_dump_json() == (
        '{"instance_id":"scanner:20260620T090000:0","agent_type":"scanner",'
        '"capability_grants":{"graph":{"operations":["append_write"]}},'
        '"config":{},"signature":""}'
    )


def test_a_pack_payload_carrying_provenance_and_explanation_is_unchanged() -> None:
    """`kernel.payload`'s evidence types serialise the same under `contracts`."""
    candidate_set = CandidateSet(
        run_id="run:1",
        candidates=(),
        filter_trace=FilterTrace(universe_size=0, evaluated=0),
        explanation=common.Explanation(summary="no candidates survived"),
        provenance=common.Provenance(run_id="run:1", source_agent="scanner"),
    )

    assert candidate_set.model_dump_json() == (
        '{"run_id":"run:1","candidates":[],'
        '"filter_trace":{"universe_size":0,"evaluated":0,'
        '"dropped_by_filter":{},"verdicts":[]},'
        '"explanation":{"summary":"no candidates survived","evidence_refs":[]},'
        '"provenance":{"run_id":"run:1","source_agent":"scanner",'
        '"correlation_id":null,"graph_node_id":null,"incident_refs":[]}}'
    )
