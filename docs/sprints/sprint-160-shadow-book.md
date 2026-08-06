<!-- Agent: planning | Role: sprint handover -->
# Sprint 160 — Every rejected pick is a discarded experiment: the shadow book

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-160-shadow-book`
**Status:** SPEC **revision 2** — makes selection quality measurable without spending capital.
🛑 **Revision 1 was stopped at the law-first gate and the stop was correct** — no locked
constitution owns a `RecommendationOutcome` label. Revision 2 removes the label entirely: the
scorecard is a **read-only derivation that persists nothing**, joining `accept.py` /
`trace_run.py` / `observatory.py`, which write zero nodes and are governed by no agent law.
**Items 2 and 6 and tests B1/B3 changed. Re-read them before starting.**
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
| ~~Wherever the new outcome fact is written~~ — **removed in revision 2: nothing is written** | `agents/reporter/laws/laws.md` (read anyway, to understand *why* the label was refused) | `RPT-IDN-02` enumerates exactly `Snapshot`, `TradeNarrative`, `ReportSnapshotResult`; `RPT-NEV-02` restricts the reporter to its own labels. **Verified 2026-08-06.** This is the clause pair that blocked revision 1 and produced the better design |
| `Recommendation` / `AnalystRun` (read-only here) | `agents/analyst/laws/laws.md` + `test-plan.md` | `ANLZ-IDN-*` — the analyst owns these. You are **reading** them; nothing in this sprint may mutate them |
| `PMRun` / `order_intent_set` (read-only here) | `agents/portfolio_manager/laws/laws.md` + `test-plan.md` | `PM-IDN-*` — the PM owns rejection reasons. Read-only |
| `MarketData` (read-only here) | `agents/provider/laws/laws.md` + `test-plan.md` | `PROV-IDN-*`, `PROV-OUT-*`. **Provider `laws.md` is LOCKED v1 (S69)** |
| `orchestration/packs/trading_graph_vocabulary.json` | `docs/laws/conventions.md` | S143/S144: every new label, edge and prop must be declared or the guard throws **fail-closed on the first write** |

---

## Why this sprint

**Every `SKIP max_positions` is a discarded experiment, and we have been discarding them nightly.**

Measured 2026-08-06 on `sched-2026-08-04/05`: the analyst produced a `buy` for **MSFT** on **two** consecutive nights (confidence 0.611 and 0.619) and the PM rejected **both** on `max_positions`. **Correction (2026-08-06):** revision 1 of this doc said *three* nights, `sched-2026-08-03/04/05`. That was wrong and the shadow book's own output caught it — the live graph holds **2** `blocked_capacity` dispositions, not 3. Verified directly: on `sched-2026-08-03` the analyst produced **zero** buys and MSFT was not in the recommendation set at all, so there was nothing to block. Two nights of that claim were traced; the third was extrapolated and never checked. The PM rejects because the book is full at ten.
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

**Result (revision 1 — BLOCKED, kept as evidence):** Not done — stopped before implementation at
the law-first ownership gate. No pricing code was written.

**Result (revision 2):** Implemented in `orchestration/shadow_book_prices.py`. Each of the 163 live
`Recommendation` facts joins to its own `AnalystRun` and that run's `MarketData`; the reference is
the final close at or before `AnalystRun.created_at`. Missing reference or forward bars produce an
explicit `unpriceable` row. Live result: 163/163 reference-priced; five horizon rows were
unpriceable rather than dropped.

### 2 · ~~One outcome fact per recommendation per horizon~~ → **a read-only derivation that persists nothing** (REVISED 2026-08-06)

> **🛑 This item was rewritten after the law-first gate blocked the original.** The blocked handback
> below is correct and is kept verbatim — it is the evidence for the revision, not a failure to
> repair. **Revision 2 supersedes it: there is no new label, no owner to decide, and no law
> amendment needed.** Read *"Why the label was wrong"* below before implementing.

**What ships instead:** a **read-only derivation** — a domain module plus a script — that computes
each recommendation's reference price, forward price, forward return and **disposition** (item 3) on
demand, and **writes nothing to the graph**.

- **No `merge_node`, no `add_edge`, no new label, no vocabulary change.** Verified 2026-08-06:
  `scripts/accept.py`, `scripts/trace_run.py` and `scripts/observatory.py` each contain **zero**
  `merge_node`/`add_edge` calls. The acceptance verdict and the 8-stage trace — both load-bearing
  artifacts — are already derived this way and governed by no agent law. This sprint joins that
  pattern rather than inventing a new one.
- **The derivation is reproducible by construction**, which is why persisting it would add nothing:
  every input is already an immutable graph fact (`MarketData.snapshot` for both prices,
  `PMRun.order_intent_set` for the disposition). A stored outcome could only ever *disagree* with
  the facts it was derived from — a stale copy is a liability, not lineage.
- A horizon that has not elapsed yet is **reported as such and excluded from statistics** — never
  imputed, never zero-filled.
- Horizons are `tunable(..., why=...)`, not bare literals. Suggested 1, 5 and 20 trading days; take a
  better set if you can justify it.

**Result (revision 1 — BLOCKED, kept as evidence):** Verified failing — no existing locked agent
constitution lawfully owns the required new outcome label. Reporter is the closest conceptual owner
(`RPT-IDN-01`), but `RPT-IDN-02` enumerates only `Snapshot`, `TradeNarrative`, and
`ReportSnapshotResult`, and `RPT-NEV-02` allows only reporter owned-label writes. Forecaster,
researcher, and curator were also read; their `*-IDN-02` owned-label lists do not include this
derived recommendation-outcome fact. `DRIFT-034` filed; no fact writer implemented.

**Result (revision 2):** Implemented as a read-only orchestration derivation plus
`scripts/shadow_book.py`. It returns one in-memory row per `(Recommendation, horizon)` with
reference price, forward price/return, disposition and explicit status. It calls no graph write
method and persists no derived copy. Default horizons are justified tunables at 1, 5 and 20 trading
days; confidence uses a justified 0.05 scorecard bucket width.

#### Why the label was wrong — the blocker was the law catching a design error

Independently verified 2026-08-06: `RPT-IDN-02` does enumerate exactly `Snapshot`,
`TradeNarrative`, `ReportSnapshotResult`, and `RPT-NEV-02` does restrict the reporter to its own
labels. **The stop was correct and the spec was wrong**, in a way worth naming because it is the
second time in two days that a spec of mine asserted its way past something it had not checked:
revision 1 told the implementer to *"decide which agent owns this label"* while taking for granted
that **some** agent should. Nobody should — because **the fact should never have been persisted at
all.**

Every input to the outcome is already an immutable graph fact. The forward return is a *computation
over* those facts, not a new observation about the world. Storing it creates a second copy that can
go stale and disagree with its own inputs, which is precisely the failure ADR-0015 §1's amendment
recorded when the monitor was writing `pnl_cents`: *"this graph records facts, it does not hold
mutable records."*

**This is the law book doing the job DL-74's trial claims it does** — a law-first read stopped a
design error before any code was written, and the error was in the spec, not in the law. That is a
success for the rule, and it is recorded as one.

**DRIFT-034 stays open**, deliberately. Routing around the gap does not close it: the law book has
no home for a *durable* cross-agent derived artifact, and the next thing that genuinely needs to
persist one will hit the same wall. It belongs in the next law-amendment cycle (the S152 shape), not
smuggled into this sprint.

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

**Result (revision 1 — BLOCKED, kept as evidence):** Not done — disposition derivation depends on
the blocked `RecommendationOutcome` writer. No PM history was rewritten or re-derived.

**Result (revision 2):** Implemented from recorded `PMRun.order_intent_set` only:
`taken`, `blocked_capacity`, `blocked_other` with its reason, or `not_actionable`. The current live
graph contains `taken=46`, `blocked_capacity=2`, `blocked_other=115`, `not_actionable=0` across 163
recommendations. The earlier handover narrative said three MSFT capacity blocks; the current graph
contains two, on analyst as-of dates 2026-08-04 and 2026-08-05. No PM logic was re-run.

### 4 · Backfill the 26 runs that already exist

A script that walks existing `AnalystRun`s and produces outcome facts for every horizon that has
already elapsed.

- **Idempotent**: a second run writes nothing new and raises nothing.
- Report counts: recommendations seen, priced, unpriceable, outcomes written, horizons not yet
  elapsed.
- This is what makes the sprint pay off immediately instead of in twenty trading days.

**Result (revision 1 — BLOCKED, kept as evidence):** Not done — backfill was not implemented or run
because there is no lawful owner for the new outcome label.

**Result (revision 2):** The read-only derivation was run from
`C:\Users\yury_\Downloads\project\trading-agents` against `PostgresGraphStore`: 163 recommendations
produced 489 horizon rows, of which 263 were scored, five were unpriceable and 221 had not elapsed.
Repeated fixture derivation returned byte-equal rows and identical per-label node/edge censuses;
there is no outcome-writer count because revision 2 writes zero facts.

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

**Result (revision 1):** Not done — scorecard was not implemented or run because the underlying
outcome facts could not be lawfully written.

**Result (revision 2):** Implemented action, 0.05-wide confidence, and disposition cuts per horizon.
Every statistic carries `n`; every horizon carries total, scored, unpriceable and not-yet-elapsed
counts. The first live scorecard is pasted in Closeout. The `taken` versus `blocked_capacity` cut is
present, but the only elapsed capacity sample is 1-day `n=1`; no conclusion is drawn.

### 6 · ~~Declare every new label, edge and prop in the vocabulary~~ → **assert that nothing is written** (REVISED 2026-08-06)

> Revision 1 required a vocabulary declaration because it wrote a new label. **Revision 2 writes
> nothing, so there is no declaration to make** — and the useful work is proving that claim rather
> than asserting it.

- **Do not touch** [`orchestration/packs/trading_graph_vocabulary.json`](../../orchestration/packs/trading_graph_vocabulary.json).
  A pack change would force image and pack to move together at deploy (the S148 stall, DL-85) for a
  sprint that ships no runtime behaviour at all.
- Instead ship the assertion that keeps this true: a test that runs the full derivation against a
  fixture graph and requires the node and edge counts to be **identical before and after**, per
  label. Plant the violation — add a write, watch it fail — then remove it (test B4/D4).
- **State in the closeout that no fleet retag is required, and why.** A sprint that adds only a
  read-only script changes nothing the fleet runs.
- ⚠️ **The pack and the image must move together at deploy** — a target on new code with a stale pack
  raises `VocabularyError` on its first write (the S148 stall, DL-85).

**Result (revision 1 — BLOCKED, kept as evidence):** Not done — vocabulary was not changed because
declaring a label before a lawful owner would create a deployable write path the law book does not
allow.

**Result (revision 2):** `trading_graph_vocabulary.json` is untouched. B4 runs the full derivation
and renderer over a fixture carrying every joined label plus an unrelated label, then requires
per-label node and per-signature edge counts to be identical. A planted `merge_node` added
`PlantedShadowWrite=1` and made B4 fail; after removal B4 passed. No fleet retag is required because
the delivered capability is an operator-run read-only script and changes no deployed agent.

### 7 · Prove the checks can fail (DL-70)

No presence assertions. Every test plants the violation and requires the failure — see the test plan.

**Result (revision 1 — BLOCKED, kept as evidence):** Not done — no tests were written because the
sprint stopped at the pre-code law gate.

**Result (revision 2):** Added 23 focused test cases at 100.00% branch coverage. The B4 planted write
was observed failing on the exact added label count before removal; malformed/orphan recommendation
joins, invalid horizons, invalid confidence width, missing bars and differing disposition returns
also plant the violations they are meant to catch.

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

### B · The derivation writes nothing (REVISED 2026-08-06 — B1/B3 are gone with the label)

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| B1 | ~~one immutable fact per (recommendation, horizon)~~ | — | **Dropped in revision 2.** No fact is written, so there is nothing to de-duplicate |
| B2 | 🪤 an un-elapsed horizon is excluded, not imputed | a recommendation 2 days old with a 20-day horizon | it is **reported as not-yet-elapsed and excluded from the statistics** — never zero-filled, never counted as a 0% return. Assert the exclusion count is non-zero before asserting the statistics |
| B3 | ~~the fact stays inside declared labels~~ | — | **Dropped in revision 2.** Replaced by B4, which is the stronger claim: *no* label is written at all |
| B4 | 🎯 **the derivation writes nothing whatsoever** | run the full derivation over a fixture graph, then **plant a write and require the test to fail** | node **and** edge counts identical before/after, per label — `Recommendation`, `AnalystRun`, `PMRun`, `MarketData` and every other label unchanged. **This is the test that replaces the whole ownership question**, and it is worthless until it has been watched failing |

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
- **Persisting the outcome as a graph fact** (revision 1's design). **Ruled out 2026-08-06 after the
  law-first gate refused it.** Two independent reasons, and the second is the real one:
  **(a)** no locked constitution owns such a label — `RPT-IDN-02` enumerates three labels and
  `RPT-NEV-02` forbids the rest, so it would have required a law-amendment cycle;
  **(b)** *it should not be stored regardless.* Every input is already an immutable fact, so the
  outcome is a computation, not an observation — and a stored copy can only ever drift from the
  facts it came from. That is the mistake ADR-0015 §1's amendment already recorded when the monitor
  was writing `pnl_cents`. **The law stopped a design error, not just a paperwork gap.**
- **Amending a locked `laws.md` to create an owner.** Rejected for this sprint: it is a
  law-amendment cycle (the S152 shape) in its own right, and doing it here would have bought a
  worse design at a higher price. DRIFT-034 keeps the underlying gap visible for that cycle.

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
| Owner of the new outcome label | `agents/reporter/laws/laws.md` + `test-plan.md`; also read `agents/forecaster/laws/laws.md` + `test-plan.md`, `agents/researcher/laws/laws.md` + `test-plan.md`, `agents/curator/laws/laws.md` + `test-plan.md` as alternate measurement owners | `RPT-IDN-01`, `RPT-IDN-02`, `RPT-NEV-02`, `RPT-OBS-01`; `FORE-IDN-01`, `FORE-IDN-02`; `RES-IDN-01`, `RES-IDN-02`; `CUR-IDN-01`, `CUR-IDN-02` | Yes — stopped before code. Reporter is conceptually closest, but no locked `*-IDN-02` owned-label enumeration includes `RecommendationOutcome`. |
| `Recommendation` / `AnalystRun` (read-only) | `agents/analyst/laws/laws.md` + `test-plan.md` | `ANLZ-IDN-01`, `ANLZ-IDN-02`, `ANLZ-NEV-04`, `ANLZ-STA-02`, `ANLZ-OBS-01` | No — confirms these nodes are read-only for this sprint and must not gain price/time properties. |
| `PMRun` / `order_intent_set` (read-only) | `agents/portfolio_manager/laws/laws.md` + `test-plan.md` | `PM-IDN-01`, `PM-IDN-02`, `PM-OUT-03`, `PM-NEV-01`, `PM-NEV-04`, `PM-OBS-01` | No — confirms rejection reasons are PM-owned facts to read, not re-run or reinterpret. |
| `MarketData` (read-only) | `agents/provider/laws/laws.md` + `test-plan.md` | `PROV-IDN-01`, `PROV-IDN-03`, `PROV-OUT-01`, `PROV-OUT-04`, `PROV-OUT-05`, `PROV-NEV-06`, `PROV-NEV-07`, `PROV-OBS-01`, `PROV-OBS-03` | No — confirms the run snapshot is the evidence source and missing prices must remain explicit, not fabricated. |
| `trading_graph_vocabulary.json` | `docs/laws/conventions.md`; `docs/laws/drift-register.md` | conventions §2, §3, §7, §9; `DRIFT-034` | Yes — vocabulary must not be widened until the owning law is amended, otherwise the first write path would be deployable but unlawful. |

**Revision 2 continuation — recorded before the first source-code change (2026-08-06):**

| Element | Law file(s) re-read | Clauses that bind it | Did reading change your approach? (yes + what / no) |
| --- | --- | --- | --- |
| Read-only outcome derivation | `agents/reporter/laws/laws.md`; revision-2 items 2 and 6 | `RPT-IDN-02`, `RPT-NEV-02` | Yes — the derivation is orchestration/tooling like `accept.py`, `trace_run.py`, and `observatory.py`: it owns no label and calls no graph write method. |
| `Recommendation` / `AnalystRun`, `PMRun`, `MarketData` inputs | analyst, portfolio-manager, and provider `laws.md` + `test-plan.md` files listed above | clauses listed above remain binding | No — all four inputs remain read-only; pricing and disposition are reconstructed only from their recorded payloads and lineage. |
| Vocabulary and fleet delivery | `docs/laws/conventions.md`; revision-2 item 6 and tests B1/B3/B4 | conventions §2, §3, §7, §9; `DRIFT-034` | Yes — B1 and B3 are dropped, B4 proves zero writes by requiring per-label node and edge censuses to remain identical. The vocabulary pack must not change and no fleet retag is required. |

Revision 2 resolves the implementation contradiction by removing the durable artifact. Stale
revision-1 phrases elsewhere in this handover that say "outcome fact", "writes", or "vocabulary"
are superseded by revised items 2 and 6 and B4; they do not authorize persistence. `DRIFT-034`
remains open because the general durable cross-agent-artifact ownership gap still exists, even
though this sprint no longer needs to decide it.

**Contradictions found between a law and this spec** (a contradiction is a success — name it):

Implementing S160 as written would contradict the current locked ownership enumerations: `RPT-IDN-02`
does not list `RecommendationOutcome`, and `RPT-NEV-02` allows the reporter to write only its own
labels. The other plausible measurement agents also have closed owned-label lists that exclude this
fact. Per the MUST RULE, implementation stopped before code.

Revision 2 removed that implementation contradiction by removing the write. The retained
revision-1 phrases that still describe an outcome fact or vocabulary write are historical text and
are superseded by revised items 2 and 6; no runtime contradiction remains for the read-only tool.

**Laws found silent where a decision was needed** (each needs a `drift-register.md` row):

No law assigns ownership for an append-only recommendation-outcome fact. `DRIFT-034` added in
`docs/laws/drift-register.md`.

**Clauses that were ⬜ unproven in `test-plan.md` and are now proven by this sprint's tests:**

None — no tests were added because the sprint stopped at the law gate.

Revision 2 proves no previously-unproven agent clause: these are orchestration/tooling tests over
injected read-only graph facts. They deliberately do not claim agent-law coverage.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | not written — law gate stopped before pricing implementation | n/a | not done | n/a |
| A2 | not written — law gate stopped before pricing implementation | n/a | not done | n/a |
| A3 | not written — law gate stopped before pricing implementation | n/a | not done | n/a |
| B1 | not written — law gate stopped before outcome writer implementation | n/a | not done | n/a |
| B2 | not written — law gate stopped before outcome writer implementation | n/a | not done | n/a |
| B3 | law ownership check failed before implementation | n/a | verified failing | `RPT-IDN-02`, `RPT-NEV-02`, `FORE-IDN-02`, `RES-IDN-02`, `CUR-IDN-02` |
| B4 | not written — law gate stopped before backfill implementation | n/a | not done | n/a |
| C1 | not written — law gate stopped before disposition implementation | n/a | not done | n/a |
| C2 | not written — law gate stopped before disposition implementation | n/a | not done | n/a |
| C3 | not written — law gate stopped before disposition implementation | n/a | not done | n/a |
| C4 | not written — law gate stopped before disposition implementation | n/a | not done | n/a |
| D1 | not written — law gate stopped before backfill implementation | n/a | not done | n/a |
| D2 | not written — law gate stopped before scorecard implementation | n/a | not done | n/a |
| D3 | not written — law gate stopped before scorecard implementation | n/a | not done | n/a |
| D4 | not written — law gate stopped before vocabulary implementation | n/a | not done | n/a |

**Tests added beyond the plan:**

None.

### Revision 2 test results

The revision-1 table above is retained as the blocked handback. These are the resumed results.

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a1_reference_price_comes_from_the_run_snapshot` | `orchestration/tests/test_shadow_book_derivation.py` | passed | n/a — read-only tooling |
| A2 | `test_a2_missing_ticker_is_reported_unpriceable` | same | passed | n/a — read-only tooling |
| A3 | `test_a3_reference_price_respects_the_as_of_boundary` | same | passed | n/a — read-only tooling |
| B1 | dropped by revision 2 — no persisted fact exists to deduplicate | n/a | superseded | n/a |
| B2 | `test_b2_unelapsed_horizon_is_excluded_not_imputed` | `orchestration/tests/test_shadow_book_derivation.py` | passed | n/a — read-only tooling |
| B3 | dropped by revision 2 — replaced by the stronger zero-write B4 | n/a | superseded | n/a |
| B4 | `test_b4_full_derivation_preserves_every_node_and_edge_count` | `orchestration/tests/test_shadow_book_scorecard.py` | passed after planted failure | n/a — no agent owns or writes this derivation |
| C1 | `test_c1_max_positions_is_blocked_capacity` | `orchestration/tests/test_shadow_book_disposition.py` | passed | n/a — reads recorded PM fact |
| C2 | `test_c2_other_rejection_is_blocked_other_with_reason` | same | passed | n/a — reads recorded PM fact |
| C3 | `test_c3_approved_recommendation_is_taken` | same | passed | n/a — reads recorded PM fact |
| C4 | `test_c4_recorded_reason_wins_over_current_context` | same | passed | n/a — deliberately does not invoke PM behavior |
| D1 | `test_d1_repeated_derivation_is_identical_and_write_free` | `orchestration/tests/test_shadow_book_scorecard.py` | passed | n/a — read-only tooling |
| D2 | `test_d2_scorecard_reports_n_and_unpriceable` | same | passed | n/a — read-only tooling |
| D3 | `test_d3_taken_and_capacity_buckets_keep_their_own_means` | same | passed | n/a — read-only tooling |
| D4 | revision-1 vocabulary test is inapplicable; revised item 6 is proven by B4 | same as B4 | superseded by passed B4 | n/a — zero new labels/edges |

