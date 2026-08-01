<!-- Agent: planning | Role: sprint handover -->
# Sprint 154 — The fill refresh never terminates: 2,742 status facts for 59 fills, and one PnL that faults forever

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-154-fill-refresh-terminal`
**Status:** SPEC — 🟠 **not an outage.** Every run is green; the defect is unbounded write growth
and an unbounded fault, both invisible to the acceptance gate
**Version:** fix → **0.84.05** (PATCH: last two digits)
**Effort:** S
**Decisions:** [ADR-0014](../decisions/0014-postgresql-system-of-record.md) **the append-only spine —
this sprint is a consequence of it, read it first** · [ADR-0018](../decisions/0018-decision-validity-same-session-or-dropped.md)
drop semantics (adjacent, not changed) · [ADR-0015](../decisions/0015-exit-lifecycle-and-stop-ownership.md)
§3 broker stops (**must not regress**) · [DL-72](../design-log.md) one attempt = one immutable node ·
[DL-79](../design-log.md) a cleanup may not outrank the foundation beside it ·
[DL-57](../design-log.md)/[DL-59](../design-log.md) *didn't look* ≠ *looked and found nothing* ·
[DL-70](../design-log.md) plant the violation first ·
[LAW-02](../../ops/laws/LAW-02-successful-execution.md) success is proven, never assumed

> **Why the version is a PATCH and not a MINOR.** No new capability ships. `refresh_pending_fills`
> already exists and is already declared; this sprint makes it *stop*. `0.84.04` → **`0.84.05`**, per
> the CLAUDE.md rule (*fix → last two digits*). If you disagree after reading the rule, say so in the
> return notes rather than silently choosing differently.

---

## Handover note — planning agent → coding agent, 2026-08-01

**You are getting a small, well-diagnosed sprint. The diagnosis is done; do not redo it.** Everything
below the fold is evidence I gathered from the live production spine this morning, and the numbers in
it are real, not illustrative. Your job is the fix, the tests, and the gate — not the investigation.

**Where this came from.** Nobody reported a bug. `sched-2026-07-31` ran **8/8 stages, clean**, and I
was tracing it to close out S144's functionality check. The defect was sitting inside a green run —
which is the whole reason it lasted this long, and the reason the test plan leans so hard on counting
writes rather than asserting absence of errors. There is no exception to catch here. **The symptom is
a number that keeps going up.**

**Read in this order.** The doc is long because it is a cold-start handover; it is not all equally
urgent.

1. **DEFINITION OF DONE** and **the vocabulary guard warning** — the two ways this sprint can go
   wrong in production rather than in review. Both are immediately below.
2. **The defect, precisely** — the four-line explanation of why `status` can never change. If that
   part does not click, stop and ask; everything else follows from it.
3. **What ships**, items 1–5, in order. Item 1 is the root cause and is roughly a two-line change.
   Items 2–5 are what stop it recurring silently.
4. The test plan, non-goals, and the road not taken.

**The three ways I expect this to go wrong**, in likelihood order:

- **You "fix" the wrong layer.** The store is right, `write_order_status` is right, the reporter is
  right. Only the *selector* is wrong. Every tempting fix that touches the other three is listed
  under non-goals with a reason — read them before you decide you have a better idea. If you still
  think you do, say so in the return notes; a challenge I can read is worth more than silent
  compliance.
- **You add the `Fill` property and forget to declare it.** That is a production `VocabularyError` at
  22:30 UTC, not a test failure. Item 4 exists for this and is not optional.
- **You stop at local green.** See DEFINITION OF DONE. Four remote runs went red unattended just
  before this sprint was written, which is why that section is a gate and not a footnote.

**What I want back that is not code.** Two judgement calls are genuinely yours to report on, and I
would rather have your opinion than your compliance:

- the **partial-upgrade gap** (road not taken) — I deferred it deliberately with zero production
  fills affected; tell me if reading the laws changes that;
- anything in the **law reading** that contradicts this spec. The constitution outranks me. **A
  contradiction you surface is a success, not a delay.**

**What is explicitly not yours:** the ABT PnL backfill (mine — production lineage), the `mcp` 2.0.0
Dependabot breakage (separate chore branch), `EXEC-FAIL-03` coverage (`chore-exec-fail-03-coverage`),
and the fleet redeploy that carries the new vocabulary pack (operator sequencing after merge).

**Scale check so you can size this honestly:** the production change is a selector condition, a
marker property, and a guard clause — I would expect well under 50 lines of source across three
files. If your diff is growing past that, something has gone wrong in the reading, and the right move
is to stop and report rather than to keep going.

---

## 🔴 READ THIS FIRST — the vocabulary guard is ARMED in production as of 2026-07-31

This is the **first sprint to ship under a live write guard.** S144 was enabled on the fleet last
night (`:s152`, `GRAPH_VOCABULARY_B64` set on all 14 targets and verified by byte-identical
read-back). `Fill` is one of the **two** property-enforced labels in
`orchestration/packs/trading_graph_vocabulary.json` (45 declared properties).

**Consequence you must internalise:** if you add a new property to a `Fill` node and do not declare
it in the pack, `kernel`'s `check_node` raises `VocabularyError` **on the first real write in
production** — inside execution's fault boundary, on the reconciliation path, at 22:30 UTC. Local
tests will not save you, because the guard is only armed when the env var is set.

This sprint **does** add a `Fill` property (item 2). Declaring it is not a cleanup step at the end;
it is part of the change. See item 4 — it is not optional and it is not deferrable.

---

## 🔴 DEFINITION OF DONE — GREEN ON GITHUB, NOT GREEN ON YOUR MACHINE

**`make ci` passing locally is not done. It is not half done. It is the precondition for starting the
part that counts.**

This is the single most-violated rule in this repo, so it is stated here as a blocking gate rather
than as a handback footnote. At the time this sprint was written, **four consecutive CI runs on the
remote were red and no one acted on them** — they were observed and left. That is the failure mode
this section exists to stop.

### The remote-green rule

1. Push the branch. **Pushing *is* the gate** (CLAUDE.md) — the security-findings `gate` runs on push
   to every branch, which is why direct merges no longer bypass it.
2. Poll until every workflow on **your** branch's tip has **completed**:

   ```bash
   gh run list --branch sprint-154-fill-refresh-terminal --limit 10
   ```

3. **All four jobs must read `success`**: `quality`, `test`, `security` (CI workflow) and `gate`
   (Security Findings workflow). Three green and one red is red.
4. Quote the **run IDs and the job conclusions** in the closeout. A sentence saying "CI passed" with
   no run ID is not evidence and will be handed back (LAW-02: success is proven, never assumed).
5. **`in_progress` is not `success`.** Do not hand back on a run that has not finished. Wait for it.

### If it goes red

**You fix it. You do not report it and stop.** A red remote on your own branch is inside this
sprint's scope by definition — it is your change failing, and diagnosing it is the work.

- Get the actual failure, not the summary: `gh run view <run-id> --log-failed`.
- Fix, push, and **poll again from step 2**. Repeat until green.
- If it is red for a reason genuinely outside your diff (a pre-existing breakage on `main`, a vendor
  outage, an unrelated dependency), **say so explicitly in the return notes with the log excerpt that
  proves it** — and still do not merge. That is a finding for me, not a licence to proceed.

### What you must never do

- **Never merge a branch you have not seen go green on the remote.** Not "it was green locally", not
  "the failure looks unrelated", not "it's only mypy".
- **Never disable, skip, or narrow a CI step to get past it** — no `# type: ignore` sprayed to
  silence a real error, no `--no-verify`, no lowering the coverage floor, no `continue-on-error`.
