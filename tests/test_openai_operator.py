"""OpenAI operator forced-function wire contract.

Agent: kernel
Role: prove structured intent and explanation calls without a model connection.
External I/O: none; the SDK is injected.
"""

import json
from types import SimpleNamespace

import pytest

TEST_CREDENTIAL = "fixture-value"


def test_b2_operator_forces_one_named_function(monkeypatch: pytest.MonkeyPatch) -> None:
    """OPR-DEP-01 / OPR-NEV-05: one forced function preserves arguments and effort."""
    import kernel.llm_openai_operator as adapter

    calls: list[dict[str, object]] = []

    def create(**kwargs: object) -> object:
        calls.append(kwargs)
        return SimpleNamespace(
            status="completed",
            output=[
                SimpleNamespace(
                    type="function_call",
                    arguments='{"answer":"safe answer","outcome":"intent"}',
                )
            ],
            usage=SimpleNamespace(
                input_tokens=10,
                output_tokens=3,
                input_tokens_details=SimpleNamespace(cached_tokens=2),
            ),
        )

    monkeypatch.setattr(
        adapter.importlib,
        "import_module",
        lambda name: SimpleNamespace(
            OpenAI=lambda **kwargs: SimpleNamespace(
                responses=SimpleNamespace(create=create)
            )
        ),
    )
    client = adapter.OperatorOpenAILLMClient(
        api_key=TEST_CREDENTIAL, max_tokens=4096, effort="max"
    )
    schema: dict[str, object] = {
        "type": "object",
        "properties": {"outcome": {"type": "string"}},
    }
    assert (
        json.loads(client.complete(system="system", user="status", tool_schema=schema))[
            "outcome"
        ]
        == "intent"
    )
    assert (
        client.complete(system="system", user="explain", tool_schema={})
        == "safe answer"
    )
    for call, name in zip(calls, ("parse_intent", "answer_question"), strict=True):
        assert call["tool_choice"] == {"type": "function", "name": name}
        assert len(call["tools"]) == 1
        assert call["tools"][0]["description"]
        assert call["tools"][0]["strict"] is False
        assert call["store"] is False
        assert call["max_output_tokens"] == 4096
        assert call["reasoning"] == {"effort": "max"}
    assert client.last_stop_reason == "completed"
    assert client.last_usage is not None
    assert client.last_usage.tokens_in == 8
    assert client.last_usage.tokens_out == 3
    assert client.last_usage.cache_read_tokens == 2
