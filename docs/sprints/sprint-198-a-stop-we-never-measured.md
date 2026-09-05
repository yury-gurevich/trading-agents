<!-- Agent: planning | Role: sprint handover - promote the scaled stop and record whether it was right -->
# Sprint 198 - a stop we never measured is a stop we never chose

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-198-a-stop-we-never-measured`
**Status:** MERGED
**Version:** `0.96.00` (MINOR)
**Effort:** M
**Decisions:** [DL-156](../design-log.md) the recorder and its rejected shapes - [DL-77](../design-log.md) the measurement and its 2026-09-05 addendum - ADR-0013 promotion path - work-queue items **47 (c)** and **49**

> **Why this bump kind.** The analyst gains a dimension it did not have: it now records what
> actually happened after a recommendation. `ANLZ-OBS-03` promised the counterfactual was
> reconstructable and it was - but unjudgeable, because nothing recorded the outcome. New capability,
> new clause, new graph property - MINOR.

---

## Goal

Two things become true together, and neither is worth much without the other:

1. **The flip.** `stop_target_mode` ships as `scaled` in the trading pack, promoting the S150
   challenger from dormant to live (ADR-0013, operator decision 2026-09-05).
2. **The record.** Every past `Recommendation` the run's own bars can settle gains
   `stop_target_observed_drawdown_pct` **and the horizon that produced it**, so the flip can be
   judged on this book instead of on an external backtest - starting with its first night.

## Why (context)

Item 47 (c) was CONFIRMED by [DL-154](../design-log.md): the same `stop_pct=0.0500` is applied to a
bank and a semiconductor, with book betas measured **XOM -0.97 ... INTC 3.35**. DL-77 measured what
that means - a 5 % stop is **2.4 ATRs on BAC and 0.6 ATRs on MRVL**, touched on 0 % and ~39 % of days
respectively. The fix has been built and dormant since S150.

Preparing that promotion on 2026-09-05 found the reason it had never been decided.

### Measured, 2026-09-05 - read these before designing

`scripts/compare_stop_targets.py` against the live graph, **269 recorded recommendations**:

| mode | stop min / median / max | RR pass rate | known outcomes | would-touch rate |
| --- | --- | --- | --- | --- |
| flat | 5.00 / 5.00 / 5.00 | 100.00 % | 0 | n/a |
| scaled | 3.00 / 5.45 / 8.00 | 100.00 % | 0 | n/a |

| Claim | Value | How it was measured |
| --- | --- | --- |
| DL-77's named trap does not bite on this book | **RR pass 100 % in both modes** | *[measured 2026-09-05]* the table above; `_scaled_target` scales the target with the stop and `test_scaled_stop_rr_gate.py::test_reward_risk_verdict_is_mode_invariant_when_both_values_scale` proves the verdict is mode-invariant |
| `stop_target_observed_drawdown_pct` has no producer | **0 writers** | *[measured 2026-09-05]* declared at `trading_graph_vocabulary.json:483`, read at `compare_stop_targets.py:30`; a repo-wide search finds only `tests/test_compare_stop_targets.py:89` and `tests/test_graph_vocabulary_completeness.py:183` |
| Touch-rate evidence that exists for our own trades | **none** | *[measured 2026-09-05]* `known_outcomes` 0 across all 269 |
| The only touch-rate evidence at all | **DL-77, 65 sessions from 2026-04, 7 tickers** | *[carried, DL-77]* external bars, not our book |
| The env override reaches the setting | `mode = scaled` | *[measured 2026-09-05]* `ANALYST_STOP_TARGET_MODE=scaled` resolved through `AnalystSettings()` |
| Next scheduled run | **Monday 2026-09-07 22:30 UTC** | *[measured 2026-09-05]* dispatcher cron `30 22 * * 1-5`, and 2026-09-05 is a Saturday |

That last row is why both halves ship together: there is no run between the decision and the
deploy, so the recorder costs the flip nothing in calendar time and buys it a first night of data.

---

## Scope - and what is deliberately NOT here

1. **`observed_drawdown`** - pure window math: the deepest close-to-low fall over the
   `stop_target_drawdown_horizon_days` sessions **after** the decision bar, as a fraction of the
   decision close. `None` when the window has not settled or the anchor session is missing.
2. **`backfill_observed_drawdowns`** - writes the value **and the horizon** onto every past
   `Recommendation` this run's bars can settle. Append-only: a recorded observation is immutable.
3. **The flip** - `ANALYST_STOP_TARGET_MODE: "scaled"` in `trading_tunables.json`, with the
   measurement recorded in the pack's own `_measured` note.
4. **Law cycle** - `ANLZ-OBS-05` declared and proven; analyst laws **v1.3**; five test-plan rows;
   one PARAM row; both rollups.

### Out of scope (do NOT build this sprint)

- **Re-pricing live stops.** DL-77 ruled out letting the monitor re-price stops as volatility
  drifts; mutating live risk instruments on a schedule is a much larger safety question.
- **Item 47 (d), the 50 bps limit band.** CONFIRMED as description and **by design**
  ([DL-76](../design-log.md)); a separate decision on a separate challenger.
- **Deciding the flip from the new data.** The recorder starts a clock. Reading it is a later
  session's job, and the honest answer today is that it has not been read.
- **No ADR reversal.** ADR-0013's promotion path is being *used*, not changed.

### The road not taken (LAW-06)

Recorded in full in [DL-156](../design-log.md): a separate `StopTargetOutcome` label (rejected -
the comparison script already reads the property off `Recommendation`, and a second label buys
ownership purity at the cost of a join nothing else needs); the monitor as the writer (rejected -
the analyst owns the `Recommendation` label and already holds ~200 bars per ticker, so the monitor
would be reaching across ownership for data it would have to fetch); a variable horizon per
recommendation, matched to its actual holding period (rejected - not every recommendation is traded,
so the holding period does not exist for most of them, and a uniform window is what makes the rate
comparable); flipping without the recorder (rejected by the operator, 2026-09-05).

---

## Blast radius - measured 2026-09-05

| What | Detail |
| --- | --- |
| Files changed | `domain/stop_target_outcome.py` **new, 57**; `outcome_backfill.py` **new, 99**; `settings_stop_target.py` **new, 67** (split out of `settings.py`, which hit the 200-line block at **200** and is now **151**); `run.py` **142 -> 169**; `orchestration/Dockerfile`; `trading_graph_vocabulary.json`; `trading_tunables.json`; laws, test-plan, both rollups, `pyproject.toml` |
| Agents affected | `analyst` only. The comparison script and the PM read the result; neither imports the analyst |
| Contract change? | **No** - no `contracts/` file is touched |
| Graph vocabulary change? | **YES** - `Recommendation` gains `stop_target_drawdown_horizon_days`. The pack moves, so the deploy is a **full `up`**, never a retag (S148 / [DL-85](../design-log.md) fail-closed write guard) |
| New env keys / tunables | `ANALYST_STOP_TARGET_MODE` (pack), `stop_target_drawdown_horizon_days` (tunable, default 10) - both make the deploy a full `up` independently |
| Deploy implication | **Full `up`.** It also carries S197, which had been waiting on a retag |

🪤 **The dispatcher image caught the settings split** - `test_dispatcher_image_copies_everything_its_entrypoint_imports` went red because `orchestration/Dockerfile` did not `COPY` the new `settings_stop_target.py`. That is exactly the S195 defect (the slim image missing a module its entrypoint imports), and this time a guard existed and fired before the push.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | HEADLINE `test_settled_window_reports_the_deepest_fall_and_the_horizon_it_covers` | 3 settled sessions, low 91 against a 100 close | `0.09` **and** `horizon_days == 3` |
| A2 | TRAP `test_an_unsettled_window_stays_absent_rather_than_reporting_zero` | 2 sessions against a 3-session horizon | `None` - the absent/zero discrimination this sprint exists for |
| A3 | `test_a_name_that_only_rose_records_a_real_zero` | a window with no fall | `0.0`, distinguishable from A2's `None` |
| A4 | `test_no_bar_on_or_before_the_decision_day_is_unmeasurable` | bars entirely after the decision | `None` - there is no denominator |
| A5 | `test_a_horizon_below_one_session_measures_nothing` | `horizon_days=0` | `None` |
| A6 | `test_the_anchor_is_the_last_session_on_or_before_the_decision_day` | a decision on a non-trading day | anchors to the prior close |
| A7 | `test_backfill_writes_the_drawdown_and_horizon_onto_a_settled_recommendation` | one settled `Recommendation` | both properties written, count `1` |
| A8 | TRAP `test_a_recorded_drawdown_is_never_rewritten` | a node already carrying a drawdown | count `0`, old value intact - the merge is append-only |
| A9 | `test_an_unsettled_recommendation_is_left_without_the_property` | an unsettled node | the property is **absent**, not `0.0` |
| A10 | `test_a_ticker_the_run_never_fetched_is_skipped` | bars for a different ticker | count `0` |
| A11 | `test_a_run_with_no_bars_writes_nothing` | no bars at all | count `0` - a degraded run is not a book of zero drawdowns |
| A12 | `test_unreadable_lineage_is_skipped_rather_than_guessed` | unparseable and non-string `created_at`, non-string ticker | count `0` |
| A13 | TRAP `test_a_backfill_failure_is_a_fault_and_does_not_withdraw_the_run` | a graph whose `list_nodes` raises | one fault recorded, nothing raised |

---

## Success factors

- [x] `stop_target_mode` ships `scaled` in `trading_tunables.json`, and `ANALYST_STOP_TARGET_MODE=scaled`
      is measured to resolve through `AnalystSettings()`.
- [x] A settled window records the drawdown **and** the horizon that produced it.
- [x] An unsettled window records nothing - never `0.0` (A2/A9), while a real zero is written (A3).
- [x] A recorded observation is immutable (A8), and a backfill failure never withdraws the run (A13).
- [x] Design decisions recorded with rejected alternatives - [DL-156](../design-log.md), plus the
      DL-77 addendum carrying the 269-row measurement.
- [x] Law cycle: `ANLZ-OBS-05`, analyst laws **v1.3**, five test-plan rows, one PARAM row, both
      rollups (**25 / 48**, the number the gate derived).
- [x] Two guards planted, watched red, restored (below).
- [x] Every touched module < 200 lines - `settings.py` was split at exactly 200.
- [x] `make ci` exit 0, 100.00 % coverage.
- [ ] **Not yet true, and deliberately so:** the flip has not been judged on the new data. It cannot
      be until settled windows accumulate.

---

## Traps

**A zero and an absence are the same to a reader who does not check.** The whole point of item 49 is
that `known_outcomes=0` read as "no outcomes yet" when it meant "no producer exists". If this
recorder ever writes `0.0` for an unsettled window it recreates the defect one level down. A2 and A9
are the tests that would catch it.

**The horizon is part of the measurement, not metadata.** A drawdown measured over 10 sessions and
one measured over 30 are different numbers. They are written together so a future horizon change
cannot silently reinterpret history - and because the merge is append-only, an already-recorded
observation keeps the horizon it was measured under.

**The flip is not the evidence.** Shipping `scaled` does not make the scaled stop right; it makes it
live. What makes it judgeable is the recorder, and what makes it judged is a later reading of
`compare_stop_targets.py` once `known_outcomes` is non-zero. Do not report the flip as if it were
the conclusion.

**Backfill cost grows with the book.** It lists every `Recommendation` each run - 269 today. It is
one list plus an in-memory pass, and every node is written at most once ever, but a five-figure book
would want a query rather than a scan.

---

## Closeout - evidence

**Status:** MERGED `b2fc22b`, 2026-09-05

**Tree the proofs ran in (and `.env` present?):** `wt-s198`, branch
`sprint-198-a-stop-we-never-measured`, **no `.env`**. The 269-row comparison in *Measured* above was
run in the **main checkout**, which has `.env`, before the branch existed - it is a live-graph read,
stated as such.

**Result:** the analyst records what happened after each recommendation it can settle, together with
the horizon that produced the number, and the pack ships `scaled`. `known_outcomes` will be non-zero
for the first time after the first run under this build.

**Design decisions:** recorded as [`DL-156`](../design-log.md), with four rejected alternatives; the
measurement that motivated it is the 2026-09-05 addendum to [`DL-77`](../design-log.md).

**Guards planted:**

- **Guard A - an unsettled window must not read as zero.** Removed the `len(after) < horizon_days`
  check: **2 failed, 11 passed** - A2 and A9, exactly the absent/zero pair. Restored.
- **Guard B - the horizon is written with the value.** Dropped `HORIZON_PROP` from the merge:
  **1 failed, 6 passed** - A7. Restored; `395 passed` across the analyst suite after restore.

**Module line counts:** `stop_target_outcome.py` **57**, `outcome_backfill.py` **99**,
`settings_stop_target.py` **67**, `settings.py` **151** (from 200), `run.py` **169**,
`test_stop_target_outcome.py` **93**, `test_stop_target_backfill.py` **147**.

**`make ci`:** redirected to a file, never piped. **Exit code 0.** `2524 passed, 6 skipped`, coverage
**100.00 %**. pip-audit `No known vulnerabilities found`. detect-secrets `Passed`.

**`make gate-ran`:** run from the branch worktree `wt-s198`, whose `HEAD` was
`9dba4257001c70f074d33819d719245c611df533` - checked against `git rev-parse HEAD`, with nothing
committed above it:

```text
GATE PROVEN for 9dba4257001c70f074d33819d719245c611df533:
  CI: success (attempt 1)
  Security Findings: success (attempt 1)