- **Never hand back with a red or unfinished remote** and the words "should be fine".

> **Not your job in this sprint:** the four red runs referenced above are on the Dependabot branch
> `dependabot/uv/python-development-cc6c16f905` (`mcp` 1.28.1 → 2.0.0, a breaking major that removes
> `Tool(inputSchema=...)` and the `Server.list_tools` / `Server.call_tool` attributes, 8 mypy errors
> in `surfaces/mcp_server.py`). That is **separate work on a separate branch** and the planning agent
> owns it. Do not fix it here, do not rebase onto it, and do not let it confuse your reading of your
> own branch's status. Your gate is **your** branch's tip.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 4 is done.**

### What the law folders are

This repo is governed by a **law book**. It is not documentation and it is not advisory — it is the
constitution the code is required to satisfy, and it outranks this sprint document.

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** — numbered clauses with IDs of the form `<AGENT>-<SECTION>-<NN>` | **LOCKED v1. Read-only. Never edit.** A clause you believe is wrong is a drift-register row plus a report, never an edit |
| `agents/<name>/laws/test-plan.md` | The clause-by-clause test map: which clauses are proven (🟩) and which are unproven (⬜) | Read it to learn whether the behaviour you are changing is currently *proven* or merely *asserted* |
| `docs/laws/*.md` | The **umbrella laws** — conventions, dependencies, drift register, ledger, functionality checks | Same status as agent laws. `drift-register.md` is the **one law-adjacent file you may append to** |

