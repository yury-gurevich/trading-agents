<!-- Agent: planning | Role: sprint handover -->
# Sprint 189 — an empty answer says why it is empty

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-189-an-empty-answer-says-why-it-is-empty`
**Status:** BUILT
**Version:** `0.94.00` (MINOR bump on branch)
**Effort:** M
**Decisions:** work-queue item 35 (the row this closes, and corrects) · [DL-99](../design-log.md) (why the second provider exists) · a new DL for the four design decisions below

> **Why this bump kind.** MINOR. The deliberator gains a distinction it does not have: *the model
> declined / was cut off* versus *the model answered with nothing*. Today those are the same value,
> and the LLM ledger cannot tell them apart after the fact either.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/deliberator/laws/laws.md` | The deliberator's **locked constitution** (v1 LOCKED) | **Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/deliberator/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it alongside the law. If a clause you rely on is ⬜, say so |
| `docs/laws/conventions.md`, `ledger.md`, `drift-register.md` | Umbrella laws + rollups | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`FAIL`** (per-order fail-open), **`OBS`** (reconstructable transcript),
**`OUT`** (recorded debate shape), **`PERF`** (peer wait bounded by request timeout), **`PARAM`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read `test-plan.md` alongside `laws.md`. If a clause you rely on is ⬜, say so.
3. Read `docs/laws/conventions.md` and `docs/laws/drift-register.md`.
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answer before step 5

> Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?

**Yes — a law cycle is owed.** No `contracts/` file changes, but the deliberator gains guarantees it
does not currently make:

- a completion that was **truncated or declined** is an error, never an empty answer;
- an empty debate turn **never silently enters a transcript**;
- every `LLMCall` records **why** the model stopped.

So: new clauses in `agents/deliberator/laws/laws.md` (**v1.1**, Changelog line), a `test-plan.md` row
per clause, the clause ID cited in each test docstring, the rollup updated in **both**
`docs/laws/ledger.md` **and** `docs/laws/INDEX.md`, and a `drift-register.md` row for anything the
change slips under.

