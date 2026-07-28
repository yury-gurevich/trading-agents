<!-- Agent: planning | Role: sprint handover -->
# Sprint 146 — A position with no floor: why ABT's stop never came back, and the lineage of four filled orders

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-146-unprotected-position`
**Status:** SPEC — 🟠 **96 ABT shares (~$10k) have carried no protective stop since a 403**
**Version:** fix → **0.80.03** (PATCH: last two digits; `0.80.02` is current)
**Effort:** M
**Decisions:** [ADR-0015](../decisions/) §3 broker stops · [DL-62](../design-log.md) gap-down
exposure · [DL-57](../design-log.md)/[DL-59](../design-log.md) intent ≠ outcome ·
[DL-70](../design-log.md) plant violations · [DL-73](../design-log.md) **(RETRACTED — read it before
you audit anything)** · [DL-44](../design-log.md) broker truth

> **Handover revision 2 (2026-07-28).** Revision 1 is in git history. This revision adds the
> **law-first MUST RULE** below. It is a deliberate trial: the operator wants to see whether making
> the coding agent read the governing law clauses *before* writing code changes the result. Treat
> the rule as binding, not decorative — the handback is how the trial is judged.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 3 is done.**

This repo is governed by a law book. Each agent has a locked constitution at
`agents/<name>/laws/laws.md`, with clause IDs of the form `<AGENT>-<SECTION>-<NN>` (e.g.
`EXEC-NEV-03`, `MON-STA-02`). Sections are shared across agents: `IDN` identity, `IN` inputs, `TRG`
triggers, `OUT` outputs, **`NEV` prohibitions**, `STA` state & effects, **`IDM` determinism &
idempotency**, `ORD` ordering, **`FAIL` failure/recovery**, `TYP` types, `SEC` security, `DEP`
dependencies, `OBS` observability, `PERF` performance, `CAP` capabilities, `PARAM` parameters.

### The rule

1. **Before writing code**, for **every** element in the map below, open and read its law file(s).
   Read the whole file the first time — not a keyword grep. The `NEV`, `IDM`, `FAIL` and `PARAM`
   sections bind this sprint most tightly.
2. Also read the umbrella laws that cross-cut: [`docs/laws/dependencies.md`](../laws/dependencies.md)
   (`DEP-BROKER` governs the Alpaca boundary), [`docs/laws/conventions.md`](../laws/conventions.md)
   (clause-ID scheme, gray ⬜ → green 🟩 rules), and
   [`docs/laws/drift-register.md`](../laws/drift-register.md) (where discovered gaps go).
3. **Write the Law reading record** (template at the bottom of this file) into this document
   **before** your first code change. It is the first thing reviewed at handback.
4. **If a law contradicts this spec, STOP and report.** Do not silently follow either one. The law
   is the constitution; this sprint doc is one sprint's opinion, and it can be wrong — revision 1 of
   this very handover was built on a retracted defect. A contradiction you surface is a **success**,
   not a blocker.
5. **If a law is silent** on something you must decide, that silence is a finding: record it in the
   Law reading record and add a row to `docs/laws/drift-register.md`.
6. Every test you write for behaviour a clause governs **must cite the clause ID in its docstring**
   (e.g. `"""EXEC-NEV-03 / EXEC-IDM-01: ..."""`). This is already a CLAUDE.md rule; the trial
   makes it measurable.

### Element → law map (read these, all of them)

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/execution/broker_stops.py` (items 1–3) | `agents/execution/laws/laws.md` | Stop placement is an execution effect; `NEV`, `IDM`, `FAIL`, `STA`, `PARAM` |
| `agents/execution/store.py` — `write_fills` (item 4) | `agents/execution/laws/laws.md` | `EXEC-NEV-03` (never skip the idempotency key), `IDM`, `STA`, `OBS` |
| `agents/execution/alpaca.py` / `settings.py` (items 3, 5) | `agents/execution/laws/laws.md` + `docs/laws/dependencies.md` | The broker boundary; `DEP-BROKER`, `SEC` |
| `contracts/positions.py` (**read-only** — item 6 imports it) | `agents/monitor/laws/laws.md` | Monitor owns `Position` state; `MON-STA-*` explains why `status` stays `"open"` |
| `agents/monitor/reconcile.py` (**do not modify** — see non-goals) | `agents/monitor/laws/laws.md` | Confirm for yourself that supersession is lawful and intended before believing any audit that says otherwise |
| `orchestration/packs/trading_vault_probes.py` (item 5) | `agents/master/laws/laws.md` + `docs/laws/dependencies.md` | Master is the sole Key Vault accessor; credential probes are its surface |
| `scripts/*` (items 4, 6) | `docs/laws/conventions.md` + `docs/laws/functionality-checks.md` | Tooling has no agent law; the umbrella conventions govern it |

### What the trial is measuring

Answer this honestly in the Law reading record, per element: **did reading the law change what you
were going to do?** "No — the intended approach already complied" is a perfectly good answer and
must be recorded as such. A record where every row says "no change" is a real result. A record that
is vague, or written after the code, defeats the trial — and will be treated as an incomplete
handback (DL-48).

---

## Why this sprint

ADR-0015 §3 exists so every held position has a durable floor at the broker. Eight of nine held
names have one at the correct quantity. **ABT does not**, and has not since its stop submission was
refused. DL-62 describes the exposure this leaves — a gap-down between the 22:30 run and the next
open — and MRVL already turned that exposure into a real **−$1,330.12**.