**Revision 2 tests added beyond the plan:**

- elapsed target date with a missing ticker close is `unpriceable`, not unelapsed;
- empty/non-positive horizon configuration is rejected;
- malformed and orphan `Recommendation` keys fail loudly instead of disappearing from the join;
- missing scan/market lineage remains visible as unpriceable while empty AnalystRuns are ignored;
- PM-absent and PM-unmatched recommendations are `not_actionable`;
- invalid confidence bucket widths are rejected and configured horizons are sorted/de-duplicated.

---

## Closeout — evidence

**Tree the proofs ran in (and `.env` present?):**

`C:\Users\yury_\Downloads\project\trading-agents`, branch `sprint-160-shadow-book`.
`.env` present (`Test-Path .env` -> `True`) but not used; no live graph command was run because the
law-first owner gate stopped implementation.

**Files changed:**

- `docs/sprints/sprint-160-shadow-book.md`
- `docs/laws/drift-register.md`

**Proven (LAW-02):**

```text
git rev-parse --short HEAD
5d9014d

git branch --show-current
sprint-160-shadow-book

Test-Path .env
True
```

Law files read before any code change: reporter, analyst, portfolio_manager, provider, forecaster,
researcher, curator constitutions and test plans; `docs/laws/conventions.md`;
`docs/laws/drift-register.md`; DL-73 and DL-93; ADR-0013, ADR-0016, ADR-0017.

