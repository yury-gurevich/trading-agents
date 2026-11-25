<!-- Agent: planning | Role: sprint handover -->
# Sprint 291 — the judge rules on what distinguishes this order, and a figure nothing enforces is not shown as a passed gate

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-291-the-judge-rules-on-what-distinguishes-the-order`
**Status:** BUILT
**Version:** *next available PATCH at merge* (the prototype measured `0.131.08`)
**Effort:** M
**Decisions:** [DL-326](../design-log.md) (this sprint's decisions, made and measured) · [DL-280](../design-log.md) (the finding) · [ADR-0010](../decisions/0010-llm-interaction-quality-gate.md) (a prompt change passes the golden set) · [ADR-0027](../decisions/0027-reward-risk-compares-measured-upside-against-measured-downside.md) Correction 2 (the ratio is disclosed, not enforced) · [ADR-0029](../decisions/0029-a-revise-is-a-finding-an-overturn-is-a-block.md) (`revise` blocks nothing) · DRIFT-118 (this sprint corrects it)

> **Why this bump kind.** No new capability: `DLIB-NEV-08` already forbids a `PASSED` for a comparison no
> agent enforces, and the debate already exists to tell one order from another. The packet breaks the
> first and the judge's prompt prevents the second. A fix, so a PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/deliberator/laws/laws.md` | The deliberator's **locked constitution** | **LOCKED.** This sprint's one amendment is in Appendix B and is applied by its script, never typed |
| `agents/deliberator/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn what is proven |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. Appendix B adds DRIFT-118 and the two rollup rows |

Binding sections here: **`DLIB-NEV-08`**, **`DLIB-NEV-09`**, **`DLIB-OUT-04`**, **`DLIB-OBS-07`**, and the new **`DLIB-OUT-09`**.

### The rule

1. **Before writing code**, read every law file in the map below, whole.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Read the law-cycle answer below.**
5. **Write the Law reading record** (at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, record it and say so in the Return notes.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**Yes, one guarantee; no contract.** `DLIB-OUT-09` is new: the judge's champion prompt tells it to rule on
what distinguishes this order, and its examples demonstrate each ruling. Appendix B makes the whole cycle:
the clause, laws **v1.19** with its Changelog line, the test-plan row, the citation added to `DLIB-NEV-08`'s
row, both rollups (**35 / 66 → 36 / 67**) and DRIFT-118. You write the tests the rows cite, under exactly
the names in the Test plan, because `make ci`'s law step resolves those names.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/deliberator/context_pm.py` | `agents/deliberator/laws/laws.md` + `test-plan.md` | `DLIB-NEV-08` no verdict for an unenforced comparison; `DLIB-NEV-09` a stated code fact is pinned |
| `kernel/deliberation_judge_prompt.py`, `kernel/deliberation_prompts.py`, `scripts/deliberation_prompt_sources.py`, `scripts/compile_deliberation_prompts.py`, `scripts/deliberation_judge_prompt.json` | same, plus ADR-0010 | `DLIB-OUT-09`; `DLIB-NEV-09`; the champion is compile output, never a hand edit |
| `agents/deliberator/prompt_recipe.py` | same | `DLIB-OBS-07`: the digest covers every module that shapes a prompt |

⚠️ **The one invariant: this sprint changes what the judge reads and how it is told to rule, and nothing that
acts on a ruling.** `uphold` and `revise` leave the order set unchanged and `overturn` subtracts
(`DLIB-OUT-04`). If your change touches `agents/execution/`, `agents/deliberator/review_batch.py` or
`contracts/`, stop and report.

---

## Goal

At merge, the evidence packet prints a disclosure-only reward-to-risk ratio as a figure with no threshold and
no verdict, and states once why it is not enforced. The judge's champion prompt tells it to rule on what
distinguishes this order, says a design property true of every order cannot decide the ruling, and shows each
of `uphold`, `revise` and `overturn`. The prompt stays compile output and is rebuilt byte for byte.

## Why (context)

The judge has ruled `revise` on every order since 2026-09-18, and `revise` changes no order
([ADR-0029](../decisions/0029-a-revise-is-a-finding-an-overturn-is-a-block.md)). The debate therefore costs
about $0.69 an order and cannot tell one order from another. Three causes add
([DL-280](../design-log.md)): the packet prints a ratio nothing enforces as a gate that passed, which
`DLIB-NEV-08` forbids; the judge is told not to uphold once any implementation flaw is named, and this one is
on every order; and all six of its examples rule `revise`.

### Measured, 2026-11-22 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Rulings since the code stopped treating `revise` as a block (`e6b26b90`, 2026-09-18) | **65 of 65 `revise`**, 29 nights, 0 orders blocked | *[measured 2026-11-22]* every `DeliberationRun` created from 2026-09-18 on the live graph, read-only |
| Debates that store their packet and turns | **43** (2026-10-01 to 2026-11-20), all `revise`; **43 of 43** rationales name reward-to-risk | *[measured 2026-11-22]* live graph; kit `stored_debates.json` |
| The prototype's renderer against those packets | **43 of 43** equal the stored packet with only the sprint's two line changes | *[measured 2026-11-22, $0]* `build_veto_context` on the live graph from the prototype; kit `f1_render.py` |
| Judge wording on the 7 development orders (judge only) | First wording **7 `uphold`**; second **5 `revise`, 2 `uphold`**, two rationales leaning on the ratio; third **3 `revise`, 4 `uphold`**, each `revise` on evidence about that name | *[measured 2026-11-22, $2.05]* the two wording changes the pre-registration allowed, then frozen |
| Held-out test, full debates on `gpt-5.5` at effort `high` | **3 `revise`, 2 `uphold`, 0 `overturn`** on 5 of 6 orders; 0 of the 3 `revise` rest on the ratio; **PASS** on all five bars (Appendix A) | *[measured 2026-11-22, $4.29]* one run; the money cap stopped the sixth debate, and the bar allowed five |
| The golden firewall (ADR-0010), four Class-1 cases on `gpt-5.5` | **4 of 4** caught and not upheld | *[measured 2026-11-22, $0.20]* |
| Total paid | **$6.54** of the operator's approved $8 (62 calls) | *[measured 2026-11-22]* vendor-reported tokens at list price, kit `spend.jsonl` |
| Prototype | `make ci` exit 0: **5,350 passed**, 8 skipped, **100.00 %**, audit clean; **15 of 15** breaks red | *[measured 2026-11-22]* `../ta-s291-proto`, local branch `proto-s291`, never pushed |
| Whether the new rulings are **right** | *not measured* | No outcome labels: the proof shows the rulings now differ by order and rest on that order's evidence, on 5 debates, run once |
| The new prompt on the fallback vendor, `claude-opus-5` | *not measured* | The paid run stayed on the fleet's primary, `gpt-5.5`. ADR-0010 decision 4 asks for it before a fallback may serve this prompt; owed to the planner before deploy |

---

## Scope — and what is deliberately NOT here

1. **The two test files first** (Test plan), seen red.
2. **Appendix B's script**, run once: the packet line, the judge's contract and five contrast examples, the
   compiled artifact, the promoted constant in a module of its own, the recipe entry, three existing tests
   that state the old text, the law cycle, and the version lines.
3. **The fifteen breaks of Appendix C**, each seen red on its named test.
4. **`make ci`**, and the handback sections.

### Out of scope (do NOT build this sprint)

- **`revise` taking any effect.** It stays a recorded finding; its effect is [DL-264](../design-log.md)'s loop, in shadow first.
- **The stop-out fact in the packet** (DL-240 amendment 2). DL-280 proposed it here; it needs a new read of past fills, which is work-queue 98. Decided in DL-326.
- **The debaters' prompts.** The challenger still argues as it did; work-queue 75 owns its steers.
- **Any change to the reward-to-risk gate.** The Portfolio Manager is a fidelity decision path, and ADR-0027 stands.
- **No ADR reversal.** ADR-0027 and ADR-0029 stand as written.

### The road not taken (LAW-06)