🪤 **The rollup is derived, not declared.** `make ci` recomputes it — let the gate tell you the number.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/deliberator/llm_anthropic.py` | `agents/deliberator/laws/laws.md` + `test-plan.md` | `FAIL` — what counts as a failed review |
| `agents/deliberator/llm_openai.py` | same | `FAIL`, and DL-105's `effort` pass-through note in the module docstring |
| `kernel/llm.py` (the `LLMClient` port) | `docs/laws/conventions.md`; kernel has no agent law — **if the umbrella laws are silent on the port's contract, that silence is a finding: file a drift row** | the port's docstring is the only contract two adapters share |
| `kernel/deliberation.py` | `agents/deliberator/laws/laws.md` | `OUT`/`OBS` — recorded debate shape and reconstructable transcript |
| `kernel/llm_ledger.py` | same | `OBS` — the ledger is the after-the-fact evidence |

⚠️ **The invariant this sprint must not break: per-order fail-open stays per-order.** Making a
truncated completion raise must not turn one bad order into an aborted batch — `review.failed_open`
already isolates per order, and S172's concurrency work depends on that isolation surviving. If your
change would abort a batch, **stop and report**.

---

## Goal

At merge, a deliberation completion that was cut off, declined, or otherwise stopped without an
answer **raises with the reason named**, and the `LLMCall` ledger records the stop reason for every
call — so *"the model was truncated"*, *"the model refused"*, and *"the model answered with nothing"*
stop being the same recorded value.

## Why (context)

Work-queue item 35 filed this as *"the **OpenAI fallback** returns an empty verdict … not currently
biting, Anthropic is primary."* **Both halves of that are wrong**, measured below: the identical
defect is in the Anthropic adapter, which is the *primary*, and empty completions are already in the
graph — 135 of them.

The deeper problem is that we cannot tell *why* any of them were empty. For all 135, the recorded
evidence is byte-identical: a SHA-256 of the empty string. A billing rejection, a truncation, a
refusal and a genuinely empty answer all leave exactly the same trace. That is the repo's recurring
shape — `Fill.status`, `FilterVerdict`, `GateOutcome.passed`, and S188's `credential_failure_statuses`
— *a value that looks like data but means nothing happened*.

### Measured, 2026-08-30 — read these before designing

Queried against the live Neon spine (`nodes where label = 'LLMCall'`, n = **1,037**).

| Claim | Value | How it was measured |
| --- | --- | --- |
| Empty completions already in the graph | **135 / 1,037 = 13.0 %** | *[measured 2026-08-30]* two independent signals agreeing exactly: `response_hash == sha256("")` and `tokens_out == 0` |
| …but **dominated by known outage days**, not a steady rate | **98 of the 135 fall on 2026-08-08 alone** (98/340 = 29 %), the DL-99 Anthropic usage-limit day; 19 more on 2026-08-19, the OpenAI no-credit day | *[measured 2026-08-30]* per-day breakdown |
| Residual on days with **no** known provider outage | **3 / 100** across 2026-08-17 (1/35) and 2026-08-18 (2/65) ≈ **3 %** | *[measured 2026-08-30]* same query. 🚨 **This is the number the sprint exists for — small, real, and unexplained** |
| It is **not** an OpenAI-only defect | of the 135, **112 are `claude-opus-5`**, 22 are `gpt-5.5`, 1 is `claude-sonnet-4-6` | *[measured 2026-08-30]* — item 35's "fallback only" framing is **wrong** |
| Arguing roles fail more than the judge | proponent **16.0 %** (71/444), opponent **13.5 %** (52/385), manager/judge **6.0 %** (11/183) | *[measured 2026-08-30]* |
| The Anthropic adapter has the same defect as the OpenAI one | `_text()` collects `block.type == "text"` and never reads `stop_reason` | *[measured 2026-08-30]* `agents/deliberator/llm_anthropic.py:54-60` |
| The OpenAI adapter never reads `finish_reason` | `_text()` docstring literally says *"tolerating empties"* | *[measured 2026-08-30]* `agents/deliberator/llm_openai.py:70-78` |
| `tokens_out` **cannot** detect truncation | it is `_rough_tokens` = `len(value.split())`, a **word count of the visible answer**; a truncated call returns no visible text, so it scores 0 regardless of tokens actually spent | *[measured 2026-08-30]* `kernel/llm_ledger.py` |
| …and nothing looks near the cap by that measure | `tokens_out` min/median/max = **0 / 168 / 468**; **0 rows** at or above 4096 | *[measured 2026-08-30]* — proves the metric is blind, **not** that truncation is absent |
| `max_tokens` cannot be tuned around it | `tunable(4096, ge=64, le=4096)` — the default **is** the ceiling | *[measured 2026-08-30]* `agents/deliberator/settings.py:81-87` |
| …against a model output cap of **128K** | Opus 5 / Sonnet 5 / Opus 4.6-4.8 support up to 128K `max_tokens` (streaming required at that size) | *[measured 2026-08-30]* `claude-api` skill |
| `effort` is `tunable("max")` in code, `high` live | max effort spends the most thinking against the smallest budget | *[measured 2026-08-30]* settings.py:77; live env read via `az containerapp show` |
| An empty **judge** answer becomes a verdict, not an error | `_parse_verdict("")` → `Verdict("revise", "judge response unparseable — defaulting to revise")` | *[measured 2026-08-30]* `kernel/deliberation.py` |
| An empty **debate turn** enters the transcript silently | `debate_turn` returns `Turn(role, n, "")` with no guard | *[measured 2026-08-30]* `kernel/deliberation.py` |

### 🚨 The severity ordering, which is not what item 35 assumed

1. **Debate turns are the worst case and have no fail-safe.** A truncated turn becomes an empty
   `Turn`, the judge then rules on a transcript with holes in it, and the verdict that comes out
   **looks completely legitimate**. No fault, no record, no reason field. The arguing roles are also
   the ones failing most (16.0 % / 13.5 %).
2. **The judge's case is fail-*safe* but mislabelled.** An empty judge answer becomes `revise` — it
   blocks rather than approves, which is the right direction — but the recorded rationale blames the
   *parser*, when the judge never actually answered. 🪤 **A forced `revise` is counted as a veto.**
   11 judge calls returned empty. If any fell inside DL-119's four binding runs, they inflated the
   **73 %** veto rate — the number ADR-0023's falsifiable test and item 3's K=4 measurement both hang
   on. *[NOT MEASURED — the correlation to those four run IDs has not been done. Do not assert
   contamination; scope item 1 settles it.]*

---

## Scope — and what is deliberately NOT here

1. **Measure first, and settle the contamination question.** Correlate the 11 empty judge calls
   against DL-119's four binding runs (`verify-2026-08-19-clean`, `-clean-2`, `verify-2026-08-20-opus`,
   `verify-2026-08-20-s182-a`) by `correlation_id`. Report the number plainly, **including if it is
   zero** — that is a real result, and DL-119's 73 % either survives or gets an asterisk.
2. **The failing test first: a truncated completion raises.** Anthropic `stop_reason == "max_tokens"`
   and OpenAI `finish_reason == "length"` each raise a named error carrying the stop reason. **Do the
   Anthropic adapter first** — it is the primary and it carries 112 of the 135.
3. **A refusal raises too, and says so.** Anthropic may return **HTTP 200** with
   `stop_reason == "refusal"` and a `stop_details.category` — a third silent-empty path item 35 does
   not mention. Raise with the category named. 🪤 `stop_details` is populated **only** for refusals and
   is `null` for every other stop reason — guard before reading it.
4. **An empty turn never enters a transcript.** `debate_turn` must refuse to emit an empty `Turn`.
   Route it through the existing per-order fail-open so one bad turn fails *that order*, not the batch.
5. **The judge's rationale stops lying.** An empty judge answer must not be recorded as
   *"judge response unparseable"*. Keep the fail-safe `revise`; name the real cause.
6. **The ledger records the stop reason.** `LLMCall` gains the stop reason so this is answerable after
   the fact instead of requiring a code read. Graph vocabulary entry in the same commit.
7. **Raise the `max_tokens` ceiling** so the value is tunable rather than pinned at its own bound.
   The new `le` is a design decision (below), not a number to pick casually.
8. **The law cycle** named above, deliberator laws → **v1.1**.

### Out of scope (do NOT build this sprint)

- **Fixing `_rough_tokens` to record real API usage.** It is the same module and it is tempting.
  🚨 **It is a bigger change than it looks:** `tokens_in`/`tokens_out` are word counts, the
  `/audit-costs` skill prices LLM spend from them, and real usage would include **thinking tokens,
  which are billed and currently invisible** — so fixing it *changes every historical cost number*.
  That deserves its own sprint and its own decision. **File it, do not fold it in.**
- **Streaming.** The 128K output cap needs streaming; this sprint does not need 128K.
- **Retrying a truncated call.** Raising is this sprint. Whether to retry with a larger budget is a
  policy question the fail-open path already has an answer for.
- **Touching `effort` or `max_rounds`.** S172's traps still apply: `effort` is part of the fixed
  baseline, and `max_rounds` 2 → 1 changes the artefact under test.
- **No ADR reversal.** An ADR is reversed by a new ADR, never by a sprint.

### The road not taken (LAW-06)

- **Treat an empty string as the error signal — no new exception type.** Rejected: it cannot carry
  *why*, which is the entire point; and `""` is a legitimate (if useless) model answer.
- **Fix only the OpenAI adapter, as item 35 asked.** Rejected on measurement: 112 of 135 empties are
  Anthropic, the primary. Fixing the fallback alone would leave the live path broken and *look* done.
- **Raise `max_tokens` and call it fixed.** Rejected: a bigger budget makes truncation rarer without
  making it visible, and the sprint is about visibility. It is a mitigation, not the fix.
- **Make `debate_turn` substitute a placeholder for an empty turn.** Rejected: it puts fabricated
  content into an evidence artefact the laws require to be reconstructable (`OBS`).

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Where the check lives: adapter, port, or caller.** Each adapter knows its own vendor's stop
   field; `kernel/deliberation.py` knows what an empty turn means. Putting it only in the adapters
   means a *third* adapter must remember; putting it only in the caller means the reason is already
   lost. Decide, and say what a future adapter must implement.
2. **What the exception carries.** At minimum the stop reason. 🚨 It must **not** carry prompt or
   completion text — the fail-open reason is recorded in the graph, and S188's `MST-SEC-04` is the
   precedent for keeping recorded evidence free of payload.
3. **The new `max_tokens` ceiling.** The model supports 128K; the current `le` is 4096 and is also the
   default. Pick a `le` you can justify against the debate's real answer length (measured median is
   **168 words**), not against the model's maximum. A ceiling far above any observed answer is how a
   runaway costs money.
4. **What the ledger records, and its vocabulary entry.** A stop-reason prop on `LLMCall` is a
   **graph vocabulary change** → the deploy is a full `up`, and the vocabulary entry must land in the
   same commit or the fail-closed write guard stalls the cascade mid-run (S148, DL-85).

🪤 **Take the next free DL number, then re-check it at merge** — the log has historic duplicates and a
branch cut before another DL lands will collide even when the number was free at branch time (S183).

---

## Blast radius — measured 2026-08-30

| What | Detail |
| --- | --- |
| Files changed | `agents/deliberator/llm_anthropic.py` **60**; `agents/deliberator/llm_openai.py` **78**; `kernel/llm.py`; `kernel/deliberation.py`; `kernel/llm_ledger.py`; `agents/deliberator/settings.py`; `orchestration/packs/trading_graph_vocabulary.json`; deliberator laws + test-plan; `docs/laws/{ledger,INDEX,drift-register}.md`; tests |
| Agents affected | **deliberator only** — but `kernel/` is shared, so check no other caller of `LLMClient.complete` breaks (`agents/master/` uses an LLM for remediation, and `kernel/deliberation_eval.py` uses a judge) |
| Contract change? | No `contracts/` file — **but the `LLMClient` port's contract changes, and new guarantees are added, so the law cycle is mandatory** |
| Graph vocabulary change? | **Yes** (decision 4) → deploy is a **full `up`** |
| New env keys / tunables | changed bound on `max_tokens` → PARAM row must match (S187's `make ci` check enforces both directions) |
| Deploy implication | **Full `up`.** 🚨 Not before `sched-2026-08-31`; sequence behind S172 and S188 |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Do scope item 1 first** — the contamination correlation. It is a query, it costs nothing, and it
   tells you whether this sprint is also an evidence correction.
3. **Record the four design decisions** in `docs/design-log.md`, with rejected alternatives.
4. **Plant A1 and watch it fail.** Paste the red output.
5. **Implement** — Anthropic adapter first, then OpenAI, then the kernel guards, then the ledger.
6. **Law cycle** — clauses, test-plan rows, docstring citations, both rollups, drift row.
7. **Prove the guards can fail (DL-70)** — break each, watch it go red, restore. **State it per guard.**
8. **`make ci` green** — all 12 steps, **redirected to a file, never piped**.
9. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 Anthropic `stop_reason == "max_tokens"` with no text raises, naming the stop reason | fake response object, thinking block only | a named error, not `""`; the reason is in the message |
| A2 | OpenAI `finish_reason == "length"` with empty content raises the same way | fake completion | same shape as A1 — one behaviour, two vendors |
| A3 | 🪤 Anthropic `stop_reason == "refusal"` raises with `stop_details.category` named | fake refusal, HTTP 200 | the refusal path is distinct from truncation, and reading `stop_details` is guarded |
| A4 | 🪤 A genuinely empty answer with `stop_reason == "end_turn"` is **not** an error | fake normal response, empty text | the fix does not turn a legitimate (useless) answer into a crash |
| A5 | An empty debate turn never enters a transcript | truncated defender turn | no `Turn` with empty text is emitted; the order fails open with a reason |
| A6 | 🪤 One truncated turn fails **that order only** | batch of orders, one truncated | the other orders complete; exactly one `failed_open` ticker — **S172's isolation survives** |
| A7 | The judge's empty answer keeps `revise` but stops blaming the parser | empty judge completion | ruling is still `revise`; the rationale names truncation/refusal, not "unparseable" |
| A8 | Every `LLMCall` records the stop reason, including on the success path | normal + truncated call | the prop is present and correct in both, and declared in the graph vocabulary |
| A9 | 🪤 No prompt or completion text reaches the exception, the fault, or the node props | sentinel string in the prompt | the sentinel appears **nowhere** in recorded evidence (S188 `MST-SEC-04` precedent) |
| A10 | The `max_tokens` PARAM row matches the new bound both ways | — | S187's sync check passes; the law table and the `tunable()` agree |

---

## Success factors

- [x] Scope item 1 answered with a number, **including if it is zero** — how many of the 11 empty judge calls fall inside DL-119's four binding runs.
- [x] A truncated completion raises with the stop reason named, on **both** adapters (A1, A2).
- [x] A refusal is distinguishable from a truncation (A3), and a legitimate empty answer is not an error (A4).
- [x] No empty `Turn` can enter a transcript (A5), and one bad turn fails one order (A6).
- [x] The judge's fail-safe `revise` is preserved, with an honest rationale (A7).
- [x] `LLMCall` records the stop reason, with its graph-vocabulary entry in the same commit (A8).
- [x] No prompt or completion text in any exception, fault, or node prop (A9).
- [x] `max_tokens` ceiling raised with a justified number, PARAM row in sync (A10).
- [x] Design decisions recorded with rejected alternatives.
- [x] Law cycle done: deliberator laws **v1.1**, test-plan row per clause, clause IDs in docstrings, rollup in **both** `ledger.md` and `INDEX.md`, drift row filed.
- [x] Every new guard planted, watched to fail, restored — **stated per guard**.
- [x] Every touched module < 200 lines. `make ci` exit 0, 100.00 % coverage, redirected to a file.

---

## Traps

🪤 **`tokens_out` will tell you truncation never happens. It cannot know.** It is a word count of the
*visible* answer, so a truncated call scores 0 — the same as an empty one. **0 rows at or above 4096
is not evidence of no truncation**, it is evidence the metric is blind. Do not cite it as reassurance.

🪤 **The 13 % headline is mostly the outages.** 98 of 135 empties are 2026-08-08 alone. Quoting 13 %
as a steady-state rate would repeat DL-119's own diluted-denominator mistake. **The sprint's number
is the ~3 % on days with no known outage.**

🪤 **Item 35's framing is wrong and it is in the queue in a confident voice.** It says OpenAI-only and
"not currently biting". Measured: 112 of 135 are `claude-opus-5`, the primary. Correct the row at merge.

🪤 **Fail-open must stay per-order.** Making truncation raise is exactly the change that could turn one
bad order into an aborted batch and silently undo S172's isolation. A6 exists for this.

🪤 **`stop_details` is `null` for every stop reason except `refusal`.** Reading it unguarded turns a
truncation into an `AttributeError` — a new silent failure inside the fix for silent failures.

🪤 **Adding a `LLMCall` prop without the vocabulary entry stalls the cascade mid-run** (S148 / DL-85).
Same commit.

🪤 **A worktree has no `.env`.** Every adapter test uses a fake response object; scope item 1's query
needs the real spine, so **run it from the main tree and say so**.

🪤 **`make ci` never through a pipe** — `make ci | tail` reports `tail`'s exit code. Redirect to a file.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `llm_openai.py` **78**, `llm_anthropic.py` **60**, `settings.py` (deliberator), `kernel/deliberation.py`, `kernel/llm_ledger.py` — report each after the change.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 12 steps** green, **100.00 % coverage floor**, redirected to a file.
- Version bump of the kind named at the top (**MINOR**), `uv.lock` staged with it.
- Secrets never through the worktree.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 Run it from the worktree whose `HEAD` is the commit you are proving — it ignores a `SHA=`
   argument. Check the printed SHA against `git rev-parse HEAD`.
2. Merge to `main` locally and push. 🪤 Check you are not on the branch already.
3. **Post-merge CodeQL** — `codeql.yml` runs only on `main`.
4. **Deploy: a full `up`, and NOT before `sched-2026-08-31`.** Queue behind S172's K=4 measurement and
   S188's deploy so the `up`s do not collide.
5. **Live check, then tear down** (record in `docs/laws/functionality-checks.md`): set `max_tokens` to
   its minimum (`ge=64`) for one manual debate, watch a truncation raise and land as a named
   `failed_open_reason` rather than a hollow verdict, then restore the value. This needs **no** bad
   credential and **no** vendor outage — the tunable's own floor reproduces it.

---

## Handover — paste this to Codex

```text
Branch: sprint-189-an-empty-answer-says-why-it-is-empty (create it BEFORE any code, never work on
main). Read docs/sprints/sprint-189-an-empty-answer-says-why-it-is-empty.md whole before starting;
this block is a summary, not a replacement.