Ownership result: no existing locked agent law currently enumerates the required
`RecommendationOutcome` label. `DRIFT-034` was added as the required drift row.

**The first scorecard (paste it):**

Not done — no scorecard was generated because no lawful outcome writer exists yet.

**Not met / verified failing:**

- Verified failing: lawful owner for the new outcome label is absent from the locked law book.
- Not done: pricing derivation, outcome writer, disposition mapping, backfill, scorecard,
  vocabulary declaration, planted-violation tests, version bump, `uv.lock`, `make ci`, push,
  `make gate-ran`, local merge to `main`.

### Revision 2 closeout

The revision-1 evidence above remains the correct record of the law-first stop. Revision 2 resumed
in the same checkout after `main` was pulled, with the revised spec commit `f7d2680` on the sprint
branch.

**Tree the revision-2 proofs ran in (and `.env` present?):**

`C:\Users\yury_\Downloads\project\trading-agents`, branch `sprint-160-shadow-book`.
`.env` was present and used only for the read-only live Postgres proof. No DSN or credential was
printed. The store was asserted as `PostgresGraphStore`, not the in-memory fallback.

**Files changed by the revision-2 implementation:**

- `orchestration/shadow_book.py`
- `orchestration/shadow_book_join.py`
- `orchestration/shadow_book_prices.py`
- `orchestration/shadow_book_scorecard.py`
- `orchestration/shadow_book_settings.py`
- `scripts/shadow_book.py`
- `orchestration/tests/shadow_book_helpers.py`
- `orchestration/tests/test_shadow_book_derivation.py`
- `orchestration/tests/test_shadow_book_disposition.py`
- `orchestration/tests/test_shadow_book_scorecard.py`
- `pyproject.toml` and `uv.lock`
- this handback and `docs/laws/functionality-checks.md`