- **Raise the floor so the gate can fail.** Rejected: ADR-0027 Correction 2 measured that the ratio does not predict returns.
- **Remove the ratio from the packet.** Rejected: the debaters would lose the stop and target geometry.
- **Drop `revise` from the judge's choices.** Rejected: it could push every ruling to `overturn`, which blocks a buy.
- **The packet line alone.** Rejected: DL-280 found rationales also lean on other properties shared by every order.
- **The judge's first wording** (uphold when no flaw is grounded). Rejected on the development set: 7 of 7 `uphold`, because passing the gates read as enough.
- **Ten full debates, as DL-280 proposed.** Rejected: at the measured $0.69 median and $1.08 at the 90th percentile they could pass the approved $8.

---

## The design decisions — made, and recorded in DL-326

1. **The ratio is printed as a figure**, with its value and full detail and with no threshold or verdict.
2. **One rule line states why**, with ADR-0027's numbers, each pinned to the ADR by a test.
3. **Only the exact field `comparison=DISCLOSURE_ONLY` on a gate that passed** drops the verdict. A gate that failed or was not evaluated keeps its outcome.
4. **The judge rules on what distinguishes this order.** Passing every gate does not earn an `uphold`; a shared design property cannot decide the ruling unless this order's case relies on it.
5. **Five contrast examples, the judge's only:** two `uphold`, one `revise`, two `overturn`. The six existing examples stay.
6. **The judge's constant moves to `kernel/deliberation_judge_prompt.py`**, because the new text would take `deliberation_prompts.py` past the 200-line block.

---

## Blast radius — measured 2026-11-22

| What | Detail |
| --- | --- |
| Files changed | 17 by Appendix B (blob ids listed there) and two new test files, 19 in all |
| Agents affected | deliberator. `kernel/deliberation_prompts.py` re-exports the same name, so no importer changes |
| Contract change? | No |
| Graph vocabulary change? | No |
| New env keys / tunables | None |
| Fidelity decision path? | **No.** None of the 19 files is under `DECISION_PATHS` in `scripts/replay_fidelity_git.py`, so the count does not restart |
| Deploy implication | Image-only retag. **Not part of this sprint**; the operator's word |
| Rollback | Retag to `s290`. A retag does not undo a `DeliberationRun` already written, or a paper buy an `overturn` dropped on a night in between |

---

## Steps, in order

1. **Read the laws** and write the Law reading record.
2. **Write the two test files** of the Test plan, under exactly those names.
3. **Run them on the unchanged tree.** Expected: `2 errors` at collection, because the names they import do not exist yet. The per-test red is step 6.
4. **Apply Appendix B** and check the 17 blob ids.
5. **Run the tests again:** 16 passed, and the existing files named in the handover pass.
6. **Run Appendix C:** 15 of 15 red on their named test.
7. **Delete `scratch-s291/`, then `make ci`**, redirected to a file, never piped.
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

The names are exact: the law step and the break script read them. Build fixtures from
`tests/veto_context_fixtures.py` (`intent`, `linked_graph`, `order_set`) and
`tests/veto_context_gate_fixtures.py` (`pm_gate_report`). `_DISCLOSED` below is
`target_pct=0.0331; stop_pct=0.0800; comparison=DISCLOSURE_ONLY`; the gate is
`GateOutcome(name="reward_risk", value=0.4132, threshold=0.0, ...)`, appended to `pm_gate_report()`.

**`tests/test_reward_risk_is_a_disclosed_figure.py`**

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 `test_a_disclosed_ratio_is_not_a_passed_gate` (`DLIB-NEV-08`) | the gate, passed, `_DISCLOSED` | `order_lines` holds exactly one line naming `name=reward_risk`, equal to `PM disclosed figure, not a gate: name=reward_risk value_reward_risk_ratio=0.4132 (<_DISCLOSED>)` |
| A2 | `test_the_rule_is_stated_once_after_the_gates` (`DLIB-NEV-08`) | same | `REWARD_RISK_RULE` appears once and is the last of `order_lines` |
| A3 | 🪤 `test_an_enforced_ratio_keeps_its_verdict` (`DLIB-NEV-08`), parametrized on `comparison` = `INFORMATIVE`, `STRUCTURALLY_DETERMINED`, `DISCLOSURE_ONLY_DRAFT` | detail `target_pct=0.03; comparison=<value>` | the line starts `PM gate outcome: name=reward_risk `, holds `threshold_reward_risk_ratio=0 -> PASSED`, and the rule is absent |
| A4 | 🪤 `test_a_gate_that_did_not_pass_is_never_recast` (`DLIB-NEV-08`), parametrized (`FAILED`, `FAILED`), (`NOT_EVALUATED`, `NOT-EVALUATED`) | `_DISCLOSED` with that outcome | the line holds `-> <rendered>`, and the rule is absent |
| A5 | `test_the_whole_packet_states_the_rule_before_the_pm_run` (`DLIB-NEV-08`) | `build_veto_context` on `linked_graph(graph, full=True)` | the ratio's line has no `-> PASSED`, and the line after the rule starts `PM run:` |
| A6 | `test_the_rule_states_what_the_code_does` (`DLIB-NEV-09`) | `evaluate_recommendations` on one buy with stop 0.08, target 0.02, at `PortfolioManagerSettings().min_reward_risk_ratio` | that default is 0.0; no key of the tunables pack contains `REWARD_RISK`; nothing rejected; the approved gate's detail, split on `"; "`, holds `comparison=DISCLOSURE_ONLY` |
| A7 | `test_the_rules_evidence_is_adr_0027s` (`DLIB-NEV-09`) | reads ADR-0027 | the ADR holds `47,485 decisions`, `**+0.03 %**` and `[95 % CI −0.17 %, +0.23 %]` (U+2212, written `−` in the test); the rule holds `47,485 decisions`, `+0.03 %`, `-0.17 %`, `+0.23 %`, `0.80` |

**`tests/test_judge_rules_on_the_order.py`**

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A8 | 🎯 `test_the_judge_is_told_to_rule_on_this_order` (`DLIB-OUT-09`) | `JUDGE_SYSTEM` | holds `JUDGE_ORDER_RULE.strip()` and `cannot decide the ruling`; does not hold `do not uphold the decision` |
| A9 | `test_every_ruling_is_demonstrated` (`DLIB-OUT-09`) | the examples of `scripts/deliberation_judge_prompt.json` | their rulings count `revise` 7, `uphold` 2, `overturn` 2, and each `expected_output=<output>` is in `JUDGE_SYSTEM` |
| A10 | `test_each_contrast_case_shows_its_ruling` (`DLIB-OUT-09`) | same, by `inputs["case"]` | for `JUDGE_CONTRAST_CASES`: `shared-disclosed-figure` and `shared-sizing-rule` `uphold`, `one-pillar-clearance` `revise`, `wrong-price-input` and `stated-limit-broken` `overturn` |
| A11 | `test_the_contrast_cases_reach_only_the_judge` (`DLIB-OUT-09`), parametrized on `DEFENDER_SYSTEM`, `CHALLENGER_SYSTEM` | those prompts | neither holds any contrast case's name |
| A12 | `test_the_judge_prompt_is_in_the_recipe` (`DLIB-OBS-07`) | `agents.deliberator.prompt_recipe.PROMPT_MODULES` | holds `kernel.deliberation_judge_prompt` |

---

## Success factors

- [x] A disclosure-only ratio prints as a figure with no threshold and no verdict; any other gate keeps its line (A1, A3, A4).
- [x] The rule is printed once, after the gates, and its code facts and numbers are pinned (A2, A5, A6, A7).
- [x] The judge's champion carries the order rule and shows each ruling; the debaters' prompts carry none of its cases (A8 to A11).
- [x] The 17 files equal Appendix B's blob ids, so the champion is the compile's output byte for byte.
- [x] No file under `agents/execution/`, `contracts/`, or `agents/deliberator/review_batch.py` changed.
- [x] Law cycle done: `DLIB-OUT-09` proven, rollups 36 / 67, DRIFT-118 recorded.
- [x] 15 of 15 breaks red, stated per break.
- [x] Every touched module under 200 lines.
- [x] `make ci` exit 0, 100.00 % coverage, or each step your sandbox cannot run named "not done".

