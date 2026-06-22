"""Grant-policy type and loader for the master bootstrap agent.

Agent: master
Role: define the grant-policy shape and load one from a pack-supplied JSON file.
      The master mechanism is domain-agnostic — it never names an agent type; the
      content (which types exist, what they may do) is pack data injected at boot.
External I/O: reads the grant-policy JSON file when load_grant_policy is called.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

# A grant policy maps an agent type to its capability grants. The master treats this
# as opaque data; the trading content lives in a pack file (orchestration/packs/
# trading_grants.json), loaded by path — never imported (ADR-0012, DL-12).
type GrantPolicy = Mapping[str, dict[str, object]]


def load_grant_policy(path: str) -> GrantPolicy:
    """Load a grant policy from JSON: a map of agent_type -> capability grants."""
    raw: object = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"grant policy at {path!r} must be a JSON object")
    policy: dict[str, dict[str, object]] = {}
    for key, value in raw.items():
        if not isinstance(value, dict):
            raise ValueError(
                f"grant policy entry {key!r} in {path!r} must be a JSON object"
            )
        policy[str(key)] = value
    return policy
