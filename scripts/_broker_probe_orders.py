"""Broker orders placed by probes, which no pipeline Fill is expected for.

Agent: tooling
Role: one probe allowlist for the broker/graph audit and the orphan Fill repair.
External I/O: none.
"""

from __future__ import annotations

# A probe order is placed by hand to measure the broker, so it has no ExecutionRun
# and never gets a pipeline Fill. The audit names it instead of failing it, and the
# repair must never adopt it: both read this one list. Name a new probe
# `probe-<sprint>-...` and it needs no row here; the other rows are probes already
# at the broker under other names (measured 2026-09-26, the audit failed all three).
PROBE_ORDER_PREFIXES = {
    "dep-broker-probe-": "dependency probe order; no pipeline Fill expected",
    "probe-": "planner live probe order; no pipeline Fill expected",
    "stop:probe-": "S164 broker-stop live probe order; no pipeline Fill expected",
    "replace-probe-": "S230 stop-replace probe order; no pipeline Fill expected",
    "s230-livecheck-": "S230 live replace check order; no pipeline Fill expected",
}


def probe_order_reason(client_order_id: str) -> str | None:
    """Return why a probe order needs no pipeline Fill, or None for any other."""
    for prefix, reason in PROBE_ORDER_PREFIXES.items():
        if client_order_id.startswith(prefix):
            return reason
    return None
