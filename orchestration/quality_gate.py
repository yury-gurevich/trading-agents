"""The verdict-quality gate's decision, separated from its command line.

Agent: orchestration
Role: turn one agreement measurement into PASS / WARN / INSUFFICIENT against a
      floor, and refuse to rule at all on a sample too small to mean anything.
External I/O: none.

Shipped warn-only, exactly as S156 did for law-coverage assertion E. The floor is
uncalibrated until Part B's repeats exist, and a gate that blocks on an invented
threshold is worse than no gate: it teaches everyone to ignore it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from orchestration.agreement import Agreement

__all__ = [
    "GATE_FAIL",
    "GATE_INSUFFICIENT",
    "GATE_OK",
    "GATE_WARN",
    "GateVerdict",
    "evaluate_quality",
]

# Named GATE_OK rather than PASS: ruff's S105 reads a constant called PASS as a
# hardcoded credential, and a noqa would hide the rule everywhere it is useful.
GATE_OK = "PASS"
GATE_WARN = "WARN"
GATE_FAIL = "FAIL"
GATE_INSUFFICIENT = "INSUFFICIENT"


@dataclass(frozen=True)
class GateVerdict:
    """What the gate decided, on what evidence, against which floor."""

    status: str
    agreement: Agreement
    floor: float
    warn_only: bool

    @property
    def exit_code(self) -> int:
        """Only a blocking FAIL is a non-zero exit."""
        return 1 if self.status == GATE_FAIL else 0

    def render(self) -> str:
        """One line of status, one of evidence, and the floor it was judged by."""
        lines = [
            f"status\t{self.status}",
            f"floor\t{self.floor * 100:.2f}%",
            f"mode\t{'warn-only' if self.warn_only else 'blocking'}",
            self.agreement.detail(),
        ]
        if self.status == GATE_INSUFFICIENT:
            lines.append(
                "note\tsample too small to compare against the floor; "
                "no quality claim is made either way"
            )
        return "\n".join(lines)


def evaluate_quality(
    agreement: Agreement, *, floor: float, min_compared: int, warn_only: bool = True
) -> GateVerdict:
    """Judge one agreement figure, refusing to rule on too little evidence."""
    return GateVerdict(
        status=_status(agreement, floor, min_compared, warn_only),
        agreement=agreement,
        floor=floor,
        warn_only=warn_only,
    )


def _status(
    agreement: Agreement, floor: float, min_compared: int, warn_only: bool
) -> str:
    rate = agreement.rate
    if rate is None or agreement.compared < min_compared:
        return GATE_INSUFFICIENT
    if rate >= floor:
        return GATE_OK
    return GATE_WARN if warn_only else GATE_FAIL
