"""Deliberator agent implementation.

Agent: deliberator
Role: serve peer turns and manager verdicts with shared LLMCall attribution.
External I/O: LLM provider via injected LLMClient.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from agents.deliberator.settings import DeliberatorSettings
from contracts.deliberator import (
    DebateProposition,
    DebateRole,
    DebateTurnRecord,
    DebateTurnReply,
    DebateTurnRequest,
    VerdictReply,
    VerdictRequest,
    contract_for,
)
from kernel import (
    AgentBase,
    FakeLLMClient,
    Proposition,
    Turn,
    debate_turn,
    record_llm_call,
)
from kernel import judge_verdict as judge_kernel_verdict

if TYPE_CHECKING:
    from kernel import GraphStore, LLMClient, MessageBus, Node
    from kernel.agent import AgentHandler


class DeliberatorAgent(AgentBase):
    """One concrete deliberator role bound to the message bus."""

    def __init__(
        self,
        bus: MessageBus,
        *,
        graph: GraphStore,
        llm: LLMClient | None = None,
        settings: DeliberatorSettings | None = None,
    ) -> None:
        """Create a deliberator instance with injected bus, graph, and LLM."""
        self.settings = settings if settings is not None else DeliberatorSettings()
        super().__init__(contract_for(self.settings.identity, self.settings.role), bus)
        self._graph = graph
        self._llm = llm if llm is not None else FakeLLMClient({})
        self.handlers = cast(
            "dict[str, AgentHandler]",
            {"debate_turn": self.debate_turn, "verdict": self.verdict},
        )

    def debate_turn(self, request: DebateTurnRequest) -> DebateTurnReply:
        """Return one peer contribution using the unchanged debate-core prompt."""
        peer_role = self.settings.peer_role
        if peer_role is not None and request.role != peer_role:
            raise ValueError(f"{self.settings.identity} cannot serve {request.role}")
        model = self.settings.model_for_role(request.role)
        ledger = _LedgerLLM(
            self._graph,
            self._llm,
            calling_agent=self.settings.identity,
            model=model,
            correlation_id=request.request_id,
        )
        turn = debate_turn(
            ledger,
            _proposition(request.proposition),
            role=request.role,
            round_number=request.round_number,
            transcript=_transcript(request.transcript),
        )
        return DebateTurnReply(
            request_id=request.request_id,
            turn=_turn_record(turn),
            llm_call_key=ledger.last_node_key,
        )

    def verdict(self, request: VerdictRequest) -> VerdictReply:
        """Return the manager ruling using the unchanged verdict parser."""
        model = self.settings.model_for_role("judge")
        ledger = _LedgerLLM(
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


class _LedgerLLM:
    """LLMClient wrapper that writes one shared LLMCall node per completion."""

    def __init__(
        self,
        graph: GraphStore,
        llm: LLMClient,
        *,
        calling_agent: str,
        model: str,
        correlation_id: str,
    ) -> None:
        self._graph = graph
        self._llm = llm
        self._calling_agent = calling_agent
        self._model = model
        self._correlation_id = correlation_id
        self.last_node_key: str | None = None

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        """Record a call around the injected LLM completion."""
        with record_llm_call(
            self._graph,
            calling_agent=self._calling_agent,
            correlation_id=self._correlation_id,
            model=self._model,
            prompt=user,
        ) as call:
            raw = self._llm.complete(system=system, user=user, tool_schema=tool_schema)
            call.set_response(raw)
        node: Node | None = call.node
        self.last_node_key = node.key if node is not None else None
        return raw


def _proposition(proposition: DebateProposition) -> Proposition:
    return Proposition(proposition.decision, proposition.context)


def _transcript(records: tuple[DebateTurnRecord, ...]) -> tuple[Turn, ...]:
    return tuple(Turn(item.role, item.round, item.text) for item in records)


def _turn_record(turn: Turn) -> DebateTurnRecord:
    return DebateTurnRecord(
        role=cast("DebateRole", turn.role),
        round=turn.round,
        text=turn.text,
    )
