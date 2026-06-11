"""Researcher agent implementation.

Agent: researcher
Role: mine graph evidence and propose bounded changes for operator review.
External I/O: MessageBus calls to supervisor.flag_for_human.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from agents.researcher.domain.evidence import collect_evidence
from agents.researcher.domain.proposal import build_proposal
from agents.researcher.settings import ResearcherSettings
from agents.researcher.store import write_proposal
from contracts.common import Explanation, Provenance
from contracts.researcher import CONTRACT, ParameterChangeProposal, ResearchRequest
from contracts.supervisor import FlagRequest
from kernel import AgentBase, AgentMessage, CollectingFaultSink, FaultSink, GraphStore
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from pydantic import BaseModel

    from agents.researcher.domain.evidence import RunEvidence
    from kernel import MessageBus


class ResearcherAgent(AgentBase):
    """Researcher boundary agent."""

    def __init__(
        self,
        bus: MessageBus,
        *,
        graph: GraphStore,
        settings: ResearcherSettings | None = None,
        sink: FaultSink | None = None,
    ) -> None:
        """Create researcher with injected bus, graph, settings, and sink."""
        super().__init__(CONTRACT, bus)
        self._graph = graph
        self._settings = settings or ResearcherSettings()
        self.sink = sink if sink is not None else CollectingFaultSink()
        self.handlers = {"propose": self._propose, "evidence": self._evidence}

    def _propose(self, request: BaseModel) -> ParameterChangeProposal:
        model = ResearchRequest.model_validate(request)
        result = _zero_proposal(_new_id(), "researcher proposal failed")
        with fault_boundary(
            self.sink,
            agent="researcher",
            module="agents.researcher.agent",
            capability="propose",
            reraise=False,
        ) as capture:
            result = self._build_and_record_proposal(model)
        if capture.fault is not None:
            return result
        return result

    def _evidence(self, request: BaseModel) -> Explanation:
        ResearchRequest.model_validate(request)
        result = Explanation(summary="researcher evidence lookup failed")
        with fault_boundary(
            self.sink,
            agent="researcher",
            module="agents.researcher.agent",
            capability="evidence",
            reraise=False,
        ) as capture:
            result = self._evidence_summary()
        if capture.fault is not None:
            return result
        return result

    def _build_and_record_proposal(
        self, request: ResearchRequest
    ) -> ParameterChangeProposal:
        del request
        evidence = collect_evidence(self._graph, self._settings.min_sample_runs)
        if evidence is None:
            return _zero_proposal(_new_id(), "insufficient data for evidence window")
        proposal = build_proposal(evidence, self._settings, _new_id())
        write_proposal(self._graph, proposal)
        if proposal.changes:
            self._flag_for_review(proposal)
        return proposal

    def _evidence_summary(self) -> Explanation:
        evidence = collect_evidence(self._graph, self._settings.min_sample_runs)
        if evidence is None:
            return Explanation(summary="insufficient data for evidence window")
        return Explanation(summary=_evidence_text(evidence))

    def _flag_for_review(self, proposal: ParameterChangeProposal) -> None:
        self.bus.request(
            AgentMessage(
                sender="researcher",
                recipient="supervisor",
                message_type="request",
                capability="flag_for_human",
                payload=FlagRequest(
                    subject_ref=f"proposal:{proposal.proposal_id}",
                    severity="info",
                    reason=f"Researcher proposes {len(proposal.changes)} change(s)",
                ).model_dump(mode="json"),
            )
        )


def _new_id() -> str:
    return uuid4().hex[:12]


def _zero_proposal(proposal_id: str, reason: str) -> ParameterChangeProposal:
    return ParameterChangeProposal(
        proposal_id=proposal_id,
        changes=(),
        rationale=Explanation(summary=reason),
        provenance=Provenance(run_id=proposal_id, source_agent="researcher"),
    )


def _evidence_text(evidence: RunEvidence) -> str:
    return (
        f"{evidence.snapshot_count} snapshots; "
        f"avg_confidence={evidence.avg_confidence:.2f}; "
        f"approval_rate={evidence.avg_approval_rate:.2f}; "
        f"rejections={evidence.avg_rejection_count:.2f}"
    )
