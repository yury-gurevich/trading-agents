"""Deliberator agent implementation.

Agent: deliberator
Role: serve peer turns and manager verdicts with shared LLMCall attribution.
External I/O: LLM provider via injected LLMClient.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from agents.deliberator.guided_turn import guided_turn
from agents.deliberator.settings import DeliberatorSettings
from agents.deliberator.turn_ledger import LedgerLLM
from contracts.deliberator import (
    DebateProposition,
    DebateTurnRecord,
    DebateTurnReply,
    DebateTurnRequest,
    VerdictReply,
    VerdictRequest,
    contract_for,
)
from kernel import AgentBase, FakeLLMClient, Proposition, Turn
from kernel import judge_verdict as judge_kernel_verdict

if TYPE_CHECKING:
    from agents.deliberator.model_chain import ModelChain
    from kernel import GraphStore, LLMClient, MessageBus
    from kernel.agent import AgentHandler


class DeliberatorAgent(AgentBase):
    """One concrete deliberator role bound to the message bus."""

    def __init__(
        self,
        bus: MessageBus,
        *,
        graph: GraphStore,
        llm: LLMClient | ModelChain | None = None,
        settings: DeliberatorSettings | None = None,
    ) -> None:
        """Create a deliberator instance with injected bus, graph, and LLM.

        In the fleet *llm* is the role's `ModelChain`: its handed-over candidates.
        """
        self.settings = settings if settings is not None else DeliberatorSettings()
        super().__init__(contract_for(self.settings.identity, self.settings.role), bus)
        self._graph = graph
        self._llm: LLMClient | ModelChain = (
            llm if llm is not None else FakeLLMClient({})
        )
        self.handlers = cast(
            "dict[str, AgentHandler]",
            {"debate_turn": self.debate_turn, "verdict": self.verdict},
        )

    def debate_turn(self, request: DebateTurnRequest) -> DebateTurnReply:
        """Return one peer contribution as a guided turn (DLIB-OUT-06)."""
        peer_role = self.settings.peer_role
        if peer_role is not None and request.role != peer_role:
            raise ValueError(f"{self.settings.identity} cannot serve {request.role}")
        model = self.settings.model_for_role(request.role)
        ledger = LedgerLLM(
            self._graph,
            self._llm,
            calling_agent=self.settings.identity,
            model=model,
            correlation_id=request.request_id,
        )
        return DebateTurnReply(
            request_id=request.request_id,
            turn=guided_turn(ledger, request),
            llm_call_key=ledger.last_node_key,
        )

    def verdict(self, request: VerdictRequest) -> VerdictReply:
        """Return the manager ruling using the unchanged verdict parser."""
        model = self.settings.model_for_role("judge")
        ledger = LedgerLLM(
            self._graph,
            self._llm,
            calling_agent=self.settings.identity,
            model=model,
            correlation_id=request.request_id,
        )
        verdict = judge_kernel_verdict(
            ledger,
            _proposition(request.proposition),
            transcript=_transcript(request.transcript),
        )
        return VerdictReply(
            request_id=request.request_id,
            ruling=verdict.ruling,  # type: ignore[arg-type]
            rationale=verdict.rationale,
            llm_call_key=ledger.last_node_key,
        )


def _proposition(proposition: DebateProposition) -> Proposition:
    return Proposition(proposition.decision, proposition.context)


def _transcript(records: tuple[DebateTurnRecord, ...]) -> tuple[Turn, ...]:
    return tuple(Turn(item.role, item.round, item.text) for item in records)