This is not a big sprint. It is a small one about a real hole in a capital-protection guarantee.

> **Read [DL-73](../design-log.md) and its retraction first.** A prior audit of this exact area
> produced a red-severity defect that did not exist, because it filtered `Position` nodes on
> `status == "open"` instead of using `contracts/positions.py::is_active_position_node`. The
> position book is **correct**: 23 nodes, 9 active, one per held ticker, every quantity matching the
> broker. **Do not "fix" reconciliation. Do not close superseded nodes.** If your work makes you
> want to, you have made the same mistake — stop and re-read.

---

## What the audit actually found (2026-07-28, fleet `:s145`)

### Finding 1 — ABT is unprotected, and the skip is unexplained

```text
D5 · Broker holdings with no live protective stop
NO-STOP ABT    qty=96
NO-STOP AMD    qty=55          <- defensible: full-exit sell already pending
OK  BAC  held=503 stop_qty=503     OK  PYPL held=175 stop_qty=175
OK  CSCO held=177 stop_qty=177     OK  SCHW held=196 stop_qty=196
OK  HPE  held=229 stop_qty=229     OK  USB  held=478 stop_qty=478
                                   OK  WFC  held=348 stop_qty=348
```

The evidence, and what it rules out:

- Fill `stop:5244d9de63d93691:ABT` — `status='rejected'`, `reason='HTTP Error 403: Forbidden'`,
  `broker_order_id='rejected:stop:5244d9de63d93691:ABT'`. So the submission was **refused before it
  reached the broker**, and `rejected_broker_fill` recorded that correctly (DL-57 working).
- **No `BrokerStopOrder` node exists for ABT** — there are exactly 7, none of them ABT. So
  `_place_stop`'s `graph.get_node(BROKER_STOP_ORDER_LABEL, key) is not None` guard
  (`agents/execution/broker_stops.py:67-69`) is **not** what blocks the retry, and neither is
  `active_broker_stop_refs` at line 52. **That hypothesis is already eliminated — do not re-test it.**
- On 2026-07-28 the run **did** place SCHW's missing stop (`stop:b56b2d2f124326d3:SCHW`, qty 196) —
  so `place_broker_stops` ran, worked, and skipped ABT specifically.

**The open question is which of the remaining gates ABT fails**, in
`agents/execution/broker_stops.py::place_broker_stops` (lines 48-58):

1. `_fresh_snapshot_quantities(snapshot)` returned `None` — no; SCHW's stop was placed in the same call.
2. `_broker_quantity_matches(threshold, broker_quantities)` — `threshold.quantity` vs broker's 96.
3. `threshold.ticker in sold_tickers` — the PM approved only `AMD sell` that run, so ABT is not in it.
4. **`open_position_stop_thresholds(graph)` never yields ABT at all** — the most likely candidate.
   `contracts/positions.py::_stop_threshold` needs `stop_pct`, and ABT's active node
   `broker:ABT:96:10437` was **created by reconciliation** (`provenance='reconciled-from-broker'`,
   `degraded=True`), not by a PM order intent that carried a `stop_pct`.

If (4) is the cause, the defect is general and serious: **every position adopted from a broker
snapshot rather than opened through the normal path is structurally incapable of receiving a
stop.** ABT is simply the one currently exposed. Confirm before assuming.

### Finding 2 — four filled orders with no `Fill` node

| `client_order_id` | Ticker | Qty | Broker status |
| --- | --- | --- | --- |
| `pm-run-f1f38e5c76104d259ff5383294141273:AMD:buy` | AMD | 19 | `filled` |
| `pm-run-f1f38e5c76104d259ff5383294141273:HPE:buy` | HPE | 229 | `filled` |
| `pm-run-f1f38e5c76104d259ff5383294141273:MRVL:buy` | MRVL | 44 | `filled` |
| `pm-run-6f34914d941d415aada73523ab14d2ea:CSCO:buy` | CSCO | 88 | `filled` |

These are why `broker-reconciled:AMD`, `broker-reconciled:HPE`, `broker-reconciled:MRVL` and
`broker-reconciled:CSCO` exist — the monitor had to invent Positions from a snapshot because no
`Fill` carried the lineage. Ignore the five `dep-broker-probe-*` / `probe-s138-*` orders; they are
test probes with no Fill by design.

### Finding 3 — the credential probe builds a doubled path

`orchestration/packs/trading_vault_probes.py:154`: `_alpaca_account_request` falls back to
`ALPACA_ENDPOINT` and then appends `/v2/account`. The documented `.env.example:108` value already
ends in `/v2`, so the Alpaca credential probe requests `/v2/v2/account` and 404s whenever
`EXECUTION_ALPACA_BASE_URL` is unset. The execution agent is unaffected — it reads
`EXECUTION_ALPACA_BASE_URL` with its own default (`agents/execution/settings.py:70`).

---

## What ships (spec)