WHAT IS BROKEN. Neither deliberator LLM adapter inspects why the model stopped.
agents/deliberator/llm_openai.py:70-78 _text() collects message.content and never reads
finish_reason - its docstring says "tolerating empties". agents/deliberator/llm_anthropic.py:54-60
has the IDENTICAL defect and never reads stop_reason. So a truncated call (the token budget spent on
reasoning before any visible text) returns "" and raises nothing, and so does a refusal, which
Anthropic returns as HTTP 200 with stop_reason "refusal" and a stop_details.category.

MEASURED, do not re-derive: 135 of 1037 LLMCall rows in the live graph have an empty completion (two
agreeing signals: response_hash == sha256("") and tokens_out == 0). 112 of those 135 are
claude-opus-5 - the PRIMARY - and only 22 are gpt-5.5. Work-queue item 35 says this is an
OpenAI-fallback-only problem that is "not currently biting"; item 35 is WRONG and gets corrected at
merge. 98 of the 135 are on 2026-08-08 alone (a known provider outage day), so the honest
steady-state figure is the ~3 % on days with no known outage (3 of 100 across 08-17 and 08-18).

WHY IT MATTERS. In kernel/deliberation.py, debate_turn returns Turn(role, n, "") with no guard, so a
truncated argument enters the transcript as an empty turn and the judge then rules on a transcript
with holes in it - producing a verdict that looks completely legitimate. No fault, no record. The
arguing roles fail most (proponent 16.0 %, opponent 13.5 %). The judge case is fail-SAFE by accident
- _parse_verdict("") returns Verdict("revise", "judge response unparseable - defaulting to revise") -
but the rationale blames the parser when the judge never answered, and a forced revise counts as a
veto.

