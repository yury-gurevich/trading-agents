"""Run a DSPy program through the caller's own LLM client.

Agent: kernel
Role: supply DSPy's engine protocol without another transport, cache or history.
External I/O: the injected LLM client only; never a DSPy vendor client.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import dspy  # type: ignore[import-untyped]
from dspy.lm15 import (  # type: ignore[import-untyped]
    Message,
    Request,
    Response,
    TextPart,
    Usage,
    response_to_events,
)
from dspy.utils.exceptions import LMUnexpectedError  # type: ignore[import-untyped]

from kernel.llm import LLMCompletionStoppedError

if TYPE_CHECKING:
    from collections.abc import Iterator

    from kernel.llm import LLMClient

# Neither cache belongs in the served path; the caller's ledger owns evidence.
dspy.configure_cache(enable_disk_cache=False, enable_memory_cache=False)


class ClientEngine:
    """An lm15 engine that makes exactly one call through the injected client."""

    def __init__(self, llm: LLMClient, *, empty_stop_reason: str) -> None:
        """Wrap the caller's client and its chosen blank-completion reason."""
        self._llm = llm
        self._empty_stop_reason = empty_stop_reason

    def complete(self, request: Request) -> Response:
        """Keep the rendered messages intact and return the client's completion."""
        text = self._llm.complete(
            system=request.system, user=request.messages[0].text, tool_schema={}
        )
        if not text.strip():
            raise LLMCompletionStoppedError(
                provider="kernel", stop_reason=self._empty_stop_reason
            )
        return Response(
            id=None,
            model=request.model,
            message=Message.assistant([TextPart(text)]),
            finish_reason="stop",
            usage=Usage(input_tokens=0, output_tokens=0, total_tokens=0),
        )

    def stream(self, request: Request) -> Iterator[Any]:
        """Expose lm15's stream protocol over that same single completion."""
        return response_to_events(self.complete(request))  # type: ignore[no-any-return]

    def close(self) -> None:
        """The caller owns its client; this wrapper owns no resources."""


def run_program(
    program: dspy.Module,
    llm: LLMClient,
    *,
    adapter: dspy.Adapter,
    empty_stop_reason: str,
    **inputs: object,
) -> dspy.Prediction:
    """Execute in this thread's context; preserve the client's failure type."""
    lm = dspy.LM(
        "custom/deliberator",
        engine=ClientEngine(llm, empty_stop_reason=empty_stop_reason),
        cache=False,
        num_retries=0,
    )
    try:
        with dspy.context(lm=lm, adapter=adapter, disable_history=True):
            return program(**inputs)
    except LMUnexpectedError as exc:
        if exc.__cause__ is not None:
            raise exc.__cause__ from None
        raise
