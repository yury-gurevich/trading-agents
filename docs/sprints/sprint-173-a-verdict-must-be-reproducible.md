<!-- Agent: deliberator | Role: sprint handover — make the veto's agreement with itself a measured number before anything is built on its verdicts -->
# Sprint 173 — a verdict that cannot be reproduced is not evidence

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-173-a-verdict-must-be-reproducible`
**Status:** MERGED — Part A complete and proven; Part B built, unfunded, unrun
**Version:** 0.97.00
**Effort:** L
**Produced:** [DL-158](../design-log.md) — five dependent rounds and the price · [DL-159](../design-log.md) — the exclusion predicate, the floor, and the re-derived baseline · [DRIFT-056](../laws/drift-register.md)
**Decisions:** [DL-104](../design-log.md) (e) — the 56 % it left open · [DL-105](../design-log.md) — the Batch API substrate and the lever order · [DL-150](../design-log.md) — the re-measured cost, and the question this sprint now answers

> **Why this bump kind.** The deliberator gains a dimension it did not have: its verdicts become
> *measurable* rather than merely recorded, and a new gate reads that measurement. New capability —
> **feat → MINOR**.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/deliberator/laws/laws.md` | The deliberator's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/deliberator/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`IDM`**, **`OBS`**, **`IDN`**, **`NEV`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Answer as specced: No — and the reason matters.** The replay harness is **read-only derivation**
and the gate is a **script reporting a number**. Neither adds a promise the deliberator makes about
its own behaviour, and no `contracts/` type changes.

🚨 **It flips to Yes the moment you persist the verdict.** If you write the reproducibility figure to
the graph as a node or a property on `DeliberationRun`, the deliberator is then *promising* to record
it, and this sprint owes the full cycle: a new `DLIB-OBS-05` clause, a `test-plan.md` row, the clause
ID cited in the test docstring, rollups in **both** `docs/laws/ledger.md` **and** `docs/laws/INDEX.md`,
and a `drift-register.md` row. **Decide this deliberately at step 2 and say which branch you took.**
🪤 S194 already took `DLIB-OBS-04`; if you need a clause, yours is **`DLIB-OBS-05`**.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| the replay harness (new) | `agents/deliberator/laws/laws.md` + `test-plan.md` | **DLIB-OBS-01** — *"the debate narrative and transcript are reconstructable from `DeliberationRun` alone"*. The harness is the **first thing that actually tests this claim.** If replay cannot rebuild the context from stored state, DLIB-OBS-01 is contradicted and that is a finding, not a bug to hide |
| the reproducibility metric | same | **DLIB-IDM-02** — *"LLM outputs are non-deterministic but bounded by role, model, max rounds, prompt hashes, response hashes, and timestamps"*. The law **asserts a bound and nothing measures it.** This sprint is that measurement |
| batch cost reporting | same; `docs/laws/conventions.md` | **DLIB-OBS-02** — spend is attributable per calling agent via `LLMCall.calling_agent` |
| `scripts/deliberation_quality.py` (new) | `docs/laws/conventions.md` | Gate scripts report; they do not mutate |

⚠️ **The invariant this sprint must not break: the harness writes nothing.** Not a `merge_node`, not
an `add_edge`, not a `DeliberationRun`. A replay that writes has corrupted the corpus it is measuring,
and the corpus is 61 rows that cannot be regenerated. If your design needs a write, stop and report.

---

## Goal

At merge, **"does the veto agree with itself?" is a number a script prints, with a confidence interval
and a stated fail-open exclusion count** — not a figure someone derived by hand once. And because that
number exists, the second question becomes answerable for the first time: **does verdict quality
actually change when `effort` or `max_rounds` change**, or do those levers move only wall clock and
cost.

## Why (context)

**The veto does not agree with itself, and nothing measures that but hand-reading.** Two
`DeliberationRun`s on the **same model, same prompt, same eighteen tickers, 3.5 hours apart** agreed
on **9 of 16** comparable verdicts — **56 %**, on a binary verdict, barely distinguishable from
chance. Until reproducibility is a number the gate reads, *"is the veto right"* is answered by hand,
which is how DL-104 was produced and does not scale to a nightly decision.

**And a live decision is now waiting on it.** `effort` and `max_rounds` have each been decided three
times — DL-105's sweep, the 2026-08-13 timeout incident, and [DL-140](../design-log.md)'s rejected
routes — and 🚨 **every one of those decisions turned on wall clock or fail-opens. Not one measured
whether the verdicts changed.** If quality holds at a lower `effort`, the pipeline gets cheaper and
faster for nothing ([DL-150](../design-log.md)).

**Why the Batch API is the right substrate** ([DL-105](../design-log.md)). Measuring reproducibility
means replaying the same debates many times: thousands of independent requests with **no latency
budget at all**. That is the Message Batches API's exact shape — up to 100 k requests per batch,
results keyed by `custom_id`, most complete inside an hour, **50 % off**. The live path's constraint
is wall clock (S172); this path's is neither, so the two do not compete.

