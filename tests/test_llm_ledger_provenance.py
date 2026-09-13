"""LLMCall prompt-provenance tests.

Agent: kernel
Role: prove the ledger records which renderer produced a prompt and hashes the
      system prompt as well as the user prompt.
External I/O: none.
"""

from __future__ import annotations

from kernel import InMemoryGraphStore
from kernel.llm_ledger import digest_text, record_llm_call, write_llm_call
from kernel.prompt_recipe import RECIPE_UNKNOWN

_KEY = "llmcall:deliberator-opponent:run:USB:challenger:r1"


def _record(**kwargs: object) -> dict[str, object]:
    graph = InMemoryGraphStore()
    with record_llm_call(
        graph,
        calling_agent="deliberator-opponent",
        correlation_id="run:USB:challenger:r1",
        model="claude-opus-5",
        prompt="DECISION UNDER TEST: buy USB",
        **kwargs,  # type: ignore[arg-type]
    ) as call:
        call.set_response("an answer")
    node = graph.get_node("LLMCall", _KEY)
    assert node is not None
    return dict(node.props)


def test_the_system_prompt_is_hashed_alongside_the_user_prompt() -> None:
    """DLIB-IDM-02 / DRIFT-056: the recorded bound now covers both halves."""
    props = _record(system_prompt="CHALLENGER ROLE PROMPT")

    assert props["system_prompt_hash"] == digest_text("CHALLENGER ROLE PROMPT")
    assert props["prompt_hash"] == digest_text("DECISION UNDER TEST: buy USB")


def test_two_calls_differing_only_in_system_prompt_are_distinguishable() -> None:
    """🪤 DRIFT-056 in one assertion — this was the measured blind spot.

    Before S200 these two rows were byte-identical, so a role-prompt experiment
    was invisible in the ledger: `prompt_hash` covered the user string only.
    """
    defender = _record(system_prompt="DEFENDER ROLE PROMPT")
    challenger = _record(system_prompt="CHALLENGER ROLE PROMPT")

    assert defender["prompt_hash"] == challenger["prompt_hash"]
    assert defender["system_prompt_hash"] != challenger["system_prompt_hash"]


def test_the_system_prompt_text_is_never_stored() -> None:
    """DLIB-OUT-05: compact audit metadata only — a hash, never the payload."""
    payload = "CHALLENGER ROLE PROMPT with operational detail"
    props = _record(system_prompt=payload)

    assert payload not in "".join(str(value) for value in props.values())


def test_the_renderer_that_produced_the_prompt_is_recorded() -> None:
    """Item 44: replayability becomes knowable without replaying the row."""
    props = _record(prompt_recipe_hash="abc123")

    assert props["prompt_recipe_hash"] == "abc123"


def test_an_unrecorded_renderer_reads_as_unknown_not_as_this_one() -> None:
    """🪤 The default must not silently claim the current renderer.

    Every row written before S200 has no recipe at all. If the default were the
    running process's digest, those rows would assert they were produced by
    today's code -- the exact false claim the field exists to prevent, and worse
    than the absence it replaces.
    """
    assert _record()["prompt_recipe_hash"] == RECIPE_UNKNOWN
    assert _record()["system_prompt_hash"] == digest_text("")

    graph = InMemoryGraphStore()
    node = write_llm_call(
        graph,
        calling_agent="operator",
        correlation_id="corr",
        model="claude-opus-5",
        prompt_hash="p",
        response_hash="r",
        tokens_in=1,
        tokens_out=1,
        latency_ms=1,
    )
    assert node.props["prompt_recipe_hash"] == RECIPE_UNKNOWN
