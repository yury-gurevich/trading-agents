"""Operator Responses request and accounting contract.

Agent: kernel
Role: pin the measured forced-function request and reply handling.
External I/O: none; only a fake SDK is called.
"""

import importlib
import json
from types import SimpleNamespace

import pytest

from kernel import llm_openai_operator as adapter
from kernel.llm import LLMCompletionStoppedError


def install_sdk(
    monkeypatch: pytest.MonkeyPatch, response: object
) -> list[dict[str, object]]:
    """Install a Responses-only SDK and collect its wire arguments."""
    calls: list[dict[str, object]] = []

    def create(**kwargs: object) -> object:
        calls.append(kwargs)
        return response

    monkeypatch.setattr(
        importlib,
        "import_module",
        lambda name: SimpleNamespace(
            OpenAI=lambda **kwargs: SimpleNamespace(
                responses=SimpleNamespace(create=create)
            )
        ),
    )
    return calls


def reply(*, cached: int = 100) -> object:
    """Reasoning precedes two calls; only the first function call is consumed."""
    return SimpleNamespace(
        status="completed",
        incomplete_details=None,
        output=[
            SimpleNamespace(type="reasoning"),
            SimpleNamespace(
                type="function_call", arguments='{"outcome":"intent","answer":"safe"}'
            ),
            SimpleNamespace(
                type="function_call", arguments='{"answer":"wrong second call"}'
            ),
        ],
        usage=SimpleNamespace(
            input_tokens=400,
            output_tokens=25,
            input_tokens_details=SimpleNamespace(
                cached_tokens=cached, cache_write_tokens=999
            ),
        ),
    )


def test_a1_measured_request(monkeypatch: pytest.MonkeyPatch) -> None:
    """OPR-DEP-01 / OPR-NEV-05: exactly eight fields force one unstored function."""
    calls = install_sdk(monkeypatch, reply())
    client = adapter.OperatorOpenAILLMClient(
        api_key="fixture-value",  # pragma: allowlist secret
        model="gpt-5.5",
        max_tokens=4096,
        effort="xhigh",
    )
    schema: dict[str, object] = {"type": "object"}
    for supplied, name, description, parameters in (
        (schema, "parse_intent", "Parse one operator command.", schema),
        (
            {},
            "answer_question",
            "Return one evidence-grounded answer.",
            {
                "type": "object",
                "properties": {"answer": {"type": "string"}},
                "required": ["answer"],
            },
        ),
    ):
        client.complete(system="system", user="user", tool_schema=supplied)
        assert calls[-1] == {
            "model": "gpt-5.5",
            "max_output_tokens": 4096,
            "reasoning": {"effort": "xhigh"},
            "instructions": "system",
            "input": "user",
            "tools": [
                {
                    "type": "function",
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                    "strict": False,
                }
            ],
            "tool_choice": {"type": "function", "name": name},
            "store": False,
        }
    assert len(calls) == 2


@pytest.mark.parametrize(
    ("cached", "uncached", "cache_read"), [(100, 300, 100), (500, 0, 400)]
)
def test_a2_function_call_and_usage(
    monkeypatch: pytest.MonkeyPatch, cached: int, uncached: int, cache_read: int
) -> None:
    """OPR-STA-03: select the first function call and clamp cached input."""
    install_sdk(monkeypatch, reply(cached=cached))
    client = adapter.OperatorOpenAILLMClient(
        api_key="fixture-value"  # pragma: allowlist secret
    )
    assert client.effort == "xhigh"
    assert json.loads(
        client.complete(system="s", user="u", tool_schema={"type": "object"})
    ) == {"outcome": "intent", "answer": "safe"}
    assert client.complete(system="s", user="u", tool_schema={}) == "safe"
    assert client.last_stop_reason == "completed"
    assert client.last_usage is not None
    assert client.last_usage.tokens_in == uncached
    assert client.last_usage.cache_read_tokens == cache_read
    assert client.last_usage.tokens_out == 25
    assert client.last_usage.cache_write_tokens == 0


def test_a3_cutoff_records_before_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    """OPR-FAIL-01 / OPR-STA-03: a cut-off's stop and tokens precede its raise."""
    install_sdk(
        monkeypatch,
        SimpleNamespace(
            status="incomplete",
            incomplete_details=SimpleNamespace(reason="max_output_tokens"),
            output=[SimpleNamespace(type="reasoning")],
            usage=SimpleNamespace(input_tokens=10, output_tokens=4096),
        ),
    )
    client = adapter.OperatorOpenAILLMClient(
        api_key="fixture-value"  # pragma: allowlist secret
    )
    with pytest.raises(LLMCompletionStoppedError) as error:
        client.complete(system="s", user="u", tool_schema={})
    assert error.value.provider == "openai"
    assert error.value.stop_reason == client.last_stop_reason == "max_output_tokens"
    assert client.last_usage is not None
    assert client.last_usage.tokens_in == 10
    assert client.last_usage.tokens_out == 4096
