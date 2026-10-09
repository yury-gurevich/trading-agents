"""Read and poll existing fleet proof facts for a provider switch.

Agent: tooling
Role: require a fresh passing fleet check and selected-vendor changed-app activations.
External I/O: injected graph reads, clock and sleep only; no graph writes.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from scripts.switch_llm_config import LlmPack

    from kernel import GraphStore


def _fresh(value: object, since: datetime) -> bool:
    if not isinstance(value, str):
        return False
    try:
        at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return at.tzinfo is not None and at.astimezone(UTC) >= since


def missing_terms(
    graph: GraphStore, pack: LlmPack, changed: list[str], since: datetime
) -> list[str]:
    """Name missing proof conjuncts; a partial activation never counts."""
    missing: list[str] = []
    checks = [
        node
        for node in graph.list_nodes("FleetPreflight")
        if _fresh(node.props.get("checked_at"), since)
    ]
    if not checks:
        missing.append("no FleetPreflight since the start")
    elif not any(node.props.get("passed") is True for node in checks):
        missing.append("FleetPreflight passed is false")
    instances = graph.list_nodes("AgentInstance")
    for app in changed:
        if app == "master":
            continue
        candidates = [
            node.props
            for node in instances
            if node.props.get("agent_type") == app
            and node.props.get("state") == "active"
            and _fresh(node.props.get("started_at"), since)
        ]
        if not candidates:
            missing.append(f"{app}: no active AgentInstance since the start")
        elif not any(_valid_activation(props, pack, app) for props in candidates):
            missing.append(
                f"{app}: vendor probe not passed or other vendor probe declared"
            )
    return missing


def _valid_activation(props: Mapping[str, object], pack: LlmPack, app: str) -> bool:
    passed = props.get("credential_tests_passed")
    declared = props.get("credential_tests_declared")
    if not isinstance(passed, (tuple, list)) or not isinstance(declared, (tuple, list)):
        return False
    required = pack.probes[app][pack.provider]
    other = frozenset(
        name
        for vendor, names in pack.probes[app].items()
        if vendor != pack.provider
        for name in names
    )
    return required.issubset(passed) and not other.intersection(declared)


def wait_for_proof(
    graph: GraphStore,
    pack: LlmPack,
    changed: list[str],
    since: datetime,
    *,
    clock: Callable[[], datetime],
    sleep: Callable[[float], None],
    poll_seconds: float,
    wait_seconds: float,
    emit: Callable[[str], None],
) -> int:
    """Poll up to the bounded deadline; name every term still missing on failure."""
    deadline = since + timedelta(seconds=wait_seconds)
    while True:
        missing = missing_terms(graph, pack, changed, since)
        if not missing:
            emit("FleetPreflight passed; changed-app activations proven")
            return 0
        remaining = (deadline - clock()).total_seconds()
        if remaining <= 0:
            for term in missing:
                emit(f"proof failed: {term}")
            return 1
        sleep(min(poll_seconds, remaining))