WHAT TO BUILD.
1. FIRST, before any code: correlate the 11 empty judge (manager) calls against DL-119's four binding
   runs by correlation_id and report the number, including if it is zero. That decides whether the
   73 % veto rate needs an asterisk.
2. Anthropic adapter FIRST (it is the primary): stop_reason "max_tokens" with no text raises a named
   error carrying the stop reason; stop_reason "refusal" raises naming stop_details.category. GUARD
   stop_details - it is null for every stop reason except refusal, so reading it unguarded turns a
   truncation into an AttributeError.
3. Same behaviour in the OpenAI adapter for finish_reason == "length".
4. A genuinely empty answer with stop_reason "end_turn" must NOT raise.
5. kernel/deliberation.py: an empty debate turn never enters a transcript; route it through the
   existing per-order fail-open.
6. The judge keeps its fail-safe "revise" but the rationale names the real cause, not "unparseable".
7. kernel/llm_ledger.py: LLMCall records the stop reason. Graph vocabulary entry in the SAME commit.
8. Raise the max_tokens ceiling - it is tunable(4096, ge=64, le=4096), so the default IS the ceiling
   and it cannot be tuned around. Justify the new le against observed answer length (median 168
   words), not against the model's 128K maximum.
9. Full law cycle: deliberator laws v1.1, test-plan row per clause, clause ID in each test docstring,
   rollup in BOTH docs/laws/ledger.md and docs/laws/INDEX.md, drift row.

