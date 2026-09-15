<!-- Agent: planning | Role: sprint handover -->
# Sprint 206 — a rendered verdict names the check that produced it

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-206-a-rendered-verdict-names-the-check-that-produced-it`
**Status:** SHIPPED
**Version:** `0.98.04`
**Effort:** M
**Decisions:** [DL-167](../design-log.md) the open thread · `DRIFT-062` the row this opens · work-queue item **59**

> **Why this bump kind.** PATCH. No agent gains a capability. The deliberator already promises
> adversarial review of *what the PM decided*; rendering a `FAILED` for a comparison no agent
> performs is that promise broken, not a new one made. The new clause codifies the existing
> intent — it does not extend it.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`DLIB-IDN`**, **`DLIB-OUT`**, **`DLIB-NEV`**, **`DLIB-IN`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**`contracts/` — No.** *[measured 2026-09-15]* `StopTargetEvidence` already lives at
`contracts/analyst.py:30` and is already carried by `Recommendation.stop_target_evidence`
(`contracts/analyst.py:63`). Everything this sprint needs to render is already in the type. Confirm
with `git diff --stat contracts/` — **it must be empty**.

**A new guarantee — Yes, one.** The deliberator will promise something its law book does not
currently say: that a rendered verdict corresponds to a check some agent actually performs. So this
sprint **owes a full law cycle**: `DLIB-NEV-08`, a `test-plan.md` row, the clause ID in the test
docstrings, `laws.md` **v1.6 → v1.7** with a Changelog line, and the rollup updated in **both**
`docs/laws/ledger.md` **and** `docs/laws/INDEX.md`. 🪤 **The rollup is derived, not declared** —
`make ci` recomputes it. Let the gate tell you the number.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/deliberator/context_pm.py` | `agents/deliberator/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `DLIB-IDN-01` (the job is review of *the PM's* decision); `DLIB-NEV-06`/`-07` (the existing "do not misrepresent the debate" pair this sits beside) |
| `agents/deliberator/context_stop.py` | same | Same clauses. Its docstring already states the rule this sprint codifies: *"render analyst stop-target proposal evidence **without inventing a gate**"* |
| `agents/deliberator/laws/laws.md` | itself, plus `conventions.md` §2 (append-only IDs) | You are adding `DLIB-NEV-08`. **LOCKED v1.6** — this is a deliberate cycle, not a quiet edit |

⚠️ **The invariant this sprint must not break: the deliberator may only ever *subtract* PM-approved
orders (`DLIB-OUT-04`), and never originates or resizes one (`DLIB-NEV-01`/`-02`).** Nothing here
touches what is traded. If your change alters *which* orders exist rather than *what the referee is
told*, stop and report.

---

## Goal

Every `PASSED` / `FAILED` the deliberator renders into a debate context corresponds to a check some
agent actually performs, and names it. Today one of them does not, and it is mathematically
incapable of passing.

---

## Why (context)

*[All figures measured 2026-09-15 against the live spine, repo at `b244e45`; see
[DL-167](../design-log.md) and work-queue item **59**.]*

`_stop_regime_line` (`agents/deliberator/context_pm.py:123-142`) renders:

```text
stop_vs_regime_volatility gate: stop_pct=X vs base_stop_loss_pct=A -> PASSED|FAILED;
                                target_pct=Y vs base_take_profit_pct=B -> PASSED|FAILED