Clause **sections**: `IDN` identity · `IN` inputs · `TRG` triggers · `OUT` outputs ·
**`NEV` prohibitions** · `STA` state & effects · **`IDM` determinism & idempotency** · `ORD` ordering ·
**`FAIL` failure/recovery** · `TYP` types · `SEC` security · `DEP` dependencies · `OBS` observability ·
`PERF` performance · `CAP` capabilities · `PARAM` parameters.

For **this** sprint the binding sections are **`IDM`** (this is an idempotency sprint above all
else — *a second refresh of a settled fill must be a no-op*), **`STA`** (append-only state — the
defect is a state-model misread), **`OBS`** (the evidence must stay visible after it stops being
rewritten), and **`FAIL`** (an unresolvable PnL is a failure that must be recorded **once**).

### The rule

1. **Before writing code**, for **every** element in the map below, open and read its law file(s).
   Read the whole file the first time — not a keyword grep. You are looking for what the agent is
   *forbidden* to do and **what it is required to do when something cannot be resolved**, which is
   exactly what this sprint touches.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜ (unproven),
   say so — you may be the first to test it.
3. Also read: [`docs/laws/conventions.md`](../laws/conventions.md),
   [`docs/laws/dependencies.md`](../laws/dependencies.md) (**`DEP-BROKER` governs the Alpaca
   boundary — this sprint changes how often you call it**), and
   [`docs/laws/drift-register.md`](../laws/drift-register.md) (**DRIFT-025/026 already cover
   execution's durable labels and drop evidence — check whether this sprint widens one before
   opening DRIFT-029**).
4. **Write the Law reading record** (template near the bottom) into this document **before** your
   first code change. It is the first thing reviewed at handback.
5. **If a law contradicts this spec, STOP and report.** The law is the constitution; this sprint doc
   is one sprint's opinion and it can be wrong. **A contradiction you surface is a success.**
6. **If a law is silent** where you must decide, that silence is a finding: record it and add a
   `docs/laws/drift-register.md` row.
7. Every test for behaviour a clause governs **must cite the clause ID in its docstring**.

### Element → law map (read all of these)

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/execution/reconciliation_store.py` (item 1 — **the root cause**) | `agents/execution/laws/laws.md` + `test-plan.md` | `EXEC-IDM-*` (a repeat refresh must be a no-op), `EXEC-STA-*` append-only writes, `EXEC-DEP-02` + `docs/laws/dependencies.md` `DEP-BROKER` (you are changing how many broker-derived writes happen per run) |
| `agents/execution/realized_pnl.py` (item 2) | `agents/execution/laws/laws.md` + `test-plan.md` | `EXEC-FAIL-*` — an unresolvable basis is a *failure to record once*, not a failure to retry forever. Check whether `EXEC-FAIL-03` is ⬜; **it is, and its coverage is `chore-exec-fail-03-coverage`'s job, not yours** |
| `agents/execution/order_status_store.py` (**read-only** — it is correct; the caller is wrong) | `agents/execution/laws/laws.md` | `EXEC-OBS-*`. `write_order_status` faithfully appends one immutable fact per call (DL-72). It is not the defect. Do not "fix" it by making it dedupe internally — see non-goals |
| `orchestration/packs/trading_graph_vocabulary.json` (item 4) | `docs/laws/conventions.md` | S143/S144: `Fill` is property-enforced and **the guard is live**. An undeclared property raises in production |
| `agents/reporter/domain/trade_outcomes.py` (item 3, likely read-only) | `agents/reporter/laws/laws.md` + `test-plan.md` | `RPT-NEV-02` never mutates other agents' nodes. The new marker property must not be mistaken for PnL evidence |
| `docs/laws/drift-register.md` (item 5) | the register's own header | The one law-adjacent file you may append to |

---

## Why this sprint

**Last night's run was clean.** `sched-2026-07-31` scored **8/8 stages complete**, the newly armed
vocabulary guard raised **zero** `VocabularyError`, broker↔graph reconciled with `totals failures=0`,
and all nine positions were fully stop-protected. Nothing about this sprint is an outage, and you
should not go looking for one.

The defect is what the green run was *also* doing, every night, unwatched:

- It appended **2,742** `BrokerOrderStatus` nodes across only **59** distinct fills — up to **73
  copies of the same settled fact for a single fill** — plus one `REFRESHES` edge each.
- It re-emitted the **same** `UnresolvedEntryBasis` fault for the same ABT sell fill it has been
  unable to resolve since 2026-07-24. Two more last night. It will emit two more tonight, forever.

Neither is visible to the acceptance gate, which is the DL-57/DL-59 pattern again: the gate scores
what a run *produced*, not what it *re-produced*.

### What is actually wrong: `status` is write-once, and the selector treats it as a state machine

`agents/execution/reconciliation_store.py:38`:

```python
for node in graph.list_nodes("Fill"):
    if node.props.get("status") != "pending":
        continue
