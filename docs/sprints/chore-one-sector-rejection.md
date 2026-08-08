<!-- Agent: tooling | Role: chore spec + closeout for DL-97 -->
# chore-one-sector-rejection — the sector reason strings exist in one place

**Closes:** [DL-97](../design-log.md) · **Type:** fix · **Version:** 0.89.06 · **Branch:**
`chore-one-sector-rejection` · **Deploys:** nothing (the fleet stays on `:s165`)

## Why

`SectorBook.rejection` mapped a failing sector gate to `sector_name_count` /
`sector_concentration` — an **exact duplicate** of the mapping the PM actually runs
(`position_gates.sector_rejection`). Two copies of the same operator-visible reason strings, either
of which could change without the other.

🚨 **Nothing in production called it.** Its only three call sites were in `test_sector_cap.py`,
invoking it directly — dead production code that the coverage gate could not flag, because the
method was 100 % covered and had a passing test named after it. A 100 % floor measures whether a
line ran, not whether anything but a test made it run.

Surfaced by [chore-split-modules-before-the-block](chore-split-modules-before-the-block.md) and
deliberately left out of that chore's scope, since deleting it changes `SectorBook`'s public API.

## What shipped

1. **`SectorBook.rejection` deleted.** The mapping now exists once, in
   `position_gates.sector_rejection`. `SectorBook` reports gate *outcomes* only, stated in its
   module docstring so the two do not re-merge.
2. **The test was re-pointed, not deleted.** `test_sector_rejection_maps_each_failing_outcome_to_its_reason`
   keeps every prior assertion and runs them through `sector_rejection(book.outcomes(...))` — the
   composition the PM actually executes, so the coverage is real rather than self-referential.
3. `concentration.py` **174 → 144**, out of the 150-line warn band as a side effect.

## Success factors

- [x] Exactly one definition of the sector reason strings remains in the tree.
- [x] No production caller lost — verified before deleting that all call sites were tests.
- [x] The re-pointed test guards the live path, proven by a planted defect.
- [x] `make ci` green, measured unpiped to a file.
- [x] Remote `make gate-ran` green.

## Closeout — evidence

**Local gate.** `make ci` **exit 0**, `2183 passed / 6 skipped / 100.00 % coverage`, redirected to a
file and read back. The count is **unchanged** from `0.89.05` — one test rewritten, none added or
removed, which is what a dead-code removal should show.

**Planted defect (DL-70).** Swapping one reason string in the surviving
`position_gates.sector_rejection` fails **5 tests** (`test_sector_cap` plus four in
`test_sector_name_count`). The same swap inside the deleted method would have failed only its own
test — which is the measure of how little the duplicate was guarding.

**Size proof.** `concentration.py` no longer appears in the gate's `[WARN] … (warn 150, hard block
200)` output; grep of the CI log returns **0** matches for it.

**Remote gate.** _Filled at merge time._

**Not proven.** Nothing was deployed and no pipeline run has executed this code. The guard is the
suite plus the planted defect, not production. The behaviour is unchanged by construction — the
deleted method had no production caller — so there is no runtime claim to make.