---

## Traps

🪤 **Never hand-edit the judge's text.** `kernel/deliberation_judge_prompt.py` and `scripts/deliberation_judge_prompt.json` are compile output; `test_the_champion_is_its_sources_rebuilt` compares them byte for byte.
🪤 **The first red is a collection error, by design.** It proves only that the names do not exist yet. The red that proves each test is step 6.
🪤 **A7's minus sign is U+2212 in the ADR.** Ruff's `RUF001` refuses the literal character in a string, so write `−`.
🪤 **A10 indexes a value typed `object`,** so mypy wants the line's `# type: ignore[index]`, or a typed helper. No `noqa`.
🪤 **Do not run `uv lock` in any form.** This machine's uv would rewrite a lock written by a newer one. Appendix B edits the one version line.
🪤 **A green suite alone proves little here:** three existing tests state the old text and Appendix B updates them. The breaks are the proof.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Sizes after Appendix B: `kernel/deliberation_judge_prompt.py` **124**, `kernel/deliberation_prompts.py` **93**, `agents/deliberator/context_pm.py` **156**, `scripts/compile_deliberation_prompts.py` **188**, `scripts/deliberation_prompt_sources.py` **116**, `tests/test_deliberation_prompt_facts.py` **151**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a pipe.**
- Version bump of the kind named at the top, in Appendix B, with `uv.lock`.
- Secrets never through the worktree: a worktree has **no `.env`**. **State which tree you ran in.**

---

## Sequencing after merge (the planner's)

1. The planner's own `make ci`, the branch pushed, **`make gate-ran` exits 0** from the proving worktree, its SHA checked against `git rev-parse HEAD`.
2. The planner re-measures: the 17 blobs; the planner's own two test files in place of the builder's; the break script against the builder's tests alone; the open CodeQL alerts set-diffed against `main`'s.
3. Merge to `main`, tag. **Post-merge CodeQL** checked on `main`.
4. **F1, at no cost and read-only:** on merged `main`, `f1_render.py` rebuilds the stored packets from the live graph: every one equals the stored packet with only the two line changes (43 of 43 on the prototype).
5. **Before any deploy:** the firewall on `claude-opus-5`, the fleet's declared fallback (ADR-0010 decision 4), on the operator's word because it spends from the Anthropic balance. **The deploy is the operator's word.**
6. **F2, after the deploy, over the first five debated orders:** the rulings are not all one value; no `revise` or `overturn` rationale rests on the ratio; every `overturn` read by the planner against its packet; 0 failed open.

---

## Handover — paste this to Codex

```text
You are building Sprint 291 in the worktree ../ta-s291, on the branch
sprint-291-the-judge-rules-on-what-distinguishes-the-order. Never work on main.

Read docs/sprints/sprint-291-the-judge-rules-on-what-distinguishes-the-order.md, whole, before
anything else. It is the spec, and its bottom sections are your handback. Every decision is made
and the whole production change is one script, Appendix B. What you write is two test files.

In order:
1. Read agents/deliberator/laws/laws.md and test-plan.md, docs/laws/conventions.md and
   docs/laws/drift-register.md. Fill the Law reading record in the spec BEFORE any change. The
   law-cycle answer is Yes, one clause, and Appendix B makes it: do not type a law edit yourself.
2. Write tests/test_reward_risk_is_a_disclosed_figure.py and tests/test_judge_rules_on_the_order.py
   with exactly the test names of the Test plan, each docstring citing its clause, each module
   docstring declaring Agent, Role and External I/O. Run
     uv run --no-sync pytest tests/test_reward_risk_is_a_disclosed_figure.py tests/test_judge_rules_on_the_order.py --no-cov -q -p no:cacheprovider
   on the unchanged tree and paste the output into the Closeout. Expected: 2 errors at collection
   (ImportError: the names do not exist yet).
3. Save Appendix B's block to scratch-s291/apply_s291.py and Appendix C's to
   scratch-s291/s291_breaks.py (a new folder in the worktree, because your sandbox denies temp
   directories). Run, from the worktree's root:
     uv run --no-sync python scratch-s291/apply_s291.py
   Then git hash-object on each of the 17 files must start with the 12 characters Appendix B
   gives. Do NOT run uv lock in any form.
4. Run the step 2 command again: 16 passed. Then run
     uv run --no-sync pytest tests/test_deliberation_prompt_facts.py tests/test_deliberation_prompt_truth.py tests/test_deliberation_prompt_pipeline.py tests/test_deliberation_prompt_artifacts.py tests/test_prompt_recipe.py tests/test_veto_context_verdict_attribution.py orchestration/tests/test_veto_stage.py --no-cov -q -p no:cacheprovider
   No test may fail.
5. Run the fifteen breaks:
     uv run --no-sync python scratch-s291/s291_breaks.py . scratch-s291/breaks.txt
   The last line must read 15 of 15. The script restores each file itself; afterwards git status
   must show the same files as before it ran. Paste breaks.txt into the Closeout.
6. Delete the folder scratch-s291. Run make ci redirected to a file and read the file. If a step
   cannot run in your sandbox (the dependency audit needs a network), say "not done" for that step
   and paste its lines.
7. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in this sprint's
   row of docs/sprints/README.md (the row's status cell must lead with BUILT). Commit on the branch
   if your sandbox lets you write the repository's git directory; if not, leave the tree
   uncommitted and say so.

DO NOT: run uv lock or uv sync; run any az or deploy command, or call any LLM; hand-edit
kernel/deliberation_judge_prompt.py, scripts/deliberation_judge_prompt.json or any law file; change
agents/execution/, contracts/, agents/deliberator/review_batch.py or the debaters' prompts; change
any existing test beyond the three Appendix B changes; add a design-log entry; edit docs/STATE.md,
docs/work-queue.md or docs/design-log.md; add entries to .secrets.baseline; use noqa; leave
scratch-s291 in the tree; paste a whole make ci log into the spec; measure make ci through a pipe.

Traps: the first red is a collection error, by design, and the per-test red is step 5; A7's minus
sign is U+2212, written − because ruff refuses the literal; A10 indexes an object, so it needs
# type: ignore[index] or a typed helper; ruff reads test files (88 characters a line); three
existing tests state the old text, so a green suite alone proves little.

Two tiers of trouble. A wrong path, count or command in this spec whose intent is plain: correct it,
go on, and record it in the Return notes. A blob id that does not match after a clean run of
Appendix B, a law that contradicts the spec, an existing test that fails, or a break that stays
green: STOP and report. State anything not done as "not done" or "verified failing". Never write a
Result for work you have not done.

Handback checklist, each answered in the Closeout:
 1. Law reading record filled before the first change.
 2. Red output of step 2 pasted (2 errors at collection).
 3. The 17 blob ids after Appendix B, as printed.
 4. Green output of step 4 pasted (16 passed; the seven existing files pass).
 5. git diff --stat against the base: exactly Appendix B's 17 files, the two new test files, this
    spec and docs/sprints/README.md.
 6. The fifteen breaks, one line each: the test that went red, and restored.
 7. The line counts of the two new test files.
 8. make ci: the file's path, the exit code, each step's verdict line, the pytest totals and
    coverage; every step not run named "not done".
 9. The tree the proofs ran in, and that it holds no .env.
10. Status BUILT in the spec and in the README row; committed or not, and the SHA if committed.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| PM disclosure renderer | `agents/deliberator/laws/laws.md` (whole), `test-plan.md` (whole); `docs/laws/conventions.md`, `drift-register.md` (whole) | DLIB-NEV-08, DLIB-NEV-09 | Yes: only exact disclosure field on a passed outcome loses its verdict. |
| Judge sources, compiler, champion and recipe | Same law book and test plan; ADR-0010 | DLIB-OUT-04, DLIB-OBS-07, new DLIB-OUT-09 | Keep verdict effects unchanged; use Appendix B alone for the amendment and compiled text. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** Yes, one guarantee (DLIB-OUT-09), no contract. Appendix B performs the v1.19 amendment and rollups; tests precede it.

**Contradictions found between a law and this spec:** None. The explicitly authorized Appendix B amendment governs this sprint.

**Laws found silent where a decision was needed:** The existing book has no order-specific judge-prompt guarantee; the spec resolves this with new DLIB-OUT-09. No further undecided silence found.

**Clauses that were ⬜ and are now proven:** New DLIB-OUT-09 is proven by A8-A10. Existing DLIB-NEV-08, DLIB-NEV-09, DLIB-OUT-04 and DLIB-OBS-07 already had green rows; this sprint strengthens the disclosure and recipe evidence. Rollups now 36 / 67.

Reading recorded before any code change, 2026-11-25. Clean branch: `sprint-291-the-judge-rules-on-what-distinguishes-the-order`; base `85a9e4bf85b7c3566b593e519aad1eaa4949638e`.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a_disclosed_ratio_is_not_a_passed_gate` | `tests/test_reward_risk_is_a_disclosed_figure.py` | PASS | DLIB-NEV-08 |
| A2 | `test_the_rule_is_stated_once_after_the_gates` | `tests/test_reward_risk_is_a_disclosed_figure.py` | PASS | DLIB-NEV-08 |
| A3 | `test_an_enforced_ratio_keeps_its_verdict` | `tests/test_reward_risk_is_a_disclosed_figure.py` | PASS (parametrized) | DLIB-NEV-08 |
| A4 | `test_a_gate_that_did_not_pass_is_never_recast` | `tests/test_reward_risk_is_a_disclosed_figure.py` | PASS (parametrized) | DLIB-NEV-08 |
| A5 | `test_the_whole_packet_states_the_rule_before_the_pm_run` | `tests/test_reward_risk_is_a_disclosed_figure.py` | PASS | DLIB-NEV-08 |
| A6 | `test_the_rule_states_what_the_code_does` | `tests/test_reward_risk_is_a_disclosed_figure.py` | PASS | DLIB-NEV-09 |
| A7 | `test_the_rules_evidence_is_adr_0027s` | `tests/test_reward_risk_is_a_disclosed_figure.py` | PASS | DLIB-NEV-09 |
| A8 | `test_the_judge_is_told_to_rule_on_this_order` | `tests/test_judge_rules_on_the_order.py` | PASS | DLIB-OUT-09 |
| A9 | `test_every_ruling_is_demonstrated` | `tests/test_judge_rules_on_the_order.py` | PASS | DLIB-OUT-09 |
| A10 | `test_each_contrast_case_shows_its_ruling` | `tests/test_judge_rules_on_the_order.py` | PASS | DLIB-OUT-09 |
| A11 | `test_the_contrast_cases_reach_only_the_judge` | `tests/test_judge_rules_on_the_order.py` | PASS (parametrized) | DLIB-OUT-09 |
| A12 | `test_the_judge_prompt_is_in_the_recipe` | `tests/test_judge_rules_on_the_order.py` | PASS | DLIB-OBS-07 |