```

`Fill.status` is written **once**, at submit time, as `"pending"`. The store is append-only
(ADR-0014, enforced at `kernel/graph_support.py:70`), so **it can never become `"filled"`.** That is
not a bug in the store — it is the store's contract, and it is the same contract S151 was taught to
respect. The terminal truth lives in a *different* property, `broker_status`, written exactly once by
`_broker_status_props` under `if "broker_status" not in node.props` (line 68).

So the guard on line 38 is permanently true for every fill ever submitted. The selector asks "is this
fill unsettled?" using the one property that can never answer.

Live proof, from the production spine this morning:

```text
Fill (status, broker_status) counts:
   23  ('pending', 'filled')     <- settled at the broker, re-refreshed every run
   16  ('pending', 'rejected')   <- settled at the broker, re-refreshed every run
   10  ('pending', None)
    5  ('rejected', None)
    4  ('filled', None)
```

**39 fills carry a terminal broker status and are still selected as pending work every single run.**

### What follows from it

`refresh_pending_fills` then calls `write_order_status` **unconditionally** (line 45), *before* the
`broker_fill.status == "pending"` early-return on line 46:

```python
write_order_status(graph, fill_node=node, broker_fill=broker_fill)   # line 45 — always
if broker_fill.status == "pending":                                   # line 46 — too late
    continue
