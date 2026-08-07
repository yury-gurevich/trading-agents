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

**Result:** Done. `contracts/broker_stops.py` now exposes `next_broker_stop_order_key`, a pure read that walks `stop:{position_ref}:{ticker}`, then `#1`, `#2`, ... . It returns the first missing key only after every prior `BrokerStopOrder` fact in the chain has `cancelled_at`; it returns `None` immediately for an active fact, so ADR-0015 §3's active-stop guard remains intact. `_place_stop` uses that selected key, and `active_broker_stop_orders` / `active_broker_stop_refs` needed no code change because they already scan every `BrokerStopOrder` node and derive liveness from `cancelled_at`.

### 2 · The unprotected fault stops lying

Once item 1 lands, *"existing inactive BrokerStopOrder fact blocks retry"* should be unreachable for
the cancelled case. Decide what that branch now means — a still-**active** stop whose ref was somehow
absent from `protected_refs` is a real inconsistency and should still fault. **Do not delete the
branch without saying what now reaches it**; if nothing can, say that and remove it.

**Result:** Done. The old *"existing inactive BrokerStopOrder fact blocks retry"* branch is gone. The remaining `fill is None` path now means an **active** stop fact blocked duplicate placement after the earlier `protected_refs` read did not skip it, which is an inconsistency or race worth faulting. The fault reason is now *"active BrokerStopOrder fact blocks duplicate stop placement"*; cancelled facts no longer reach it.

### 3 · Prove the checks can fail (DL-70)

Plant the violation and require the failure. **Watch each test fail before trusting it** — S163's
sprint-defining test passed for the wrong reason because a fixture *constructed* an identifier
instead of reading it back.

**Result:** Done. Six tests were added in `agents/execution/tests/test_broker_stop_replacement.py`, and the existing edge tests were adjusted so the former cancelled-stop blocking behavior is no longer expected. Planted failures were watched: restoring the old base-key guard produced **5 failed, 1 passed** in the new test module; disabling the active `protected_refs` skip failed A3; adding a write inside `next_broker_stop_order_key` failed A5's node/edge census. Restored tree: focused slice **35 passed**.

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
  📌 Current sizes: `contracts/broker_stops.py` **100**, `agents/execution/broker_stops.py` **179**.
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
| Key selection in `contracts/broker_stops.py` | `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md`; `docs/decisions/0015-exit-lifecycle-and-stop-ownership.md` | `EXEC-IDN-03`; `EXEC-IDM-02`; `EXEC-NEV-03`; `EXEC-OBS-03`; ADR-0015 §3 | Yes. The key is both graph identity and broker `client_order_id`, so a cancelled fact can only be extended with a new attempt suffix; the base key must not be reused, and an active fact must still block placement. |
| `_place_stop` | `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md`; `docs/decisions/0015-exit-lifecycle-and-stop-ownership.md` | `EXEC-IDN-01`; `EXEC-IDN-03`; `EXEC-DEP-04`; `EXEC-OBS-02`; `EXEC-OBS-03`; `EXEC-NEV-03` | Yes. DRIFT-038 is a code gap, not a law gap: `EXEC-OBS-03` already promises retry, and the implementation must make that retry land without mutating or deleting the cancelled evidence. |

**Contradictions found between a law and this spec:** None.

**Laws found silent where a decision was needed:** None. The law is explicit about retry and append-only stop lifecycle; the only gap is the current code's inability to select a fresh broker stop key after cancellation.

