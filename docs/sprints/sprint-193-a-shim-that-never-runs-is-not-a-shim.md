<!-- Agent: planning | Role: sprint handover — the back-compat shim must run against the type the store actually returns -->
# Sprint 193 — a shim that never runs is not a shim

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-193-a-shim-that-never-runs-is-not-a-shim`
**Status:** MERGED — main gate proven for implementation SHA
**Version:** `0.94.04` (PATCH from `0.94.03`)
**Effort:** S
**Decisions:** [DL-143](../design-log.md) · work-queue item 40

> **Why this bump kind.** No new capability, no new promise. S184 already declared that pre-S184
> `passed` payloads are accepted; the validator that delivers that declaration has never executed.
> Restoring a promise that was already made is a **fix**, so PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/portfolio_manager/laws/laws.md` | The PM agent's **locked constitution** (LOCKED v1) | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/portfolio_manager/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding clause: **`PM-NEV-09`** — an unevaluated gate must never be read as passed. It is the reason
`GateOutcome.outcome` is tri-state at all, and the reason `.passed` raises rather than returning
`False`. **Everything in this sprint sits underneath that clause**, so read it before you touch the
validator that decides which of the three states a historical row becomes.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read `test-plan.md` alongside `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row (next free is **DRIFT-056**).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**It changes `contracts/portfolio_manager.py`, so the first half is unambiguously YES — and you must
still answer the second half yourself rather than inherit my reading.**

**My reading:** the guarantee is *unchanged*. S184 already promised that a pre-S184 `passed` payload
is normalised into the tri-state field; `_accept_historical_passed` exists solely to keep that
promise, and this sprint makes it capable of keeping it. No property is added, no field changes type,
no agent starts asserting anything new. On that reading it is a repair inside an existing contract,
and a full law cycle is **not** triggered.

🪤 **Do not accept that without checking two things.** (a) Whether `PM-NEV-09`'s wording, or the S184
law-cycle entry that introduced it, states the accepted **input shapes** — if it enumerates `dict`
and says nothing about mappings generally, the law is *silent* where this sprint needs a decision,
which is a `DRIFT-056` row and a report, **not** a quiet edit. (b) Whether widening acceptance to any
`Mapping` could let a payload through that `PM-NEV-09` intends to reject. It should not — the
widening is about the *container type*, never about which of the three states a gate lands in — but
say so from the code, not from this paragraph.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `contracts/portfolio_manager.py` (`_accept_historical_passed`) | `agents/portfolio_manager/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `PM-NEV-09` — the tri-state exists so an unevaluated gate is never read as passed; this validator decides the state a historical row takes |
| the new regression test | same | Must cite the clause ID in its docstring (conventions §3, CLAUDE.md) |

⚠️ **The invariant this sprint must not break:** a payload carrying **neither** `outcome` **nor**
`passed` must still fail validation. The shim's job is to convert a *known* historical shape, not to
invent a state for an unknown one. If your change makes a shapeless payload validate, stop and report.

---

## Goal

Make S184's back-compat validator run against the type the graph store actually returns, and prove it
with a test that cannot pass unless it does.

**The single postcondition:** `accept_run` over every `RunRequest` on the spine returns **zero
`ERROR`s**. That is the measurement that found this, and it is the measurement that closes it.

---

## Why (context)

### Measured 2026-09-01 — read these before designing

Running the acceptance gate over **all 55 `RunRequest`s on the live Neon spine** returned
**38 `ERROR`, 16 `FAIL`, 1 `PASS`**. All 38 errors are **one** cause:

```text
rejected.N.gate_report.M.outcome
  Field required [type=missing, input_value=mappingproxy({...}), input_type=mappingproxy]
```

raised from `orchestration/packs/trading_observatory_chain.py:71` (`pm`). The per-run error *count*
varies only with how many rejected intents that run held — 5 to 126 — which is what makes it one
defect and not many.

**The cause is one line.** S184 added the tri-state `GateOutcome.outcome`
(`contracts/portfolio_manager.py:33`) and, beside it, a migration validator whose entire purpose is
to normalise the older shape (`:38`). It opens:

```python
if not isinstance(data, dict) or "outcome" in data or "passed" not in data:
    return data
```

`kernel/graph_support.py:55` `_frozen_value` wraps **every nested Mapping recursively** (`:56`) in
`MappingProxyType`, and `isinstance(MappingProxyType({}), dict)` is **`False`**. So the shim takes
its early return on every payload it exists to convert.

**Proven directly, not inferred from the traceback:**

```text
isinstance(mappingproxy, dict) = False
plain dict   -> GateStatus.PASSED
mappingproxy -> RAISED ValidationError - 1 validation error for GateOutcome
```

Same payload, same validator, opposite outcomes. The only variable is the wrapper the real store
applies and the tests do not.

🪤 **Why nothing caught it.** The shim's tests hand it plain dict literals. Nothing ever exercised it
against a payload that had made a round trip through a `GraphStore`, so it passed its own suite while
being dead in the one place it is ever needed. **That is the actual subject of this sprint.** The
one-word fix is not the deliverable; a test that would have failed is.

---

## Scope — and what is deliberately NOT here

**In scope**

1. `_accept_historical_passed` accepts any `Mapping`, not only `dict`.
2. A regression test whose input has **round-tripped through a real `GraphStore`**, so it fails
   against today's code.
3. A sweep over the spine as the live proof: zero `ERROR`s across every run.
4. A check of the other `isinstance(..., dict)` call sites listed under *Blast radius*.

### Out of scope (do NOT build this sprint)

- **Do not change `_frozen_value` or make the store return plain dicts.** The immutability of props is
  deliberate; the reader is what is wrong. Changing the store to suit one validator would trade a
  contained defect for an uncontained one.
- **Do not touch the 16 `FAIL` verdicts** the sweep also reported. Those are old runs failing on old
  data — a different question, and mostly a legitimate one.
- **Do not add a `dict()` coercion at each call site.** There are at least seven; fixing the validator
  fixes all of them, and per-site coercion is the version of this fix that rots.
- **No new `GateStatus` member, no schema migration, no backfill of stored rows.** Historical rows
  stay exactly as written; this is about reading them.

### The road not taken (LAW-06)

**Rewriting stored `gate_report` rows to add `outcome`** was considered and rejected. It would make
the shim unnecessary — but it mutates append-only history to suit a reader, it cannot be undone, and
it would leave the same blindness in place for the *next* field that gets a back-compat shim. The
shim is the right mechanism; it simply has to run. **Record this in your handback** if you find a
reason to revisit it.

---

## Blast radius — measured 2026-09-01

Wider than the observatory, and this is the part that should decide how carefully you test.
`OrderIntentSet.model_validate(...)` is called on **graph props** from at least seven places:

| Site | Reads |
| --- | --- |
| `orchestration/packs/trading_observatory_chain.py:71` | the `pm` stage view — **where the 38 errors surface** |
| `orchestration/packs/trading_deliberation_view.py:135` | S191's approved-buy count — **already guarded** by `except ValueError` |
| `agents/deliberator/poll.py:55` | the deliberator reading a `PMRun` |
| `agents/execution/pm_execution.py:49` | execution reading a `PMRun` |
| `agents/execution/deliberation_gate.py:139` | the veto gate's order set |
| `agents/execution/agent.py:87` | execution reading `orders` |
| `orchestration/batch_trace.py:136`, `orchestration/shadow_book_join.py:46` | history joins |

🟩 **Current runs are unaffected** and this is not a live trading defect: PM writes `outcome` today,
so every one of these succeeds on a fresh run. That is exactly why it hid.
🚨 **But every one of them fails on a pre-S184 row**, so anything that re-reads history — the
dashboard (`surfaces/dashboard/projections.py:55` raises rather than renders), a replay, a shadow-book
join, a backfill — is broken for **69 %** of the runs on the spine.
🪤 **Confirm this table rather than trusting it.** I measured the observatory site directly and read
the others; if one of them coerces before validating, say so and correct the row.

---