**Tests added beyond the plan:** None; A1-A12 produce 16 cases.

---

## Closeout — evidence

**Status:** BUILT — all 16 local CI steps pass; no remote/merge/deploy proof.

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/Downloads/project/ta-s291`, branch `sprint-291-the-judge-rules-on-what-distinguishes-the-order`. No `.env` present; confirmed before tests and after breaks.

**Result:** Appendix B applied unchanged; 17 exact blob matches. Initial red: two intended collection errors. New tests: 16 passed. Required existing tests: 53 passed. All 15 named breaks red and restored. `make ci` exit 0: all 16 steps passed; 5,350 passed, 8 skipped, 100.00 % coverage.

**Files changed:** Exactly Appendix B's 17, two new test files, this spec and `docs/sprints/README.md` (21 total). No excluded paths changed. `git diff --stat` against base `85a9e4bf85b7c3566b593e519aad1eaa4949638e`:

```text
agents/deliberator/context_pm.py                   |  29 ++++-
 agents/deliberator/laws/laws.md                    |  10 +-
 agents/deliberator/laws/test-plan.md               |   5 +-
 agents/deliberator/prompt_recipe.py                |   2 +
 docs/laws/INDEX.md                                 |   2 +-
 docs/laws/drift-register.md                        |   1 +
 docs/laws/ledger.md                                |   2 +-
 docs/sprints/README.md                             |   2 +-
 ...-judge-rules-on-what-distinguishes-the-order.md | 138 ++++++++++++++++++--
 kernel/deliberation_judge_prompt.py                | 124 ++++++++++++++++++
 kernel/deliberation_prompts.py                     |  66 +---------
 orchestration/tests/test_veto_stage.py             |   2 +-
 pyproject.toml                                     |   2 +-
 scripts/compile_deliberation_prompts.py            |  22 +++-
 scripts/deliberation_judge_prompt.json             |  56 +++++++-
 scripts/deliberation_prompt_sources.py             |  70 +++++++++-
 tests/test_deliberation_prompt_artifacts.py        |   2 +-
 tests/test_deliberation_prompt_facts.py            |   7 +-
 tests/test_judge_rules_on_the_order.py             |  81 ++++++++++++
 tests/test_reward_risk_is_a_disclosed_figure.py    | 144 +++++++++++++++++++++
 uv.lock                                            |   2 +-
 21 files changed, 669 insertions(+), 100 deletions(-)
```

**Design decisions:** recorded as [`DL-326`](../design-log.md) by the planner.

**Proof — the red run first:** production unchanged, exit 2.

```text
=================================== ERRORS ====================================
______ ERROR collecting tests/test_reward_risk_is_a_disclosed_figure.py _______
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s291\tests\test_reward_risk_is_a_disclosed_figure.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_reward_risk_is_a_disclosed_figure.py:19: in <module>
    from agents.deliberator.context_pm import REWARD_RISK_RULE, order_lines
E   ImportError: cannot import name 'REWARD_RISK_RULE' from 'agents.deliberator.context_pm' (C:\Users\yury_\Downloads\project\ta-s291\agents\deliberator\context_pm.py)
___________ ERROR collecting tests/test_judge_rules_on_the_order.py ___________
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s291\tests\test_judge_rules_on_the_order.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_judge_rules_on_the_order.py:15: in <module>
    from scripts.deliberation_prompt_sources import JUDGE_CONTRAST_CASES, JUDGE_ORDER_RULE
