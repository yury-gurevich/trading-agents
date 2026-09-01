<!-- Agent: planning | Role: sprint handover — one verdict for a quiet night, whatever the ordering -->
# Sprint 191 — a quiet night gets the same verdict twice

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-191-a-quiet-night-gets-the-same-verdict-twice`
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** [ADR-0022](../decisions/0022-the-veto-gates-buys-never-exits.md) the veto gates buys, never exits · `DL-140` (take it, then re-check at merge) · work-queue item 38

> **Why this bump kind.** No new capability. `EXEC-OBS-04` already promises that acceptance severity
> follows the posture, and the acceptance view cannot deliver it: it reds a run whose every artefact
> is correct. That is a **fix**, so PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/execution/laws/laws.md` | The execution agent's **locked constitution** (currently **v1.4**) | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/execution/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`EXEC-OUT`**, **`EXEC-OBS`**. Specifically **`EXEC-OUT-09`** (what an
`ExecutionRun` must record) and **`EXEC-OBS-04`** (fault/acceptance severity follows posture).

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

**My reading is No, and you must confirm it rather than inherit it.** Nothing in `contracts/` is
touched, no `ExecutionRun` property is added or changed, and the agent makes no new promise — the
change is confined to how `orchestration/` *reads* facts the execution agent already writes. The
clause already promises the behaviour; the reader fails to deliver it.

