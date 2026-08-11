"""The OpenAI adapter sends what the tunables say, not just what it stores.

Agent: deliberator
Role: pin the wire shape of the OpenAI deliberation call — the system/user
      split, the token cap, and the reasoning effort the operator selected.
External I/O: none — the SDK is faked; no vendor is contacted.

Split out of `test_llm_provider.py` at the 200-line hard block. That file pins
*which* provider is chosen; this one pins what the chosen provider is sent.
"""

from __future__ import annotations

import sys
import types
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pytest


def test_complete_sends_system_and_user_and_returns_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The adapter maps the port's system/user split onto chat messages."""
    from agents.deliberator.llm_openai import OpenAILLMClient

    sent: dict[str, Any] = {}

    class _Completions:
        def create(self, **kwargs: Any) -> Any:
            sent.update(kwargs)
            return types.SimpleNamespace(
                choices=[
                    types.SimpleNamespace(
                        message=types.SimpleNamespace(content="uphold")
                    )
                ]
            )

    class _SDK:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key
            self.chat = types.SimpleNamespace(completions=_Completions())

    module = types.ModuleType("openai")
    module.OpenAI = _SDK  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "openai", module)

    client = OpenAILLMClient(
        api_key="k", model="gpt-5.5", max_tokens=32, effort="medium"
    )
    answer = client.complete(system="be terse", user="review this", tool_schema={})

    assert answer == "uphold"
    assert sent["model"] == "gpt-5.5"
    assert sent["max_completion_tokens"] == 32
    assert [m["role"] for m in sent["messages"]] == ["system", "user"]
    assert sent["messages"][0]["content"] == "be terse"
    # DL-105: the adapter stored `effort` and never sent it, so the tunable read
    # as live and did nothing. Asserting on the *stored* attribute is what let
    # that survive at 100 % coverage — assert on what reaches the wire.
    assert sent["reasoning_effort"] == "medium"


# Read off `openai` 2.49.0 on 2026-08-11. Pinned rather than imported because
# `openai` is an optional extra (`llm`) that CI's `uv sync --frozen` does not
# install — an importorskip here would skip on every CI run, which is decoration
# rather than a check. The live cross-check below runs wherever the extra exists.
_OPENAI_REASONING_EFFORT = frozenset(
    {"none", "minimal", "low", "medium", "high", "xhigh", "max"}
)


def test_our_effort_values_are_all_valid_openai_values() -> None:
    """DL-105: `Effort` must stay a subset of the SDK's `ReasoningEffort`.

    Pass-through is unmapped, so a value we can hold but OpenAI cannot accept
    would 400 at run time on a live deliberation rather than in CI. The risk is
    ours: widening `Effort` is what breaks this, not the vendor narrowing.
    """
    import importlib
    from typing import get_args

    from agents.deliberator.settings import Effort

    ours = set(get_args(Effort))
    assert ours <= _OPENAI_REASONING_EFFORT, (
        f"not accepted by OpenAI: {sorted(ours - _OPENAI_REASONING_EFFORT)}"
    )

    try:  # pragma: no cover - only where the optional `llm` extra is installed
        module = importlib.import_module("openai.types.shared.reasoning_effort")
    except ModuleNotFoundError:
        return
    live = set(get_args(get_args(module.ReasoningEffort)[0]))  # pragma: no cover
    assert live == _OPENAI_REASONING_EFFORT, (  # pragma: no cover
        f"pinned set is stale against the installed SDK: {sorted(live)}"
    )