The earlier `f7d2680` revision also retains `DRIFT-034` in `docs/laws/drift-register.md`; it remains
open and was not edited by the resumed implementation. No `laws.md` or vocabulary file changed.

**Proven (LAW-02):**

```text
git switch main
git pull --ff-only origin main
Already up to date.
main = 5d9014d

git switch sprint-160-shadow-book
sprint branch = f7d2680 before implementation

live store proof (repo-root .env; DSN not printed)
proof_exit=0
store=PostgresGraphStore
Recommendation=163
AnalystRun=26
PMRun=26
MarketData=26

focused revision-2 suite
23 passed
TOTAL 196 statements, 44 branches, 100.00%

B4 with planted graph.merge_node("PlantedShadowWrite", "s160-b4", {})
FAILED test_b4_full_derivation_preserves_every_node_and_edge_count
node-count difference: PlantedShadowWrite=1

B4 after removing the planted write
1 passed

uv lock
Updated trading-agents v0.86.5 -> v0.87.0

make ci > %TEMP%\s160-make-ci-final.txt 2>&1
make_ci_exit=0
elapsed=211.2s
ruff: passed; format: 922 files already formatted
mypy: Success, 761 source files
import-linter: 4 kept, 0 broken
module size: passed; module headers: passed; law coverage: passed
pytest: 2124 passed, 4 skipped; TOTAL 13983 statements / 2952 branches = 100.00%
pip-audit: No known vulnerabilities found
detect-secrets tracked: Passed
detect-secrets untracked: Passed (10 new files scanned)
```

