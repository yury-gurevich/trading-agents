<!-- Agent: planning | Role: sprint handover -->
# Sprint 214 — a `revise` is a finding, an `overturn` is a block

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-214-revise-is-a-finding`
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** S–M
**Decisions:** implements [ADR-0029](../decisions/0029-a-revise-is-a-finding-an-overturn-is-a-block.md)
decisions **1** and **5** only · closes [DL-173](../design-log.md) · DRIFT row expected

> **Why this bump kind.** PATCH. No new capability and no new endpoint. Two verdicts that already exist
> stop being treated as one, and a failure that already has a lawful path stops borrowing a verdict's name.

> 🚨 **ADR-0029 decisions 2, 3 and 4 are NOT in this sprint.** Decision 3 (telling the judge what its
> verdicts do) is deliberately sequenced **after** this one so the first measurement is clean: shipping
> both together would make it impossible to tell a change in *consequence* from a change in *behaviour*.
> See **Sequencing** below. Do not implement them here even though the ADR contains them.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/deliberator/laws/laws.md` | The deliberator's **locked constitution** (LOCKED **v1.7**) | **You are amending it.** `DLIB-OUT-02` changes meaning — full law cycle owed |
| `agents/execution/laws/laws.md` | Execution's **locked constitution** (LOCKED **v1.6**) | **Read-only if execution code does not change** — see the law-cycle question |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding clauses: **`DLIB-OUT-02`** (*"Each `DeliberationRun` records verdicts, vetoed tickers, …"*),
**`DLIB-NEV-06`** (*"Never hides a failed debate or peer call as a clean veto"* — decision 5 is exactly
this clause one level down), **`EXEC-NEV-01`** (*"Never decides what to trade"*), and **LAW-02**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, record it and add a `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered **YES**, with the reason

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**Yes — for the deliberator.** `DLIB-OUT-02` guarantees what `vetoed_tickers` contains, and this sprint
changes what goes into it. That is an output guarantee changing meaning, so the deliberator owes a full
law cycle: clause amendment, `test-plan.md` row, changelog entry, rollup recount, DRIFT row.

🪤 **`contracts/deliberator.py` does NOT change.** `Ruling = Literal["uphold", "overturn", "revise"]`
already declares all three values. This sprint changes only how they are **consumed**. If you find
yourself editing `contracts/`, stop — you have taken a wider path than this spec authorises.

🎯 **Execution may need no code change at all.** `drop_vetoed` reads `vetoed_tickers`
(`agents/execution/deliberation_gate.py:83`). If the deliberator writes fewer tickers into it, execution's
behaviour follows with no edit and `EXEC-NEV-01` stays literally true — execution still honours an arrived
veto exactly as before; what *counts* as one changed upstream. **Confirm this by reading, and say so in
the Law reading record.** If it holds, execution's law book is read-only for this sprint.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/deliberator/review_batch.py` (**98** lines) | `agents/deliberator/laws/laws.md` + `test-plan.md` | `DLIB-OUT-02` — the veto predicate lives at `:87` |
| `agents/deliberator/review_record.py` (**100** lines) | same | `fail_open_review` is the lawful non-answer marker |
| `kernel/deliberation.py` (**198** lines 🚨) | `docs/laws/conventions.md`; LAW-02 | Kernel currently decides a *policy* default; see trap 2 |
| `agents/execution/deliberation_gate.py` (**147** lines) | `agents/execution/laws/laws.md` | Read to confirm no change is needed |

---

## Goal

`vetoed_tickers` contains **only** tickers whose verdict is `overturn`. A `revise` is recorded in full —
verdict, rationale, transcript, `debates` payload — and its order **proceeds**. A judge that cannot
answer is **not** recorded as `revise`: it takes the existing fail-open path, so the order proceeds
**loudly** (`applied_failed_open` + fault) rather than silently.

## Why (context)

Four consecutive scheduled sessions closed with **zero fills** while every stage ran green and
`ACCEPTANCE PASS` printed. The cause is a code-level collapse, not a model fault: the deliberator returns
three rulings and `review_batch.py:87` reduces them to two outcomes. The referee's critiques are
*systemic*, and rejecting a trade is the only channel it has, so system critique is spent as trade
rejection and the book stops trading. Three experiments show those critiques are correct **and** that
acting on them does not pay ([EXP-008](../research/experiments/EXP-008-correlation-cutoff-replay.md),
[EXP-011](../research/experiments/EXP-011-regime-markov-and-barrier-calibration.md),
[EXP-012](../research/experiments/EXP-012-volatility-sizing-ten-year-replay.md)). Full reasoning:
[DL-173](../design-log.md); the ruling: [ADR-0029](../decisions/0029-a-revise-is-a-finding-an-overturn-is-a-block.md).

