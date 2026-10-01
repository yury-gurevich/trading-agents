"""Where the two health counts come from (S251, DRIFT-076, DL-260).

Agent: supervisor
Role: keep the sources apart: open incidents are live Fault incidents and never Flags;
      pending human flags are unresolved critical Flags and never Faults.
External I/O: none (in-memory graph).
"""

from __future__ import annotations

from agents.supervisor.domain.health import compute_health
from kernel import InMemoryGraphStore


def test_open_incidents_count_faults_and_pending_flags_count_critical_flags() -> None:
    """SUP-OBS-02 (DRIFT-076): a critical Flag alone is a pending human flag and no
    incident; a live error Fault alone is an incident and no pending flag; a resolved
    critical Flag and a warn Flag count as neither."""
    flags_only = InMemoryGraphStore()
    flags_only.merge_node(
        "Flag", "flag:risk:critical", {"subject_ref": "risk", "severity": "critical"}
    )
    flags_only.merge_node(
        "Flag", "flag:noise:warn", {"subject_ref": "noise", "severity": "warn"}
    )
    flags_only.merge_node(
        "Flag", "flag:done:critical", {"subject_ref": "done", "severity": "critical"}
    )
    flags_only.merge_node(
        "FlagResolution",
        "resolution:flag:done:critical",
        {"subject_ref": "done", "severity": "critical"},
    )
    faults_only = InMemoryGraphStore()
    faults_only.merge_node(
        "Fault", "fault:live", {"status": "pending", "severity": "error"}
    )

    from_flags = compute_health(flags_only, None)
    from_faults = compute_health(faults_only, None)

    assert (from_flags["open_incidents"], from_flags["pending_human_flags"]) == (0, 1)
    assert (from_faults["open_incidents"], from_faults["pending_human_flags"]) == (1, 0)