**The first scorecard (live Postgres, pasted in full):**

```text
SHADOW BOOK SCORECARD
recommendations_seen=163 reference_priced=163 reference_unpriceable=0
outcomes_scored=263 outcomes_unpriceable=5 horizons_not_yet_elapsed=221
dispositions taken=46 blocked_capacity=2 blocked_other=115 not_actionable=0

HORIZON 1 TRADING DAYS
coverage n=163 scored=151 unpriceable=1 not_yet_elapsed=11
| cut | bucket | n | hit_rate | mean_return | median_return |
| --- | --- | ---: | ---: | ---: | ---: |
| all | all | 151 | 61.59% | -0.04% | 0.65% |
| disposition | blocked_capacity | 1 | 0.00% | -1.09% | -1.09% |
| disposition | blocked_other | 105 | 60.00% | 0.03% | 0.46% |
| disposition | taken | 45 | 66.67% | -0.18% | 0.91% |
| action | buy | 40 | 72.50% | 0.79% | 1.19% |
| action | hold | 105 | 60.00% | 0.03% | 0.46% |
| action | sell | 6 | 16.67% | -6.75% | -6.87% |
| confidence | 0.55-0.60 | 4 | 25.00% | -3.55% | -2.62% |
| confidence | 0.60-0.65 | 99 | 64.65% | 0.28% | 0.70% |
| confidence | 0.65-0.70 | 46 | 60.87% | -0.39% | 0.50% |
| confidence | 0.70-0.75 | 2 | 0.00% | -1.06% | -1.06% |

HORIZON 5 TRADING DAYS
coverage n=163 scored=108 unpriceable=4 not_yet_elapsed=51
| cut | bucket | n | hit_rate | mean_return | median_return |
| --- | --- | ---: | ---: | ---: | ---: |
| all | all | 108 | 75.93% | 1.89% | 1.56% |
| disposition | blocked_other | 65 | 76.92% | 1.85% | 1.16% |
| disposition | taken | 43 | 74.42% | 1.94% | 2.50% |
| action | buy | 38 | 73.68% | 1.38% | 2.43% |
| action | hold | 65 | 76.92% | 1.85% | 1.16% |
| action | sell | 5 | 80.00% | 6.17% | 6.19% |
| confidence | 0.55-0.60 | 2 | 100.00% | 3.69% | 3.69% |
| confidence | 0.60-0.65 | 72 | 79.17% | 2.20% | 1.62% |
| confidence | 0.65-0.70 | 32 | 65.62% | 1.11% | 1.18% |
| confidence | 0.70-0.75 | 2 | 100.00% | 1.16% | 1.16% |

HORIZON 20 TRADING DAYS
coverage n=163 scored=4 unpriceable=0 not_yet_elapsed=159
| cut | bucket | n | hit_rate | mean_return | median_return |
| --- | --- | ---: | ---: | ---: | ---: |
| all | all | 4 | 100.00% | 7.09% | 7.59% |
| disposition | taken | 4 | 100.00% | 7.09% | 7.59% |
| action | buy | 4 | 100.00% | 7.09% | 7.59% |
| confidence | 0.60-0.65 | 4 | 100.00% | 7.09% | 7.59% |
```

