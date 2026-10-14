"""Place an LLM candidate's model and effort into a declared probe body.

Agent: master
Role: let one vendor probe test each declared candidate exactly as it will run.
External I/O: none.

A probe declares ``candidate_paths``: where in its JSON body the model and the effort
go. The values travel to the probe in two reserved configuration keys, which no
environment name can spell, so a probe of a candidate sends that candidate's model
and effort and nothing else changes.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

MODEL_KEY = "llm:model"
EFFORT_KEY = "llm:effort"
_FIELDS = {"model": MODEL_KEY, "effort": EFFORT_KEY}

type CandidatePaths = dict[str, tuple[str, ...]]


def candidate_paths(value: object) -> CandidatePaths | None:
    """Validate a probe's ``candidate_paths``; None when it declares none."""
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != set(_FIELDS):
        raise ValueError("candidate_paths must name exactly 'model' and 'effort'")
    paths: CandidatePaths = {}
    for field, path in value.items():
        if (
            not isinstance(path, list)
            or not path
            or not all(isinstance(part, str) and part for part in path)
        ):
            raise ValueError(f"candidate_paths {field!r} must be a list of keys")
        paths[field] = tuple(path)
    return paths


def candidate_body(
    declared: object, paths: CandidatePaths, config: Mapping[str, str]
) -> bytes:
    """Serialise the declared body with the candidate's model and effort placed."""
    body = deepcopy(declared)
    if not isinstance(body, dict):
        raise ValueError("candidate_paths need a json_body object")
    for field, path in paths.items():
        node: dict[str, object] = body
        for part in path[:-1]:
            child = node.setdefault(part, {})
            if not isinstance(child, dict):
                raise ValueError(f"candidate path {'.'.join(path)} crosses a value")
            node = child
        node[path[-1]] = config[_FIELDS[field]]
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def with_candidate(
    config: Mapping[str, str], model: str, effort: str
) -> dict[str, str]:
    """Return the configuration a candidate's probe runs against."""
    return {**config, MODEL_KEY: model, EFFORT_KEY: effort}