ORDER. Read laws -> Law reading record -> the correlation query -> record 4 design decisions in
docs/design-log.md WITH rejected alternatives -> plant A1 and watch it fail, paste the red ->
implement.

DO NOT:
- Do NOT fix _rough_tokens to record real API usage. tokens_in/tokens_out are word counts, the
  /audit-costs skill prices LLM spend from them, and real usage includes thinking tokens that are
  billed and currently invisible - so changing it rewrites every historical cost number. Separate
  sprint. File it, do not fold it in.
- Do NOT add streaming, retries, or touch effort / max_rounds.
- Do NOT let a truncated order abort the batch. Per-order fail-open isolation is what S172 depends
  on; test A6 exists for exactly this.
- Do NOT put prompt or completion text into the exception, the fault, or any node prop (S188's
  MST-SEC-04 is the precedent). Test A9 asserts a sentinel appears nowhere.
- Do NOT edit laws.md except as the law cycle requires; it is LOCKED v1.

TRAPS:
- tokens_out will tell you truncation never happens. It CANNOT know - it is a word count of the
  visible answer, so a truncated call scores 0 exactly like an empty one. "0 rows above 4096" is
  evidence the metric is blind, not evidence of no truncation. Never cite it as reassurance.
- Do not quote 13 % as a steady-state rate; 98 of 135 are one outage day. That is the same
  diluted-denominator mistake DL-119 had to correct.