This is an instrument reading, not a conclusion. The `blocked_capacity` performance cut has only
one elapsed observation, and the 20-day horizon has only four scored recommendations in total.

**Remote gates and hardening row M:**

```text
implementation commit 2865c5e931e928071fdb3f17f098822f09abb1e4
Security Findings run 31074162666: success (gate job success)
CI run 31074162687: success
  quality: success
  security: success
  test: success (100.00% coverage floor enforced)

make gate-ran
GATE PROVEN for 2865c5e931e928071fdb3f17f098822f09abb1e4:
  Security Findings: success
  CI: success
gate_ran_exit=0
```

Verified failing and then repaired: B4 caught the planted write exactly as required. No success
factor remains unmet. The final handback-only documentation commit is pushed and remotely gated
again before the required local fast-forward merge; that latest-HEAD result is returned with the
merged revision because changing this block afterward would itself create a new un-gated HEAD.

---

## Return notes

S160 stopped at the MUST RULE before implementation. Ownership decision: the reporter is the likely
future owner because `RPT-IDN-01` covers graph traversal and projection, but it is not lawful today:
`RPT-IDN-02` does not enumerate `RecommendationOutcome`, and `RPT-NEV-02` permits only reporter-owned
labels. Forecaster/researcher/curator were checked as alternate measurement owners and also do not
own this fact shape.

Fleet retag required: no, not from this blocked branch. No code, vocabulary pack, image, or version
changed. A future implementation will require image and vocabulary pack to move together if the fact
writer is deployed; if it remains a local backfill/reporting script only, state that separately in
that sprint's return notes.

### Revision 2 return notes

There is no new label and therefore no owner decision. The scorecard is a read-only orchestration
derivation, not an agent artifact. `DRIFT-034` stays open exactly as requested: avoiding a durable
cross-agent artifact does not solve the general ownership gap, and no `laws.md` was amended.

Fleet retag required: **no**. The fleet does not run this operator script, the graph vocabulary is
unchanged, and the script makes no graph or broker write. There is therefore no image/pack movement
to coordinate.

The live graph at closeout has 163 actual `Recommendation` nodes and only two recorded
`max_positions` dispositions for MSFT, despite the earlier three-night narrative. One has a scored
1-day return and one is not yet elapsed. The discrepancy is reported rather than repaired because
this sprint is read-only and the sample is too small for a selection-quality conclusion.