### Measured, 2026-09-03 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Self-agreement, same model/prompt/tickers 3.5 h apart | **9 of 16 = 56 %** | *[measured 2026-08-10/11, DL-104]* two `DeliberationRun`s hand-compared |
| Cross-vendor agreement, `claude-opus-5` vs `gpt-5.5` | **12 of 17 = 71 %** | *[measured 2026-08-10/11, DL-104]* shared tickers only |
| `revise` share of real debates | **45 of 58 = 78 %** | *[measured 2026-08-10/11, DL-104]* four runs carrying real verdicts |
| `DeliberationRun` rows on the spine | **61** | *[measured 2026-09-03]* `g.list_nodes("DeliberationRun")` |
| …with `real_debate_count > 0` | **23** | *[measured 2026-09-03]* same listing |
| …**and** `failed_open_count == 0` | **15** | *[measured 2026-09-03]* same listing |
| **The corpus that matters — `PMRun`s with full lineage, renderable today** | **46 runs / 261 approved orders** | *[measured 2026-09-03]* rendered every `PMRun` through `replayed_user_prompt`; 4 early-return, 11 with no approved orders |
| Turns that replay to their *stored* hash (needs the recording code version) | **49 of 272**; **4 of 4** on current-code runs | *[measured 2026-09-03]* step 0, live |
| Ticker verdicts across runs with real debates | **210** | *[measured 2026-09-03]* sum of `verdicts` map lengths |
| `LLMCall` rows available for hash comparison | **1,132** | *[measured 2026-09-03]* `g.list_nodes("LLMCall")` |
| Calls per order | **5** (`defender:r1`, `challenger:r1`, `defender:r2`, `challenger:r2`, `judge`) | *[measured 2026-09-03]* `correlation_id` suffixes, `sched-2026-09-02` |
| Tokens per order | **≈ 5,800 in / 1,280 out** | *[measured 2026-09-03]* USB on `sched-2026-09-02` |
| Largest `tokens_out` across the last 95 calls | **394**, against a `max_tokens` cap of **4096**; **zero** non-`end_turn` stops | *[measured 2026-09-03, DL-150]* the truncation theory for the 56 % is **not visible in the data** |
| `effort` on the deployed fleet | **`high`** — while `settings.py` defaults to `max` | *[measured 2026-09-03]* `az containerapp show -n deliberator-manager` |
| Context byte-identity is checkable | **yes** — `prompt_hash` is stored per call | *[measured 2026-09-03]* `_digest(capture.prompt)`, `kernel/llm_ledger.py:65` |
| `agents/deliberator/context_pm.py` size | **152 lines** — already past the 150 warn line | *[measured 2026-09-03]* `wc -l` |

---

## Scope — and what is deliberately NOT here

1. **Step 0, and it gates everything after it.** Rebuild the deliberation context for a stored
   `PMRun`, digest it the same way `kernel/llm_ledger.py:65` does, and **compare against the
   `prompt_hash` the live run recorded**. Assert on equality of the two hashes, both quoted.
2. **A read-only replay harness** — rebuild context for a stored `PMRun` and its order set,
   deterministically, without touching the live spine. Follow the pattern `accept.py`,
   `trace_run.py` and `observatory.py` already use: **zero** `merge_node` / `add_edge` calls.
3. **Batch submission** with `custom_id` = `{pm_run}:{ticker}:{repeat}:{arm}:{role}`.
4. **The metrics**, each with fail-opens excluded and the exclusion count reported beside it:
   self-agreement, cross-vendor agreement, and agreement with DL-104's hand-checked ground truth
   where it exists.
5. **The gate** — `scripts/deliberation_quality.py`, PASS/FAIL against a `tunable()` floor, shipped
   **warn-only**, exactly as S156 did for law-coverage assertion E.
6. **Part B, the three-arm sweep** (below).

### Out of scope (do NOT build this sprint)

- **Changing any deployed tunable.** This sprint produces numbers. Moving `effort` or `max_rounds`
  on the fleet is a separate, deliberate act.
- **Fixing the 56 %.** Measuring it and improving it are different sprints. If the harness suggests a
  cause, write it in the design log and stop.
- **Anything in the live deliberation path.** S172 owns wall clock; this owns reproducibility.
- **No `laws.md` edit** unless the law-cycle question flipped to Yes — then the amendment is in scope
  and named above.
- **No ADR reversal.** An ADR is reversed by a new ADR, never by a sprint.

### The road not taken (LAW-06)

- **Measure reproducibility on the live nightly path.** Rejected: a quiet market withholds real
  debates indefinitely — the last four nights produced 2, 2, 9 and 7 orders, and two of those
  produced no comparable pair at all. Replay is the only way to choose the sample.
- **Use the synchronous API for the repeats.** Rejected on [DL-105](../design-log.md)'s measurement:
  same tokens at twice the price, for a workload with **no latency requirement whatsoever**.
- **Compare verdict *text* rather than verdict *labels*.** Rejected: the label is what execution acts
  on (`drop_vetoed` reads the ticker list), so label disagreement is the thing with consequences.
  Text similarity is a richer signal and a later question.
- **Fix `effort` by reasoning from the token cap.** Rejected on measurement, not on principle: the
  cap is not biting (394 tokens out against 4096, zero non-`end_turn`), so the theory has nothing to
  stand on. Recorded so it is not re-proposed.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Does the reproducibility figure get persisted to the graph?** This is the law-cycle fork above.
   Persisting makes the number durable and trendable, and **owes a `DLIB-OBS-05` clause plus the full
   cycle**. Not persisting keeps the sprint read-only and the harness a pure derivation. **Say which,
   and why.**
2. **What is "comparable"?** A verdict pair is only comparable if both sides are real debates on the
   same ticker in the same `PMRun`. Fail-opens are stored as `verdict: "uphold"`
   (`review_record.fail_open_review`), so **every metric must exclude them and prove it does**.
   DL-104's run D is 5 of **6**, not 5 of 10. Define the predicate once, in one place, and test it.
