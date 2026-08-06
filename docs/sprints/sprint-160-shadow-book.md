<!-- Agent: planning | Role: sprint handover -->
# Sprint 160 — Every rejected pick is a discarded experiment: the shadow book

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-160-shadow-book`
**Status:** SPEC — makes selection quality measurable without spending capital
**Version:** feat → **0.87.00** (MINOR: two middle digits, zeroing the patch group)
**Effort:** M
**Decisions:** [DL-93](../design-log.md) sizing/cap/sell-policy · [DL-09](../design-log.md) filter
decisions as a labeled source (DRAFT, generalised here) · [ADR-0013](../decisions/0013-continuous-improvement-system.md)
continuous improvement · [ADR-0017](../decisions/0017-exit-authority-alpha-proposes-risk-disposes.md)
exit authority (**not** reversed here) · [DL-73](../design-log.md) **(RETRACTED — read it before you
audit any position)** · [DL-70](../design-log.md) plant the violation

> **Why the version is a MINOR and not a PATCH.** This adds a new capability — a measured selection
> scorecard and the outcome facts behind it — rather than fixing a defect. `0.86.05` → **`0.87.00`**,
> patch group zeroed. If `main` has moved, bump the minor group from whatever is on `main` and say so
> in the return notes.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 4 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** — clauses `<AGENT>-<SECTION>-<NN>` | **LOCKED v1. Read-only. Never edit.** A clause you believe is wrong is a `drift-register.md` row plus a report, never an edit |
| `agents/<name>/laws/test-plan.md` | The clause-by-clause map: proven (🟩) vs unproven (⬜) | Read it to learn whether what you rely on is *proven* or merely *asserted* |
| `docs/laws/*.md` | Umbrella laws crossing every agent | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Clause **sections** are shared vocabulary:
`IDN` identity · `IN` inputs · `TRG` triggers · `OUT` outputs · **`NEV` prohibitions** ·
`STA` state & effects · **`IDM` determinism & idempotency** · **`ORD` ordering** ·
`FAIL` failure/recovery · `TYP` types · `SEC` security · `DEP` dependencies ·
`OBS` observability · `PERF` performance · `CAP` capabilities · `PARAM` parameters.

For **this** sprint the binding sections are **`IDN`** (who is allowed to write the new facts),
**`NEV`** (what an agent must never write), and **`OBS`**. This sprint adds a new *derived* artifact
over other agents' outputs, so **ownership is the question that decides the design**.

### The rule

1. **Before writing code**, for every element in the map below, open and read its law file(s) — the
   whole file the first time, not a keyword grep.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Also read [`docs/laws/conventions.md`](../laws/conventions.md) (clause-ID scheme, ⬜ → 🟩) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Write the Law reading record** (template at the bottom) **before** your first code change.
5. **If a law contradicts this spec, STOP and report.** A contradiction you surface is a success.
6. **If a law is silent** where you must decide, that silence is a finding: record it and add a
   `drift-register.md` row.
7. Every test for behaviour a clause governs **cites the clause ID in its docstring**.

### Element → law map (read all of these)

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| Wherever the new outcome fact is written (**you must decide the owner — see item 2**) | The owning agent's `laws.md` + `test-plan.md` | `*-IDN-*` enumerates what each agent may write. **A new label written by the wrong agent is a law violation, not a style question** |
| `Recommendation` / `AnalystRun` (read-only here) | `agents/analyst/laws/laws.md` + `test-plan.md` | `ANLZ-IDN-*` — the analyst owns these. You are **reading** them; nothing in this sprint may mutate them |
| `PMRun` / `order_intent_set` (read-only here) | `agents/portfolio_manager/laws/laws.md` + `test-plan.md` | `PM-IDN-*` — the PM owns rejection reasons. Read-only |
| `MarketData` (read-only here) | `agents/provider/laws/laws.md` + `test-plan.md` | `PROV-IDN-*`, `PROV-OUT-*`. **Provider `laws.md` is LOCKED v1 (S69)** |
| `orchestration/packs/trading_graph_vocabulary.json` | `docs/laws/conventions.md` | S143/S144: every new label, edge and prop must be declared or the guard throws **fail-closed on the first write** |

---

## Why this sprint

**Every `SKIP max_positions` is a discarded experiment, and we have been discarding them nightly.**

Measured 2026-08-06 on `sched-2026-08-03/04/05`: the analyst produced a `buy` for **MSFT** on three
consecutive nights. The PM rejected all three on `max_positions` because the book is full at ten.
**There is no record anywhere of whether MSFT would have been a good pick.** The information the
project most needs — *is the selection any good?* — is being thrown away by a capital constraint that
has nothing to do with selection quality.

[DL-93](../design-log.md) records the operator's framing, and it is the premise of this sprint:

> *"We are not at the trading stage. Far from it. We are still in development… the attention is on
> the SELECTION PROCESS. We are trying to predict the future at the moment, not make money. So even
> 1 share of a profitable stock is better than 10 fully exhausted purchase power."*

This is also a principle the project already holds and has only ever applied to *models*:
[`build-plan.md:26`](../build-plan.md) — *"Advisory before binding. ML and any non-deterministic
component ships shadow"* — and [`build-plan.md:128`](../build-plan.md) defines a
`paper → broker-shadow → live-manual` ladder. The forecaster runs shadow predictions with an IC
scorecard today. **The selection decision itself has never been shadowed.** [DL-09](../design-log.md)
(still `DRAFT` since 2026-06-22) proposed exactly this shape for scanner *filters*. This sprint is
DL-09 generalised from filters to recommendations.

**Why now, and why it outranks the sizing work:** DL-93 leaves open whether to resize positions or
reintroduce a mechanical loss exit. **Both decisions are currently guesses**, because nothing
measures whether the picks are right. The scorecard is the instrument those decisions need, and it
costs no capital and reverses no ADR.

---

## The opportunity, precisely — this is mostly a join, not instrumentation

The raw material already exists. **Measured 2026-08-06 against the live Postgres graph:**

| Label | Count | Carries |
| --- | --- | --- |
| `Recommendation` | **163** | `action`, `confidence`, `technical_score`, `quant_metrics`, `ticker` |
| `AnalystRun` | 26 | `created_at`, `recommendation_set`, `source_scan_run_id`, `held_count`, `position_book_status` |
| `PMRun` | 26 | `created_at`, `approved_count`, `rejected_count`, `order_intent_set` — **including `rejected[].reason`** |
| `MarketData` | 26 | `snapshot` (≈41 daily bars per ticker), `tickers`, `window_end` |

So **163 decisions and 26 price snapshots are already on disk**. A first scorecard can be produced by
**backfill over existing data**, without waiting a single night for new runs. That is the shape of
this sprint: derive, do not instrument.

### 🪤 The trap that decides the design

**`Recommendation` carries no price and no timestamp.** Measured — its full prop set is exactly:

```text
action · confidence · exit_trigger · quant_metrics · technical_score · ticker
```

There is **no `created_at`** and **no reference price**. You therefore cannot order recommendations in
time, or price them, from the `Recommendation` node alone. Both must come from the join:

```text
Recommendation --(belongs to)--> AnalystRun.created_at        (when)
AnalystRun --source_scan_run_id--> ScanRun --> MarketData.snapshot   (price at decision time)
AnalystRun.run_id  ==  PMRun.source_analyst_run_id            (what the PM then did with it)
```

**Do not "fix" this by mutating `Recommendation`.** The graph is **append-only at the property
level** — `kernel/graph_support.py` raises `ValueError: property 'X' cannot be overwritten` on a
changed value. Adding a prop to *existing* nodes is not possible. The outcome is a **new fact**, not
an edit (item 2).

---

## What ships (spec)

> Fill in the `**Result:**` line under each item as you complete it. Results go in this file.

### 1 · A decision-time reference price for every recommendation

Derive the price each recommendation was made at, from the run's own `MarketData.snapshot` — the
close of the last bar at or before the analyst run's as-of date.

- **Source of truth is the run's own snapshot**, not a fresh vendor call. The point is to price the
  decision with the evidence the decision was actually made on (ADR-0016's one-run-one-evidence
  shape). A later vendor fetch would silently re-price history.
- If a ticker has no usable bar in that run's snapshot, the recommendation is **`unpriceable`** and
  must be counted and reported as such — **never silently dropped**. A scorecard that quietly
  excludes rows it could not price is a scorecard that flatters itself.

**Result:**

### 2 · One outcome fact per recommendation per horizon — and decide its owner from the law

Write a new derived fact carrying: the recommendation it scores, its reference price, the horizon,
the forward price, the forward return, and its **disposition** (item 3).

- **You must decide which agent owns this label and justify it from `*-IDN-*` clauses**, then record
  the reasoning in the Law reading record. The reporter is the obvious candidate (it already projects
  completed runs), but **verify against `RPT-IDN-*` rather than assuming** — if the reporter's
  constitution does not admit the label, say so and propose the owner that does. **If no existing
  agent may lawfully write it, that is a finding: stop and report, do not invent an owner.**
- **Append-only, one immutable fact per (recommendation, horizon).** Re-running must merge to the
  same node with identical values, never overwrite. A horizon that has not elapsed yet writes
  **nothing** — absence is the honest representation of "not yet knowable".
- Horizons are `tunable(..., why=...)`, not bare literals. Suggested 1, 5 and 20 trading days; take a
  better set if you can justify it.

**Result:**

### 3 · Disposition: why the pick did or did not become a position

Each outcome fact records what actually happened to that recommendation:

| Disposition | Meaning |
| --- | --- |
| `taken` | the PM approved it and it reached the broker |
| `blocked_capacity` | rejected on `max_positions` — **the discarded experiments** |
| `blocked_other` | rejected for any other PM reason (carry the reason string) |
| `not_actionable` | a `hold` on a held name, or any recommendation that was never a candidate for an order |

Source the reason from `PMRun.order_intent_set.rejected[].reason` — **measured present**, joined via
`PMRun.source_analyst_run_id == AnalystRun.run_id`. Do not re-derive the reason by re-running PM
logic; read the recorded fact.

**Result:**

### 4 · Backfill the 26 runs that already exist

A script that walks existing `AnalystRun`s and produces outcome facts for every horizon that has
already elapsed.

- **Idempotent**: a second run writes nothing new and raises nothing.
- Report counts: recommendations seen, priced, unpriceable, outcomes written, horizons not yet
  elapsed.
- This is what makes the sprint pay off immediately instead of in twenty trading days.

**Result:**

### 5 · The scorecard — and the one cut that matters

A read-only report (script + a `RecommendationOutcome`-driven projection) showing, per horizon:

- hit rate and mean/median forward return, **split by `action`** (`buy` vs `hold`);
- the same, **bucketed by `confidence`** — the question behind the whole thing is whether confidence
  is *calibrated*, i.e. does a 0.62 outperform a 0.55;
- 🎯 **the same, split by `disposition`** — this is the cut the sprint exists for. It answers
  *"are the picks we could not afford better or worse than the ones we took?"* If
  `blocked_capacity` picks outperform `taken` ones, the capital constraint is actively costing
  selection quality and DL-93's resize decision is settled by evidence rather than argument.
- `n` alongside every statistic, and **`unpriceable` counted in the output**. With 163
  recommendations the buckets will be small; a scorecard that hides its sample size invites exactly
  the over-reading this sprint exists to prevent.

**Result:**

### 6 · Declare every new label, edge and prop in the vocabulary

S143 built the write-time guard; S144 found enabling it would have thrown on the first real write
because two edges were undeclared. The guard is **enabled on the fleet** and fails closed.

- Add the new label, its edges and its property shape to
  [`orchestration/packs/trading_graph_vocabulary.json`](../../orchestration/packs/trading_graph_vocabulary.json).
- Re-run `scripts/vocabulary_coverage.py` and `scripts/vocabulary_signatures.py`; paste the output
  into the closeout.
- ⚠️ **The pack and the image must move together at deploy** — a target on new code with a stale pack
  raises `VocabularyError` on its first write (the S148 stall, DL-85).

**Result:**

### 7 · Prove the checks can fail (DL-70)

No presence assertions. Every test plants the violation and requires the failure — see the test plan.

**Result:**

---

## Test plan — every test I want, and why

**Ground rules.** Cite clause IDs where a clause governs the behaviour. **Plant the violation and
require the failure.** If you conclude one of these is wrong or untestable, say so with a reason —
do not silently drop it.

### A · Pricing

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | reference price comes from the run's own snapshot | a run whose snapshot close differs from a later bar | the reference price is the **run's** close, not the later one — proves history is not silently re-priced |
| A2 | a ticker missing from the snapshot is `unpriceable`, not dropped | a recommendation whose ticker has no bar | it is counted as `unpriceable` and **appears in the report**; assert the count is non-zero before asserting the behaviour |
| A3 | the as-of boundary is respected | bars on both sides of the run's as-of date | the bar chosen is the last at-or-before as-of; a later bar is never used |

### B · Outcome facts

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| B1 | one immutable fact per (recommendation, horizon) | write the same outcome twice | second write merges to the same node, no duplicate, **no `ValueError`** |
| B2 | 🪤 an un-elapsed horizon writes nothing | a recommendation 2 days old with a 20-day horizon | **zero** outcome nodes for that horizon — absence, not a zero-valued row |
| B3 | the fact stays inside declared labels | run the backfill | the set of labels written is a subset of the owning agent's `*-IDN-*` enumeration. **Cite the clause.** This is the test that catches an accidental law violation |
| B4 | nothing upstream is mutated | run the backfill over a fixture graph | `Recommendation`, `AnalystRun`, `PMRun` and `MarketData` are **byte-identical** afterwards |

### C · Disposition

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| C1 | 🎯 a `max_positions` rejection is `blocked_capacity` | a PMRun whose `rejected[]` carries `reason='max_positions'` | the outcome is `blocked_capacity`. **This is the regression test** — it is the row the whole sprint exists to count |
| C2 | another rejection reason is not miscounted | `reason='hold_recommendation'` | `blocked_other` carrying the reason string, **not** `blocked_capacity` |
| C3 | an approved pick is `taken` | an approved intent | `taken` |
| C4 | disposition is read, not re-derived | a PMRun whose recorded reason contradicts what PM logic would produce today | the **recorded** reason wins — proves history is not rewritten by current code |

### D · Backfill and scorecard

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| D1 | backfill is idempotent | run it twice | second pass writes nothing, raises nothing |
| D2 | the scorecard reports `n` and `unpriceable` | a fixture with a known unpriceable row | both appear in the output |
| D3 | the disposition split is correct | fixture with known `taken` and `blocked_capacity` rows and different returns | the two groups report their own means — plant a difference and require the report to show it |
| D4 | every new edge/label is declared | the new edge | the vocabulary guard accepts it; then **plant an undeclared edge and require rejection** — otherwise you have only proven the guard is quiet |

---

## Explicit non-goals

- **No trading behaviour change of any kind.** No sizing change, no `max_positions` change, no exit
  policy change, no order placed, cancelled or modified. This sprint **observes**.
- **No ADR-0017 reversal.** "Sell what is losing" is an open question in DL-93 and is **not** decided
  here. Do not implement a mechanical loss exit.
- **No broker calls.** Everything is derived from facts already in the graph.
- **Not a backtester.** No simulated portfolio construction, no compounding, no transaction costs, no
  slippage model. One recommendation → one forward return. Resist the urge; a backtester is a
  different sprint with different failure modes.
- **No changes to `Recommendation`, `AnalystRun`, `PMRun` or `MarketData`.** Read-only, all four.
- **No `laws.md` edits.** LOCKED v1. Findings go to `drift-register.md`.

### The road not taken (LAW-06)

Options weighed and **ruled out** — record any further ones you rule out:

- **Fractional / 1-share live sizing** to fit more picks in the real account. Genuinely useful and
  **complementary**, but it is a *capital* answer to a *measurement* question: it would still cap
  breadth at whatever the account affords, still carry margin risk, and still take twenty trading
  days to say anything. Recorded in DL-93; not this sprint.
- **Multiple portfolios / sub-accounts** to multiply purchasing power. Rejected: firms use separate
  books to isolate *strategies* and their attribution, not to dodge a capital cap. It multiplies
  reconciliation, credential scope and divergence surface by N to answer a question a shadow book
  answers with no capital at all.
- **Selling holdings to free slots.** Rejected on two grounds: `EXEC-IDN-01` makes execution the sole
  broker interface so a hand-fired order writes no lineage, and — more importantly — forcing exits to
  create room would **contaminate the very measurement**, mixing "selection quality" with "effects of
  forced churn".
- **Rank displacement** (sell the worst-ranked holding when a better signal arrives). The correct
  long-run answer to a full book, and better than an absolute P&L rule because it is *relative*. But
  it needs a trustworthy ranking, which is what this sprint produces. **Sequenced after, not
  instead.**
- **Re-pricing history from a fresh vendor call** instead of the run's own snapshot. Rejected: it
  would silently re-price decisions against evidence that did not exist when they were made, and
  would burn Tiingo's 50 req/hr budget re-deriving what is already stored.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0** (hardening row M), then merge
   to `main` locally and push. **PRs are not required** (DL-56).
2. **Run the backfill and read the first scorecard.** With 163 recommendations across 26 runs, the
   1-day and 5-day horizons should populate immediately; 20-day will be sparse.
3. **Report the `taken` vs `blocked_capacity` split to the operator.** That number is the input to
   DL-93's open decision and the reason this sprint was pulled forward.
4. A fleet retag is **only** required if the new fact is written by a deployed agent rather than by a
   backfill script. State which, explicitly, in the return notes — and if a retag is needed, remember
   **image and vocabulary pack move together**.
5. Record the functionality check in [`docs/laws/functionality-checks.md`](../laws/functionality-checks.md).

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds, never a bare literal.
- Faults, not silent failure — `kernel.fault_boundary`, errors redirected with provenance.
- `make ci` **all 11 steps** green, **100.00 % coverage floor**, before handback. Never lower it.
  **Never measure the gate through a pipe** — `make ci | tail` reports `tail`'s exit code (row S).
  Redirect to a file and read the file.
- Version bump in `pyproject.toml` to **0.87.00** (feat → MINOR), `uv.lock` staged with it.
- Any law clause your tests cover cites the clause ID in the test docstring.
- If `main` has moved when you finish: merge `main` into the branch, resolve, re-run `make ci`, and
  **say so in the return notes** (DL-48).
- Secrets never through the worktree — chat or gitignored `.env` only.

---

## Handover notes — read these before you start

**Traps that have cost this repo real time. Every one is measured, not folklore.**

1. **`Recommendation` has no price and no `created_at`.** Measured prop set:
   `action, confidence, exit_trigger, quant_metrics, technical_score, ticker`. Everything temporal or
   monetary must come from the join through `AnalystRun` → `MarketData`. Do not attempt to add props
   to existing `Recommendation` nodes.
2. **The graph is append-only at the property level.** `kernel/graph_support.py` raises
   `ValueError: property 'X' cannot be overwritten` when merging a node with a *changed* value for an
   existing prop. "Update the record" is not expressible — append a new fact. This is the rule that
   made a position-keyed `CloseDecision` unbuildable (ADR-0015 §2's amendment); do not rediscover it.
3. **The vocabulary guard is live and fails closed.** An undeclared label, edge or prop raises
   `VocabularyError` on the **first write**, in production, not in CI. Declare before you write.
4. **Never filter positions on raw `status == "open"`.** Superseded and broker-absent nodes keep
   `status="open"` by design; `contracts/positions.py::is_active_position_node` is the only correct
   filter. A prior audit produced a red-severity defect that did not exist by getting this wrong —
   read [DL-73](../design-log.md)'s retraction. This sprint should not need position state at all; if
   you find yourself reaching for it, stop and ask why.
5. **The store is Postgres (Neon), not Neo4j.** ADR-0014. `POSTGRES_DSN` from `.env`. A helper script
   run from outside the repo root silently gets the **in-memory** store and every count reads `0` —
   if your backfill reports zero recommendations, this is why, and the data is fine.
6. **Tests must never transact with production.** S159/DL-89: an autouse conftest guard blocks live
   Service Bus sends and derives from `BaseException` so a `fault_boundary` cannot swallow it. Do not
   weaken it, and do not add an opt-out.
7. **A worktree has no `.env`.** Any proof that depends on live graph data is vacuous there. Say
   which tree you ran in.
8. **Small samples.** 163 recommendations across 26 runs, most of them `hold` on the same ten held
   names. The `buy` bucket is *tiny*. Report `n` everywhere and resist drawing conclusions in the
   closeout — the sprint's job is to build the instrument, not to interpret the first reading.

---

## Handback contract — MANDATORY

**Append your results INSIDE this file, at the bottom, in the placeholder sections below.**
Not a separate report file. Not chat-only.

1. Fill the **Law reading record** *before* your first code change.
2. Fill the `**Result:**` line under **each** of the seven spec items, in place.
3. Fill the **Test plan results** table — one row per test, with its final name and status. A test
   you chose not to write needs a reason, not a blank.
4. Fill the **Closeout — evidence** block with real command output pasted in: `make ci` counts,
   `make gate-ran`, the remote gate results, the planted-violation runs, the vocabulary script output,
   and **the first scorecard**.
5. Fill the **Return notes** block, including the ownership decision for the new label and whether a
   fleet retag is required.
6. State any success factor you did **not** meet plainly, as "verified failing" or "not done"
   (LAW-02 — a proven failure is a valid handback, a silent gap is not).

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? (yes + what / no) |
| --- | --- | --- | --- |
| Owner of the new outcome label | | | |
| `Recommendation` / `AnalystRun` (read-only) | | | |
| `PMRun` / `order_intent_set` (read-only) | | | |
| `MarketData` (read-only) | | | |
| `trading_graph_vocabulary.json` | | | |

**Contradictions found between a law and this spec** (a contradiction is a success — name it):

**Laws found silent where a decision was needed** (each needs a `drift-register.md` row):

**Clauses that were ⬜ unproven in `test-plan.md` and are now proven by this sprint's tests:**

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | | | | |
| A2 | | | | |
| A3 | | | | |
| B1 | | | | |
| B2 | | | | |
| B3 | | | | |
| B4 | | | | |
| C1 | | | | |
| C2 | | | | |
| C3 | | | | |
| C4 | | | | |
| D1 | | | | |
| D2 | | | | |
| D3 | | | | |
| D4 | | | | |

**Tests added beyond the plan:**

---

## Closeout — evidence

**Tree the proofs ran in (and `.env` present?):**

**Files changed:**

**Proven (LAW-02):**

**The first scorecard (paste it):**

**Not met / verified failing:**

---

## Return notes