## Steps, in order

1. Do the **MUST RULE** reading and write the Law reading record.
2. **Write the failing test first.** Build a `GateOutcome` payload in the pre-S184 shape, write it to
   a real `GraphStore`, read it back, and validate it. Confirm it **fails on today's code** and paste
   that failure into the handback. A test that passes before your change has not tested this.
3. Change `isinstance(data, dict)` → `isinstance(data, Mapping)` and import `Mapping` from
   `collections.abc` (note the file already imports from `typing`; follow the module's existing style).
4. Re-run the test — it must now pass — plus the full existing PM contract suite.
5. Check the other `isinstance(..., dict)` sites named under *Traps*, and report what you found even
   if the answer is "all safe".
6. `make ci` redirected **to a file**, then read the file.
7. Bump the PATCH digits, fill the sprint doc, `docs/design-log.md` (amend DL-143 to CLOSED), and the
   work-queue row for item 40.

---

## Test plan

| # | Test | Passes only if |
| --- | --- | --- |
| 1 | Pre-S184 payload **round-tripped through a real `GraphStore`** validates to `GateStatus.PASSED` | The shim runs against `mappingproxy`. **Must fail before the fix.** |
| 2 | Same, with `passed=False` → `GateStatus.FAILED` | The conversion is not hard-coded to one state |
| 3 | A payload with neither `outcome` nor `passed`, round-tripped, still raises | The invariant above holds — no state is invented |
| 4 | A payload already carrying `outcome`, round-tripped, is untouched | The early return still short-circuits correctly |
| 5 | `OrderIntentSet` with a `rejected[].gate_report[]` in the old shape, round-tripped, validates | The nesting depth that actually bites is covered — the failure is two levels down, not at the top |
| 6 | The `pm` stage view renders such a run without raising | The 38 errors are closed at the site they surfaced |

🪤 **Test 5 is the one that matters most.** The recursive wrap means the top-level props map is not
where this bites — `rejected.1.gate_report.5` is. A test that round-trips only a flat `GateOutcome`
would pass while the real bug survived.

---

## Success factors

1. 🟩 **The new test fails on `main` and passes after the change** — both outputs pasted.
2. 🟩 `make ci` exit 0, 100 % coverage, redirected to a file and read.
3. 🟩 **The live sweep returns zero `ERROR`s** across every `RunRequest` on the spine, with the
   before (`38 ERROR, 16 FAIL, 1 PASS`) and after tallies both quoted. **This is the closing
   measurement.** The `FAIL` count may move only if you can explain why.
4. 🟩 `make gate-ran` exits 0 for the merged SHA, run from the worktree whose `HEAD` is that commit.
5. 🟩 The other `isinstance(..., dict)` sites reported on, either way.

---

## Traps

🪤 **`mappingproxy` is not a `dict`, and it is not the only such type.** `isinstance(x, dict)` applied
to anything that came out of a `GraphStore` is permanently `False`, at every nesting depth. When you
sweep the other call sites, the question is not "does this look like graph data" but "can this value
have come from `_frozen_value`".

🪤 **I swept the tree and believe `contracts/portfolio_manager.py:40` is the only live instance** —
every other hit reads `json.loads` output or an HTTP payload, which really are `dict`s, and
`narrative()` (`agents/deliberator/review_record.py:85`) is called only at write time with
in-process dicts (`agents/deliberator/poll.py:86`). **Verify that; do not inherit it.** If you find a
second instance, it is a finding worth more than the fix.

🪤 **`ValidationError` subclasses `ValueError`.** That is why S191's guarded call degrades instead of
raising, and it is why a bare `except ValueError` elsewhere could be *hiding* this defect rather than
handling it. Note any you find.

🪤 **Do not measure `make ci` through a pipe** — `make ci | tail` reports `tail`'s exit code. Redirect
to a file and read the file.

🪤 **The sweep needs `.env` and the repo root.** A script run from outside the repo silently gets the
in-memory store and every count reads 0 — that is DL-124's shape, and it would report a triumphant
"zero errors" that means nothing.

---

## Guardrails (every sprint)

- Branch `sprint-193-a-shim-that-never-runs-is-not-a-shim`; never commit to `main`.
- `make ci` locally **before** pushing; then push and require `make gate-ran` to exit 0 for the exact
  SHA, run from the worktree at that commit.
- Module size: hard block at 200 lines, warning at 150. No `# noqa` to bypass.
- Architecture boundaries are import-linter-enforced; add no import that crosses one.
- 🪤 **Check `git branch --show-current` immediately before every commit** — this working tree is
  shared, and a commit has landed on the wrong branch here before.

---

## Sequencing after merge

**No deploy is required and none should be done for this alone.** The fix lands in `contracts/`,
which every agent image carries — but nothing in the live path is currently failing, so there is no
live defect for a deploy to repair. It rides along with the next fleet move. **Say this in the
handback rather than leaving it implied**, so nobody retags on a fix that changes no running
behaviour.

---

## Handover — paste this to Codex

> Build **Sprint 193** from `docs/sprints/sprint-193-a-shim-that-never-runs-is-not-a-shim.md`.
>
> S184 shipped a back-compat validator for pre-S184 PM gate payloads. It has **never executed in
> production**: it opens with `isinstance(data, dict)` and the graph store returns `MappingProxyType`
> at every nesting depth, so it takes its early return on every payload it exists to convert. The
> acceptance gate consequently **cannot read 38 of the 55 runs on the spine**, and the dashboard
> raises rather than renders on any of them.
>
> The one-word fix is `dict` → `Mapping`. **That is not the deliverable.** The deliverable is a test
> that round-trips the payload through a real `GraphStore` before validating it — one that fails on
> `main` today — because the reason this survived is that the existing tests hand the validator plain
> dict literals. Write that test first and paste its failure before you fix anything.
>
> Read the MUST RULE section first: this touches `contracts/`, so answer the law-cycle question
> yourself rather than inheriting my reading that no full cycle is triggered. `PM-NEV-09` binds.
>
> Close with the measurement that opened it: the acceptance sweep over every `RunRequest` on the
> spine returning **zero `ERROR`s**, quoted before and after. Fill the Closeout block at the bottom.

---

## Handback contract — MANDATORY

Report, in this order: what you changed and why · the **failing** test output from before the fix ·
the passing output after · `make ci` result (from the file, with the tally) · the merged SHA and
`make gate-ran` result · the **live sweep tallies, before and after** · the other
`isinstance(..., dict)` sites you checked and what you found · anything you could not do.

🚨 **Do not hand back with the Closeout block below unfilled.**

---

## Law reading record — fill BEFORE writing code

| Law file | Read in full? | Clauses relied on | Status (🟩/⬜) | Notes |
| --- | --- | --- | --- | --- |
| `agents/portfolio_manager/laws/laws.md` | Yes | `PM-NEV-09`, `PM-TYP-03` | 🟩 | `PM-NEV-09` requires not-evaluated gates to stay distinct from passed gates; `PM-TYP-03` requires `GateOutcome` to carry the three states and keeps `gate_report` additive for older payloads. Neither clause narrows accepted containers to plain `dict`. |
| `agents/portfolio_manager/laws/test-plan.md` | Yes | `PM-NEV-09`, `PM-TYP-03` | 🟩 | Both relied-on clauses are green. The new regression test cites `PM-NEV-09` because it protects the historical-reader path from silently collapsing missing state. |
| `docs/laws/conventions.md` | Yes | §3, §7, §9 | N/A | Functional tests must cite the law ID they prove; discovered law/code drift belongs in the central drift register. |
| `docs/laws/drift-register.md` | Yes | `DRIFT-044`, `DRIFT-046` | CORRECTED | S184 already corrected the tri-state and missing-gate drift. This sprint repairs the historical reader for that existing contract rather than opening a new law gap. |

**Law-cycle answer:** This changes `contracts/portfolio_manager.py`, but it does **not** add a new
agent guarantee or change any contract field. My reading is that a full law cycle is **not**
triggered: S184 already promised that legacy `passed` payloads are accepted as the tri-state
`outcome`, and widening the validator from `dict` to `Mapping` changes only which immutable
container type can reach that existing conversion. A payload with neither `outcome` nor `passed`
must still fail validation, so `PM-NEV-09`'s invariant remains intact.

---

## Test plan results — fill at handback

| # | Test | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Round-tripped pre-S184 payload → `PASSED` | 🟩 Passes after red proof | Red: `GateOutcome.model_validate(mappingproxy(...passed=True...))` raised missing `outcome`; green: `tests/test_pm_gate_outcome_graph_roundtrip.py` passed. |
| 2 | Round-tripped `passed=False` → `FAILED` | 🟩 Passes after red proof | Red: `GateOutcome.model_validate(mappingproxy(...passed=False...))` raised missing `outcome`; green: same focused run passed. |
| 3 | Shapeless payload still raises | 🟩 Passed before and after | `test_shapeless_gate_round_tripped_through_graph_still_raises` keeps the invariant: no `outcome` and no `passed` still raises. |
| 4 | Payload with `outcome` untouched | 🟩 Passed before and after | `test_current_outcome_round_tripped_through_graph_is_not_rewritten` preserves authoritative `outcome=not_evaluated`; `.passed` still raises. |
| 5 | Nested `rejected[].gate_report[]` validates | 🟩 Passes after red proof | Red: `OrderIntentSet` raised at `rejected.0.gate_report.0.outcome`; green: same graph-roundtrip file passed. |
| 6 | `pm` stage view renders | 🟩 Passes after red proof | Red: `trading_observatory_chain.pm` raised the same nested validation error; green: stage view returns `approved=0  rejected=1`. |

---

## Closeout — evidence

**Fill this at handback. A placeholder here means the sprint is not done.**

- **Merged SHA:** `a9603d7f5390ba8b94c7b33ce961a7fc3c1bbce9`
- **Version:** `0.94.04`
- **`make ci`:** `make ci *> ..\s193-make-ci.txt; ...` exited 0. File evidence:
  ruff/format/mypy/import-linter passed; module-size had warnings only
  (`contracts\portfolio_manager.py` 151 lines, below hard block); law coverage and
  PARAM sync emitted existing warn-only debt; pytest `2448 passed, 6 skipped` with
  `100.00%`; pip-audit found no known vulnerabilities; detect-secrets and untracked
  secret scan passed.
- **`make gate-ran`:** passed from the main worktree at
  `a9603d7f5390ba8b94c7b33ce961a7fc3c1bbce9`:
  Security Findings success, CI success, CodeQL success, Build and push agent
  images success, plus configured graph/dependency update workflows success.
- **Sweep before:** `38 ERROR, 16 FAIL, 1 PASS` over 55 runs *(measured 2026-09-01)*
- **Sweep after:** `0 ERROR, 54 FAIL, 0 NO_TRADE, 0 UNPROVEN, 2 PASS` over 56
  `RunRequest`s on Postgres (2026-09-02); the denominator moved because
  `sched-2026-09-01` now exists and passes beside `sched-2026-08-31`.
- **Other `isinstance(..., dict)` sites checked:** tree sweep found the fixed
  contract validator as the only graph-prop compatibility instance. Other hits read
  `json.loads`, HTTP/LLM/API payloads, env/config data, or tests; `narrative()` reads
  in-process write-time dicts only. Graph `OrderIntentSet.model_validate(...)` readers
  in observatory, deliberation view, execution, deliberator, batch trace, and
  shadow-book joins are covered by the contract-level fix; no per-site coercion added.
- **Deploy:** not required and none done. This fixes retrospective readers; fresh
  production runs already write `outcome`, and the fix can ride the next fleet move.

---

## Return notes

The live denominator moved from 55 to 56 because `sched-2026-09-01` appeared
between the sprint measurement and handback; the postcondition that mattered was
still met: historical PM-reader `ERROR`s are now zero. This handback
distinguishes the implementation merge proof from any docs-only closeout commit
that records the evidence after the proof.