```

Three facts, each measured:

1. **No agent performs that comparison.** The PM emits exactly **nine** gate names — `atr_pct`,
   `cash_available`, `correlated_cluster_pct`, `max_names_per_sector`, `max_positions`,
   `max_sector_pct`, `min_order_quantity`, `reward_risk`, `sizing`. `stop_vs_regime_volatility` is
   not among them in any code path, and the string `stop_vs` does not appear in
   `agents/portfolio_manager/` at all. The only two uses of the regime bases outside the deliberator
   are a *derivation input* (`agents/analyst/domain/stop_target.py:42-43`) and a *default*
   (`agents/portfolio_manager/run.py:81-82`). Neither rejects anything.

2. **It compares a value against its own input, so under `scaled` it cannot pass.**
   `agents/analyst/domain/stop_target.py:86` defines
   `scaled_target = min(flat_target * (scaled_stop / flat_stop), 1.0)`. So whenever ATR tightens the
   stop (`scaled_stop < flat_stop`), `scaled_target < flat_target` **necessarily** — the target leg
   **cannot** pass and the stop leg **cannot** fail. Measured on `sched-2026-09-14`:
   WFC `stop 4.14% <= 5.00%` PASSED, `target 8.29% < 10.00%` **FAILED**; MDLZ `3.83%` / `7.66%`.
   Both orders carried `reward_risk = 2.0` **exactly** — the ratio the real gate tests — and both
   passed it.

🚨 **It is a mode detector, not a risk check — measured 2026-09-15 over the last 8 scheduled runs
(32 recommendations carrying `stop_target_evidence`):**

| applied mode | n | both legs PASSED | exactly one FAILED | both FAILED |
| --- | --- | --- | --- | --- |
| `flat` | 12 | **12** | 0 | 0 |
| `scaled` | 20 | **0** | **20** | 0 |

Of the 20 scaled cases, **13 fail the target leg** (bracket tightened, `2xATR < 5%`) and **7 fail the
stop leg** (bracket widened, `2xATR > 5%`). So the line does not detect risk in either direction — it
reports `flat` as all-clear and `scaled` as one-failure, **100 % of the time, both ways**. A reader
cannot distinguish "this bracket is dangerous" from "this bracket was adjusted at all".

🪰 **The clamps have never bitten, but they are not theoretical:** 0 of 32 hit the 2.5 % floor or the
8 % ceiling — though AMD reached **7.995 %** against the 8.00 % cap, 0.005 points short. The bounds
are the real protection here, and they are close to live, not far away.

3. **The referee leads with it.** Both 2026-09-14 vetoes cite it first: *"A live FAILED
   `stop_vs_regime_volatility` target leg was approved with no rendered waiver."* Both orders were
   dropped; the run submitted **0**.

🚨 **Why it matters beyond one night.** Splitting all 48 scheduled runs by `deliberation_status`: the
five where the referee genuinely ran (`applied`) submitted **0** orders each (`sched-2026-09-01,
-02, -03, -04, -14`); the four that reached the broker were all `applied_failed_open`
(`sched-2026-09-08..-11`). **Every order that has reached the broker since 2026-09-01 did so because
the referee was blind — 9 of 9.**

🪰 **This is a repeat, and the repeat is the point.**
[S175](sprint-175-the-veto-says-only-what-it-can-prove.md) removed the *sibling* invented comparison
(`stop_pct vs ATR%`) from this **same rendered line**, for this **same reason**
([DL-104](../design-log.md)). It left the other two comparisons in place and **wrote no clause**, so
nothing in the law book forbade the class. [S198](sprint-198-a-stop-we-never-measured.md)'s
`ANALYST_STOP_TARGET_MODE=scaled` flip (2026-09-05, deployed `s198`) then turned the survivor from
always-true into **always-false** — and the four blind nights meant no referee read it until
2026-09-14. **Two correct sprints composed into a defect neither could see alone.**

🪤 **The test that should have caught it protects it instead.**
`tests/test_veto_context.py:93` is named `test_regime_context_does_not_invent_an_atr_gate_outcome`,
its docstring reads *"PM context may not fabricate a gate verdict"*, and it cites **`DLIB-NEV-06`** —
a clause about *never hiding a failed debate or peer call as a clean veto*, which says nothing of the
kind. The test asserts `"ATR%" not in stop_line` **and** `"stop_vs_regime_volatility gate:" in
stop_line`: it forbids the removed fiction and **pins the surviving one**. Its fixture uses flat mode,
where `stop_pct == base_stop_loss_pct`, so the lie is invisible to it.

---

## Scope — and what is deliberately NOT here

**In scope — three renderers, audited as a set, not one defect fixed in isolation.**

| # | Site | Today | After |
| --- | --- | --- | --- |
| 1 | `_gate_outcome` (`context_pm.py:149`) | Renders real `GateOutcome`s from `gate_report`, with `NOT-EVALUATED` | **Unchanged.** It is truthful and `PM-NEV-09` already governs it |
| 2 | `_confidence_floor_line` (`context_pm.py:104`) | Renders `PASSED`/`FAILED` for a check that **is** real but is **not** named | Keep the verdict; **name the enforcer** — it is `agents/analyst/domain/recommend.py:87`, not a PM gate. The referee has already reasoned about it as if it were one |
| 3 | `_stop_regime_line` (`context_pm.py:123`) | Renders `PASSED`/`FAILED` for **no check at all** | **Stop rendering a verdict.** Render the basis: applied vs flat vs scaled, the mode, and the preserved ratio. Move it to `context_stop.py`, beside `stop_target_basis` |

Plus: drop the now-dead `bars` parameter threaded into `_stop_regime_line` (already `_bars`, unused
since S175), and rewrite the mis-named, mis-cited test at `tests/test_veto_context.py:93`.

**Explicitly NOT here — each is a separate decision, and taking one on is scope creep:**

- ❌ **Do not add a real stop-vs-regime-volatility gate.** Whether the PM *should* enforce a
  volatility relationship is a policy question with capital consequences. File it as a work-queue
  row; do not answer it in a defect sprint.
- ❌ **Do not touch the referee's other recurring grounds** — non-volatility-adjusted fixed-fraction
  sizing, and `correlated_cluster_pct` enumerating clusters that omit co-held names. Both repeat on
  **every** night measured. Both are unassessed. They are not this sprint.
- ❌ **Do not change `deliberation_posture`.** Work-queue item **6b** is gated on this sprint's
  measurement, not the other way round.
- ❌ **Do not change `contracts/`.** Everything needed is already on `Recommendation`.
- ❌ **Do not re-bless `prompt_hash` history.** See Traps.

---

## The design decisions this sprint has to make

### 1. Render a basis, not a verdict — and do not invent a passing one

🪤 **The tempting wrong fix is to make the comparison mode-aware** — compare the scaled target
against a *scaled* baseline so it passes. **Do not.** Under `scaled`, `scaled_target` is *defined* as
`flat_target * (scaled_stop / flat_stop)`; comparing it to that same expression is an identity that
can never fail. That is precisely the **check that cannot fail** class that
[S202](sprint-202-a-probe-that-cannot-fail-is-not-an-entry-condition.md) and
[S203](sprint-203-a-check-that-cannot-fail-says-so.md) just spent two sprints eliminating
([DRIFT-058](../laws/drift-register.md)). **Replacing a check that always fails with one that always
passes is not a fix — it is the same defect wearing the other mask.**

The correct move is to stop claiming a verdict. Render what is true and let the referee judge: the
applied stop/target, the flat and scaled counterparts, the mode that ran, and the fact that the ratio
is preserved. `StopTargetEvidence` already carries `mode`, `atr_pct`, `volatility_present`,
`applied_*`, `counterfactual_*`, `flat_*` and `scaled_*`.

### 2. Where the rule lives

Put the new renderer in `context_stop.py`, not `context_pm.py`. Two reasons, both measured:
`context_pm.py` is **152 lines**, already past the 150-line warning, and `context_stop.py` is **33**;
and `context_stop.py`'s docstring already declares the exact principle. Cohesion and the size gate
point the same way.

### 3. The clause — `DLIB-NEV-08`

`DLIB-NEV-01` … `-07` are taken; `-08` is free (IDs are append-only, conventions §2). Write the rule
you actually want, then bring **all three** sites into compliance — do not write a clause that
describes only the site you fixed. That is the S205 anti-pattern (a clause whose oracle is the thing
it describes) committed on purpose.

Suggested shape, to be refined against the law book's voice:

> **DLIB-NEV-08** — Never renders a `PASSED`/`FAILED` outcome for a comparison no agent enforces.
> Every rendered verdict in a debate context names the check that produced it and the agent that
> enforces it; evidence that is descriptive is rendered without a verdict.

🪤 **`rec` may be `None`** in `regime_gate_lines`, and `stop_pct`/`target_pct` may be `None` on an
exit intent. Degrade honestly — `stop_target_basis` already models this with
`"stop_target basis: unavailable"`. Do not emit a verdict to fill a gap.

---

## Blast radius — measured 2026-09-15

| File | Lines now | Change |
| --- | --- | --- |
| `agents/deliberator/context_pm.py` | **152** ⚠️ past the 150 warn | Shrinks — the stop renderer moves out |
| `agents/deliberator/context_stop.py` | **33** | Grows — gains the basis renderer |
| `agents/deliberator/context.py` | 133 | `regime_gate_lines` signature loses `bars` |
| `agents/deliberator/context_values.py` | 81 | Likely untouched |
| `tests/test_veto_context.py` | — | 3 assertions (`:40`, `:102`, `:142`); the test at `:93` is **rewritten**, not tweaked |
| `tests/test_veto_context_value_labels.py` | — | 1 assertion (`:63`) |
| `orchestration/tests/test_veto_stage.py` | — | 1 assertion (`:140`) |
| `agents/deliberator/laws/laws.md` | LOCKED **v1.6**, rollup **20 / 55** | → v1.7, `DLIB-NEV-08` |
| `contracts/` | — | **UNTOUCHED — verify with `git diff --stat contracts/`** |

**Deploy shape: image-only retag.** *[measured]* No `contracts/` change, no new graph label or
property, no new env key, no new tunable — so the vocabulary pack does **not** move and a full `up`
is not required. 🪤 If you find yourself needing a pack change, the scope has drifted: stop and report.

---

## Steps, in order

1. Create the branch and a worktree. **Do not work on `main`.**
2. Do the MUST RULE reading. Fill the **Law reading record** before any edit.
3. **Write the failing test first** — the property test (T1 below). It must fail on `main`, naming
   `stop_vs_regime_volatility`. **Paste that red output into the Closeout.** A sprint that cannot
   show the red run has not proven the defect existed.
4. Add `DLIB-NEV-08` to `laws.md` (v1.7 + Changelog), add the `test-plan.md` row.
5. Move and rewrite the stop renderer into `context_stop.py`; remove the verdict for the unenforced
   comparison.
6. Name the enforcer on the confidence-floor line.
7. Drop the dead `bars` parameter through `regime_gate_lines` and its caller in `context.py`.
8. Update the five pinned assertions; rewrite the mis-cited test with the new clause ID.
9. Add `DRIFT-062` recording that S175 fixed this defect's sibling **without a clause**, which is why
   the class survived — and that a test cited `DLIB-NEV-06` for a rule that clause does not contain.
10. `make ci` to a **file**, read the file. 🪤 Never `make ci | tail` — that reports `tail`'s exit code.
11. Rebuild the `sched-2026-09-14` prompt and diff it against the recorded one (T5).
12. Fill the handback sections at the bottom of this file.

---

## Test plan

| # | Test | Asserts | Clause |
| --- | --- | --- | --- |
| T1 | `test_no_rendered_verdict_lacks_an_enforcing_check` | **Property test over the whole rendered context**: every `-> PASSED`/`FAILED` token's check name is either a `gate_report` entry or a declared, attributed check. **Must fail on `main`** | `DLIB-NEV-08` |
| T2 | `test_scaled_mode_renders_no_failed_for_a_preserved_ratio` | With `mode=scaled`, `scaled_stop < flat_stop` and `reward_risk` preserved, the rendered stop basis contains **no** `FAILED`. This is the fixture the old test never had | `DLIB-NEV-08` |
| T3 | `test_stop_basis_degrades_without_evidence` | `rec=None`, and `stop_pct`/`target_pct=None`, render as unavailable — **no verdict invented to fill the gap** | `DLIB-NEV-08` |
| T4 | `test_confidence_floor_names_its_enforcer` | The confidence-floor line names the analyst as enforcer, and keeps its (real) verdict | `DLIB-NEV-08` |
| T5 | Prompt rebuild (manual, free) | `scripts/deliberation_reproducibility.py` rebuilds the `sched-2026-09-14` defender prompt; the rebuilt text contains **no** `stop_vs_regime_volatility gate:`. Paste the before/after fragment | — |
| T6 | Replay measurement (paid, **capped under $1**) | Replay **WFC only** — one order, five calls — with the corrected context, and **report whether the verdict changes**. *[measured 2026-09-15 from the ledger: WFC's five calls were 27,939 in / 5,568 out = **$0.84** at opus-5 list, or **~$0.42** through `scripts/deliberation_replay_batch.py`. The full two-order replay would be $1.73; one order is enough for a clean A/B and is the scoped spend.]* 🪤 **Do not replay both orders, and do not swap in a cheaper model** — a different model invalidates the comparison. If the spend is refused, say so and fall back to T6-free below | — |

🚨 **T6 is a measurement, not a success condition.** See Success factors.

**T6-free — the zero-cost fallback.** The next scheduled run after the retag answers the same question for **no marginal spend**, because that run happens anyway. 🪤 **It is a weaker instrument and the spec says so plainly:** it runs on different tickers in a different regime, so a changed verdict cannot be attributed to this fix. Prefer the $0.84 A/B; use this if the spend is refused, and report which one you ran.

💰 **Project LLM spend to date, for calibration:** *[measured 2026-09-15 from the `LLMCall` ledger]* **$34.20** lifetime at opus-5 list — $0.19 in July, $26.42 in August (the experimentation month), **$7.59** so far in September. A nightly deliberation that reaches a real debate costs about **$1.73**. Keep this sprint's measurement under a dollar.

---

## Success factors

1. T1 **fails on `main`** (red output pasted) and passes after.
2. T2, T3, T4 pass.
3. `git diff --stat contracts/` is **empty**.
4. `make ci` **all 12 steps** green, exit code read **from a file**, 100.00 % coverage.
5. `agents/deliberator/laws/laws.md` at **v1.7** with `DLIB-NEV-08`, a `test-plan.md` row, the clause
   ID cited in T1–T4 docstrings, and the rollup updated in **both** `ledger.md` and
   `docs/laws/INDEX.md` — **the number the gate computed**, not one you chose.
6. `DRIFT-062` filed.
7. Every module touched **< 200 lines**, and `context_pm.py` **below 150** after the move.
8. T5's rebuilt prompt shows the line gone.
9. `make gate-ran` exits 0 **from the worktree whose HEAD is the commit being proven**.

🚨 **What is deliberately NOT a success factor: that the referee stops vetoing.** This sprint's claim
is that the context tells the truth, and that claim is proven by T1–T5 alone. Whether removing a
false ground changes a verdict is **unknown** — the 2026-09-14 narratives cite two to three further
grounds per order, and those are untouched here. **Report T6's result either way, plainly.** If the
referee still vetoes both orders, this sprint still succeeded and the queue gains a better-posed
question. 🪤 **Do not tune anything to make the verdict change.** That would be fitting the instrument
to the answer.

---

## Traps

1. 🪤 **The mode-aware "fix" is a check that cannot fail.** See design decision 1. This is the single
   most likely way to turn this sprint into new debt.
2. 🪤 **`agents/deliberator/laws/laws.md` is being edited right now by
   [S205](sprint-205-a-type-clause-names-the-fields-it-requires.md)** (`DLIB-TYP-01` is in its clause
   table, and `ledger.md` already anticipates its rewrite). **Branch S206 from a `main` that has S205
   merged**, or you will collide on the law book and race two version bumps. If S205 has not merged,
   say so and wait — do not fork the law file.
3. 🪤 **`atr_pct` IS a real PM gate name.** Do not confuse it with the ATR *fragment* S175 removed
   from the rendered line. Removing the real gate's rendering would be a regression.
4. 🪤 **Changing the renderer changes `prompt_hash`.** `scripts/deliberation_reproducibility.py` will
   report mismatches for pre-fix runs. That is correct and expected. **Do not "repair" it** by
   re-blessing historical hashes — the old prompts genuinely said something else.
5. 🪤 **Five assertions pin the current text.** Updating them is the work, not collateral damage. The
   one at `tests/test_veto_context.py:93` must be **rewritten** — its name and its `DLIB-NEV-06`
   citation are both wrong.
6. 🪤 **`context_pm.py` is at 152 lines.** Adding before moving walks it toward the 200 hard block.
7. 🪤 **A worktree has no `.env`**, so T5 and T6 cannot run there. State which tree you ran them in.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `context_pm.py` **152**, `context.py` **133**, `context_values.py` **81**,
  `context_market.py` **64**, `context_stop.py` **33**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. 🪤 A **mode selector** is *not* a
  tunable — check the agent's PARAM table before registering. **This sprint should need neither.**
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 12 steps** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it.
- Secrets never through the worktree — a worktree has **no `.env`**.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving** — it resolves the SHA
   from the working directory and ignores a `SHA=` argument. **Check the printed SHA against
   `git rev-parse HEAD`.**
2. Merge to `main` locally and push. 🪤 Check you are not on the branch already.
3. **Post-merge CodeQL.** `codeql.yml` runs **only on `main`**. Check after merging.
4. **Deploy: image-only retag** — no pack move. Then the **next scheduled run is the real test**, and
   it is the one that produces T6's live counterpart.
5. Re-measure work-queue item **59** and un-gate item **6b**.

---

## Handover — paste this to Codex

```text
Branch: sprint-206-a-rendered-verdict-names-the-check-that-produced-it, from main at ebe827d or
later. The S205 collision is GONE - S205 merged af75079 on 2026-09-15 and its law-book edits are in
main already, so branch from main and there is nothing to wait for.

