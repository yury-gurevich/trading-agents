"""The ledger row around each completion a deliberator role makes.

Agent: deliberator
Role: write one LLMCall per completion attempt, and send a request a vendor refused
      to the role's next handed-over candidate (DLIB-OBS-08, DLIB-FAIL-05).
External I/O: GraphStore writes; the LLM vendor through the injected clients.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.deliberator.model_chain import ModelChain, RoleCandidate, refusal
from agents.deliberator.prompt_recipe import PROMPT_RECIPE_HASH
from kernel import (
    LLMCompletionStoppedError,
    llm_stop_reason,
    llm_usage,
    record_llm_call,
)

if TYPE_CHECKING:
    from kernel import GraphStore, LLMClient, Node


class LedgerLLM:
    """LLMClient wrapper that writes one shared LLMCall node per completion.

    Given a plain client it runs that client under *model*, as before; given the
    role's `ModelChain` it runs the candidate in use, and a vendor's error answer
    sends the request to the next candidate, each attempt its own row.
    """

    def __init__(
        self,
        graph: GraphStore,
        llm: LLMClient | ModelChain,
        *,
        calling_agent: str,
        model: str,
        correlation_id: str,
    ) -> None:
        """Wrap the role's client or chain for one request."""
        self._graph = graph
        self._chain = (
            llm
            if isinstance(llm, ModelChain)
            else ModelChain((RoleCandidate("", model, llm),))
        )
        self._calling_agent = calling_agent
        self._correlation_id = correlation_id
        self.last_node_key: str | None = None

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        """Answer on the candidate in use; a vendor's refusal moves to the next."""
        candidate = self._chain.current()
        passed_over: list[str] = []
        while True:
            try:
                return self._attempt(
                    candidate, tuple(passed_over), system, user, tool_schema
                )
            except Exception as exc:
                reason = refusal(exc)
                following = None if reason is None else self._chain.after(candidate)
                if following is None:
                    raise
                passed_over.append(f"{candidate.label}: {reason}")
                candidate = following

    def _attempt(
        self,
        candidate: RoleCandidate,
        passed_over: tuple[str, ...],
        system: str,
        user: str,
        tool_schema: dict[str, object],
    ) -> str:
        """Record one call around one candidate's completion."""
        llm = candidate.client
        raw = ""
        stopped: LLMCompletionStoppedError | None = None
        with record_llm_call(
            self._graph,
            calling_agent=self._calling_agent,
            correlation_id=self._correlation_id,
            model=candidate.model,
            prompt=user,
            system_prompt=system,
            prompt_recipe_hash=PROMPT_RECIPE_HASH,
            passed_over=passed_over,
        ) as call:
            try:
                raw = llm.complete(system=system, user=user, tool_schema=tool_schema)
            except LLMCompletionStoppedError as exc:
                call.set_stop_reason(exc.stop_reason)
                stopped = exc
            else:
                call.set_response(raw)
                call.set_stop_reason(llm_stop_reason(llm))
            # Usage is read on both paths: a truncated or refused completion was
            # still generated and still billed, so dropping its tokens here would
            # under-report exactly the calls that cost the most — `effort=max`
            # spends the whole output budget before raising `max_tokens`, and the
            # estimate fallback sees an empty response, so a success-only capture
            # records those calls as costing *zero* output. Measured: planting
            # that guard turned the truncation test red at `assert 0 == 4096`.
            call.set_usage(llm_usage(llm))
        node: Node | None = call.node
        self.last_node_key = node.key if node is not None else None
        if stopped is not None:
            raise stopped
        return raw
