<!-- Agent: planning | Role: sprint handover - the correlated-cluster gate reports its own census -->
# Sprint 197 - a gate that found nothing says how much it looked at

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-197-a-gate-says-what-it-examined`
**Status:** MERGED
**Version:** `0.95.03` (PATCH)
**Effort:** S
**Decisions:** [DL-155](../design-log.md) the census and its rejected shapes - [DL-154](../design-log.md) the measurement that found the defect - work-queue item **47**, first of three parts

> **Why this bump kind.** No new capability. `PM-NEV-08` already promised a measured
> correlated-cluster cap and the gate already computed every pair; what it could not do was *say* so.
> A producer that under-reports what it knows is a defect, not a missing feature - PATCH.

---

## Goal

The `correlated_cluster_pct` outcome names the comparison behind its verdict: how many held issuers
were examined, which reached `correlation_threshold` and at what measured value, the strongest near
misses below it, and the thinnest pairwise overlap used. After this sprint, `cluster_issuers=AVGO`
after eight comparisons and `cluster_issuers=AVGO` after none are two different strings in the same
`detail` the deliberator reads.

## Why (context)

Four consecutive scheduled nights - `sched-2026-09-01` through `sched-2026-09-04` - ended
`8/8 stages, ACCEPTANCE PASS, 0 orders submitted`. On the fourth, the deliberator vetoed `USB` and
`AVGO` partly on the reading that the correlation gate had not evaluated the co-held issuers.
[DL-154](../design-log.md) measured that objection and **refuted it**: every pair had full 120-bar
overlap, `C` (0.5650) and `SCHW` (0.3180) *were* measured and correctly omitted, and a cluster of one
was the right answer. **The judge read our evidence correctly; the evidence was incomplete.** This is
the third instance of DL-152's *producer knew something it never said* - after S183's scanner
skipped-vs-passed and S196's earnings horizon - and the first that cost a veto.

### Measured, 2026-09-04 / 2026-09-05 - read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Every USB/AVGO pair had full overlap | **120 of 120 bars** | *[measured 2026-09-04, DL-154]* pairwise recompute over the run's own bars |
| `min_correlation_bars` never bound | **0 pairs below 60** | *[measured 2026-09-04, DL-154]* same recompute |
| The strongest omitted pair | **USB~C 0.5650** | *[measured 2026-09-04, DL-154]* below the 0.70 threshold, correctly excluded |
| Fields the old detail carried about the comparison | **0** | *[measured 2026-09-05]* `correlation.py:83-88` - `candidate_issuer`, `cluster_issuers`, two dollar figures |
| Nights lost to objections resting on this | **2 of 4** | *[measured 2026-09-04, DL-154]* objections (a) and (b) of four; (c) and (d) stand |
| Where the detail reaches the judge | `context_pm.py:95` | *[measured 2026-09-05]* `gate.detail` is interpolated verbatim - no contract change needed |

---

## Scope - and what is deliberately NOT here

1. **The census is recorded, not summarised.** `build_census` compares the candidate against every
   held issuer and keeps each result - issuer, measured correlation (or `None`), widest overlap.
2. **The census renders into the gate's own `detail`,** so it travels the existing path to the
   deliberator with no contract or vocabulary change.
3. **The cluster is derived from the census,** not from a second short-circuiting pass - one
   traversal, one set of numbers, no way for the rendered evidence and the verdict to disagree.
4. **Law cycle:** `PM-OBS-03` declared and proven; laws **v1.4**; three test-plan rows; both rollups.

### Out of scope (do NOT build this sprint)

- **Item 47 (c) - volatility-scaled stops.** CONFIRMED by DL-154 and **already built** (S150,
  [DL-77](../design-log.md)); it is a promotion decision plus a verification run, not code.
- **Item 47 (d) - the 50 bps limit band.** CONFIRMED as description and **by design**
  ([DL-76](../design-log.md)); challenger shipped S149, promotion pending.
- **The same census for the sector and position-count gates.** The pattern generalises; only the
  correlation gate has cost a veto. Widening it without a second measured case is speculative work.
- **No ADR reversal.**

### The road not taken (LAW-06)

Recorded in full in [DL-155](../design-log.md) with reasons: a separate census gate outcome
(rejected - invites the judge to weigh evidence as a verdict); naming every below-threshold issuer
(rejected on context budget); rendering the census only for singleton clusters (rejected -
conditional evidence is how this defect class is born); fixing it in the prompt (rejected - asks the
judge to infer what we can state).

---

## Blast radius - measured 2026-09-05

| What | Detail |
| --- | --- |
| Files changed | `correlation_census.py` **new, 131**; `correlation.py` **159 -> 153**; `test_correlation_census.py` **new, 163**; `laws/laws.md`, `laws/test-plan.md`, `docs/laws/ledger.md`, `docs/laws/INDEX.md`, `pyproject.toml` |
| Agents affected | `portfolio_manager` only. The deliberator *reads* the longer string through `context_pm.py:95`; it imports nothing from the PM |
| Contract change? | **No** - `GateOutcome.detail` is an existing `str` field |
| Graph vocabulary change? | **No** - no new label or property; the pack is untouched |
| New env keys / tunables | **None** |
| Deploy implication | **Image-only retag.** No vocabulary move, so the fail-closed write guard (S148 / [DL-85](../design-log.md)) is not in play |

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | HEADLINE `test_census_names_the_issuers_it_examined_and_the_ones_it_ruled_out` | DL-154's own measured values for BAC/C/SCHW | the exact rendered string, including `examined_issuers=3` and both near misses |
| A2 | TRAP `test_a_census_of_nothing_says_so_rather_than_rendering_as_a_clean_pass` | zero held issuers | `examined_issuers=0` and `min_pair_overlap_bars=none` - **the string the old code could not produce differently** |
| A3 | `test_below_threshold_list_is_ranked_and_capped_at_three` | five below-threshold issuers | strongest three, in order, and the *minimum* overlap not the maximum |
| A4 | `test_an_unmeasurable_pair_is_labelled_and_ranked_last` | a pair with undefined correlation | reported as `unmeasured`, never silently dropped |
| A5 | `test_a_thin_pair_is_excluded_from_correlation_but_counted_in_overlap` | 30 bars against `min_bars=60` | the thin pair does not cluster, and its overlap is still visible |
| A6 | `test_a_multi_ticker_issuer_is_judged_on_its_strongest_pair` | GOOG + GOOGL under one issuer | `PM-NEV-07` aggregation survives the census |
| A7 | `test_gate_detail_carries_the_census_beside_the_cluster` | real bars through `CorrelationBook.outcomes` | the census reaches `GateOutcome.detail`, not just the domain object |

---

## Success factors

- [x] The evaluated `correlated_cluster_pct` detail carries `examined_issuers`,
      `correlated_issuers`, `below_threshold_top`, `correlation_threshold`, `min_pair_overlap_bars`.
- [x] A census over zero issuers renders differently from one that examined and found nothing (A2).
- [x] The verdict is unchanged: the cluster is derived from the same comparisons that are rendered.
- [x] Design decisions recorded with rejected alternatives - [DL-155](../design-log.md).
- [x] Law cycle done: `PM-OBS-03`, laws v1.4, three test-plan rows, both rollups (**29 / 48**,
      the number the gate derived - not arithmetic).
- [x] Both guards planted, watched red, restored (below).
- [x] Every touched module < 200 lines.
- [x] `make ci` exit 0, 100.00 % coverage.

---

## Traps

**The old tests still pass.** `assert "cluster_issuers=AAPL" in outcome.detail` is a substring check,
and the census is *appended*, so every pre-existing correlation test stayed green through this
change. Green here proves nothing was broken; it does not prove anything was added. A2 is the test
that would have failed before.

**`min_pair_overlap_bars` is a minimum, not a maximum.** The whole point is to expose the *thinnest*
comparison. Guard B below exists because `max` reads identically on a book where every pair is
full-length - which is every book we have measured so far.

**A longer `detail` is a longer LLM prompt.** Five fields, three named near misses; the cap is
deliberate ([DL-155](../design-log.md)).

---

## Closeout - evidence

**Status:** MERGED `dc79d05`, 2026-09-05

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\AppData\Local\Temp\wt-s197`, branch
`sprint-197-a-gate-says-what-it-examined`, **no `.env`** - every proof here is unit-level and needs
none. The live re-render is owed after deploy (see Return notes).

