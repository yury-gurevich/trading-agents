<!-- Agent: planning | Role: sprint handover -->
# Sprint 250 — a replay's excess return comes with an interval and a verdict, and no buy is decided on history the fleet never has

**Phase:** Next leg P17, item E17.5 ([next-leg-plan.md](../next-leg-plan.md)) · work-queue 82
**Branch:** `sprint-250-a-replays-excess-return-comes-with-an-interval-and-a-verdict`
**Status:** SPEC
**Version:** *next available MINOR at merge*
**Effort:** M
**Decisions:** [DL-232](../design-log.md) (what the replay covers) · [DL-257](../design-log.md) (the
planner's design for EXP-014, with the roads not taken) · the builder's decisions go to the **next
free DL** (`DL-258` at spec time) ·
[EXP-014](../research/experiments/EXP-014-does-the-price-only-pipeline-beat-spy-held-at-the-same-exposure.md)
is pre-registered and frozen

> **Why this bump kind.** New capability: the harness gains a rule it did not have, and two commands
> exist that did not (run the experiment's arms, score them into a verdict). `scripts/` ships in no
> image, so there is no deploy.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during this build.** A clause you believe is wrong is a `drift-register.md` row plus a report, never an edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: the reporter's **`OUT`**, the analyst's **`PARAM`**, the provider's **`TRG`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read each agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Read the law-cycle answer below.**
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — expected answer: **NO**

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

Everything lives in `scripts/` and `tests/`. Scripts may import agents (the S235 and S237 precedent);
agents never import scripts or each other. No agent, contract, kernel or orchestration file changes,
so no clause is owed. **If you find you need to edit one, stop and report: the spec is wrong.**

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `scripts/replay_session.py`, `replay_series.py`, `replay_runner.py`, `replay_pipeline.py` (the history rule) | `agents/analyst/laws/laws.md` + `test-plan.md`; `agents/provider/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | The rule's threshold is the analyst's own `required_history_bars` (PARAM `lookback_days`, `min_history_bars`), the number a fleet run's lookback is declared to cover (`PROV-TRG-05`). No number of your own |
| `scripts/replay_verdict*.py` (new): the scorer | `agents/reporter/laws/laws.md` + `test-plan.md` | `RPT-OUT-07`: a return is computed only by `calculate_performance` |
| `scripts/exp014_arms.json`, `scripts/replay_arms*.py` (new) | `agents/analyst/laws/laws.md` (PARAM `relative_strength_weight`) | Each arm's override is a real setting, resolved through `build_effective_settings` |

⚠️ **Two invariants.** (1) **The scorer never computes a return of its own.** Every return in the
report, every yearly row and every bootstrap draw comes out of `calculate_performance`. If you catch
yourself multiplying daily ratios, stop. (2) **The arms, the statistic, the interval and the verdict
rule are EXP-014's Appendix P, and it is frozen.** If the code needs to differ from it, stop and
report; do not adjust either side.

---

## Goal

At merge, two commands exist. One runs each arm of EXP-014 through the S235 harness and records what
it ran on. The other reads the arms and returns the experiment's verdict: the annualised excess return
over exposure-matched SPY with a 95 % interval, the paired differences between arms, the yearly table,
and one of EDGE, EDGE IN A PILLAR or NO EDGE, or a refusal that says why. With the history rule on,
the harness offers the pipeline no line whose window holds fewer bars than the analyst is always given.

## Why (context)

G-EDGE is the decision every later leg waits on (P18A or P18B, then P20's place in the order), and it
needs EXP-014. The harness (S235) and its fidelity check (S237) are merged. What is missing is the
part that turns five replays into a verdict with an interval, by a rule fixed beforehand.

The one ten-year replay that exists is not usable as evidence. It has no interval, and a fifth of its
buys were decided on history the fleet never decides on (measured below).

### Measured, 2026-10-01 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| The smoke replay's result | portfolio +217.9 %, exposure-matched SPY +232.2 %, excess −14.3 pts, 2,698 sessions, 552 buys | *[measured]* its `summary.json` and `fills.csv` in the OneDrive cache (`replays/index-2016-2026-10bps`) |
| Buys decided on fewer than 200 bars | **113 of 552**: 103 in 2016, 3 in 2017, 3 in 2019, 4 in 2020; 57 on fewer than 50; the least on **11** | *[measured]* bars before each buy's fill date, counted per line in `sp500_bars.csv.gz` |
| Why | no line has a bar before 2016-01-04, the replay's first session; **187 of 721** lines have their first bar after 2016 (the year they joined) | *[measured]* first bar date per line |
| The analyst's floor | `min_history_bars` **2**; `required_history_bars(AnalystSettings())` **200**; `lookback_days` 260 | *[measured, run]* |
| The setting cannot be raised to fix it | `min_history_bars` is bounded `≤ 60` | *[measured, read]* `agents/analyst/settings.py:35-44` |
| The harness shows a line every bar inside the declared window | `window_bars(by_line, members, session, days)` keeps `session − days ≤ date ≤ session`; `days` is `declared_lookback_days(...)` | *[measured, read]* `scripts/replay_series.py:77-89`, `scripts/replay_session.py:179-190` |
| Sessions from 2017-01-03 | **2,446** to 2026-09-25; 252 sessions of 2016 precede them | *[measured]* `sp500_sessions.csv.gz` |
| The ablation is one setting | `blended = (1 − w) × technical + w × rs`, `w = relative_strength_weight` (0.20; bounds 0 to 1) | *[measured, read]* `agents/analyst/domain/scoring.py:132-149` |
| Overrides reach the settings by env name | `--set ANALYST_RELATIVE_STRENGTH_WEIGHT=0.0` resolves through `_resolve_key`; an unknown key raises | *[measured, read]* `scripts/replay_settings.py:98-117` |
| Slippage is already a parameter | `run(..., slippage_bps=10)`; `_apply_slippage` moves a buy up and a sell down | *[measured, read]* `scripts/replay_runner.py:38-48`, `scripts/replay_broker.py:124-128` |
| What a replay writes | `equity.csv` (`date, equity_cents, long_cents`), `fills.csv`, `sessions.csv`, `summary.json`; refused inside the worktree | *[measured, read]* `scripts/replay_outputs.py` |
| A rebuilt series reproduces the metric | the smoke run's pairs, re-chained from integer cents starting at 10¹⁴ and passed through `calculate_performance`: portfolio differs by 0, exposure-matched by 2.8 × 10⁻¹⁴ | *[measured, run]* |
| One `calculate_performance` call on 2,698 points | **3.16 ms**, so 10,000 resamples of five arms is about 2.6 minutes | *[measured, run]* the planner's machine, 4 logical cores |
| Stock and SPY bars carry the same adjustment | `adjustment=all` on both | *[measured, read]* `scripts/replay_dataset_sources.py:61`, `scripts/sp500_context.py:55` |
| numpy in the gate's environment | **absent**: core dependencies are `cryptography`, `msgpack`, `pydantic`, `pydantic-settings` | *[measured, read]* `pyproject.toml` |
| What the gate measures in `scripts/` | ruff, format, module size, module header: **yes**. mypy and coverage: **no** (`PKGS` and `[tool.coverage.run] source` omit `scripts`) | *[measured, read]* `Makefile:5`, `pyproject.toml:245-248` |
| One ten-year replay | 84 minutes | *[carried from S235's record, not re-measured]* |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first.** C1, C5 and C6 from the test plan, red, pasted in the Closeout.
2. **The history rule, off by default.** `replay_runner.run(..., require_history=False)` and
   `replay_pipeline.py run --require-history`. With it on, a line that is **not held** is offered to
   the pipeline (its ticker and its bars) only when its visible window holds at least
   `required_history_bars(settings.analyst)` bars. A **held** line is always offered. The
   member-sessions removed are counted as `member_sessions_below_required_history`. With it off, every
   output is what it is today.
3. **The arms.** `scripts/exp014_arms.json` holds exactly Appendix P's five arms. A command runs one
   named arm, or all, through `replay_runner.run` with `--start 2017-01-03` and the rule on, into
   `<out-root>/<arm>/`, and writes an `arm.json` beside the replay's files: the arm's name, slippage
   and overrides, the first and last session, the rule's state, the repo commit, and a checksum prefix
   of each cache file it read.
4. **The scorer.** A command reads `<out-root>`, checks the arms belong together, and writes
   `verdict.json` and `verdict.md` there (outside the worktree) and a summary to stdout:
   - per arm, over the whole window: the `calculate_performance` outputs, and
     `A = ((1 + P/100)^(252/n) − (1 + E/100)^(252/n)) × 100`;
   - per arm, per calendar year, and for the two halves of the window: the same outputs;
   - the 95 % interval of `A` per arm, and of `A(X) − A(base-25)` for each ablation arm, from a
     stationary block bootstrap over session pairs (mean block 20, 10,000 resamples, seed 0), one set
     of index draws for every arm, each resampled series rebuilt and scored by
     `calculate_performance`;
   - the control: a replica earning exactly SPY at `base-25`'s exposure scores `A = 0`, interval [0, 0];
   - the verdict by Appendix P's rule, or a refusal naming the arm and the reason.
5. **Tests on synthetic series only.** No file from the cache and no replay output enters the repo.

### Out of scope (do NOT build this sprint)

- **Running EXP-014**, writing its results, the verdict ADR and the G-EDGE recommendation. The
  planner's, after merge, on the licensed cache.
- **History before a line joined the index.** The right repair for the 187 late lines is to fetch
  their earlier bars. That is a cache rebuild over the network, in `scripts/replay_universe.py`
  (**199** lines). Here the lines are held back and counted.
- **Any file under `agents/`, `contracts/`, `kernel/`, `orchestration/` or `surfaces/`**, and
  `calculate_performance` itself. No tunable, env key, label or property.
- **The fidelity scripts** (`scripts/replay_fidelity*.py`, `scripts/fidelity_export*.py`).
- **numpy, pandas or scipy.** The gate's environment has none.
- **A train/test split or a purge.** Nothing is fitted (DL-257).
- **No `laws.md` edit and no ADR.**

### The road not taken (LAW-06)

Recorded with reasons in [DL-257](../design-log.md). In short:

- **Start the replay on 2016-01-04 with the rule on.** Rejected: ten months of cash in the scored
  window.
- **Raise `ANALYST_MIN_HISTORY_BARS`.** Rejected: bounded at 60, and it would be a setting the fleet
  does not run.
- **Chain the daily ratios inside the bootstrap.** Rejected: a second definition of return.
- **An i.i.d. bootstrap of daily returns.** Rejected: it ignores volatility clustering and a book
  that carries positions across days.
- **A fresh replay per year.** Rejected: each would start in cash, which is not the strategy.
- **A t-test on ten yearly numbers.** Rejected: ten observations.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Where the history rule lives**, and how `replay_session.py` (190 lines) stays under 200.
2. **Whether the new counter is always in `absent_inputs`** (0 when the rule is off) or only when it
   is on. The constraint: no existing test's expected value changes.
3. **The bootstrap's exact draw algorithm and percentile convention.** Both must be deterministic for
   a seed and pinned by a test. State the index arithmetic of the 2.5th and 97.5th percentiles.
4. **What `arm.json` records and what makes an arm refusable**: at least commit, cache checksums,
   sessions and the rule's state. Decide what a worktree with uncommitted changes means.
5. **How a resampled series is rebuilt** for `calculate_performance` (the planner's measurement used
   integer cents from 10¹⁴ and consecutive synthetic dates).
6. **The layout of `verdict.md`.** One page; the verdict and `base-25`'s interval first.

🪤 **Take the next free DL number, then re-check it at merge.** `DL-258` at spec time.

---

## Blast radius — measured 2026-10-01

| What | Detail |
| --- | --- |
| Files changed | `scripts/replay_session.py` (**190**), `replay_series.py` (**133**), `replay_runner.py` (**82**), `replay_pipeline.py` (**53**), `replay_counters.py` (**62**); new `scripts/exp014_arms.json`, `scripts/replay_arms*.py`, `scripts/replay_verdict*.py`; new tests under `tests/`; `docs/design-log.md`; this file and its README row |
| Agents affected | none. Scripts import the analyst's `required_history_bars` and the reporter's `calculate_performance`; nothing imports scripts |
| Contract change? | No |
| Graph vocabulary change? | No |
| New env keys / tunables | None |
| Deploy implication | None: `scripts/` ships in no image |
| Rollback | Revert the merge. Nothing is deployed and nothing is written outside the planner's OneDrive output folder |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Read EXP-014 whole**, then record the design decisions in `docs/design-log.md`.
3. **Plant C1, C5 and C6 first** and watch them fail. Paste the red output.
4. **Implement**: the rule, the arms, the scorer.
5. **Prove the guards can fail (DL-70)** — the six plants in the handover, each red, pasted, restored.
6. **`make ci` green** — every step of the `ci:` target, **redirected to a file, never piped**.
7. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| C1 | 🎯 A line under the required history is not offered | a synthetic cache with a line holding the required bars and one holding fewer; rule on | the day runner receives the first line's ticker and bars only; the counter equals the short line's member-sessions; on the session the short line reaches the bar, it is offered |
| C2 | 🪤 A held line stays visible | a held line whose window falls under the bar (a gap in its bars) | its ticker and bars still reach the day runner; it is not counted |
| C3 | 🪤 The rule off changes nothing | the existing runner fixtures | every existing replay test passes with no expected value edited |
| C4 | The bar is the analyst's own number | an override that changes `required_history_bars` (`ANALYST_SMA_LONG_PERIOD`) | the threshold follows it; no literal bar count in `scripts/` |
| C5 | 🎯 A return comes only from `calculate_performance` | the scorer's `calculate_performance` replaced by a stub with fixed outputs | the headline, every yearly row and every bootstrap draw derive from the stub's values |
| C6 | 🎯 A planted edge is found, and a planted null is not | synthetic arms: portfolio = exposure × SPY + a drift per session, with seeded noise; drift positive, zero, negative | EDGE; NO EDGE read *indistinguishable*; NO EDGE read *behind* |
| C7 | A rebuilt series is faithful | the pairs in their original order | portfolio, exposure-matched and session count equal the original's to 1e-9 |
| C8 | The bootstrap is seeded and blocked | a series tagged by index | same seed, same draws; each resample has the original length; runs of consecutive indices (wrapping) with a mean length near the block setting; another seed differs |
| C9 | Arms are compared on the same days | arm B equal to arm A; arm B = arm A plus a drift | the difference is 0 with interval [0, 0]; then its lower bound is above 0 |
| C10 | The years partition the window | a series across three calendar years, the last partial | each pair in exactly one year; the product of `(1 + P_year)` equals `1 + P_total`, and the same for exposure-matched, to 1e-9; the partial year is labelled |
| C11 | The verdict rule | intervals given directly | EDGE; EDGE IN A PILLAR only when both of its conditions hold (each alone is NO EDGE); NO EDGE *behind*; NO EDGE *indistinguishable* |
| C12 | 🪤 Arms that do not belong together give no verdict | a missing arm; a different commit; a different cache checksum; different sessions; the rule off in one; a gap session | a refusal naming the arm and the reason, and no verdict |
| C13 | The control | an arm's own exposure series | the replica scores `A = 0`, interval [0, 0]; a failing control refuses the verdict |
| C14 | The manifest is Appendix P | the committed `exp014_arms.json` and the scorer's defaults | exactly five arms with Appendix P's names, slippage and overrides; each override resolves through `build_effective_settings`; block 20, 10,000 resamples, seed 0 |
| C15 | Outputs stay out of the repo and are byte-stable | an out-root inside the worktree; scoring twice | refused; identical bytes |
| C16 | The arms command records what it ran | `replay_runner.run` faked | one named arm runs with its slippage, overrides, start and the rule on; `arm.json` holds the fields decision 4 chose; an unknown arm is refused |

---

## Success factors

- [ ] With the rule on, no line under `required_history_bars` is offered unless held (C1, C2, C4).
- [ ] With the rule off, no existing replay test changed an expected value (C3).
- [ ] The scorer returns EDGE on a planted edge and NO EDGE on a planted null (C6).
- [ ] Every return in the scorer comes from `calculate_performance` (C5).
- [ ] `scripts/exp014_arms.json` and the scorer's defaults equal Appendix P (C14).
- [ ] C1–C16 pass; C1, C5 and C6 were red first, and the red output is pasted.
- [ ] Design decisions recorded with rejected alternatives.
- [ ] Law-cycle question answered No, with the reason.
- [ ] Each of the six guards planted, watched to fail, restored — stated per guard.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

**Owed to the planner, not the builder:** `uv lock` with the MINOR bump, Windows `make ci`,
`make gate-ran` from the proving worktree, the merge, and the live checks. **F1** (on the licensed
cache, after merge): a three-month replay of `base-25` with the rule on decides **0** buys on fewer
than 200 bars and reports the removed member-sessions; the same command with the rule off, on the
merged code and on the commit before it, writes byte-identical files. **F2:** EXP-014 itself, once
E17.4's fidelity verdict reads PASS.

---

## Traps

🪤 **Coverage and mypy do not see `scripts/`.** The gate's 100.00 % says nothing about your code, and
a type error there passes. The tests and the six plants are the proof. Ruff, the module-size block
and the module-header check do apply.
🪤 **`replay_session.py` is at 190 lines.** A parameter, a call and a counter can cross 200. Move
`_visible_bars` out, or put the filter in `replay_series.py`, before you add.
🪤 **A rule that is on by default empties every existing replay test.** Their fixtures hold a handful
of bars. The rule is opt-in, and C3 is how you know.
🪤 **The window is a calendar slice.** A line's "visible bars" are those inside the declared lookback,
about 203 at most. Count those, not every bar the cache holds for the line.
🪤 **`n` is session pairs, not points.** 2,446 points make 2,445 pairs. Take `n` from
`performance_sessions`.
🪤 **Keep unit tests small.** One `calculate_performance` call over ten years costs about 3 ms; use a
few hundred pairs and a few hundred resamples in tests, and leave 10,000 as the command's default.
🪤 **Byte-stable means sorted keys, fixed rounding and no set or dict ordering in the output.** The
random source is `random.Random(seed)`, never the module-level functions.
🪤 **A drift test that passes by luck.** In C6 choose the drift and the noise so the result is far
from the boundary, and say in the test why the numbers were chosen.
🪤 **No real data in the repo.** Not a cache row, not a replay output, not a line name with prices.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass a rule.
  📌 Current sizes: `replay_session.py` **190**, `replay_series.py` **133**, `replay_runner.py`
  **82**, `replay_pipeline.py` **53**, `replay_counters.py` **62**, `replay_outputs.py` **80**,
  `replay_settings.py` **145**, `replay_universe.py` **199** (do not touch).
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers. The history bar is the analyst's function; the block length, resample count and
  seed are named defaults that equal Appendix P.
- Faults, not silent failure: a refusal names what is wrong.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — `make ci | tail` reports *`tail`'s* exit code. Redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it (the planner's, see below).
- Secrets never through the worktree — a worktree has **no `.env`** and no cache. **State which tree
  you ran in.**
- 🪤 `make ci` does not run markdownlint and the commit hook does. Leave a blank line before and
  after every fenced code block, including inside list items.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving** and check the printed SHA
   against `git rev-parse HEAD`.
2. Merge to `main` locally and push. 🪤 Check you are not on the branch already.
3. **Post-merge CodeQL** on `main`, and the branch's open alerts against the last merged branch's
   (`sprint-249-a-runs-market-window-ends-on-its-as-of`, 131 open).
4. **F1** on the cache. No deploy.
5. **F2, EXP-014:** re-run the fidelity check; on PASS run the five arms (two at a time), score them,
   write sections 6–8 and the run record, then the verdict ADR and one G-EDGE recommendation for the
   operator.

---

## Handover — paste this to the Claude cloud session

```text
Sprint 250 — a replay's excess return comes with an interval and a verdict, and no buy is decided on
history the fleet never has (next leg P17, E17.5).
Spec: docs/sprints/sprint-250-a-replays-excess-return-comes-with-an-interval-and-a-verdict.md on main
(read ALL of it, then CLAUDE.md). Then read, whole:
docs/research/experiments/EXP-014-does-the-price-only-pipeline-beat-spy-held-at-the-same-exposure.md
and DL-257 in docs/design-log.md. Repo: yury-gurevich/trading-agents.

Branch: sprint-250-a-replays-excess-return-comes-with-an-interval-and-a-verdict, cut from main. Never
main. If your session forces another branch name, use it and name it in the handback.
You have NO .env, NO gh, NO replay cache (it is licensed data outside the repo) and no route to
download.pytorch.org. Every proof is a unit test on synthetic series. You cannot run `make gate-ran`
or the experiment: both are owed to the planner. Leave pyproject.toml's version and uv.lock untouched
and say so. Take the next free DL (DL-258 at spec time; re-check on main).

This handover is complete: nobody will send you follow-up messages. If something in the spec is wrong
or blocked, record it in the handback (Return notes, "not done") and stop; do not wait.

What and why: the operator's next decision (is there an edge) waits on EXP-014: five ten-year replays
of the deterministic pipeline over the S&P 500 as it stood, scored against SPY held at the same
exposure. The replay harness exists (scripts/replay_*.py, S235). Missing: (1) a rule so the harness
never offers the pipeline a line with less history than the fleet's analyst is given; measured, 113 of
552 buys in the one existing ten-year replay were decided on fewer than 200 bars, as few as 11,
because the cache starts on 2016-01-04; (2) a command that runs the experiment's five arms and
records what each ran on; (3) a scorer that turns the arms into a verdict with a 95 % interval by the
rule frozen in EXP-014's Appendix P.

MUST RULE before any code: read, whole, the laws.md and test-plan.md of the analyst, the provider and
the reporter, docs/laws/conventions.md, docs/laws/drift-register.md. Fill the Law reading record
first.

Law-cycle answer: NO. Everything lives in scripts/ and tests/. If you find you need to edit a file
under agents/, contracts/, kernel/, orchestration/ or surfaces/, stop and report.

Build:
1. The history rule, OFF by default: replay_runner.run(..., require_history=False) and
   `replay_pipeline.py run --require-history`. On: a line that is not held is offered to the pipeline
   (ticker and bars) only when its visible window holds at least
   required_history_bars(settings.analyst) bars; a held line is always offered; removed
   member-sessions are counted as member_sessions_below_required_history. Off: every output as today.
2. scripts/exp014_arms.json = exactly the five arms of Appendix P, and a command that runs one named
   arm (or all) through replay_runner.run with --start 2017-01-03 and the rule on, into
   <out-root>/<arm>/, writing arm.json (name, slippage, overrides, first and last session, rule state,
   repo commit, a checksum prefix of each cache file read).
3. The scorer: reads <out-root>; refuses arms that do not belong together; per arm the
   calculate_performance outputs and A = ((1 + P/100)^(252/n) - (1 + E/100)^(252/n)) * 100 over the
   whole window, per calendar year and per half; a stationary block bootstrap over session pairs
   (mean block 20, 10,000 resamples, seed 0, ONE set of index draws for all arms, each resampled
   series rebuilt and scored by calculate_performance) for A's 95 % interval per arm and for the
   paired difference of each ablation arm from base-25; the control (a replica earning SPY at
   base-25's exposure scores 0, interval [0, 0]); the verdict by Appendix P; verdict.json and
   verdict.md written to <out-root>, outside the worktree, byte-stable.

Order: next free DL (decisions 1-6 with rejected alternatives) -> red C1, C5, C6 (paste) -> implement
-> DL-70 plants, each red, pasted, restored:
  (a) skip the history filter: C1 red;
  (b) chain the daily ratios yourself instead of calling calculate_performance: C5 red;
  (c) resample with block length 1: C8 red;
  (d) draw separate indices per arm: C9 red;
  (e) drop the paired condition from EDGE IN A PILLAR: C11 red;
  (f) switch the arms-belong-together check off: C12 red
-> make ci redirected to a file, exit 0, 100.00 %.

DO NOT:
- change Appendix P, or make the code differ from it. If they cannot agree, stop and report.
- compute a return anywhere but through agents/reporter/domain/performance.calculate_performance.
- edit any file under agents/, contracts/, kernel/, orchestration/, surfaces/, or the fidelity
  scripts, or scripts/replay_universe.py (199 lines).
- change an expected value in an existing test. The rule is opt-in so that none has to.
- import numpy, pandas or scipy: the gate's environment has none. Standard library only.
- commit any cache row or replay output. Fixtures are synthetic.
- grow a module past 200 (replay_session.py is at 190); # noqa to bypass a rule.
- trust coverage or mypy for scripts/: neither reads it. The tests and the plants are the proof.
- run or claim EXP-014, a live proof or GATE PROVEN: those are the planner's.
- pin a version: MINOR, next available at merge.

Handback — the planner returns it if ANY of these is missing:
[ ] Law reading record filled, including the law-cycle answer and contradictions/silences found.
[ ] Test plan results: C1-C16, each with final test name, file, PASS, clause IDs cited.
[ ] Closeout: the red run of C1, C5 and C6 pasted before the implementation; the green run after.
[ ] Each of the six DL-70 plants: what was planted, its red output, restored.
[ ] The DL number used, with decisions 1-6 and their rejected alternatives.
[ ] The exact commands the planner runs: one arm, all arms, the scorer, with every flag.
[ ] A sample verdict.md produced from synthetic arms, pasted.
[ ] Module line counts for every file touched (all < 200).
[ ] make ci: the file, exit code, passed/skipped, coverage 100.00 %, dependency audit, detect-secrets.
[ ] Exactly how pyproject.toml and uv.lock were touched (untouched and owed, or what changed).
[ ] Owed items named: uv lock + MINOR bump, make gate-ran, Windows make ci, F1, F2 (EXP-014).
[ ] Status: BUILT in this file and in its docs/sprints/README.md row, in the same commit.
[ ] A blank line before and after every fenced code block in this file (the commit hook lints it).
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`, here and in the README row.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| *(builder fills)* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *(builder fills)*

**Contradictions found between a law and this spec:** *(builder fills)*

**Laws found silent where a decision was needed:** *(builder fills)*

**Clauses that were ⬜ and are now proven:** *(builder fills)*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| *(builder fills)* | | | | |

**Tests added beyond the plan:** *(builder fills)*

---

## Closeout — evidence

*(builder fills every field below; a field left as written here returns the handback)*

**Tree the proofs ran in (and `.env` present?):**

**Result:**

**Files changed:**

**Design decisions:**

**Proof — the red run first:**

**Proof — the green run:**

**Guards planted:**

**The commands the planner runs:**

**A sample `verdict.md` from synthetic arms:**

**Module line counts:**

**`make ci`:**

**`pyproject.toml` and `uv.lock`:**

**Owed to the planner:**

**Not met / verified failing:**

---

## Return notes

*(builder fills)*
