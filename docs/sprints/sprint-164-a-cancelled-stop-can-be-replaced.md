<!-- Agent: planning | Role: sprint handover -->
# Sprint 164 — A cancelled stop can be replaced

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-164-a-cancelled-stop-can-be-replaced`
**Status:** SPEC — packaged 2026-08-07; **the last gate before [chore-flatten-and-resize](chore-flatten-and-resize.md)**
**Version:** fix → **0.89.02** (PATCH: closes `DRIFT-038`, no new capability)
**Effort:** S
**Decisions:** [DRIFT-038](../laws/drift-register.md) the row this closes ·
[S163](sprint-163-an-exit-cancels-its-own-stop.md) which made it routinely reachable ·
[ADR-0015](../decisions/0015-exit-lifecycle-and-stop-ownership.md) §3 stops rest at the exchange ·
[DL-95](../design-log.md) the deadlock · [DL-70](../design-log.md) plant the violation

> **Why PATCH.** No new capability — `EXEC-OBS-03` already promises the retry; the code cannot
> deliver it. `0.89.01` → **`0.89.02`**.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 4 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED v1. Read-only. Never edit.** A clause you believe is wrong is a `drift-register.md` row plus a report |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`IDN`** (execution owns `BrokerStopOrder`), **`IDM`** (idempotency and the
`client_order_id`), **`OBS`** (the stop lifecycle), **`NEV`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read `agents/execution/laws/test-plan.md` alongside `laws.md`. If a clause you rely on is ⬜, say so.
3. Also read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md) — **`DRIFT-038` is the row you are closing.**
4. **Write the Law reading record** (template at the bottom) **before** your first code change.
5. **If a law contradicts this spec, STOP and report.**
6. **If a law is silent**, that silence is a finding: record it and add a `drift-register.md` row.
7. Every test for behaviour a clause governs **cites the clause ID in its docstring**.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `contracts/broker_stops.py` (key selection) | `agents/execution/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `EXEC-IDN-03` execution exclusively owns `BrokerStopOrder`; `EXEC-IDM-02` the key is the stable broker identity |
| `agents/execution/broker_stops.py::_place_stop` | same | `EXEC-OBS-03` the lifecycle clause you are making true; `EXEC-NEV-03` never skip the idempotency key; ADR-0015 §3 |

⚠️ **`ADR-0015 §3`: an active stop must remain untouchable.** This sprint only lets a **cancelled**
chain be extended. If your change would let a *live* stop be re-placed or duplicated, stop and report.

---

## Why this sprint

**`EXEC-OBS-03` promises a retry the code cannot perform.** The clause says a held position ending a
run with no live broker stop is *"surfaced as an `UnprotectedPosition` fault **and retried on the next
run** — a refusal is never recorded once and then forgotten."*