### Measured, 2026-09-18 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| The veto predicate | `if review.verdict != "uphold": vetoed.append(...)` | *[measured]* `agents/deliberator/review_batch.py:87` |
| Verdict mix, all-time | `revise` **164**, `uphold` **163**, `overturn` **22** over **349** reviewed orders in **63** runs | *[measured 2026-09-18, live spine]* every `DeliberationRun.verdicts` |
| Expected effect on the block rate | **53 % → ~6 %** | *[derived]* `overturn` 22 / 349 |
| Nothing is ever revised | `drop_vetoed` removes the ticker; no resize path exists | *[measured]* `agents/execution/deliberation_gate.py:83`, `agents/execution/pm_execution.py:58` |
| It has stopped discriminating | all-time 17 of 30 acting runs vetoed *some*; **since 09-14, 4 of 5 vetoed all** | *[measured 2026-09-18]* 50 multi-order runs |
| Not an outage | **1** `unparseable` and **1** `defaulting to revise` across all 63 runs | *[measured 2026-09-18]* narrative scan |
| 🚨 The two failure paths disagree today | a raised LLM error → `fail_open_review` → verdict `uphold`, `failed_open=True`, **does not block**; an *unparseable* judge reply → `Verdict("revise", …)` → **blocks** | *[measured]* `agents/deliberator/review_record.py:41-52` vs `kernel/deliberation.py:105-115` |
| The lawful non-answer marker already exists | `fail_open_review(reason)` sets `failed_open=True` and a queryable `failed_open_reason` | *[measured]* `agents/deliberator/review_record.py:41` |
| Fail-open is already loud | `applied_failed_open` + `record_failed_open_submit` fault | *[measured]* `agents/execution/pm_execution.py:90`, ADR-0022 amendment 2026-08-13 |
| `kernel/deliberation.py` size | **198 / 200** | *[measured]* `wc -l` |

---

## Scope — and what is deliberately NOT here

1. **The veto predicate becomes `== "overturn"`.** `revise` and `uphold` both leave `vetoed_tickers`.
   Everything else `_assemble` records is unchanged — `verdicts`, `debates`, `transcript`,
   `real_debate_count`, `failed_open_*` all keep their current contents.
2. **A non-answer is no longer a `revise`.** Where `_parse_verdict` today returns `Verdict("revise", …)`
   for an empty, unparseable, unrecognised or stopped judge response, the deliberator must instead
   produce the **existing** `fail_open_review(reason)` marker, so the order joins `failed_open_tickers`,
   the run stamps `applied_failed_open`, and the fault fires.
   🎯 **This also makes the two failure paths agree**, which they do not today (see the measured table).
3. **Decide where that policy lives.** Today `kernel/deliberation.py` picks `revise` — a *policy* choice
   in the layer that should only parse. Prefer: the kernel reports "could not read a ruling" and the
   **agent** decides what that means. Whatever you choose, record it (design decision 1).
4. **Law cycle for the deliberator.** `DLIB-OUT-02` amended so it states that `vetoed_tickers` carries
   `overturn` only; a new clause for the non-answer rule if `DLIB-NEV-06` does not already cover it —
   **read it first and say which**. `test-plan.md` row per clause, changelog, rollup recount, DRIFT row.
5. **Keep every module under 200 lines.** `kernel/deliberation.py` is at **198**. If your change adds a
   line there, **split the module** — do not trim a docstring to fit.

### Out of scope (do NOT build this sprint)

- **ADR-0029 decisions 2, 3 and 4.** No prompt change, no order-specific-ground requirement, no findings
  register, no deduplication. Decision 3 in particular is sequenced *after* this deliberately.
- **No `contracts/` change.** The vocabulary is already three-valued.
- **No execution behaviour change**, unless reading proves one is required — then report before writing.
- **No change to the grace period, the posture selector, or fail-open's existing semantics.**
- **No resize-on-revise.** Ruled out in ADR-0029 and in the 2026-06-27 founding note.
- **No retroactive reclassification** of past `DeliberationRun` rows.