🪤 **But check `EXEC-OBS-04`'s actual wording before you accept that.** If it enumerates the statuses
under which advisory acceptance stays green and **omits `not_required`**, then the law is *silent*
where this sprint needs a decision — that is a `DRIFT-056` row and a report, **not** a quiet
edit and not a reason to stop.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `orchestration/packs/trading_deliberation_view.py` | `agents/execution/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `EXEC-OBS-04` — acceptance severity follows the posture; `EXEC-OUT-09` — the status vocabulary this view reads |
| `orchestration/tests/test_trading_deliberation_posture.py` | same | Existing tests already cite `EXEC-OUT-09 / EXEC-OBS-04`; new tests must cite too (conventions §3) |

⚠️ **The invariant this sprint must not break:** a run that submitted a **buy** while recording
`deliberation_status="not_required"` must **still** breach. That combination means the veto was
skipped on exposure-opening orders, and it is the one thing the current red is accidentally
catching. If your change makes that green, stop and report.

---

## Goal

On a quiet day — one where the portfolio manager approves no buy — the advisory acceptance gate
returns the **same verdict regardless of when the deliberator writes its `DeliberationRun`**. Today
the verdict is decided by a race: if the (empty) run lands *before* execution polls, the status is
`applied` and acceptance **passes**; if it lands *after*, the status is `not_required` and acceptance
**fails**. After this sprint both orderings pass, and a `not_required` that coexists with an approved
buy still fails.

## Why (context)

`sched-2026-08-31` completed **8/8 stages with zero orders** and returned
`ACCEPTANCE FAIL  deliberation.advisory_attribution: missing`. Every artefact was correct: posture
`advisory`, status `not_required`, and the `DeliberationRun` narrating *"No PM-approved orders
required deliberation."* `not_required` is a **declared** status
(`agents/execution/deliberation_gate.py:38`, ADR-0022, execution laws v1.4) that `ADVISORY_STATUSES`
omits (`orchestration/packs/trading_deliberation_view.py:20`), so `_advisory_attribution` returns
`missing` and the gate reds.

Nine hours later `verify-2026-09-01-s190-stops` ran the **same as-of, the same 99 tickers, the same
zero approved orders** — and returned `ACCEPTANCE PASS`, because that time the deliberator's empty
run landed first.

**The cost is that a red stops meaning anything on a quiet night.** A red that means *nothing to
trade* is indistinguishable at a glance from a red that means *the fleet broke* — DL-125's
cries-wolf shape, which the operator's etalon bar names explicitly ("the evidence discipline catches
its own defects without the operator in the loop"). A **non-deterministic** red is worse than a
consistent one: it cannot be reproduced on demand, so it trains the reader to discount it.

### Measured, 2026-09-01 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| A quiet run can FAIL acceptance | `FAIL deliberation.advisory_attribution: missing` | *[measured 2026-09-01]* `scripts/accept.py --run-id sched-2026-08-31` |
| The identical inputs can PASS | `ACCEPTANCE PASS` | *[measured 2026-09-01]* `scripts/accept.py --run-id verify-2026-09-01-s190-stops`, 99 tickers, as-of 2026-08-31, `approved=0` both runs |
| The difference is ordering, nothing else | `not_required` vs `applied` | *[measured 2026-09-01]* both `ExecutionRun`s carried `deliberation_posture=advisory`; `sched` PMRun 22:41:27 → `DeliberationRun` 22:42:28, i.e. **after** execution polled |
| `not_required` covers **two** cases | no `DeliberationRun` **and** `not has_buy(order_set)` | *[measured 2026-09-01]* read in `agents/execution/deliberation_gate.py:70-84` |
| `ADVISORY_STATUSES` omits it | `{applied, applied_failed_open, proceeded_unvetoed}` | *[measured 2026-09-01]* `orchestration/packs/trading_deliberation_view.py:20` |
| View module size | **136** lines | *[measured 2026-09-01]* `wc -l` |
| Graph vocabulary unchanged | no new label or property | *[measured 2026-09-01]* the change reads existing props only — this is what keeps the deploy an image-only retag |
| Second instance of this policy gap | the `analyst.scored: 0 < floor` no-trade signature, 2026-07-09 | *[ASSUMED — not re-measured]* recorded in the `/diagnose-run` known-signatures table; **not** in scope here, but if you find they share a fix, say so rather than building it |

---

## Scope — and what is deliberately NOT here

1. **🎯 The failing test first.** A `DeliberationRun` whose linked `ExecutionRun` carries
   `deliberation_posture="advisory"` and `deliberation_status="not_required"`, with **no approved buy
   intent**, produces **no breach**. Assert on the breach list from the acceptance view, not on a
   printed string.
2. **The sells-only case passes too.** Same shape, but the PM approved one or more **sell** intents.
   ADR-0022 makes this legitimate: the veto gates buys, never exits, so `has_buy` is false and the
   status is honestly `not_required` *with orders submitted*.
3. **The negative still breaches.** Same shape, but with an approved **buy** intent. This must still
   return `missing` and breach.
4. **Every other status is untouched.** `applied`, `applied_failed_open` (with and without a reason),
   `proceeded_unvetoed`, and the whole `binding` branch behave exactly as they do today.

### Out of scope (do NOT build this sprint)

- **Do not change the deliberator's write ordering.** The race is real, but this sprint makes the
  *verdict* insensitive to it; re-sequencing the cascade is a choreography change with a far larger
  blast radius, and it is not needed once both orderings agree.
- **Do not touch `agents/execution/`.** The statuses it writes are correct. Every fact this sprint
  needs is already on the graph.
- **Do not fix the `analyst.scored: 0 < floor` no-trade signature.** Same family, different check,
  separate decision.
- **No `laws.md` edit** unless the law-cycle question answered Yes — then the amendment is in scope
  and named above.
- **No ADR reversal.** ADR-0022 is the authority for the sells-only case, not something to revisit.

### The road not taken (LAW-06)

- **Add `not_required` to `ADVISORY_STATUSES` and stop.** Rejected: it makes scope item 3 green.
  A run that submitted buys while recording `not_required` would then be attributed as fine, and that
  combination is exactly the veto being skipped on exposure-opening orders.
- **Condition on `submitted == 0`.** Rejected: it breaks scope item 2. A sells-only run has
  `submitted > 0` and a legitimate `not_required`, and ADR-0022 requires it to pass.
- **Condition on `ExecutionRun.approved_count == 0`.** Rejected for the same reason — `approved_count`
  counts *all* approved intents, so a sells-only run reads non-zero. The question is about **buys**,
  which means reading the approved set's `action` values.
- **Add a new `ExecutionRun` property recording the submitted buy count.** Rejected: it moves the
  graph vocabulary, which turns the deploy from an image-only retag into a full `up` (S148/DL-85's
  fail-closed write guard). The fact is already derivable from the `PMRun` the view can already reach.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` as `DL-140` with their rejected alternatives BEFORE
implementing (LAW-06).**

1. **What makes `not_required` attributable?** My recommendation is *"no buy intent in the linked
   `PMRun`'s approved set"* — the view already walks to the `PMRun` via
   `graph.ancestors(node, edge_types={DELIBERATED_EDGE})` inside `_linked_execution`, so the node is
   in reach without a new traversal. **Verify that the approved set is readable and typed as you
   expect before committing to it** — it is stored as a nested structure on `PMRun.order_intent_set`,
   and if reading it proves fragile, say so and propose the alternative rather than forcing it.