Measured on `main` ([`broker_stops.py:116-126`](../../agents/execution/broker_stops.py#L116)):

```python
def _place_stop(graph, broker, sink, plan) -> BrokerFill | None:
    threshold = plan.threshold
    key = broker_stop_order_key(threshold.position_ref, threshold.ticker)
    if graph.get_node(BROKER_STOP_ORDER_LABEL, key) is not None:
        return None                      # <-- also true for a CANCELLED fact
    return place_stop(graph, broker, sink, threshold, key, ...)
```

`place_broker_stops` then records *"existing inactive BrokerStopOrder fact blocks retry"*. So the
fault repeats truthfully every run and the position is **never re-protected**.

### S163 changed this from latent to routine

Before S163 a stop was only cancelled once its position was already gone (`reconcile_broker_stops`
cancels on an inactive `position_ref`), so a cancelled fact and a live position never coexisted.
**S163 makes every exit cancel its own stop before submitting.** A rejected exit therefore leaves a
position *held*, *unstopped*, and *unrepairable* — the failure mode of the feature just shipped.

**The flatten is the worst possible first exposure:** ten exits at once, all with cancelled stops, on
a ~2× levered book. One rejection strands that position with no stop and no repair path.

### 🪤 It cannot be fixed by relaxing the guard

`broker_stop_order_key` is documented as *"the shared graph key **and broker client_order_id**"*.
Re-placing under the same key is rejected by the broker as a duplicate `client_order_id` — that is
`EXEC-NEV-03` / `EXEC-IDM-02` working exactly as designed. **A replacement needs a new key.**

### The pattern already exists, with production evidence

The rejected ABT stops observed 2026-08-07 are keyed `stop:5244d9de63d93691:ABT`, `…ABT#1`,
`…ABT#2` — `select_fill_attempt` / `fill_attempt_chain` already chain the stop **`Fill`** side. Only
the **`BrokerStopOrder`** fact does not. This sprint applies the established idea to the second label.

---

## What ships (spec)

> Fill in the `**Result:**` line under each item as you complete it.

### 1 · A cancelled stop no longer blocks its own replacement

Add a key-selection read to `contracts/broker_stops.py` beside the existing read model — it derives
purely from facts already there:

```python
def next_broker_stop_order_key(
    graph: GraphStore, position_ref: str, ticker: Ticker
) -> str | None:
    """Return the free key to place under, or None while one is still active."""
```

Walk `stop:{ref}:{ticker}`, then `#1`, `#2`, … Return the first key with **no** node. Return `None`
as soon as a node is found whose `cancelled_at` is `None` (still active — do not double-place).
Then `_place_stop` asks for that key instead of testing the base key for existence.

📌 **Expected to need no change:** `active_broker_stop_orders` / `active_broker_stop_refs` read
`cancelled_at` off whatever nodes exist, so chained facts should be picked up automatically. **Verify
that rather than assuming it** — say so in the return notes either way.

**Result:**

### 2 · The unprotected fault stops lying

Once item 1 lands, *"existing inactive BrokerStopOrder fact blocks retry"* should be unreachable for
the cancelled case. Decide what that branch now means — a still-**active** stop whose ref was somehow
absent from `protected_refs` is a real inconsistency and should still fault. **Do not delete the
branch without saying what now reaches it**; if nothing can, say that and remove it.

**Result:**

### 3 · Prove the checks can fail (DL-70)

Plant the violation and require the failure. **Watch each test fail before trusting it** — S163's
sprint-defining test passed for the wrong reason because a fixture *constructed* an identifier
instead of reading it back.

**Result:**

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 a cancelled stop is replaced on the next run | active stop → cancelled → position still held | a **new** `BrokerStopOrder` at `#1`, active, and **no** `UnprotectedPosition` fault |
| A2 | the replacement reaches the broker under a new key | same | the broker sees a **different** `client_order_id`, so it is not a duplicate submission |
| A3 | an active stop is still never double-placed | active stop, position held | no new fact, no new broker call. **ADR-0015 §3** |
| A4 | the chain extends past the first replacement | two cancelled facts | the third placement lands at `#2` |
| A5 | key selection is a pure read | any graph | `next_broker_stop_order_key` writes nothing (node/edge census identical before and after) |
| A6 | 🪤 end-to-end through the real path | S163's rejected-exit scenario, run twice | run 1 faults `UnprotectedPosition`; **run 2 re-protects the position**. This is the clause `EXEC-OBS-03` actually promises |

---

## Explicit non-goals

- **No change to stop thresholds, placement policy, or `broker_stop_fallback_stop_pct`.**
- **No ADR-0015 / ADR-0017 reversal.** An active stop stays untouchable.
- **No flatten, no resize, no parameter move.** Those follow this sprint.
- **No `laws.md` edits.** `DRIFT-038` closes as corrected-in-code — the law was right and the code
  was short of it.

### The road not taken (LAW-06)

- **Relax the guard to ignore cancelled facts and reuse the base key.** Rejected: the key is the
  broker `client_order_id`, so the broker rejects the replacement as a duplicate.
- **Delete the cancelled fact.** Rejected: `EXEC-OBS-03` requires cancellation to be an appended
  marker, *never a deletion*, and the graph is append-only.
- **Reuse `fill_attempts.py`.** Rejected: it is `Fill`-labelled throughout
  (`graph.get_node("Fill", …)`, `graph.list_nodes("Fill")`). Generalising it is a wider refactor than
  a deadlock-adjacent fix should carry — but say in the return notes if you disagree after reading it.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0** for the **full 40-char SHA**
   (never through a pipe), then merge and push.
2. **Fleet retag required.** Hash `orchestration/packs/trading_graph_vocabulary.json` at the deployed
   commit and at `HEAD`; identical → image-only retag. S164 adds no label or property, so it should
   be identical — **verify, do not assume**.
3. **Then run [chore-flatten-and-resize](chore-flatten-and-resize.md).** S163 + S164 together are its
   prerequisites: the exit can free its own shares, and a failed exit can be re-protected.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `contracts/broker_stops.py` **74**, `agents/execution/broker_stops.py` **180**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 11 steps** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — redirect to a file and read the file (row S).
- Version bump to **0.89.02**, `uv.lock` staged with it.
- Secrets never through the worktree — a worktree has **no `.env`**, so any proof needing live data
  is vacuous there. State which tree you ran in.

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the `**Result:**` line under **each** of the three items.
3. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
4. Fill **Closeout — evidence** with real pasted output.
5. Fill **Return notes**.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| Key selection in `contracts/broker_stops.py` | | | |
| `_place_stop` | | | |

**Contradictions found between a law and this spec:**

**Laws found silent where a decision was needed:**

**Clauses that were ⬜ and are now proven:**

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | | | | |
| A2 | | | | |
| A3 | | | | |
| A4 | | | | |
| A5 | | | | |
| A6 | | | | |

**Tests added beyond the plan:**

---

## Closeout — evidence

**Tree the proofs ran in (and `.env` present?):**

**Item 2 decision — what still reaches the "blocks retry" branch:**

**Module line counts:**

**Did `active_broker_stop_orders` / `active_broker_stop_refs` need changing? (verified how):**

**Planted violations watched fail:**

**Final full gate:**

**Remote gate / gate-ran / merge:**

**Not met / verified failing:**

---

## Return notes