```

Merged to `main` as `b2fc22b`, and re-proven on the merge commit itself - **CI, CodeQL, Security
Findings and `Build and push agent images` all `success`**, with **0 open error-level alerts**.
The post-merge CodeQL check matters here: `codeql.yml` runs only on `main` (queue item 31).

**Deploy:** full `up -Tag s198` from `70bf6662` - never a retag, and the decision was proven before
it was taken (vocabulary `d47e88b1...` -> `2d1b2dbc...`, tunables `ec468c49...` -> `90b4d637...`).
`ENV PRESERVATION` **16/16**, alembic OK, **16/16** apps on tag, **16/16 `Succeeded`**, cron
`30 22 * * 1-5` intact. The deployed `GRAPH_VOCABULARY_B64` decodes **byte-identical** to the repo
pack and declares `stop_target_drawdown_horizon_days`, so the fail-closed guard will accept the
write. `ANALYST_STOP_TARGET_MODE=scaled` read back off the live analyst app;
`DELIBERATOR_DEBATE_CONCURRENCY=1` unchanged. `DeployRecord` written on the build run's own SHA.
Full row in [`functionality-checks.md`](../laws/functionality-checks.md).

**Verifying the deploy found a contradiction the diff would not have** ([DL-157](../design-log.md)):
both peer deliberators came up at `maxReplicas`/`desiredReplicas` **4** against a baseline of **1**,
because `deploy-agents.ps1` hardcoded it in S172's own infra commit while the pack still declared
`DELIBERATOR_DEBATE_CONCURRENCY=1` - the fan-out withheld in the code half and taken in the infra
half. Fixed in the script rather than the cluster (`b0c1d4c`, no bump, `GATE PROVEN` for `01f1ec5`);
the re-`up` leaves scale **byte-identical to the pre-deploy baseline, zero drift**, all three
deliberators **1/1**. **The scale diff is the only check that would have caught it.**

**Not met / verified failing:** none. **Owed, not failed:** the first reading of
`compare_stop_targets.py` with a non-zero `known_outcomes`. No cascade has run under `s198` yet - the
first is the scheduled **Monday 2026-09-07 22:30 UTC**, the cron being weekdays-only.

---

## Return notes

- **Both halves shipped together on purpose.** The operator chose flip-plus-recorder; the calendar
  made it free, because 2026-09-05 is a Saturday and the next scheduled run is Monday.
- **The deploy is a full `up`, not a retag** - the vocabulary gained a property. It carries S197 too.
- **What the next session must not assume.** A non-zero `known_outcomes` is not yet a verdict. The
  first settled windows will be short and few; the comparison is worth reading, not acting on, until
  the sample is big enough to say something. State the denominator when you report it.