3. **How many repeats, and what interval do you report?** N repeats per arm gives a proportion; state
   the interval method and why it suits a small N. A bare percentage without an interval does not
   satisfy success factor 1.
4. **What does the gate do on its first day?** Warn-only is specced. Name the `tunable()` floor and
   its `why`, and be explicit that the threshold is **uncalibrated until this sprint's own numbers
   exist** — a gate that blocks on an invented threshold is worse than no gate.

🪤 **Take the next free DL number, then re-check it at merge.** The log has historic duplicates —
including **two `DL-148`** as of 2026-09-03 — and entries are prepended at the top *and* appended at
the bottom. A branch cut before another DL lands will collide even when the number was free at branch
time. **Check again when you merge.**

---

## Blast radius — measured 2026-09-03

| What | Detail |
| --- | --- |
| Files changed | new harness module(s) under `agents/deliberator/` or `orchestration/`; new `scripts/deliberation_quality.py`; tests. 🪤 `agents/deliberator/context_pm.py` is **152 lines** — if you must touch it, **split rather than grow**: the hard block is 200 |
| Agents affected | deliberator only — and confirm it imports no other agent |
| Contract change? | **No** as specced. If decision 1 says persist, **yes in effect** — the law cycle becomes mandatory |
| Graph vocabulary change? | **No** as specced. If decision 1 says persist, **yes** — and the deploy becomes a **full `up`**, not a retag |
| New env keys / tunables | the gate's floor `tunable()`; the batch model/effort/arm selectors if you register them. **Any new tunable makes the deploy a full `up`** |
| Deploy implication | **None as specced** — this is offline tooling and does not have to reach the fleet at all. Say so at handback rather than deploying out of habit |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md`, decision 1 first — it changes the shape
   of everything after it.
3. **Step 0 as a failing test first**, and watch it fail: rebuilt digest vs stored `prompt_hash`.
   🚨 **If it cannot be made to pass, stop and report — that is a complete and acceptable outcome**,
   and it is a contradiction of **DLIB-OBS-01** worth more than the rest of the sprint.
4. **Implement** the harness, then batch submission, then the metrics, then the gate.
5. **Re-derive the 56 % baseline** through the harness from DL-104's runs. If the harness cannot
   reproduce the hand-computed figure, **the harness is wrong** — say so and stop.
6. **Part B**: run the three arms.
7. **Law cycle** if decision 1 owed one — clause, test-plan row, docstring citation, rollups, drift row.
8. **Prove the guards can fail (DL-70)** — break the implementation, watch each guard go red, restore.
9. **`make ci` green** — all 12 steps, **redirected to a file, never piped**.
10. **Fill the handback sections** at the bottom of this file.

---

## Step 0 - RE-MEASURED 2026-09-05, after the 49-commit catch-up merge, and now a committed script

🚨 **The catch-up merge could have invalidated step 0 and did not - checked, not assumed.** The
branch forked at `f89f8e9`; `main` has since carried S172, S180, S191, S194-S198 and the peer-replica
fix. **S197 changes the PM gate `detail` string**, which is rendered straight into the veto context, so
the first question was whether the renderer moved. It did not: `orchestration/veto_context.py`,
`agents/deliberator/context_pm.py`, `kernel/deliberation.py` and `kernel/llm_ledger.py` are **all absent
from the 49-commit diff**. S197 put its census in the *stored data*, not the renderer, so historical runs
render exactly as before.

🟩 **Re-proven live, and stronger than before: 10 of 10 on the five most recent debated runs** -
`pm-run-5c9c98f0`, `d5688a43`, `63b92d6a`, `c31f4806`, `f6614d3f`, spanning 2026-09-01 through
2026-09-04, i.e. nights recorded after S194, S195, S196 **and** S197 merged. The spec's original claim
was 4 of 4.

| Measure | Value | How |
| --- | --- | --- |
| Corpus on the spine now | **65 `PMRun`, 65 `DeliberationRun`, 1,172 `LLMCall`** | *[measured 2026-09-05]* live listing; every call carries a `prompt_hash` |
| Approved orders across all runs | **329** | *[measured 2026-09-05]* `scripts/deliberation_reproducibility.py` |
| Turns with a stored hash to compare | **280** | same - 49 approved orders were never debated (fail-open or no turn) |
| Replay to their stored hash, **whole corpus** | **57 of 280 = 20.36 %** | same |
| Replay to their stored hash, **five most recent runs** | **10 of 10 = 100 %** | same, `--run-id` per run |

🎯 **The two numbers together are the finding.** 100 % on current-code runs says the harness is
correct; 20 % across history says **replay fidelity tracks the recording code version**, which is
work-queue **item 44** and not this sprint's job. Reporting only the 20 % would have read as a broken
harness; reporting only the 100 % would have hidden the drift.

🪴 **The measurement is a committed script this time, not a scratchpad.**
`scripts/deliberation_reproducibility.py` is read-only (zero `merge_node` / `add_edge`), takes
`--run-id` to narrow, and **states its denominator** rather than printing a bare percentage - S192
recorded that DL-140's harness lived in a session scratchpad and was gone when it was next needed.
🪴 It was run from the branch worktree with `POSTGRES_DSN` passed **through the process
environment only**, never as a file in the tree, so the no-secrets-in-the-worktree rule held while
branch code still read the live spine.

---

## Step 0 — RESULT, measured live 2026-09-03

🟩 **Step 0 passes, and it is a real `DLIB-OBS-01` proof — scoped.** `orchestration/deliberation_replay.py`
reproduces the recorded user prompt **byte-for-byte**, verified against the ledger's own digest, on the
turns recorded by the renderer currently on `main`: **4 of 4** (`sched-2026-09-01`, `sched-2026-09-02`,
full lineage, 7,933-char contexts).

🚨 **Across all history it is 49 of 272, and the failures are not random.** Replay fidelity tracks
**the code version that recorded the run**:

| Group | Replays | Why |
| --- | --- | --- |
| `sched` runs on `s191` / `s194` (built from `main`) | **4 / 4** | recorded by today's renderer |
| every `sched` run 2026-08-07 → 08-28 | **0 / N** | recorded by an older renderer — S175 removed the ATR fragment, S183/S184 changed `FilterVerdict` |
| three `verify-2026-08-19-s172-k4-*` | 45 / 45 | 🪤 **not evidence** — these are synthetic runs with *no lineage*, so the string is a short early-return that barely changed |
| `verify-2026-09-01-s192-k4` | **0 / 15** | recent, but recorded on **`s172b`**, the unmerged branch image |

🪤 **The distinction I got wrong first, corrected here because it changes the sprint's size.** "Replays to
the stored hash" and "can be rendered and re-run today" are **different questions**:

- Matching a *historical* hash needs the recording code — that is the **4 turns** above, and it is only
  needed to validate the replay path, which it now has.
- **Self-agreement needs neither.** It generates all N samples itself under identical conditions the
  harness controls, so it needs only **intact lineage**. Measured 2026-09-03: **46 `PMRun`s with full
  lineage carrying 261 approved orders** (plus 4 early-return runs and 11 with no approved orders).

🎯 **So Part A is not blocked and never was — the corpus is 261 orders across 46 runs**, far past the
"≥ 3 historical `PMRun`s" this spec asks for.

🚨 **One success factor is withdrawn as unmeetable.** *"The 56 % baseline is reproduced or refuted
against DL-104's four runs, by the harness"* — those runs are 2026-08-08/10 and replay **0 / 18**. The
prompts that produced the 56 % no longer exist in reproducible form. **The 56 % stays a historical
datapoint and stops being a target**; the sprint measures a **fresh** baseline under today's code
instead, on a far larger sample. Recorded rather than quietly re-scoped.

🟠 **The gap that made this discoverable-only-by-accident is filed, not fixed here:** nothing stamps
`LLMCall` with the code version that produced it, so replayability is unknowable until you try. That is
**work-queue item 44** — a graph-vocabulary change, which drags in the pack, a law cycle and a full `up`
deploy, and would swallow this sprint.

---

## Part B — the effort and `max_rounds` sweep

🚨 **The control arm is not optional, and it is the whole reason Part B lives in this sprint.** At
**56 %** self-agreement the same configuration disagrees with itself on nearly half of comparable
verdicts. A `high`-vs-`medium` difference **cannot be told apart from that noise** without measuring
the noise first. Three arms, same `PMRun`s, same repeats, one batch:

| Arm | Varies | Answers |
| --- | --- | --- |
| **A — control** | nothing (`high` vs `high`) | the noise floor; this is Part A's self-agreement number |
| **B — effort** | `high` vs `medium` (and `low` if B separates) | whether `effort` moves verdicts **beyond** the floor |
| **C — rounds** | `max_rounds` 2 vs 1 | whether the second round changes the verdict at all |

**Report each arm as an agreement rate against arm A's interval, never as a bare percentage.** A
result inside arm A's interval is *"indistinguishable from noise"* — a finding, not a failure.

🪤 **Arm A must replay at `effort=high`, the deployed value**, not the `max` that `settings.py`
defaults to. Replaying at the code default measures a configuration that has never run in production.

🪤 **Arm C measures a decision, it does not make one.** `max_rounds` 2 → 1 has been rejected twice on
the same recorded ground: the debate's own `why` requires more than one round in live proof, so
cutting it is *"cutting the artefact under test to buy wall clock"*. **Measuring it here is in scope;
changing the deployed value is an ADR, not a sprint outcome.** Report the number and stop.

🪤 **Arm B carries a confound, and it runs the opposite way to the obvious one.** Lowering `effort`
also shortens the peer-call tail, and that tail is what interacts with `request_timeout_seconds` —
the coupling that caused three fail-opens on 2026-08-13. **In batch there is no timeout, so the
confound is absent here**, which means a Part B result **does not transfer to the live path
unchanged**. Say so in the report rather than implying the sweep licenses a live change.

**Cost, measured rather than guessed.** 5 calls per order at ≈ 5,800 in / 1,280 out. Multiply by
orders × repeats × arms, halve for batch pricing, report against the synchronous equivalent.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 Rebuilt context digest equals the stored `prompt_hash` | one real historical `PMRun` fixture | replay reconstructs the *same bytes* the live run sent — **DLIB-OBS-01**, **DLIB-IDM-02** |
| A2 | Self-agreement over N repeats returns a rate **and** an interval | a fixture with known verdict labels | success factor 1's shape, not just its value |
| A3 | 🪤 Fail-opens are excluded, and the count is reported | a run mixing real verdicts with `fail_open_review` uphelds | DL-104's run D reads 5 of **6**, never 5 of 10 |
| A4 | 🪤 The harness writes nothing | a planted `merge_node` in the derivation path | the planted write **fails the test** — watched failing first |
| A5 | Batch results keyed by `custom_id`, not position | results returned deliberately out of order | reassembly is order-independent |
| A6 | The gate can FAIL | a planted low-agreement fixture | `deliberation_quality.py` returns FAIL |
| A7 | The gate can PASS | a planted high-agreement fixture | the gate is not stuck red |
| A8 | Part B arms are separable | fixtures for arms A/B/C | each arm reports against arm A's interval |

---

## Success factors

- [ ] **Step 0 proved, not asserted:** a rebuilt context digest **equals** the stored `prompt_hash`
      for at least one real historical `PMRun`, both hashes quoted. If it does not, the sprint stops
      there and reports that — a complete and acceptable outcome.
- [ ] **Self-agreement is a number with a confidence interval**, over ≥ 5 repeats on ≥ 3 historical
      `PMRun`s (15 clean ones exist), with the fail-open exclusion count beside it.
- [ ] ~~**The 56 % baseline is reproduced or refuted** by the harness rather than by hand.~~
      🚨 **WITHDRAWN 2026-09-03 as unmeetable** — DL-104's runs replay **0 / 18** under today's
      renderer. Replaced by: **a fresh self-agreement baseline measured under today's code**, on
      the 46-run / 261-order corpus, reported beside the historical 56 % without claiming to
      reproduce it.
- [ ] **The harness writes nothing** — planted `merge_node` fails a test, watched failing first.
- [ ] **Batch economics measured, not assumed:** actual batch cost against the synchronous
      equivalent, and the observed turnaround.
- [ ] **The gate can fail** — planted low-agreement fixture drives FAIL, high-agreement drives PASS.
- [ ] **Part B: all three arms reported against arm A's interval**, each with its fail-open exclusion
      count, and an explicit statement of which differences fall **inside** the noise floor. A bare
      "quality was the same" without arm A's interval does not satisfy this.
- [ ] Design decisions recorded with rejected alternatives.
- [ ] Law cycle done, or the law-cycle question answered No **with the reason and the fork stated**.
- [ ] Every new guard planted, watched to fail, restored — stated per guard.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **Self-agreement is not accuracy.** A veto that agrees with itself 100 % of the time on unsound
grounds is reproducibly wrong. This gate measures *precision of process*; DL-104 class-3 (grounds that
checked out correct) is the only accuracy signal we have, and it is **2 of 15**.

🪤 **A fail-open is stored with `verdict: "uphold"`** (`review_record.fail_open_review`). Any run with
fail-opens must have those tickers excluded before a rate is computed, and **every metric must prove
it applies the exclusion**.

🪤 **Prompt caching: put the `cache_control` breakpoint at the end of the *shared* span**, not at the
end of the whole prompt. Otherwise each request writes its own cache entry and nothing is ever read.

🪤 **The `fallbacks` parameter is rejected on the Batches API**, and **`max_tokens: 0` is rejected
inside a batch** — the cache pre-warm trick does not apply here. A refusal in a batch result is
handled by the caller.

🪤 **Do not let the harness become a second live tracker.** Its output is a report, not state. The
live "does it work" proof stays in `docs/laws/ledger.md` and `docs/laws/drift-register.md`, and the
one live status doc is `docs/STATE.md`.

🪤 **Two traps this spec used to carry are CLEARED — do not reinstate them.** The invented ATR
fragment is **gone** from `context_pm.py` (verified 2026-09-03: no `atr` reference remains; the gate
line now reports the real `stop_vs_regime_volatility` comparison), shipped in S175. And the
Anthropic-key date of 2026-09-01 has **passed**, with [DL-135](../design-log.md) verifying both
providers `HTTP 200`.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `agents/deliberator/context_pm.py` **152**, `agents/deliberator/review_record.py`
  **100**, `kernel/llm_ledger.py` **115**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. 🪤 A **mode selector** is *not* a
  tunable — check the PARAM table before registering.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 12 steps** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — `make ci | tail` reports *`tail`'s* exit code. Redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it.
- Secrets never through the worktree — a worktree has **no `.env`**, so any proof needing live data is
  vacuous there. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving** — it resolves the SHA
   from the working directory and ignores a `SHA=` argument. **Check the printed SHA against
   `git rev-parse HEAD`.**
2. Merge to `main` locally and push. 🪤 Check you are not on the branch already — a `git merge` from
   the branch's own worktree says *"Already up to date"* and merges nothing.
3. **Post-merge CodeQL.** `codeql.yml` runs **only on `main`**, so a green branch gate is not proof of
   a CodeQL-clean merge. Check after merging.
4. **Deploy: none as specced.** This is offline tooling. Deploy only if decision 1 persisted to the
   graph — and then it is a **full `up`**, not a retag.

---

## Handover — paste this to Codex

```text
Work item: S173 - a verdict that cannot be reproduced is not evidence.
Repo: trading-agents. Branch: sprint-173-a-verdict-must-be-reproducible, cut from main BEFORE any
code. Never commit to main. Read docs/sprints/sprint-173-a-verdict-must-be-reproducible.md in full,
then CLAUDE.md, then docs/INDEX.md before opening any docs folder.

