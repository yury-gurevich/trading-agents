"""Each role's configured output cap reaches both vendors' requests (S257 A2).

Agent: deliberator
Role: test the shared factory and adapters against synthetic vendor SDKs.
External I/O: none; synthetic clients capture the request without a model call.
"""

from __future__ import annotations

import sys
import types
from typing import Any, Literal

import pytest

from agents.deliberator.settings import DebateRole, DeliberatorSettings
from kernel.llm_factory import build_llm


@pytest.mark.parametrize(
    ("provider", "constructor", "cap_key"),
    [
        ("openai", "OpenAI", "max_completion_tokens"),
        ("anthropic", "Anthropic", "max_tokens"),
    ],
)
@pytest.mark.parametrize("role", ["defender", "challenger", "judge"])
def test_each_roles_default_cap_reaches_the_vendor_request(
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
    constructor: str,
    cap_key: str,
    role: DebateRole | Literal["judge"],
) -> None:
    """DLIB-DEP-04 / DLIB-DEP-03: default settings drive the actual request cap."""
    sent: dict[str, Any] = {}

    class Messages:
        def create(self, **kwargs: Any) -> object:
            sent.update(kwargs)
            return types.SimpleNamespace(
                content=[types.SimpleNamespace(type="text", text="answer")],
                stop_reason="end_turn",
                choices=[
                    types.SimpleNamespace(
                        finish_reason="stop",
                        message=types.SimpleNamespace(content="answer"),
                    )
                ],
            )

    class SDK:
        def __init__(self, api_key: str) -> None:
            self.messages = Messages()
            self.chat = types.SimpleNamespace(completions=self.messages)

    module = types.ModuleType(provider)
    setattr(module, constructor, SDK)
    monkeypatch.setitem(sys.modules, provider, module)
    settings = DeliberatorSettings(llm_provider=provider)
    client = build_llm(
        settings.llm_provider,
        api_key="k",
        model=settings.model_for_role(role),
        max_tokens=settings.max_tokens,
        effort=settings.effort,
    )

    assert client.complete(system="system", user="packet", tool_schema={}) == "answer"
    assert sent[cap_key] == 16384