```

`write_order_status` keys its node on `f"broker-order-status:{fill_node.key}:{created_at}"` — a fresh
timestamp every call — so every pass mints a genuinely new node. It is behaving exactly as designed
(DL-72: one read = one immutable fact). The caller is asking it to read something that stopped
changing days ago.

Growth is **O(settled fills × runs)**, unbounded, on a paid Neon spine — and it accelerates under
retry storms. During the 07-29 08:48 UTC storm one fill collected **17 status facts in 40 seconds**.

`_broker_status_props` correctly returns `{}` on the repeat (S151's guard holds, no overwrite fault),
so the loop is silent. That silence is why this survived two sprints of live-fire debugging.

### And the fault that never stops

`realized_pnl_props` re-runs on every pass too. Its own re-entry guard is
`REALIZED_PNL_PROP not in fill_node.props` (`realized_pnl.py:54`) — which works for the two sell
fills that resolved:

```text
exit:22d71d0d3acc0586:AMD:sell    realized_pnl_cents = -351560   (-$3,515.60)
exit:e67227ec57fa1e46:MRVL:sell   realized_pnl_cents = -133012   (-$1,330.12)
pm-run-927de0c7…:ABT:sell         realized_pnl_cents = None      <- never set, so never guarded
```

The ABT fill can never resolve. `_position_ref_from_order` tries two sources and both are empty:

- **its own `position_ref` prop** — absent;
- **an `EXECUTES` descendant carrying one** — there is no such order node.

The reason is a key-shape change. The two that resolve are keyed `exit:{position_ref}:{ticker}:sell`
(0.74.01, see `docs/STATE.md:141`) — the position ref is *in the key*. The ABT fill is keyed
`pm-run-{pm_run_id}:ABT:sell`, the **pre-0.74.01 shape**, which encodes no ref. It is a legacy
orphan, and no amount of retrying will change that.

So the code correctly declines to invent a PnL — and then correctly declines again, ~forever, with a
fault each time. **The failure is not the skip. The failure is that the skip is not durable.**

### Scope this honestly — what is NOT affected

Say this back to me at handback so I know you read it:

- **Lifetime realized PnL is understated by exactly one trade** — the 98-share ABT exit filled at
  $101.35 on 2026-07-24. That is the whole PnL impact. AMD and MRVL *are* attributed.
- **The reporter is not broken.** Last night's `profit_factor=unavailable` / `expectancy_cents=unavailable`
  is `collect_trade_outcomes` correctly omitting uncomputable metrics for a run with **0 closes**
  (`trade_outcomes.py:30`). It is per-run scoped and it is right. Do not "fix" the reporter.
- **Broker↔graph state is correct.** `scripts/audit_broker_graph.py` → `totals failures=0`, 9/9
  positions qty-matched, 9/9 stop-protected. Nothing about holdings is in question.

---

## What ships (spec)

### 1 · 🎯 The selector must read the property that can actually change

In `refresh_pending_fills`, stop selecting fills whose broker status is already **terminal**. A fill
that the broker has settled is not pending work: no status fact, no PnL recomputation, no broker
lookup, nothing.

- Terminal set is **`{"filled", "rejected"}`** only.
- **`"partial"` is NOT terminal** and must keep refreshing — a partial can still progress. Getting
  this wrong freezes a half-filled order's evidence. There is a real wrinkle here; read the road not
  taken before you decide anything beyond "keep refreshing partials".
- Keep the existing `status != "pending"` guard. It is not *sufficient*, but it is not *wrong* — it
  still excludes fills that were never submitted as pending. Add the new condition; do not swap one
  for the other.
- The skip must happen **before** `write_order_status`, not after. That call is the growth.

Expected effect on production data: 39 fills stop being refreshed; the remaining pending ones behave
exactly as today.

### 2 · An unresolvable PnL is recorded once, not forever

When `realized_pnl_props` concludes a sell fill's entry basis is **unresolvable**, that conclusion
must become durable so the next pass does not redo it.

- Write a marker property on the `Fill` — name it `pnl_unresolved_at` (ISO-8601 UTC), matching the
  `dropped_at` precedent S151 established.
- `_needs_realized_pnl` gains a third condition: skip when the marker is present.
- Emit the `UnresolvedEntryBasis` fault **only on the pass that writes the marker.** One fault, once,
  with the same message and context it has today. Never a second.
- This is append-safe by construction: the marker is written once and never rewritten. Do **not**
  make it a mutable status field.
- Both reasons (`"missing position_ref"` and `"entry basis unresolved"`) get the marker. They are
  equally durable conclusions.

Note that item 1 alone would *also* stop the ABT fault, by never selecting the fill again. That is
not good enough, and the difference matters: item 1 makes it stop **by accident of scheduling**;
item 2 makes it stop **because the system recorded what it concluded.** A silent skip is the DL-57
failure mode. Ship both.

### 3 · The marker must not be mistaken for PnL evidence

`agents/reporter/domain/trade_outcomes.py::_pnl_cents` already ignores any node without an integer
`realized_pnl_cents`, so a marked fill contributes nothing — **verify this, do not assume it.** Add a
reporter test that a `Fill` carrying `pnl_unresolved_at` and no `realized_pnl_cents` is excluded from
profit-factor and expectancy, and does not inflate `closed_trades_with_pnl`.

If it turns out the reporter *does* need a change, that is a finding — report it before changing
reporter code, because `RPT-NEV-02` and the per-run scoping in item "what is NOT affected" both bind.

### 4 · Declare the new property — the guard is armed

Add `pnl_unresolved_at` to `Fill` in `orchestration/packs/trading_graph_vocabulary.json` (45 → 46
declared properties) and re-run both recovery scripts:

```bash
uv run python scripts/vocabulary_coverage.py
uv run python scripts/vocabulary_signatures.py
uv run pytest tests/test_graph_vocabulary_completeness.py tests/test_graph_vocabulary.py --no-cov
```

**Prove the guard catches the omission (DL-70).** Temporarily remove `pnl_unresolved_at` from the
pack, observe the completeness test **fail naming that property**, restore it, observe it pass. Put
both observations in the handback. A declaration you added but never saw enforced is not proven.

> The redeploy that carries the new pack to the fleet (`GRAPH_VOCABULARY_B64`) is **operator
> sequencing after merge**, not yours. But if you ship the property without the declaration, the
> next production run raises. Do not hand back with item 4 incomplete.

### 5 · Record the drift you find (do not fix it here)

Open **DRIFT-029** against execution: the LOCKED law declares `Fill` durable state and execution's
idempotency obligations, but does not name a terminal-status refresh boundary or an unresolved-PnL
marker. Follow the DRIFT-024..028 row format exactly. Do not edit `laws.md`.

If your reading finds the partial-upgrade gap (road not taken, below) is *also* a law gap, say so in
the same row rather than opening a second.

---

## Test plan — every test I want, and why

Cite the clause ID in every docstring. **Plant the violation and watch the test fail before you make
it pass** (DL-70) — for group A this is the whole point.

### A · Termination (the defect itself)

1. A `Fill` with `status="pending"` and `broker_status="filled"` is **not** selected: a second
   `refresh_pending_fills` over the same graph writes **zero** new `BrokerOrderStatus` nodes and
   **zero** new edges. Assert on counts before/after, not on absence of exceptions.
2. Same for `broker_status="rejected"`.
3. A `Fill` with `broker_status="partial"` **is** still selected and still gets a status fact.
4. A `Fill` with no `broker_status` yet behaves exactly as today (the first refresh must still work —
   this is the regression risk of item 1).
5. **Idempotency at N passes**, not 2: run the refresh five times; total `BrokerOrderStatus` count
   equals the count after the first pass.

### B · The fault stops (the second symptom)

6. A sell fill with no resolvable `position_ref` gets **one** fault and one `pnl_unresolved_at` on
   the first pass; a second pass over the same graph yields **zero** additional faults and does not
   rewrite the marker.
7. The `"entry basis unresolved"` path gets the same treatment as `"missing position_ref"`.
8. A sell fill that **can** resolve still gets `realized_pnl_cents` and **no** marker. The marker
   must never appear on a healthy path.

### C · Nothing regresses

9. A resolvable sell fill's realized PnL is unchanged — pin the AMD case shape (`exit:{ref}:{ticker}:sell`,
   ref recovered from the `EXECUTES` order) so the two live-attributed fills stay covered.
10. Reporter: a marked fill is excluded from profit-factor/expectancy/`closed_trades_with_pnl` (item 3).
11. **Stop safety.** `BrokerStopOrder` placement and the ADR-0015 §3 nine-stop path are untouched by
    this change. Assert it rather than assuming it — S151's group E exists because this is the thing
    that must never break.

### D · Vocabulary

12. The planted-removal proof from item 4, both directions.

---

## Explicit non-goals

- **Do not backfill the ABT PnL.** Reconstructing which `Position` that 2026-07-24 exit closed is a
  judgment call about production lineage, and it is mine, not yours. Item 2 makes the gap *durable
  and visible*; deciding what to do about the missing $-figure comes after, with the marker as the
  index of what needs deciding. Inventing an entry basis to make a number appear is the worst
  available outcome.
- **Do not delete or compact the 2,742 existing `BrokerOrderStatus` nodes.** They are production
  lineage on an append-only spine (DL-44). Stopping the growth is this sprint; whether to archive the
  backlog is a separate operator decision.
- **Do not make `write_order_status` dedupe internally.** It is correct: one broker read = one
  immutable fact (DL-72). Pushing the caller's scheduling bug down into the writer would hide it and
  break the drop-sweep path that legitimately writes a fact per event.
- **Do not relax the append-only store** to let `status` be updated to `"filled"`. That is the
  tempting fix and it is the forbidden one — it would undo ADR-0014 and re-open exactly what S151
  closed. The selector adapts to the store, never the reverse.
- **Do not touch the reporter's per-run scoping** (see "what is NOT affected").
- **Do not fix `EXEC-FAIL-03` coverage.** That belongs to `chore-exec-fail-03-coverage`.

### The road not taken (LAW-06)

**`partial` can never upgrade to `filled`, and I am deliberately not fixing it here.**

`_broker_status_props` writes `broker_status` only `if "broker_status" not in node.props` (line 68).
So a fill that reaches the broker as `partial` keeps `broker_status="partial"` permanently, even
after the broker fills it. Under item 1 that fill therefore refreshes forever — the same unbounded
growth this sprint closes, surviving in one narrow case.

I considered three fixes and rejected all three for this sprint:

1. **Add `"partial"` to the terminal set** — wrong. It would freeze a genuinely in-flight order's
   evidence, which is worse than the growth.
2. **Let `broker_status` be rewritten `partial` → `filled`** — forbidden. Same property, two writes,
   different values: that is precisely the collision that stalled the fleet on 2026-07-30 (DL-79).
3. **Derive current status from the latest `BrokerOrderStatus` fact instead of the `Fill` prop** —
   this is almost certainly the *right* end-state, and it is a design change to the read model that
   deserves its own sprint and probably an ADR amendment. Not a bolt-on to a PATCH.

**Zero production fills are currently in this state** (0 of 58 carry `broker_status="partial"`), so
the cost of deferring is nil today and the risk is bounded and named. Record it in DRIFT-029 and
raise it in your return notes. **Do not silently pick option 1 because it makes a test easier.**

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing upward. `import-linter` enforces.
- Every module < 200 lines (warn at 150). `realized_pnl.py` is at 109 and
  `reconciliation_store.py` is the one to watch — split rather than grow.
- Module docstrings declare `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — the terminal-status set is a module constant next to `_REALIZED_STATUSES`, not
  an inline literal. It is a domain vocabulary, not a tunable: do **not** wrap it in `tunable()`.
