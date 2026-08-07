<!-- Agent: planning | Role: sprint handover -->
# Sprint 165 — Score every name, not five

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-165-score-every-name-not-five`
**Status:** SPEC — packaged 2026-08-07
**Version:** feat → **0.90.00** (MINOR: decision evidence that does not exist today)
**Effort:** M
**Decisions:** [DL-09](../design-log.md) filter decisions as a training source ·
[DL-93](../design-log.md) the object under test is the **selection process** ·
[S88](sprint-88-filter-verdicts-collection.md) / [S89](sprint-89-filter-quality-scorecard.md) which built the verdict shape ·
[S160](sprint-160-shadow-book.md) the read-only-derivation precedent · [DRIFT-034](../laws/drift-register.md) the label-ownership wall ·
[DL-70](../design-log.md) plant the violation

---

## Why this sprint

**The system produces 1.67 selection decisions per run.** Measured across 27 runs: 45 buys total,
6 runs produced zero. DL-93 says the object under test is *the selection process — can the system
predict?* At this rate the answer arrives at roughly one data point a night.

Flattening the book (2026-08-07) unblocked a frozen system. **It did not change the supply of
decisions**, and it was never going to: capacity was never the constraint.

### 🚨 The throttle is not the filters — it is a cap of 5, and this is measured

From `sched-2026-08-07`:

```text
[scanner] universe=100  evaluated=100  survived=5
          dropped  min_average_volume:60  min_relative_strength:18