**Clauses that were ⬜ and are now proven:** `EXEC-OBS-03` and `EXEC-DEP-04` moved ⬜ → 🟩 in `agents/execution/laws/test-plan.md`; `docs/laws/ledger.md` and `docs/laws/INDEX.md` now show execution at **32 / 57**.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_cancelled_stop_is_replaced_on_next_run` | `agents/execution/tests/test_broker_stop_replacement.py` | PASS | `EXEC-OBS-03`; `EXEC-IDN-03`; `EXEC-DEP-04` |
| A2 | `test_replacement_reaches_broker_under_new_client_order_id` | `agents/execution/tests/test_broker_stop_replacement.py` | PASS | `EXEC-NEV-03`; `EXEC-IDM-02` |
| A3 | `test_active_stop_still_blocks_duplicate_submission` | `agents/execution/tests/test_broker_stop_replacement.py` | PASS | `EXEC-OBS-03`; `EXEC-IDM-02`; ADR-0015 §3 |
| A4 | `test_replacement_chain_extends_past_first_suffix` | `agents/execution/tests/test_broker_stop_replacement.py` | PASS | `EXEC-OBS-03`; `EXEC-IDN-03` |
| A5 | `test_next_broker_stop_order_key_is_read_only` | `agents/execution/tests/test_broker_stop_replacement.py` | PASS | `EXEC-OBS-03`; `EXEC-IDN-03` |
| A6 | `test_rejected_exit_reprotects_on_later_hold_run` | `agents/execution/tests/test_broker_stop_replacement_e2e.py` | PASS | `EXEC-OBS-03`; `EXEC-DEP-04` |

**Tests added beyond the plan:** None. Existing edge tests were reconciled to the new behavior, and `test_drop_sweep_append_safe.py::test_2026_07_30_collision_records_drop_without_status_rewrite` now cites `EXEC-DEP-04` for the `BrokerOrderStatus` half of that broad dependency clause.

---

## Closeout — evidence

**Tree the proofs ran in (and `.env` present?):** Worktree `C:\Users\yury_\Downloads\project\trading-agents-sprint-164-a-cancelled-stop-can-be-replaced`, branch `sprint-164-a-cancelled-stop-can-be-replaced`. **`.env` absent** in this worktree; no live broker/graph proof was attempted here.

**Item 2 decision — what still reaches the "blocks retry" branch:** A cancelled fact no longer reaches it. The remaining `fill is None` branch means an **active** `BrokerStopOrder` fact blocked placement even though the earlier active-ref set did not skip the position — a stale read, concurrent placement, or corrupt key/props mismatch. It remains loud as an `UnprotectedPosition` fault because execution must not double-place an active stop.

**Module line counts:** `contracts/broker_stops.py` **100**; `agents/execution/broker_stops.py` **179**; `agents/execution/tests/test_broker_stop_replacement.py` **195**, `agents/execution/tests/test_broker_stop_replacement_e2e.py` **59** after `ruff format`; touched existing test files all remain below 200 (`test_broker_stop_branch_edges.py` **187**, `test_broker_stop_edges.py` **196**, `test_drop_sweep_append_safe.py` **141**).

**Did `active_broker_stop_orders` / `active_broker_stop_refs` need changing? (verified how):** No. Verified by A1/A3/A4/A6: active refs include the replacement suffix, exclude cancelled base facts, and still prevent active duplicate placement. The functions already scan all `BrokerStopOrder` nodes and filter solely on `cancelled_at`.

**Planted violations watched fail:** Old base-key guard restored in `next_broker_stop_order_key` -> `uv run pytest agents/execution/tests/test_broker_stop_replacement.py agents/execution/tests/test_broker_stop_replacement_e2e.py --no-cov` produced **5 failed, 1 passed** (A1, A2, A4, A5, A6 failed; A3 passed). Disabling the `protected_refs` skip -> A3 failed on an unexpected `UnprotectedPosition` fault. Planting a write inside `next_broker_stop_order_key` -> A5 failed on the graph census.

**Final full gate:** `make ci` redirected to `%TEMP%\s164-make-ci-final.txt`, **`MAKE_CI_EXIT=0`**:

```text
MAKE_CI_EXIT=0
TOTAL                                                14205      0   3018      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
================= 2164 passed, 6 skipped in 69.49s (0:01:09) ==================
No known vulnerabilities found
Detect secrets...........................................................Passed
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 2 new file(s)
```

Earlier full gate failure was useful and fixed: **`MAKE_CI_EXIT=2`** at module size with `[FAIL] agents\execution\tests\test_broker_stop_replacement.py: 237 lines - exceeds the 200-line hard block`. The file was split into `test_broker_stop_replacement.py` (**195**) and `test_broker_stop_replacement_e2e.py` (**59**), then the full gate passed.

**Remote gate / gate-ran / merge:** Pending.

**Not met / verified failing:** No live-environment proof in this worktree (`.env` absent). The behavior is locally proven against in-memory graph/broker fixtures; fleet retag/live scheduled proof remains after merge/deploy.

---

## Return notes

- Scope held: no stop threshold, placement policy, fallback percent, flatten, resize, ADR, or `laws.md` change.
- `DRIFT-038` is marked **CORRECTED (S164)**. The law was already right; the code now makes the retry land by using a fresh broker `client_order_id` for a cancelled stop chain.
- The road not taken still stands. Reusing the base key would collide with the broker's `client_order_id`; deleting cancelled facts would violate append-only stop lifecycle; generalising `fill_attempts.py` is still wider than this deadlock-adjacent fix needs.
- A second-run re-protect is proven for the later **hold** run. If the later run approves another sell, stop placement still skips that ticker because the run is trying to take risk to zero; a second sell rejection remains loud rather than pretending the position is protected.
