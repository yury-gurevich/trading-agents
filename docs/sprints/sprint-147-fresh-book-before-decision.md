<!-- Agent: planning | Role: sprint handover -->
# Sprint 147 — Never decide on a book nobody reconciled: DL-71 option B

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-147-fresh-book-before-decision`
**Status:** SPEC — closes the **upstream cause** of the 2026-07-27 outage
**Version:** feat → **0.81.00** (MINOR: two middle digits, zeroing the patch group)
**Effort:** M–L
**Decisions:** [DL-71](../design-log.md) option B (this sprint *is* option B) ·
[DL-44](../design-log.md) broker truth · [ADR-0016](../decisions/0016-one-run-one-evidence-both-directions.md)
one run, one evidence set · [ADR-0018](../decisions/0018-decision-validity-same-session-or-dropped.md)
a decision is valid for one session · [DL-57](../design-log.md)/[DL-59](../design-log.md) intent ≠
outcome · [DL-70](../design-log.md) plant violations · [DL-73](../design-log.md) **(RETRACTED —
read it before you audit anything)**

> **Why the version is a MINOR and not a PATCH.** This sprint fixes a defect, but the mechanism is a
> **new cascade stage** plus two new poll triggers — new capability by the CLAUDE.md rule
> (*feat → two middle digits*). `0.80.03` → **`0.81.00`**, patch group zeroed. If you disagree after
> reading the rule, say so in the return notes rather than silently choosing differently.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 4 is done.**

### What the law folders are

This repo is governed by a **law book**. It is not documentation and it is not advisory — it is the
constitution the code is required to satisfy, and it outranks this sprint document.

There are two kinds of law folder, and you must read from both:

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** — numbered clauses with IDs of the form `<AGENT>-<SECTION>-<NN>` | **LOCKED v1. Read-only. Never edit.** A clause you believe is wrong is a drift-register row plus a report, never an edit |
| `agents/<name>/laws/test-plan.md` | The clause-by-clause test map for that agent: which clauses are proven (🟩) and which are unproven (⬜) | Read it to find out whether the behaviour you are changing is currently *proven* or merely *asserted* |
| `docs/laws/*.md` | The **umbrella laws** that cross-cut every agent — conventions, dependencies, drift register, ledger, functionality checks | Same status as agent laws. `drift-register.md` is the **one law-adjacent file you may append to** |

Clause **sections** are shared vocabulary across all agents:
`IDN` identity · `IN` inputs · `TRG` triggers · `OUT` outputs · **`NEV` prohibitions** ·
`STA` state & effects · **`IDM` determinism & idempotency** · **`ORD` ordering** ·
**`FAIL` failure/recovery** · `TYP` types · `SEC` security · `DEP` dependencies ·
`OBS` observability · `PERF` performance · `CAP` capabilities · `PARAM` parameters.

For **this** sprint the binding sections are `IDN` (who exclusively writes what), `TRG` (who is
allowed to trigger whom), `ORD`, `IDM` and `FAIL`. This sprint changes **when things run**, so the
trigger and ordering clauses are the ones that will decide your design.

### The rule

1. **Before writing code**, for **every** element in the map below, open and read its law file(s).
   Read the whole file the first time — not a keyword grep. You are looking for what the agent is
   *forbidden* to do and *who is allowed to trigger it*, which is exactly what a cascade reorder
   touches.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you are about to rely on is
   ⬜ (unproven), say so — you may be the first person to actually test it.
3. Also read the umbrella laws:
   [`docs/laws/conventions.md`](../laws/conventions.md) (clause-ID scheme, ⬜ → 🟩 rules),
   [`docs/laws/dependencies.md`](../laws/dependencies.md) (`DEP-BROKER` governs the Alpaca
   boundary), and [`docs/laws/drift-register.md`](../laws/drift-register.md) (where discovered gaps
   go).
4. **Write the Law reading record** (template near the bottom of this file) into this document
   **before** your first code change. It is the first thing reviewed at handback.
5. **If a law contradicts this spec, STOP and report.** Do not silently follow either one. The law
   is the constitution; this sprint doc is one sprint's opinion and it can be wrong — revision 1 of
   the S146 handover was built on a defect that turned out not to exist. **A contradiction you
   surface is a success, not a blocker.**
6. **If a law is silent** on something you must decide, that silence is itself a finding: record it
   in the Law reading record and add a row to `docs/laws/drift-register.md`.
7. Every test you write for behaviour a clause governs **must cite the clause ID in its docstring**
   (e.g. `"""MON-IDN-02 / MON-TRG-01: ..."""`). Already a CLAUDE.md rule; here it is also how the
   test plan below is checked off.

### Element → law map (read all of these)

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/monitor/reconcile.py` + a new monitor poll path (items 1, 3) | `agents/monitor/laws/laws.md` + `test-plan.md` | **MON-IDN-02 decides this sprint's architecture** — the monitor *exclusively* writes `Position`. `MON-TRG-01`/`MON-TRG-04` decide who may trigger the early reconcile |
| `agents/execution/reconciliation.py` + a new execution poll path (item 1) | `agents/execution/laws/laws.md` + `test-plan.md` + `docs/laws/dependencies.md` | `EXEC-IDN-01` (sole broker interface), `EXEC-IDN-02` (labels it owns — **check whether `BrokerPositionSnapshot` is actually named there**), `EXEC-TRG-01`, `DEP-BROKER` |
| `agents/analyst/poll.py` — the pending predicate (item 2) | `agents/analyst/laws/laws.md` + `test-plan.md` | `ANLZ-TRG-01`/`ANLZ-TRG-03` (the analyst never self-triggers), `ANLZ-IN-03` (empty candidate set behaviour), `ANLZ-IDN-02` |
| `contracts/positions.py` (**read-only** — you import it, you do not change it) | `agents/monitor/laws/laws.md` | Monitor owns `Position` state; `MON-STA-*` explains why `status` stays `"open"` and why `is_active_position_node` is the only correct filter |
| `contracts/resume.py`, `orchestration/resume.py` (item 5) | `agents/supervisor/laws/laws.md` + `docs/laws/conventions.md` | Resume placement is a supervisor-facing contract; adding a stage changes an **index-aligned** tuple (see the trap in item 5) |
| `orchestration/local_pipeline.py`, `orchestration/packs/trading_acceptance.py` (item 5) | `docs/laws/conventions.md` + `docs/laws/functionality-checks.md` | Orchestration has no agent law; umbrella conventions govern it |
| `orchestration/packs/trading_graph_vocabulary.json` (item 6) | `docs/laws/conventions.md` | S143/S144: every new label and edge must be declared or the guard throws on first write |

### What the trial is measuring

S146 ran this same law-first rule as a deliberate trial ([DL-74](../design-log.md)) and it produced
a real result: 4 of 7 elements changed approach, 3 honest "no change", and **DRIFT-024 surfaced
before any code was written**. The rule is retained on that evidence, not out of ceremony.

Answer honestly in the Law reading record, per element: **did reading the law change what you were
going to do?** "No — the intended approach already complied" is a good answer and must be recorded
as such. A record that is vague, or written after the code, defeats the trial and will be treated as
an incomplete handback (DL-48).

---

## Why this sprint

On 2026-07-27 the analyst scored a position book that was **nine hours stale**, decided `MRVL sell`
for a position that had already sold at Monday's open, the PM approved a full exit of a position
that no longer existed, and execution rebuilt the dead position's exit key — which raised
`ValueError: property 'price_cents' cannot be overwritten` and crash-looped the fleet for two hours.

S145 fixed the *crash*. S146 fixed the *silence* around a refused stop. **Neither fixed the reason a
phantom exit was authored in the first place.** That is this sprint, and it is the last open half of
DL-71.

> **Read [DL-73](../design-log.md) and its retraction before you audit anything.** A prior audit of
> this exact area produced a red-severity defect that did not exist, because it filtered `Position`
> nodes on the raw `status == "open"` property instead of using
> `contracts/positions.py::is_active_position_node`. Superseded and broker-absent nodes **stay**
> `status="open"` by design — that is what append-only means. **The position book is correct. Do not
> "fix" reconciliation. Do not close superseded nodes.** If your work makes you want to, you have
> made the same mistake — stop and re-read.

---

## The defect, precisely

The cascade is graph-pull: each agent polls for upstream nodes that lack its own downstream marker
([`orchestration/local_pipeline.py`](../../orchestration/local_pipeline.py) is the readable
statement of the order; in production each agent container runs its own
`kernel.work_loop.work_loop`).

| # | Stage | Reads | Writes |
| --- | --- | --- | --- |
| 1 | provider | `RunRequest` | `MarketData` |
| 2 | scanner | `MarketData` | `ScanRun` |
| 3 | **analyst** | `ScanRun` + **`open_positions(graph)`** | `AnalystRun` |
| 4 | pm | `AnalystRun` | `PMRun` |
| 5 | **execution** | `PMRun` | `Fill`, **fresh `BrokerPositionSnapshot`**, `ExecutionRun` |
| 6 | **monitor** | `ExecutionRun` | `Position` (**reconciled from the snapshot**), `MonitorRun` |
| 7 | reporter | `MonitorRun` | `Snapshot` |

Read stages 3, 5 and 6 together and the defect is structural, not incidental:

- **The truth arrives at stage 5.** `reconcile_run_start`
  ([`agents/execution/reconciliation.py:25`](../../agents/execution/reconciliation.py#L25)) asks the
  broker what is actually held and writes a `fresh` `BrokerPositionSnapshot`.
- **It is adopted at stage 6.** `reconcile_positions_from_latest_snapshot`
  ([`agents/monitor/reconcile.py:33`](../../agents/monitor/reconcile.py#L33)) turns that snapshot
  into the `Position` book — superseding changed quantities, marking sold tickers `broker_absent`.
- **It is consumed at stage 3 — of the *next* run.** `open_positions(graph)`
  ([`agents/analyst/poll.py:77`](../../agents/analyst/poll.py#L77)) feeds `scoring_universe`, which
  is what puts held tickers in front of the analyst at all.

**So every decision this system makes is made against broker truth that is at minimum one full run
old.** On a normal weeknight that is ~24 hours. Across the 07-25/07-26 weekend skips it was **three
days**, and MRVL sold inside that window.

This is not a bug in any one module. Every module named above is behaving exactly as written. The
defect is the **order**, and that is why DL-71 recorded it as an option rather than a fix.

### The three-day-old book, drawn

```text
Fri 07-24 stage 6   monitor reconciles  ->  Position book: MRVL 44 open
Mon 07-27 09:30 ET  MRVL exit fills at the broker  (book still says 44 open)
Mon 07-27 22:30 UTC run starts
          stage 3   analyst reads open_positions() -> MRVL 44   <-- THREE DAYS STALE
                    scores it, decides SELL
          stage 4   PM approves a full exit of a position that does not exist
          stage 5   execution rebuilds the dead position's exit key -> ValueError -> crash loop
                    (the fresh snapshot proving MRVL was gone was written on this very line,
                     nine hours after the fill, and four stages too late to matter)
```

The parenthesis is the whole sprint. **The evidence that would have prevented the decision was
collected in the same run — just after the decision instead of before it.**

---

## What ships (spec)

> Fill in the `**Result:**` line under each item as you complete it. See
> [Handback contract](#handback-contract--mandatory) — results go in this file, not in chat.

### 1 · A head-of-run position sync

Insert a sync step **between the run request and the analyst** that refreshes broker truth and
reconciles the book, so stage 3 reads a book that is minutes old rather than days.

**The architecture is decided by law, not by preference. Verify both clauses yourself before you
build:**

- **`MON-IDN-02`** — the monitor *exclusively* writes `Position` (single-writer rule). So the early
  reconcile **must** be performed by the monitor. The analyst may not reconcile. Execution may not
  reconcile. Do not "just call the helper" from another agent — besides the law, `import-linter`
  forbids agent→agent imports.
- **`EXEC-IDN-01`** — execution is the *sole* broker interface. So the fresh snapshot **must** be
  written by execution. The monitor may not call the broker.

Two agents, each doing only what it already lawfully does, in a new order. Concretely:

- **Execution** gains a **new work source, not a new capability**: a `RunRequest` with no snapshot
  for that run is pending; processing it calls the *existing* `reconcile_run_start` with that
  `run_id`. `EXEC-TRG-01` (invoked by the dispatcher) is the lawful door.
- **Monitor** gains a **new work source, not a new capability**: a run whose fresh snapshot has not
  yet been adopted is pending; processing it calls the *existing*
  `reconcile_positions_from_latest_snapshot` and writes a marker. `MON-TRG-01` (triggered by the
  dispatcher or any authorised caller) is the lawful door; `MON-TRG-04` (never self-triggers) is
  the thing you must not break.
- **The marker should stay inside already-declared labels.** `MON-IDN-02` enumerates exactly what
  the monitor may write, and a new label would put you outside it. The suggested shape is a
  `MonitorRun` carrying a distinguishing prop (e.g. `phase="sync"` vs `phase="evaluate"`), linked
  to the `RunRequest`. **If you find a better shape that also stays inside the declared labels, take
  it and record why in the Law reading record.** If you conclude a new label is genuinely required,
  that is a law amendment — stop and report, do not just add it.
- Both new work sources must be **idempotent per run**: a second pass finds nothing pending.
- Each agent's entrypoint runs a single `work_loop`. Two work sources for one agent therefore need
  a deliberate composition (a dispatching `find_pending`/`process` pair, or a second loop). Choose
  one, state which, and make sure the *existing* source keeps working — the end-of-run monitor stage
  is not optional (item 3).

**Result:** Implemented. Execution now has a `RunRequest` work source that writes one
`BrokerPositionSnapshot` per run via the existing broker reconciliation path, and monitor now has a
snapshot work source that adopts fresh snapshots into `Position` before analyst work. Both agents
compose the new source with the existing source through typed work items, keeping a single
`work_loop` per entrypoint. The sync marker is `MonitorRun phase="sync"` linked from the
`RunRequest`, so it stays inside monitor-owned labels.

### 2 · The analyst never scores an unreconciled book

This is the clause that makes 2026-07-27 impossible.

- `analyst_poll.find_pending` returns a `ScanRun` **only** when its run's book has been synced.
  Not-yet-synced is *not pending*, so the analyst waits rather than scoring stale state. This
  respects `ANLZ-TRG-03` (the analyst never self-triggers) — it is still purely reactive, it simply
  has one more precondition.
- **When the sync could not reach the broker, the analyst still runs — degraded and visibly.**
  `reconcile_run_start` already writes a `status="stale"` snapshot with a `stale_reason` when the
  broker read fails, and `reconcile_positions_from_latest_snapshot` already refuses to adopt a
  non-`fresh` snapshot. In that case the analyst proceeds against the old book but records a
  `Fault` naming the staleness, and the degradation is visible on the run.
- **Rationale for fail-visible rather than fail-closed — do not "improve" this into a hard block.**
  Blocking the run on a broker outage blocks *exits*, and exits are the risk-reducing side of the
  book. A stale book that trades is a bad decision; a blocked run that cannot sell is an unbounded
  one. The floor is the resting broker stop (ADR-0015 §3), which is exactly why it is exempt from
  ADR-0018 — it keeps working while everything else degrades.

**Result:** Implemented. `agents/analyst/poll.py::find_pending` now returns a `ScanRun` only after
the run has a fresh-or-stale sync marker. Missing sync waits without writing an `AnalystRun`; stale
sync proceeds with `position_book_status="stale"`, a visible stale reason, and a
`position_book_stale` incident in the recommendation provenance.

### 3 · Keep the end-of-run reconcile — both, and both idempotent

- **Do not remove the stage-6 reconcile.** It is not redundant: it adopts the fills *this run just
  created*. Removing it would leave every new position unreconciled until the next run — the exact
  defect you are fixing, moved one stage.
- After this sprint a normal run reconciles **twice**: once at the head against yesterday's closing
  reality, once at the tail against this run's own fills.
- Therefore reconciliation must be provably idempotent within a single run. `_mark_superseded` and
  `_mark_absent` are already guarded by an `if "..." not in node.props` check and
  `_create_broker_position` already returns the existing node — confirm that this holds under a
  double call and prove it with a test rather than reading it and assuming (LAW-02).

**Result:** Implemented. The tail monitor reconcile remains in place and still adopts fills created
by the same run. Head sync and tail monitor now both call the shared snapshot reconciliation helper,
and the tests prove repeated sync/reconcile passes do not duplicate `Position` nodes or rewrite
supersession state.

### 4 · The new stage must not be able to brick the run

DL-71's general lesson, applied to the code this sprint adds. Execution's fan-out had no per-item
containment and one ticker's failure cost three stages, a night's trading, and the reconciliation
that would have prevented it.

- Every new poll path wraps its per-run work in `kernel.fault_boundary`. A broker timeout at the
  head of the run produces a `Fault` and a `stale` snapshot — never an exception into `work_loop`.
- One run's sync failure must not stop another run's sync in the same pass.
- **Non-negotiable:** the sync stage is now the *first* thing that touches the broker. If it can
  raise, it can brick the fleet before a single decision is made — strictly worse than the outage
  this sprint exists to prevent.

**Result:** Implemented. New sync paths are wrapped per run in `kernel.fault_boundary`; broker read
failure becomes a stale snapshot plus `Fault`, while an outer reconciliation failure is captured and
does not escape `work_loop`. A poisoned first run no longer prevents a healthy second run from
syncing in the same pass.

### 5 · Wire the stage in everywhere it is enumerated — including the index trap

Adding a stage touches four enumerations. Three are obvious; the fourth will pass tests and be
wrong.

- [`orchestration/local_pipeline.py`](../../orchestration/local_pipeline.py) — add the sync stage at
  the head, before `provider`.
- [`orchestration/packs/trading_acceptance.py`](../../orchestration/packs/trading_acceptance.py) —
  the acceptance gate's stage list. A run's stage count moves from 7 to 8; keep `ACCEPTANCE PASS`
  meaningful rather than merely still-green.
- [`contracts/resume.py`](../../contracts/resume.py) — `ResumeStage` and `RESUME_STAGES`.
- 🪤 **The trap.** `contracts/resume.py` defines
  `BROKER_RESUME_STAGES = frozenset(RESUME_STAGES[:5])` — *the first five stages, by index*, meaning
  "resuming from here will submit new orders at the broker". `orchestration/resume.py` then does
  `_ARTIFACTS[: RESUME_STAGES.index(stage)]`, so `_ARTIFACTS` is **positionally aligned** with
  `RESUME_STAGES`. Inserting a stage at the head shifts every index by one. Get this wrong and the
  supervisor either warns about broker consequences on a harmless resume, or — far worse — **stops
  warning before a resume that really does submit orders.** Fix it by making the set explicit by
  name rather than by slice, and pin it with the test in the plan below.

**Result:** Implemented. `position_sync` is now the first local pipeline stage, acceptance and trace
counts are eight stages, resume stages start with `position_sync`, and broker-consequence stages are
an explicit named set rather than an index slice. Resume artifact alignment moved to
`orchestration/resume_plan.py` with a planted mismatch test.

### 6 · Declare every new label, edge and prop in the vocabulary

S143 built a write-time vocabulary guard; S144 found that enabling it would have thrown on the first
real broker stop because two edges were undeclared.

- Any new edge type (e.g. `RunRequest → MonitorRun`) or new prop shape goes in
  [`orchestration/packs/trading_graph_vocabulary.json`](../../orchestration/packs/trading_graph_vocabulary.json).
- Re-run `scripts/vocabulary_coverage.py` and `scripts/vocabulary_signatures.py` and paste the
  output into the closeout.

**Result:** Implemented. Added the new sync edges to
`orchestration/packs/trading_graph_vocabulary.json`:
`RunRequest -REFRESHES-> BrokerPositionSnapshot`,
`BrokerPositionSnapshot -MONITORED_BY-> MonitorRun`, and
`RunRequest -POSITION_SYNCED_BY-> MonitorRun`. Vocabulary tests include a planted undeclared-edge
rejection.

### 7 · Prove the checks can fail (DL-70)

No presence assertions. Plant the violation and require the failure — see the full test plan below,
where every test is specified with the violation it plants.

**Result:** Implemented. The test suite plants each critical violation before asserting the fix:
unsynced run not pending, stale snapshot not adopted, MRVL absent after broker truth says absent,
resume artifact mismatch raising, index-slice drift rejected, and undeclared vocabulary edge
rejected.

### 8 · Record the declaration debt you find (do not fix it here)

While reading execution's constitution for item 1, check `EXEC-IDN-02` against what
`agents/execution/` actually writes. Report what you find with evidence — a clause quote and a file
line — and add a `docs/laws/drift-register.md` row for each gap. **Do not edit any `laws.md`**; they
are LOCKED v1 and a law amendment is its own cycle.

DRIFT-024 (already open) records that execution's constitution declares neither `BrokerStopOrder`
state nor a fallback stop parameter. If you find more of the same shape, that is a pattern worth
naming as one finding rather than three rows.

**Result:** Implemented. Added DRIFT-025 to `docs/laws/drift-register.md` for execution law
declaration debt: execution writes `BrokerPositionSnapshot` through
`agents/execution/reconciliation_store.py`, but `EXEC-IDN-02` does not declare that label. No locked
`laws.md` file was edited.

---

## Test plan — every test I want, and why

**Ground rules.** Every test below cites its clause ID(s) in the docstring. Every test **plants the
violation** and requires the failure (DL-70) — a test that asserts a thing is present, without ever
having proven it can be absent, is not evidence. Name them as you like; the names below are
descriptive, not prescriptive. If you add tests beyond this list, list them in the closeout. **If
you conclude one of these tests is wrong or untestable, say so with a reason — do not silently
drop it.**

### A · Execution: the head-of-run snapshot

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | sync work source finds only unsynced runs | one `RunRequest` with no snapshot, one already synced | only the first is returned; the synced one is **not** re-processed |
| A2 | sync writes a fresh snapshot from broker truth | a stub broker holding 3 tickers | a `BrokerPositionSnapshot` with `status="fresh"`, keyed to the run, holdings matching exactly |
| A3 | **broker failure degrades, never raises** | `broker.positions()` raises | snapshot written with `status="stale"` **and** a non-empty `stale_reason`; exactly one `Fault`; **no exception escapes**; the call returns normally |
| A4 | sync is idempotent per run | run the sync twice for one run | second pass finds nothing pending; no duplicate snapshot node |

### B · Monitor: the early reconcile

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| B1 | **a sold position leaves the book before the analyst** | `Position` MRVL 44 active + fresh snapshot **without** MRVL | after sync, MRVL is `broker_absent` and **absent from `open_positions()`**; the node itself is *not* deleted and its `status` is still `"open"` (append-only, DL-73) |
| B2 | a changed quantity supersedes cleanly | graph ABT 96 active, snapshot says ABT 191 | new node active at 191, old marked `broker_superseded_by`, `open_positions()` reports ABT **once**, at 191 |
| B3 | a stale snapshot is never adopted | snapshot with `status="stale"` | the book is byte-identical afterwards; **zero** `Position` writes |
| B4 | the marker stays inside declared labels | run the sync | assert the set of labels written is a subset of `MON-IDN-02`'s enumeration. **Cite the clause.** This is the test that catches an accidental law violation |
| B5 | reconcile twice is a no-op | run the reconcile twice against one snapshot | identical book; no second supersession marker; no duplicate broker position node |

### C · Analyst: the actual defect

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| C1 | analyst is not pending until the book is synced | `ScanRun` with **no** sync marker | `find_pending` returns `[]`; add the marker → the same `ScanRun` is returned. **Plant the violation first** — assert the empty case before the populated one |
| C2 | 🎯 **the 2026-07-27 regression test** | `Position` MRVL 44 active; broker snapshot **without** MRVL; then run sync → analyst | MRVL is **not** in the scoring universe and **no sell recommendation is produced for it**. Name the date in the docstring. If exactly one test in this sprint survives a future refactor, it must be this one — it is the outage, in miniature, made permanent |
| C3 | a stale book degrades but still trades | stale snapshot, then run the analyst | a `RecommendationSet` **is** produced, marked degraded, with a `Fault` naming the staleness. **Proves fail-visible, not fail-closed** — and guards item 2's rationale against a future "improvement" into a hard block |
| C4 | held tickers still reach scoring | fresh snapshot with 2 holdings, empty candidate set | both held tickers appear in the scoring universe — the sync must not accidentally starve `scoring_universe` (`ANLZ-IN-03`) |

### D · Cascade, resume, and the index trap

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| D1 | the end-of-run reconcile still runs | a fill created during this run | it is adopted into the book at stage 6 — **proves item 3 was not "simplified" away** |
| D2 | full cascade still reaches the reporter | an e2e graph-pull run | every stage completes with the sync stage present; the run is acceptable |
| D3 | 🪤 **broker-consequence stages are correct by name** | — | `BROKER_RESUME_STAGES` contains exactly the stages that can submit orders, **asserted by name, never by index**. Add a stage in the test and prove the set does not silently drift |
| D4 | resume artifacts stay aligned | — | `_ARTIFACTS` and `RESUME_STAGES` have equal length and corresponding order. Plant a mismatch and require the failure |
| D5 | resume from a later stage requires the sync artifact | resume from `analyst` with no sync artifact | it refuses with a clear error rather than resuming onto an unreconciled book |

### E · Containment and vocabulary

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| E1 | one run's sync failure does not stop another | two pending runs, the **first** poisoned | the second still syncs; exactly one `Fault`; the pass returns normally. This is DL-71's own lesson, applied to this sprint's code |
| E2 | every new label and edge is declared | the new edge/label | the vocabulary guard accepts the run. Then **plant an undeclared edge and require the guard to reject it** — otherwise you have only proven the guard is quiet |

---

## Explicit non-goals

- **No change to `reconcile_positions_from_latest_snapshot`'s logic.** You are changing *when* it is
  called, not *what* it does. If you believe it is wrong, re-read DL-73's retraction first, then
  report rather than change.
- **No change to `contracts/positions.py`.** It is the correct read model; `is_active_position_node`
  is the only correct filter. Import it; do not re-derive it.
- **No removal of the stage-6 monitor reconcile** (item 3).
- **No ADR-0018 implementation.** Dropping unfilled orders at session end is the next sprint and it
  is a separate decision. This sprint must not cancel or modify any live broker order.
- **No broker-side cleanup of any kind.** Do not cancel, replace, or modify live orders. Read-only
  at the broker except for what the existing cascade already submits.
- **No `laws.md` edits.** LOCKED v1. Findings go to `drift-register.md`.
- **No fan-out audit of the other stages.** Parked in [`docs/ideas.md`](../ideas.md). Item 4 covers
  only the code this sprint adds.

### The road not taken (LAW-06)

Options weighed and **ruled out** — record any further ones you rule out during implementation:

- **Let the analyst read the broker directly.** Kills the staleness at the source, and it is the
  smallest diff. Rejected: `EXEC-IDN-01` makes execution the *sole* broker interface, and putting a
  second agent on the Alpaca boundary would double the credential surface and the rate-limit
  budget for one read.
- **Have the analyst call the monitor's reconcile helper.** Rejected twice over: `MON-IDN-02`
  reserves `Position` writes to the monitor, and `import-linter` forbids agent→agent imports
  outright. This is the constraint that shapes the whole sprint — two agents in a new order rather
  than one agent doing both jobs.
- **Move reconciliation into `contracts/`** so both agents can call it. Rejected: `contracts` is a
  read model; giving it write authority would put position truth in a layer with no owner and no
  law, which is worse than the staleness.
- **Run the whole cascade twice and discard the first pass.** Rejected: doubles broker load and LLM
  spend to solve an ordering problem, and the second pass would still decide on the first pass's
  book.
- **Do nothing and rely on ADR-0018.** Genuinely tempting — dropping unfilled orders removes the
  *carried* phantom intent. Rejected because it does not touch the *authored* one: on 07-27 the
  analyst would still have decided `MRVL sell` against a book showing a position that had already
  sold. ADR-0018 stops a stale decision from surviving the night; this sprint stops it from being
  made. **They are complementary, not alternatives.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, all four remote gates green **before** merging locally
   (DL-56 — pushing is the gate; no PR required).
2. Build + retag the fleet at `:s147`. The running fleet is `:s146`; nothing changes in production
   until the retag.
3. **Watch the first scheduled run closely.** This sprint changes the order in which production
   touches the broker. Confirm the sync stage ran *before* the analyst, that the analyst's book
   matched broker holdings at decision time, and that the run still reaches the reporter.
4. Record the functionality check in [`docs/laws/functionality-checks.md`](../laws/functionality-checks.md).

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds, never a bare literal.
- Faults, not silent failure — `kernel.fault_boundary`, errors redirected with provenance.
- `make ci` all 9 steps green, **100.00 % coverage floor**, before handback. Never lower the floor.
- Version bump in `pyproject.toml` to **0.81.00** (feat → MINOR), `uv.lock` staged with it.
- Any law clause your tests cover cites the clause ID in the test docstring.
- If `main` has moved when you finish: merge `main` into the branch, resolve, re-run `make ci`, and
  **say so in the return notes** (DL-48 — drift reconciliation is the coding agent's step).
- Secrets never through the worktree — chat or gitignored `.env` only.

---

## Handback contract — MANDATORY

**Append your results INSIDE this file, at the bottom, in the placeholder sections below.**
Not a separate report file. Not chat-only. Not a summary that points elsewhere.

Specifically:

1. Fill the **Law reading record** *before* your first code change.
2. Fill the `**Result:**` line under **each** of the eight spec items above, in place.
3. Fill the **Test plan results** table — one row per test in the plan, with its final name and
   status. A test you chose not to write needs a reason, not a blank.
4. Fill the **Closeout — evidence** block with real command output pasted in: `make ci` counts, the
   remote gate job results, the planted-violation runs, the vocabulary script output.
5. Fill the **Return notes** block.
6. State any success factor you did **not** meet plainly, as "verified failing" or "not done"
   (LAW-02 — intent is never restated as outcome; a proven failure is a valid handback, a silent
   gap is not).

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? (yes + what / no) |
| --- | --- | --- | --- |
| `agents/monitor/reconcile.py` + new poll path | `agents/monitor/laws/laws.md`; `agents/monitor/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | `MON-IDN-02` single-writer ownership of `Position`/`MonitorRun`; `MON-TRG-01` authorized caller trigger; `MON-TRG-04` never self-triggers; `MON-STA-02` append-only writes; `MON-IDM-02` existing `check_positions` is not globally idempotent; `MON-OBS-01` reconstructable monitor run facts | Yes - the marker must stay on owned `MonitorRun` rather than a new label, and the early work source must be dispatcher/run-request driven rather than self-triggered. `MON-IDN-02` and `MON-TRG-04` are gray in the test plan, so this sprint must cite and prove them where relied on. |
| `agents/execution/reconciliation.py` + new poll path | `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md`; `docs/laws/dependencies.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | `EXEC-IDN-01` sole broker interface; `EXEC-IDN-02` declared execution-owned labels; `EXEC-TRG-01` dispatcher-triggered submit door; `EXEC-FAIL-02` broker unavailable degrades without crash; `EXEC-OBS-02` broker outcomes are not silent; `DEP-BROKER-01/02` broker boundary and idempotency | Yes - the head sync must reuse execution for the broker read but cannot let execution adopt `Position`. Reading `EXEC-IDN-02` found declaration debt: `BrokerPositionSnapshot` is written by execution code but absent from the owned-label list. Added DRIFT-025 before code changes. |
| `agents/analyst/poll.py` | `agents/analyst/laws/laws.md`; `agents/analyst/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | `ANLZ-TRG-01`/`ANLZ-TRG-03` reactive only, never self-triggered; `ANLZ-IN-03` empty candidate set behavior; `ANLZ-IDN-02` owned labels only; `ANLZ-NEV-04` read-only to other agents' labels; `ANLZ-FAIL-01/02` degraded provider-like paths are visible and non-crashing | Yes - the analyst change must be a pending precondition, not a direct reconcile or broker read. `ANLZ-TRG-03` is gray, so the new wait-for-sync test must plant the unsynced case first and cite it. |
| `contracts/positions.py` (read-only) | `agents/monitor/laws/laws.md`; `agents/monitor/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md`; DL-73 retraction in `docs/design-log.md` | `MON-IDN-02` owns `Position`; `MON-STA-02` append-only state; DL-73 requires `is_active_position_node`, not raw `status == "open"` | No - the sprint already required read-only use. The law/design-log pass confirmed the active-position predicate is the correct import and that superseded/absent nodes must keep `status="open"`. |
| `contracts/resume.py` + `orchestration/resume.py` | `agents/supervisor/laws/laws.md`; `agents/supervisor/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | `SUP-IDN-01` governance/routing only; `SUP-NEV-03` never routes forbidden capability; `SUP-FAIL-03` clear failure on graph placement errors; conventions section 3 gray-to-green and section 7 test citations | Yes - `BROKER_RESUME_STAGES` must become explicit by stage name rather than index slice. Resume placement also needs an explicit sync artifact in `_ARTIFACTS` so resume-from-analyst cannot bypass the fresh-book precondition. |
| `orchestration/local_pipeline.py` + acceptance | `docs/laws/conventions.md`; `docs/laws/functionality-checks.md`; `docs/laws/drift-register.md`; DL-57/DL-59/DL-70 in `docs/design-log.md` | Conventions section 3 requires passing functional tests for green claims; DL-57/DL-70 require planted failures; DL-59 requires UNPROVEN/PASS distinction based on outcome, not intent | Yes - acceptance must expose an 8-stage chain with a real sync stage, and tests must prove the old 7-stage shape can fail rather than only asserting the new stage is present. |
| `trading_graph_vocabulary.json` | `docs/laws/conventions.md`; `docs/laws/drift-register.md`; DL-70 in `docs/design-log.md` | Conventions section 9 drift register; DL-70 plant-the-violation rule; S143/S144 vocabulary guard discipline | No - the pack already declares `BrokerPositionSnapshot`, `MonitorRun`, and `RunRequest`; any new edge such as `RunRequest -> BrokerPositionSnapshot` / `BrokerPositionSnapshot -> MonitorRun` / `RunRequest -> MonitorRun` must be added and then proven with an undeclared-edge rejection. |
| `agents/reporter/poll.py` (phase-skip only) | `agents/reporter/laws/laws.md`; `agents/reporter/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | `RPT-IDN-01` reporter projects completed runs only; `RPT-IN-01` report is keyed by a pipeline run; `RPT-NEV-02` never mutates other agents' nodes; `RPT-TRG-04` never self-triggers | Yes - I rejected using `MonitorDecisionResult` as the sync marker because `MON-TYP-02` gives it a claim-check payload meaning. The cleaner path is the spec's `MonitorRun phase="sync"` marker plus a reporter pending predicate that ignores sync-phase monitor runs. |

**Contradictions found between a law and this spec** (a contradiction is a success — name it):

None found before code changes.

**Laws found silent where a decision was needed** (each needs a `drift-register.md` row):

`EXEC-IDN-02` / `EXEC-DEP-02` / execution CAP are silent on `BrokerPositionSnapshot`, even though `agents/execution/reconciliation_store.py:82` defines `write_snapshot` and `agents/execution/reconciliation_store.py:101` writes the `BrokerPositionSnapshot` label. DRIFT-025 added before code changes. I did not edit locked `laws.md`.

**Clauses that were ⬜ unproven in `test-plan.md` and are now proven by this sprint's tests:**

`MON-IDN-02`, `MON-TRG-04`, `MON-STA-02`, `MON-IDM-02`, `ANLZ-TRG-03`,
`ANLZ-IN-03`, `EXEC-TRG-01`, `EXEC-IDN-01`, `EXEC-IDM-02`, `EXEC-FAIL-02`,
`EXEC-OBS-02`, `SUP-FAIL-03`, and `SUP-OBS-01` now have sprint-local tests that cite
the clause IDs and plant at least one failure/violation path before asserting the protected
behavior. `EXEC-IDN-02` itself remains declaration debt and is recorded as DRIFT-025 rather than
claimed green.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_sync_work_source_finds_only_unsynced_runs` | `agents/execution/tests/test_position_sync_poll.py` | PASS | `EXEC-TRG-01` / `EXEC-IDN-01` |
| A2 | `test_sync_writes_fresh_snapshot_from_broker_truth` | `agents/execution/tests/test_position_sync_poll.py` | PASS | `EXEC-IDN-01` / `EXEC-OBS-02` |
| A3 | `test_sync_broker_failure_degrades_without_raising` | `agents/execution/tests/test_position_sync_poll.py` | PASS | `EXEC-FAIL-02` / `EXEC-OBS-02` |
| A4 | `test_sync_is_idempotent_per_run` | `agents/execution/tests/test_position_sync_poll.py` | PASS | `EXEC-IDM-02` / `EXEC-TRG-01` |
| B1 | `test_sync_removes_sold_position_before_analyst_book_read` | `agents/monitor/tests/test_monitor_position_sync.py` | PASS | `MON-IDN-02` / `MON-STA-02` |
| B2 | `test_sync_supersedes_changed_quantity_cleanly` | `agents/monitor/tests/test_monitor_position_sync.py` | PASS | `MON-IDN-02` / `MON-STA-02` |
| B3 | `test_sync_stale_snapshot_never_adopts_book` | `agents/monitor/tests/test_monitor_position_sync.py` | PASS | `MON-IDN-02` / `MON-STA-02` |
| B4 | `test_sync_marker_stays_inside_monitor_owned_labels` | `agents/monitor/tests/test_monitor_position_sync.py` | PASS | `MON-IDN-02` |
| B5 | `test_sync_reconcile_twice_is_noop` | `agents/monitor/tests/test_monitor_position_sync.py` | PASS | `MON-IDM-02` / `MON-STA-02` |
| C1 | `test_analyst_pending_waits_until_book_synced` | `orchestration/tests/test_fresh_book_before_decision.py` | PASS | `ANLZ-TRG-03` / `MON-TRG-04` |
| C2 | `test_2026_07_27_mrvl_sold_book_never_reaches_analyst` | `orchestration/tests/test_fresh_book_before_decision.py` | PASS | `ANLZ-TRG-03` / `MON-STA-02` |
| C3 | `test_stale_book_degrades_but_still_writes_recommendation_set` | `orchestration/tests/test_fresh_book_before_decision.py` | PASS | `ANLZ-FAIL-01` / `MON-FAIL-01` |
| C4 | `test_synced_held_tickers_still_reach_scoring_universe` | `orchestration/tests/test_fresh_book_before_decision.py` | PASS | `ANLZ-IN-03` / `MON-STA-02` |
| D1 | `test_tail_monitor_still_adopts_this_run_fill` | `orchestration/tests/test_graph_pull_e2e.py` | PASS | `MON-STA-02` / `MON-IDM-02` |
| D2 | `test_clean_cascade_is_accepted` | `orchestration/tests/test_trading_acceptance.py` | PASS | LAW-02 / DL-70 |
| D3 | `test_broker_resume_stages_are_explicit_by_name` | `orchestration/tests/test_resume_stage_contracts.py` | PASS | `SUP-FAIL-03` / `SUP-OBS-01` |
| D4 | `test_resume_artifacts_validate_alignment_rejects_mismatch` | `orchestration/tests/test_resume_stage_contracts.py` | PASS | `SUP-FAIL-03` / `SUP-OBS-01` |
| D5 | `test_missing_source_stage_and_invalid_stage_are_refused` | `orchestration/tests/test_resume.py` | PASS | `SUP-FAIL-03` |
| E1 | `test_sync_failure_for_one_run_does_not_stop_next_run` | `agents/execution/tests/test_position_sync_poll.py` | PASS | `EXEC-FAIL-02` / `EXEC-OBS-02` |
| E2 | `test_declared_vocabulary_covers_sync_edges_and_rejects_bad_signature` | `orchestration/tests/test_graph_vocabulary_e2e.py` | PASS | LAW-02 / DL-70 |

**Tests added beyond the plan:**

- `agents/analyst/tests/test_position_sync_poll_branches.py` covers a `ScanRun` with no
  `MarketData` lineage and an invalid sync-marker status.
- `agents/execution/tests/test_position_sync_work_items.py` covers mixed execution work-item
  ordering, both dispatch arms, no-snapshot reconciliation, and outer-fault containment.
- `agents/monitor/tests/test_monitor_position_sync_work_items.py` covers mixed monitor work-item
  ordering, both dispatch arms, orphan snapshots with no fake `RunRequest`, and direct non-fresh
  snapshot no-op reconciliation.
- `orchestration/tests/test_position_sync_display_branches.py` covers stale sync reasons in
  `batch_trace` and observatory output.
- Updated existing analyst, supervisor, dashboard, resume, graph-pull, observatory, vocabulary, and
  acceptance tests so the new `position_sync` stage is part of their actual fixture truth rather
  than a presence-only assertion.

---

## Closeout — evidence

**Files changed:**

- New sync contract and chain helpers: `contracts/position_sync.py`, `orchestration/batch_chain.py`,
  `orchestration/resume_plan.py`.
- Execution head sync: `agents/execution/poll.py`, `agents/execution/entrypoint.py`, and execution
  sync tests/helpers.
- Monitor head sync and reconciliation reuse: `agents/monitor/position_sync.py`,
  `agents/monitor/poll.py`, `agents/monitor/entrypoint.py`, `agents/monitor/reconcile.py`, and
  monitor sync tests/helpers.
- Analyst pending/precondition: `agents/analyst/poll.py` plus analyst sync fixtures/regressions.
- Stage enumeration, observatory, acceptance, resume, dashboard, and vocabulary updates across
  `orchestration/`, `contracts/resume.py`, `agents/reporter/poll.py`, and `surfaces/tests/`.
- Version/lock: `pyproject.toml` bumped `0.80.03 -> 0.81.00`; `uv.lock` refreshed.
- Law/debt docs: DRIFT-025 added to `docs/laws/drift-register.md`; this sprint file filled in.

**Proven (LAW-02):**

Branch and version:

```text
git branch --show-current
sprint-147-fresh-book-before-decision

uv lock
Resolved 170 packages in 3.84s
Updated trading-agents v0.80.3 -> v0.81.0
```

Focused branch/planted-violation coverage:

```text
uv run pytest agents/analyst/tests/test_position_sync_poll_branches.py agents/execution/tests/test_position_sync_work_items.py agents/monitor/tests/test_monitor_position_sync_work_items.py orchestration/tests/test_position_sync_display_branches.py --tb=short -x --no-cov
============================= test session starts =============================
collected 10 items

agents\analyst\tests\test_position_sync_poll_branches.py ..              [ 20%]
agents\execution\tests\test_position_sync_work_items.py ...              [ 50%]
agents\monitor\tests\test_monitor_position_sync_work_items.py ....       [ 90%]
orchestration\tests\test_position_sync_display_branches.py .             [100%]

============================= 10 passed in 2.06s ==============================
```

Expanded affected suite:

```text
uv run pytest agents/execution/tests/test_position_sync_poll.py agents/monitor/tests/test_monitor_position_sync.py agents/analyst/tests/test_analyst_poll.py agents/analyst/tests/test_broker_stop_deferral.py agents/analyst/tests/test_exit_authority.py agents/analyst/tests/test_unified_held_analysis.py agents/execution/tests/test_execution_entrypoint.py agents/supervisor/tests/test_resume_dispatch.py orchestration/tests/test_fresh_book_before_decision.py orchestration/tests/test_graph_pull_e2e.py orchestration/tests/test_adr0015_graph_pull.py orchestration/tests/test_unified_decision_run.py orchestration/tests/test_batch_trace.py orchestration/tests/test_trading_observatory.py orchestration/tests/test_trading_acceptance.py orchestration/tests/test_trading_acceptance_outcomes.py orchestration/tests/test_resume.py orchestration/tests/test_resume_stage_contracts.py orchestration/tests/test_resume_postgres_semantics.py orchestration/tests/test_graph_vocabulary_e2e.py surfaces/tests/test_dashboard_app.py surfaces/tests/test_dashboard_projections.py surfaces/tests/test_dashboard_resume.py surfaces/tests/test_dashboard_chat.py --tb=short -x --no-cov
============================= test session starts =============================
collected 121 items
...
============================ 121 passed in 16.09s =============================
```

Vocabulary scripts:

```text
uv run python scripts/vocabulary_coverage.py
<exit 0; no stdout>

uv run python scripts/vocabulary_signatures.py
<exit 0; no stdout>
```

Local full gate:

```text
make ci
uv run ruff check . --output-format=github
uv run ruff format --check .
834 files already formatted
uv run mypy kernel contracts agents orchestration surfaces
pyproject.toml: note: unused section(s): module = ['azure.core', 'azure.identity.*', 'azure.keyvault', 'celery.*', 'redis', 'redis.*']
Success: no issues found in 700 source files
uv run lint-imports
Contracts: 4 kept, 0 broken.
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests
<warnings only; exit 0>
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run pytest
Required test coverage of 100.0% reached. Total coverage: 100.00%
================= 1910 passed, 5 skipped in 180.40s (0:03:00) =================
uv run pip-audit
No known vulnerabilities found
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 19 new file(s)
```

Diff hygiene:

```text
git diff --check
<exit 0; no stdout>
```

Remote gates:

```text
git push -u origin sprint-147-fresh-book-before-decision
To https://github.com/yury-gurevich/trading-agents.git
 * [new branch]      sprint-147-fresh-book-before-decision -> sprint-147-fresh-book-before-decision
branch 'sprint-147-fresh-book-before-decision' set up to track 'origin/sprint-147-fresh-book-before-decision'.

gh run watch 30423330499 --exit-status
✓ sprint-147-fresh-book-before-decision CI · 30423330499
✓ quality in 35s (ID 90484393659)
✓ security in 1m55s (ID 90484393710)
✓ test in 55s (ID 90484479721)

gh run watch 30423330469 --exit-status
✓ sprint-147-fresh-book-before-decision Security Findings · 30423330469
✓ gate in 12s (ID 90484393396)
```

**Not met / verified failing:**

- First scheduled production run proof is not done. That is explicitly post-merge/retag sequencing,
  so no production functionality-check row was added in `docs/laws/functionality-checks.md`.
- Remote gates for the implementation commit passed. This evidence-only doc update will be pushed
  and watched separately; recording that final result inside the same file would require another
  evidence-only commit and create a new gate run.

---

## Return notes

- The law pass changed the shape of the implementation: execution owns the broker snapshot,
  monitor owns the book adoption, and the marker stays in `MonitorRun phase="sync"` so no new
  monitor-owned label was required.
- The only law debt found was execution's missing `BrokerPositionSnapshot` declaration in
  `EXEC-IDN-02`; DRIFT-025 records it. No locked `laws.md` files were edited.
- I deliberately did not change `contracts/positions.py`, did not close superseded/absent
  positions, did not remove the tail monitor reconcile, did not implement ADR-0018, and did not
  perform broker-side cleanup.
- Resume needed the most care: the broker-risk set is now explicit by stage name, and resume
  artifact alignment has a planted mismatch test so a future head-stage insert cannot silently
  shift consequences.
- Final pre-implementation-commit drift check: `origin/main` did not move while the sprint ran
  (`git rev-list --left-right --count HEAD...origin/main` returned `0 0`; both tips were
  `4933ae1`). Initial remote gates for commit `d8fe82e` passed: CI `30423330499` and Security
  Findings `30423330469`.