E   ImportError: cannot import name 'JUDGE_CONTRAST_CASES' from 'scripts.deliberation_prompt_sources' (C:\Users\yury_\Downloads\project\ta-s291\scripts\deliberation_prompt_sources.py)
=========================== short test summary info ===========================
ERROR tests/test_reward_risk_is_a_disclosed_figure.py
ERROR tests/test_judge_rules_on_the_order.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!
2 errors in 30.09s
```

**Proof — the green run:** new tests, exit 0.

```text
................                                                         [100%]
16 passed in 2.75s
```

Seven required existing test files, exit 0:

```text
.....................................................                    [100%]
53 passed in 12.60s
```

Appendix B exit 0; all 17 `git hash-object` values matched:

```text
192a8e3957d3335ce7556bd7c44dcd0718705f31 agents/deliberator/context_pm.py
22ba8999d40a031b24be5c925b1fa1cc3ea19d70 agents/deliberator/laws/laws.md
3c01cc3c67b85bfe72826c3cfdb496d9cf2b836d agents/deliberator/laws/test-plan.md
f0f6337dadc2dca175623a084aa7030ec8289df1 agents/deliberator/prompt_recipe.py
23107d0d5f8a69148f64d57a13f2176c50ebe337 docs/laws/INDEX.md
43db0327e87c70b8428e3abe7b85de0032290040 docs/laws/drift-register.md
3536d77c660267b35f43f67a4798070966f717fd docs/laws/ledger.md
9cd3186328928f99e681537910af257b13654eda kernel/deliberation_judge_prompt.py
dfffa695b4093646ac57c3e802ef4b11f9f5a622 kernel/deliberation_prompts.py
3669fb10922f38090119f554d15fbe778022978e orchestration/tests/test_veto_stage.py
6f12b92fc6a7d6323c8f8359381188d73797f871 pyproject.toml
6e75a80c5f8c28e7da68452d56ce684657479577 scripts/compile_deliberation_prompts.py
4b2426c1e472a4079f5840ab2191bccb5f59c1e9 scripts/deliberation_judge_prompt.json
97a7150f217e0182bd2a2d4eff64570219ce69e6 scripts/deliberation_prompt_sources.py
6e9921c3029ad731098ee68201cc0b4a2c3d8b8e tests/test_deliberation_prompt_artifacts.py
441bfeefc984a692dbe3e739dcc36519eb227d98 tests/test_deliberation_prompt_facts.py
ba64b9e85da0a2f8573ff8e3674f80ddbc607562 uv.lock
```

**Guards planted:** Appendix C exit 0. All 15 named tests went red; every planted file restored byte for byte, and `git status --short` is identical before/after.

```text
B1 RED expected test_a_disclosed_ratio_is_not_a_passed_gate; failed: ['test_a_disclosed_ratio_is_not_a_passed_gate', 'test_the_whole_packet_states_the_rule_before_the_pm_run']
B2 RED expected test_the_rule_is_stated_once_after_the_gates; failed: ['test_the_rule_is_stated_once_after_the_gates', 'test_the_whole_packet_states_the_rule_before_the_pm_run']
B3 RED expected test_the_rule_is_stated_once_after_the_gates; failed: ['test_the_rule_is_stated_once_after_the_gates', 'test_the_whole_packet_states_the_rule_before_the_pm_run']
B4 RED expected test_a_gate_that_did_not_pass_is_never_recast; failed: ['test_a_gate_that_did_not_pass_is_never_recast[failed-FAILED]', 'test_a_gate_that_did_not_pass_is_never_recast[not_evaluated-NOT-EVALUATED]']
B5 RED expected test_an_enforced_ratio_keeps_its_verdict; failed: ['test_an_enforced_ratio_keeps_its_verdict[DISCLOSURE_ONLY_DRAFT]']
B6 RED expected test_a_disclosed_ratio_is_not_a_passed_gate; failed: ['test_a_disclosed_ratio_is_not_a_passed_gate']
B7 RED expected test_the_rules_evidence_is_adr_0027s; failed: ['test_the_rules_evidence_is_adr_0027s']
B8 RED expected test_the_rules_evidence_is_adr_0027s; failed: ['test_the_rules_evidence_is_adr_0027s']
B9 RED expected test_the_rule_states_what_the_code_does; failed: ['test_the_rule_states_what_the_code_does']
B10 RED expected test_the_judge_is_told_to_rule_on_this_order; failed: ['test_the_judge_is_told_to_rule_on_this_order']
B11 RED expected test_the_champion_is_its_sources_rebuilt; failed: ['test_the_champion_is_its_sources_rebuilt']
B12 RED expected test_every_ruling_is_demonstrated; failed: ['test_every_ruling_is_demonstrated', 'test_each_contrast_case_shows_its_ruling']
B13 RED expected test_the_champion_is_its_sources_rebuilt; failed: ['test_the_champion_is_its_sources_rebuilt']
B14 RED expected test_the_contrast_cases_reach_only_the_judge; failed: ['test_the_contrast_cases_reach_only_the_judge[shared-sizing-rule']
B15 RED expected test_the_judge_prompt_is_in_the_recipe; failed: ['test_the_judge_prompt_is_in_the_recipe']
15 of 15 breaks red on their named test
```

**Module line counts:**

```text
agents/deliberator/context_pm.py: 156
agents/deliberator/prompt_recipe.py: 79
kernel/deliberation_judge_prompt.py: 124
kernel/deliberation_prompts.py: 93
orchestration/tests/test_veto_stage.py: 193
scripts/compile_deliberation_prompts.py: 188
scripts/deliberation_prompt_sources.py: 116
tests/test_deliberation_prompt_artifacts.py: 168
tests/test_deliberation_prompt_facts.py: 151
tests/test_reward_risk_is_a_disclosed_figure.py: 144
tests/test_judge_rules_on_the_order.py: 81
```

**`make ci`:** exit **0**, redirected to `C:/Users/yury_/.codex/tmp/s291-evidence-20261125/ci.txt`; exit recorded separately in `ci-exit.txt`. `UV_NO_SYNC=1`; output never piped. No local step is not done. Silent checks exited 0, evidenced by the next recipe executing and final make exit 0.

| Step | Check | Verdict |
| --- | --- | --- |
| 1 | ruff | PASS (exit 0) |
| 2 | format | PASS (exit 0) |
| 3 | mypy | PASS (exit 0) |
| 4 | import-linter | PASS (exit 0) |
| 5 | module size | PASS (exit 0) |
| 6 | module header | PASS (exit 0) |
| 7 | law coverage | PASS (exit 0) |
| 8 | PARAM/settings sync | PASS (exit 0) |
| 9 | sprint status | PASS (exit 0) |
| 10 | tracker size | PASS (exit 0) |
| 11 | markdown links | PASS (exit 0) |
| 12 | version scheme | PASS (exit 0) |
| 13 | pytest / coverage | PASS (exit 0) |
| 14 | dependency audit | PASS (exit 0) |
| 15 | detect-secrets | PASS (exit 0) |
| 16 | untracked secrets | PASS (exit 0) |

Selected real verdict lines (full log retained at the path above):

```text
1848 files already formatted
Success: no issues found in 1301 source files
Contracts: 5 kept, 0 broken.
docs_seen=297 SPEC=10 BUILT=1 MERGED=286 UNMAPPED=0 MISSING=0
TOTAL                                                           21969      0   4704      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
========= 5350 passed, 8 skipped, 2470 warnings in 855.45s (0:14:15) ==========
No unaccepted vulnerabilities; 1 accepted advisory re-checked
Detect secrets...........................................................Passed
detect-secrets (untracked): no untracked files to scan
make ci exit: 0
```

Eight skips: local `.env` proofs (2), Celery broker (1), link privilege (1), Postgres DSN (2), optional Finnhub/Stooq network probes (2). Pytest reported 2,470 warnings.

**`make gate-ran`:** the planner's, after the push.

**Not met / verified failing:** No failing local gate. Remote `make gate-ran`, push, merge, deployment, F1/F2 and fallback-vendor firewall: **not done**, as assigned to the planner/operator.

---

## Return notes

- Appendix B and C were extracted unchanged from the fenced blocks. No `uv lock`, `uv sync`, Azure/deploy command or LLM call was run. `UV_NO_SYNC=1` is set for `make ci` because its recipes use plain `uv run`.
- All production/law changes came solely from Appendix B. The two new test modules have the exact planned test names and clause citations. A7 uses the Python escape `\u2212`; A10 uses a typed cast.
- No change to verdict effects, execution, contracts, review_batch, debater prompts, baseline, STATE or design log. The handover's narrower scope overrides the memory skill's local-state recommendation.
- Scratch was removed after copying its break log outside the worktree. No extra worktree files remain.
- Remote `make gate-ran`, push/merge, CodeQL comparison, F1, fallback-vendor firewall and F2 are not done by the builder; owed to the planner/operator as specified. No deployment or live-success claim.
- Local CI is complete and green. Commit on the requested branch follows this completed handback; resulting build SHA is recorded below after committing.

---

## Appendix A — the paid proof, fixed before the first call

**The bar, written before any paid call** (kit `prereg.md`, SHA-256 starting `f47d31a3549576c4`): over a held-out
test set, B1 at least two different rulings; B2 no `revise` or `overturn` rationale matches the ratio's pattern;
B3 at most 2 of 6 are `overturn`; B4 every debate finishes, at least five of six; B5 the four golden cases pass.
The wording could change at most twice on the development set and never on the test set.

**Result: PASS.** Order set by rule (`i % 7 == 3` of the 43, in date order); the $8 cap stopped the sixth (CSCO, index 38) before it started.

| Order | Stored | Ruling | The judge's reason, as written |
| --- | --- | --- | --- |
| EMR | 2026-10-01 | `revise` | EMR clears the confidence floor by only 0.015 while fundamental and sentiment scores are below neutral and the technical setup includes stretched weak subsignals |
| CAT | 2026-10-13 | `uphold` | CAT's scaled stop/target asymmetry is the shared disclosed reward-risk non-gate, and its confidence is not solely sentiment-driven because technical is above neutral and fundamentals are neutral. |
| SBUX | 2026-10-20 | `revise` | SBUX earnings are in 9 days inside the 10-day holding window, with no evidence the 5% stop is gap-aware or that the position exits before the event |
| SO | 2026-10-26 | `revise` | SO’s 11-share sizing pass has only a tiny cushion below the 1% issuer cap, and without an execution cap a fill near the recorded $93.39 high would breach that limit |
| MA | 2026-10-30 | `uphold` | MA is not a sentiment-only pass: its technical and fundamental pillars are both above neutral, and the overbought/low-rank objections are already reflected in the scored inputs rather than showing a MA-specific defect |

Each cited fact was read back from that order's packet ($0, kit `check_rationales.txt`): EMR's floor margin 0.615 − 0.600, SBUX's `days_to_earnings=9`, SO's 11 shares at a sizing ratio of 0.00996 and a day's high of $93.39.

---

## Appendix B — the change, measured on the planner's prototype

Save this block as `scratch-s291/apply_s291.py` and run it once from the worktree's root. On a clean checkout of
the base it reproduced the prototype's tree exactly (`c03f972c`, with the planner's two test files added).

```python
"""Sprint 291's whole change except its two new test files. Run once, on the clean base.

Usage, from the worktree's root:
  uv run --no-sync python scratch-s291/apply_s291.py
"""

