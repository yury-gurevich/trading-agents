"""Operator agent implementation.

Agent: operator
Role: expose bounded human-command interpretation and explanation capabilities.
External I/O: LLM provider via injected LLMClient.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.operator.domain.evidence import gather_evidence
from agents.operator.domain.grammar import normalize_explicit_intent
from agents.operator.domain.prompts import (
    INTENT_TOOL_SCHEMA,
    build_explain_system,
    build_explain_user,
    build_interpret_system,
    build_interpret_user,
)
from agents.operator.domain.result import (
    CUT_OFF_REPLY,
    failed_request,
    failed_request_reply,
    intent_from_data,
    message,
    outcome,
    parse_json,
    refused,
    request_correlation,
    with_graph,
)
from agents.operator.ledger import recorded_completion
from agents.operator.settings import OperatorSettings
from agents.operator.store import write_command_audit, write_intent
from contracts.common import Explanation
from contracts.operator import (
    CONTRACT,
    CommandResult,
    ExplainRequest,
    HumanCommand,
)
from kernel import (
    AgentBase,
    CollectingFaultSink,
    FakeLLMClient,
    FaultSink,
    GraphStore,
)
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from contextlib import AbstractContextManager

    from pydantic import BaseModel

    from kernel import FaultCapture, LLMClient, MessageBus


class OperatorAgent(AgentBase):
    """Bounded operator LLM bridge."""

    def __init__(
        self,
        bus: MessageBus,
        *,
        graph: GraphStore,
        llm: LLMClient | None = None,
        settings: OperatorSettings | None = None,
        sink: FaultSink | None = None,
    ) -> None:
        """Create operator with injected bus, graph, LLM, settings, and sink."""
        super().__init__(CONTRACT, bus)
        self._graph = graph
        self._settings = settings or OperatorSettings()
        self._llm = llm if llm is not None else FakeLLMClient({})
        self.sink = sink if sink is not None else CollectingFaultSink()
        self.handlers = {"interpret": self._interpret, "explain": self._explain}

    def _boundary(self, capability: str) -> AbstractContextManager[FaultCapture]:
        return fault_boundary(
            self.sink,
            agent="operator",
            module="agents.operator.agent",
            capability=capability,
            reraise=False,
        )

    def _interpret(self, request: BaseModel) -> CommandResult:
        command = HumanCommand.model_validate(request)
        with self._boundary("interpret") as capture:
            result = self._interpret_command(command)
        if capture.fault is not None:
            return refused("Operator could not parse the command.")
        return result

    def _explain(self, request: BaseModel) -> Explanation:
        explain = ExplainRequest.model_validate(request)
        corr = request_correlation(
            explain.request_id, "explain", explain.subject, "operator"
        )
        evidence = gather_evidence(
            self._graph, explain.subject, self._settings.explain_max_evidence_nodes
        )
        system = build_explain_system()
        user = build_explain_user(explain.subject, evidence)
        row, raw, fault = recorded_completion(
            self._graph,
            self._llm,
            self._boundary("explain"),
            correlation_id=corr,
            model=self._settings.resolved_model,
            system=system,
            user=user,
            tool_schema={},
        )
        write_command_audit(
            self._graph,
            correlation_id=corr,
            actor="operator",
            channel="dashboard",
            text=explain.subject,
            outcome="explain",
            llm_call_node=row,
        )
        if fault is not None:
            return Explanation(summary=failed_request_reply(fault))
        if raw is None:
            return Explanation(summary=CUT_OFF_REPLY)
        return Explanation(summary=raw.strip() or "No explanation returned.")

    def _interpret_command(self, command: HumanCommand) -> CommandResult:
        corr = request_correlation(
            command.request_id, command.actor, command.channel, command.text
        )
        system = self._settings.system_prompt or build_interpret_system()
        user = build_interpret_user(command)
        row, raw, fault = recorded_completion(
            self._graph,
            self._llm,
            self._boundary("interpret"),
            correlation_id=corr,
            model=self._settings.resolved_model,
            system=system,
            user=user,
            tool_schema=INTENT_TOOL_SCHEMA,
        )
        if fault is not None:
            data = failed_request(fault)
        else:
            data = normalize_explicit_intent(command.text, parse_json(raw))
        parsed_outcome = outcome(data)
        audit = write_command_audit(
            self._graph,
            correlation_id=corr,
            actor=command.actor,
            channel=command.channel,
            text=command.text,
            outcome=parsed_outcome,
            llm_call_node=row,
        )
        if parsed_outcome != "intent":
            return CommandResult(outcome=parsed_outcome, message=message(data))
        intent = intent_from_data(data, corr)
        if intent is None:
            return CommandResult(outcome="refused", message=message(data))
        node = write_intent(
            self._graph, correlation_id=corr, audit_node=audit, intent=intent
        )
        return CommandResult(
            outcome="intent",
            intent=with_graph(intent, node),
            message=Explanation(summary=f"Parsed {intent.family} intent."),
        )
