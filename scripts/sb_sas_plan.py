"""Pure planning helpers for per-target Service Bus SAS grants.

Agent: tooling
Role: derive topic authorization grants from served-agent routes and source topics.
External I/O: none in the planner; the CLI reads local source and prints no secrets.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.pg_role_plan import AGENTS as ROLE_TARGETS  # noqa: E402
from scripts.pg_role_plan import normalize_agent  # noqa: E402
from scripts.sb_sas_scan import (  # noqa: E402
    SourceText,
    owner_for_path,
    scan_source,
    source_paths,
)

from kernel.serve_transport import SERVED_AGENT_TYPES, request_topic  # noqa: E402

SERVICEBUS_TARGETS = tuple(agent for agent in ROLE_TARGETS if agent != "ops")
DEFAULT_REPLY_TOPIC_SUFFIX = ".reply"
RULE_CAP_PER_TOPIC = 12
_TOPIC_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True, order=True)
class SasGrant:
    """One target's rights on one Service Bus topic."""

    target: str
    topic: str
    rights: tuple[str, ...]


def plan_from_repo(root: Path | str = ".") -> tuple[SasGrant, ...]:
    """Read source files under *root* and derive the Service Bus SAS plan."""
    base = Path(root)
    sources = tuple(
        SourceText(str(path.relative_to(base)), path.read_text(encoding="utf-8"))
        for path in source_paths(base)
    )
    return plan_from_sources(sources)


def plan_from_sources(sources: tuple[SourceText, ...]) -> tuple[SasGrant, ...]:
    """Derive per-target topic grants from source text without live I/O."""
    grants: dict[tuple[str, str], set[str]] = defaultdict(set)
    for served in SERVED_AGENT_TYPES:
        _add(grants, served, request_topic(served), "Listen")
    for source in sources:
        owner = owner_for_path(source.path)
        if owner is None:
            continue
        scan = scan_source(source)
        for topic, right in scan.topic_events:
            _add(grants, owner, topic, right)
        for sender, recipient in scan.agent_messages:
            if recipient not in SERVED_AGENT_TYPES:
                continue
            caller = _sender_target(sender, owner)
            reply_topic = f"{sender}{DEFAULT_REPLY_TOPIC_SUFFIX}"
            _add(grants, caller, request_topic(recipient), "Send")
            _add(grants, caller, reply_topic, "Listen")
            _add(grants, recipient, reply_topic, "Send")
    return tuple(
        SasGrant(target, topic, _ordered_rights(rights))
        for (target, topic), rights in sorted(grants.items())
    )


def grants_by_target(grants: tuple[SasGrant, ...]) -> dict[str, tuple[SasGrant, ...]]:
    """Group a grant plan by target identity."""
    grouped: dict[str, list[SasGrant]] = defaultdict(list)
    for grant in grants:
        grouped[grant.target].append(grant)
    return {target: tuple(items) for target, items in sorted(grouped.items())}


def cap_violations(
    grants: tuple[SasGrant, ...], *, rule_cap: int = RULE_CAP_PER_TOPIC
) -> dict[str, int]:
    """Return topics whose distinct target rules would exceed the Azure cap."""
    by_topic: dict[str, set[str]] = defaultdict(set)
    for grant in grants:
        by_topic[grant.topic].add(grant.target)
    return {
        topic: len(targets)
        for topic, targets in sorted(by_topic.items())
        if len(targets) > rule_cap
    }


def authorization_rule_name(target: str) -> str:
    """Return the topic-level authorization-rule name for a target."""
    return f"ta-{_normalize_target(target).replace('_', '-')}"


def target_secret_name(target: str) -> str:
    """Return the primary per-target Key Vault secret name."""
    return f"servicebus-connection-string-{_normalize_target(target).replace('_', '-')}"


def target_bundle_secret_name(target: str) -> str:
    """Return the per-target Key Vault secret holding all scoped topic strings."""
    return (
        f"servicebus-connection-strings-{_normalize_target(target).replace('_', '-')}"
    )


def primary_grant_for_target(
    target: str, grants: tuple[SasGrant, ...]
) -> SasGrant | None:
    """Pick the target's single-string compatibility grant, if any."""
    normalized = _normalize_target(target)
    owned = tuple(grant for grant in grants if grant.target == normalized)
    own_request = request_topic(normalized) if normalized in SERVED_AGENT_TYPES else ""
    for grant in owned:
        if grant.topic == own_request and "Listen" in grant.rights:
            return grant
    return owned[0] if owned else None


def plan_json(grants: tuple[SasGrant, ...]) -> str:
    """Return printable, non-secret JSON for the derived plan."""
    return json.dumps(
        {
            "rule_cap_per_topic": RULE_CAP_PER_TOPIC,
            "targets": {
                target: [
                    {"topic": grant.topic, "rights": list(grant.rights)}
                    for grant in items
                ]
                for target, items in grants_by_target(grants).items()
            },
            "cap_violations": cap_violations(grants),
        },
        indent=2,
        sort_keys=True,
    )


def _add(
    grants: dict[tuple[str, str], set[str]], target: str, topic: str, right: str
) -> None:
    normalized = _normalize_target(target)
    if not _TOPIC_RE.fullmatch(topic):
        raise ValueError(f"unsafe Service Bus topic: {topic}")
    grants[(normalized, topic)].add(right)


def _normalize_target(raw: str) -> str:
    target = normalize_agent(raw)
    if target == "ops":
        raise ValueError("ops is not a Service Bus fleet target")
    return target


def _ordered_rights(rights: set[str]) -> tuple[str, ...]:
    return tuple(right for right in ("Listen", "Send") if right in rights)


def _sender_target(sender: str, owner: str) -> str:
    if sender == "orchestration":
        return "dispatcher"
    return sender if sender in SERVICEBUS_TARGETS else owner


def main() -> int:
    """Print the non-secret SAS plan for review."""
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    print(plan_json(plan_from_repo(root)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