- Adding an LLMCall prop without the trading_graph_vocabulary.json entry hits the fail-closed write
  guard and stalls the cascade mid-run (S148 / DL-85). Same commit.
- A worktree has NO .env. Adapter tests use fake response objects; the correlation query needs the
  real spine, so run it from the main tree and say which tree you ran in.
- make ci through a pipe reports the pipe's exit code. Redirect to a file and read the file.

VERSION: next available MINOR at merge - do not pin a number.
GATE: make ci exit 0 (12 steps, 100.00 % coverage) redirected to a file, then push the branch and get
make gate-ran GATE PROVEN, run from the worktree whose HEAD is that commit, and check the printed SHA
against git rev-parse HEAD. Fill the Closeout block before handing back; a handback with a
placeholder left in it is returned, not repaired.
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

Read before code on 2026-08-30, on branch
`sprint-189-an-empty-answer-says-why-it-is-empty`: `agents/deliberator/laws/laws.md`,
`agents/deliberator/laws/test-plan.md`, `docs/laws/conventions.md`,
`docs/laws/drift-register.md`, and `docs/laws/ledger.md` after entering through
`docs/INDEX.md`, `docs/sprints/INDEX.md`, and `docs/laws/INDEX.md`.

Binding deliberator clauses:
`DLIB-FAIL-01` (green) requires each LLM or peer-call failure to fail open for the
affected order with a recorded rationale; `DLIB-NEV-06` (green) forbids hiding a
failed debate or peer call as a clean veto; `DLIB-OUT-02` (green) binds the
recorded verdict/debate/narrative shape; `DLIB-OUT-03` (gray) governs `LLMCall`
audit evidence; `DLIB-IDM-02` (gray) requires LLM output bounds and hashes to be
stamped; `DLIB-OBS-01` (gray) requires a reconstructable debate transcript;
`DLIB-OBS-02` (gray) binds attributable LLM spend; `DLIB-OBS-03` (green) requires
visible fail-open outcomes; `DLIB-PERF-01` and `DLIB-PERF-02` (both gray) bind
round and peer-wait bounds; the `PARAM` table binds `max_tokens` and must stay in
sync with `DeliberatorSettings`.

Umbrella conventions bind clause ID stability, gray-to-green proof by functional
test docstring citation, locked-law amendment through a visible changelog, and
central drift registration. Kernel has no agent law, and `docs/laws/conventions.md`
does not define the shared `LLMClient` port contract for vendor stop/finish
semantics; S189 therefore owes a `drift-register.md` row for that law silence.

Law-cycle answer: yes. No `contracts/` file change is planned, but S189 adds
deliberator guarantees for truncated/refused completions, empty debate turns, and
`LLMCall` stop-reason evidence, so deliberator laws move to v1.1 with test-plan
rows, clause IDs in the proving test docstrings, and rollups updated in both
`docs/laws/ledger.md` and `docs/laws/INDEX.md`.

---

## Test plan results — fill at handback