**Result:** the correlated-cluster gate renders the comparison behind its verdict. Against DL-154's
own measured numbers:

```text
candidate_issuer=AVGO; cluster_issuers=AVGO; examined_issuers=3; correlated_issuers=none;
  below_threshold_top=INTC:0.4988,NVDA:0.4739,MRVL:0.4102; correlation_threshold=0.7000;
  min_pair_overlap_bars=120; cluster_value_usd=...; portfolio_value_usd=...

candidate_issuer=AVGO; cluster_issuers=AVGO; examined_issuers=0; correlated_issuers=none;
  below_threshold_top=none; correlation_threshold=0.7000; min_pair_overlap_bars=none; ...
```

Before this sprint those two lines were byte-identical.

**Design decisions:** recorded as [`DL-155`](../design-log.md) - the census shape, with four rejected
alternatives and the reason each dies.

**Guards planted:**

- **Guard A - the census is real, not a constant.** `build_census` forced to compare nothing
  (`if False`): **6 failed, 1 passed**. The one that stayed green is A2, which *should* pass on an
  empty census - that is the discrimination this sprint adds, demonstrated from both sides. Restored.
- **Guard B - `min_pair_overlap_bars` is a minimum.** `min(...)` changed to `max(...)`: A3 red
  (**1 failed, 6 passed**), every other test blind to it because their pairs are equal-length.
  Restored; `113 passed` after restore.

**Module line counts:** `correlation_census.py` **131**, `correlation.py` **153**,
`test_correlation_census.py` **163**.

**`make ci`:** redirected to a file, never piped. **Exit code 0.** `2508 passed, 6 skipped`, coverage
**100.00 %**. pip-audit `No known vulnerabilities found`. detect-secrets `Passed` (tracked and
untracked).

**`make gate-ran`:** run from the branch worktree `wt-s197`, whose `HEAD` was
`64764c733c4bdd229efb3fa0f470b54f6f286533` - checked against `git rev-parse HEAD`, with nothing
committed above it:

```text
GATE PROVEN for 64764c733c4bdd229efb3fa0f470b54f6f286533:
  CI: success (attempt 1)
  Security Findings: success (attempt 1)
```

Merged to `main` as `dc79d05`.

**Not met / verified failing:** none. **Owed, not failed:** the live re-render on the fleet, which
needs a deployed run.

---

## Return notes

- **Scope held to (a)/(b).** Item 47's (c) and (d) are promotion decisions on already-built code and
  are deliberately not in this diff; the queue row is updated to say so.
- **The generalisation is real but unearned.** Three gates have now shipped the same defect. A
  cross-agent "an evaluated gate reports its census" umbrella clause is the honest end state, but it
  should follow a fourth measured instance, not precede it.
- **What the next session must not assume.** This sprint makes the *evidence* right. It does not
  predict the judge will now approve `USB` or `AVGO` - objections (c) and (d) are unaddressed and
  were confirmed. If the next scheduled night still ends 0 orders, that is expected, and the reason
  string will now say which objection did it.