RE-VERIFIED ON main @ ebe827d, 2026-09-15, after S205 merged - every file:line below still resolves
to what this spec says it does (the S186 hazard, checked not assumed): context_pm.py is 152 lines,
context_stop.py 33, deliberator laws are LOCKED v1.6 and DLIB-NEV-07 is the highest clause, so
DLIB-NEV-08 is free.

THE DEFECT, measured 2026-09-15. agents/deliberator/context_pm.py:123 renders
"stop_vs_regime_volatility gate: ... -> PASSED/FAILED" into the debate context. No agent performs
that comparison: the PM emits exactly nine gate names (atr_pct, cash_available,
correlated_cluster_pct, max_names_per_sector, max_positions, max_sector_pct, min_order_quantity,
reward_risk, sizing) and "stop_vs" appears nowhere in agents/portfolio_manager/. Worse, under
ANALYST_STOP_TARGET_MODE=scaled the target leg CANNOT pass: stop_target.py:86 defines
scaled_target = flat_target * (scaled_stop / flat_stop), so a tightened stop necessarily produces a
target below the regime base. On sched-2026-09-14 both approved orders rendered FAILED, both were
vetoed, and the run submitted 0 - while both carried reward_risk 2.0, which is the real gate, passed.

MUST RULE: read agents/deliberator/laws/laws.md AND test-plan.md AND docs/laws/conventions.md AND
docs/laws/drift-register.md before you open an editor. Fill the Law reading record FIRST.