MUST RULE - DO NOT OPEN AN EDITOR FIRST. Read agents/deliberator/laws/laws.md and test-plan.md
whole, plus docs/laws/conventions.md and docs/laws/drift-register.md. Then write the "Law reading
record" at the bottom of the sprint file BEFORE your first code change. laws.md is LOCKED and
read-only during a build. If a law contradicts the spec, STOP and report - the law is more likely
right. Binding: DLIB-IDM-02, DLIB-OBS-01, DLIB-OBS-02.

WHAT IS WRONG
The veto does not agree with itself and nothing measures it. Two DeliberationRuns on the same model,
same prompt, same 18 tickers, 3.5 hours apart agreed on 9 of 16 verdicts - 56%, on a binary verdict.
DLIB-IDM-02 asserts outputs are "bounded by ... prompt hashes, response hashes" and NOTHING measures
that bound.

STEP 0, AND IT GATES THE WHOLE SPRINT
Every LLMCall row stores prompt_hash, written as _digest(capture.prompt) at kernel/llm_ledger.py:65.
Rebuild the deliberation context for a stored PMRun, digest it the SAME way, and compare to the
stored hash. Write this as a FAILING TEST FIRST and watch it fail. If it cannot be made to pass,
STOP AND REPORT - that is a complete and acceptable outcome, and it contradicts DLIB-OBS-01
("narrative and transcript are reconstructable from DeliberationRun alone"), which is worth more
than the rest of the sprint.

