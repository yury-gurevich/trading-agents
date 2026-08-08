<!-- Agent: tooling | Role: chore spec + closeout for the S162 module-size debt -->
# chore-split-modules-before-the-block — split the trio S162 trimmed to fit

**Closes:** the S162 module-size debt · **Opens:** [DL-96](../design-log.md) · **Type:** fix ·
**Version:** 0.89.05 · **Branch:** `chore-split-modules-before-the-block` · **Deploys:** nothing
(the fleet stays on `:s165`)

## Why

S162's implementer hit the 200-line hard block at exactly 200 and **trimmed three modules to fit
rather than splitting them**. CLAUDE.md says split *before* the block, so all three were one edit
away from a blocked gate — including `gate_report.py` and `risk.py`, which sit directly in the PM
path Monday's `sched-2026-08-10` run exercises.

## What shipped — sizes before and after

| Before | After |
| --- | --- |
| `gate_report.py` **198** | `gate_report.py` **111** + `position_gates.py` **133** |
| `risk.py` **193** | `risk.py` **133** + `order_decision.py` **128** |
| `trading_observatory_views.py` **198** | `…_views.py` **124** + `…_chain.py` **86** + `trading_stage_view.py` **29** |

Every module is now under the **150-line warn** line. The splits follow what the code already meant:
`gate_report` keeps reward-risk and approved-order construction while entry-sizing gates and the
gate-to-reason mapping move to `position_gates`; `risk` keeps ordering, precheck and the running book
state while the per-recommendation decision moves to `order_decision`; the observatory's
scanner → analyst → PM chain moves to its own module, with the shared `view()` builder extracted so
neither imports the other.

## Success factors

- [x] All three modules under the 200-line hard block, and under the 150-line warn line.
- [x] **No behaviour change** — test count unchanged at the split itself (2180 → 2180).
- [x] `make ci` green, measured unpiped to a file.
- [x] Remote `make gate-ran` green.

## Closeout — evidence

**Local gate.** `make ci` **exit 0**, `2183 passed / 6 skipped / 100.00 % coverage`, redirected to a
file and read back. The split itself was 2180 → **2180** — no test added, removed or changed, which
is the signal a pure refactor should give. The three tests added afterwards for DL-96 take it to 2183.

**Size proof.** None of the new or split modules appears in the gate's `[WARN] … (warn 150, hard
block 200)` list. `concentration.py` (**174**) still does — pre-existing, untouched, and named here
rather than quietly bundled in.

🚨 **The finding, and it is the valuable part of this chore.** A planted reorder — evaluating
`reward_risk` **before** the sizing gates — **passed all 86 PM tests**. Under that reorder an order
failing both `max_positions` and `reward_risk` is rejected as `reward_risk_below_min` instead of
`max_positions`, and that reason string is the operator-visible output on every `SKIP` line. The
existing test that looked like coverage pins `max_positions` over `cash_available`, but both live
*inside* `position_rejection`'s own loop — it constrains that function and says nothing about the
ordering of the stages around it. Closed by `test_rejection_precedence.py`; the same planted reorder
now **fails 2 of 89**. Full reasoning: [DL-96](../design-log.md).

**Remote gate.** `make gate-ran` **exit 0** — GATE PROVEN for `9818fd4f4c590f5e0bd56edaafc71a4612d15938`, **CI: success** and **Security Findings: success**. Merged to `main` as `63cba7a`.

**Found and deliberately not fixed.** `SectorBook.rejection` is an exact duplicate of the sector
gate-to-reason mapping and is **called only by tests** — dead production code kept green by a test
that exercises it directly, and a second copy of reason strings that can drift from the live one.
Removing it changes `SectorBook`'s public API and deletes a test's subject, so it is a decision
rather than a tidy-up, and it was left out of a chore scoped to move code without changing it.

**Not proven.** This is a refactor with no runtime proof: nothing was deployed and no pipeline run
has executed this code. The guard is the suite plus the planted reorder, not production.