2. **Where does the condition live?** `_advisory_attribution` currently takes four scalars. Adding a
   graph lookup inside it would mix traversal into a pure helper. Decide whether the buy count is
   computed by the caller and passed in, or the helper gains the node — and say why.
3. **What does the breach say when it does fire?** `missing` is uninformative for the buy case. If a
   more specific value is warranted, name it — but check it does not break the `oneof ("ok",)` check
   shape.

🪤 **Take the next free DL number (`DL-140`), then re-check it at merge.** The log has historic
duplicates and entries are prepended *and* appended. A branch cut before another DL lands will
collide even when the number was free at branch time.

---

## Blast radius — measured 2026-09-01

| What | Detail |
| --- | --- |
| Files changed | `orchestration/packs/trading_deliberation_view.py` (**136**), `orchestration/tests/test_trading_deliberation_posture.py` (**103**), possibly `orchestration/tests/test_trading_acceptance_deliberation.py` (**171**) |
| Agents affected | **None.** This is `orchestration/` only — no agent imports another, and none is touched |
| Contract change? | **No** |
| Graph vocabulary change? | **No** — reads existing properties only |
| New env keys / tunables | **None** |
| Deploy implication | **Image-only retag.** Confirm before deploying: `git show <deployed-sha>:orchestration/packs/trading_graph_vocabulary.json \| sha256sum` must equal `HEAD`'s. If they differ, something else moved the pack and it is a full `up` |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md` as `DL-140`.
3. **Plant the failing test first** (test A1) and watch it fail. Paste the red output.
4. **Implement.**
5. **Law cycle** if owed — otherwise record the answer and the `EXEC-OBS-04` reading that justifies it.
6. **Prove the guards can fail (DL-70)** — in particular, break the buy-detection and watch A3 go red.
7. **`make ci` green** — all 12 steps, **redirected to a file, never piped**.
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 Quiet day is attributable | `DeliberationRun` + `ExecutionRun{posture=advisory, status=not_required}`, PM approved **nothing** | `advisory_attribution == "ok"`; **no breach** in the returned view |
| A2 | Sells-only is attributable | same, but PM approved one or more **sell** intents (`submitted > 0`) | `"ok"`; no breach — ADR-0022's case survives |
| A3 | 🪤 A skipped veto on a buy still breaches | same, but PM approved a **buy** intent | attribution is **not** `"ok"`; the breach is still raised |
| A4 | The race yields one verdict | the two orderings from the incident: `status=not_required` and `status=applied`, both zero-buy | **both** produce no breach — the verdict no longer depends on ordering |
| A5 | Regression on every other status | `applied`, `applied_failed_open` with and without `failed_open_reason`, `proceeded_unvetoed`, and the `binding` branch | unchanged from today, including `binding`'s `debate_coverage`/`failed_open_count` checks |

Every test docstring **must cite the clause IDs** it proves (`EXEC-OUT-09` / `EXEC-OBS-04`),
matching the convention the existing tests in that file already follow.

---

## Success factors

- [ ] A `not_required` advisory run with **no approved buy** produces no acceptance breach (A1).
- [ ] A **sells-only** `not_required` advisory run produces no breach (A2).
- [ ] A `not_required` advisory run **with an approved buy** still breaches (A3) — stated explicitly,
      because this is the invariant the obvious fix destroys.
- [ ] Both orderings of the incident give the same verdict (A4).
- [ ] No change to `applied`, `applied_failed_open`, `proceeded_unvetoed`, or the `binding` branch (A5).
- [ ] No `contracts/` change, no graph-vocabulary change, no new env key or tunable — stated as
      observed, so the deploy stays an image-only retag.
- [ ] Design decisions recorded as `DL-140` with rejected alternatives.
- [ ] Law cycle done, or the law-cycle question answered No **with the `EXEC-OBS-04` wording that
      justifies it**, plus a `DRIFT-056` row if the law is silent.
- [ ] Every new guard planted, watched to fail, restored — stated per guard.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **The one-line fix passes most of the plan and destroys the invariant.** Adding `not_required` to
`ADVISORY_STATUSES` makes A1, A2 and A4 green in one character-level edit. It also makes A3 green,
which is the failure. **Write A3 before you implement.**