### The road not taken (LAW-06)

- **Make `revise` blocking only when it cites an order-specific fact.** Rejected in ADR-0029: it puts a
  block/no-block decision inside a natural-language judgement about another natural-language judgement.
- **Map a non-answer to `uphold` directly** instead of `fail_open_review`. Rejected: it would be silent,
  which is the exact failure `DLIB-NEV-06` and ADR-0022's amendment exist to prevent.
- **Change `drop_vetoed` in execution instead of the deliberator.** Rejected: it would put the meaning of
  a deliberator verdict inside execution, where `EXEC-NEV-01` says execution never decides what to trade.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Where the non-answer policy lives** — kernel returns a sentinel / raises / returns an optional, and
   the agent maps it. What hangs on it: `kernel/deliberation.py` is at 198 lines, `judge_verdict` and
   `deliberate` are both callers, and `kernel/deliberation_eval.py` reads `result.verdict.ruling`.
   **Grep every caller before changing a return type.**
2. **Whether `DLIB-NEV-06` already covers the non-answer rule** or a new clause is owed. Read it and
   decide; do not add a clause the book already has.

🪤 **Take the next free DL number, then re-check it at merge.** `main` is at **DL-173**; it may gain more.

---

## Blast radius — measured 2026-09-18

| What | Detail |
| --- | --- |
| Files changed | `agents/deliberator/review_batch.py` (98), `agents/deliberator/review_record.py` (100), `kernel/deliberation.py` (**198** — may need a split), `agents/deliberator/laws/laws.md` + `test-plan.md`, `docs/design-log.md`, `docs/laws/drift-register.md`, new test module, `pyproject.toml` + `uv.lock` |
| Agents affected | **deliberator** (behaviour), **execution** (behaviour follows, likely no code change) |
| Contract change? | **No** |
| Graph vocabulary change? | **No** — same properties, different contents |
| New env keys / tunables | **None** |
| Deploy implication | **Full `up` NOT required** — no new label, property, env key or tunable. **Image-only retag** of the deliberator (and execution if it changed). Confirm against `docs/deployment.md` before deploying |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md`.
3. **Plant the failing tests first** and watch them fail. Paste the red output.
4. **Implement.**
5. **Prove the guards can fail (DL-70)** — break the implementation, watch each guard go red, restore.
6. **Law cycle** — clause, test-plan row, changelog, rollup recount, DRIFT row.
7. **`make ci` green** — all 12 steps, **redirected to a file, never piped**.
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

All tests use an in-memory `GraphStore` / fixtures. **No `.env`, no network** — they must run in a worktree.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 A `revise` does not veto | Batch of 3 approved; verdicts `revise`/`revise`/`uphold` | `vetoed_tickers == []`; `verdicts` still records all three; `debates` carries each rationale |
| A2 | 🎯 An `overturn` still vetoes | verdicts `overturn`/`uphold` | `vetoed_tickers == ["<the overturned ticker>"]` |
| A3 | Mixed set | `overturn`/`revise`/`uphold` | Exactly one ticker vetoed; the `revise` ticker is **absent** from `vetoed_tickers` and **present** in `verdicts` |
| A4 | 🪤 An unparseable judge reply is **not** a `revise` | Judge returns `"{{{"` | The ticker appears in `failed_open_tickers` with a reason; its verdict is **not** `revise`; `vetoed_tickers` does not contain it |
| A5 | 🪤 …and it is **loud** | as A4, through execution | `ExecutionRun.deliberation_status == "applied_failed_open"` and the fail-open fault is raised |
| A6 | Empty and stopped judge responses | empty string; `LLMCompletionStoppedError` | Same treatment as A4 — one path, not three |
| A7 | 🪤 Execution honours the narrowed veto unchanged | `DeliberationRun` with `vetoed_tickers=["X"]`, approved X + Y | `drop_vetoed` removes only X — proves execution needed no edit |
| A8 | Old rows still read | `DeliberationRun` predating this change | Nothing raises; no retroactive reclassification |

🪤 **A4–A6 are the safety tests.** If they are weak, this sprint converts a fail-*closed* default into a
silent fail-*open*, which is the one outcome ADR-0029 refuses. Write them first.

---

## Success factors

- [ ] `vetoed_tickers` contains only `overturn` verdicts; `revise` and `uphold` orders proceed.
- [ ] Every verdict, rationale and transcript is still recorded — **nothing stops being written**.
- [ ] A non-answer (empty / unparseable / unrecognised / stopped) produces `failed_open`, never `revise`,
      and reaches execution as `applied_failed_open` with its fault.
- [ ] `contracts/` diff is **empty**.
- [ ] Execution code unchanged, **or** the change is named and justified in the handback.
- [ ] Design decisions recorded with rejected alternatives.
- [ ] Deliberator law cycle done: clause amended, test-plan row, changelog, rollup recounted, DRIFT filed.
- [ ] Every new guard planted, watched to fail, restored — stated per guard.
- [ ] Every touched module < 200 lines (`kernel/deliberation.py` starts at **198**).
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **The silent fail-open.** Today an unparseable judge reply *blocks*. Change the veto predicate without
changing the parse default and that same reply silently stops blocking. Tests A4–A6 exist for this.

🪤 **`kernel/deliberation.py` is at 198 / 200.** Two added lines break `make ci`. Split the module; do not
delete a docstring to make room, and do not `# noqa`.

