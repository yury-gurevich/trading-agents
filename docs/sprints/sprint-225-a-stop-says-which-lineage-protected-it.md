<!-- Agent: execution | Role: sprint spec + closeout for work-queue item 27 -->
# Sprint 225 — a stop says which lineage protected it

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-225-a-stop-says-which-lineage-protected-it`
**Status:** BUILT
**Version:** `0.108.00` (MINOR)
**Effort:** M
**Decisions:** [DL-200](../design-log.md) · [DRIFT-072](../laws/drift-register.md) · closes
work-queue item **27** · builds on [DL-118](../design-log.md) (S182) and [DL-44](../design-log.md)

> **Why this bump kind.** MINOR: the graph gains a fact it did not carry. Not a fix — nothing was
> computing the wrong answer; the record simply could not express which of two paths ran.

---

## Goal

Every placed broker stop records the lineage that produced it, so *"which path protected this
holding?"* is a property read rather than an inference — and `EXEC-OBS-03`'s promise that the
protective-stop lifecycle is **fully reconstructable** becomes true of that dimension.

## Why (context)

Work-queue item 27 shipped and deployed in S182 and then sat open for a month owing a **live proof**
that the pending-`Fill` path had ever fired. The proof never arrived, and the reason turned out not
to be bad luck.

🪤 **The evidence the item was resting on could not say what it was read as saying.** A 2026-08-21 run
was judged *"the fallback never fired"* because each stop carried `stop_pct_source=position`. That
field records where the stop **percent** came from — the node's own `stop_pct` versus the settings
fallback — and `filled_entry_stops` reports exactly `"position"` whenever the `OrderIntent` carries a
`stop_pct`, which is the ordinary case. The observation was equally consistent with either path.

🎯 **Nothing else discriminated, by design.** Both builders emit the same `BrokerStopThresholdPlan`,
and the Fill path deliberately computes the *same* `position_ref` the monitor will later produce so
the eventual `Position` cannot double-place ([DL-118](../design-log.md)). Identical facts were the
feature; the cost was an unanswerable question.

### Measured 2026-09-22 on the live spine — before any change

`position_ref` is `sha256(sorted Position keys)[:16]`, so the preimage is recoverable: hash every
subset of a ticker's `Position` keys and look each stop's ref up.

| Claim | Value | How it was measured |
| --- | --- | --- |
| Stops whose ref hashes from **broker-adopted** `Position` keys | **55 of 55** | *[measured]* preimage match over every `BrokerStopOrder` on the spine |
| Stops whose ref hashes from keys that do not exist (a Fill-path signature) | **0** | *[measured]* same query |
| Stops placed since S182 deployed (2026-08-20) | **23** | *[measured]* `placed_at >= 2026-08-20` |
| `Position` rows by key shape | **67** broker-adopted / **4** run-lineage | *[measured]* key-prefix count |
| `BrokerStopOrder` rows by `stop_pct_source` | 48 `position`, 7 absent (pre-S182), **0** `fallback` | *[measured]* group-by |
| `UnprotectedPosition` faults reading *"no active graph position"* | **4**, newest 2026-08-19 — all **before** S182 | *[measured]* fault scan |

🚨 **So the pending-`Fill` path has never fired in production, and the reason is structural, not
incidental:** run-start broker reconciliation ([DL-44](../design-log.md)) adopts every holding into an
active `Position` before execution reaches `place_broker_stops`, so the ticker always has an active
plan and `blocked_tickers` keeps the Fill path out. **The window S182 was built for is closed by a
later mechanism** — S182 did not fail, it was superseded for the ordinary case.

## Scope — and what is deliberately NOT here

1. **`derived_from` on every placed stop** — `active_position` or `pending_fill`, written to both the
   `BrokerStopOrder` fact and the stop `Fill`, declared in the pack's `Fill` property list.
2. **Four tests citing `EXEC-OBS-03`**, including the boundary the measurement found: an adopted
   holding is protected *from the Position*, and the Fill path is blocked.
3. **[DRIFT-072](../laws/drift-register.md)** — the clause read 🟩 on nine tests, none of which
   touched the reconstructability limb item 27 needed.
4. **A split before the block** — `broker_stop_actions.py` was at **191** lines and this change would
   have pushed it past the warn line for good; graph writes move to `broker_stop_writes.py` and the
   shared types to `broker_stop_types.py`, below both builders (the [DL-198](../design-log.md) shape,
   so no module imports a caller back to name a type).

### Out of scope (do NOT build this sprint)

- **Removing the S182 path.** "Never observed" is not "unreachable" — see the road not taken.
- **No `laws.md` edit.** `EXEC-OBS-03` already promises this; making a LOCKED clause true is a drift
  row plus test rows, never an amendment.
- **Changing stop placement order.** Moving execution after monitor adoption is DL-118's rejected
  route and still is.

### The road not taken (LAW-06)

- **Wait for a run that supplies the proof.** Rejected: measured, that run cannot occur under current
  ordering. The item would have waited indefinitely for an event the pipeline prevents.
- **Retire the S182 path as dead code.** Rejected: its trigger is a degraded reconciliation, which is
  exactly when protection matters most. It costs nothing while idle.
- **Infer the path from `position_ref` shape in a report.** Rejected: it works only while the two key
  shapes differ, and it *infers* rather than records — the same category of evidence that produced the
  wrong 2026-08-21 conclusion.
- **Add a new law clause.** Rejected: see above.

## Blast radius — measured 2026-09-22

| What | Detail |
| --- | --- |
| Files changed | `broker_stop_actions.py` 191→**131**, `broker_stop_thresholds.py` 161→**142**, `filled_entry_stops.py` **174**, `broker_stops.py` **185**, new `broker_stop_writes.py` **104**, new `broker_stop_types.py` **65**, new test file, pack vocabulary, laws test-plan, drift register |
| Agents affected | execution only — no agent imports another |
| Contract change? | **no** — `contracts/` untouched |
| Graph vocabulary change? | **yes** — `derived_from` added to the pack's `Fill` property list |
| New env keys / tunables | none |
| Deploy implication | 🚨 **full `up`, not an image-only retag** — the vocabulary pack moves with the image |

**Law-cycle question — does this change `contracts/` or add a guarantee an agent did not previously
make?** **No.** `EXEC-OBS-03` already requires the protective-stop lifecycle to be fully
reconstructable; this sprint makes that true of the derivation dimension and files DRIFT-072 for the
gap. No clause added, no `laws.md` edit, law version unchanged at **LOCKED v1.6**.

## Test plan results

| # | Test | Status | Proves |
| --- | --- | --- | --- |
| A1 | `test_a_stop_from_an_active_position_records_that_lineage` | PASS | the Position path is named on both the stop fact and its Fill |
| A2 | `test_a_stop_from_a_pending_fill_records_that_lineage` | PASS | the S182 path is distinguishable in the record |
| A3 | 🪤 `test_the_percent_source_does_not_answer_which_lineage_placed_the_stop` | PASS | the Fill path reports `stop_pct_source=position` too — the exact misreading item 27 rested on |
| A4 | 🪤 `test_an_adopted_holding_is_protected_from_the_position_not_the_fill` | PASS | run-start adoption wins the race and the record says so — the 55/55 measurement, pinned |

All four cite `EXEC-OBS-03` and are appended to its `test-plan.md` row.

## Success factors

- [x] Every placed stop records `derived_from` on both facts it writes.
- [x] The two paths are distinguishable in the record without touching `position_ref`, which stays
      deliberately identical so a later `Position` cannot double-place.
- [x] `EXEC-OBS-03`'s unproven limb has test rows; DRIFT-072 records why it read green without them.
- [x] Every touched module under 200 lines, and the two that were past the warn line came down.
- [x] Guards planted, watched to fail, restored — stated per guard below.
- [x] `make ci` exit 0, 100.00 % coverage.
- [x] No `contracts/` change, no law amendment, law-cycle question answered with its reason.

## Traps

🪤 **`stop_pct_source` is not a derivation path.** It answers "where did the percent come from", and
both builders can answer `"position"`. Reading it as a path is what cost item 27 a month.
🪤 **The identical `position_ref` is deliberate.** Do not "fix" it to tell the paths apart — that is
DL-118's rejected route and it would double-place a stop after monitor adoption.
🪤 **This deploy is a full `up`.** The `Fill` property list moved; an image-only retag would ship code
that writes a property the deployed vocabulary pack does not declare.

## Closeout — evidence

**Tree the proofs ran in:** `C:/Users/yury_/Downloads/project/ta-s225`, branch
`sprint-225-a-stop-says-which-lineage-protected-it`, **no `.env`**. The spine measurements above were
taken separately, read-only, from the main checkout, which has `.env`.

**Result:** `derived_from` is written on the `BrokerStopOrder` fact and the stop `Fill` for both
derivation paths and declared in the vocabulary pack. The question item 27 could not answer for a
month is now one property read; and the reason it could not be answered is recorded — measured, the
pending-`Fill` path has never fired in production because run-start adoption reaches the holding
first.

**Guards planted, watched to fail, restored — per guard:**

1. *The two paths become indistinguishable again* — set `derived_from="active_position"` in
   `filled_entry_stops`: A2 and A3 failed with `assert 'active_position' == 'pending_fill'`;
   restored, 4 passed.
2. *The fact stops being written* — dropped `derived_from` from `write_stop_order`: **all four**
   failed with `KeyError: 'derived_from'`; restored, 4 passed.

**Module line counts:** `broker_stop_actions.py` **131**, `broker_stop_thresholds.py` **142**,
`broker_stop_types.py` **65**, `broker_stop_writes.py` **104**, `broker_stops.py` **185**,
`filled_entry_stops.py` **174**.

**`make ci`:** redirected to a file, never piped. Exit code **0**. `3052 passed, 6 skipped`, coverage `100.00 %`. Dependency audit: `No unaccepted vulnerabilities; 1 accepted advisory re-checked`. Both secret scans read `Passed`. The PARAM/settings step prints its **57** baselined warnings (item 33) and exits 0, unchanged by this sprint.

**`make gate-ran`:** filled at merge.

**Not met / verified failing:** the live proof item 27 originally asked for is **not** supplied and
**cannot be** under current ordering — stated plainly rather than quietly dropped. What replaced it
is a measurement that explains why, and a record that will show the first time it changes.

## Return notes

- **The item's own evidence was the defect.** Item 27 was not blocked on a rare event; it was blocked
  on a field that could not answer the question, and a row that read that field as if it could.
- **Next time the question comes up**, it is `select props->>'derived_from' from nodes where
  label='BrokerStopOrder'`, not a hash-preimage search.
- **What this does not prove:** that the pending-`Fill` path *works* in production. It has never run
  there. The four tests prove it works at the boundary; only a degraded reconciliation would exercise
  it live, and that is not an event to arrange deliberately.