LAW CYCLE: YES, one new clause. contracts/ must NOT change (StopTargetEvidence already exists on
Recommendation). Add DLIB-NEV-08 ("never render a PASSED/FAILED for a comparison no agent enforces;
every rendered verdict names its check and its enforcing agent"), bump laws.md v1.6 -> v1.7 with a
Changelog line, add a test-plan.md row, cite the clause ID in every test docstring, and let make ci
compute the rollup for ledger.md and docs/laws/INDEX.md. Do not pick the rollup number yourself.

ORDER OF WORK: failing test FIRST. Write the property test that every "-> PASSED/FAILED" in a
rendered context maps to a real enforcing check. It MUST fail on main naming
stop_vs_regime_volatility. PASTE THAT RED OUTPUT into the Closeout. Then fix.

THE FIX: stop rendering a verdict for the unenforced comparison. Render the basis instead - mode,
applied vs flat vs scaled, and the preserved ratio - all of which StopTargetEvidence already carries.
Put it in context_stop.py (33 lines, and its docstring already says "without inventing a gate"), NOT
in context_pm.py (152 lines, already past the 150 warning). Also: name the analyst as the enforcer on
the confidence_floor line (it IS real - agents/analyst/domain/recommend.py:87 - it just does not say
so), and drop the dead `bars` parameter threaded into the stop renderer.

DO NOT make the comparison mode-aware so that it passes. Comparing scaled_target against a scaled
baseline is an identity that can never fail - that is the exact "check that cannot fail" defect S202
and S203 just removed (DRIFT-058). Replacing an always-fails check with an always-passes one is the
same defect wearing the other mask.

DO NOT add a real stop-vs-volatility gate (policy decision, not this sprint). DO NOT touch the
referee's other grounds (non-vol-adjusted sizing, correlated_cluster_pct omitting co-held names). DO
NOT change deliberation_posture. DO NOT change contracts/ - verify with git diff --stat contracts/.
DO NOT re-bless prompt_hash history: this change legitimately alters the prompt, and
deliberation_reproducibility.py reporting mismatches for pre-fix runs is correct.

TRAPS: atr_pct IS a real PM gate - do not remove its rendering while removing the invented one. Five
existing assertions pin the current text (tests/test_veto_context.py:40,:102,:142,
tests/test_veto_context_value_labels.py:63, orchestration/tests/test_veto_stage.py:140); the test at
tests/test_veto_context.py:93 must be REWRITTEN - it is named for ATR, it cites DLIB-NEV-06 for a
rule that clause does not contain, and it currently asserts the invented line IS present. Its fixture
uses flat mode, where the two values are equal, which is why the suite never saw this.

SUCCESS IS NOT "the referee stops vetoing". It is: the context tells the truth. Report the replay
result either way, and if it still vetoes, say so plainly and do not tune anything to change it.

COST IS CAPPED UNDER $1. Replay WFC ONLY - one order, five calls, measured at $0.84 at opus-5 list
(27,939 in / 5,568 out), or ~$0.42 through scripts/deliberation_replay_batch.py. Do NOT replay both
orders ($1.73) and do NOT substitute a cheaper model - a different model invalidates the comparison.
Project lifetime LLM spend is $34.20, so this is a real constraint, not a formality. If the spend is
refused, fall back to the free option: let the next scheduled run answer it, and say that is what you
did, noting it runs on different inputs so a changed verdict cannot be attributed to this fix.

make ci all 12 steps, redirected to a FILE (never | tail - that reports tail's exit code), 100.00%
coverage. Then make gate-ran from the worktree whose HEAD is the commit you are proving.

HANDBACK: fill Law reading record, Test plan results, Closeout - evidence (real pasted output,
including the RED run), Return notes, and set Status: BUILT. A placeholder left intact means the
handback is returned, not repaired.
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
| `agents/deliberator/context_pm.py` | `agents/deliberator/laws/laws.md`; `agents/deliberator/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | `DLIB-IDN-01`, `DLIB-OUT-04`, `DLIB-NEV-01`, `DLIB-NEV-02`, `DLIB-NEV-06`, `DLIB-NEV-07`; new `DLIB-NEV-08` owed | Yes. Existing green clauses guard failed debate evidence, not invented rendered gate verdicts, so the confidence verdict must name its real analyst enforcer and the stop/regime verdict must stop being a verdict. |
| `agents/deliberator/context_stop.py` | `agents/deliberator/laws/laws.md`; `agents/deliberator/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | `DLIB-IDN-01`, `DLIB-OUT-04`, `DLIB-NEV-01`, `DLIB-NEV-02`; new `DLIB-NEV-08` owed | Yes. The stop-target evidence renderer is the cohesive home for descriptive stop/target basis text because it already promises not to invent a gate. |
| `agents/deliberator/context.py` | `agents/deliberator/laws/laws.md`; `agents/deliberator/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | `DLIB-IDN-01`, `DLIB-OUT-04`, `DLIB-NEV-01`, `DLIB-NEV-02`; new `DLIB-NEV-08` owed | No contradiction. Signature cleanup is allowed only because it removes dead context plumbing and does not alter approved orders. |
| `agents/deliberator/laws/laws.md` and `agents/deliberator/laws/test-plan.md` | Same deliberator law book/test plan plus `docs/laws/conventions.md` §§2-4, 7, 7a, 9 | `DLIB-NEV-08`; conventions append-only IDs, gray-to-green, lock/amendment, clause-summary fidelity, drift-register rules | Yes. This is a deliberate law cycle: append `DLIB-NEV-08`, bump v1.6 to v1.7, add the test-plan row, and cite the clause in T1-T4 docstrings. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *(the spec says
No to `contracts/` and Yes to one new clause — confirm after reading, and say if you disagree)*

Confirmed. This sprint must not change `contracts/`; `StopTargetEvidence` already supplies the values needed for the renderer. It does add one deliberator guarantee: rendered `PASSED`/`FAILED` outcomes must correspond to checks some agent enforces and must name the enforcing agent/check.

**Contradictions found between a law and this spec:**

None found. The existing deliberator law is silent on this exact rendered-verdict truthfulness rule, but no clause contradicts the sprint.

**Laws found silent where a decision was needed:**

`DLIB-NEV-*` currently forbids order origination/resizing, broker/feed access, cross-agent imports, hidden failed peer calls, and empty transcript evidence, but no clause forbids rendering a `PASSED`/`FAILED` outcome for a comparison no agent performs. This silence is the finding recorded as `DRIFT-062` in this sprint.

**Clauses that were ⬜ and are now proven:** *(IDs, and the rollup the gate computed)*

`DLIB-NEV-08` was added and proven green. The gate-derived deliberator rollup is
`20 / 55` -> `21 / 56` in both `docs/laws/ledger.md` and `docs/laws/INDEX.md`.

**Clauses that were 🟩 and are now ⬜:** *(IDs, and why the old test does not prove the new clause)*

None. The old `DLIB-NEV-06` coverage remains about failed debate/peer-call evidence; the
mis-cited test was rewritten under `DLIB-NEV-08` rather than used to demote that clause.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| T1 | `test_no_rendered_verdict_lacks_an_enforcing_check` | `tests/test_veto_context_verdict_attribution.py` | PASS; watched fail first on the old renderer | `DLIB-NEV-08` |
| T2 | `test_scaled_mode_renders_no_failed_for_a_preserved_ratio` | `tests/test_veto_context_verdict_attribution.py` | PASS | `DLIB-NEV-08` |
| T3 | `test_stop_basis_degrades_without_evidence` | `tests/test_veto_context_verdict_attribution.py` | PASS | `DLIB-NEV-08` |
| T4 | `test_confidence_floor_names_its_enforcer` | `tests/test_veto_context_verdict_attribution.py` | PASS | `DLIB-NEV-08` |
| T5 | `sched-2026-09-14` prompt rebuild | `scripts/deliberation_reproducibility.py` | PASS; rebuilt prompt has no `stop_vs_regime_volatility gate:` | -- |
| T6 | WFC-only replay measurement | in-memory replay using the deliberation modules | measured; WFC changed `revise` -> `uphold` | -- |

**Tests added beyond the plan:**

`tests/test_veto_context_verdict_attribution.py::test_stop_basis_renders_zero_stop_ratio_as_unavailable`
covers the zero-stop reward-risk fallback so `context_stop.py` remains at 100.00 % coverage.

---

## Closeout — evidence

**Status:** SHIPPED — local CI, remote branch CI, Security Findings and branch `make gate-ran` were
proven for the implementation commit. Main merge, post-merge CodeQL, fleet retag and the next
scheduled live counterpart are not done.

**Tree the proofs ran in (and `.env` present?):**

`C:/Users/yury_/Downloads/project/wt-s206`, branch
`sprint-206-a-rendered-verdict-names-the-check-that-produced-it`; `.env` present in that worktree:
`False`. T5/T6 used the main checkout's `.env` at call time for graph/API access, without copying
credentials into the worktree and without persisting full prompts or completions.

**Result:** *(what is now true, in the artefact's own words — not the intent restated)*

The debate context no longer renders `stop_vs_regime_volatility gate:` or any `PASSED`/`FAILED`
verdict for stop/regime comparisons. Stop/regime data now renders as
`stop_target_regime basis:` with `mode`, applied/flat/scaled stop-target values and reward-risk
ratios. The confidence-floor verdict remains, but now names `enforced_by=analyst`; PM gate outcomes
are unchanged.

**Files changed:**

`agents/deliberator/context.py`; `agents/deliberator/context_pm.py`;
`agents/deliberator/context_stop.py`; `agents/deliberator/laws/laws.md`;
`agents/deliberator/laws/test-plan.md`; `docs/STATE.md`; `docs/laws/INDEX.md`;
`docs/laws/drift-register.md`; `docs/laws/ledger.md`;
`docs/sprints/sprint-206-a-rendered-verdict-names-the-check-that-produced-it.md`;
`orchestration/tests/test_veto_stage.py`; `pyproject.toml`; `tests/test_veto_context.py`;
`tests/test_veto_context_value_labels.py`; `tests/test_veto_context_verdict_attribution.py`;
`uv.lock`.

**Design decisions:** recorded as `DL-NNN`

No new `DL-*` entry was opened. The implementation follows [DL-167](../design-log.md) and files
[DRIFT-062](../laws/drift-register.md) for the missing rendered-verdict law after S175.

**Proof — the RED run first (T1 failing on `main`, naming the invented gate):**

```text
uv run pytest tests/test_veto_context.py::test_no_rendered_verdict_lacks_an_enforcing_check --no-cov -vv
FAILED tests/test_veto_context.py::test_no_rendered_verdict_lacks_an_enforcing_check
E   AssertionError: assert [
E     'missing enforcing agent analyst: confidence_floor: confidence_floor gate: confidence_score=0.620 vs base_min_confidence_score=0.570 -> PASSED',
E     'no enforcing check declared: stop_vs_regime_volatility: stop_vs_regime_volatility gate: stop_pct=3.00% vs base_stop_loss_pct=3.00% -> PASSED; target_pct=8.00% vs base_take_profit_pct=8.00% -> PASSED',
E   ] == []
```

**Proof — the green run:**

```text
uv run pytest tests/test_veto_context.py tests/test_veto_context_verdict_attribution.py tests/test_veto_context_value_labels.py orchestration/tests/test_veto_stage.py --no-cov
collected 20 items
tests\test_veto_context.py ......                                        [ 30%]
tests\test_veto_context_verdict_attribution.py .....                     [ 55%]
tests\test_veto_context_value_labels.py .                                [ 60%]
orchestration\tests\test_veto_stage.py ........                          [100%]
============================= 20 passed in 1.61s ==============================

uv run ruff check agents/deliberator/context_pm.py agents/deliberator/context_stop.py agents/deliberator/context.py tests/test_veto_context.py tests/test_veto_context_verdict_attribution.py tests/test_veto_context_value_labels.py orchestration/tests/test_veto_stage.py
All checks passed!

uv run mypy agents/deliberator/context_pm.py agents/deliberator/context_stop.py agents/deliberator/context.py tests/test_veto_context_verdict_attribution.py --no-incremental
Success: no issues found in 4 source files

uv run python scripts/check_law_coverage.py
<exit 0>
```

**Proof — T5, the rebuilt `sched-2026-09-14` prompt, before and after:**

```text
[WFC before]
confidence_floor gate: confidence_score=0.675 vs base_min_confidence_score=0.600 -> PASSED
stop_vs_regime_volatility gate: stop_pct=4.14% vs base_stop_loss_pct=5.00% -> PASSED; target_pct=8.29% vs base_take_profit_pct=10.00% -> FAILED

[WFC after]
confidence_floor gate: enforced_by=analyst; confidence_score=0.675 vs base_min_confidence_score=0.600 -> PASSED
stop_target_regime basis: mode=scaled; applied_stop_pct=4.14%; applied_target_pct=8.29%; flat_stop_pct=5.00%; flat_target_pct=10.00%; scaled_stop_pct=4.14%; scaled_target_pct=8.29%; counterfactual_mode=flat; applied_reward_risk_ratio=2.00; flat_reward_risk_ratio=2.00; scaled_reward_risk_ratio=2.00

[MDLZ before]
confidence_floor gate: confidence_score=0.650 vs base_min_confidence_score=0.600 -> PASSED
stop_vs_regime_volatility gate: stop_pct=3.83% vs base_stop_loss_pct=5.00% -> PASSED; target_pct=7.66% vs base_take_profit_pct=10.00% -> FAILED

[MDLZ after]
confidence_floor gate: enforced_by=analyst; confidence_score=0.650 vs base_min_confidence_score=0.600 -> PASSED
stop_target_regime basis: mode=scaled; applied_stop_pct=3.83%; applied_target_pct=7.66%; flat_stop_pct=5.00%; flat_target_pct=10.00%; scaled_stop_pct=3.83%; scaled_target_pct=7.66%; counterfactual_mode=flat; applied_reward_risk_ratio=2.00; flat_reward_risk_ratio=2.00; scaled_reward_risk_ratio=2.00

scripts/deliberation_reproducibility.py:
before matched 2 / 2 prompt turns, reproducible_pct 100.00
after mismatched 2 / 2 prompt turns, reproducible_pct 0.00
```

**T6 — replay result, and whether the verdicts changed:** *(either answer is a pass; state it plainly)*

```text
corpus=pm_runs=1; unreadable_runs=0; subjects=2; selected=1 WFC
planning ('defender', 1): 1 request(s)
planning ('challenger', 1): 1 request(s)
planning ('defender', 2): 1 request(s)
planning ('challenger', 2): 1 request(s)
planning ('judge', 0): 1 request(s)
requests=5; completed=1; failed=0
WFC original=revise; replay=uphold; changed=True; failure=None
tokens_in=28675; tokens_out=6764; cache_read=2556; cache_write=5025
```

**`git diff --stat contracts/`:** *(must be empty)*

Empty output.

**Rollups, as computed by the gate:** *(before → after, in `ledger.md` and `docs/laws/INDEX.md`)*

Deliberator: `20 / 55` -> `21 / 56` in both `docs/laws/ledger.md` and `docs/laws/INDEX.md`;
`uv run python scripts/check_law_coverage.py` exits 0.

**Module line counts:** *(`context_pm.py` must be below 150)*

```text
129 agents\deliberator\context_pm.py
83 agents\deliberator\context_stop.py
133 agents\deliberator\context.py
158 tests\test_veto_context.py
165 tests\test_veto_context_verdict_attribution.py
64 tests\test_veto_context_value_labels.py
191 orchestration\tests\test_veto_stage.py
```

**`make ci`:** redirected to `C:\Users\yury_\Downloads\project\s206-make-ci.txt`. Exit code `0`.
`2758 passed, 6 skipped`, coverage `100.00 %`.

```text
TOTAL                                                     16475      0   3504      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
================= 2758 passed, 6 skipped in 83.57s (0:01:23) ==================
uv run pip-audit
No known vulnerabilities found
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 1 new file(s)
```

**`make gate-ran`:** run from *(worktree path)* at *(full 40-char SHA)*:

```text
HEAD=2807b446ca7789b0117c9548a88eb53f61e00aaa
uv run python scripts/assert_gate_ran.py
GATE PROVEN for 2807b446ca7789b0117c9548a88eb53f61e00aaa:
  CI: success (attempt 1)
  Security Findings: success (attempt 1)
```

**Handback verification — re-measured on merge, 2026-09-15 (planning):**

🚨 **The handback's `make gate-ran` proves `2807b44`, which is the implementation commit, not the
branch tip** — `5a192a9` (the docs handback commit) sits above it. That is exactly the S186 hazard, so it
was re-run rather than accepted:

```text
$ cd C:/Users/yury_/Downloads/project/wt-s206 && make gate-ran
GATE PROVEN for 5a192a960b366ccbab25c31d518dd934acf4d17c:
  CI: success (attempt 1)
  Security Findings: success (attempt 1)
$ git rev-parse HEAD
5a192a960b366ccbab25c31d518dd934acf4d17c
```

🟩 **T1's red run reproduced independently**, not read from the paste — the new test file copied into a
throwaway worktree detached at the branch base `823e5cf`, where the fix does not exist:

```text
$ uv run pytest tests/t1_red_check.py::test_no_rendered_verdict_lacks_an_enforcing_check --no-cov -q
E   AssertionError: assert ['missing enf...0% -> PASSED'] == []
E     Left contains 2 more items, first extra item: 'missing enforcing agent analyst: confidence_floor: ...'
1 failed in 3.46s
```

🟩 **Re-measured, each independently:** `git diff --stat contracts/` **empty**; `context_pm.py` **129**,
`context_stop.py` **83**, `context.py` **133** — all under the warn line; `kernel/` and `.github/` untouched and
the secrets baseline unedited; the bump is `0.98.03 → 0.98.04`, **PATCH**, correct because no agent gains a
capability; laws `v1.6 → v1.7` with `DLIB-NEV-08`, a test-plan row citing five tests, and **21 / 56** in both
`ledger.md` and `docs/laws/INDEX.md`; all five pinned assertions updated and the mis-cited
`test_regime_context_does_not_invent_an_atr_gate_outcome` deleted rather than patched.

🎯 **T1 is a real oracle, not the S205 anti-pattern** — it scans every `-> PASSED`/`-> FAILED` in the whole
rendered context, extracts the check name, and requires it to be a `gate_report` entry or an explicitly
declared context check carrying `enforced_by=`. A new fabricated verdict cannot pass without someone adding
it to the allowlist by hand.

🟠 **One residue, named rather than left implicit:** the happy-path `stop_target_regime basis:` line never
prints `base_stop_loss_pct` / `base_take_profit_pct`, so the label says *regime* while the regime bases appear
only under their derivation names (`flat_*`, which equal them). No information is lost; the naming is looser
than the line's own label.

🟩 **MERGED `8c6f74afb76d4d323f262521c7907d0e92d31c80`**, 2026-09-15. The merge commit differs from the
gate-proven tip only by S207's three docs files (`git diff 5a192a9..8c6f74a --stat`: `docs/sprints/INDEX.md`,
`docs/sprints/sprint-207-*.md`, `docs/work-queue.md`) — **no code**. One `INDEX.md` row conflict, resolved by
keeping both sprint rows. **Post-merge `main` gate, all six workflows:**

```text
GATE PROVEN for 8c6f74afb76d4d323f262521c7907d0e92d31c80:
  Build and push agent images: success (attempt 1)
  CI: success (attempt 1)
  CodeQL: success (attempt 1)
  Security Findings: success (attempt 1)
```

🟠 **Not deployed.** Deploy shape is the image-only retag the spec names; until it runs the fleet still
renders the invented verdict, so no live run has yet read the corrected context.

**Not met / verified failing:**

Main merge, post-merge CodeQL, image-only retag, and the next scheduled live counterpart are not
done in this BUILT handback. No `contracts/` edit was made. No live fleet state was changed.

---

## Return notes

- Scope held. The only functional behavior changed is the rendered deliberation context: no PM order
  creation/sizing path moved, no `contracts/` file changed, and no new PM gate was added.
- I disagreed with none of the sprint after reading the laws. The useful finding was law silence:
  the existing green clauses did not forbid an invented rendered verdict, so `DLIB-NEV-08` now does.
- The WFC replay changed from `revise` to `uphold`, but that is measurement, not the success
  condition. The safer next question is to re-measure work-queue item 59 and then revisit item 6b
  after the branch is merged/deployed and a scheduled run has produced the live counterpart.