THEN
1. Record design decisions in docs/design-log.md WITH rejected alternatives, BEFORE implementing.
   Decision 1 first: does the reproducibility figure get PERSISTED to the graph? If yes, this sprint
   owes a full law cycle (new DLIB-OBS-05 clause - OBS-04 is taken by S194 - plus test-plan row,
   clause ID in the test docstring, rollups in BOTH docs/laws/ledger.md and docs/laws/INDEX.md, and
   a drift-register row) and the deploy becomes a full `up`. If no, the sprint stays read-only.
   Say which branch you took and why.
2. Build a READ-ONLY replay harness. ZERO merge_node / add_edge calls in the derivation path -
   follow accept.py / trace_run.py / observatory.py. Plant a merge_node, watch the test fail,
   restore. The corpus is 61 DeliberationRun rows that CANNOT be regenerated.
3. Batch submission, custom_id = {pm_run}:{ticker}:{repeat}:{arm}:{role}. Results arrive in ANY
   ORDER - key by custom_id, never by position.
4. Prompt caching: put the cache_control breakpoint at the end of the SHARED span, not the end of
   the whole prompt, or every request writes its own entry and nothing is read.
5. Metrics with fail-opens EXCLUDED and the exclusion count reported beside each. A fail-open is
   stored as verdict "uphold" (review_record.fail_open_review), so DL-104's run D is 5 of 6, not
   5 of 10. Define the "comparable" predicate ONCE and test it.
