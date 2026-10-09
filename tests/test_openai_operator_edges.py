"""OpenAI operator unusable-response and configuration guards.

Agent: kernel
Role: prove refusal, length accounting and lazy SDK failure paths.
External I/O: none; fake SDK completions only.
"""

import json
from types import SimpleNamespace

import pytest

from kernel import llm_openai_operator as adapter
from kernel.llm import LLMCompletionStoppedError
from kernel.llm_openai import ConfigurationError

TEST_CREDENTIAL = "fixture-value"


def _sdk(monkeypatch: pytest.MonkeyPatch, response: object) -> None:
    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **kwargs: response)
        )
    )
    monkeypatch.setattr(
        adapter.importlib,
        "import_module",
        lambda name: SimpleNamespace(OpenAI=lambda **kwargs: client),
    )


@pytest.mark.parametrize("raw", [None, "not json", "[]", 23])
def test_b3_unusable_tool_reply_is_refused(
    monkeypatch: pytest.MonkeyPatch, raw: object
) -> None:
    """OPR-NEV-05 / OPR-FAIL-02: absent or non-object tool arguments refuse."""
    calls = (
        []
        if raw is None
        else [SimpleNamespace(function=SimpleNamespace(arguments=raw))]
    )
    _sdk(
        monkeypatch,
        SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=calls))]
        ),
    )
    client = adapter.OperatorOpenAILLMClient(api_key=TEST_CREDENTIAL)
    assert json.loads(
        client.complete(system="s", user="u", tool_schema={"type": "object"})
    ) == {"outcome": "refused", "reason": "model returned no tool result"}
    assert client.last_stop_reason == "unknown"
    assert client.last_usage is None


def test_b3_length_raises_after_recording_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OPR-FAIL-01 / OPR-STA-03: a billed length stop remains visible and fails."""
    _sdk(
        monkeypatch,
        SimpleNamespace(
            choices=[SimpleNamespace(finish_reason="length")],
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=4096),
        ),
    )
    client = adapter.OperatorOpenAILLMClient(api_key=TEST_CREDENTIAL)
    with pytest.raises(LLMCompletionStoppedError) as error:
        client.complete(system="s", user="u", tool_schema={})
    assert error.value.provider == "openai"
    assert error.value.stop_reason == client.last_stop_reason == "length"
    assert client.last_usage is not None
    assert client.last_usage.tokens_out == 4096


def test_optional_sdk_is_lazy_and_missing_key_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OPR-SEC-01 / OPR-DEP-01: no selected key or optional SDK fails construction."""
    _sdk(monkeypatch, object())
    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY"):
        adapter.OperatorOpenAILLMClient(api_key=None)

    def missing(name: str) -> object:
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(adapter.importlib, "import_module", missing)
    with pytest.raises(ConfigurationError, match="package is not installed"):
        adapter.OperatorOpenAILLMClient(api_key=TEST_CREDENTIAL)


def test_transport_failure_clears_old_accounting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OPR-STA-03 / OPR-FAIL-01: a failed new call cannot reuse previous tokens."""

    def broken(**kwargs: object) -> object:
        raise TimeoutError("fixture timeout")

    _sdk(monkeypatch, object())
    client = adapter.OperatorOpenAILLMClient(api_key=TEST_CREDENTIAL)
    client.last_stop_reason = "stop"
    monkeypatch.setattr(client._client.chat.completions, "create", broken)
    with pytest.raises(TimeoutError):
        client.complete(system="s", user="u", tool_schema={})
    assert client.last_stop_reason == "unknown"
    assert client.last_usage is None