- Faults, not silent failure. Item 2 changes *how often* a fault is emitted, never *whether*.
- `make ci` green before handback — all 9 steps, 100 % coverage floor. Never lower the floor.
- Stay in scope. Anything else you find goes in the return notes.

---

## Handback contract — MANDATORY

1. Branch `sprint-154-fill-refresh-terminal`, cut from current `origin/main`.
2. Law reading record filled in **before** the first code change.
3. `make ci` green locally, all 9 steps, full output quoted in the closeout.
4. 🔴 **Remote green — the blocking gate.** Push, poll, and do not hand back until every job on your
   branch tip reads `success`. Fill in this table; an empty cell is an incomplete handback:

   | Workflow | Job | Run ID | Conclusion |
   | --- | --- | --- | --- |
   | CI | `quality` | | |
   | CI | `test` | | |
   | CI | `security` | | |
   | Security Findings | `gate` | | |

   Read the full rules in **DEFINITION OF DONE** above — including *if it goes red, you fix it*.
   **Do not merge.** Merging is the operator's step, after review.
5. Test plan results table filled in — every row, with the planted-failure observations for groups A
   and D.
6. Closeout evidence block completed. **Never hand back with the placeholder unfilled.**
7. Return notes: the partial-upgrade decision, anything the laws contradicted, anything you found and
   did not fix, and **every red remote run you hit on the way** (run ID + what it was + how you fixed
   it). A branch that went green on the first push says so; a branch that took four attempts says
   that too. Hiding the red attempts is the thing I am trying to stop.