> Fill in the `**Result:**` line under each item as you complete it. See
> [Handback contract](#handback-contract--mandatory) — results go in this file.

### 1 · Find out why ABT is skipped — diagnosis before fix

Do **not** patch until the gate is identified. Write a focused test that reproduces the skip from
the real shape: an active Position with `provenance='reconciled-from-broker'`, `degraded=True`, and
whatever `stop_pct` that node actually carries (inspect it — do not assume), a fresh snapshot whose
holdings match its quantity, and an `OrderIntentSet` that does not sell it. Assert that
`place_broker_stops` places **no** stop, then walk gates 2-4 above until you can name the one that
fails.

State the answer explicitly in the return notes.

**Result:** The production shape did **not** reproduce a graph skip: ABT is one active
`reconciled-from-broker` Position (`broker:ABT:96:10437`) with `stop_pct=0.05`, graph quantity 96
matching broker quantity 96, and a computed stop threshold. The failed gate is the broker submit
itself: Alpaca refuses the ABT stop with HTTP 403 because an opposite-side order already exists.
The earlier gate-4 hypothesis was wrong; see DL-75 and the pre-audit / live retry output below.

### 2 · A snapshot-adopted position must still be able to receive a stop

Assuming item 1 confirms gate 4 (or whichever it is), fix the **cause**:

- A position adopted from a broker snapshot has no PM-supplied `stop_pct`. It still needs a floor.
  Give it one from a declared default — `kernel.tunable(..., why=...)` with bounds, **never a bare
  literal** — and make the fallback explicit and visible rather than implicit. **Check the execution
  `PARAM` section first**: a parameter that must be declared there is a law obligation, not a style
  preference.
- The stop price arithmetic must reuse `contracts/stop_rule.py::check_stop`'s own computation, as
  S138 required, so the two cannot drift.
- A position that genuinely cannot be given a justified stop must raise a **`Fault` naming the
  ticker and the reason** — silence is what let ABT sit unprotected (DL-57, and the execution `FAIL`
  and `OBS` clauses).
- **Do not force a stop where the guard is right to refuse.** `_broker_quantity_matches` correctly
  refused SCHW while the graph and broker disagreed, and that self-healed. Preserve that behaviour
  exactly; S145 proved it works.

**Result:** Added `agents/execution/broker_stop_thresholds.py` so broker-adopted active Positions
can be planned from the code-owned `contracts.positions` predicates. The fallback stop percent is
declared as `ExecutionSettings.broker_stop_fallback_stop_pct` with `kernel.tunable` bounds, and the
stop price still flows through `contracts.stop_rule.check_stop`. If a held ticker cannot receive a
threshold, execution now raises an `UnprotectedPosition` Fault instead of silently skipping it.

### 3 · A refused stop must be retried, and its refusal must be visible

The 403 was recorded and then nothing happened — for days, on a live position.

- After a refused stop submission, the next run must **re-attempt** it (no `BrokerStopOrder` node is
  written on refusal today, so confirm the retry actually happens rather than assuming).
- Surface unprotected held positions as a **`Fault`** each run they remain unprotected, so the
  condition is loud instead of discoverable only by an audit.
- Diagnose the `HTTP Error 403: Forbidden` itself far enough to say whether it was transient
  (retry suffices) or structural (e.g. shares committed to another order). **Say which in the return
  notes**; if structural, the retry must not become an infinite loop of refusals.

**Result:** Refused stop submissions are retryable and visible. A rejected retry does not write a
`BrokerStopOrder`, appends a new `Fill` attempt ordinal when a prior refusal chain exists, preserves
the same broker idempotency key, and records an `UnprotectedPosition` Fault with the ticker,
quantity, and broker refusal body. The live ABT retry proved the 403 is structural right now:
Alpaca reported an existing opposite-side order, not a transient transport failure.

### 4 · Lineage for the four filled orphans (append-only)

`scripts/repair_orphan_fills.py` — dry-run by default, `--apply` to write, `--since` bounded by a
declared tunable, in the `scripts/repair_close_pnl.py` mould.

- Find broker orders whose `client_order_id` has **no** `Fill` chain, resolved via
  `agents.execution.fill_attempts.fill_attempt_chain` so it stays correct with S145 attempt ordinals.
- Adopt **broker state read at run time** — status, `filled_avg_price`, `filled_qty`,
  `broker_order_id`. Never carry an `OrderIntent`'s `est_price_cents` in as if it were a fill price.
- Write through the **same** `agents/execution/store.py::write_fills` path the agent uses, so both
  routes converge on one key and either can run second as a no-op. Attach
  `Fill -EXECUTES-> OrderIntent` where the `OrderIntent` exists.
- Allowlist the `dep-broker-probe-*` / `probe-s138-*` prefixes as **data with a reason string**, not
  an inline `if`.
- **Never write an `ExecutionRun`** — forging the node whose absence proves a crash happened would
  destroy the record in order to tidy it (DL-72).
- Second run reports `already_recorded` for every row and changes no node count.

**Result:** Added `scripts/repair_orphan_fills.py`, dry-run by default and append-only through
`write_fills`. Production dry-run found the four PM-run orphans, `--apply` recorded all four, and a
second `--apply` recorded zero and reported them as already recorded. The script uses broker-read
fill state, attaches `Fill -EXECUTES-> OrderIntent` where present, allowlists known probe prefixes
with reasons, and never writes an `ExecutionRun`.

### 5 · The probe path fix (Finding 3)

`_alpaca_account_request` must not append `/v2` to a base URL that already ends in it. Fix the
fallback; do not change `EXECUTION_ALPACA_BASE_URL`'s meaning.

**Result:** Fixed `_alpaca_account_request` to normalize the configured Alpaca base URL to exactly
one trailing `/v2` before appending `/account`. Added a regression test that plants
`ALPACA_ENDPOINT=https://paper-api.alpaca.markets/v2` and proves the probe requests
`https://paper-api.alpaca.markets/v2/account`, not `/v2/v2/account`.

### 6 · An audit that uses the code's own predicates

`scripts/audit_broker_graph.py`, read-only, non-zero exit on any failure. This exists because the
first version of this sprint was built on an audit that re-derived its own definitions and was
wrong (DL-73 retraction).

- **It must import `contracts.positions.is_active_position_node`** and must **not** filter Positions
  on `status` or any hand-rolled prop check. Same rule for Fill chains: use `fill_attempt_chain`.
- Checks: **A1** one active Position per held ticker with matching quantity · **A2** every held
  position has a live broker stop at the right quantity · **A3** broker orders with no `Fill` chain
  (allowlisted probes excluded) · **A4** unacknowledged `Flag` count, reported not enforced.
- A comment at the top stating why the predicates are imported rather than reimplemented, citing
  DL-73's retraction. This is the guard against repeating the mistake.

**Result:** Added read-only `scripts/audit_broker_graph.py`. It imports
`contracts.positions.is_active_position_node` and `agents.execution.fill_attempts.fill_attempt_chain`
instead of re-deriving active Position or Fill-chain semantics, and it includes the DL-73 comment at
the top. Checks A1/A2/A3 return non-zero on failures; A4 reports unacknowledged Flags as INFO.

### 7 · Prove every check can fail (DL-70)

Plant the violation and require the failure — no presence assertions:

- plant a held position with no stop → **A2 fails**; run item 2's placement → passes;
- plant a filled broker order with no Fill → **A3 fails**; run item 4's repair → passes;
- plant **two** active Positions for one held ticker → **A1 fails** (this is the check whose absence
  produced DL-73);
- plant a Position carrying `broker_superseded_by` → **A1 still passes**, proving the audit honours
  the real predicate rather than counting raw nodes;
- plant `ALPACA_ENDPOINT=https://paper-api.alpaca.markets/v2` → assert the probe URL has one `/v2`;
- plant a stop submission that raises 403 → assert a `Fault` is recorded **and** the next run
  re-attempts.

**Result:** Added unit coverage that plants each violation and proves the checks fail before they
pass: duplicate active Positions for A1, superseded Positions ignored by A1, missing live stops for
A2 then broker-stop placement, orphan broker orders for A3 then repair, the one-`/v2` probe URL, and
403 stop retry visibility with a second Fill attempt.

### 8 · Prove it against production

- Run the audit **before** any change; paste the failing rows (expect A2:ABT and A3:×4).
- Apply fixes; run the repair dry-run then `--apply`.
- Run the audit again; paste it. **Target: A1, A2, A3 clean; A4 reported.**
- ABT must end with a live broker stop at qty 96 **or** a stated, evidenced reason why it must not
  have one — a refusal you can justify is a valid outcome, a silent gap is not (LAW-02).
- Record the row in `docs/laws/functionality-checks.md`, with teardown for anything the check created.

**Result:** Production proof completed with a deliberate caveat. Before repair, A2 failed for ABT
and A3 failed for four PM-run fills. Repair cleaned A3. The post-repair audit has A1 clean, A3
clean, A4 reported, and a verified remaining A2 failure for ABT (`held=96 stop_qty=0`). ABT did not
end with a live broker stop because Alpaca refused the retry as a potential wash trade against an
existing opposite-side order; that refusal is now durable and visible rather than silent.

---

## Explicit non-goals

- **Do not touch reconciliation or Position supersession.** It is correct. See the DL-73 retraction.
- **Do not acknowledge the 46 Flags.** Operator action from the dashboard (S127); bulk-acking from a
  script destroys the signal that some are real. Report the count.
- **Do not change the S145 exit-replay, attempt-key, or adoption paths.** Shipped, tested, and
  proven in production on 2026-07-28. If the audit implicates them, **stop and report**.
- **Do not force a stop onto AMD.** It has a full-exit sell pending; a stop under a closing position
  is what S138 Part B's `sold_tickers` skip exists to prevent.
- **No broker-side cleanup** — do not cancel or modify live orders.
- **No cascade reordering** — DL-71 option B stays out.
- **Do not edit any `laws.md`.** They are LOCKED v1. If one is wrong, that is a
  `docs/laws/drift-register.md` row and a report — never an edit.

### The road not taken (LAW-06)

**Placing ABT's stop by hand and moving on.** It would close the exposure in one API call, and the
temptation is real while the position sits unprotected. Rejected because the same 403 will recur on
the next snapshot-adopted position and nobody will be watching; the hole is the missing retry and
the missing Fault, not the missing order. If the operator wants the exposure closed *now*, that is a
separate deliberate action — not this sprint quietly doing it and calling the defect fixed.

**Writing the audit against raw node props again, because it is quicker.** That is exactly how
DL-73 happened. The import rule in item 6 is the fix.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, all remote gates green **before** merging locally
   (DL-56 — pushing is the gate; no PR required).
2. The repair script needs no retag. The **code** fixes do: build + retag at the next `:sNNN`
   (fleet is on `:s145`).
3. Re-run the audit **after the next scheduled run** — proving reconciliation and stop placement
   keep A1/A2 clean is the real proof, not making them clean once.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds (the stop-pct fallback and `--since`
  default included).
- Faults, not silent failure — `kernel.fault_boundary`, errors redirected with provenance.
- `make ci` all 9 steps green, **100.00 % coverage floor**, before handback. Never lower the floor.
- Version bump in `pyproject.toml` to **0.80.03** (fix → PATCH), `uv.lock` staged with it.
- Any law clause your tests cover cites the clause ID in the test docstring.
- Declare any new label/edge/prop in `orchestration/packs/trading_graph_vocabulary.json` and re-run
  `scripts/vocabulary_coverage.py` + `scripts/vocabulary_signatures.py`.
- If `main` has moved when you finish: merge `main` into the branch, resolve, re-run `make ci`, and
  **say so in the return notes** (DL-48).
- Secrets never through the worktree — chat or gitignored `.env` only.

---

## Handback contract — MANDATORY

**Append your results INSIDE this file, at the bottom, in the placeholder sections below.**
Not a separate report file. Not chat-only. Not a summary that points elsewhere.

1. **Fill the Law reading record FIRST**, before any code. It is reviewed first at handback.
2. Fill the `**Result:**` line under **each** of the eight spec items above, in place.
3. Fill the **Closeout — evidence** block with real command output: the **before** audit, `make ci`
   counts, the remote gate results, the repair dry-run and `--apply` tables, and the **after** audit.
4. Fill the **Return notes** block — including item 1's answer (**which gate skipped ABT**) and
   item 3's (**was the 403 transient or structural**).
5. State any success factor you did **not** meet plainly, as "verified failing" or "not done".

An incomplete handback is returned, not repaired (DL-48). **A handback with an empty or
written-afterwards Law reading record is incomplete by definition** — it is the one thing this
revision exists to collect.

---

## Law reading record — FILL BEFORE WRITING CODE

> One row per element in the map. `Clauses that bind` = the specific IDs you judged relevant, not
> the whole file. `Changed my approach?` = **yes + what changed**, or **no + the approach already
> complied**. Both are valid; vagueness is not.

| Element | Law file(s) read | Clauses that bind | Changed my approach? |
| --- | --- | --- | --- |
| `agents/execution/broker_stops.py` | `agents/execution/laws/laws.md` | `EXEC-IDN-01`, `EXEC-NEV-01`, `EXEC-NEV-03`, `EXEC-STA-03`, `EXEC-IDM-01`, `EXEC-IDM-02`, `EXEC-FAIL-01`, `EXEC-FAIL-02`, `EXEC-DEP-03`, `EXEC-OBS-02`, `EXEC-PARAM` table | Yes — the stop fallback must be a declared/bounded tunable and any unprotected held position must be loud; the law is silent on `BrokerStopOrder` and the broker-stop fallback parameter, so DRIFT-024 is required before code. |
| `agents/execution/store.py` | `agents/execution/laws/laws.md` | `EXEC-IDN-02`, `EXEC-OUT-02`, `EXEC-NEV-03`, `EXEC-STA-01`, `EXEC-STA-03`, `EXEC-IDM-01`, `EXEC-IDM-02`, `EXEC-FAIL-03`, `EXEC-FAIL-04`, `EXEC-TYP-01`, `EXEC-TYP-02`, `EXEC-OBS-01`, `EXEC-OBS-02` | No — the intended orphan-fill repair already had to converge through `write_fills`, preserve the client order id, and stay append-only/idempotent. |
| `agents/execution/alpaca.py` / `settings.py` | `agents/execution/laws/laws.md`; `docs/laws/dependencies.md` | `EXEC-NEV-03`, `EXEC-NEV-05`, `EXEC-SEC-01`, `EXEC-DEP-03`, `EXEC-PERF-01`, `DEP-BROKER-01`, `DEP-BROKER-02`, `DEP-CONFIG-02`, `EXEC-PARAM` table | No — the probe-path fix must preserve the execution base-url meaning, keep credentials out of output, and keep idempotent broker order keys intact. |
| `contracts/positions.py` (read-only) | `agents/monitor/laws/laws.md` | `MON-IDN-01`, `MON-IDN-02`, `MON-NEV-05`, `MON-STA-01`, `MON-STA-02`, `MON-IDM-01`, `MON-IDM-02`, `MON-FAIL-03`, `MON-OBS-01`, `MON-OBS-02`, `MON-PARAM` table | Yes — use `is_active_position_node` as the source of truth and do not infer active state from raw `status` props. |
| `agents/monitor/reconcile.py` (read-only) | `agents/monitor/laws/laws.md` | `MON-IDN-01`, `MON-NEV-05`, `MON-STA-01`, `MON-STA-02`, `MON-IDM-02`, `MON-FAIL-03`, `MON-OBS-01`, `MON-OBS-02` | Yes — superseded broker-reconciled positions are append-only evidence, so reconciliation is not part of this fix. |
| `orchestration/packs/trading_vault_probes.py` | `agents/master/laws/laws.md`; `docs/laws/dependencies.md` | `MST-IDN-03`, `MST-NEV-02`, `MST-NEV-04`, `MST-SEC-02`, `MST-SEC-03`, `MST-DEP-02`, `DEP-BROKER-01`, `DEP-CONFIG-02` | No — normalize the Alpaca account URL in the probe without changing secret delivery or logging sensitive values. |
| `scripts/*` | `docs/laws/conventions.md`; `docs/laws/functionality-checks.md` | conventions §§3, 7, 9; functionality-check procedure; `DEP-BROKER-01`, `DEP-BROKER-02` | Yes — tests must cite law IDs, the audit must import code-owned predicates instead of re-deriving them, and the live proof/teardown row belongs in `docs/laws/functionality-checks.md`. |

**Contradictions found between a law and this spec** (rule 4 — a contradiction surfaced is a
success):

None.

**Laws silent where I had to decide** (rule 5 — add a `drift-register.md` row for each):

Execution laws do not yet declare ADR-0015 broker-stop graph state (`BrokerStopOrder`) or the
fallback stop-percent parameter needed when a broker-adopted position has no PM lineage. Record as
DRIFT-024 in `docs/laws/drift-register.md` before implementation.

**Overall verdict on the trial:** did law-first reading change the outcome of this sprint, and
where? Answer plainly, including "it did not".

Yes. It changed the sprint from "patch the skip and add an audit" to "patch the skip, make the
stop fallback an explicit bounded parameter, keep every governed test clause-cited, and log the
law gap instead of pretending the execution constitution already covers broker-stop state."

---

## Closeout — evidence

**Files changed:**

- Execution stop placement:
  `agents/execution/broker_stop_thresholds.py`, `agents/execution/broker_stops.py`,
  `agents/execution/broker_stop_actions.py`, `agents/execution/fill_attempts.py`,
  `agents/execution/poll.py`, `agents/execution/settings.py`, `agents/execution/broker.py`,
  `agents/execution/alpaca.py`, `agents/execution/alpaca_orders.py`.
- Tests:
  `agents/execution/tests/test_broker_stop_unprotected.py`,
  `agents/execution/tests/test_broker_stop_branch_edges.py`,
  `agents/execution/tests/test_broker_stop_sold_edges.py`,
  `agents/execution/tests/test_alpaca_http_errors.py`,
  `agents/execution/tests/test_alpaca_stop_orders.py`,
  `tests/test_repair_orphan_fills.py`, `tests/test_audit_broker_graph.py`,
  `orchestration/tests/test_trading_vault_probes.py`.
- Scripts:
  `scripts/audit_broker_graph.py`, `scripts/_audit_broker_graph_impl.py`,
  `scripts/repair_orphan_fills.py`, `scripts/_repair_orphan_fills_impl.py`.
- Probe/docs/version:
  `orchestration/packs/trading_vault_probes.py`, `docs/design-log.md`,
  `docs/laws/drift-register.md`, `docs/laws/functionality-checks.md`,
  this sprint doc, `pyproject.toml`, `uv.lock`.

**Proven (LAW-02):**

Before audit, production read-only:

```text
PRE-AUDIT production read-only
A1 active positions vs broker holdings
A1 OK ABT active_nodes=1 graph_qty=96 broker_qty=96
A1 OK AMD active_nodes=1 graph_qty=55 broker_qty=55
A1 OK BAC active_nodes=1 graph_qty=503 broker_qty=503
A1 OK CSCO active_nodes=1 graph_qty=177 broker_qty=177
A1 OK HPE active_nodes=1 graph_qty=229 broker_qty=229
A1 OK PYPL active_nodes=1 graph_qty=175 broker_qty=175
A1 OK SCHW active_nodes=1 graph_qty=196 broker_qty=196
A1 OK USB active_nodes=1 graph_qty=478 broker_qty=478
A1 OK WFC active_nodes=1 graph_qty=348 broker_qty=348
A2 live broker stops
A2 FAIL ABT held=96 stop_qty=0
A2 SKIP AMD held=55 reason=pending_sell
A2 OK BAC held=503 stop_qty=503
A2 OK CSCO held=177 stop_qty=177
A2 OK HPE held=229 stop_qty=229
A2 OK PYPL held=175 stop_qty=175
A2 OK SCHW held=196 stop_qty=196
A2 OK USB held=478 stop_qty=478
A2 OK WFC held=348 stop_qty=348
A3 broker orders without Fill chain
A3 FAIL pm-run-6f34914d941d415aada73523ab14d2ea:CSCO:buy ticker=CSCO side=buy qty=88 status=filled broker_order_id=98991314-326e-4f26-a970-915a42c257c9
A3 FAIL pm-run-f1f38e5c76104d259ff5383294141273:AMD:buy ticker=AMD side=buy qty=19 status=filled broker_order_id=dd94c982-7b0f-4ef1-97fd-dbdf880057ff
A3 FAIL pm-run-f1f38e5c76104d259ff5383294141273:HPE:buy ticker=HPE side=buy qty=229 status=filled broker_order_id=972b9e0b-ca54-4857-adbe-50e278c89b58
A3 FAIL pm-run-f1f38e5c76104d259ff5383294141273:MRVL:buy ticker=MRVL side=buy qty=44 status=filled broker_order_id=10752fe2-9f77-4112-bce6-8733852f46af
A3 total_missing=4
ABT active node detail
ABT node=broker:ABT:96:10437 qty=96 opened=10437 stop_pct=0.05 provenance=reconciled-from-broker degraded=True
stop thresholds
ABT threshold qty=96 ref=5244d9de63d93691 opened=10437 stop_pct=0.05
graph_active_broker_stop_orders=7
```

Audit script before repair (exit 1 as expected):

```text
check	verdict	subject	detail
A1	OK	ABT	active_nodes=1 graph_qty=96 broker_qty=96
A2	FAIL	ABT	held=96 stop_qty=0
A3	FAIL	pm-run-6f34914d941d415aada73523ab14d2ea:CSCO:buy	ticker=CSCO side=buy qty=88 status=filled
A3	FAIL	pm-run-f1f38e5c76104d259ff5383294141273:AMD:buy	ticker=AMD side=buy qty=19 status=filled
A3	FAIL	pm-run-f1f38e5c76104d259ff5383294141273:HPE:buy	ticker=HPE side=buy qty=229 status=filled
A3	FAIL	pm-run-f1f38e5c76104d259ff5383294141273:MRVL:buy	ticker=MRVL side=buy qty=44 status=filled
A4	INFO	unacknowledged_flags	46
totals failures=5
```

Repair dry-run with the correct production window:

```text
uv run --extra runtime python scripts/repair_orphan_fills.py --env-file .env --since 2026-07-01T00:00:00Z
mode=dry-run since=2026-07-01T00:00:00+00:00
client_order_id	ticker	side	quantity	status	verdict	reason
pm-run-6f34914d941d415aada73523ab14d2ea:CSCO:buy	CSCO	buy	88	filled	would_record	missing Fill chain
pm-run-f1f38e5c76104d259ff5383294141273:AMD:buy	AMD	buy	19	filled	would_record	missing Fill chain
pm-run-f1f38e5c76104d259ff5383294141273:HPE:buy	HPE	buy	229	filled	would_record	missing Fill chain
pm-run-f1f38e5c76104d259ff5383294141273:MRVL:buy	MRVL	buy	44	filled	would_record	missing Fill chain
totals candidates=50 would_record=4 recorded=0 already_recorded=44 ignored=2
```

Repair apply:

```text
uv run --extra runtime python scripts/repair_orphan_fills.py --env-file .env --since 2026-07-01T00:00:00Z --apply
client_order_id	ticker	side	quantity	status	verdict	reason
pm-run-6f34914d941d415aada73523ab14d2ea:CSCO:buy	CSCO	buy	88	filled	recorded	missing Fill chain
pm-run-f1f38e5c76104d259ff5383294141273:AMD:buy	AMD	buy	19	filled	recorded	missing Fill chain
pm-run-f1f38e5c76104d259ff5383294141273:HPE:buy	HPE	buy	229	filled	recorded	missing Fill chain
pm-run-f1f38e5c76104d259ff5383294141273:MRVL:buy	MRVL	buy	44	filled	recorded	missing Fill chain
totals candidates=50 would_record=0 recorded=4 already_recorded=44 ignored=2
```

Repair second apply proves idempotence:

```text
uv run --extra runtime python scripts/repair_orphan_fills.py --env-file .env --since 2026-07-01T00:00:00Z --apply
totals candidates=50 would_record=0 recorded=0 already_recorded=48 ignored=2
```

Live ABT retry proof:

```text
S146 stop placement proof
fill_nodes_delta=1
broker_stop_nodes_delta=0
fault_nodes_delta=2
abt_position_ref=5244d9de63d93691
abt_broker_stop_order=absent
abt_fill_chain=['stop:5244d9de63d93691:ABT', 'stop:5244d9de63d93691:ABT#1']
fault RuntimeError: HTTP Error 403: Forbidden: {"code":40310000,"existing_order_id":"fd1f1c2c-4911-4df5-b7a1-e2e9929a7341","message":"potential wash trade detected. use complex orders","reject_reason":"opposite side market/stop order exists"}
fault UnprotectedPosition: unprotected held position ABT qty=96: stop submission rejected: HTTP Error 403: Forbidden: {"code":40310000,"existing_order_id":"fd1f1c2c-4911-4df5-b7a1-e2e9929a7341","message":"potential wash trade detected. use complex orders","reject_reason":"opposite side market/stop order exists"}
```

After audit (exit 1, with the only remaining failure verified as ABT's live broker-stop absence):

```text
uv run --extra runtime python scripts/audit_broker_graph.py --env-file .env
check	verdict	subject	detail
A1	OK	ABT	active_nodes=1 graph_qty=96 broker_qty=96
A1	OK	AMD	active_nodes=1 graph_qty=55 broker_qty=55
A1	OK	BAC	active_nodes=1 graph_qty=503 broker_qty=503
A1	OK	CSCO	active_nodes=1 graph_qty=177 broker_qty=177
A1	OK	HPE	active_nodes=1 graph_qty=229 broker_qty=229
A1	OK	PYPL	active_nodes=1 graph_qty=175 broker_qty=175
A1	OK	SCHW	active_nodes=1 graph_qty=196 broker_qty=196
A1	OK	USB	active_nodes=1 graph_qty=478 broker_qty=478
A1	OK	WFC	active_nodes=1 graph_qty=348 broker_qty=348
A2	FAIL	ABT	held=96 stop_qty=0
A2	SKIP	AMD	pending full-exit sell
A2	OK	BAC	held=503 stop_qty=503
A2	OK	CSCO	held=177 stop_qty=177
A2	OK	HPE	held=229 stop_qty=229
A2	OK	PYPL	held=175 stop_qty=175
A2	OK	SCHW	held=196 stop_qty=196
A2	OK	USB	held=478 stop_qty=478
A2	OK	WFC	held=348 stop_qty=348
A3	SKIP	dep-broker-probe-40b86996aa344259	dependency probe order; no pipeline Fill expected
A3	SKIP	dep-broker-probe-d467017ee70247b9	dependency probe order; no pipeline Fill expected
A3	SKIP	dep-broker-probe-d8d17e0855224306	dependency probe order; no pipeline Fill expected
A3	SKIP	dep-broker-probe-dad74f5af1a44da5	dependency probe order; no pipeline Fill expected
A3	SKIP	probe-s138-1784950327	S138 broker-stop live probe order; no pipeline Fill expected
A4	INFO	unacknowledged_flags	46
totals failures=1
```

Focused tests:

```text
uv run pytest --no-cov agents/execution/tests/test_alpaca_http_errors.py agents/execution/tests/test_broker_stop_branch_edges.py agents/execution/tests/test_broker_stop_sold_edges.py agents/execution/tests/test_alpaca_stop_orders.py agents/execution/tests/test_broker_stop_unprotected.py
collected 16 items
agents\execution\tests\test_alpaca_http_errors.py ..                     [ 12%]
agents\execution\tests\test_broker_stop_branch_edges.py .....            [ 43%]
agents\execution\tests\test_broker_stop_sold_edges.py .                  [ 50%]
agents\execution\tests\test_alpaca_stop_orders.py .....                  [ 81%]
agents\execution\tests\test_broker_stop_unprotected.py ...               [100%]
============================= 16 passed in 1.17s ==============================
```

Vocabulary guard scripts:

```text
uv run python scripts/vocabulary_coverage.py
# exit 0, no stdout
uv run python scripts/vocabulary_signatures.py
# exit 0, no stdout
```

Version / lock:

```text
uv lock
Resolved 170 packages in 1.98s
Updated trading-agents v0.80.2 -> v0.80.3
```

Local `make ci`:

```text
uv run ruff check . --output-format=github
uv run ruff format --check .
813 files already formatted
uv run mypy kernel contracts agents orchestration surfaces
Success: no issues found in 681 source files
uv run lint-imports
Contracts: 4 kept, 0 broken.
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run pytest
TOTAL                                                12405      0   2606      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
================= 1877 passed, 5 skipped in 133.31s (0:02:13) =================
uv run pip-audit
No known vulnerabilities found
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
detect-secrets (untracked): no untracked files to scan
```

Remote gates:

```text
gh run list --branch sprint-146-unprotected-position --limit 10
completed	success	fix: protect unprotected broker positions	Security Findings	sprint-146-unprotected-position	push	30344885685	18s	2026-07-28T09:02:31Z
in_progress		fix: protect unprotected broker positions	CI	sprint-146-unprotected-position	push	30344886036	58s	2026-07-28T09:02:31Z

gh run watch 30344886036 --exit-status
✓ sprint-146-unprotected-position CI · 30344886036
Triggered via push about 2 minutes ago

JOBS
✓ quality in 42s (ID 90228673321)
  ✓ Ruff lint
  ✓ Ruff format check
  ✓ Mypy
  ✓ import-linter (agents are islands)
  ✓ Module size guard
  ✓ Module header guard
  ✓ Gate self-test (can each gate fail?)
✓ security in 2m20s (ID 90228673341)
  ✓ pip-audit (Python vulnerabilities)
  ✓ detect-secrets
  ✓ Initialize CodeQL
  ✓ Perform CodeQL analysis
✓ test in 55s (ID 90228846022)
  ✓ Tests + coverage floor
```

**Not done, deliberately:**

- ABT does **not** have a live broker stop after this branch-local proof. That is verified failing
  in A2, with an evidenced structural broker refusal: Alpaca reports an existing opposite-side
  order and refuses the stop as a potential wash trade.
- I did not cancel or modify broker-side orders. The sprint explicitly forbids broker cleanup.
- I did not acknowledge the 46 unacknowledged Flags.
- I did not touch reconciliation or Position supersession; DL-73 says that path is correct.

---

## Return notes

- **Which gate skipped ABT (item 1), and was the 403 transient or structural (item 3)?**
- ABT was not skipped by a graph gate. It passed active-position discovery, quantity matching, and
  threshold planning (`stop_pct=0.05`, ref `5244d9de63d93691`). The stop reached broker submission
  and was refused. The 403 is structural in the current broker state: Alpaca says an opposite-side
  order already exists (`fd1f1c2c-4911-4df5-b7a1-e2e9929a7341`) and returned
  `reject_reason="opposite side market/stop order exists"`.
- **Decisions made inside the sprint** (and anything ruled out — LAW-06):
- DL-75 records the diagnosis pivot: make ABT's refusal durable/retryable instead of changing active
  Position semantics. The fallback stop policy lives in execution as a bounded tunable; the audit
  imports `contracts.positions.is_active_position_node`; refused stops append a new Fill attempt
  but do not write a `BrokerStopOrder`.
- Ruled out: changing reconciliation/supersession, placing a fake `BrokerStopOrder` for a refused
  stop, cancelling broker orders, or forcing a stop onto AMD while its full-exit sell is pending.
- **Surprises / anything the spec got wrong:**
- The spec's likely gate-4 diagnosis was wrong for current production: ABT already carried
  `stop_pct=0.05` and produced a threshold. The live blocker is broker-side wash-trade protection.
- The first repair `--since 2026-07-20T00:00:00Z` was too tight; the four orphans were older, so the
  production repair used `--since 2026-07-01T00:00:00Z`.
- **Did `main` move? Merge performed, `make ci` re-run?**
- `git fetch origin main` left `main` and `origin/main` at
  `96dfa6f2501be4db028efc764665a997608f3fc9`, and `git merge-base --is-ancestor
  origin/main HEAD` returned `origin/main is ancestor of HEAD`. No merge was needed and no merge to
  `main` was performed.
- **Out-of-scope findings** (flag, do not fix):
- A4 still reports 46 unacknowledged Flags. They remain operator/dashboard action, not S146 scope.
- ABT's opposite-side broker order is the operator/fleet state that keeps the stop structurally
  refused; this sprint records and retries the refusal, but does not alter live orders.
