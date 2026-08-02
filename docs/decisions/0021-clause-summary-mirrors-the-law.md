---
type: Architecture Decision
status: accepted
closes: "When a test proves only part of a law clause, may the clause summary in test-plan.md be narrowed to describe what the test actually covers? Which document wins when laws.md and test-plan.md disagree about what a clause says?"
tags: [laws, conventions, test-plan, coverage, honesty, execution, adr-0021]
---

# ADR 0021 — A clause summary mirrors the law; it is never reworded to fit a test

**Status:** Accepted · **Date:** 2026-08-02 · **Decider:** Yury Gurevich (product owner), on a
finding raised in the S151 planning review

## Context

`agents/<name>/laws/laws.md` holds the clause text. `agents/<name>/laws/test-plan.md` holds one row
per clause: a short **summary** of what a test must prove, the test that proves it, and a ⬜/🟩
status. [conventions §7](../laws/conventions.md) already calls the test-plan *"the master"* and says
*"the plan is the master; tests are the proof."*

In S151 that ordering inverted without anyone deciding it should. `EXEC-FAIL-03` reads:

> Graph write failure → fault recorded; fills already held in-process are safe (**idempotency key
> prevents re-submission to broker**). Safe to retry: **a repeated graph write appends a new record**.

A new roll-up-containment test proved the *fault-recorded* half and nothing else. The clause was
flipped ⬜ → 🟩 — and the **summary in `test-plan.md` was reworded toward that test's scenario**, so
the row read as a complete match. Nothing in the document then disclosed that two of the three halves
were untested. The planning review reverted the flip, restored the summary, and returned execution to
30 / 57.

**Why this is worse than an ordinary over-claim.** The greens/total ratio is the one number that
answers "how much of this constitution is actually proven". Narrowing a clause to fit an available
test does not merely mis-mark one row — it makes the ratio *look* honest while quietly shrinking what
each green means. The defect is invisible from inside the ledger, because both documents agree.

This is the DL-57 shape at document level: *didn't look* rendering identically to *looked and found
nothing*.

## Decision

**The clause summary in `test-plan.md` mirrors `laws.md`. It is never reworded to fit an available
test.**

Operationally:

1. **`laws.md` is upstream of `test-plan.md`.** The summary column is a faithful (possibly
   abbreviated) restatement of the clause. Abbreviating is allowed; **dropping a conjunct is not** —
   if the clause asserts three things, the summary asserts three things.
2. **A partial test does not make a clause green.** Green requires a passing test citing the ID that
   covers the clause **as written**. Where a test covers part of it, keep the clause ⬜ and name the
   covered and uncovered halves in the Test column. Keep the partial test — it is real evidence of
   something, just not of that clause.
3. **When the two disagree, `laws.md` wins and `test-plan.md` is corrected** — never the reverse. A
   summary found narrower than its clause is *widened back*, even though that lowers the apparent
   coverage.
4. **Changing what a clause asserts is an amendment**, subject to [conventions §4](../laws/conventions.md):
   bump the law version, add a changelog line. It is never a side effect of editing a test-plan row.

## Consequences

- Ratios get *worse* on correction, and that is the intended direction. A green that shrank to fit
  its test was never worth what it claimed.
- Reviewers gain a cheap mechanical check: diff the summary against the clause. Disagreement is a
  defect regardless of which document moved.
- `EXEC-FAIL-03` is the first clause corrected under this rule. Its summary now carries all three
  conjuncts, and `chore-exec-fail-03-coverage` proves each of them
  (`agents/execution/tests/test_graph_write_failure_retry.py`), taking execution to 31 / 57.

## The road not taken

**"Split the clause into three IDs so each test maps cleanly."** Rejected. It is the same narrowing
wearing better clothes: `EXEC-FAIL-03` describes one behaviour — a failed graph write is survivable —
and three IDs would let two stay ⬜ forever while the ledger showed a green for the easy one.
[conventions §2](../laws/conventions.md) also makes IDs append-only, so a split cannot renumber; it
can only add. Splitting a clause remains available when a law genuinely conflates two behaviours, but
"a test only covers part of it" is not that case.

**"Let the summary describe the test, and put the full clause text in a footnote."** Rejected for the
same reason the roll-up flip was reverted: the column a reader scans is the column that must be true.
