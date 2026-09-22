"""Judge one pip-audit report against the advisories this repo accepts.

Agent: tooling
Role: decide which findings fail the gate and which accepted ones still hold.
External I/O: none; pure functions over a decoded report.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final

from scripts.dependency_audit_baseline import ACCEPTED, AcceptedAdvisory

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

_EXTRA: Final = re.compile(r"--extra[=\s]+([A-Za-z0-9._-]+)")
BASELINE_FILE: Final = "scripts/dependency_audit_baseline.py"


@dataclass(frozen=True)
class Finding:
    """One vulnerability pip-audit reported against one locked package."""

    vuln_id: str
    package: str
    version: str
    aliases: tuple[str, ...]
    fix_versions: tuple[str, ...]

    @property
    def identifiers(self) -> frozenset[str]:
        """Every name this advisory answers to."""
        return frozenset({self.vuln_id, *self.aliases})


def findings_of(report: Mapping[str, Any]) -> list[Finding]:
    """Return pip-audit's vulnerabilities, deduplicated by advisory and package."""
    seen: dict[tuple[str, str], Finding] = {}
    for dependency in report.get("dependencies", []):
        for vulnerability in dependency.get("vulns", []):
            finding = Finding(
                vuln_id=vulnerability["id"],
                package=dependency["name"],
                version=dependency.get("version", "?"),
                aliases=tuple(vulnerability.get("aliases", ())),
                fix_versions=tuple(vulnerability.get("fix_versions", ())),
            )
            seen.setdefault((finding.vuln_id, finding.package), finding)
    return sorted(seen.values(), key=lambda found: (found.package, found.vuln_id))


def extras_installed_by(dockerfiles: Mapping[str, str]) -> dict[str, list[str]]:
    """Map each extra named in a Dockerfile to the Dockerfiles that install it."""
    installers: dict[str, list[str]] = {}
    for name, text in sorted(dockerfiles.items()):
        for extra in _EXTRA.findall(text):
            installers.setdefault(extra, []).append(name)
    return installers


def _match(entry: AcceptedAdvisory, findings: Sequence[Finding]) -> Finding | None:
    """Return the finding an acceptance answers for, matching aliases too."""
    names = {entry.vuln_id, *entry.aliases}
    return next((f for f in findings if f.identifiers & names), None)


def _premise_errors(
    entry: AcceptedAdvisory, found: Finding, installers: Mapping[str, list[str]]
) -> list[str]:
    """Return the acceptance's premises that no longer hold."""
    errors: list[str] = []
    if found.fix_versions:
        errors.append(
            f"{entry.vuln_id}: a fix has shipped "
            f"({', '.join(found.fix_versions)}) - upgrade {found.package} and "
            f"delete the acceptance in {BASELINE_FILE}"
        )
    if found.package != entry.package:
        errors.append(
            f"{entry.vuln_id}: accepted for {entry.package} but reported against "
            f"{found.package} - re-read the advisory before re-accepting it"
        )
    extra = entry.reachable_only_via_extra
    if extra and installers.get(extra):
        errors.append(
            f"{entry.vuln_id}: the '{extra}' extra is now installed by "
            f"{', '.join(installers[extra])}, so {entry.package} reaches a "
            f"deployed container - the acceptance in {BASELINE_FILE} is void"
        )
    return errors


def _accepted_note(
    entry: AcceptedAdvisory, found: Finding, dockerfile_count: int
) -> str:
    """Return the line that puts an acceptance and its premises in gate output."""
    reach = (
        f"reachable only via the '{entry.reachable_only_via_extra}' extra, "
        f"installed by 0 of {dockerfile_count} Dockerfiles; "
        if entry.reachable_only_via_extra
        else ""
    )
    return (
        f"accepted: {entry.vuln_id} ({found.package} {found.version}) - "
        f"{reach}{entry.reason} [{entry.decision}] - "
        f"retire when {entry.retire_when}"
    )


def evaluate(
    report: Mapping[str, Any],
    dockerfiles: Mapping[str, str],
    accepted: Sequence[AcceptedAdvisory] = ACCEPTED,
) -> tuple[list[str], list[str]]:
    """Return (errors, notes) for one audit report against the acceptances."""
    findings = findings_of(report)
    installers = extras_installed_by(dockerfiles)
    errors: list[str] = []
    notes: list[str] = []
    answered: set[tuple[str, str]] = set()
    for entry in accepted:
        found = _match(entry, findings)
        if found is None:
            errors.append(
                f"{entry.vuln_id}: accepted but no longer reported - delete the "
                f"stale acceptance in {BASELINE_FILE}"
            )
            continue
        answered.add((found.vuln_id, found.package))
        premise_errors = _premise_errors(entry, found, installers)
        errors.extend(premise_errors)
        if not premise_errors:
            notes.append(_accepted_note(entry, found, len(dockerfiles)))
    errors.extend(
        f"{found.package} {found.version}: {found.vuln_id} is not accepted "
        f"(fix versions: {', '.join(found.fix_versions) or 'none'})"
        for found in findings
        if (found.vuln_id, found.package) not in answered
    )
    return errors, notes
