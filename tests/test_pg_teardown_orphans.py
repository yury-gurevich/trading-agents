"""A container-owned row is found wherever its owner's key sits in the key.

Agent: tooling
Role: pin the orphan shape `<label-slug>:<container key>:<suffix>`, which the
      prefix-anchored owned pass missed — and which the survivor check missed
      for the same reason, because both call `_owned_patterns`.
External I/O: none.

🚨 Measured 2026-09-13, tearing down `verify-2026-09-13-s200` on the live spine.
`pg_teardown --run-id` printed `deleted_edges=171 deleted_nodes=146
protected_kept=26` and exited **0**, leaving

    broker-position-snapshot:pm-run-e9f5109333ea4851b404c58fd0306bb9:2026-09-13T05:59:49.790962+00:00

a `BrokerPositionSnapshot` — a label that **is** in `RUN_ARTIFACT_LABELS`, i.e.
declared disposable. The row is keyed by the **PMRun** id rather than the run-id
stamp, and `_owned_patterns` anchored its pattern as a prefix (`<key>:%`), so the
key *contains* its owner but does not *start* with it.

🪤 **The self-check shared the blind spot, which is why the exit code said fine.**
`survivors()` builds its patterns from the same `_owned_patterns`, so a row the
deleter could not reach is a row the verifier cannot see. `pg_teardown`'s own
docstring promises the opposite — *"exits non-zero if any deletable row
survived … printing a count and exiting 0 while orphans remained is the defect
DL-94 records"* — so this is DL-94 recurring through the verifier rather than the
deleter. A verifier that shares its subject's reachability assumption can only
ever confirm what its subject already handled.

The existing suite covered `<container key>:<suffix>` — the
`monitor-run-…:broker:WFC:…:check` shape, which the prefix anchor does catch.
That is precisely why this other shape survived.
"""

from __future__ import annotations

from scripts.pg_teardown_targets import (
    PROTECTED_LABELS,
    RUN_ARTIFACT_LABELS,
    collect,
    survivors,
)
from tests.test_pg_teardown_targets import FakeCursor

RUN_ID = "verify-2026-09-13-s200"
PM_RUN = ("PMRun", "pm-run-e9f5109333ea4851b404c58fd0306bb9")
#: The real orphan, verbatim from the live spine.
SNAPSHOT_ORPHAN = (
    "BrokerPositionSnapshot",
    f"broker-position-snapshot:{PM_RUN[1]}:2026-09-13T05:59:49.790962+00:00",
)
#: The shape that already worked — kept so the fix cannot trade one for the other.
PREFIXED_CHILD = ("PositionCheck", f"{PM_RUN[1]}:broker:MDLZ:1:100:check")


def test_collect_finds_a_row_keyed_slug_then_container() -> None:
    """🎯 The measured orphan: the owner's key is inside the key, not at its start."""
    cursor = FakeCursor(fetchall=[[PM_RUN], [SNAPSHOT_ORPHAN]])

    found = collect(cursor, RUN_ID)

    assert SNAPSHOT_ORPHAN in found
    _, owned_params = cursor.calls[-1]
    assert f"%{PM_RUN[1]}:%" in owned_params[-1]


def test_survivors_reports_the_orphan_so_the_exit_code_can_fail() -> None:
    """🪤 The half that made the defect silent rather than merely present.

    Without this the teardown deleted 146 rows, missed one, and exited 0 — and
    the operator's only signal was a count that looked complete.
    """
    cursor = FakeCursor(fetchall=[[SNAPSHOT_ORPHAN]])

    assert survivors(cursor, RUN_ID, [PM_RUN]) == [SNAPSHOT_ORPHAN]
    _, params = cursor.calls[0]
    assert f"%{PM_RUN[1]}:%" in params[-1]


def test_the_prefixed_child_shape_still_resolves() -> None:
    """The previously-covered shape must not be traded away for the new one."""
    cursor = FakeCursor(fetchall=[[PM_RUN], [PREFIXED_CHILD]])

    assert PREFIXED_CHILD in collect(cursor, RUN_ID)


def test_widening_the_pattern_keeps_protected_labels_unreachable() -> None:
    """🪤 The reason widening is safe, asserted rather than assumed.

    A contains-match is broader than a prefix-match, so the guard that matters is
    that the owned pass is scoped to `RUN_ARTIFACT_LABELS` — `Position`, `Fill`,
    `BrokerStopOrder` and `BrokerOrderStatus` can never be selected by it no
    matter how wide the key pattern gets.
    """
    cursor = FakeCursor(fetchall=[[PM_RUN], []])
    collect(cursor, RUN_ID)

    _, owned_params = cursor.calls[-1]
    selectable = owned_params[0]
    assert selectable == list(RUN_ARTIFACT_LABELS)
    assert all(label not in selectable for label in PROTECTED_LABELS)


def test_a_container_key_is_specific_enough_to_widen_safely() -> None:
    """Container keys are uuid-suffixed, so contains-matching cannot cross runs."""
    other = ("PMRun", "pm-run-0000000000000000000000000000beef")
    cursor = FakeCursor(fetchall=[[PM_RUN], []])
    collect(cursor, RUN_ID)

    _, owned_params = cursor.calls[-1]
    patterns = owned_params[-1]
    assert f"%{PM_RUN[1]}:%" in patterns
    assert not any(other[1] in pattern for pattern in patterns)
