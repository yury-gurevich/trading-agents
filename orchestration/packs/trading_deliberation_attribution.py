"""What an advisory deliberation run can actually prove about its own veto.

Agent: orchestration
Role: score an advisory run's veto evidence, separating "the veto did not execute
      at all" from "the veto ran and degraded on some of its subjects".
External I/O: none.

🚨 **Operator decision, 2026-09-13** — *"should a run where the veto could not
execute at all stay green under advisory posture? No."*

Three statuses describe a run whose buys reached the broker without review, and
before S202 the board's verdict depended on **which label** described it rather
than on the outcome:

| Status | DeliberationRun | What it means | Before S202 |
| --- | --- | --- | --- |
| `not_required` + buy | absent | claimed nothing to veto, untrue | 🔴 |
| `proceeded_unvetoed` + buy | absent | grace expired, submitted | 🟢 |
| `applied_failed_open`, all failed | present, empty | every call empty | 🟢 |

All three are the same fact. The first was already red (S191). This module makes
the other two red as well, and leaves the genuinely different case — a veto that
ran and degraded on *some* of its subjects — green with its stated reason.

🪤 **The line is partial-vs-total, not present-vs-absent**, and getting that wrong
once already made a gate that could never fire. Measured 2026-09-13 over the 40
linked `ExecutionRun` rows that carry a deliberation status:

| Condition | Occurrences |
| --- | --- |
| `advisory` + `proceeded_unvetoed` | **0** |
| `advisory` + `applied_failed_open`, `failed_open_count == reviewed` | **4** |
| `advisory` + `applied_failed_open`, `0 < failed_open_count < reviewed` | **0** |

So keying only on the absent-`DeliberationRun` statuses produces a tripwire for a
condition that has never occurred, while the condition the operator described sits
in the third row wearing a different label. All **4** carry `real_debate_count=0`
and a `failed_open_reason` naming `400 … credit balance is too low` — the
2026-08-21→28 and 2026-09-08→11 billing outages.

🪤 **[DL-125](../../docs/design-log.md) does not forbid this, and reading it as if
it did is what produced the inert rule.** DL-125 argued against the gate going red
nightly *for a declared, accepted, external outage*, and its proposed remedy was a
declared `advisory` posture so that knowingly-unvetoed submissions become "a stated
mode with a truthful green". It never argued that a veto which reviewed **nothing**
should read as green; its own `sched-2026-08-21` entry records that run failing
acceptance as the correct outcome. The operator's 2026-09-13 decision settles the
remaining ambiguity in the narrow direction: declared posture excuses trading
unvetoed, it does not excuse reporting that the veto worked.
"""

from __future__ import annotations

NOT_REQUIRED_STATUS = "not_required"
PROCEEDED_UNVETOED_STATUS = "proceeded_unvetoed"
APPLIED_FAILED_OPEN_STATUS = "applied_failed_open"

ADVISORY_STATUSES = frozenset(
    {"applied", APPLIED_FAILED_OPEN_STATUS, PROCEEDED_UNVETOED_STATUS}
)

#: Scored green — the run can account for its own veto evidence.
OK = "ok"
#: The run claimed no veto was needed while approving a buy (S191).
BUY_VETO_MISSING = "buy_veto_missing"
#: The veto did not execute at all, by either route.
VETO_NEVER_RAN = "veto_never_ran"
#: Evidence is unreadable, so nothing can be proven either way.
MISSING = "missing"


def advisory_attribution(
    *,
    posture: str | None,
    status: str | None,
    failed_open_count: int | None,
    failed_open_reason: str,
    approved_buy_count: int | None,
    reviewed: int,
) -> str:
    """Classify what an advisory run proves about its veto."""
    if posture != "advisory":
        return MISSING
    if status == NOT_REQUIRED_STATUS:
        return _no_veto_claimed(approved_buy_count)
    if status == PROCEEDED_UNVETOED_STATUS:
        return OK if approved_buy_count == 0 else VETO_NEVER_RAN
    if status not in ADVISORY_STATUSES:
        return MISSING
    if failed_open_count and not failed_open_reason:
        return MISSING
    if _reviewed_nothing(failed_open_count, reviewed):
        return VETO_NEVER_RAN
    return OK


def _no_veto_claimed(approved_buy_count: int | None) -> str:
    if approved_buy_count == 0:
        return OK
    if approved_buy_count is not None:
        return BUY_VETO_MISSING
    return MISSING


def _reviewed_nothing(failed_open_count: int | None, reviewed: int) -> bool:
    """Every subject the veto was given failed open, so it reviewed none of them.

    A `reviewed` of 0 is not this case: there was nothing to review, which the
    `not_required` branch above already scores on approved buys instead.
    """
    return bool(failed_open_count) and reviewed > 0 and failed_open_count == reviewed