| # | Result | Evidence |
| --- | --- | --- |
| A1 | Passed. Anthropic `stop_reason == "max_tokens"` raises a named stop error instead of returning `""`. | Planted red: `uv run pytest tests/test_deliberator_anthropic.py::test_anthropic_max_tokens_without_text_raises_stop_reason --no-cov` failed with `Failed: DID NOT RAISE RuntimeError`; restored/final focused run: 44 passed. |
| A2 | Passed. OpenAI `finish_reason == "length"` raises the same shared stop error. | `agents/deliberator/tests/test_llm_openai_adapter.py::test_openai_length_without_text_raises_stop_reason`; final focused run: 44 passed. |
| A3 | Passed. Anthropic refusal raises with guarded `stop_details.category`; missing category stays safe. | `tests/test_deliberator_anthropic.py::test_anthropic_refusal_raises_with_guarded_category` and `...::test_anthropic_refusal_without_category_still_raises`; final focused run: 44 passed. |
| A4 | Passed. A normal `end_turn` empty answer remains a legitimate empty completion at the adapter port. | `tests/test_deliberator_anthropic.py::test_anthropic_end_turn_empty_text_is_not_a_stop_error`; final focused run: 44 passed. |
| A5 | Passed. `debate_turn` refuses to emit an empty `Turn`. | `tests/test_deliberation.py::test_empty_debate_turn_raises_instead_of_entering_transcript`; DL-70 red proved removing the guard fails. |
| A6 | Passed. One stopped debate call fails open only that order, not the batch. | `agents/deliberator/tests/test_stop_reason_fail_open.py::test_one_stopped_turn_fails_only_that_order_and_records_reason` asserts AAPL completes, MSFT fails open, `real_debate_count=1`, `failed_open_count=1`, `failed_open_tickers=("MSFT",)`. |
| A7 | Passed. Judge fail-safe `revise` is preserved and the reason names stop/empty-answer cause instead of parser blame. | `tests/test_deliberation.py::test_stopped_judge_response_defaults_to_revise_with_reason` and `...::test_parse_verdict_empty_defaults_to_revise_without_parser_blame`; final focused run: 44 passed. |
| A8 | Passed. `LLMCall.stop_reason` is written on success and stopped paths, and declared in graph vocabulary. | `agents/deliberator/tests/test_stop_reason_fail_open.py::test_llmcall_records_stop_reason_without_payload`, `tests/test_graph_vocabulary_deliberation.py`, `tests/test_graph_vocabulary_properties.py`, `agents/operator/tests/test_operator_store.py`; DL-70 red proved undeclared vocabulary fails. |
| A9 | Passed. No prompt/completion sentinel reaches the exception, fault, `DeliberationRun`, or `LLMCall` node props. | `test_one_stopped_turn_fails_only_that_order_and_records_reason` and `test_llmcall_records_stop_reason_without_payload` use `S189_PROMPT_SENTINEL` and assert it is absent from recorded evidence. |
| A10 | Passed. `max_tokens` ceiling is raised and law/PARAM sync remains clean. | `agents/deliberator/tests/test_llm_provider.py::test_max_tokens_ceiling_is_tunable_above_the_default`; `uv run python scripts/check_param_law_sync.py` exit 0 with known baseline warnings only. |

---

## Closeout — evidence

Scope item 1 — live-spine read-only correlation, rerun 2026-08-31 from the S189 worktree with `.env`
loaded and no DSN printed. A separate `main` worktree was not present (`git worktree list` showed only
this S189 worktree and the S172 worktree). Result: **1 of the 11 empty judge calls falls inside
DL-119's four binding runs**.

```text
binding_run_id,pm_run_key,judge_calls,empty_judge_calls,empty_llm_keys,total_empty_judge_calls
verify-2026-08-19-clean,pm-run-61025f7ffe254ae08b16f2adbaa456a7,6,1,llmcall:deliberator-manager:pm-run-61025f7ffe254ae08b16f2adbaa456a7:AMZN:judge,11
verify-2026-08-19-clean-2,pm-run-9119508ef66d40a894637a1b80ee6015,9,0,,11
verify-2026-08-20-opus,pm-run-506722dd718d43d29a43bece973f6112,4,0,,11
verify-2026-08-20-s182-a,pm-run-08cdb3584cb5443d8c2abd5a8260d21b,4,0,,11
binding_run_empty_judge_calls=1
```

Design/law cycle: [DL-137](../design-log.md) records the four S189 decisions and rejected
alternatives. Deliberator laws move to **v1.1** with new `DLIB-OUT-05`, `DLIB-NEV-07`, and
`DLIB-FAIL-04`; `test-plan.md` has green rows and docstring citations; `docs/laws/ledger.md` and
`docs/laws/INDEX.md` now roll up deliberator as **9 / 51**. `DRIFT-054` records the law silence around
the shared `LLMClient` vendor-stop contract.

A1 planted red before the fix:

```text
uv run pytest tests/test_deliberator_anthropic.py::test_anthropic_max_tokens_without_text_raises_stop_reason --no-cov
tests\test_deliberator_anthropic.py F
E   Failed: DID NOT RAISE RuntimeError
============================== 1 failed in 1.14s ==============================
```

