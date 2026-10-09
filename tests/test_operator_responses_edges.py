"""Responses refusal and content-filter cases.

Agent: kernel
Role: prove unusable function arguments and vendor stop metadata.
External I/O: none; fake SDK only.
"""

import json
from types import SimpleNamespace

import pytest
from tests.test_operator_responses import install_sdk

from kernel import llm_openai_operator as adapter


@pytest.mark.parametrize(
    "output",
    [
        [],
        [
            SimpleNamespace(
                type="message", content=[SimpleNamespace(type="refusal", refusal="no")]
            )
        ],
        [SimpleNamespace(type="function_call", arguments=None)],
        [SimpleNamespace(type="function_call", arguments="not json")],
        [SimpleNamespace(type="function_call", arguments="[]")],
        [SimpleNamespace(type="function_call", arguments=23)],
    ],
)
def test_a4_unusable_output_is_refused(
    monkeypatch: pytest.MonkeyPatch, output: list[object]
) -> None:
    """OPR-NEV-05 / OPR-FAIL-02: missing calls and non-object arguments refuse."""
    install_sdk(monkeypatch, SimpleNamespace(output=output))
    client = adapter.OperatorOpenAILLMClient(api_key="fixture-value")
    assert json.loads(
        client.complete(system="s", user="u", tool_schema={"type": "object"})
    ) == {"outcome": "refused", "reason": "model returned no tool result"}
    assert client.last_stop_reason == "unknown"
    assert client.last_usage is None


def test_a5_filtered_reply_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """OPR-FAIL-02 / OPR-STA-03: content filtering refuses with its own reason."""
    install_sdk(
        monkeypatch,
        SimpleNamespace(
            status="incomplete",
            incomplete_details=SimpleNamespace(reason="content_filter"),
            output=[],
        ),
    )
    client = adapter.OperatorOpenAILLMClient(api_key="fixture-value")
    assert json.loads(
        client.complete(system="s", user="u", tool_schema={"type": "object"})
    ) == {"outcome": "refused", "reason": "model returned no tool result"}
    assert client.last_stop_reason == "content_filter"


@pytest.mark.parametrize("output", [None, [SimpleNamespace(type="function_call")]])
def test_missing_arguments_and_output(
    monkeypatch: pytest.MonkeyPatch, output: object
) -> None:
    """OPR-NEV-05: missing SDK fields remain a refusal, not an exception."""
    install_sdk(monkeypatch, SimpleNamespace(output=output))
    client = adapter.OperatorOpenAILLMClient(api_key="fixture-value")
    assert (
        json.loads(
            client.complete(system="s", user="u", tool_schema={"type": "object"})
        )["outcome"]
        == "refused"
    )