6. Re-derive the 56% baseline through the harness. If it cannot reproduce the hand-computed figure,
   THE HARNESS IS WRONG - say so and stop.
7. Gate: scripts/deliberation_quality.py, PASS/FAIL against a tunable() floor, shipped WARN-ONLY
   (as S156 did for law-coverage assertion E). A gate whose threshold has never been calibrated must
   not block a merge on its first day.
8. PART B, three arms, same PMRuns, same repeats, one batch:
   A control (high vs high) = the noise floor; B effort (high vs medium); C rounds (2 vs 1).
   REPORT EVERY ARM AGAINST ARM A'S INTERVAL, never as a bare percentage. At 56% self-agreement a
   high-vs-medium difference cannot be told from noise without the control.
   Arm A must replay at effort=high - the DEPLOYED value. settings.py defaults to max, which has
   never run in production.
   Arm C MEASURES a decision, it does not make one: changing max_rounds is an ADR, not a sprint
   outcome. Report the number and stop.
   Arm B does NOT transfer to the live path unchanged - batch has no timeout, and the effort/tail/
   request_timeout_seconds coupling is what caused three fail-opens on 2026-08-13. Say so.

MEASURED FACTS (do not re-derive)
- Clean replay corpus: 15 DeliberationRuns with real debates and zero fail-opens, of 23 with real
  debates, of 61 total. 210 ticker verdicts. 1,132 LLMCall rows.
- 5 calls per order (defender:r1, challenger:r1, defender:r2, challenger:r2, judge), ~5,800 tokens
  in / 1,280 out per order.
- The 4096 max_tokens cap is NOT biting: largest tokens_out across the last 95 calls was 394, zero
  non-end_turn stops. Do not build on a truncation theory.
- agents/deliberator/context_pm.py is 152 lines - past the 150 warn line. If you must touch it,
  SPLIT rather than grow. Hard block is 200.

DO NOT
- Do not change any deployed tunable. This sprint produces numbers.
- Do not touch the live deliberation path. S172 owns wall clock.
- Do not edit laws.md unless decision 1 flipped the law-cycle answer to Yes.
- Do not pin a version number - it is "next available MINOR at merge". feat -> MINOR.
- Do not measure make ci through a pipe. Redirect to a file and read the file.
- Do not leave the Closeout placeholder intact - a handback with it unfilled is returned, not
  repaired.

Take the next free DL number and RE-CHECK IT AT MERGE - the log already has two DL-148 entries and
entries are prepended at the top and appended at the bottom.
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

