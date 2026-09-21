<!-- Agent: planning | Role: sprint handover — the PM correlation gate becomes a ramp -->
# Sprint 220 — a correlated issuer counts in proportion to its correlation

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-220-a-correlated-issuer-counts-in-proportion`
**Status:** SPEC
**Version:** *next available MINOR at merge*
**Effort:** M
**Decisions:** [ADR-0030](../decisions/0030-the-correlation-gate-is-a-ramp-not-a-cliff.md) settles ramp-vs-cliff · [EXP-008](../research/experiments/EXP-008-correlation-cutoff-replay.md) is the measurement · `DL-189` (take the next free number and re-check it at merge) is the implementation thread · work-queue item **68**

> **Why this bump kind.** MINOR. The gate gains a dimension it did not have: a held issuer's
> contribution becomes a **graded weight** rather than membership, a second shape parameter
> (`correlation_ceiling`) is declared and injected, and `PM-NEV-08`'s guarantee changes from
> *"issuers at or above the threshold"* to *"issuers in proportion to correlation"*. That is a new
> capability with a law amendment behind it, not a bug fix.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/portfolio_manager/laws/laws.md` | The PM's **locked constitution** (LOCKED **v1.7**) | Read-only *except* for the amendment this sprint owes and names below |
| `agents/portfolio_manager/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it: every clause this sprint touches is currently 🟩, so a regression here **un-proves a green clause** |
| `docs/laws/conventions.md`, `docs/laws/drift-register.md`, `docs/laws/ledger.md`, `docs/laws/INDEX.md` | Umbrella laws, drift rows, rollups | `drift-register.md` is the one law-adjacent file you may append to freely |

Binding sections here: **`PM-NEV-08`**, **`PM-NEV-09`**, **`PM-OBS-01`**, **`PM-OBS-03`**, **`PM-OBS-04`**, and the **PARAM table**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the PM's `test-plan.md` alongside its `laws.md`. Note which rows name the tests you are about to change.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** For this sprint the answer is already **Yes** — confirm it, do not re-decide it.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, record it and add a `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**Yes — and `contracts/` is NOT touched.** `GateOutcome` keeps its four fields; `threshold` keeps
carrying `max_correlated_cluster_pct`, not the correlation number. What changes is the **guarantee**:
the cluster is no longer a set of issuers at or above a line, it is every examined issuer weighted by
its measured correlation. That owes a full law cycle **in this unit of work**:

- amend **`PM-NEV-08`** (cluster definition → proportional contribution; name the ramp floor and ceiling);
- amend **`PM-OBS-03`** (the evaluated gate now discloses the **weight it used**, not only which issuers cleared a line);
- add the **PARAM row** for `correlation_ceiling` and restate `correlation_threshold`'s row as the ramp floor — 🚨 the PARAM/settings sync step of `make ci` fails without it;
- bump the PM law book **v1.7 → v1.8** with a Changelog line citing ADR-0030 and EXP-008;
- a `test-plan.md` row per amended clause, with the clause ID cited in the test docstring;
- update the rollup in **both** `docs/laws/ledger.md` **and** `docs/laws/INDEX.md` — 🪤 it is **derived**; let `make ci` tell you the number, do not declare it;
- a `drift-register.md` row for the disclosure-vocabulary change (`correlation_threshold=` leaves the gate detail, `correlation_ramp=` replaces it), so the next reader of an old artefact knows why the field name moved.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/portfolio_manager/domain/correlation.py` | PM `laws.md` + `test-plan.md`; `conventions.md` | `PM-NEV-08` defines the cluster; `PM-NEV-09` forbids recording an unevaluable gate as passed |
| `agents/portfolio_manager/domain/correlation_census.py` | same | `PM-OBS-03` requires the evaluated gate to name what it examined, what correlated and the near misses; `PM-OBS-04` requires it to disclose whether the opposite verdict was reachable |
| `agents/portfolio_manager/domain/correlation_ramp.py` *(new)* | same, plus [ADR-0030](../decisions/0030-the-correlation-gate-is-a-ramp-not-a-cliff.md) | The ramp **is** the clause's arithmetic; ADR-0030 fixes its shape (0 at ρ = 0.50, 1 at ρ = 0.90, linear between) |
| `agents/portfolio_manager/settings.py` | PM `laws.md` PARAM table | Every `tunable()` needs its PARAM row or the sync step fails |
| `orchestration/packs/trading_tunables.json` | PM `laws.md` PARAM table; [ADR-0030](../decisions/0030-the-correlation-gate-is-a-ramp-not-a-cliff.md) consequences | The deployed value, not the code default, is what the fleet runs |

⚠️ **The one invariant this sprint must not break: a gate that could not be evaluated must never come
back as a pass.** `PM-NEV-09` is green today for two paths — every pair below `min_correlation_bars`,
and a book below the deployment floor. A ramp that treats "no usable pair" as "weight 0, therefore
a small clean ratio" would convert a `NOT_EVALUATED` into a confident `PASSED`. If your change makes
that possible, stop and report.

---

## Goal

At merge, the PM's correlated-cluster gate counts **every examined held issuer in proportion to its
measured correlation with the candidate**: contribution rises linearly from 0 at ρ = 0.50 to 1 at
ρ = 0.90 and is clamped outside that band. The gate's own detail states the ramp it used and the
weight it gave each issuer, and the ratio it reports is arithmetically reproducible from the weights
it renders. `PORTFOLIO_MANAGER_CORRELATION_THRESHOLD` survives as the **ramp floor**, a new
`PORTFOLIO_MANAGER_CORRELATION_CEILING` is declared and injected, and both are `tunable()` shape
parameters of a graded test rather than a single decision boundary.

## Why (context)

`PORTFOLIO_MANAGER_CORRELATION_THRESHOLD = 0.70` is a **binary inclusion test**: an issuer at or above
it joins the cluster at full value, one below it contributes nothing. Since 2026-09-14 this has been
the referee's **lead ground on buy vetoes** — MDLZ 09-14, AMZN 09-15, AMZN on both 09-16 runs — and
EXP-008 measured that the critique is *true and inert*: no cutoff between 0.50 and 0.70 changes a
single one of 38 recorded approvals. So the argument consumes every debate without being able to
change an outcome, and the line itself does not survive its own error bars on 12 of 16 near-line pairs.

ADR-0030 accepted the ramp on 2026-09-20 and **shipped no code**. This sprint is that code.

### Measured, 2026-09-17 → 2026-09-21 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Approvals rejected by the ramp, replayed | **0 of 38** | *[measured 2026-09-17]* [EXP-008](../research/experiments/EXP-008-correlation-cutoff-replay.md), 17 scheduled runs, 38/38 validated against recorded cluster membership **and** cluster value |
| Worst cluster share — ramp vs cliff | **0.098** vs **0.102** (cap 0.25) | *[measured 2026-09-17]* EXP-008 variant table — the ramp reads the book **slightly more tightly**, it is not a loosening |
| Near-line pairs whose 95 % interval spans 0.70 | **12 of 16** | *[measured 2026-09-17]* EXP-008 noise check, pairs with 0.50 ≤ ρ < 0.90 |
| The staples complex the cliff discards | KO **0.6397**, KHC **0.6097**, MO **0.5811** — all `correlated_issuers=none` | *[measured 2026-09-17]* MDLZ on `sched-2026-09-16` |
| Deployed threshold on the `portfolio-manager` app | **0.70**, from `trading_tunables.json:16` | *[measured 2026-09-20]* read off the running app, not the file (ADR-0031's warning) |
| Module line counts before the change | `correlation.py` **182**, `correlation_census.py` **174**, `correlation_math.py` **69**, `risk.py` **161**, `run.py` **142**, `settings.py` **135** | *[measured 2026-09-21]* `wc -l` |
| Rejections under weighted ρ⁺ (the rejected alternative) | **5**, all MDLZ, worst share **0.300** | *[measured 2026-09-17]* EXP-008 — this is what a retroactive shock looks like, for comparison |

🚨 **Two of those modules start within 26 lines of the hard block.** See Traps.

---

## Scope — and what is deliberately NOT here

1. **The failing test first.** A held issuer at ρ = 0.70 must contribute **half** its value to the
   cluster, not all of it. Write it, watch it fail against today's binary code, paste the red output.
2. **New module `agents/portfolio_manager/domain/correlation_ramp.py`.** One responsibility: convert a
   measured correlation into a contribution weight.
   - `contribution(correlation: float | None, *, floor: float, ceiling: float) -> float`
   - `None` → `0.0`; `ρ ≤ floor` → `0.0`; `ρ ≥ ceiling` → `1.0`; between → `(ρ - floor) / (ceiling - floor)`.
   - 🪤 **Degenerate configuration is a real path, because both numbers are pack-injected.** When
     `ceiling <= floor`, the function degrades to a **binary test at the floor** (`ρ ≥ floor` → 1.0,
     else 0.0) and the gate detail must say `ramp=degenerate`. Never a `ZeroDivisionError`, never a
     silent full-value cluster.
   - Weights are rounded to **4 decimal places at the point of use**, and the rounded weight is both
     what the arithmetic uses and what the detail renders. The explanation is generated from what was
     measured — a rendered weight that differs from the applied weight is a defect, not a rounding note.
3. **`correlation_census.py` — the census carries the weight.** `IssuerComparison` gains a
   `contribution: float`. `clustered()` becomes a contribution view: every examined issuer with
   weight > 0, ranked by weight then issuer. `all_pairs_unusable()`, `first_skipped()`,
   `max_skipped_overlap()` and the skipped-pair rendering are **unchanged**.
4. **`correlation.py` — the ratio uses the weights.** Cluster value becomes
   `cost + issuer_values[candidate_issuer] + Σ (weight_i × issuer_values[i])` over examined issuers.
   🪤 Weights are `float` and issuer values are `Decimal`: convert with `Decimal(str(weight))` on the
   rounded weight. Do not build a `Decimal` from a raw `float`.
5. **Gate detail vocabulary.** Keep every existing field name except one:
   - `examined_issuers=<n>` — unchanged.
   - `correlated_issuers=USB:0.7172:w0.5430,C:0.6788:w0.4470` — same field, extended value: `ISSUER:ρ:w<weight>`, only issuers with weight > 0, `none` when empty.
   - `below_threshold_top=` — **name unchanged**, now the top 3 issuers with **weight 0**.
   - `correlation_threshold=0.7000` → **replaced by** `correlation_ramp=0.5000..0.9000` (or `correlation_ramp=0.5000..0.9000:degenerate`).
   - `cluster_weight_total=<sum of weights, 4dp>` — **new**, so a reader can see how much book the cluster actually counted.
   - `min_pair_overlap_bars=`, `skipped_pairs=`, `skipped_pair_issuers=` — unchanged.
6. **`settings.py`.** `correlation_threshold` default **0.70 → 0.50** with a `why=` that says *ramp
   floor*; new `correlation_ceiling` default **0.90**, `ge=0.0, le=1.0`, `why=` saying *the correlation
   at which a held issuer counts in full*.
7. **`risk.py` and `run.py` wiring.** `risk.py:49`'s `correlation_threshold: float = 0.70` default
   becomes `0.50` and gains `correlation_ceiling: float = 0.90`; `run.py:94` passes
   `settings.correlation_ceiling` alongside it. `CorrelationBook` gains a `ceiling: float` field.
8. **`orchestration/packs/trading_tunables.json`.** `PORTFOLIO_MANAGER_CORRELATION_THRESHOLD`
   **0.70 → 0.50**, and add `PORTFOLIO_MANAGER_CORRELATION_CEILING: "0.90"`.
   🚨 **This is not optional tidy-up.** Leave the pack at 0.70 and the fleet runs a **0.70 → 0.90**
   ramp, which is not the shape EXP-008 measured and not the shape ADR-0030 accepted. The unit tests
   would all pass and the deployed gate would be wrong.
9. **The law cycle** named in the law-cycle question above.

### Out of scope (do NOT build this sprint)

- **Any change to `max_correlated_cluster_pct` (0.25).** The cap is ADR-0025's and is not reopened here. This sprint changes *what goes into the ratio*, never the line it is compared against.
- **Any change to the deployment floor path** (`deployment_floor.py`) or to `PM-NEV-09`'s not-evaluated outcomes. They are green; keep them green.
- **Any sizing change.** Risk-based sizing is item 62 and regime scaling is item 64 / ADR-0031. Neither is authorised here.
- **A `/tuner` run on the floor or the ceiling.** ADR-0030 fixed the shape; *where the line sits* can become an experiment later, and this sprint must not pre-empt it by tuning.
- **Renaming the `PORTFOLIO_MANAGER_CORRELATION_THRESHOLD` key.** ADR-0030 keeps it deliberately.
- **No ADR reversal.** An ADR is reversed by a new ADR, never by a sprint.

### The road not taken (LAW-06)

- **Keep the binary cliff at 0.70.** Rejected by ADR-0030: it is the option the noise measurement indicts, and it keeps feeding the referee a true-but-inert lead argument.
- **Lower the cutoff to 0.60 or 0.50 and stay binary.** Rejected: measured to change **nothing** (0 rejections either way), so it buys none of the benefit and keeps all of the noise sensitivity. 🪤 It looks like action while being none.
- **Weight every positive correlation (ρ⁺).** Rejected on measurement: **5 rejections, all MDLZ**, worst share **0.300** against a 0.25 cap — a real retroactive shock — and it turns a *cluster* check into a **book-wide co-movement** check, a different gate rather than a better one.
- **Rename `below_threshold_top` to match the new vocabulary.** Rejected: the field is cited in a `PM-OBS-03` test-plan row and its meaning — *examined, counted nothing* — is unchanged. Churn without a reader benefit.
- **Validate `ceiling > floor` at settings level instead of degrading in the function.** Rejected: the values arrive by pack injection at runtime, so a settings-time check is not where the bad pair appears. A degenerate ramp that **says it is degenerate** is this repo's shape (a check that cannot discriminate says so).

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Where rounding happens** — the weight is rounded once, at the point of use, and the same rounded value is rendered and applied. The alternative (render full precision, apply full precision) makes the artefact un-recomputable by a reader, which is exactly what DL-187 said the product cannot be.
2. **What `clustered()` means now** — a contribution view over every examined issuer with weight > 0, replacing set membership. Name the callers you checked.
3. **How a degenerate ramp behaves** — binary at the floor, and disclosed. Name what you rejected.
4. **Whether `below_threshold_top` keeps its name** — this spec says yes; if reading the laws changes your mind, that is a finding to report, not a quiet rename.

🪤 **Take the next free DL number (`DL-189` at spec time), then re-check it at merge.** The log has
historic duplicates and entries are prepended *and* appended. A branch cut before another DL lands
collides even when the number was free at branch time.

---

## Blast radius — measured 2026-09-21

| What | Detail |
| --- | --- |
| Files changed | `correlation.py` **182**, `correlation_census.py` **174**, `correlation_ramp.py` *(new)*, `settings.py` **135**, `risk.py` **161**, `run.py` **142**, `trading_tunables.json`, PM `laws.md` + `test-plan.md`, `docs/laws/ledger.md`, `docs/laws/INDEX.md`, `docs/laws/drift-register.md`, 4 PM test files (`test_correlation_census.py` **192**, `test_correlation_concentration.py` **153**, `test_correlation_edges.py` **172**, `test_correlation_market_context.py` **122**) |
| Agents affected | `portfolio_manager` only. Confirm no agent imports another (`import-linter`). |
| Contract change? | **No** — `GateOutcome` is unchanged. But a **guarantee** changes, so the law cycle is mandatory. |
| Graph vocabulary change? | **No** new label or property. The gate detail string changes content, not schema. |
| New env keys / tunables | **`PORTFOLIO_MANAGER_CORRELATION_CEILING`** (new) and a changed value for `PORTFOLIO_MANAGER_CORRELATION_THRESHOLD`. |
| Deploy implication | 🚨 **Full `up`, not an image-only retag.** The tunables pack moves, and an image-only retag refreshes no injected pack — the S202 trap. Verify by **decoding the pack off the running `portfolio-manager` app** and hash-matching it to the repo, then reading back the two values. |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md`.
3. **Plant the failing test first** — A1 below — and watch it fail. Paste the red output.
4. **Implement** `correlation_ramp.py`, then the census, then the gate, then settings/wiring, then the pack.
5. **Law cycle** — clause amendments, PARAM rows, test-plan rows, docstring citations, both rollups, drift row.
6. **Prove the guards can fail (DL-70)** — break each guard in turn, watch it go red, restore. State it per guard.
7. **`make ci` green** — all 12 steps, **redirected to a file, never piped**.
8. **Fill the handback sections** at the bottom of this file and set **Status:** to `BUILT`.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 A held issuer at the ramp midpoint counts half | one held issuer, ρ = 0.70 by construction, known issuer value | cluster value includes **0.5 ×** that issuer's value; detail renders `w0.5000` |
| A2 | A held issuer at or above the ceiling counts in full | ρ = 0.95 | weight is **1.0**, clamped — never above 1 |
| A3 | 🪤 A held issuer below the floor counts nothing and is still disclosed | ρ = 0.45 | weight **0**; issuer absent from `correlated_issuers`, present in `below_threshold_top` |
| A4 | 🎯 The ratio is reproducible from the rendered weights | two held issuers at different ρ | parse `correlated_issuers` and `cluster_weight_total` out of the detail, recompute the value, assert it equals `GateOutcome.value` — the artefact **is** the arithmetic |
| A5 | The staples complex stops being invisible | KO 0.6397, KHC 0.6097, MO 0.5811 against an MDLZ candidate (EXP-008's measured values) | `correlated_issuers` is **not** `none`; total weight > 0; ratio still ≤ 0.25 so the order still passes |
| A6 | 🪤 A degenerate ramp says so and still discriminates | `ceiling = floor = 0.70` | binary at 0.70, `ramp=...:degenerate` in the detail, no exception |
| A7 | 🪤 `PM-NEV-09` unchanged — every pair unusable is still NOT_EVALUATED | all pairs below `min_correlation_bars` | outcome is `NOT_EVALUATED`, **not** a weight-0 pass |
| A8 | 🪤 No retroactive shock, unit-scale | the recorded-verdict fixture pattern of `test_concentration_no_shock.py` | previously `PASSED` cluster verdicts stay `PASSED` under the ramp |
| A9 | A census over zero held issuers still renders differently from a clean pass | no held issuers | `PM-OBS-03`'s existing guarantee survives the rewrite |
| A10 | The deployed pack carries the ramp the code expects | `trading_tunables.json` | a test asserting the pack declares **both** keys and that floor < ceiling — so the 0.70-left-behind mistake fails the gate, not the fleet |

Every test above cites its clause ID (`PM-NEV-08`, `PM-NEV-09`, `PM-OBS-03`, `PM-OBS-04`) in its docstring.

---

## Success factors

- [ ] A held issuer's contribution is `0` at ρ ≤ 0.50, `1` at ρ ≥ 0.90 and linear between, clamped both ends.
- [ ] The cluster ratio is recomputable from the weights the gate renders (A4 passes on parsed output, not on internals).
- [ ] `correlation_threshold` = **0.50** and `correlation_ceiling` = **0.90** in `settings.py` **and** in `trading_tunables.json`.
- [ ] `PM-NEV-09`'s two not-evaluated paths are untouched and still green (A7).
- [ ] No previously `PASSED` cluster verdict becomes `FAILED` in the unit fixtures (A8).
- [ ] Law cycle done: `PM-NEV-08` and `PM-OBS-03` amended, PARAM rows for both parameters, laws **v1.8** with a Changelog line, test-plan rows, both rollups updated by the gate, drift row filed.
- [ ] Design decisions recorded in `docs/design-log.md` with their rejected alternatives.
- [ ] Every new guard planted, watched to fail, restored — stated per guard.
- [ ] Every touched module **< 200 lines**; state the final count for each.
- [ ] `make ci` exit 0, 100.00 % coverage, redirected to a file.

---

## Traps

🪤 **Two modules start within 26 lines of the hard block.** `correlation.py` is **182** and
`correlation_census.py` is **174**; the block is 200 and the warning is 150. The ramp arithmetic goes
in its own module for that reason. If the census still crosses 200, split it by **responsibility**
(rendering vs. building) — never by line count, and never with a `# noqa`.

🪤 **The pack is the deployed truth.** Unit tests read `settings.py` defaults; the fleet reads
`trading_tunables.json`. A1–A9 can be perfectly green while the running PM uses a 0.70 floor. A10
exists to make that mistake fail the gate.

🪤 **`Decimal(float)` is not `Decimal(str(float))`.** The weights are floats and the money is
`Decimal`. Build the multiplier from the **rounded** weight's string, or the value you render and the
value you use will differ in the last places — and A4 is specifically designed to catch that.

🪤 **A weight-0 cluster is not an unevaluated gate.** After the ramp, a candidate with usable pairs
that all sit below the floor produces a **legitimate `PASSED` with a small ratio**. A candidate with
**no usable pairs at all** must still be `NOT_EVALUATED`. These now look similar in the arithmetic and
must stay opposite in the outcome.

🪤 **The census is what the referee reads.** The gate detail reaches the deliberation packet
(`PM-OBS-03`). A field renamed or dropped silently changes what the referee argues about next — which
is the whole reason this row exists. Change exactly the fields listed in scope item 5, no others.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `correlation.py` **182**, `correlation_census.py` **174**, `correlation_math.py` **69**, `risk.py` **161**, `run.py` **142**, `settings.py` **135**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. 🪤 The ramp **shape** (linear) is a mode, not a tunable; the **floor** and **ceiling** are tunables.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 12 steps** green, **100.00 % coverage floor**. **Never measure the gate through a pipe** — `make ci | tail` reports *`tail`'s* exit code. Redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it.
- Secrets never through the worktree — a worktree has **no `.env`**, so any proof needing live data is vacuous there. **State which tree you ran in.**

---

## What this sprint CANNOT prove, and who proves it

🚨 **The builder cannot run the retroactive-shock replay.** EXP-008's replay reads the live spine and
needs `.env`, which a worktree does not have. A8 is its **unit-scale stand-in**, not its equivalent.

**Planner-side, before merge:** re-run the EXP-008 replay on the book as it stands, and require
**0 retroactive rejections** and a worst share **no higher than the cliff's 0.102**. ADR-0030 asks for
this explicitly: 0/38 was measured on a 17-run history, not promised for the future. If the re-replay
rejects anything, the merge stops and the finding goes to a new ADR — not to a quiet threshold nudge.

**After deploy:** the closing evidence is the first scheduled run on the new image whose gate detail
carries `correlation_ramp=0.5000..0.9000` with a non-empty `correlated_issuers` on a candidate the
cliff would have read as `none`. Until that run exists, item 68 is code-fixed, not closed — and no
`functionality-checks.md` row is written.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving** — it resolves the SHA from the working directory and ignores a `SHA=` argument. **Check the printed SHA against `git rev-parse HEAD`.**
2. Merge to `main` locally and push. 🪤 Check you are not on the branch already — a `git merge` from the branch's own worktree says *"Already up to date"* and merges nothing.
3. **Post-merge CodeQL.** `codeql.yml` runs **only on `main`**, so a green branch gate is not proof of a CodeQL-clean merge. Check after merging.
4. **Deploy: full `up`**, then **decode the tunables pack off the running `portfolio-manager` app** and hash-match it to the repo. An image-only retag leaves the old ramp injected while every image check passes.

---

## Handover — paste this to the builder

```text
Sprint 220 - a correlated issuer counts in proportion to its correlation.
Repo: trading-agents. Branch: sprint-220-a-correlated-issuer-counts-in-proportion (create it
BEFORE any code; never work on main). Full spec:
docs/sprints/sprint-220-a-correlated-issuer-counts-in-proportion.md - read it whole first.

WHAT IS WRONG TODAY
The Portfolio Manager's correlated-cluster gate is a binary line at 0.70: a held issuer at or above
it joins the cluster at FULL value, one below it contributes NOTHING. Measured on a real run: WFC
clusters USB at 0.7172 but ignores C at 0.6788; MDLZ reads "correlated_issuers=none" beside KO
0.6397, KHC 0.6097 and MO 0.5811 - the whole staples complex, invisible. ADR-0030 decided the fix:
the cluster becomes a RAMP. Contribution is 0 at rho = 0.50, rises linearly, and is 1 at rho = 0.90.

MUST RULE - BEFORE YOU OPEN AN EDITOR
Read agents/portfolio_manager/laws/laws.md (LOCKED v1.7) and its test-plan.md, plus
docs/laws/conventions.md and docs/laws/drift-register.md. Then fill the "Law reading record" table
at the bottom of the spec. The binding clauses are PM-NEV-08, PM-NEV-09, PM-OBS-01, PM-OBS-03,
PM-OBS-04 and the PARAM table. If a law contradicts the spec, STOP AND REPORT - the law is more
likely right than the spec.

THIS SPRINT OWES A LAW CYCLE (the answer is already Yes; confirm, do not re-decide):
amend PM-NEV-08 (cluster = proportional contribution, naming floor and ceiling); amend PM-OBS-03
(the gate discloses the weight it used); add a PARAM row for correlation_ceiling and restate
correlation_threshold's row as the ramp floor; bump the law book v1.7 -> v1.8 with a Changelog line
citing ADR-0030 and EXP-008; add a test-plan row per amended clause; cite the clause ID in each test
docstring; update the rollup in BOTH docs/laws/ledger.md AND docs/laws/INDEX.md (it is DERIVED - let
make ci tell you the number); add a drift-register.md row for the gate-detail field that changes name.

ORDER OF WORK
1. Read laws, write the Law reading record.
2. Record the design decisions in docs/design-log.md (next free DL number, re-check at merge).
3. PLANT THE FAILING TEST FIRST: a held issuer at rho = 0.70 must contribute HALF its value.
   Watch it fail against today's binary code. Paste the red output into the spec.
4. Implement, in this order: new module correlation_ramp.py -> correlation_census.py ->
   correlation.py -> settings.py -> risk.py + run.py wiring -> orchestration/packs/trading_tunables.json.
5. Law cycle. 6. Break each new guard, watch it go red, restore it, and say so per guard.
7. make ci, ALL 12 STEPS, redirected to a FILE (make ci > /tmp/ci.txt 2>&1 ; echo $?) then read the
   file. NEVER pipe it - a pipe reports the pipe's exit code and a real failure reads as green.
8. Fill the handback sections, set Status: BUILT.

THE SHAPE (exact)
contribution(correlation, floor, ceiling): None -> 0.0; rho <= floor -> 0.0; rho >= ceiling -> 1.0;
else (rho - floor) / (ceiling - floor). Round to 4dp AT THE POINT OF USE, and render the SAME
rounded number you apply. If ceiling <= floor, degrade to a binary test at the floor and render
"ramp=...:degenerate" - never a ZeroDivisionError, never a silent full-value cluster.
Cluster value = cost + candidate issuer value + sum(weight_i * issuer_value_i) over examined issuers.

DO NOT
- Do not touch contracts/. GateOutcome keeps its four fields; its "threshold" field carries
  max_correlated_cluster_pct (0.25), NOT the correlation number. Leave both alone.
- Do not change max_correlated_cluster_pct, the deployment-floor path, or anything about sizing.
- Do not rename PORTFOLIO_MANAGER_CORRELATION_THRESHOLD. ADR-0030 keeps the key deliberately;
  its VALUE moves 0.70 -> 0.50 and it now means "ramp floor".
- Do not rename below_threshold_top. Its meaning (examined, counted nothing) is unchanged.
- Do not add # noqa for module size. Split by responsibility instead.
- Do not tune the floor or the ceiling. Where the line sits is a later experiment.

TRAPS THAT HAVE ALREADY COST THIS PROJECT
- correlation.py is 182 lines and correlation_census.py is 174; the hard block is 200 and the
  warning is 150. That is why the ramp gets its own module. Report the final counts.
- The PACK is the deployed truth. Unit tests read settings.py defaults; the fleet reads
  orchestration/packs/trading_tunables.json. Leave the pack at 0.70 and every test passes while the
  deployed gate runs the wrong ramp. Set BOTH keys, and write the test (A10) that fails if they drift.
- Decimal(float) is not Decimal(str(float)). Weights are floats, money is Decimal. Build the
  multiplier from the ROUNDED weight's string. Test A4 parses the rendered detail and recomputes the
  ratio, so a mismatch between rendered and applied weight fails.
- A weight-0 cluster (usable pairs, all below the floor) is a legitimate PASSED with a small ratio.
  NO usable pairs at all must still be NOT_EVALUATED. These are now similar in arithmetic and must
  stay opposite in outcome. PM-NEV-09 is green today - keep it green.
- The gate detail is what the referee reads in the debate packet. Change exactly the fields listed
  in scope item 5 of the spec, and no others.

WHAT YOU CANNOT PROVE, AND MUST NOT CLAIM
The worktree has no .env, so no live-spine replay is possible from there. Test A8 is a unit-scale
stand-in for the retroactive-shock replay, not its equivalent. The planner runs the live replay
before merge. State plainly in the handback which tree you ran in and whether it had .env.

HANDBACK CONTRACT
Fill the Law reading record BEFORE your first code change. Fill the Test plan results table - a test
you chose not to write needs a reason, not a blank. Fill Closeout - evidence with real pasted output
(the RED run first, then the green). Fill Return notes. Set Status: BUILT. Anything not met is
stated plainly as "verified failing" or "not done" - never write a Result for work you did not do.
An incomplete handback is returned, not repaired.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| *(fill)* | *(fill)* | *(fill)* | *(fill)* |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *(fill — the spec says Yes on the guarantee, No on `contracts/`; confirm and list what you did)*

**Contradictions found between a law and this spec:** *(fill)*

**Laws found silent where a decision was needed:** *(fill)*

**Clauses that were ⬜ and are now proven:** *(fill — and the rollup in ledger.md + INDEX.md)*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | *(fill)* | *(fill)* | *(fill)* | *(fill)* |

**Tests added beyond the plan:** *(fill)*

---

## Closeout — evidence

**Status:** *(fill: BUILT | MERGED)*

**Tree the proofs ran in (and `.env` present?):** *(fill)*

**Result:** *(fill — what is now true, in the artefact's own words)*

**Files changed:** *(fill)*

**Design decisions:** recorded as `DL-NNN` — *(fill)*

**Proof — the red run first:**

```text
(fill)
```

**Proof — the green run:**

```text
(fill)
```

**Guards planted:** *(fill, per guard)*

**Module line counts:** *(fill)*

**`make ci`:** *(fill — redirected to which path, exit code, counts, coverage, pip-audit, detect-secrets)*

**`make gate-ran`:** *(fill — run from which worktree, at which full 40-char SHA)*

```text
(fill)
```

**Not met / verified failing:** *(fill, or "none")*

---

## Return notes

- *(Scope held / where it moved and why.)*
- *(What you disagreed with in the spec after reading the laws.)*
- *(What the next sprint should know that is not obvious from the diff.)*