import re
import subprocess
import sys
from pathlib import Path

root = Path.cwd()


def sub(rel, old, new, count=1):
    p = root / rel
    s = p.read_bytes().decode("utf-8")
    assert s.count(old) == count, (rel, old[:60], s.count(old))
    p.write_bytes(s.replace(old, new).encode("utf-8"))


sub(
    "agents/deliberator/context_pm.py",
    """    from contracts.provider import RegimeContext


def order_lines""",
    """    from contracts.provider import RegimeContext

_DISCLOSURE_ONLY = "comparison=DISCLOSURE_ONLY"
REWARD_RISK_RULE = (
    "Reward-to-risk, the rule for every order: min_reward_risk_ratio is 0, so this "
    "ratio is printed and rejects no order at any value. ADR-0027 chose this on "
    "47,485 decisions from 2017 to 2026: names at or above a ratio of 0.80 earned "
    "+0.03 % a trade more than names below it (95 % CI -0.17 % to +0.23 %). That "
    "it is not enforced is true of every order and is a recorded design decision, "
    "not a flaw of this order."
)


def order_lines""",
)
sub(
    "agents/deliberator/context_pm.py",
    """    return [f"PM gate outcome: {_gate_line(gate)}" for gate in intent.gate_report]
""",
    """    lines = [_gate_report_line(gate) for gate in intent.gate_report]
    if any(_is_disclosure_only(gate) for gate in intent.gate_report):
        lines.append(REWARD_RISK_RULE)
    return lines


def _gate_report_line(gate: GateOutcome) -> str:
    if not _is_disclosure_only(gate):
        return f"PM gate outcome: {_gate_line(gate)}"
    value_label, _ = gate_value_labels(gate.name)
    return (
        f"PM disclosed figure, not a gate: name={gate.name} "
        f"{value_label}={gate.value:.4g} ({gate.detail})"
    )


def _is_disclosure_only(gate: GateOutcome) -> bool:
    return gate.outcome == "passed" and _DISCLOSURE_ONLY in gate.detail.split("; ")
""",
)

sub(
    "scripts/deliberation_prompt_sources.py",
    """# Added by the pipeline (S119), so part of the judge's instruction, not its base.
JUDGE_GROUNDED_FLAW_RULE = (
    " If the Challenger catches a grounded implementation-specific flaw from "
    "the evidence, do not uphold the decision."
)
""",
    """# What the judge rules on (S291, DL-326). It replaced S119's "do not uphold once a
# flaw is named", under which every ruling from 2026-09-18 was `revise`.
JUDGE_ORDER_RULE = (
    " Rule on what distinguishes THIS order from every other order the system "
    "would approve. A design property that is true of every order, such as a "
    "figure printed and not enforced (the target's size against the stop is one), "
    "fixed-fraction sizing, or a regime label that changes no number, is a design "
    "note and cannot decide the ruling unless this order's own case relies on it. "
    "Passing every gate does not earn an uphold: the gates are why the order "
    "reached you. Rule uphold when this name's own evidence supports the order and "
    "the objections are shared or unsupported. Rule revise when this name's own "
    "evidence shows a material weakness the gates do not answer, such as "
    "confidence that clears its floor only through one pillar, news or a recent "
    "move against the thesis, or an event inside the holding period. Rule overturn "
    "only when evidence specific to this order shows it should not be placed, such "
    "as a wrong input it depends on or a stated limit it breaks. A revise or "
    "overturn rationale states only the evidence that decided it and names no "
    "design note."
)
# Hypotheticals, so the judge sees every ruling demonstrated: (name, decision,
# context, ruling, rationale). They state no fact about this system's code.
JUDGE_CONTRAST_CASES = (
    (
        "shared-disclosed-figure",
        "Buy KO: every enforced gate passed.",
        "A ratio in the report is printed and rejects no order at any value. KO's "
        "inputs are current and its stop is recorded. The challenger's only "
        "objection is that this ratio is not enforced.",
        "uphold",
        "the objection holds for every order and names nothing wrong with this one",
    ),
    (
        "shared-sizing-rule",
        "Buy PG, sized like every other order.",
        "PG has beta 0.4 and an ordinary range for its history. The challenger's "
        "only objection is that the sizing rule ignores volatility.",
        "uphold",
        "the sizing rule is shared by every order and this low-beta name gives it "
        "no extra force",
    ),
    (
        "one-pillar-clearance",
        "Buy XYZ at confidence 0.61.",
        "The floor is 0.60. With its sentiment score at neutral the confidence "
        "would be 0.58, and its technical and fundamental scores are below neutral.",
        "revise",
        "this order clears its floor only through sentiment, so its case is "
        "thinner than its score suggests",
    ),
    (
        "wrong-price-input",
        "Buy 10 XYZ at the estimated price of $412.00.",
        "The latest close in the evidence is $41.20, so the order's estimated "
        "price is ten times the market's.",
        "overturn",
        "the order's price contradicts its own latest close, so its size and stop "
        "rest on a wrong input",
    ),
    (
        "stated-limit-broken",
        "Buy ABC, a new issuer in Energy.",
        "The evidence states a limit of three names per sector and shows three "
        "Energy names already held, so ABC would be the fourth.",
        "overturn",
        "this order breaks the stated limit on names in its sector",
    ),
)
""",
)

c = "scripts/compile_deliberation_prompts.py"
sub(
    c,
    "    JUDGE_BASE,\n    JUDGE_GROUNDED_FLAW_RULE,\n",
    "    JUDGE_BASE,\n    JUDGE_CONTRAST_CASES,\n    JUDGE_ORDER_RULE,\n",
)
sub(
    c,
    '"judge": JUDGE_BASE + JUDGE_GROUNDED_FLAW_RULE + CLASS1_CALIBRATION,',
    '"judge": JUDGE_BASE + JUDGE_ORDER_RULE + CLASS1_CALIBRATION,',
)
sub(
    c,
    """            )
        )
    return tuple(examples)
""",
    """            )
        )
    if role == "judge":
        examples.extend(_contrast_example(*case) for case in JUDGE_CONTRAST_CASES)
    return tuple(examples)


def _contrast_example(
    name: str, decision: str, context: str, ruling: str, rationale: str
) -> PromptExample:
    return PromptExample(
        inputs={
            "case": name,
            "decision": decision,
            "context": context,
            "flaw_keywords": [],
        },
        output=json.dumps({"ruling": ruling, "rationale": rationale}, sort_keys=True),
        rationale=rationale,
    )
""",
)

