"""Collect what each credential test did during one activation or fleet check.

Agent: master
Role: run one test against resolved config and file its outcome under its name.
External I/O: none directly (delegates to the injected test callable).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from agents.master.credential_report import (
    CredentialFailure,
    CredentialTestReport,
    CredentialTransportFailure,
)
from agents.master.credential_result import coerce_result

if TYPE_CHECKING:
    from collections.abc import Mapping

    from agents.master.credential_check import CredentialTest, PassCache


@dataclass
class Outcomes:
    """Every name a run of tests declared, tested, passed, cached or failed."""

    applicable: list[str] = field(default_factory=list)
    tested: list[str] = field(default_factory=list)
    passed: list[str] = field(default_factory=list)
    cached: list[str] = field(default_factory=list)
    failed_required: list[str] = field(default_factory=list)
    failed_optional: list[str] = field(default_factory=list)
    transport_failures: list[CredentialTransportFailure] = field(default_factory=list)
    credential_failures: list[CredentialFailure] = field(default_factory=list)

    def run(
        self,
        test: CredentialTest,
        config: Mapping[str, str],
        cache: PassCache | None,
    ) -> None:
        """Run one applicable test, or reuse its fresh costly pass."""
        self.applicable.append(test.name)
        if test.cost == "costly" and cache is not None and cache.fresh(test.name):
            self.cached.append(test.name)
            return
        self.tested.append(test.name)
        result = coerce_result(test.run(config))
        if result.status == "passed":
            self.passed.append(test.name)
            if test.cost == "costly" and cache is not None:
                cache.record(test.name)
        elif result.status == "transport_failure":
            self.transport_failures.append(
                CredentialTransportFailure(test.name, result.reason)
            )
        else:
            self.credential_failures.append(CredentialFailure(test.name, result.reason))
            if test.required:
                self.failed_required.append(test.name)
            else:
                self.failed_optional.append(test.name)

    @property
    def proven(self) -> bool:
        """No required test was refused and none went unanswered."""
        return not self.failed_required and not self.transport_failures

    def first_reason(self) -> str:
        """The first refusal's reason, else the first unanswered test's."""
        refused = [
            failure.reason
            for failure in self.credential_failures
            if failure.name in self.failed_required
        ]
        unanswered = [failure.reason for failure in self.transport_failures]
        return (refused or unanswered or [""])[0]

    def extend(self, other: Outcomes) -> None:
        """Add another run's outcomes after this one's, in order."""
        for name in self.__dataclass_fields__:
            getattr(self, name).extend(getattr(other, name))

    def report(
        self,
        config: dict[str, object],
        *,
        llm_candidate: str = "",
        llm_passed_over: tuple[str, ...] = (),
    ) -> CredentialTestReport:
        """Freeze the outcomes into the activation evidence."""
        return CredentialTestReport(
            config,
            tuple(self.applicable),
            tuple(self.tested),
            tuple(self.passed),
            tuple(self.cached),
            tuple(self.failed_required),
            tuple(self.failed_optional),
            tuple(self.transport_failures),
            tuple(self.credential_failures),
            llm_candidate,
            llm_passed_over,
        )