🪤 **The rollup is recounted, not edited.** Run the coverage gate and copy what it prints.

🪤 **"Fewer vetoes" is not proof.** The postcondition is *which* verdicts veto, not *how many*. A bug that
empties `vetoed_tickers` entirely also reduces vetoes — A2 and A7 are what separate the two.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `kernel/deliberation.py` **198**, `agents/execution/deliberation_gate.py` **147**,
  `agents/deliberator/review_record.py` **100**, `agents/deliberator/review_batch.py` **98**,
  `agents/execution/pm_execution.py` **101**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 12 steps** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — `make ci | tail` reports *`tail`'s* exit code. Redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it.
- Secrets never through the worktree — a worktree has **no `.env`**. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving** — it ignores a `SHA=`
   argument. **Check the printed SHA against `git rev-parse HEAD`.**
2. Merge to `main` locally and push.
3. **Post-merge CodeQL** — `codeql.yml` runs only on `main`.
4. **Deploy: image-only retag** (no new label, property, env key or tunable).
5. 🎯 **Then the ADR-0029 tests, in this order — this is the point of the sprint:**
   - **Test 1 (null check):** every verdict still recorded; `revise` in `verdicts`, absent from
     `vetoed_tickers`.
   - **Test 2 (first scheduled run):** an order with a `revise` reaches the broker; an `overturn`, if
     any, still blocks.
   - **Test 4 (fail-closed on non-answer):** force an unparseable reply; expect `applied_failed_open`
     and a fault, not a `revise`.
   - **Test 5 (the bar):** fills resume on nights the PM approves buys.
   - **Test 3 (relabelling tripwire), over the next 10 real-debate sessions:** `overturn` share must
     stay near **6.3 %**. 🪤 **Above 20 % → revisit ADR-0029**, do not tighten the prompt until the
     numbers look right.
6. **Only after tests 1–5 read clean**, ADR-0029 decisions 2–4 become the next sprint (prompt discloses
   verdict consequences; a block must name an order-specific fact; findings register with dedup).
   🚨 **Do not bring decision 3 forward** — telling the judge that `revise` no longer blocks while also
   changing what `revise` does makes the tripwire unreadable.

---

## Handover — paste this to Codex