DL-70 guard break/restore proof:

```text
Anthropic max_tokens guard removed:
FAILED tests/test_deliberator_anthropic.py::test_anthropic_max_tokens_without_text_raises_stop_reason
E   Failed: DID NOT RAISE RuntimeError

kernel empty-turn guard removed:
FAILED tests/test_deliberation.py::test_empty_debate_turn_raises_instead_of_entering_transcript
E   Failed: DID NOT RAISE LLMCompletionStoppedError

stopped-call ledger stop_reason assignment removed:
FAILED agents/deliberator/tests/test_stop_reason_fail_open.py::test_llmcall_records_stop_reason_without_payload
E   AssertionError: assert 'unknown' == 'max_tokens'

LLMCall.stop_reason removed from graph vocabulary:
FAILED tests/test_graph_vocabulary_deliberation.py::test_llmcall_props_are_declared_and_unknown_prop_fails
E   kernel.graph_vocabulary.VocabularyError: undeclared properties for label 'LLMCall': ['stop_reason']
```

Restored focused green:

```text
uv run pytest tests/test_deliberator_anthropic.py agents/deliberator/tests/test_llm_openai_adapter.py tests/test_deliberation.py agents/deliberator/tests/test_stop_reason_fail_open.py agents/deliberator/tests/test_llm_provider.py tests/test_graph_vocabulary_deliberation.py tests/test_graph_vocabulary_properties.py agents/operator/tests/test_operator_store.py --no-cov
============================= 44 passed in 9.03s ==============================

uv run python scripts/check_law_coverage.py
[WARN] law coverage: 101 clause(s) have no test-plan row (assertion E warn-only)

uv run python scripts/check_param_law_sync.py
[WARN] agents/deliberator/settings.py:48: deliberator.llm_provider settings field has no PARAM row
```

The `max_tokens` default stays `4096`; the ceiling is **8192**. This doubles emergency headroom and
keeps the live proof reproducible with the existing `ge=64` floor, while staying bounded against the
observed visible-answer median of 168 words and max of 468 words. The 128K vendor maximum remains
out of scope because it implies streaming and a different cost/risk envelope.

Final touched Python line counts:

```text
80 kernel/llm.py
115 kernel/llm_ledger.py
198 kernel/deliberation.py
172 agents/deliberator/agent.py
86 agents/deliberator/llm_anthropic.py
98 agents/deliberator/llm_openai.py
142 agents/deliberator/settings.py
186 agents/deliberator/tests/test_stop_reason_fail_open.py
198 tests/test_deliberation.py
119 tests/test_deliberator_anthropic.py
117 agents/deliberator/tests/test_llm_openai_adapter.py
151 agents/deliberator/tests/test_llm_provider.py
97 tests/test_graph_vocabulary_deliberation.py
151 tests/test_graph_vocabulary_properties.py
41 agents/operator/tests/test_operator_store.py
```

Version bump evidence: `pyproject.toml` is `0.94.00`; `uv lock` updated the normalized lock package
entry `trading-agents v0.93.0 -> v0.94.0`. The documented `trading-bump-version` helper is not
installed in this checkout (`Failed to spawn: trading-bump-version`), and no
`src/trading_v2/core/version.py` path exists, so the bump was applied directly and lock refreshed.

Local `make ci` was redirected to `C:\Users\yury_\AppData\Local\Temp\s189-make-ci.log`, not piped:

```text
exit=0
TOTAL                                                     15480      0   3322      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
================= 2420 passed, 4 skipped in 198.21s (0:03:18) =================
uv run pip-audit
No known vulnerabilities found
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 1 new file(s)
```

Remote branch gate is not pasted into this committed closeout before the branch tip exists. After
this closeout commit is pushed, run `make gate-ran` from this worktree and check its printed SHA
against `git rev-parse HEAD`; do not amend only to paste that output, because that would create a new
unproved SHA.

---

## Return notes

- DL-119's four binding runs are not clean of the empty-judge path: one AMZN judge call under
  `verify-2026-08-19-clean` was empty and counted as a forced `revise`. The 73 % veto-rate evidence
  therefore needs an asterisk, not a full retraction.
- The spec's worktree trap was stale in this checkout: `.env` was present in the S189 worktree, and
  there was no separate `main` worktree. The query was still read-only and printed no DSN.
- The repo documents a `trading-bump-version` helper, but this checkout has no such console script and
  no `make bump-version` target. S189 used the required MINOR bump manually (`0.93.00` -> `0.94.00`)
  and refreshed `uv.lock`.
- Deployment/live proof are deliberately not done here. Because `LLMCall.stop_reason` changes the
  graph vocabulary, deploy needs a full `up` in the S172/S188/S189 sequence, then the sprint's live
  minimum-`max_tokens` debate check and teardown.
