"""A12-A13: a candidate's probe is the request the role will send.

Agent: master
Role: prove body substitution without changing the declared body or headers.
External I/O: none; HTTP transport records the request only.
"""

import json

import pytest

from agents.master.credential_probe_candidate import (
    candidate_body,
    candidate_paths,
    with_candidate,
)
from agents.master.credential_probes import HttpProbeRequest, parse_credential_tests

PATHS = {"model": ["model"], "effort": ["output_config", "effort"]}


def test_a12_candidate_probe_carries_own_model_and_effort() -> None:
    """MST-OUT-05: copied candidate body, JSON type and unchanged legacy bytes."""
    declared = {
        "max_tokens": 1,
        "model": "declared",
        "output_config": {"effort": "low"},
    }
    original = json.dumps(declared, sort_keys=True, separators=(",", ":")).encode()
    paths = candidate_paths(PATHS)
    assert paths is not None
    config = with_candidate({"KEY": "fixture"}, "claude-opus-5", "max")
    expected = (
        b'{"max_tokens":1,"model":"claude-opus-5","output_config":{"effort":"max"}}'
    )
    assert candidate_body(declared, paths, config) == expected
    assert (
        json.dumps(declared, sort_keys=True, separators=(",", ":")).encode() == original
    )
    seen: list[HttpProbeRequest] = []

    def transport(request: HttpProbeRequest) -> int:
        seen.append(request)
        return 200

    (probe,) = parse_credential_tests(
        json.dumps(
            {
                "role": [
                    {
                        "name": "anthropic",
                        "kind": "http_status",
                        "method": "POST",
                        "url": "https://example.invalid/messages",
                        "json_body": declared,
                        "candidate_paths": PATHS,
                    }
                ]
            }
        ),
        http_transport=transport,
    )
    assert probe.takes_candidate
    probe.run(config)
    probe.run({})
    assert seen[0].body == expected
    assert seen[0].headers == {"content-type": "application/json"}
    assert seen[1].body == original
    assert candidate_paths(None) is None


@pytest.mark.parametrize(
    "value",
    [
        [],
        {"model": ["model"]},
        PATHS | {"extra": ["extra"]},
        PATHS | {"model": "model"},
        PATHS | {"model": []},
        PATHS | {"model": [""]},
        PATHS | {"effort": [1]},
    ],
)
def test_a13_malformed_candidate_paths_are_refused(value: object) -> None:
    """MST-NEV-08: exactly two nonempty key-list paths are required."""
    with pytest.raises(ValueError, match="candidate_paths"):
        candidate_paths(value)


def test_a13_missing_body_and_scalar_paths_are_refused() -> None:
    """MST-NEV-08: a path cannot be used without an object or through a scalar."""
    paths = candidate_paths(PATHS)
    assert paths is not None
    config = with_candidate({}, "claude-opus-5", "max")
    for body, cause in (
        ([], "json_body object"),
        ({"output_config": 1}, "crosses a value"),
    ):
        with pytest.raises(ValueError, match=cause):
            candidate_body(body, paths, config)
    entry = {
        "name": "candidate",
        "kind": "http_status",
        "url": "https://example.invalid",
        "candidate_paths": PATHS,
    }
    with pytest.raises(ValueError, match="need a json_body"):
        parse_credential_tests(json.dumps({"role": [entry]}))
    paths = candidate_paths({"model": ["nested", "model"], "effort": ["effort"]})
    assert paths is not None
    assert json.loads(candidate_body({}, paths, config)) == {
        "nested": {"model": "claude-opus-5"},
        "effort": "max",
    }