*Filled 2026-09-03, before the first code change.*

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| the replay harness | `agents/deliberator/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | **DLIB-OBS-01** (⬜, test `_tbd_`) | **Yes, twice.** (1) OBS-01 is **unproven** — the harness is not *relying* on a proven claim, it is the **first test of it**. (2) Reading `kernel/deliberation.py:89` showed the `user` string is `_render(proposition, transcript)`, and for **`defender:r1` the transcript is empty** — so that one turn is reconstructible from graph state *alone*. That is now the step-0 assertion, because it isolates `build_veto_context` from transcript fidelity |
| the reproducibility metric | same | **DLIB-IDM-02** (⬜, test `_tbd_`) | **Yes.** The clause's bound is **narrower than it reads** — see contradictions below |
| batch cost reporting | same | **DLIB-OBS-02** (⬜, test `_tbd_`) | **Yes.** Attribution is real, but the *quantity* is a word count — work-queue item 43. Part B's cost figures must come from the API's `usage`, not from `LLMCall` |
| `_render` / digest parity | `docs/laws/conventions.md` | — | The digest must be **the same function** the ledger uses, not a re-implementation, or step 0 proves only that two hash functions agree |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?**
**No new clause is owed as specced** — no `contracts/` type changes, and the harness is a read-only
derivation. 🚨 **But the sprint is not law-neutral:** all three clauses it touches are **⬜ with test
`_tbd_`**, so S173 is the first thing to prove them. That owes the *proving* half of the cycle —
clause IDs cited in the test docstrings (conventions §3), the `_tbd_` rows in `test-plan.md` replaced
with real test names, and the rollup recomputed in **both** `docs/laws/ledger.md` and
`docs/laws/INDEX.md`. 🪤 The rollup is derived — let `make ci` tell you the number.
**Decision 1 branch taken:** *not yet taken — recorded here at handback.*

**Contradictions found between a law and this spec:**
🚨 **One, and it is material.** `DLIB-IDM-02` says LLM outputs are *"bounded by role, model, max
rounds, **prompt hashes**, response hashes, and timestamps"*. Measured: `agents/deliberator/agent.py:139`
passes **`prompt=user`** to `record_llm_call`, so `prompt_hash` is `sha256` of the *user* string only
and **does not cover the system prompt** (`kernel/llm_ledger.py:110`). Two calls with identical
`prompt_hash` can therefore have had **different system prompts** — precisely what a compiled-prompt
change ([DL-42](../design-log.md)) does. The bound is real but narrower than the clause reads.
**Not treated as a law defect to fix in this sprint** — the clause is LOCKED and the honest response
is a `drift-register.md` row plus scoping step 0's claim to the user half. Filed accordingly.

**Laws found silent where a decision was needed:**
**One.** No clause says whether a *derivation* over `DeliberationRun` may write anything back. The
prohibition this sprint works under (`the harness writes nothing`) is a **spec invariant and an S160
convention, not a law**. Recorded here rather than assumed; if decision 1 persists the figure, that
silence is what a new `DLIB-OBS-05` would fill.

**Clauses that were ⬜ and are now proven:** *(fill at handback — candidates are DLIB-OBS-01 via
step 0, DLIB-IDM-02 via the reproducibility metric, and DLIB-OBS-02 only if Part B's cost reporting
uses the API's own `usage` rather than the ledger's word counts.)*

---

## Test plan results — filled at handback 2026-09-05

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| step 0 | `test_defender_r1_replays_to_its_recorded_prompt_hash` | `tests/test_deliberation_replay.py` | 🟩 | DLIB-OBS-01 / DLIB-IDM-02 |
| step 0 | read-only assertion on the replay | `tests/test_deliberation_replay.py` | 🟩 | DLIB-OBS-01 |
| measure | 6 tests | `tests/test_deliberation_reproducibility.py` | 🟩 | DLIB-IDM-02 |
| identity | 6 tests | `tests/test_replay_keys.py` | 🟩 | — |
| rounds | 15 tests | `tests/test_replay_rounds.py` | 🟩 | DLIB-TYP-03 |
| driver | 8 tests | `tests/test_replay_batch.py` | 🟩 | — |
| corpus | 4 tests | `tests/test_replay_corpus.py` | 🟩 | — |
| metrics | 7 tests | `tests/test_verdict_metrics.py` | 🟩 | — |
| sources | 5 tests | `tests/test_verdict_sources.py` | 🟩 | — |
| interval | 7 tests | `tests/test_agreement.py` | 🟩 | — |
| gate | 7 tests | `tests/test_quality_gate.py` | 🟩 | — |

**Tests added beyond the plan:** the DL-70 sweep found two guards that did not guard, and both fixes
added assertions — `test_the_interval_is_wilsons_by_value_not_merely_by_range`, and a
`no_counterpart == 2` assertion on `test_two_different_decisions_are_never_compared_against_each_other`.

**Clauses that were ⬜ and are now proven: none.** This is the honest outcome, not an omission.
`DLIB-IDM-02` was the candidate, and measuring it produced **DRIFT-056** instead of a green: the
clause's `prompt hashes` bound covers the *user* string only. Greening a clause this sprint just
filed drift against would be certifying the half that was measured as if it were the whole.
`DLIB-OBS-02` needs Part B's `usage` figures, which do not exist because nothing was submitted.

---

## Closeout — evidence

**Result: Part A complete and proven; Part B built but unfunded and therefore unrun.**

**Decision 1 branch taken: NOT PERSISTED.** The figure is a pure derivation over stored state; no
`merge_node`, no `add_edge`, no new label. Consequences, all confirmed: **no law cycle owed, no
`contracts/` change, no graph-vocabulary move, and no deploy** — this sprint does not reach the
fleet at all. Recorded in DL-159. The road not taken: persisting would make the figure trendable and
owe a `DLIB-OBS-05` plus the full cycle; rejected because there is no figure worth trending until a
funded sweep produces one, and a persisted zero-sample metric is a durable lie.

**Files changed:** `orchestration/replay_keys.py`, `replay_types.py`, `replay_rounds.py`,
`replay_corpus.py`, `replay_batch.py`, `agreement.py`, `verdict_metrics.py`, `verdict_sources.py`,
`quality_gate.py`, `settings.py`, `deliberation_replay.py`; `scripts/deliberation_reproducibility.py`,
`deliberation_replay_batch.py`, `deliberation_quality.py`; eleven test files;
`docs/design-log.md` (DL-158, DL-159), `docs/laws/drift-register.md` (DRIFT-056).

**Step 0 — rebuilt digest vs stored `prompt_hash`: MATCHED.** Re-measured 2026-09-05 after the
49-commit catch-up merge, via the committed `scripts/deliberation_reproducibility.py` against the
live spine:

| Sample | Result |
| --- | --- |
| Whole corpus | **57 of 280 = 20.36 %** |
| Five most recent debated runs (2026-09-01 → 09-04) | **10 of 10 = 100 %** |

Both numbers are the finding. 100 % on current-code runs says the harness is correct; 20 % across
history says replay fidelity tracks the *recording* code version — work-queue item 44, not this
sprint. Quoting either alone would mislead.

**Self-agreement: not measured — nothing was submitted to a provider.** The harness plans
**1,645 requests** for one repeat of one arm over the live corpus (65 PM runs, 0 unreadable,
**329 subjects**), proven by a read-only `--dry-run` end to end. No self-agreement number exists and
none can until a sweep is funded.

**56 % baseline: REPRODUCED, exactly.**
`scripts/deliberation_quality.py --recorded-run pm-run-0c3c9324… --recorded-run pm-run-cbd26639…`:

```text
self_agreement: matched=9; compared=16; excluded=0; no_counterpart=2;
                rate=56.25%; ci95=[33.18%, 76.90%]