```text
Sprint 214 — a `revise` is a finding, an `overturn` is a block.
Branch: sprint-214-revise-is-a-finding. Bump: PATCH. Spec:
docs/sprints/sprint-214-a-revise-is-a-finding-an-overturn-is-a-block.md

MUST RULE FIRST. Before any code: read agents/deliberator/laws/laws.md (LOCKED v1.7) and its
test-plan.md in full, agents/execution/laws/laws.md (LOCKED v1.6), docs/laws/conventions.md and
docs/laws/drift-register.md. Then fill the "Law reading record" at the bottom of the spec. Only
then write code.

LAW-CYCLE ANSWER: YES for the deliberator. DLIB-OUT-02 guarantees what `vetoed_tickers` contains
and this sprint changes it, so a full law cycle is owed: clause amendment, test-plan row,
changelog, rollup RECOUNTED (run the gate, copy what it prints), DRIFT row.
contracts/ does NOT change — `Ruling` is already three-valued. If you are editing contracts/, stop.

WHAT TO BUILD, and nothing else:
1. agents/deliberator/review_batch.py:87 — the veto predicate becomes `== "overturn"`. `revise` and
   `uphold` both leave vetoed_tickers. Everything else _assemble records stays identical.
2. A judge that cannot answer must NOT be recorded as `revise`. Today kernel/deliberation.py:105-115
   and :155 return Verdict("revise", ...) for empty / unparseable / unrecognised / stopped replies.
   Route those to the EXISTING marker agents/deliberator/review_record.py:41 `fail_open_review(reason)`
   so the ticker lands in failed_open_tickers, the run stamps applied_failed_open, and the fault fires.
   This also makes the two failure paths agree — today a raised LLM error fails open and does not
   block, while an unparseable reply blocks.
3. Decide where that policy lives (kernel parses, agent decides is preferred) and record the decision
   in docs/design-log.md with rejected alternatives BEFORE implementing. Grep every caller of
   judge_verdict / deliberate / _parse_verdict first — kernel/deliberation_eval.py reads
   result.verdict.ruling.

DO NOT:
- Do NOT implement ADR-0029 decisions 2, 3 or 4. No prompt change, no order-specific-ground rule,
  no findings register. Decision 3 is sequenced AFTER this sprint on purpose: shipping both makes
  the relabelling tripwire unreadable.
- Do NOT change contracts/.
- Do NOT change execution behaviour. drop_vetoed reads vetoed_tickers, so execution should follow
  with no edit. Confirm by reading and say so. If you believe an execution change is required,
  report before writing it.
- Do NOT add resize-on-revise. Ruled out.
- Do NOT reclassify past DeliberationRun rows.
- Do NOT use # noqa to fit a line budget.

TRAPS (named because a trap you do not write down gets hit):
- THE SILENT FAIL-OPEN. Changing the veto predicate without fixing the parse default converts a
  fail-CLOSED default into a silent fail-OPEN. Tests A4/A5/A6 exist for this. Write them FIRST.
- kernel/deliberation.py is 198/200 lines. Two added lines break make ci. SPLIT the module; do not
  trim docstrings to fit.
- "Fewer vetoes" is not proof. The postcondition is WHICH verdicts veto. A bug emptying
  vetoed_tickers entirely also reduces vetoes — A2 and A7 separate the two.
- The rollup is RECOUNTED by the gate, never hand-edited.

ORDER OF WORK: laws -> Law reading record -> design decisions in design-log -> failing tests first
(paste the red output) -> implement -> break each guard and watch it go red, then restore -> law
cycle -> make ci redirected to a FILE (never piped; `make ci | tail` reports tail's exit code) ->
fill Test plan results, Closeout evidence and Return notes -> set Status: BUILT.

Expected effect once deployed: the block rate falls from 53% to about 6%. That is intended, not a
bug. Deploy is an image-only retag — no new label, property, env key or tunable.

An incomplete handback is returned, not repaired.
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

| Law file | Read in full? | Clauses that bind this sprint | Anything the law forbids that the spec asks for? |
| --- | --- | --- | --- |
| `agents/deliberator/laws/laws.md` | | | |
| `agents/deliberator/laws/test-plan.md` | | | |
| `agents/execution/laws/laws.md` | | | |
| `docs/laws/conventions.md` | | | |
| `docs/laws/drift-register.md` | | | |

**Does `DLIB-NEV-06` already cover the non-answer rule, or is a new clause owed?**
*Answer:*

**Did execution need a code change?**
*Answer:*

---

## Test plan results — fill at handback

| # | Test | Red first? | Result |
| --- | --- | --- | --- |
| A1 | | | |
| A2 | | | |
| A3 | | | |
| A4 | | | |
| A5 | | | |
| A6 | | | |
| A7 | | | |
| A8 | | | |

---

## Closeout — evidence

<!-- Real pasted output. Never leave this placeholder unfilled. -->

**Red-first output:**

**`make ci` (redirected to a file, exit code):**

**`contracts/` diff:**

**Module sizes after the change:**

**Law rollup, as the gate printed it:**

**DRIFT row filed:**

---

## Return notes

<!-- What surprised you, what the spec got wrong, what the next sprint should know. -->
