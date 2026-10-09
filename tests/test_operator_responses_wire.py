"""Captured operator request and reply replayed through the installed SDK.

Agent: kernel
Role: compare actual SDK serialization with the measured Responses wire body.
External I/O: reads one sanitized fixture; HTTP uses an in-memory mock transport.
"""

import json
from pathlib import Path

import httpx

from kernel.llm_openai_operator import OperatorOpenAILLMClient


def test_a8_captured_wire_replay() -> None:
    """OPR-DEP-01 / OPR-STA-03: the real SDK sends and reads the captured shape."""
    import openai

    fixture = json.loads(
        Path("tests/fixtures/openai_responses_forced_function.json").read_text(
            encoding="utf-8"
        )
    )
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.path == "/v1/responses"
        assert json.loads(request.content) == fixture["request"]
        return httpx.Response(200, json=fixture["reply"])

    client = OperatorOpenAILLMClient(
        api_key="fixture-value",  # pragma: allowlist secret
        model=fixture["request"]["model"],
        max_tokens=fixture["max_tokens"],
        effort=fixture["effort"],
    )
    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as transport,
        openai.OpenAI(
            api_key="fixture-value",  # pragma: allowlist secret
            max_retries=0,
            http_client=transport,
        ) as sdk,
    ):
        client._client = sdk
        returned = client.complete(
            system=fixture["system"],
            user=fixture["user"],
            tool_schema=fixture["tool_schema"],
        )
    assert json.loads(returned) == fixture["returned"]
    assert len(requests) == 1
    assert client.last_stop_reason == "completed"
    assert client.last_usage is not None
    assert client.last_usage.tokens_in == 286
    assert client.last_usage.tokens_out == 187
    assert client.last_usage.cache_read_tokens == 0