```

`matched=9, compared=16` — DL-104's hand-computed figure, through the same code path every other
agreement number goes through. 🚨 **And the interval is a finding of its own: [33.2 %, 76.9 %]
contains both 50 % and 75 %, so the 56 % that has been cited in three decisions cannot distinguish
"chance" from "acceptable".** Recorded in DL-159.

**Part B — three arms: NOT RUN.** Built arm-agnostic and unfunded by design; the arm count is an
operator decision against DL-158's table (control only ≈ $30 · three arms × 3 ≈ $90 · three arms ×
5 ≈ $151), not an assumption baked into code.

**Batch economics: priced, not observed.** $0.0305 per order-replay on batch (DL-158). No batch has
been submitted, so turnaround is unmeasured.

**Guards planted (DL-70): 10 mutations, 10 caught — after two rounds.** The first sweep planted ten
and **two survived**: `wilson_interval`'s `max(0.0, …)/min(1.0, …)` clamps returned an in-range
interval from a deliberately corrupted denominator, and `self_agreement`'s `no_counterpart` could be
zeroed because its only covering test used a case where zero is correct. The clamps are removed (a
clamp cannot correct a real Wilson bound, only hide a broken one) and the interval is now pinned by
value. Re-run: **10 of 10 red, then restored, then `make ci` green.**

**`make ci`: exit 0** — **2592 passed, 6 skipped, 100.00 % coverage**, redirected to a file and read,
never piped.

**`make gate-ran`:** *(filled below at merge.)*

---

## Return notes

**What this spec got wrong, measured:**

1. 🚨 **The `custom_id` shape implies a batching that is impossible.**
   `{pm_run}:{ticker}:{repeat}:{arm}:{role}` reads as though one debate's five calls go into a batch
   together. They cannot — `render_debate_prompt` interpolates the transcript, so turn N+1's prompt
   contains turn N's answer. The harness runs **five dependent rounds**, each a batch across every
   debate. Recorded as DL-158 before any code was written.
2. **`custom_id` also cannot be that string on the wire.** The Batch API bounds it by charset and
   length, and a colon-separated label satisfies neither. The readable label is kept, sanitised and
   truncated, then made unique again by a digest of the *whole* label — so truncation can never
   merge two turns.
3. **"46 runs / 261 approved orders" is now 65 / 329.** Re-measured through the committed corpus
   builder; the spec's 2026-09-03 figures were correct when written.

**What was found that the spec did not anticipate:**

4. 🚨 **83 of 329 approved orders on the spine are fail-opens — 25.2 %.** Every one of the other 246
   has a real recorded verdict, so the corpus splits exactly two ways with nothing unaccounted for.
   The spec was right that the exclusion predicate matters; it is larger than "a correction".
5. **The recorded verdict distribution is 61 % `revise` over 246, not DL-104's 78 % over 58.**
6. 🪤 **The two graph stores return different Python types for one property.** `InMemoryGraphStore`
   freezes props (`dict` → `mappingproxy`, `list` → `tuple`); Postgres returns plain JSON. An
   `isinstance(x, dict)` guard passes in production and fails in tests. Caught by a red test here;
   every reader of `node.props` is exposed. Both in DL-159.

**Not done, stated plainly:**

- **No provider submission, so no self-agreement, no cross-vendor number, and no Part B.** Awaiting
  the funding decision.
- **`DLIB-OBS-02` remains ⬜.** Part B's cost reporting was to prove it from the API's `usage`;
  nothing was submitted.
- **Cross-vendor agreement is not implemented.** Only an Anthropic batch adapter exists; a `gpt-5.5`
  arm needs an OpenAI batch adapter, which is a separate piece of work and was not in Part A's path.

**For the next sprint:** the DL-70 mutation sweep was run from a throwaway script and found two real
gaps in one pass. A repeatable version is worth having, but it is **deliberately not queued**: the queue is under a
2026-09-18 empty-by deadline and this is discretionary. Recorded here so the next person can pick it
up without rediscovering it.
