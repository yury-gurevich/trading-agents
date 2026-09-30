<!-- Agent: planning | Role: sprint handover -->
# Sprint 245 — Every fact the referee is told about our code is pinned to the code

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-245-every-fact-the-referee-is-told-is-pinned-to-the-code`
**Status:** BUILT — 2026-09-30 by a cloud session on `claude/sprint-245-referee-facts-5co3h4`, not merged (Closeout below)
**Version:** *next available PATCH at merge*
**Effort:** M
**Decisions:** [DL-250](../design-log.md) (the measurement and the direction) · work-queue **96** · new `DLIB-NEV-09` · `DRIFT-092`

> **Why this bump kind.** No new capability. The referee was always meant to argue from true facts
> about this system, and its prompts told it a false one. Removing it and pinning the rest is a fix,
> as S206's `DLIB-NEV-08` was (`0.98.04`).

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/deliberator/laws/laws.md` | The deliberator's **locked constitution** (v1.9) | **LOCKED.** This sprint owes one new clause (below). Any other clause you believe is wrong is a `drift-register.md` row plus a report, never a quiet edit |
| `agents/deliberator/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Add the new row; read the rows for `DLIB-OBS-06`/`DLIB-OBS-07` (prompt cache, recipe digest) |
| `agents/provider/laws/laws.md` | `PROV-OUT-09` (the pooled extreme-move guard) | **Read-only.** Your pooled-sigma pin tests behaviour this clause governs; do not change it |
| `docs/laws/*.md` | Conventions, ledger, drift register | `drift-register.md` is the one law-adjacent file you may append to |

Binding sections here: **`DLIB-NEV-08`** (the precedent: a rendered verdict must name the check that
produced it), **`DLIB-OBS-06`** and **`DLIB-OBS-07`** (the system prompt is hashed and cached; changing
it moves both digests by design), **`PROV-OUT-09`**.

### The rule

1. **Before writing code**, read every law file in the map below, whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, record it and add a `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Yes — a new guarantee.** No `contracts/` change. The deliberator gains
**`DLIB-NEV-09`**: *never tells a debate role how this system's code behaves unless a test pins that
statement to the code it describes.* That owes, in this unit of work: the clause in `laws.md`
(v1.9 → **v1.10**, Changelog line), a `test-plan.md` row, the ID cited in the proving tests'
docstrings, the rollup in **both** `docs/laws/ledger.md` and `docs/laws/INDEX.md` (deliberator is
**23 / 56** at spec time; let `make ci` tell you the new number), and **`DRIFT-092`** for the false
fact that shipped (take the next free number if `DRIFT-092` is taken when you start).

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `kernel/deliberation_prompts.py` (champion role prompts) | `agents/deliberator/laws/laws.md` + `test-plan.md` | `DLIB-NEV-09` (new); `DLIB-OBS-06`/`-07` (the prompt is hashed and cached) |
| `scripts/compile_deliberation_prompts.py`, `scripts/deliberation_eval.py`, the three `scripts/deliberation_*_prompt.json`, `scripts/deliberation_golden.json` | same; ADR-0010 (eval-gated prompts) | ADR-0010: a prompt change must not break the golden firewall |
| Pin for pooled sigma (reads `agents/provider/domain/integrity.py`) | `agents/provider/laws/laws.md` | `PROV-OUT-09` (read-only) |
| Pins for sizing, Alpha158, LightGBM (read PM, analyst, forecaster code) | `agents/portfolio_manager/laws/laws.md`, `agents/analyst/laws/laws.md` | read-only: you assert what they do, you change nothing there |

⚠️ **The one invariant: no runtime behaviour changes except the text of the challenger and judge
system prompts.** No change to the defender prompt, the debate flow, parsing, models, effort, rounds,
the context renderer, or any agent other than through those two strings. If your change would touch
anything else, stop and report.

---

## Goal

At merge, every statement the champion challenger and judge prompts make about how *this system's*
code behaves is true today and is pinned by a test that reads the code it describes. The two
statements that are false or stale are gone from the prompts, the case library they were compiled
from, the calibration text, the committed artifacts and the golden file. Re-running the compile
pipeline reproduces the champion prompts byte for byte, so the next compile cannot bring a falsehood
back or silently double the prompt.

## Why (context)

The challenger and judge prompts carry a *"Preserve these distinctions"* list and eight worked
examples, compiled on 2026-07-08 (S119, promoted S121) from the Class-1 case library in
`scripts/deliberation_eval.py`. **One distinction was false on the day it was written.** The
calendar-staleness case says *"Our staleness gate counts CALENDAR days, not trading sessions
(DL-10)"*, but S87 had already made it count trading sessions three days earlier. The case even cites
DL-10, the decision that fixed it. The challenger prompt then tells the model that calendar-day
counting *"is the decision flaw under test"*, and it is used: the challenger has attacked live orders
with it, quoting the planted sentence nearly word for word, on nights that followed no long weekend.
The name-correlation case is stale for a different reason: the portfolio now has a correlation-cluster
gate and a per-sector name cap, so its decision can no longer reach the referee at all.

### Measured, 2026-09-30 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| The staleness gate counts trading sessions | `max_staleness_days` `unit="sessions"`, *"excludes weekends + NYSE holidays (DL-10), not calendar days"* (`agents/provider/settings.py:53`) | *[measured 2026-09-30]* read in code |
| When the fix and the false case landed | fix `d00739e0` **2026-06-22** (S87); case added `17f7f3e5` **2026-06-25** | *[measured]* `git log` on both files |
| Where the false claim lives | `CHALLENGER_SYSTEM` + `JUDGE_SYSTEM` (`kernel/deliberation_prompts.py:24`, `:116`, text at `:34-43`, `:67-74`, `:124`, `:151-159`); `_CLASS1_CALIBRATION` / `_CHALLENGER_CALIBRATION` (`scripts/compile_deliberation_prompts.py:34`, `:43`); the case tuple (`scripts/deliberation_eval.py:70-79`); all three `scripts/deliberation_*_prompt.json`; `scripts/deliberation_golden.json` (`passing` + `fractions`); the fake debate text in `scripts/compare_deliberation_prompts.py:80` | *[measured]* `grep -n -i calendar` |
| Live use of the false claim | **180 of 936** recorded debate turns mention calendar-day staleness; **150** assert calendar counting; **0** state session counting; challenger **169**, defender **11**; in **18 of 38** runs that carry transcript text, **2026-08-07 → 2026-09-29** | *[measured 2026-09-30, read-only on the spine]* regexes over every `DeliberationRun.transcript`. Denominator: runs whose transcript carries text |
| The name-correlation case is stale | `correlated_cluster_pct` (S210 / ADR-0030) and `max_names_per_sector` = **3** now run in the PM; "sector" is Finnhub's `finnhubIndustry` (`agents/provider/fundamentals_parse.py:46`), not a GICS sector | *[measured]* the `sched-2026-09-28` TXN packet shows both gates; code read |
| The compile pipeline is not idempotent after promotion | re-running `compile_artifacts` today gives a **13,023**-char challenger prompt vs the **6,764**-char champion (judge **12,490** vs **6,341**); `"Compiled calibration"` and `"Examples:"` appear **twice** | *[measured 2026-09-30]* `compile_artifacts(..., dspy_module=types.SimpleNamespace())` into a temp dir. Cause: `_ROLE_INSTRUCTIONS` (`scripts/compile_deliberation_prompts.py:53`) starts from the **promoted** constants, not from the hand-written bases |
| Promoted constants equal the committed artifacts | challenger and judge: **byte-identical**; defender: **not promoted** (artifact 6,940 chars, live constant 434) | *[measured]* compared in Python |
| The other four distinctions are true today | pooled sigma: `_outliers` pools one session's cross-section, 8σ default (`integrity.py:109`, `settings.py:46`); fixed fraction: `size_quantity(portfolio_value, max_position_pct, est_price)` (`agents/portfolio_manager/domain/sizing.py:16`), one `settings.max_position_pct` per run (`agents/portfolio_manager/run.py:77`); Alpha158: `alpha158_pillar_weight` default **0.00**, no pack override; LightGBM: no module in scanner/analyst/PM/deliberator/execution references `contracts.forecaster` | *[measured]* code read + grep |
| A lone +9 % open-to-close move does not trip the guard | ≈ **5.1σ** at 98 names × ±1.5 %; a −30 % move ≈ **8.95σ** trips | *[computed, not run]* population σ including the mover; your pin makes it run |
| The golden firewall's models are not production's | golden frozen 2026-07-08 on `gpt-5.5` debaters + `claude-opus-4-8` judge; **production runs `claude-opus-5` for all three roles** | *[measured]* `LLMCall.model` since 2026-09-20. **Out of scope here**, filed under work-queue 97 |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first** (A1, A2, A7 below): red on current `main`, pasted.
2. **Make the pipeline rebuild the champion from its base.** Move the hand-written base prompts and
   the calibration text into a new pack-side module, **`scripts/deliberation_prompt_sources.py`**
   (`Agent: tooling`), and make `_ROLE_INSTRUCTIONS` start from those bases, never from the kernel
   constants. Recover each base from the champion text: it is everything before
   `" Compiled calibration from the existing Class-1 library"`. For the judge, the sentence
   *"If the Challenger catches a grounded implementation-specific flaw from the evidence, do not
   uphold the decision."* is **added by the pipeline** (`scripts/compile_deliberation_prompts.py:53`),
   so it is not part of the base. **Prove it before changing any content:** with today's case library
   and calibration, the rebuilt challenger and judge prompts are byte-identical to today's constants.
   Commit that on its own; it is the characterisation step.
3. **Remove the false and stale content**, everywhere it lives (see the Measured table):
   - the `calendar-staleness` and `name-correlation` cases from `_CLASS1`;
   - *"calendar-day staleness is not trading-session freshness;"* and *"the sector cap is not a
     name-correlation penalty;"* from the distinctions list;
   - every calendar sentence from `_CHALLENGER_CALIBRATION`. **Keep its first sentence**
     (*"For each attack, explicitly state why the exact flaw should force REVISE or OVERTURN rather
     than being dismissed as a policy preference."*): it is a steer, not a fact about our code, and
     changing steers is work-queue 75's experiment, not this fix;
   - both case names from `scripts/deliberation_golden.json` (`passing` and `fractions`), plus a
     `"corrected"` key saying what was removed, when, and why (the loader reads only `passing`,
     `fractions`, `model`, `judge`, `date`; `scripts/deliberation_gate.py:160-176`);
   - the words for the removed cases from the fake debate text at
     `scripts/compare_deliberation_prompts.py:80` (a frozen-baseline file at **363** lines: it may
     not grow).
4. **Regenerate and re-promote.** Re-run the pipeline for all three roles, stamped with the
   production model (`--debate-model claude-opus-5 --judge-model claude-opus-5`) and a version string
   naming S245. Replace `CHALLENGER_SYSTEM` and `JUDGE_SYSTEM` with the regenerated `system_prompt`s,
   updating their `# Promoted from …` comments. **Do not promote the defender** (it has never been
   promoted; DL-186). The compile is a deterministic string join (`kernel/dspy_optimizer.py:33` only
   imports `dspy` to prove it is installed), so the pipeline's injectable fake `dspy_module` gives
   byte-identical output. Say which path you used.
5. **Pin every remaining fact** (A3–A6) and **the completeness rule** (A7) as a new test module,
   `tests/test_deliberation_prompt_facts.py`.
6. **Law cycle** (`DLIB-NEV-09`, v1.10, test-plan row, rollups, `DRIFT-092`).

### Out of scope (do NOT build this sprint)

- **The defender's grounding, persona, or example balance** (work-queue **75**). The judge still sees
  only `revise` examples, and that remains 75's measured question.
- **Re-freezing the golden on production models.** It needs paid LLM calls and a baseline design;
  it belongs to work-queue **97**.
- **Class-2 examples** (`concentration`, `event-risk`). They are textbook hypotheticals, not claims
  about our code. Note that `event-risk`'s premise (earnings in 2 days) cannot reach the referee,
  because the scanner excludes names within `earnings_exclusion_days` = 5
  (`agents/scanner/settings.py:70`). Record it in Return notes for item 75, and change nothing.
- **Any DSPy Signature, glossary, name change or recorded reasoning** (work-queue **97**).
- **Moving the champion prompts out of `kernel/`** (an ADR-0012 platform/pack leak): name it in Return
  notes, and do not move them.
- **No other `laws.md` edit**, and no ADR reversal.

### The road not taken (LAW-06)

- **Rewrite the two cases as true ones.** Rejected: a rewritten case is a new eval case whose
  effect must be measured, and new cases belong to item 75/97's balanced set. S245 only removes what
  is false.
- **Remove all hard-coded distinctions and examples now** (DL-186's circularity). Rejected: that is a
  prompt redesign whose effect on the verdict distribution is exactly item 75's experiment, so doing
  it here would ship an unmeasured behaviour change inside a fix.
- **Pin by string match only** (assert the sentence exists in a docstring). Rejected: a pin must fail
  when the *code* changes, so behavioural claims (sigma, sizing) are pinned by behaviour.
- **Edit the kernel constants by hand and leave the pipeline alone.** Rejected: the pipeline is how
  the falsehood arrived, and today it would double the prompt on the next run. A champion that cannot
  be rebuilt from its sources cannot be kept honest.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Where the bases and calibration live.** Recommended: `scripts/deliberation_prompt_sources.py`
   (pack tooling). The kernel keeps only the promoted champion literals, because the runtime never
   imports `scripts/` or `dspy`. Alternative: kernel constants. Weigh ADR-0012 (no trading facts in
   the substrate) and say why.
2. **The shape of the pin registry.** One mapping from each distinction sentence and each Class-1 case
   name to a check function, so the completeness test can compare sets.
3. **The golden correction.** Edit the golden (remove the two invalid cases, record why) or re-freeze
   it. Recommended: edit and record. A re-freeze is paid, and the golden's models are not
   production's anyway (Measured table).

🪤 **Take the next free DL number, then re-check it at merge.** At spec time the newest is **DL-250**,
so yours is likely **DL-251**. The log has historic duplicates, and a branch cut before another DL
lands will collide.

---

## Blast radius — measured 2026-09-30

| What | Detail |
| --- | --- |
| Files changed | `kernel/deliberation_prompts.py` (**199**, will shrink); `scripts/compile_deliberation_prompts.py` (**185**); new `scripts/deliberation_prompt_sources.py`; `scripts/deliberation_eval.py` (**195**, shrinks); `scripts/deliberation_{defender,challenger,judge}_prompt.json` (regenerated); `scripts/deliberation_golden.json` (**26**); `scripts/compare_deliberation_prompts.py` (**363**, frozen baseline: may not grow); `tests/test_deliberation_prompt_pipeline.py` (its temp golden names `calendar-staleness`, line 71); new `tests/test_deliberation_prompt_facts.py`; `agents/deliberator/laws/laws.md`, `test-plan.md`; `docs/laws/ledger.md`, `docs/laws/INDEX.md`, `docs/laws/drift-register.md`; `docs/design-log.md`; `pyproject.toml` |
| Agents affected | **deliberator** (all three identities read the kernel champion prompts). No agent imports another |
| Contract change? | **No** |
| Graph vocabulary change? | **No** |
| New env keys / tunables | **None** |
| Deploy implication | **Image-only retag** |
| Rollback | Retag the fleet back to the tag live before the deploy (**`s244`** at spec time). A retag does **not** undo the `DeliberationRun` and `LLMCall` rows written under the new prompts. They carry the new `system_prompt_hash` and `prompt_recipe_hash` (`DLIB-OBS-06`/`-07`), which is correct and marks them as a different prompt. Nothing else is written |

🪤 **Both digests move, by design.** `kernel.deliberation_prompts` is in `PROMPT_MODULES`
(`agents/deliberator/prompt_recipe.py`), so `PROMPT_RECIPE_HASH` changes, and every challenger and
judge `LLMCall` gets a new `system_prompt_hash`. Debates before and after this merge are **not**
comparable replays. That is the point, not a regression.

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md`.
3. **Plant the failing tests first** (A1, A2, A7) and watch them fail. Paste the red output.
4. **Characterise:** bases + pipeline fix with **no content change**, so A2 goes green with today's
   text. Commit.
5. **Remove** the false and stale content (Scope 3), **regenerate and re-promote** (Scope 4).
   A1 and A7 go green once the pins exist.
6. **Pins** A3–A6.
7. **Law cycle** (`DLIB-NEV-09`, v1.10, test-plan row, rollups, `DRIFT-092`).
8. **Prove the guards can fail (DL-70)**, each planted, red, pasted, restored:
   (a) put the calendar sentence back into `CHALLENGER_SYSTEM` → A1 red;
   (b) add a fifth distinction with no pin → A7 red;
   (c) set `alpha158_pillar_weight`'s default to `0.10` → A5 red;
   (d) make `_outliers` judge each name against its own history, or drop the default to `4.0` → A3 red;
   (e) edit one character of `JUDGE_SYSTEM` → A2 red.
9. **`make ci` green**, redirected to a file, never piped.
10. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 No false fact reaches a role | the three champion constants and the three committed artifact JSONs (`system_prompt` **and** every example's `inputs`/`output`/`rationale`) | none contains, case-insensitively: `counts CALENDAR days`, `calendar-day staleness`, `calendar-day counting`, `post-holiday recheck`, `GICS-SECTOR cap`, `NO name-correlation`, `"calendar-staleness"`, `"name-correlation"`. **Red on `main` today.** Cites `DLIB-NEV-09` |
| A2 | 🎯 The champion is its sources, rebuilt | `compile_artifacts(..., dspy_module=<fake>)` into `tmp_path` | the rebuilt challenger and judge `system_prompt` are **byte-identical** to `CHALLENGER_SYSTEM` / `JUDGE_SYSTEM` **and** to the committed artifacts. **Red on `main` today** (13,023 vs 6,764) |
| A3 | Pooled sigma is one session's cross-section | `validate_bars` (`agents/provider/domain/integrity.py:23`), 99 tickers, one session each, open 100: 98 with close alternating 101.5 / 98.5, plus **X** | **X** close 109 (+9 %) → **not** in `anomalous_tickers`; **X** close 70 (−30 %) → **in** `anomalous_tickers`; default `ProviderSettings()`. Cites `PROV-OUT-09` (read-only) and `DLIB-NEV-09` |
| A4 | Sizing is a fixed fraction, not volatility-adjusted | `size_quantity` | `size_quantity(portfolio_value=Decimal(100000), max_position_pct=Decimal("0.01"), est_price=Decimal(50)) == 20`, and its parameters are exactly `{portfolio_value, max_position_pct, est_price}`. **Prefer** a PM-level pair if an existing fixture builds a buy decision cheaply: two buys, same price, beta 0.5 vs 2.5 and `atr_pct` 1.0 vs 6.0 → the same quantity. Say which you did |
| A5 | Alpha158 contributes nothing | `AnalystSettings()` and `orchestration/packs/trading_tunables.json` | `alpha158_pillar_weight == 0.0`, and no env block in the pack has a key containing `ALPHA158` |
| A6 | LightGBM does not feed the live decision | AST or text scan of every non-test module under `agents/scanner`, `agents/analyst`, `agents/portfolio_manager`, `agents/deliberator`, `agents/execution` | none imports `contracts.forecaster` or names `ShadowPrediction` |
| A7 | 🎯 Every stated fact has a pin | the distinctions list parsed from `CHALLENGER_SYSTEM` and `JUDGE_SYSTEM` (the text after `Preserve these distinctions:` up to the first `.`, split on `;`), and every `"case": "<name>"` in their examples | the distinction set **equals** the pin registry's distinction set; every example case is a `_CLASS2` name or a **pinned** `_CLASS1` name; every `_CLASS1` name is pinned. **Red on `main` today** (six distinctions, zero pins). Cites `DLIB-NEV-09` |
| A8 | 🪤 The golden names only live cases | `scripts/deliberation_golden.json` | every name in `passing` and `fractions` is a current `_CLASS1` case name |

Input → expected output, one row per case class, for the two behavioural pins:

| Pin | Input | Expected |
| --- | --- | --- |
| A3 | 98 × ±1.5 % + one +9 % (open-to-close) | `anomalous_tickers` = `()` |
| A3 | 98 × ±1.5 % + one −30 % | `anomalous_tickers` = `("X",)` |
| A4 | 100,000 × 0.01 ÷ 50 | `20` |
| A4 | 100,000 × 0.01 ÷ 333 | `3` (floor, whole shares) |

---

## Success factors

- [ ] A1–A8 pass; A1, A2 and A7 were pasted **red** on `main` first.
- [ ] Re-running the pipeline reproduces the promoted challenger and judge prompts byte for byte (A2).
- [ ] The defender prompt, the debate flow and every other agent are unchanged (the ⚠️ invariant).
- [ ] `DLIB-NEV-09` added, v1.10 Changelog, test-plan row, rollups in `ledger.md` **and** `INDEX.md`,
      `DRIFT-092`.
- [ ] Design decisions recorded with rejected alternatives under the DL you took.
- [ ] All five DL-70 plants: planted, red, pasted, restored.
- [ ] Every touched module < 200 lines; the two frozen-baseline files did not grow.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **A2 can pass for the wrong reason.** If the rebuilt prompt is compared with a constant that was
itself regenerated in the same step, A2 proves nothing. Take the characterisation step (Steps, 4)
against today's **unchanged** constants and paste it before you change any content.
🪤 **Doubling.** Any instruction built from `CHALLENGER_SYSTEM` or `JUDGE_SYSTEM` re-nests the
calibration and examples. After this sprint, nothing in `scripts/` may read those two constants
except the tests that compare against them.
🪤 **"Calendar" is not banned.** Legitimate text may say *calendar-gated* or *calendar window*. A1
bans the specific false claims, not the word.
🪤 **A3's move is open-to-close on each name's newest session** (`_anomalous_tickers`, DL-247), not
close-to-close. Build the bars that way, or the pin tests something the guard does not do.
🪤 **Section and case counts shrink.** `tests/test_deliberation_prompt_pipeline.py:39` asserts
`len(examples) == len(_CLASS1) + 2`. That follows automatically; do not hard-code 8 or 6 anywhere.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`). The new pack
  module lives in `scripts/`, never `kernel/`.
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `kernel/deliberation_prompts.py` **199**, `scripts/deliberation_eval.py` **195**,
  `scripts/compile_deliberation_prompts.py` **185**, `scripts/deliberation_gate.py` **230** (frozen),
  `scripts/compare_deliberation_prompts.py` **363** (frozen).
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- `make ci` **every step** green, **100.00 % coverage floor**. Never through a pipe.
- Version bump: PATCH. **`uv.lock` is owed to the planner** (a cloud session cannot re-resolve it).
- Secrets never through the worktree. **State which tree you ran in.** No proof here needs `.env`.

---

## Sequencing after merge

1. Planner: `uv lock`, Windows `make ci`, push, **`make gate-ran`** from the proving worktree, with the
   printed SHA checked against `git rev-parse HEAD`.
2. Merge to `main` and push; post-merge CodeQL.
3. **Live check (planner, before the deploy, needs `.env`):** replay the **challenger's round-1 turn
   only** on the **10** most recent recorded propositions whose recorded challenger turn asserted
   calendar-day counting. Use the recorded defender r1 text as the transcript and `claude-opus-5`,
   once with the old champion and once with the new: **20 calls**. Count assertions of calendar-day
   counting (the DL-250 regex). Expected: old reproduces it, new never states it. Budget stated
   before running; estimated **≈ $1–2** at Opus 5 rates. Record it in
   `docs/laws/functionality-checks.md`.
4. **Deploy:** image-only retag. Record `s244` as the rollback tag.
5. **F1 (first scheduled run after the retag):** challenger and judge `LLMCall` rows carry a new
   `system_prompt_hash` and a new `prompt_recipe_hash`, and **0** transcript turns assert calendar-day
   counting. Read-only.

---

## Handover — paste this to the Claude cloud session

```text
Sprint 245 — every fact the referee is told about our code is pinned to the code.
Spec: docs/sprints/sprint-245-every-fact-the-referee-is-told-is-pinned-to-the-code.md on main
(read ALL of it, then CLAUDE.md). Repo: yury-gurevich/trading-agents.

Branch: sprint-245-every-fact-the-referee-is-told-is-pinned-to-the-code, cut from main. Never main.
If your session forces another branch name, use it and name it in the handback.
You have NO .env, NO gh, NO Azure and no route to download.pytorch.org. Every proof here is a unit
test on code in the repo; nothing needs the network or the database. You cannot run `make gate-ran`:
it is owed to the planner. Leave uv.lock untouched and say so. Take the next free DL (DL-251 at
spec time; re-check on main) and the next free DRIFT (DRIFT-092 at spec time).

This handover is complete: nobody will send you follow-up messages. If something in the spec is wrong
or blocked, record it in the handback (Return notes, "not done") and stop; do not wait.

What and why: the challenger and judge system prompts (kernel/deliberation_prompts.py) state six
"distinctions" about how our code behaves and carry eight worked examples, compiled from the Class-1
case library (scripts/deliberation_eval.py). One distinction is false: "our staleness gate counts
CALENDAR days" - it has counted trading sessions since S87 (2026-06-22), and the case was written
2026-06-25. The challenger uses it: 150 of 936 recorded debate turns assert it, never correctly. A
second case (name-correlation) is stale: the PM now has a correlation-cluster gate and a per-sector
name cap. And the compile pipeline starts from the already-promoted constants, so re-running it today
doubles the prompt (13,023 vs 6,764 chars).

MUST RULE before any code: read, whole, agents/deliberator/laws/laws.md + test-plan.md,
agents/provider/laws/laws.md (PROV-OUT-09, read-only), docs/laws/conventions.md,
docs/laws/drift-register.md. Fill the Law reading record first.

Law-cycle answer: YES, a new guarantee. Deliberator v1.10: new DLIB-NEV-09 "never tells a debate
role how this system's code behaves unless a test pins that statement to the code it describes".
Changelog line, test-plan row, clause ID in the A1/A7 docstrings, rollups in docs/laws/ledger.md AND
docs/laws/INDEX.md (let make ci give the number), DRIFT-092 for the false fact that shipped.

Build, in this order:
1. Red first: A1 (no false phrase in the constants or the committed artifacts), A2 (the pipeline
   rebuilds the champion byte for byte), A7 (every distinction and Class-1 example case has a pin).
   Paste the red output.
2. Characterise: move the hand-written bases and the calibration text into a new
   scripts/deliberation_prompt_sources.py; the base is the champion text before
   " Compiled calibration from the existing Class-1 library"; the judge's "If the Challenger catches
   ... do not uphold the decision." is added by the pipeline, not part of the base. Make
   _ROLE_INSTRUCTIONS start from the bases. With NO content change, A2 goes green against today's
   constants. Commit that alone.
3. Remove: the calendar-staleness and name-correlation cases from _CLASS1; "calendar-day staleness is
   not trading-session freshness;" and "the sector cap is not a name-correlation penalty;" from the
   distinctions; every calendar sentence from _CHALLENGER_CALIBRATION (KEEP its first sentence); both
   names from the golden's passing + fractions, plus a "corrected" key saying what/when/why; the
   removed cases' words from the fake text at scripts/compare_deliberation_prompts.py:80 (frozen at
   363 lines, may not grow).
4. Regenerate all three artifacts (--debate-model claude-opus-5 --judge-model claude-opus-5, a
   version naming S245; the fake dspy_module is byte-identical, since the compile is a string join)
   and re-promote the challenger and judge constants from them. Do NOT promote the defender.
5. Pins A3-A6 in tests/test_deliberation_prompt_facts.py, exactly as the spec's tables say (A3 uses
   validate_bars with open-to-close bars; A4 size_quantity, or the PM-level pair if cheap - say which).
6. Law cycle. 7. DL-70 plants (a)-(e): each red, pasted, restored. 8. make ci redirected to a file,
   exit 0, 100.00 %.

DO NOT:
- change the defender prompt, the debate flow, parsing, models, effort, rounds, the context renderer,
  or any agent's behaviour: only the challenger and judge prompt text changes.
- rewrite the removed cases as new true ones, touch the Class-2 examples, or remove the remaining
  distinctions (item 75's experiment).
- re-freeze the golden or make any real LLM call.
- move the champion prompts out of kernel/, or let anything in scripts/ read CHALLENGER_SYSTEM or
  JUDGE_SYSTEM except the tests comparing against them.
- ban the word "calendar": ban the specific false claims.
- grow any module past 200, or the two frozen-baseline files at all; # noqa to bypass a rule.
- claim a live proof or GATE PROVEN: the replay check, the gate, the deploy and F1 are the planner's.
- pin a version: PATCH, next available at merge.

Handback — the planner returns it if ANY of these is missing:
[ ] Law reading record filled, including the law-cycle answer and contradictions/silences found.
[ ] Test plan results: A1-A8, each with final test name, file, PASS, clause IDs cited.
[ ] The red run of A1, A2, A7 pasted before any change; the characterisation commit's A2 green run.
[ ] Each of the five DL-70 plants: what was planted, its red output, restored.
[ ] The new champion challenger and judge prompt lengths, and a diff summary of what left them.
[ ] Module line counts for every file touched (all < 200; the two frozen files not grown).
[ ] make ci: the file, exit code, passed/skipped, coverage 100.00 %, dependency audit, detect-secrets.
[ ] Exactly how uv.lock was touched (untouched and owed).
[ ] The design decisions under the DL you took, with rejected alternatives.
[ ] Return notes: scope held or moved; what you disagreed with after reading the laws; the
    event-risk premise note for item 75; the kernel/pack leak note.
[ ] Status: BUILT on the spec, and this sprint's README.md row leads with BUILT, in the same commit.
[ ] Owed items named: uv lock, make gate-ran, Windows make ci, the 20-call replay check, retag, F1.
Commit on the branch and PUSH it, then stop: no merge. Anything not met: "not done", never a
Result: for work not done.
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

Filled 2026-09-30 09:50 AEST, before the first code change, in the claude.ai cloud container (branch
`claude/sprint-245-referee-facts-5co3h4`, cut from `main` `02f3e7da`). Every file below was read whole.

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| `kernel/deliberation_prompts.py` (champion challenger + judge) | `agents/deliberator/laws/laws.md` (v1.9) + `test-plan.md` | `DLIB-NEV-09` (new); `DLIB-OBS-06` (frozen prompt offered to the cache); `DLIB-OBS-07` (recipe digest); `DLIB-IDM-02` (both prompt halves hashed); `DLIB-IDN-03` (one image, three identities); `DLIB-NEV-08` (the precedent) | **Yes.** `kernel.deliberation_prompts` is in `PROMPT_MODULES`, so *any* text in that module moves `PROMPT_RECIPE_HASH`, including text no model reads. That settles where the bases go (D1 in DL-251): compile-only text in the kernel would make `DLIB-OBS-07` report a new renderer for an edit no role ever sees. The champions stay frozen literals, so `OBS-06`'s cache-marked block and `IDM-02`'s hashing are untouched; both digests move by design |
| `scripts/compile_deliberation_prompts.py`, `scripts/deliberation_eval.py`, new `scripts/deliberation_prompt_sources.py`, the three `scripts/deliberation_*_prompt.json`, `scripts/deliberation_golden.json`, `scripts/compare_deliberation_prompts.py` | deliberator book; `docs/decisions/0010-llm-interaction-quality-gate.md`; `docs/decisions/0012-platform-domain-separation.md` (with its S232 correction) | `DLIB-NEV-09`; ADR-0010 D1 (the frozen set gates a prompt change); ADR-0012 (no trading content added to the substrate) | **Yes.** `check_robust` reports every golden-passing name missing from a candidate run as *regressed*, so a golden still naming `calendar-staleness` would trip the firewall on every future check: the golden edit is load-bearing and A8 pins it. ADR-0012's S232 correction already lists `kernel/deliberation_prompts.py` as deferred residue; this sprint adds no trading text to `kernel/` (the module shrinks) |
| A3 pin (reads `agents/provider/domain/integrity.py`) | `agents/provider/laws/laws.md` (v1.6), **read-only** | `PROV-OUT-09` (newest bar, open-to-close, that session's pooled population mean and σ, fewer than two moves abstains, √(n−1) ceiling); `PROV-FAIL-02`; PARAM `max_daily_move_sigma` = 8.0 | **Yes.** The ceiling means a pool of 66 moves or fewer cannot exclude anything at 8σ, so the pin must use one session of more than 66 names (99) or it proves nothing; the bars are open-to-close on one session, as the clause says |
| A4 pin (reads PM sizing) | `agents/portfolio_manager/laws/laws.md` (v1.10), **read-only** | `PM-IDN-01` (sizes to whole shares from the estimated entry price); `PM-NEV-05` (whole shares, truncated); `PM-NEV-06` / `PM-NEV-08` (label cap vs correlation penalty) | **Yes, on the removal.** `PM-NEV-06` says in its own words that the sector cap *"is not the correlation penalty"*, so the distinction sentence being removed is literally true of the cap. What is false is the case built on it (*"GICS-SECTOR cap with NO name-correlation … penalty"*: the labels are not GICS, DRIFT-041, and `PM-NEV-08` is a measured correlation penalty). The sentence exists only to serve that case, so it goes with it, as the spec says (Return notes) |
| A5 pin (reads analyst settings, the tunables pack) | `agents/analyst/laws/laws.md` (v1.6), **read-only** | `ANLZ-IDN-01` (*"optional Alpha158 pillar (off by default, weight = 0.00)"*); PARAM `alpha158_pillar_weight` | No |
| A6 pin (scans five agents for the forecaster contract) | `agents/forecaster/laws/laws.md` (v1.8), **read-only** | `FORE-NEV-01` / `FORE-NEV-02` (never a binding signal; never gates a recommendation, sizing or exit) | No |
| The law cycle (`laws.md` v1.10, `test-plan.md`, rollups, `DRIFT-092`) | `docs/laws/conventions.md`, `docs/laws/drift-register.md`, `docs/laws/ledger.md`, `docs/laws/INDEX.md` | §2 (next free ID: `DLIB-NEV-09`), §3 (green = a passing functional test citing the ID), §4 (amendment: version + changelog), §5 (the clause names no other agent), §7 (law before test), §7a (the summary mirrors the clause), §9 (one drift row) | **Yes.** §7 wants the law before the test, and the spec plants tests citing `DLIB-NEV-09` before its law cycle. The clause text is fixed by the spec's law-cycle answer before any test exists, and the clause lands in the same commit as the tests that cite it |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** Yes, a new
guarantee; no `contracts/` change. Deliberator v1.9 → **v1.10** adds `DLIB-NEV-09`: *never tells a
debate role how this system's code behaves unless a test pins that statement to the code it
describes.* It names no other agent (§5). Rollup: 23 / 56 → 24 / 57 at spec-time counts; `make ci`
gives the final number.

**Contradictions found between a law and this spec:** none between a law book and the spec. Three
tensions, recorded and not stopping the build:

1. **Conventions §7 vs the spec's order.** §7 says a needed test with no law gets its law first.
   The spec's step 3 plants tests citing `DLIB-NEV-09` before step 7's law cycle. The clause is
   decided (its text is in the spec) before any test is written, and the tests that cite it are not
   committed before the clause is.
2. **ADR-0010 D1 (an ADR, not a law book).** *"Every change to … prompt … must pass the frozen set
   before promotion."* This sprint promotes new challenger and judge prompts without a firewall run:
   the spec forbids real LLM calls and the container has no `.env`. The golden's models are not
   production's (item 97). Named for the planner in Return notes; the 20-call replay is a different
   check.
3. **The spec's A7 parse rule.** *"Up to the first `.`"* stops inside *"Alpha158 weight 0.00"*.
   The parse runs to the first sentence-ending period (a `.` followed by whitespace).

**Laws found silent where a decision was needed:**

1. **The deliberator book never governed whether what a role prompt says about this system is true.**
   That silence is how the calendar-day sentence was promoted on 2026-07-08 and never re-checked.
   `DLIB-NEV-09` fills it; `DRIFT-092` records what shipped under it.
2. **`DLIB-NEV-09`'s reach over existence claims.** Every role prompt, the defender's included, names
   three *"system parameter[s]"* as examples (`max_daily_move_sigma`, `base_min_confidence`,
   `max_sector_pct`). That is a claim about this system (the parameters exist), not about behaviour.
   Decided in DL-251: read the clause as covering it, and pin each name to the live settings field.
   No prompt text changes; the defender stays untouched.

**Clauses that were ⬜ and are now proven:** none. `DLIB-NEV-09` is new, added and proven in the same
unit of work. No existing deliberator clause changes status.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_no_false_fact_reaches_a_role` | `tests/test_deliberation_prompt_truth.py` | PASS (red on `main` first: 34 hits) | `DLIB-NEV-09` |
| A2 | `test_the_champion_is_its_sources_rebuilt` | `tests/test_deliberation_prompt_pipeline.py` | PASS (red on `main` first: `(13023, 2, 2) == (6764, 1, 1)`; green on the unchanged constants at the characterisation commit) | `DLIB-NEV-09` |
| A3 | `test_pooled_sigma_is_one_sessions_cross_section` | `tests/test_deliberation_prompt_facts.py` | PASS | `DLIB-NEV-09`, `PROV-OUT-09` (read-only) |
| A4 | **Both.** `test_sizing_is_a_fixed_fraction_not_volatility_adjusted` (`size_quantity`: 20, the floor 3, exactly three parameters) and `test_a_high_beta_buy_gets_the_same_size_as_a_low_beta_one` (the PM-level pair through `evaluate_recommendations`, using the existing `recommendation` / `cash_portfolio` helpers) | `tests/test_deliberation_prompt_facts.py` | PASS | `DLIB-NEV-09`, `PM-IDN-01`, `PM-NEV-05` (read-only) |
| A5 | `test_alpha158_contributes_nothing` | `tests/test_deliberation_prompt_facts.py` | PASS | `DLIB-NEV-09`, `ANLZ-IDN-01` (read-only) |
| A6 | `test_lightgbm_does_not_feed_the_live_decision` | `tests/test_deliberation_prompt_facts.py` | PASS | `DLIB-NEV-09`, `FORE-NEV-02` (read-only) |
| A7 | `test_every_stated_fact_has_a_pin[challenger]`, `[judge]` | `tests/test_deliberation_prompt_facts.py` | PASS (red on `main` first: six distinctions, zero pins) | `DLIB-NEV-09` |
| A8 | `test_the_golden_names_only_live_cases` | `tests/test_deliberation_prompt_truth.py` | PASS | `DLIB-NEV-09`, ADR-0010 |

**Tests added beyond the plan:**

- `tests/test_deliberation_prompt_truth.py::test_no_script_builds_from_the_promoted_champions`
  (`DLIB-NEV-09`, DL-251 D5): the doubling guard, an AST scan of `scripts/` for `CHALLENGER_SYSTEM` /
  `JUDGE_SYSTEM`. It was red on `main` (`compile_deliberation_prompts.py`) in the same red run.
- `tests/test_deliberation_prompt_truth.py::test_every_parameter_a_role_is_shown_is_a_live_setting`
  `[defender]`, `[challenger]` (`DLIB-NEV-09`, DL-251 D5): the three example parameter names every
  prompt cites are exactly `max_daily_move_sigma`, `base_min_confidence` (`ProviderSettings`) and
  `max_sector_pct` (`PortfolioManagerSettings`), each a live field. No prompt text changed.
- `tests/test_deliberation_prompt_truth.py::test_the_same_nine_percent_is_excluded_on_a_calm_session`
  (`PROV-OUT-09`): the pooled-sigma example's *"one 9% name does not trip it"* holds on an ordinary
  session only; at ±0.5 % the same +9 % is 8.66σ and excluded (Return notes).
- Edited: `tests/test_deliberation_prompt_artifacts.py` (its two promotion tests pinned the S119/S121
  version strings; they now read S245's) and `tests/test_deliberation_prompt_pipeline.py` (its
  temporary golden no longer names `calendar-staleness`). New helper `tests/deliberation_fact_probes.py`
  (not collected) holds the probes the pins read the code with, so every pin and the registry stay in
  one module under 150 lines.

---

## Closeout — evidence

**Status:** BUILT — 2026-09-30, on `claude/sprint-245-referee-facts-5co3h4` (cloud session), not merged.

**Tree the proofs ran in (and `.env` present?):** the claude.ai cloud container's clone,
`/home/user/trading-agents`, branch `claude/sprint-245-referee-facts-5co3h4`. The session forced that
name; the spec's is `sprint-245-every-fact-the-referee-is-told-is-pinned-to-the-code`. Cut from `main`
`02f3e7da`. **No `.env`**, no `gh`, no Azure. Dependencies from `uv sync --frozen` (dev group, no
extras; `dspy` is not installed). Every command ran frozen (`uv run --frozen`, `UV_FROZEN=1`). No LLM
call was made and no network was needed for any proof.

**Result:** `CHALLENGER_SYSTEM` (4,818 chars) and `JUDGE_SYSTEM` (4,713) tell the referee to *"Preserve
these distinctions: pooled cross-sectional sigma is not per-name volatility; fixed-fraction sizing is
not volatility-adjusted; Alpha158 weight 0.00 contributes nothing; LightGBM shadow output does not feed
the live decision"*, with six worked examples: Class-2 `concentration` and `event-risk`, Class-1
`pooled-sigma`, `fixed-fraction-size`, `alpha158-weight-zero` and `lightgbm-shadow`. No constant and
no committed artifact says the staleness gate counts calendar days or that the portfolio has no
name-correlation penalty (A1). Every distinction and every Class-1 example is registered to a pin test
that reads the code it describes (A7, pins A3–A6). `compile_artifacts` rebuilds both champions and all
three committed artifacts byte for byte from `scripts/deliberation_prompt_sources.py` and the case
library, with the calibration and the examples once each (A2), and no `scripts/` module reads the
champions. The golden names only the four live cases and records the correction (A8). Deliberator laws
v1.10 carry `DLIB-NEV-09`, 🟩, **24 / 57** (was 23 / 56). The defender prompt, the debate flow, parsing,
models, effort, rounds and the context renderer are unchanged: the only runtime text that moved is the
two champion strings (the ⚠️ invariant), and with it, by design, `PROMPT_RECIPE_HASH` and the challenger
and judge `system_prompt_hash`.

**What left the prompts (diff summary):** challenger 6,764 → **4,818** chars (−1,946), judge 6,341 →
**4,713** (−1,628), eight examples → six in each. Both lost two distinctions (*"calendar-day staleness is
not trading-session freshness;"*, *"the sector cap is not a name-correlation penalty;"*) and two worked
examples (`calendar-staleness`, `name-correlation`: inputs, expected output and rationale). The
challenger also lost the three calendar sentences of its calibration (*"For the calendar staleness
pattern … that is the decision flaw under test. Do not frame calendar staleness … post-holiday recheck
…"*); its first sentence, a steer, stays. The defender artifact (never promoted) went 6,940 → 5,192 by
the same removals; `DEFENDER_SYSTEM` is unchanged (434 chars). Stamps: `claude-opus-5` for all three,
version `2026-09-30-s245-v6-<role>-claude-opus-5`, through the injected fake `dspy_module` (DL-251 D4).
Measured against `main`'s constants with `difflib`: both champions changed **by deletion only** (opcodes
`equal` and `delete`, no insertion or rewrite), the challenger in 3 spans (1,946 chars) and the judge in
2 (1,628); `DEFENDER_SYSTEM` and `_DEFINE_THEN_JUSTIFY` are byte-identical to `main`'s.

**Files changed:** `kernel/deliberation_prompts.py` (the two champions re-promoted, docstring);
`scripts/deliberation_prompt_sources.py` (new); `scripts/compile_deliberation_prompts.py`;
`scripts/deliberation_eval.py`; `scripts/deliberation_{defender,challenger,judge}_prompt.json`
(regenerated); `scripts/deliberation_golden.json`; `scripts/compare_deliberation_prompts.py` (line 80's
fake text only); tests: new `tests/test_deliberation_prompt_facts.py`,
`tests/test_deliberation_prompt_truth.py`, `tests/deliberation_fact_probes.py`, edited
`tests/test_deliberation_prompt_pipeline.py`, `tests/test_deliberation_prompt_artifacts.py`; laws:
`agents/deliberator/laws/laws.md` + `test-plan.md` (v1.10), `docs/laws/ledger.md`, `docs/laws/INDEX.md`,
`docs/laws/drift-register.md` (DRIFT-092); docs: `docs/design-log.md` (DL-251), this spec,
`docs/sprints/README.md`, `docs/sprints/INDEX.md`. **Not touched:** `pyproject.toml`, `uv.lock`,
`scripts/deliberation_gate.py`, any agent's code.

**Design decisions:** [DL-251](../design-log.md) — D1 the bases and calibration live in
`scripts/deliberation_prompt_sources.py` (kernel rejected: ADR-0012 residue, and compile-only text in a
`PROMPT_MODULES` module would move the recipe digest for text no role reads); D2 the registry is two
dicts of pin test functions compared by set equality; D3 the golden is edited and the edit recorded, not
re-frozen; D4 regeneration through the fake `dspy_module`; D5 the clause's reach over the example
parameter names, the scope of A2 (three artifacts, calibration and examples once each) and the static
doubling guard. Rejected alternatives are in each decision; *"Measured while pinning"* records the
pooled-sigma caveat.

**Proof — the red run first** (A1, A2, A7 and the doubling guard, written before any other change,
against the unchanged `main` code at `7065e719`, which differs from `main` `02f3e7da` only by the two
documents above):

```text
FFFFF                                                                    [100%]
=================================== FAILURES ===================================
______________________ test_no_false_fact_reaches_a_role _______________________
tests/test_deliberation_prompt_truth.py:74: in test_no_false_fact_reaches_a_role
    assert hits == []
E   assert [('CHALLENGER...leness'), ...] == []
E
E     Left contains 34 more items, first extra item: ('CHALLENGER_SYSTEM', '"calendar-staleness"')
E     Use -v to get more diff
______________ test_no_script_builds_from_the_promoted_champions _______________
tests/test_deliberation_prompt_truth.py:92: in test_no_script_builds_from_the_promoted_champions
    assert readers == []
E   AssertionError: assert ['compile_del...n_prompts.py'] == []
E
E     Left contains one more item: 'compile_deliberation_prompts.py'
E     Use -v to get more diff
_________________ test_every_stated_fact_has_a_pin[challenger] _________________
tests/test_deliberation_prompt_facts.py:49: in test_every_stated_fact_has_a_pin
    assert _distinctions(prompt) == set(DISTINCTION_PINS)
E   AssertionError: assert {'Alpha158 we...tion penalty'} == set()
E
E     Extra items in the left set:
E     'calendar-day staleness is not trading-session freshness'
E     'Alpha158 weight 0.00 contributes nothing'
E     'fixed-fraction sizing is not volatility-adjusted'
E     'LightGBM shadow output does not feed the live decision'
E     'the sector cap is not a name-correlation penalty'
E     'pooled cross-sectional sigma is not per-name volatility'
E     Use -v to get more diff
___________________ test_every_stated_fact_has_a_pin[judge] ____________________
tests/test_deliberation_prompt_facts.py:49: in test_every_stated_fact_has_a_pin
    assert _distinctions(prompt) == set(DISTINCTION_PINS)
E   AssertionError: assert {'Alpha158 we...tion penalty'} == set()
E
E     Extra items in the left set:
E     'calendar-day staleness is not trading-session freshness'
E     'Alpha158 weight 0.00 contributes nothing'
E     'fixed-fraction sizing is not volatility-adjusted'
E     'LightGBM shadow output does not feed the live decision'
E     'the sector cap is not a name-correlation penalty'
E     'pooled cross-sectional sigma is not per-name volatility'
E     Use -v to get more diff
___________________ test_the_champion_is_its_sources_rebuilt ___________________
tests/test_deliberation_prompt_pipeline.py:51: in test_the_champion_is_its_sources_rebuilt
    assert _shape(rebuilt[role].system_prompt) == _shape(champion), role
E   AssertionError: challenger
E   assert (13023, 2, 2) == (6764, 1, 1)
E
E     At index 0 diff: 13023 != 6764
E     Use -v to get more diff
=========================== short test summary info ============================
FAILED tests/test_deliberation_prompt_truth.py::test_no_false_fact_reaches_a_role
FAILED tests/test_deliberation_prompt_truth.py::test_no_script_builds_from_the_promoted_champions
FAILED tests/test_deliberation_prompt_facts.py::test_every_stated_fact_has_a_pin[challenger]
FAILED tests/test_deliberation_prompt_facts.py::test_every_stated_fact_has_a_pin[judge]
FAILED tests/test_deliberation_prompt_pipeline.py::test_the_champion_is_its_sources_rebuilt
5 failed in 0.47s
```

A1's 34 hits by source:

```text
34 distinct (source, claim) hits
  CHALLENGER_SYSTEM: 8 of 8 banned claims
  JUDGE_SYSTEM: 6 of 8 banned claims
  deliberation_challenger_prompt.json: 8 of 8 banned claims
  deliberation_defender_prompt.json: 6 of 8 banned claims
  deliberation_judge_prompt.json: 6 of 8 banned claims
  DEFENDER_SYSTEM: 0
```

**Proof — the green run.** The characterisation step, before any content changed: the working tree that
became `41bd823c`, with `kernel/deliberation_prompts.py` byte-identical to `main`'s:

```text
HEAD 7065e719; kernel/deliberation_prompts.py blob 48e68cd9d32e8567b03693bdf8352584fabb7045 (HEAD: 48e68cd9d32e8567b03693bdf8352584fabb7045)
============================= test session starts ==============================
collecting ... collected 2 items
tests/test_deliberation_prompt_pipeline.py::test_the_champion_is_its_sources_rebuilt PASSED [ 50%]
tests/test_deliberation_prompt_truth.py::test_no_script_builds_from_the_promoted_champions PASSED [100%]
============================== 2 passed in 0.41s ===============================
```

Every S245 test module on the final tree:

```text
HEAD 2aea53b5
tests/test_deliberation_prompt_truth.py::test_no_false_fact_reaches_a_role PASSED
tests/test_deliberation_prompt_truth.py::test_no_script_builds_from_the_promoted_champions PASSED
tests/test_deliberation_prompt_truth.py::test_the_golden_names_only_live_cases PASSED
tests/test_deliberation_prompt_truth.py::test_every_parameter_a_role_is_shown_is_a_live_setting[defender] PASSED
tests/test_deliberation_prompt_truth.py::test_every_parameter_a_role_is_shown_is_a_live_setting[challenger] PASSED
tests/test_deliberation_prompt_truth.py::test_the_same_nine_percent_is_excluded_on_a_calm_session PASSED
tests/test_deliberation_prompt_facts.py::test_pooled_sigma_is_one_sessions_cross_section PASSED
tests/test_deliberation_prompt_facts.py::test_sizing_is_a_fixed_fraction_not_volatility_adjusted PASSED
tests/test_deliberation_prompt_facts.py::test_a_high_beta_buy_gets_the_same_size_as_a_low_beta_one PASSED
tests/test_deliberation_prompt_facts.py::test_alpha158_contributes_nothing PASSED
tests/test_deliberation_prompt_facts.py::test_lightgbm_does_not_feed_the_live_decision PASSED
tests/test_deliberation_prompt_facts.py::test_every_stated_fact_has_a_pin[challenger] PASSED
tests/test_deliberation_prompt_facts.py::test_every_stated_fact_has_a_pin[judge] PASSED
tests/test_deliberation_prompt_pipeline.py::test_the_champion_is_its_sources_rebuilt PASSED
tests/test_deliberation_prompt_pipeline.py::test_compile_deliberation_prompts_writes_role_artifacts PASSED
tests/test_deliberation_prompt_pipeline.py::test_compile_deliberation_prompts_can_write_one_role PASSED
tests/test_deliberation_prompt_pipeline.py::test_compare_deliberation_prompts_fake_path_passes PASSED
tests/test_deliberation_prompt_artifacts.py::test_parse_prompt_artifact_rejects_invalid_json[payload0] PASSED
tests/test_deliberation_prompt_artifacts.py::test_parse_prompt_artifact_rejects_invalid_json[payload1] PASSED
tests/test_deliberation_prompt_artifacts.py::test_parse_prompt_artifact_rejects_invalid_json[payload2] PASSED
tests/test_deliberation_prompt_artifacts.py::test_parse_prompt_artifact_rejects_invalid_json[payload3] PASSED
tests/test_deliberation_prompt_artifacts.py::test_parse_prompt_artifact_rejects_invalid_json[payload4] PASSED
tests/test_deliberation_prompt_artifacts.py::test_parse_prompt_artifact_accepts_examples PASSED
tests/test_deliberation_prompt_artifacts.py::test_load_and_validate_one_deliberation_artifact PASSED
tests/test_deliberation_prompt_artifacts.py::test_ensure_deliberation_artifact_rejects_wrong_task PASSED
tests/test_deliberation_prompt_artifacts.py::test_ensure_deliberation_artifact_requires_model_and_prompt[ -prompt-model] PASSED
tests/test_deliberation_prompt_artifacts.py::test_ensure_deliberation_artifact_requires_model_and_prompt[m- -system_prompt] PASSED
tests/test_deliberation_prompt_artifacts.py::test_load_directory_and_compose_prompts PASSED
tests/test_deliberation_prompt_artifacts.py::test_prompts_from_artifacts_can_overlay_one_role PASSED
tests/test_deliberation_prompt_artifacts.py::test_promoted_judge_prompt_matches_committed_artifact PASSED
tests/test_deliberation_prompt_artifacts.py::test_promoted_challenger_prompt_matches_committed_artifact PASSED
tests/test_deliberation_prompt_artifacts.py::test_prompts_from_artifacts_rejects_unknown_role PASSED
============================== 32 passed in 0.77s ==============================
```

**Guards planted (DL-70)** — each planted in the tracked file, run red, restored with `git checkout`,
`git status --porcelain` empty, then green again:

(a) the calendar sentence put back into `CHALLENGER_SYSTEM` → A1 red:

```text
=== PLANT (a): calendar sentence prepended to CHALLENGER_SYSTEM ===
F                                                                        [100%]
=================================== FAILURES ===================================
______________________ test_no_false_fact_reaches_a_role _______________________
tests/test_deliberation_prompt_truth.py:90: in test_no_false_fact_reaches_a_role
    assert hits == []
E   AssertionError: assert [('CHALLENGER...LENDAR days')] == []
E
E     Left contains one more item: ('CHALLENGER_SYSTEM', 'counts CALENDAR days')
FAILED tests/test_deliberation_prompt_truth.py::test_no_false_fact_reaches_a_role
1 failed in 0.38s
pytest exit=1
restored: []
.                                                                        [100%]
1 passed in 0.35s
after restore exit=0
```

(b) a fifth distinction with no pin, added to `CLASS1_CALIBRATION`, then regenerated and re-promoted so
A2 and A1 stay green → A7 red on both prompts (2 failed, 2 passed):

```text
=== PLANT (b): fifth distinction 'the reward-risk floor is disclosure-only' added to CLASS1_CALIBRATION, artifacts regenerated, champions re-promoted ===
FF..                                                                     [100%]
=================================== FAILURES ===================================
_________________ test_every_stated_fact_has_a_pin[challenger] _________________
tests/test_deliberation_prompt_facts.py:143: in test_every_stated_fact_has_a_pin
    assert distinctions(prompt) == set(DISTINCTION_PINS)
E   AssertionError: assert {'Alpha158 we...closure-only'} == {'Alpha158 we...e volatility'}
E
E     Extra items in the left set:
E     'the reward-risk floor is disclosure-only'
___________________ test_every_stated_fact_has_a_pin[judge] ____________________
tests/test_deliberation_prompt_facts.py:143: in test_every_stated_fact_has_a_pin
    assert distinctions(prompt) == set(DISTINCTION_PINS)
E   AssertionError: assert {'Alpha158 we...closure-only'} == {'Alpha158 we...e volatility'}
E
E     Extra items in the left set:
E     'the reward-risk floor is disclosure-only'
FAILED tests/test_deliberation_prompt_facts.py::test_every_stated_fact_has_a_pin[challenger]
FAILED tests/test_deliberation_prompt_facts.py::test_every_stated_fact_has_a_pin[judge]
2 failed, 2 passed in 0.43s
pytest exit=1
restored: []
...........                                                              [100%]
11 passed in 0.98s
after restore exit=0
```

(c) `alpha158_pillar_weight`'s default set to `0.10` → A5 red:

```text
=== PLANT (c): alpha158_pillar_weight default 0.00 -> 0.10 (agents/analyst/settings.py) ===
F                                                                        [100%]
=================================== FAILURES ===================================
______________________ test_alpha158_contributes_nothing _______________________
tests/test_deliberation_prompt_facts.py:93: in test_alpha158_contributes_nothing
    assert AnalystSettings().alpha158_pillar_weight == 0.0
E   assert 0.1 == 0.0
E    +  where 0.1 = AnalystSettings(rsi_period=14, macd_fast=12, macd_slow=26, macd_signal=9, bollinger_window=20, bollinger_sigma=2.0, sm... rs_window=20, relative_strength_weight=0.2, signal_diversity_slack=5.0, max_top_signals=5, alpha158_pillar_weight=0.1).alpha158_pillar_weight
E    +    where AnalystSettings(rsi_period=14, macd_fast=12, macd_slow=26, macd_signal=9, bollinger_window=20, bollinger_sigma=2.0, sm... rs_window=20, relative_strength_weight=0.2, signal_diversity_slack=5.0, max_top_signals=5, alpha158_pillar_weight=0.1) = AnalystSettings()
FAILED tests/test_deliberation_prompt_facts.py::test_alpha158_contributes_nothing
1 failed in 0.42s
pytest exit=1
restored: []
.                                                                        [100%]
1 passed in 0.35s
after restore exit=0
```

(c2, beyond the spec) an `ANALYST_ALPHA158_PILLAR_WEIGHT` key in the pack's analyst block → A5 red on its
second half:

```text
=== PLANT (c2, beyond the spec): ANALYST_ALPHA158_PILLAR_WEIGHT=0.10 in the analyst env block of orchestration/packs/trading_tunables.json ===
F                                                                        [100%]
=================================== FAILURES ===================================
______________________ test_alpha158_contributes_nothing _______________________
tests/test_deliberation_prompt_facts.py:94: in test_alpha158_contributes_nothing
    assert [key for key in keys(pack) if "ALPHA158" in key.upper()] == []
E   AssertionError: assert ['ANALYST_ALP...ILLAR_WEIGHT'] == []
E
E     Left contains one more item: 'ANALYST_ALPHA158_PILLAR_WEIGHT'
FAILED tests/test_deliberation_prompt_facts.py::test_alpha158_contributes_nothing
1 failed in 0.39s
pytest exit=1
restored: []
```

(d1) `max_daily_move_sigma`'s default dropped to `4.0` → A3 red (the +9 % is now excluded):

```text
=== PLANT (d1): max_daily_move_sigma default 8.0 -> 4.0 (agents/provider/settings.py) ===
F                                                                        [100%]
=================================== FAILURES ===================================
_______________ test_pooled_sigma_is_one_sessions_cross_section ________________
tests/test_deliberation_prompt_facts.py:49: in test_pooled_sigma_is_one_sessions_cross_section
    assert anomalous(109.0) == ()
E   AssertionError: assert ('X',) == ()
E
E     Left contains one more item: 'X'
FAILED tests/test_deliberation_prompt_facts.py::test_pooled_sigma_is_one_sessions_cross_section
1 failed in 0.35s
pytest exit=1
restored: []
.                                                                        [100%]
1 passed in 0.38s
after restore exit=0
```

(d2) `_anomalous_tickers` rewritten to judge each name against its own history → A3 red (the −30 % is no
longer excluded, a one-bar history abstains):

```text
=== PLANT (d2): _anomalous_tickers judges each name against its OWN history (moves grouped by ticker, not by session) ===
F                                                                        [100%]
=================================== FAILURES ===================================
_______________ test_pooled_sigma_is_one_sessions_cross_section ________________
tests/test_deliberation_prompt_facts.py:50: in test_pooled_sigma_is_one_sessions_cross_section
    assert anomalous(70.0) == ("X",)
E   AssertionError: assert () == ('X',)
E
E     Right contains one more item: 'X'
FAILED tests/test_deliberation_prompt_facts.py::test_pooled_sigma_is_one_sessions_cross_section
1 failed in 0.35s
pytest exit=1
restored: []
.                                                                        [100%]
1 passed in 0.37s
after restore exit=0
```

(e) one character of `JUDGE_SYSTEM` edited by hand → A2 red:

```text
=== PLANT (e): one character of JUDGE_SYSTEM edited by hand ('Weigh' -> 'weigh') ===
F                                                                        [100%]
=================================== FAILURES ===================================
___________________ test_the_champion_is_its_sources_rebuilt ___________________
tests/test_deliberation_prompt_pipeline.py:52: in test_the_champion_is_its_sources_rebuilt
    assert rebuilt[role].system_prompt == champion, role
E   AssertionError: judge
E   assert 'You are the ... confirmation' == 'You are the ... confirmation'
E
E     Skipping 4663 identical trailing characters in diff, use -v to show
E     - You are the JUDGE in a decision review. weigh the
E     ?                                         ^
E     + You are the JUDGE in a decision review. Weigh the
E     ?                                         ^
FAILED tests/test_deliberation_prompt_pipeline.py::test_the_champion_is_its_sources_rebuilt
1 failed in 0.35s
pytest exit=1
restored: []
.                                                                        [100%]
1 passed in 0.33s
after restore exit=0
```

**Module line counts** (as `check_module_size.py` counts them; `main` in brackets; all under 200):

| Module | Lines |
| --- | --- |
| `kernel/deliberation_prompts.py` | 155 (199) |
| `scripts/compile_deliberation_prompts.py` | 170 (185) |
| `scripts/deliberation_eval.py` | 180 (195) |
| `scripts/deliberation_prompt_sources.py` | 54 (new) |
| `scripts/compare_deliberation_prompts.py` | 363 (363): frozen baseline, **not grown** |
| `scripts/deliberation_gate.py` | 230 (230): frozen baseline, **untouched** |
| `tests/test_deliberation_prompt_facts.py` | 148 (new) |
| `tests/test_deliberation_prompt_truth.py` | 143 (new) |
| `tests/deliberation_fact_probes.py` | 90 (new) |
| `tests/test_deliberation_prompt_pipeline.py` | 131 (96) |
| `tests/test_deliberation_prompt_artifacts.py` | 168 (167) |

**`make ci`:** `UV_FROZEN=1 make ci > <scratchpad>/make_ci_final.txt 2>&1` in the cloud container's clone
(the scratchpad is session storage, not persisted), on the final tree including this handback: **exit 0**,
all 15 steps. Ruff clean; format 1,489 files; mypy no issues in 1,118 source files; import-linter 5 kept,
0 broken; module size 0 `[FAIL]` (warnings only; `kernel/deliberation_prompts.py` warns at 155, down
from 199); module header; law coverage (deliberator derived **24 / 57**, both rollups agree); PARAM/settings
sync (the two pre-existing PM envelope warnings); sprint status (`docs_seen=250 SPEC=10 BUILT=3
MERGED=237`); markdown links; version scheme; pytest **3,701 passed, 8 skipped, 100.00 %** (19,755
statements, 4,208 branches, none missed); dependency audit *"No unaccepted vulnerabilities; 1 accepted
advisory re-checked"*; detect-secrets passed; untracked secrets *"no untracked files to scan"*.
`UV_FROZEN=1` keeps every step on the committed lock, as CI's `uv sync --frozen` does; an unfrozen
`uv run` would try to re-lock and cannot reach `download.pytorch.org`. The pinned markdownlint hook (not
a `make ci` step) also passes on every changed document.

**`make gate-ran`:** *(planner — owed)*. The container has no `gh`.

**Not met / verified failing:** nothing in the spec's build list is unmet. **Not done (owed, by design):**

- **`uv lock`: not done.** `uv.lock` is untouched (sha256 `313ca0f1…4a38b`, identical to `main`), and so is
  `pyproject.toml` (`0.119.04`): the handover says not to pin a version, the PATCH is the next available
  at merge (`0.119.05` if nothing lands first), and a re-lock needs `download.pytorch.org`, which this
  session cannot reach.
- **`make gate-ran`: not done** (no `gh`). **Windows `make ci`: not done.**
- **The 20-call replay check: not done** (no `.env`; no LLM call is allowed here).
- **The image-only retag (rollback tag `s244`) and F1: not done**; both are the planner's after merge.
- **ADR-0010 D1's firewall run on the new prompts: not done** (paid, and forbidden here); a planner
  decision (Return notes).

---

## Return notes

- **Branch.** The session forced `claude/sprint-245-referee-facts-5co3h4`. Commits: `7065e719` (law
  reading record + DL-251, before any code), `41bd823c` (the characterisation step alone), `2aea53b5`
  (removal, regeneration, re-promotion, pins, law cycle), then this handback. Pushed; not merged.
- **Scope held.** Only the challenger and judge prompt text changed at runtime. Three files outside the
  spec's blast radius, each forced: `tests/test_deliberation_prompt_artifacts.py` (its two promotion
  tests pinned the S119/S121 version strings), the helper `tests/deliberation_fact_probes.py` (keeps the
  pins and their registry in one module under 150 lines), and the `docs/sprints/INDEX.md` row.
  `pyproject.toml` was not bumped (the handover's *"do not pin a version"*; S244's builder did the same).
  `compile_deliberation_prompts.py` gained one `# noqa: E402` for its new import, the file's existing
  `sys.path` idiom (three before it), not a gate bypass.
- **What I read differently from the spec, after reading the laws.**
  1. *"The sector cap is not a name-correlation penalty"* is literally **true**: `PM-NEV-06` says the
     label cap *"is not the correlation penalty"*. It is removed as the spec says, because it existed only
     to serve the stale `name-correlation` example and, alone, points the referee at *"there is no
     correlation penalty"* while `PM-NEV-08` is one. Keeping it as a pinned true distinction would be a
     one-line source change plus a pin, but it is a prompt change whose effect is item 75's to measure.
  2. A7's *"up to the first `.`"* stops inside *"Alpha158 weight 0.00"*; the parse runs to the first
     sentence-ending period (DL-251 D2).
  3. The spec's −30 % figure: measured **8.86σ**, not ≈8.95σ (population σ including the mover). It trips
     either way; the +9 % is 5.11σ as computed.
  4. **ADR-0010 D1** says every prompt change must pass the frozen set before promotion. This sprint
     promotes without a firewall run: real LLM calls are forbidden here, and the golden's models are not
     production's (item 97). Whether the planner runs `deliberation_gate.py --check` before the deploy,
     or accepts the 20-call replay in its place, is the planner's call; this handback does not claim it.
  5. **The pooled-sigma example is true only on an ordinary day.** *"One 9% name does not trip it"*
     holds at ±1.5 % (5.11σ), but among 98 names at ±0.5 % the same move is 8.66σ and is excluded
     (`test_the_same_nine_percent_is_excluded_on_a_calm_session`). The distinction it serves is true
     either way. The text is unchanged (rewording a case is item 75/97's), and this is reported so the
     next case library does not keep an unconditional sentence that is conditional.
- **The event-risk premise, for item 75.** The Class-2 `event-risk` example (*"Earnings are in 2 days and
  the -3% stop is not earnings-gap-aware"*) describes an order the referee should not see: the scanner
  excludes a name whose known next earnings date is within `earnings_exclusion_days` = 5
  (`agents/scanner/settings.py:70`, applied in `agents/scanner/domain/filter_attestation.py:40`). It can
  still arrive when the earnings date is unknown and the filter is recorded as skipped
  (`filter_attestation.py:49`), so it is not impossible, only off the normal path. Changed nothing.
- **The kernel/pack leak.** `kernel/deliberation_prompts.py` still holds trading content in the substrate
  (ADR-0012's S232 correction lists it as deferred residue). S245 moved only the compile-time sources, to
  `scripts/` (pack tooling), and the module shrank 199 → 155 lines. The champions stay: moving them
  renames a module hashed into every `LLMCall`'s recipe digest (`DLIB-OBS-07`). The new module docstring
  names a `scripts/` path in prose; there is no import. `compare_deliberation_prompts.py` and
  `deliberation_gate.py` still read `DEFAULT_DELIBERATION_PROMPTS` to evaluate the champion, never to
  build an instruction.
- **Prompt caching (`DLIB-OBS-06`) still applies.** The API reference gives Claude Opus 5 a 512-token
  minimum cacheable prefix. The new prompts are ~1.1–1.4k tokens (an estimate at 3.5–4.5 chars per token;
  `count_tokens` needs a key), so the cache-marked system block still caches, carrying ~28 % fewer tokens
  per call. F1 can confirm non-zero cache reads on the first challenger and judge calls.
- **Digests.** `PROMPT_RECIPE_HASH` moves because `kernel.deliberation_prompts` is in `PROMPT_MODULES`,
  and the challenger and judge `system_prompt_hash` move with the text. None of the new `scripts/` or
  `tests/` modules is runtime, so none belongs in `PROMPT_MODULES`.
- **Historical records left as they are.** EXP-004, EXP-005, the S119 transcripts and `STATE-03` still
  describe the removed cases as they were; they are dated evidence, not prompts.
- **The compile CLI** cannot run in this container (`dspy` is in the `optimizer` extra), and its defaults
  still read `gpt-5.5` / `claude-opus-4-8` / `2026-07-08-s119-v1`. Unchanged, because the spec asks for
  flags, not new defaults.
- **Owed to the planner:** `uv lock` with the PATCH bump, `make gate-ran` (from the proving worktree,
  SHA checked against `git rev-parse HEAD`), Windows `make ci`, the 20-call replay check (budget first,
  row in `functionality-checks.md`), the image-only retag (rollback `s244`), and F1.
