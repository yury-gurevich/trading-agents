"""The batch harness offers every round's system prompt to the cache.

Agent: tooling
Role: pin the wire shape the sweep submits, because the one thing that went
      unmeasured last time was whether the marker was sent at all.
External I/O: none — nothing is submitted; only the request body is built.

🚨 S173 Part B's funded round ran 2,957 calls with `cache_read` at **0**
throughout (DL-160). The prompts were byte-identical within each round, so the
discount was available the whole time and simply never requested. A shape this
cheap to get wrong is worth a test that reads the dict.
"""

from __future__ import annotations

from scripts.deliberation_replay_batch import _cached_system, _wire

from orchestration.replay_types import BatchRequest


def _request() -> BatchRequest:
    return BatchRequest(
        custom_id="pm-run-1:USB:challenger:r2",
        model="claude-opus-5",
        effort="high",
        max_tokens=4096,
        system="CHALLENGER ROLE PROMPT",
        user="DECISION UNDER TEST: buy USB",
    )


def test_the_submitted_system_block_carries_a_cache_marker() -> None:
    params = _wire(_request())["params"]

    assert params["system"] == [  # type: ignore[index]
        {
            "type": "text",
            "text": "CHALLENGER ROLE PROMPT",
            "cache_control": {"type": "ephemeral", "ttl": "1h"},
        }
    ]


def test_the_batch_path_uses_the_one_hour_ttl_not_the_default() -> None:
    """A batch is processed over minutes to hours, not seconds.

    A 5-minute entry would expire mid-round and be rewritten repeatedly, paying
    the write premium again for few reads. The live nightly adapter makes the
    opposite choice because its requests are seconds apart — the asymmetry is
    the decision, so both halves are pinned.
    """
    (block,) = _cached_system("ROLE PROMPT")

    assert block["cache_control"] == {"type": "ephemeral", "ttl": "1h"}


def test_caching_does_not_disturb_the_rest_of_the_request() -> None:
    """custom_id keying and the arm's own knobs must survive the change.

    Batch results arrive in any order and are reassembled by `custom_id`; an
    edit here that dropped or reshaped it would silently scramble a paid round.
    """
    wired = _wire(_request())
    params = wired["params"]

    assert wired["custom_id"] == "pm-run-1:USB:challenger:r2"
    assert params["model"] == "claude-opus-5"  # type: ignore[index]
    assert params["max_tokens"] == 4096  # type: ignore[index]
    assert params["output_config"] == {"effort": "high"}  # type: ignore[index]
    assert params["messages"] == [  # type: ignore[index]
        {"role": "user", "content": "DECISION UNDER TEST: buy USB"}
    ]