🪤 **`approved_count` is the wrong number.** It counts every approved intent, so a sells-only run
reads non-zero and would be wrongly treated as "had orders". The question is specifically about
**buy** intents — the same question `has_buy` answers in `agents/execution/deliberation_gate.py`.
Do not import that function across the boundary; `orchestration` may read the graph, but check the
import-linter contract before reaching for anything in `agents/`.

🪤 **A green acceptance run is not proof this worked.** `verify-2026-09-01-s190-stops` was green
*before* any fix, because of the race. If you verify against a live run, you must construct the
`not_required` ordering deliberately, or you will be reading the lucky branch. The unit tests are
the real proof here; a live run is corroboration at best.

🪤 **The view is keyed on the `DeliberationRun`.** If no `DeliberationRun` exists at all, this stage
view is never produced and no check runs — so acceptance is silent, not green, in that case. That is
a **different** hole and out of scope. Note it in Return notes if you confirm it; do not fix it here.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `trading_deliberation_view.py` **136**, `test_trading_deliberation_posture.py`
  **103**, `test_trading_acceptance_deliberation.py` **171**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. This sprint should need none; if you
  think it needs one, that is a design smell worth reporting.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 12 steps** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — `make ci | tail` reports *`tail`'s* exit code. Redirect to a file and read the file.
- Version bump of the kind named at the top (**PATCH**), `uv.lock` staged with it.
- Secrets never through the worktree — a worktree has **no `.env`**, so any proof needing live data
  is vacuous there. **State which tree you ran in.** This sprint's proofs are unit tests and need
  no `.env`, which is deliberate.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving** — it resolves the SHA
   from the working directory and ignores a `SHA=` argument. **Check the printed SHA against
   `git rev-parse HEAD`.**
2. Merge to `main` locally and push. 🪤 Check you are not on the branch already.
3. **Post-merge CodeQL** — `codeql.yml` runs only on `main`.
4. **Deploy: image-only retag**, after re-confirming the vocabulary hash matches (Blast radius).
   🪤 `main` may carry Dependabot merges that reached it ungated (work-queue item 39) — check the
   SHA you are building is gate-proven before the fleet moves.

---

## Handover — paste this to Codex

