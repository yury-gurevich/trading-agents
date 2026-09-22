from __future__ import annotations

import json

import pytest


def _rules():
    try:
        from scripts.dependency_audit_rules import evaluate, findings_of
    except ModuleNotFoundError as exc:
        pytest.fail(f"dependency audit rules are missing: {exc}")
    return evaluate, findings_of


def _baseline():
    try:
        from scripts.dependency_audit_baseline import ACCEPTED, AcceptedAdvisory
    except ModuleNotFoundError as exc:
        pytest.fail(f"dependency audit baseline is missing: {exc}")
    return ACCEPTED, AcceptedAdvisory


def _report(*vulns, name="diskcache", version="5.6.3"):
    return {"dependencies": [{"name": name, "version": version, "vulns": list(vulns)}]}


def _vuln(vuln_id="PYSEC-2026-2447", *, aliases=(), fix_versions=()):
    return {
        "id": vuln_id,
        "aliases": list(aliases),
        "fix_versions": list(fix_versions),
    }


def _accepted(**overrides):
    _, advisory = _baseline()
    fields = {
        "vuln_id": "PYSEC-2026-2447",
        "package": "diskcache",
        "aliases": ("GHSA-w8v5-vhqr-4h9v",),
        "decision": "DL-184",
        "reason": "no fix release exists",
        "retire_when": "diskcache publishes a fixed release",
        "reachable_only_via_extra": "optimizer",
    }
    return advisory(**{**fields, **overrides})


_CLEAN_DOCKERFILES = {"agents/scanner/Dockerfile": "RUN uv sync --extra runtime\n"}


def test_an_unaccepted_vulnerability_fails_the_gate():
    evaluate, _ = _rules()

    errors, notes = evaluate(
        _report(_vuln("PYSEC-2099-0001"), name="requests", version="2.0.0"),
        _CLEAN_DOCKERFILES,
        accepted=(),
    )

    assert notes == []
    assert errors == [
        "requests 2.0.0: PYSEC-2099-0001 is not accepted (fix versions: none)"
    ]


def test_an_accepted_advisory_passes_and_states_its_premises():
    evaluate, _ = _rules()

    errors, notes = evaluate(
        _report(_vuln()), _CLEAN_DOCKERFILES, accepted=(_accepted(),)
    )

    assert errors == []
    assert len(notes) == 1
    assert "PYSEC-2026-2447" in notes[0]
    assert "diskcache 5.6.3" in notes[0]
    assert "installed by 0 of 1 Dockerfiles" in notes[0]
    assert "DL-184" in notes[0]
    assert "retire when" in notes[0]


def test_a_shipped_fix_retires_the_acceptance():
    evaluate, _ = _rules()

    errors, notes = evaluate(
        _report(_vuln(fix_versions=("5.6.4",))),
        _CLEAN_DOCKERFILES,
        accepted=(_accepted(),),
    )

    assert notes == []
    assert len(errors) == 1
    assert "a fix has shipped (5.6.4)" in errors[0]
    assert "scripts/dependency_audit_baseline.py" in errors[0]


def test_an_advisory_that_stopped_being_reported_is_a_stale_acceptance():
    evaluate, _ = _rules()

    errors, notes = evaluate({"dependencies": []}, {}, accepted=(_accepted(),))

    assert notes == []
    assert len(errors) == 1
    assert "accepted but no longer reported" in errors[0]


def test_installing_the_extra_voids_the_unreachability_premise():
    evaluate, _ = _rules()

    errors, notes = evaluate(
        _report(_vuln()),
        {
            "agents/curator/Dockerfile": (
                "RUN uv sync --extra runtime --extra optimizer\n"
            )
        },
        accepted=(_accepted(),),
    )

    assert notes == []
    assert len(errors) == 1
    assert "agents/curator/Dockerfile" in errors[0]
    assert "reaches a deployed container" in errors[0]


def test_an_acceptance_matches_its_advisory_by_alias():
    evaluate, _ = _rules()

    errors, notes = evaluate(
        _report(_vuln("GHSA-w8v5-vhqr-4h9v")),
        _CLEAN_DOCKERFILES,
        accepted=(_accepted(),),
    )

    assert errors == []
    assert len(notes) == 1


def test_an_acceptance_answers_for_its_package_only():
    evaluate, _ = _rules()

    errors, _ = evaluate(
        _report(_vuln(), name="celery", version="5.4.0"),
        _CLEAN_DOCKERFILES,
        accepted=(_accepted(),),
    )

    assert len(errors) == 1
    assert "accepted for diskcache but reported against celery" in errors[0]


def test_pip_audit_reporting_one_advisory_twice_yields_one_finding():
    _, findings_of = _rules()

    findings = findings_of(_report(_vuln(), _vuln()))

    assert len(findings) == 1
    assert findings[0].package == "diskcache"


def test_every_shipped_acceptance_names_a_decision_and_a_retire_trigger():
    accepted, _ = _baseline()

    assert accepted
    for entry in accepted:
        assert entry.decision.startswith(("DL-", "ADR-")), entry.vuln_id
        assert entry.retire_when.strip(), entry.vuln_id
        assert entry.reason.strip(), entry.vuln_id


def test_the_cli_reads_a_recorded_report_and_reports_the_acceptance(tmp_path, capsys):
    try:
        from scripts.check_dependency_audit import main
    except ModuleNotFoundError as exc:
        pytest.fail(f"dependency audit checker is missing: {exc}")
    recorded = tmp_path / "audit.json"
    recorded.write_text(
        json.dumps(_report(_vuln(aliases=("GHSA-w8v5-vhqr-4h9v", "CVE-2025-69872")))),
        encoding="utf-8",
    )

    assert main(["--audit-json", str(recorded)]) == 0
    output = capsys.readouterr().out
    assert "accepted: PYSEC-2026-2447" in output
    assert "1 accepted advisory re-checked" in output