# Existing tests that state the old text.
sub(
    "tests/test_deliberation_prompt_artifacts.py",
    'assert artifact.version == "2026-09-30-s245-v6-judge-claude-opus-5"',
    'assert artifact.version == "2026-11-22-s291-v7-judge-gpt-5.5"',
)
sub(
    "orchestration/tests/test_veto_stage.py",
    'assert "PM gate outcome: name=reward_risk" in prompt',
    'assert "PM disclosed figure, not a gate: name=reward_risk" in prompt',
)
f = "tests/test_deliberation_prompt_facts.py"
sub(
    f,
    "from scripts.deliberation_eval import _CLASS1, _CLASS2\n",
    "from scripts.deliberation_eval import _CLASS1, _CLASS2\n"
    "from scripts.deliberation_prompt_sources import JUDGE_CONTRAST_CASES\n",
)
sub(
    f,
    "    ones, every worked example is a Class-2 hypothetical or a pinned Class-1 case,\n",
    "    ones, every worked example is a Class-2 or contrast hypothetical or a pinned\n"
    "    Class-1 case,\n",
)
sub(
    f,
    "    class2 = {str(case[0]) for case in _CLASS2}\n",
    "    class2 = {str(case[0]) for case in _CLASS2}\n"
    "    contrast = {str(case[0]) for case in JUDGE_CONTRAST_CASES}\n",
)
sub(
    f,
    "assert set(_CASE.findall(prompt)) <= class2 | set(CASE_PINS)",
    "assert set(_CASE.findall(prompt)) <= class2 | contrast | set(CASE_PINS)",
)

# The law cycle.
laws = "agents/deliberator/laws/laws.md"
sub(laws, "**status:** LOCKED v1.18", "**status:** LOCKED v1.19")
sub(
    laws,
    "  says in one line why it is withheld.\n",
    "  says in one line why it is withheld.\n"
    "+ **DLIB-OUT-09** -- The judge's champion prompt tells it to rule on what\n"
    "  distinguishes this order: a design property true of every order cannot decide\n"
    "  the ruling unless this order's own case relies on it. Its examples demonstrate\n"
    "  each of `uphold`, `revise` and `overturn`.\n",
)
sub(
    laws,
    "  fallbacks are handed over too). PARAM: `llm_fallbacks` added, `llm_provider`\n  reworded.\n",
    "  fallbacks are handed over too). PARAM: `llm_fallbacks` added, `llm_provider`\n  reworded.\n"
    "+ v1.19 -- S291 / DL-326 (2026-11-22). Adds and proves `DLIB-OUT-09`. The packet\n"
    "  stops rendering the disclosure-only reward-to-risk ratio as a passed gate, which\n"
    "  `DLIB-NEV-08` forbade and its test could not see (DRIFT-118). One clause added\n"
    "  and proven: 35 / 66 -> 36 / 67.\n",
)
plan = "agents/deliberator/laws/test-plan.md"
sub(plan, "**status:** LOCKED v1.18 · **aligned with:** laws.md LOCKED v1.18", "**status:** LOCKED v1.19 · **aligned with:** laws.md LOCKED v1.19")
s = (root / plan).read_bytes().decode("utf-8")
row = next(x for x in s.split("\n") if x.startswith("| DLIB-OUT-08 |"))
sub(
    plan,
    row + "\n",
    row
    + "\n| DLIB-OUT-09 | The judge's champion prompt rules on what distinguishes this order; a shared design property cannot decide it unless this order's own case relies on it; its examples demonstrate each ruling. | functional | `tests/test_judge_rules_on_the_order.py::test_the_judge_is_told_to_rule_on_this_order`; `tests/test_judge_rules_on_the_order.py::test_every_ruling_is_demonstrated`; `tests/test_judge_rules_on_the_order.py::test_each_contrast_case_shows_its_ruling` | 🟩 |\n",
)
sub(
    plan,
    "`tests/test_veto_context_verdict_attribution.py::test_no_rendered_verdict_lacks_an_enforcing_check`;",
    "`tests/test_veto_context_verdict_attribution.py::test_no_rendered_verdict_lacks_an_enforcing_check`; `tests/test_reward_risk_is_a_disclosed_figure.py::test_a_disclosed_ratio_is_not_a_passed_gate`;",
)
note = "S291 (DL-326) adds and proves DLIB-OUT-09, the judge rules on what distinguishes the order, and corrects DRIFT-118. "
sub("docs/laws/ledger.md", "| deliberator | ✅ v1.18 (LOCKED) | 35 / 66 | ", "| deliberator | ✅ v1.19 (LOCKED) | 36 / 67 | " + note)
sub("docs/laws/INDEX.md", "| deliberator | ✅ LOCKED v1.18 (S277, DL-289) | 35 / 66 | ", "| deliberator | ✅ LOCKED v1.19 (S291, DL-326) | 36 / 67 | " + note)
reg = "docs/laws/drift-register.md"
s = (root / reg).read_bytes().decode("utf-8")
row = next(x for x in s.split("\n") if x.startswith("| DRIFT-117 |"))
sub(
    reg,
    row + "\n",
    row
    + "\n| DRIFT-118 | `DLIB-NEV-08` | Never renders a `PASSED` verdict for a comparison no agent enforces. | *[measured 2026-11-22]* Since the reward-to-risk floor went to 0 (ADR-0027 Correction 2, 2026-09-17) every packet printed `PM gate outcome: name=reward_risk … threshold_reward_risk_ratio=0 -> PASSED (… comparison=DISCLOSURE_ONLY)`. `test_no_rendered_verdict_lacks_an_enforcing_check` accepts any PM gate's name, so it stayed green. All 43 debates with a stored packet (2026-10-01 to 2026-11-20) were ruled `revise` with a rationale naming that figure ([DL-326](../design-log.md)). | code-drift | **CORRECTED** by S291: the ratio prints as a disclosed figure with no threshold and no verdict, and a test reads the exact line. |\n",
)

# The version: one line each, and uv.lock is never re-resolved here.
sub("pyproject.toml", 'version = "0.131.07"', 'version = "0.131.08"')
sub("uv.lock", 'version = "0.131.7"', 'version = "0.131.8"')

# The recipe names the module that now holds the judge's text.
sub(
    "agents/deliberator/prompt_recipe.py",
    "    deliberation_guided_render,\n",
    "    deliberation_guided_render,\n    deliberation_judge_prompt,\n",
    count=2,
)

# The compiled artifact, then the promoted constant in a module of its own.
subprocess.run(
    [
        sys.executable,
        "scripts/compile_deliberation_prompts.py",
        "--role",
        "judge",
        "--judge-model",
        "gpt-5.5",
        "--version",
        "2026-11-22-s291-v7",
    ],
    check=True,
)
artifact = __import__("json").loads(
    (root / "scripts/deliberation_judge_prompt.json").read_text(encoding="utf-8")
)


def escaped(ch):
    return {"\\": "\\\\", '"': '\\"', "\n": "\\n"}.get(ch, ch)


chunks, current, width = [], "", 0
for ch in artifact["system_prompt"]:
    piece = escaped(ch)
    if width + len(piece) > 78:
        chunks.append(current)
        current, width = "", 0
    current += piece
    width += len(piece)