---

## Law reading record — fill BEFORE writing code

| Law file | Read? | Clauses that bind this sprint | Anything contradictory or silent |
| --- | --- | --- | --- |
| `agents/execution/laws/laws.md` | ⬜ | | |
| `agents/execution/laws/test-plan.md` | ⬜ | | |
| `agents/reporter/laws/laws.md` | ⬜ | | |
| `agents/reporter/laws/test-plan.md` | ⬜ | | |
| `docs/laws/conventions.md` | ⬜ | | |
| `docs/laws/dependencies.md` | ⬜ | | |
| `docs/laws/drift-register.md` | ⬜ | | |

---

## Test plan results — fill at handback

| # | Test | File::name | Result | Planted-failure observed? |
| --- | --- | --- | --- | --- |
| A1 | filled not re-selected | | | |
| A2 | rejected not re-selected | | | |
| A3 | partial still refreshed | | | |
| A4 | first refresh unchanged | | | |
| A5 | five passes, count stable | | | |
| B6 | one fault, one marker | | | |
| B7 | entry-basis-unresolved marked | | | |
| B8 | healthy path unmarked | | | |
| C9 | resolvable PnL unchanged | | | |
| C10 | reporter excludes marked fill | | | |
| C11 | stop path untouched | | | |
| D12 | vocabulary planted removal | | | |

---

## Tests changed because they encoded the old spec

<!-- list them here with a one-line reason each; "none" is an acceptable answer -->

---

## Closeout — evidence

**Files changed:**

<!-- fill -->

**Proven (LAW-02):**

<!-- version bump, focused runs, make ci output, remote run IDs -->

**Not met / verified failing:**

<!-- state plainly; deploy + live proof are operator sequencing after merge -->

---

## Return notes

<!-- fill -->
