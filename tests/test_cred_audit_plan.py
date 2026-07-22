"""Tests for the pure credential-delivery audit logic.

Agent: tooling
Role: pin the verdicts the fleet credential audit must reach.
External I/O: none.
"""

from __future__ import annotations

import json

from scripts.cred_audit_plan import (
    CROSS_WIRED,
    DEGRADED,
    FLEET_TARGETS,
    MISSING,
    REQUIRED_PRIVILEGES,
    SCOPED,
    SHARED,
    UNREACHABLE,
    audit_json,
    classify,
    container_name,
    expected_role,
    role_of_dsn,
    summarize,
)

ALL_PRIVILEGES = REQUIRED_PRIVILEGES


def test_fleet_is_the_fourteen_delivery_targets() -> None:
    """The audit covers every deployed target and excludes the ops-only role."""
    assert len(FLEET_TARGETS) == 14
    assert "ops" not in FLEET_TARGETS
    assert {"master", "dispatcher", "analyst"} <= set(FLEET_TARGETS)


def test_container_name_maps_underscores_and_the_job() -> None:
    """Container Apps names use dashes; the dispatcher is a differently named job."""
    assert container_name("portfolio_manager") == "portfolio-manager"
    assert container_name("dispatcher") == "dispatcher-cron"
    assert container_name("analyst") == "analyst"


def test_role_of_dsn_returns_user_and_never_raises() -> None:
    """A DSN yields its username only; malformed input yields empty, not an error."""
    fake = "postgresql://ta_analyst:pw@host/db"  # pragma: allowlist secret
    assert role_of_dsn(fake) == "ta_analyst"
    assert role_of_dsn("") == ""
    assert role_of_dsn("not-a-dsn") == ""


def test_scoped_when_role_matches_and_all_privileges_granted() -> None:
    """The healthy case: own role, reachable, full spine grants."""
    audit = classify("analyst", "ta_analyst", reachable=True, privileges=ALL_PRIVILEGES)
    assert audit.verdict == SCOPED
    assert audit.missing_privileges == ()


def test_shared_admin_dsn_is_the_failure_this_audit_exists_for() -> None:
    """An unrecognised role means the target still holds a shared credential."""
    audit = classify(
        "analyst", "neondb_owner", reachable=True, privileges=ALL_PRIVILEGES
    )
    assert audit.verdict == SHARED


def test_another_targets_role_is_cross_wired_not_shared() -> None:
    """Holding a *different* agent's role is a distinct, worse defect than shared."""
    audit = classify(
        "analyst", "ta_execution", reachable=True, privileges=ALL_PRIVILEGES
    )
    assert audit.verdict == CROSS_WIRED


def test_missing_when_no_dsn_delivered() -> None:
    """No delivered secret is reported as missing, not as shared."""
    assert classify("analyst", "", reachable=False).verdict == MISSING


def test_unreachable_when_right_role_cannot_connect() -> None:
    """A correct role that will not connect fails rather than passing quietly."""
    audit = classify("analyst", "ta_analyst", reachable=False, note="OperationalError")
    assert audit.verdict == UNREACHABLE
    assert audit.note == "OperationalError"


def test_degraded_lists_the_missing_privileges() -> None:
    """A role short of the spine grants is degraded and names what it lacks."""
    granted = tuple(p for p in ALL_PRIVILEGES if p != "edges:INSERT")
    audit = classify("analyst", "ta_analyst", reachable=True, privileges=granted)
    assert audit.verdict == DEGRADED
    assert audit.missing_privileges == ("edges:INSERT",)


def test_summarize_flags_failing_targets_and_overall_state() -> None:
    """The summary is not ok while any target is off its scoped credential."""
    good = classify("analyst", "ta_analyst", reachable=True, privileges=ALL_PRIVILEGES)
    bad = classify("scanner", "neondb_owner", reachable=True, privileges=ALL_PRIVILEGES)
    result = summarize((good, bad))
    assert result["ok"] is False
    assert result["failing"] == ["scanner"]
    assert result["verdicts"] == {SCOPED: 1, SHARED: 1}


def test_summarize_of_all_scoped_is_ok() -> None:
    """A wholly scoped fleet reports ok with no failing targets."""
    audits = tuple(
        classify(t, expected_role(t), reachable=True, privileges=ALL_PRIVILEGES)
        for t in FLEET_TARGETS
    )
    result = summarize(audits)
    assert result["ok"] is True
    assert result["failing"] == []
    assert result["targets"] == 14


def test_empty_audit_is_not_ok() -> None:
    """An audit that examined nothing must not report success."""
    assert summarize(())["ok"] is False


def test_audit_json_is_parseable_and_carries_no_credential() -> None:
    """Rendered output holds role names and verdicts only."""
    audit = classify("analyst", "ta_analyst", reachable=True, privileges=ALL_PRIVILEGES)
    rendered = audit_json((audit,))
    assert "ta_analyst" in rendered
    assert "password" not in rendered.lower()
    parsed = json.loads(rendered)
    assert parsed["summary"]["ok"] is True
    assert parsed["targets"][0]["verdict"] == SCOPED