chunks.append(current)
body = "\n".join(f'    "{chunk}"' for chunk in chunks)
module = (
    '"""Deliberation champion judge prompt.\n\n'
    "Agent: kernel\n"
    "Role: hold the promoted judge system prompt, compile output and never a hand edit.\n"
    "External I/O: none.\n\n"
    "Its sources are pack tooling (`scripts/deliberation_prompt_sources.py`); a rebuild\n"
    "reproduces it byte for byte (S245, S291, DLIB-NEV-09).\n"
    '"""\n\n'
    "# Promoted from PromptArtifact task=deliberation.judge,\n"
    f"# version={artifact['version']}.\nJUDGE_SYSTEM = (\n{body}\n)\n"
)
(root / "kernel/deliberation_judge_prompt.py").write_bytes(module.encode("utf-8"))
prompts = root / "kernel/deliberation_prompts.py"
text = prompts.read_bytes().decode("utf-8")
found = re.search(r"# Promoted from PromptArtifact task=deliberation\.judge,.*\Z", text, re.S)
kept = text[: found.start()].rstrip() + "\n"
anchor = "_DEFINE_THEN_JUSTIFY = ("
assert kept.count(anchor) == 1
kept = kept.replace(
    anchor,
    "from kernel.deliberation_judge_prompt import JUDGE_SYSTEM as JUDGE_SYSTEM\n\n" + anchor,
)
prompts.write_bytes(kept.encode("utf-8"))
subprocess.run(
    [
        sys.executable,
        "-m",
        "ruff",
        "format",
        "-q",
        "kernel/deliberation_prompts.py",
        "kernel/deliberation_judge_prompt.py",
        "scripts/compile_deliberation_prompts.py",
        "scripts/deliberation_prompt_sources.py",
        "agents/deliberator/context_pm.py",
        "agents/deliberator/prompt_recipe.py",
    ],
    check=True,
)
print("applied")
```

After it, `git hash-object <file>` must start with:

```text
192a8e3957d3 agents/deliberator/context_pm.py
22ba8999d40a agents/deliberator/laws/laws.md
3c01cc3c67b8 agents/deliberator/laws/test-plan.md
f0f6337dadc2 agents/deliberator/prompt_recipe.py
23107d0d5f8a docs/laws/INDEX.md
43db0327e87c docs/laws/drift-register.md
3536d77c6602 docs/laws/ledger.md
9cd318632892 kernel/deliberation_judge_prompt.py
dfffa695b409 kernel/deliberation_prompts.py
3669fb10922f orchestration/tests/test_veto_stage.py
6f12b92fc6a7 pyproject.toml
6e75a80c5f8c scripts/compile_deliberation_prompts.py
4b2426c1e472 scripts/deliberation_judge_prompt.json
97a7150f217e scripts/deliberation_prompt_sources.py
6e9921c3029a tests/test_deliberation_prompt_artifacts.py
441bfeefc984 tests/test_deliberation_prompt_facts.py
ba64b9e85da0 uv.lock
```

---

## Appendix C — the fifteen breaks, as exact replacements

Save this block as `scratch-s291/s291_breaks.py`. Each row is (name, file, old, new, test file, test that must go red). It plants one, runs that test file, restores the file's bytes, and prints every test that failed.

```python
"""Plant each S291 break in a committed tree, run the named test, restore.

Usage: python s291_breaks.py <tree> [out-file]. The tree must be committed and clean.
"""
import subprocess
import sys
from pathlib import Path

tree = Path(sys.argv[1]).resolve()
PY = sys.executable
PM = "agents/deliberator/context_pm.py"
SRC = "scripts/deliberation_prompt_sources.py"
COMP = "scripts/compile_deliberation_prompts.py"
JUDGE = "kernel/deliberation_judge_prompt.py"
A = "tests/test_reward_risk_is_a_disclosed_figure.py"
B = "tests/test_judge_rules_on_the_order.py"
ART = "tests/test_deliberation_prompt_pipeline.py"
BREAKS = [
    ("B1", PM, "    if not _is_disclosure_only(gate):\n", "    if True:\n", A, "test_a_disclosed_ratio_is_not_a_passed_gate"),
    ("B2", PM, "        lines.append(REWARD_RISK_RULE)\n", "        pass\n", A, "test_the_rule_is_stated_once_after_the_gates"),
    ("B3", PM, "        lines.append(REWARD_RISK_RULE)\n", "        lines.insert(0, REWARD_RISK_RULE)\n", A, "test_the_rule_is_stated_once_after_the_gates"),
    ("B4", PM, 'return gate.outcome == "passed" and _DISCLOSURE_ONLY in', "return _DISCLOSURE_ONLY in", A, "test_a_gate_that_did_not_pass_is_never_recast"),
    ("B5", PM, '_DISCLOSURE_ONLY in gate.detail.split("; ")', "_DISCLOSURE_ONLY in gate.detail", A, "test_an_enforced_ratio_keeps_its_verdict"),
    ("B6", PM, 'f"{value_label}={gate.value:.4g} ({gate.detail})"', 'f"{value_label}={gate.value:.4g} threshold={gate.threshold:.4g} ({gate.detail})"', A, "test_a_disclosed_ratio_is_not_a_passed_gate"),
    ("B7", PM, '"47,485 decisions from', '"47,000 decisions from', A, "test_the_rules_evidence_is_adr_0027s"),
    ("B8", PM, '"+0.03 % a trade', '"+0.30 % a trade', A, "test_the_rules_evidence_is_adr_0027s"),
    ("B9", "agents/portfolio_manager/settings.py", "min_reward_risk_ratio: float = tunable(\n        0.0,", "min_reward_risk_ratio: float = tunable(\n        0.8,", A, "test_the_rule_states_what_the_code_does"),
    ("B10", JUDGE, "cannot decide the", "may decide the", B, "test_the_judge_is_told_to_rule_on_this_order"),
    ("B11", COMP, 'if role == "judge":\n        examples.extend', 'if role == "never":\n        examples.extend', ART, "test_the_champion_is_its_sources_rebuilt"),
    ("B12", "scripts/deliberation_judge_prompt.json", '\\"ruling\\": \\"overturn\\"', '\\"ruling\\": \\"revise\\"', B, "test_every_ruling_is_demonstrated"),
    ("B13", SRC, '"wrong-price-input",\n        "Buy 10 XYZ at the estimated price of $412.00.",\n        "The latest close in the evidence is $41.20, so the order\'s estimated "\n        "price is ten times the market\'s.",\n        "overturn",', '"wrong-price-input",\n        "Buy 10 XYZ at the estimated price of $412.00.",\n        "The latest close in the evidence is $41.20, so the order\'s estimated "\n        "price is ten times the market\'s.",\n        "uphold",', ART, "test_the_champion_is_its_sources_rebuilt"),
    ("B14", "kernel/deliberation_prompts.py", '"You are the DEFENDER in a decision review. Argue *for* the decision with the "', '"shared-sizing-rule You are the DEFENDER in a decision review. Argue *for* the decision with the "', B, "test_the_contrast_cases_reach_only_the_judge"),
    ("B15", "agents/deliberator/prompt_recipe.py", "    deliberation_guided_render,\n    deliberation_judge_prompt,\n    deliberation_program,\n    deliberation_prompts,\n    dspy_engine,\n)\n\n#:", "    deliberation_guided_render,\n    deliberation_program,\n    deliberation_prompts,\n    dspy_engine,\n)\n\n#:", B, "test_the_judge_prompt_is_in_the_recipe"),
]
lines, red = [], 0
for name, rel, old, new, test_file, test_name in BREAKS:
    path = tree / rel
    original = path.read_bytes()
    text = original.decode("utf-8")
    if old not in text:
        lines.append(f"{name} NOT PLANTED: pattern absent in {rel}")
        continue
    path.write_bytes(text.replace(old, new).encode("utf-8"))
    try:
        run = subprocess.run(
            [PY, "-m", "pytest", test_file, "--no-cov", "-q", "-p", "no:cacheprovider", "--tb=no"],
            cwd=tree, capture_output=True, text=True, encoding="utf-8", errors="replace",
            env={**__import__("os").environ, "PYTHONPATH": "."}, timeout=120,
        )
    finally:
        path.write_bytes(original)
    failed = [x.split(" ")[1].split("::")[-1] for x in run.stdout.splitlines() if x.startswith(("FAILED", "ERROR"))]
    hit = any(test_name in x for x in failed)
    red += hit
    lines.append(f"{name} {'RED' if hit else 'GREEN!'} expected {test_name}; failed: {failed}")
lines.append(f"{red} of {len(BREAKS)} breaks red on their named test")
out = "\n".join(lines)
print(out)
if len(sys.argv) > 2:
    Path(sys.argv[2]).write_text(out + "\n", encoding="utf-8")
```
