"""Offline completion fixtures shared by operator and chat cut-off tests.

Agent: operator
Role: script SDK replies through real adapters and assert literal ledger counts.
External I/O: none; SDK constructors and requests are injected fakes.
"""

from __future__ import annotations

import importlib
import json
from types import SimpleNamespace
from typing import TYPE_CHECKING

from kernel import LLMCompletionStoppedError
from kernel.llm_factory import (
    build_operator_llm,
    default_model_for,
    default_operator_effort_for,
)
from kernel.llm_tokens import LLMUsage

if TYPE_CHECKING:
    import pytest

    from kernel import LLMClient, Node

PARTIAL_ANSWER = "The run finished: 8 of"
EXPLAIN_INTENT: dict[str, object] = {
    "outcome": "intent",
    "family": "explain",
    "parameters": {"subject": "how the run finished"},
}


def vendor_reply(
    provider: str, stop_reason: str, data: dict[str, object] | None = None
) -> object:
    """Build only the vendor fields the real operator adapter reads."""
    if provider == "anthropic":
        return SimpleNamespace(
            stop_reason=stop_reason,
            content=[SimpleNamespace(type="tool_use", input=data)]
            if data is not None
            else [SimpleNamespace(type="thinking", thinking="private reasoning")],
            usage=SimpleNamespace(
                input_tokens=21_133,
                output_tokens=4096,
                cache_read_input_tokens=0,
                cache_creation_input_tokens=0,
            ),
        )
    return SimpleNamespace(
        status="completed" if stop_reason == "completed" else "incomplete",
        incomplete_details=None
        if stop_reason == "completed"
        else SimpleNamespace(reason=stop_reason),
        output=[SimpleNamespace(type="function_call", arguments=json.dumps(data))]
        if data is not None
        else [SimpleNamespace(type="reasoning")],
        usage=SimpleNamespace(
            input_tokens=21_133,
            output_tokens=4096,
            input_tokens_details=SimpleNamespace(cached_tokens=0),
        ),
    )


def scripted_client(
    monkeypatch: pytest.MonkeyPatch, provider: str, replies: list[object]
) -> tuple[LLMClient, list[dict[str, object]]]:
    """Build the selected real adapter on a request-counting fake SDK."""
    pending = iter(replies)
    requests: list[dict[str, object]] = []
    real_import = importlib.import_module

    def create(**kwargs: object) -> object:
        requests.append(kwargs)
        reply = next(pending)
        if isinstance(reply, Exception):
            raise reply
        return reply

    def sdk_client(*, api_key: str) -> object:
        assert api_key == "fixture-key"  # pragma: allowlist secret
        endpoint = SimpleNamespace(create=create)
        return SimpleNamespace(messages=endpoint, responses=endpoint)

    def fake_import(name: str, package: str | None = None) -> object:
        if name == provider:
            return SimpleNamespace(Anthropic=sdk_client, OpenAI=sdk_client)
        return real_import(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import)
    client = build_operator_llm(
        provider,
        api_key="fixture-key",  # pragma: allowlist secret
        model=default_model_for(provider),
        max_tokens=4096,
        effort=default_operator_effort_for(provider),
    )
    return client, requests


def assert_vendor_row(row: Node, stop_reason: str) -> None:
    """Assert reported counts, their provenance, and the vendor's stop word."""
    assert row.props["stop_reason"] == stop_reason
    assert row.props["tokens_in"] == 21_133
    assert row.props["tokens_out"] == 4096
    assert row.props.get("token_source") == "vendor"


class CompletionStub:
    """Expose metadata like an adapter, or fail before a reply exists."""

    def __init__(
        self,
        stop_reason: str = "completed",
        response: str = "finished answer",
        *,
        stopped: bool = False,
        failed: bool = False,
    ) -> None:
        self.reason = stop_reason
        self.response = response
        self.stopped = stopped
        self.failed = failed
        self.last_stop_reason = "unknown"
        self.last_usage: LLMUsage | None = None
        self.requests: list[tuple[str, str, dict[str, object]]] = []

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        self.requests.append((system, user, tool_schema))
        if self.failed:
            raise TimeoutError("fixture request timed out")
        self.last_stop_reason = self.reason
        self.last_usage = LLMUsage(tokens_in=21_133, tokens_out=4096)
        if self.stopped:
            raise LLMCompletionStoppedError(
                provider="anthropic" if self.reason == "max_tokens" else "openai",
                stop_reason=self.reason,
            )
        return self.response