```

100 − 60 − 18 = **22 names pass the filters**. Only **5** reach the analyst, because
[`candidate_cap`](../../agents/scanner/settings.py#L47) is **5**, with a declared bound of `le=50`:

> `why="Keep the first vertical slice small and explainable for analyst handoff."`

**That justification has lapsed** — the same shape as `starting_cash` in S161 and `max_positions` in
DL-93. The first vertical slice is long gone; the cap is now the single largest limiter on how much
selection evidence the system can generate, and it is one integer.

### The counterfactual machinery already exists and is switched off

- [`bypass_scanner_filter`](../../agents/scanner/settings.py#L75) is a real tunable, default
  **`False`**, whose `why` already names this exact purpose: *"tickers the filters would drop still
  flow downstream (tagged bypassed in the verdict) so their outcome can be observed — the DL-09
  counterfactual that lets a drop be scored against what actually happened."*
- `FilterVerdict` is a **live contract** and `agents/scanner/domain/filters.py` already builds one
  per ticker, with `decision`, `features` and a `bypassed` flag.

### 🪤 But the verdicts are never persisted — this is the actual gap

Measured on the live graph: **`FilterVerdict` count = 0**, and `FilterVerdict` is **not in the
vocabulary pack's `labels` list**. No store code writes it. The verdicts are built, used to decide,
and then discarded when the process exits.

**So DL-09 cannot work today.** Its whole premise is scoring a drop against what actually happened,
and the drop leaves no record. Turning `bypass` on without fixing this just widens a funnel whose
decisions still evaporate.

---

## 🚨 Read this before designing — S160 hit this exact wall

**A new persisted label needs a locked constitution that owns it.** S160 was stopped here: no agent
law owned `RecommendationOutcome`, `RPT-IDN-02` enumerates a closed list, and the sprint had to be
redesigned as a **read-only derivation that persists nothing**. `DRIFT-034` records that the book
still has no home for such a case.

**Resolve this first, before any code:**

1. Read `agents/scanner/laws/laws.md` — **does `SCAN-IDN-*` enumerate scanner's owned labels, and is
   the list closed?** If `FilterVerdict` can be added as scanner-owned within the existing clause,
   say so and cite it.
2. **If it cannot**, prefer the S160 resolution: is the verdict *derivable* rather than observable?
   The features come from the run's own immutable `MarketData` snapshot, so a derivation may
   reconstruct every verdict without persisting anything — the pattern `shadow_book.py`,
   `accept.py` and `trace_run.py` already use.
   🪤 **But check honestly:** a verdict depends on the *settings in force at scan time*
   (`min_average_volume`, `candidate_cap`, `bypass`…). If those are not recoverable for a past run,
   the verdict is **not** derivable and a stored fact is genuinely required — which is a law
   amendment, so **stop and report** rather than smuggling a label in.
3. Whatever you conclude, **write it down with the evidence**. This is the judgement of the sprint.

---

## What ships (spec)

### 1 · 🎯 Resolve where a filter decision lives — derivation or owned label

Per the block above. State the decision, the clause you relied on, and the rejected option.

**Result:**

### 2 · A filter decision survives the run

Every evaluated ticker's verdict becomes queryable after the run — by whichever mechanism item 1
chose. Must carry: ticker, decision, which filter bound, the features behind it, and `bypassed`.

If a new label is lawful, **declare it in
[`trading_graph_vocabulary.json`](../../orchestration/packs/trading_graph_vocabulary.json)** — the
write guard is fail-closed and a stale pack stalls the run on first write (S148/DL-85). Image and
pack then move together at deploy.

**Result:**

### 3 · Raise the cap, with a stated justification to replace the lapsed one

`candidate_cap` 5 → higher (bound `le=50`). Rewrite its `why`: the current one describes a first
vertical slice that no longer exists.

🪤 **Check the blast radius before choosing a number** — this multiplies analyst work per run, and
the analyst calls the LLM. State the measured cost delta per run (`LLMCall` ledger) rather than
assuming it is free. The scanner is not the only thing that scales.

**Result:**

### 4 · Decide `bypass_scanner_filter` separately from the cap

They are different questions. The cap controls *how many survivors reach the analyst*; bypass
controls *whether losers flow through at all*. **Do not turn both on in one step** — you would not
be able to attribute the change. Recommend the cap first, bypass second, and say why.

**Result:**

### 5 · Prove the checks can fail (DL-70)

**Result:**

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 every evaluated ticker is accounted for | a 100-ticker run | verdict count == evaluated count; none silently missing |
| A2 | a dropped name records which filter bound it | a name failing `min_average_volume` | the verdict names that filter, with the feature value |
| A3 | a bypassed name is distinguishable from a survivor | bypass on, a would-be drop | `bypassed=True`, decision preserved — the counterfactual is not laundered into a pass |
| A4 | the cap no longer silently discards | cap raised | survivors above the old cap reach the analyst, and the count matches |
| A5 | 🪤 if derivation was chosen: it writes nothing | any run | node/edge census identical before and after (the S160 assertion) |
| A6 | if a label was chosen: the guard rejects an undeclared prop | a planted undeclared prop | `VocabularyError` fail-closed |

---

## Explicit non-goals

- **No filter threshold changes.** `min_average_volume` / `min_relative_strength` stay as they are —
  the point is to *measure* whether they are right, not to guess again.
- **No PM/sizing change.** `max_position_pct` and `max_positions` were set 2026-08-07 and stay.
- **No scoring-model change.** The analyst decides exactly as it does today.
- **No `laws.md` edits.** Findings go to `drift-register.md`.

### The road not taken (LAW-06)

- **Just turn on `bypass_scanner_filter` and call it done.** Rejected: verdicts are not persisted, so
  the extra decisions evaporate exactly like today's. It would look like progress and produce none.
- **Loosen the filter thresholds instead.** Rejected: it changes what the system believes *without*
  producing evidence about whether the old belief was right, which is the opposite of DL-09.
- **Raise `candidate_cap` to its `le=50` ceiling immediately.** Rejected as a default: analyst work
  and LLM spend scale with it; pick a number against the measured cost.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. **A lapsed `why` is a defect.**
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 11 steps** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — redirect to a file and read the file (row S).
- Version bump to **0.90.00**, `uv.lock` staged with it.
- Secrets never through the worktree — a worktree has **no `.env`**, so any proof needing live data
  is vacuous there. State which tree you ran in.

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the `**Result:**` line under **each** of the five items.
3. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
4. Fill **Closeout — evidence** with real pasted output.
5. Fill **Return notes**, including the item-1 decision and its rejected option.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| Where a filter decision lives | | | |
| `candidate_cap` / `bypass_scanner_filter` | | | |

**Does any locked constitution own a filter-decision label? (cite the clause):**

**Contradictions found between a law and this spec:**

**Laws found silent where a decision was needed:**

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

---

## Closeout — evidence

**Tree the proofs ran in (and `.env` present?):**

**Item 1 decision — derivation or owned label, and the clause relied on:**

**Cap chosen, and the measured cost delta per run:**

**Module line counts:**

**Planted violations watched fail:**

**Final full gate:**

**Remote gate / gate-ran / merge:**

**Not met / verified failing:**

---

## Return notes