```text
Build sprint 191 in the trading-agents repo, on a new branch
`sprint-191-a-quiet-night-gets-the-same-verdict-twice` cut from main. Never commit to main.
The full spec is docs/sprints/sprint-191-a-quiet-night-gets-the-same-verdict-twice.md — read it
whole before you start. This summary does not replace it.

THE PROBLEM, MEASURED 2026-09-01.
Two pipeline runs with identical inputs (same as-of, same 99 tickers, zero approved orders)
returned opposite acceptance verdicts. sched-2026-08-31 returned
  ACCEPTANCE FAIL  deliberation.advisory_attribution: missing
and verify-2026-09-01-s190-stops returned ACCEPTANCE PASS. The only difference was ordering: the
deliberator writes an empty DeliberationRun, and if it lands BEFORE execution polls, execution
records deliberation_status="applied"; if AFTER, it records "not_required". ADVISORY_STATUSES in
orchestration/packs/trading_deliberation_view.py:20 contains {applied, applied_failed_open,
proceeded_unvetoed} and omits not_required, so _advisory_attribution returns "missing" and the
gate reds. The verdict on a quiet night is therefore decided by a race.

WHAT TO MAKE TRUE.
A quiet day gets the same verdict either way. Both orderings pass, AND a not_required that
coexists with an approved BUY still fails.

MUST RULE — READ THE LAWS FIRST, BEFORE ANY CODE.
Read agents/execution/laws/laws.md (LOCKED, currently v1.4) and its test-plan.md, plus
docs/laws/conventions.md and docs/laws/drift-register.md. The binding clauses are EXEC-OUT-09
(what an ExecutionRun records) and EXEC-OBS-04 (acceptance severity follows posture). Fill the
"Law reading record" section of the spec BEFORE your first code change. If a law contradicts the
spec, STOP and report — the law is more likely right. If EXEC-OBS-04 enumerates the green
statuses and omits not_required, the law is SILENT where a decision is needed: file a
drift-register row (next free is DRIFT-056) and report it. Do NOT edit laws.md.

LAW-CYCLE ANSWER (confirm, do not inherit): I read it as No — nothing in contracts/ changes, no
ExecutionRun property is added, and the agent makes no new promise. Confirm against EXEC-OBS-04's
wording and record your answer.

ORDER OF WORK.
1. Read laws, write the Law reading record.
2. Record the design decisions in docs/design-log.md as DL-140, WITH the rejected alternatives.
   Re-check the number is still free when you merge — the log has historic duplicates.
3. Write the FAILING TEST FIRST and paste the red output before implementing.
4. Implement. 5. Guards. 6. make ci. 7. Fill the handback sections.

THE THREE CASES THAT MATTER.
not_required means TWO things (agents/execution/deliberation_gate.py:70-84): no DeliberationRun
existed when execution polled, AND has_buy(order_set) was false. So:
  A1 zero approved intents        -> must be attributable, no breach
  A2 sells-only, submitted > 0    -> must be attributable, no breach (ADR-0022: the veto gates
                                     buys, never exits)
  A3 an approved BUY present      -> must STILL breach. This is a skipped veto on exposure-opening
                                     orders and is the one thing today's red accidentally catches.
  A4 both race orderings          -> same verdict
  A5 applied / applied_failed_open (with and without reason) / proceeded_unvetoed / the whole
     binding branch -> unchanged

DO NOT:
- Do NOT just add "not_required" to ADVISORY_STATUSES. It is a one-character-class fix that makes
  A1, A2 and A4 pass and SILENTLY BREAKS A3. Write A3 first.
- Do NOT key the condition on submitted == 0 — that breaks A2, the sells-only case.
- Do NOT key it on approved_count == 0 — approved_count counts ALL approved intents, so sells-only
  reads non-zero. The question is about BUY intents specifically.
- Do NOT add a new ExecutionRun property. That moves the graph vocabulary, which turns the deploy
  from an image-only retag into a full `up` against a fail-closed write guard. The fact is already
  derivable from the PMRun the view can already reach.
- Do NOT change the deliberator's write ordering or touch agents/execution/. The statuses written
  are correct.
- Do NOT import has_buy from agents/ into orchestration/ without checking the import-linter
  contract first.

TRAPS:
- A green live run proves nothing here — verify-2026-09-01-s190-stops was green BEFORE any fix,
  because of the race. The unit tests are the proof.
- The view is keyed on the DeliberationRun; if none exists the stage view is never produced and no
  check runs at all. That is a DIFFERENT hole. Out of scope — note it in Return notes if you
  confirm it, do not fix it.

CONVENTIONS:
- Every test docstring cites the clause IDs it proves (EXEC-OUT-09 / EXEC-OBS-04), matching the
  existing tests in orchestration/tests/test_trading_deliberation_posture.py.
- Every module stays under 200 lines. Current: trading_deliberation_view.py 136,
  test_trading_deliberation_posture.py 103, test_trading_acceptance_deliberation.py 171.
- Version: next available PATCH at merge. Do NOT pin a number in the spec; read main's version at
  merge time and bump the last two digits. Stage uv.lock with it.
- make ci must be run REDIRECTED TO A FILE, never piped: `make ci > /tmp/ci.txt 2>&1 ; echo $?`.
  A pipe reports the exit code of the last command in the pipe, not make's, so a real failure
  reads as green.
- Prove each guard can fail (DL-70): break the implementation, watch the guard go red, restore.
  State this per guard.

HANDBACK IS A CONTRACT.
Fill Law reading record, Test plan results, Closeout — evidence (with REAL pasted output: the red
run first, then the green), and Return notes. Set Status: BUILT. State anything not met plainly
as "verified failing" or "not done" — never write a Result for work you have not done. A handback
with a placeholder left intact is returned, not repaired.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?**

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

**Tests added beyond the plan:**

---

## Closeout — evidence

**Status:**

**Tree the proofs ran in (and `.env` present?):**

**Result:**

**Files changed:**

**Design decisions:** recorded as `DL-140` —

**Proof — the red run first:**

```text
```

**Proof — the green run:**

```text
```

**Guards planted:**

**Module line counts:**

**`make ci`:** redirected to `<path>`. Exit code . , coverage . pip-audit . detect-secrets .

**`make gate-ran`:** run from `<worktree path>` at `<full 40-char SHA>`:

```text
```

**Not met / verified failing:**

---

## Return notes

-
-
-
