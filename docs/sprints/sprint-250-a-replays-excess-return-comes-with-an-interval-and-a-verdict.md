<!-- Agent: planning | Role: sprint handover -->
# Sprint 250 — a replay's excess return comes with an interval and a verdict, and no buy is decided on history the fleet never has

**Phase:** Next leg P17, item E17.5 ([next-leg-plan.md](../next-leg-plan.md)) · work-queue 82
**Branch:** `sprint-250-a-replays-excess-return-comes-with-an-interval-and-a-verdict`
**Status:** MERGED 2026-10-01 — `0.121.00`, fast-forwarded to `96b03d52`, tag `v0.121.00`, GATE PROVEN `96b03d52` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (3,915 passed, 8 skipped, 100.00 %); built by a Claude cloud session on `claude/hopeful-davinci-oob51b`, returned once for the holiday-table repair its own handback found; **F1 PASS** (three months on the licensed cache with the history rule on: 54 buys, 0 decided on fewer than 200 bars, least 217, 1,199 member-sessions withheld); the provider's NYSE table now holds every closure from 2016, so the harness window is 203 sessions on all 2,446 scored sessions (194–198 before 2024 until now); deployed with `s251` 2026-10-02 (the calendar repair; `scripts/` ships in no image); owed: F2, EXP-014 itself, once E17.4's fidelity verdict reads PASS
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

All eight files were read whole on 2026-10-01, before the first code change: `agents/analyst/laws/laws.md`
(LOCKED v1.6) + `test-plan.md`, `agents/provider/laws/laws.md` (LOCKED v1.7) + `test-plan.md`,
`agents/reporter/laws/laws.md` (LOCKED v1.3) + `test-plan.md`, `docs/laws/conventions.md`,
`docs/laws/drift-register.md`.

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| The history rule (`replay_history.py`, `replay_session.py`, `replay_runner.py`, `replay_pipeline.py`) | analyst laws + test-plan; provider laws + test-plan; conventions | Analyst `PARAM` `lookback_days` (260), `min_history_bars` (2, bounded ≤ 60), `sma_long_period` (200), the spans `required_history_bars` takes its maximum over; `PROV-TRG-05` 🟩 (a run's window ends on its as-of and starts the declared lookback before it) | Yes. `PROV-TRG-05` describes the window the harness already slices (`declared_lookback_days` from the session), so the rule counts bars **inside that window**, never the cache's whole history for the line, and takes its bar from `required_history_bars(settings.analyst)` itself: no literal anywhere in `scripts/` (C4 proves it follows `ANALYST_SMA_LONG_PERIOD`). Reading `scoring.py` against the PARAM rows showed the analyst scores anything with ≥ `min_history_bars` (2), so the 200 is the fleet's *declared supply*, not an analyst floor; the rule is a data-defect repair in the harness, and the tests cite `PROV-TRG-05`, not an analyst clause |
| The scorer (`replay_verdict*.py`) | reporter laws + test-plan | `RPT-OUT-07` 🟩 (performance from equity, holdings and benchmark bars through the reporter's own calculation), the `PARAM` `performance_rolling_sessions` (20) | Yes. Every return in the scorer goes through one wrapper in `replay_verdict_stats.py` that calls `calculate_performance`, so one monkeypatch (C5) reaches the headline, every year, both halves and every bootstrap draw. The rolling window passed is the reporter's 20 |
| The arms (`exp014_arms.json`, `replay_arms.py`) | analyst laws (`PARAM`) | `relative_strength_weight` (0.20, `float ≥ 0.0, ≤ 1.0`, tunable) | No. 0.0 and 1.0 are inside its declared bounds, and C14 resolves each override through `build_effective_settings` and reads the effective weight back |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** **No.** Every
file changed is under `scripts/`, `tests/` or `docs/`. No agent, contract, kernel, orchestration or
surfaces file is edited; scripts import the analyst's `required_history_bars`, the reporter's
`calculate_performance` and the provider's `is_trading_session` (the S235/S237 precedent) and nothing
imports scripts. No clause is owed.

**Contradictions found between a law and this spec:** none. One looseness, not a contradiction: the
spec's map cites `RPT-OUT-07` as *"a return is computed only by `calculate_performance`"*. The clause
says the reporter computes `performance_metrics` *"only from facts other agents wrote"*; it governs the
reporter's own snapshot and is silent on scripts. The one-metric rule binding this scorer is DL-257's
and the plan's. The scorer obeys both; nothing in the law had to bend.

**Laws found silent where a decision was needed:** one, filed as **DRIFT-096** (analyst section). No
analyst clause says what the analyst does with a candidate whose window holds at least
`min_history_bars` (2) and fewer than `required_history_bars` (200) bars: `scoring.py:64` scores it
with whatever indicators the bars allow. The fleet never meets the case (its run declares a lookback
that covers 203 sessions), the replay met it 113 times, and S250's rule exists because of that
silence. Recorded, not resolved: the analyst book is LOCKED and read-only here.

**Clauses that were ⬜ and are now proven:** none. The clauses cited (`PROV-TRG-05`, `RPT-OUT-07`)
were already 🟩; the new tests add citing tests to them and move no count.

---

## Test plan results — fill at handback

All in `tests/`; every row PASS in the final run (`35 passed in 5.27s`) and inside `make ci`.

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| C1 | `test_c1_a_line_under_the_required_history_is_not_offered` | `test_replay_history_rule.py` | PASS (red first) | `PROV-TRG-05` |
| C2 | `test_c2_a_held_line_stays_visible_and_is_not_counted` | `test_replay_history_rule.py` | PASS | `PROV-TRG-05` |
| C3 | `test_c3_the_rule_off_changes_nothing`, plus every existing replay test, unedited (`git diff --stat -- tests/` is empty) | `test_replay_history_rule.py` | PASS | `RPT-OUT-07` |
| C4 | `test_c4_the_bar_is_the_analysts_own_number` | `test_replay_history_rule.py` | PASS | `PROV-TRG-05` |
| C5 | `test_c5_every_return_comes_from_calculate_performance` | `test_replay_verdict_stats.py` | PASS (red first) | `RPT-OUT-07` |
| C6 | `test_c6_a_planted_edge_is_found_and_a_planted_null_is_not` | `test_replay_verdict_edge.py` | PASS (red first) | `RPT-OUT-07` |
| C7 | `test_c7_a_rebuilt_series_is_faithful` | `test_replay_verdict_stats.py` | PASS | `RPT-OUT-07` |
| C8 | `test_c8_the_bootstrap_is_seeded_and_blocked`, `test_c8_the_percentiles_are_order_statistics` | `test_replay_verdict_stats.py` | PASS | none (no clause governs a bootstrap; cites `S250-C8`) |
| C9 | `test_c9_arms_are_compared_on_the_same_days` | `test_replay_verdict_edge.py` | PASS | none (`S250-C9`) |
| C10 | `test_c10_the_years_partition_the_window` | `test_replay_verdict_stats.py` | PASS | `RPT-OUT-07` |
| C11 | `test_c11_the_verdict_rule[...]`, 10 cases | `test_replay_verdict_rule.py` | PASS | none (`S250-C11`) |
| C12 | `test_c12_arms_that_do_not_belong_together_give_no_verdict[...]` (6 cases), `test_c12_a_gap_session_gives_no_verdict` | `test_replay_verdict_refusals.py` | PASS | `RPT-OUT-07` (the gap case) |
| C13 | `test_c13_the_control_scores_zero_and_a_failing_control_refuses` | `test_replay_verdict_edge.py` | PASS | `RPT-OUT-07` |
| C14 | `test_c14_the_manifest_is_appendix_p` | `test_replay_arms.py` | PASS | none (`S250-C14`) |
| C15 | `test_c15_outputs_stay_out_of_the_repo_and_are_byte_stable` | `test_replay_verdict_refusals.py` | PASS | none (`S250-C15`) |
| C16 | `test_c16_the_arms_command_records_what_it_ran`, `test_c16_an_unknown_arm_and_a_dirty_worktree_are_refused`, `test_c16_all_runs_every_arm_from_the_command_line` | `test_replay_arms.py` | PASS | none (`S250-C16`) |

**Tests added beyond the plan:** `test_replay_history_calendar.py::test_before_2024_the_declared_window_holds_fewer_sessions_than_the_bar`
(cites `PROV-TRG-05`). It pins the finding in Return notes: on a 2019 cache that skips 2019's real
NYSE closures, a line with a bar on every session holds **197** bars in its declared window on
2019-12-31 and the rule withholds it. It asserts today's behaviour so that it flips, and is
re-written, the day the provider's calendar is extended (the S240 `..._yet` precedent).

---

## Closeout — evidence

**Tree the proofs ran in (and `.env` present?):** the claude.ai cloud container's checkout
`/home/user/trading-agents`, on the session-forced branch **`claude/hopeful-davinci-oob51b`** (not
`sprint-250-…`: the session fixed the name), cut from `main` `05ca2be`. **No `.env`**, no replay
cache, no `gh`. Python deps from `uv sync --frozen` (no re-lock; `uv.lock` unchanged).

**Result:** BUILT. The history rule, the arms command and the scorer exist and are proven on
synthetic series: C1–C16 pass, C1/C5/C6 were red first, six DL-70 plants each went red and were
restored, `make ci` exit 0 (3,828 passed, 8 skipped, 100.00 %). **One finding blocks F1 and F2 as
specified** (Return notes 1): before 2024 the harness's declared window holds 194–198 sessions, so
the rule, built exactly as the spec says, withholds every unheld line from 2017-01-03 to
2023-12-29. EXP-014 must not run until the planner decides the repair.

**Files changed:**

- `scripts/replay_history.py` (new): `visible_window` (moved verbatim out of `replay_session.py`)
  and `offer_lines`, the rule.
- `scripts/replay_session.py`: `require_history` keyword, one call; the moved helper is gone
  (190 → 180 lines).
- `scripts/replay_runner.py`: `require_history=False`; the counter key exists only when on.
- `scripts/replay_pipeline.py`: `--require-history`.
- `scripts/exp014_arms.json` (new): Appendix P's five arms, start, rule on.
- `scripts/replay_arms.py`, `scripts/replay_arms_record.py` (new): the arms command and what an arm
  records (commit, dirty, cache checksums, sessions, SPY closes).
- `scripts/replay_verdict.py`, `_load.py`, `_score.py`, `_stats.py`, `_windows.py`, `_rule.py`,
  `_report.py`, `_markdown.py` (new): the scorer.
- `tests/`: `test_replay_history_rule.py`, `test_replay_history_calendar.py`,
  `test_replay_verdict_stats.py`, `test_replay_verdict_edge.py`, `test_replay_verdict_rule.py`,
  `test_replay_verdict_refusals.py`, `test_replay_arms.py`; fixtures `replay_history_fixtures.py`,
  `replay_verdict_fixtures.py`, `replay_arm_folders.py` (all synthetic).
- `docs/design-log.md` (DL-258), `docs/laws/drift-register.md` (DRIFT-096), this file, its
  `docs/sprints/README.md` row.

**Design decisions:** **DL-258** (DL-258 was free on `main` `05ca2be`; re-check at merge).

1. Where the rule lives: `scripts/replay_history.py`. *Rejected:* in `replay_series.py` (settings-free
   helpers), inline in `replay_session.py` (crosses 200), in the day runner (two meanings of "held").
2. The counter exists only when the rule is on. *Rejected:* always present at 0 (breaks F1's
   byte-identity with the rule off).
3. One `random.Random(seed)`; first index `randrange(n)`, then a fresh `randrange(n)` with
   probability `1/mean_block`, else previous + 1 mod `n`; resamples drawn one at a time and applied to
   every arm and the control before the next. Percentiles: sort, `k = B × 25 // 1000`, interval
   `v[k]`, `v[B − 1 − k]` (`v[250]`, `v[9749]` at 10,000). *Rejected:* fixed blocks, interpolated
   percentiles, all indices up front (~1 GB), a generator per arm (Appendix P forbids it).
4. `arm.json`: name, slippage, overrides, start, first/last session and count, rule state, commit,
   `dirty`, a 12-hex SHA-256 prefix per cache file read (`absent` when missing), and a `benchmark.csv`
   of the arm's SPY closes beside it; written last. A dirty worktree refuses to start an arm; the
   scorer refuses missing files, manifest mismatches, a rule-off or dirty arm, commit / cache /
   session / SPY differences, `equity.csv` ≠ `arm.json`, a gap session, a failed control.
   *Rejected:* a dirty run with its diff recorded, checksumming the whole folder, the scorer reading
   the cache.
5. Rebuild at 10¹⁴ integer cents on consecutive ordinal dates, integer round-half-up steps; SPY from
   1.0; scored by `calculate_performance`. The control's replica steps by `E + L × (S'/S − 1)`; it
   passes within 1e-6 points. *Rejected:* the original scale (rounds at 1e-7), float equity, real
   dates.
6. `verdict.md`: verdict and base-25's interval first, then arms, differences, control, years
   (partial marked, years with positive excess), halves, provenance; a refusal replaces the tables;
   exit 2. *Rejected:* per-year intervals, a plot.

**Proof — the red run first** (before any implementation; C5 and C6 could not import the scorer):

```text
$ uv run pytest --no-cov -q tests/test_replay_history_rule.py::test_c1_a_line_under_the_required_history_is_not_offered
E   TypeError: run() got an unexpected keyword argument 'require_history'
FAILED tests/test_replay_history_rule.py::test_c1_a_line_under_the_required_history_is_not_offered
1 failed in 0.64s

$ uv run pytest --no-cov -q tests/test_replay_verdict_stats.py::test_c5_every_return_comes_from_calculate_performance \
    tests/test_replay_verdict_edge.py::test_c6_a_planted_edge_is_found_and_a_planted_null_is_not
E   ModuleNotFoundError: No module named 'scripts.replay_verdict_score'
E   ModuleNotFoundError: No module named 'scripts.replay_verdict_score'
ERROR tests/test_replay_verdict_stats.py
ERROR tests/test_replay_verdict_edge.py
2 errors in 0.85s
```

**Proof — the green run:**

```text
$ uv run pytest --no-cov -v tests/test_replay_history_rule.py tests/test_replay_history_calendar.py \
    tests/test_replay_verdict_stats.py tests/test_replay_verdict_edge.py tests/test_replay_verdict_rule.py \
    tests/test_replay_verdict_refusals.py tests/test_replay_arms.py
... (35 test ids, each PASSED; listed in the table above)
============================== 35 passed in 5.27s ==============================
```

**Guards planted:** each plant was applied by a script, the named test run, the file restored and its
SHA-256 checked identical to the original.

```text
--- plant (a) skip the history filter: `if require_history and False:` in scripts/replay_session.py
E   AssertionError: 205
E     At index 0 diff: ('LONG', 'SHORT') != ('LONG',)
FAILED tests/test_replay_history_rule.py::test_c1_a_line_under_the_required_history_is_not_offered
restored scripts/replay_session.py (sha256 identical)

--- plant (b) performance() chains the daily ratios itself instead of calling calculate_performance
E   assert 0.09584999999998622 == 10.0
FAILED tests/test_replay_verdict_stats.py::test_c5_every_return_comes_from_calculate_performance
restored scripts/replay_verdict_stats.py (sha256 identical)

--- plant (c) block length 1: `restart = 1.0` in stationary_draws
E   assert 17.0 <= (100000 / 99816)
FAILED tests/test_replay_verdict_stats.py::test_c8_the_bootstrap_is_seeded_and_blocked
restored scripts/replay_verdict_stats.py (sha256 identical)

--- plant (d) a fresh draw per arm inside the arms loop in scripts/replay_verdict_score.py
E     {'interval': [-7.009611900285906, 6.026702508502446]} != {'interval': [0.0, 0.0]}
FAILED tests/test_replay_verdict_edge.py::test_c9_arms_are_compared_on_the_same_days
restored scripts/replay_verdict_score.py (sha256 identical)

--- plant (e) EDGE IN A PILLAR without the paired condition in scripts/replay_verdict_rule.py
E     {'verdict': 'EDGE IN A PILLAR'} != {'verdict': 'NO EDGE'}
FAILED tests/test_replay_verdict_rule.py::test_c11_the_verdict_rule[own bound alone is no pillar]
restored scripts/replay_verdict_rule.py (sha256 identical)

--- plant (f) the arms-belong-together check switched off in scripts/replay_verdict_load.py
E   AssertionError: assert {'verdict': 'NO EDGE', 'reading': 'indistinguishable', 'pillars': []} is None
E   ValueError: arms differ in their number of session pairs
FAILED tests/test_replay_verdict_refusals.py::test_c12_arms_that_do_not_belong_together_give_no_verdict[different cache]
FAILED tests/test_replay_verdict_refusals.py::test_c12_arms_that_do_not_belong_together_give_no_verdict[different commit]
FAILED tests/test_replay_verdict_refusals.py::test_c12_arms_that_do_not_belong_together_give_no_verdict[different sessions]
restored scripts/replay_verdict_load.py (sha256 identical)
```

(Plant (b)'s first attempt went red for the wrong reason, an `UnboundLocalError` from a `del` in the
plant itself; it was re-planted as a clean hand-chained return and the red above is the second run.)

**The commands the planner runs** (from the proving worktree; `--cache` defaults to the replay
dataset folder, `REPLAY_DATASET_DIR` or OneDrive `trading-agents-data`; `<OUT>` must be outside the
worktree):

```text
# one arm
uv run python scripts/replay_arms.py run --arm base-25 --out-root <OUT> --cache <CACHE>
# all five, in manifest order (or run two at a time with --arm <name> in two shells)
uv run python scripts/replay_arms.py run --arm all --out-root <OUT> --cache <CACHE>
# the scorer: Appendix P's 10,000 resamples by default; exit 0 with a verdict, 2 with a refusal
uv run python scripts/replay_verdict.py score --out-root <OUT>
# F1's two runs (the rule on, then off), on the merged commit and on the commit before it
uv run python scripts/replay_pipeline.py run --cache <CACHE> --out <OUT>/f1-on --start <D1> --end <D2> --slippage-bps 25 --require-history
uv run python scripts/replay_pipeline.py run --cache <CACHE> --out <OUT>/f1-off --start <D1> --end <D2> --slippage-bps 25
```

Other flags: `--manifest` (both commands, default `scripts/exp014_arms.json`), `--progress-every`
(arms), `--resamples` (scorer; anything but 10,000 is marked `NOT Appendix P's bootstrap` in the
title and `appendix_p: false` in `verdict.json`). Measured here: 50 resamples of five 2,446-point
arms plus the control took 1.3 s, so 10,000 is about **4.5 minutes**.

**A sample `verdict.md` from synthetic arms** (five invented arms of 601 sessions from 2017-01-03,
base-25 with a planted drift of 0.0004 a session, the ablations with none; 1,000 resamples, so the
title says it is not Appendix P's bootstrap; the commit and checksum are low-entropy fixture
placeholders):

```markdown
# EXP-014 verdict: EDGE, NOT Appendix P's bootstrap

**base-25:** A = +11.94 pts a year, 95 % interval [+6.24, +18.21]; 600 session pairs, 1,000 resamples, mean block 20, seed 0.

## Arms

| Arm | Slippage (bps) | A (pts/yr) | 95 % interval | Portfolio % | Exposure-matched % | SPY % | Avg exposure % | Max drawdown % |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| base-05 | 5 | +11.89 | [+6.28, +18.94] | 70.23 | 34.19 | 43.55 | 80.00 | -17.02 |
| base-10 | 10 | +11.95 | [+6.52, +17.36] | 70.43 | 34.19 | 43.55 | 80.00 | -16.55 |
| base-25 | 25 | +11.94 | [+6.24, +18.21] | 70.40 | 34.19 | 43.55 | 80.00 | -16.99 |
| technical-only-25 | 25 | -0.06 | [-4.14, +4.00] | 34.02 | 34.19 | 43.55 | 80.00 | -17.32 |
| relative-strength-only-25 | 25 | -0.06 | [-4.12, +4.36] | 34.03 | 34.19 | 43.55 | 80.00 | -17.52 |

## Paired differences from base-25

| Arm | A(X) - A(base-25) | 95 % interval |
| --- | ---: | --- |
| technical-only-25 | -12.00 | [-18.39, -5.56] |
| relative-strength-only-25 | -12.00 | [-18.57, -4.67] |

## Control

The replica of base-25 earning SPY at its exposure: A = +0.000000, interval [+0.000000, +0.000000] (tolerance 1e-06): PASS.

## Years (A, pts a year)

| Block | base-05 | base-10 | base-25 | technical-only-25 | relative-strength-only-25 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2017 (2017-01-03 → 2017-12-29), partial | +17.69 | +17.95 | +20.62 | -0.68 | -1.48 |
| 2018 (2017-12-29 → 2018-12-31) | +5.19 | +6.94 | +4.88 | +0.27 | -1.62 |
| 2019 (2018-12-31 → 2019-04-23), partial | +20.60 | +11.65 | +11.61 | +0.86 | +13.50 |
| Years with positive excess | 3 | 3 | 3 | 2 | 1 |

## Halves (A, pts a year)

| Block | base-05 | base-10 | base-25 | technical-only-25 | relative-strength-only-25 |
| --- | ---: | ---: | ---: | ---: | ---: |
| first half (2017-01-03 → 2018-02-27) | +12.37 | +15.62 | +17.52 | +0.48 | -2.62 |
| second half (2018-02-27 → 2019-04-23) | +11.35 | +8.08 | +6.15 | -0.64 | +2.81 |

## Provenance

- Commit: `cccccccccccccccccccccccccccccccccccccccc`
- Sessions: 601, 2017-01-03 → 2019-04-23; history rule on
- Cache (SHA-256 prefix): `sp500_bars.csv.gz` bbbbbbbbbbbb, `sp500_sectors.csv.gz` absent
- Member-sessions withheld by the history rule: base-05 7, base-10 7, base-25 7, technical-only-25 7, relative-strength-only-25 7
```

**Module line counts** (all < 200; `replay_universe.py` and the fidelity scripts untouched):

| File | Lines | File | Lines |
| --- | ---: | --- | ---: |
| `scripts/replay_session.py` | 180 (was 190) | `scripts/replay_verdict_score.py` | 168 |
| `scripts/replay_runner.py` | 87 (was 82) | `scripts/replay_verdict_stats.py` | 119 |
| `scripts/replay_pipeline.py` | 59 (was 53) | `scripts/replay_verdict_windows.py` | 65 |
| `scripts/replay_history.py` | 68 | `scripts/replay_verdict_rule.py` | 47 |
| `scripts/replay_arms.py` | 156 | `scripts/replay_verdict_report.py` | 99 |
| `scripts/replay_arms_record.py` | 82 | `scripts/replay_verdict_markdown.py` | 140 |
| `scripts/replay_verdict.py` | 66 | `scripts/replay_verdict_load.py` | 133 |
| `tests/test_replay_history_rule.py` | 165 | `tests/test_replay_history_calendar.py` | 71 |
| `tests/test_replay_verdict_stats.py` | 175 | `tests/test_replay_verdict_edge.py` | 103 |
| `tests/test_replay_verdict_rule.py` | 79 | `tests/test_replay_verdict_refusals.py` | 135 |
| `tests/test_replay_arms.py` | 189 | `tests/replay_history_fixtures.py` | 154 |
| `tests/replay_verdict_fixtures.py` | 99 | `tests/replay_arm_folders.py` | 84 |

`replay_counters.py` was not touched (the counter key is added by `replay_runner.py`). Six files sit
between 150 and 200 (a warning, not a block). `exp014_arms.json` is 39 lines.

**`make ci`:** `make ci > <scratchpad>/ci.txt 2>&1 ; echo $?` → **exit 0**, in the container above,
no `.env`. Every step of the `ci:` target ran: ruff (clean), format (1,536 files formatted), mypy (no
issues in 1,134 files; it does not read `scripts/`), import-linter (5 kept, 0 broken), module size,
module header, law coverage, PARAM sync, sprint status, markdown links, version scheme, pytest
**3,828 passed, 8 skipped, coverage 100.00 %** (it does not measure `scripts/`), dependency audit
(*"No unaccepted vulnerabilities; 1 accepted advisory re-checked"*: PYSEC-2026-2447, DL-184),
detect-secrets **Passed**, untracked secrets (*"scanning 22 new file(s)"*) **Passed**. The first run
failed at the untracked-secrets step on two hex placeholders in `tests/replay_arm_folders.py`; they
were replaced with low-entropy strings (no allowlist pragma) and the second run is the one quoted.
`make ci` was then re-run on the finished tree (this handback, DL-258 and the README row included):
**exit 0**, 3,828 passed, 8 skipped, 100.00 %, dependency audit and detect-secrets passed. The repo's
pre-commit hooks (ruff, format, mypy, markdownlint, detect-secrets, module size, header) passed on
every changed file.

**`pyproject.toml` and `uv.lock`:** **untouched**, both. No version bump; no `uv lock` (the session
cannot reach `download.pytorch.org`). `uv sync --frozen` installed from the existing lock.

**Owed to the planner:** `uv lock` with the **MINOR** bump (next available at merge); Windows
`make ci`; `make gate-ran` from the proving worktree (check the printed SHA against
`git rev-parse HEAD`); the merge; post-merge CodeQL; **the repair decision in Return notes 1, before
F1**; **F1** on the licensed cache (rule on: 0 buys on fewer than 200 bars and the removed
member-sessions reported; rule off: byte-identical files on the merged commit and the commit before);
**F2**, EXP-014 itself, once E17.4 reads PASS **and** Return notes 1 is resolved.

**Not met / verified failing:**

- **The rule as specified cannot serve EXP-014's scored window** (Return notes 1). The code meets the
  spec and is proven; the experiment it was built for is blocked until the calendar (or the window)
  is repaired. Not repaired here: the fix is in `agents/provider/domain/market_calendar.py`, which
  the spec's stop rule puts out of scope.
- **Branch name:** the session forced `claude/hopeful-davinci-oob51b`; no `sprint-250-…` branch was
  created.
- **Not run, by design:** EXP-014, F1, F2, `make gate-ran`, Windows `make ci`, any live proof. No
  GATE PROVEN is claimed.

---

## Return notes

1. 🚨 **Before 2024 the declared window holds 194–198 sessions, so the rule withholds every unheld
   line; F1 and F2 are blocked until the planner picks a repair.** `declared_lookback_days` counts
   sessions with the provider's calendar, whose holiday table covers 2024–2027 only (every earlier
   weekday counts as a session). *[measured in this container: NYSE's 2016–2023 closures written out
   and checked against EXP-014's counts, 2,698 sessions from 2016-01-04 and 2,446 from 2017-01-03,
   both reproduced once 2025-01-09 (also missing from the provider's table) is removed]* A line with
   a bar on every session holds 194–198 bars in its window on **1,760 of 1,760** sessions from
   2017-01-03 to 2023-12-29 and on 74 sessions of 2024; 203 from 2025. With `--require-history`, no
   unheld line reaches `required_history_bars` (200) before 2024, so every arm would sit in cash for
   seven years. The same arithmetic says every replay so far gave the analyst at most 198 bars before
   2024, so SMA-200 distance was absent from every pre-2024 replayed decision, the smoke run's
   included: a fidelity gap in the harness independent of this sprint. Repairs, the planner's call
   (DL-258 records both): **(a, recommended)** extend `_NYSE_HOLIDAYS` back to 2016 and add
   2025-01-09, a provider data change the fleet never reads for a date it trades, after which the
   window holds 203 sessions and both the rule and the rule-off replay match the fleet; **(b)** cut the
   harness window from the cache's own sessions (scripts only, but it changes rule-off output too, so
   F1's byte-identity fails by design). `tests/test_replay_history_calendar.py` flips under (a).
2. **EXP-014 section 2 and Appendix P differ in one corner.** H1 says *"`A > 0` and the lower bound
   above 0"*; Appendix P says the lower bound alone. The code follows Appendix P (the spec binds it);
   `verdict.json` carries the point estimate beside the interval, so the case is visible if it occurs.
3. **2017 is labelled partial.** A pair belongs to the year of its later session, so the pair arriving
   on 2017-01-03 (from 2016-12-30) is outside the scored window and 2017 holds one pair fewer than the
   year. The flag uses no calendar for a start year; for an end year it asks the provider's calendar
   only for the year's last session (31 December or the weekday before, which the pre-2024 fallback
   gets right).
4. **Two justified suppressions, both with repo precedent:** `# noqa: S311` once, on the scorer's
   single `random.Random(seed)` (`seeded()` in `replay_verdict_stats.py`; precedent
   `scripts/exp013_regime_sizing.py`), and `# noqa: E402` on the two CLIs' imports after the
   `sys.path` insert (precedent `replay_pipeline.py`). The git calls reuse `replay_fidelity_git._git`
   (imported, not edited) rather than add another `# noqa: S603`.
5. **Reported, not computed:** buys a year and exits by reason (EXP-014 §5.9) are not in the
   verdict; they are in each arm's `fills.csv`. Every absent-input counter is copied into
   `verdict.json` (`absent_inputs`), and the withheld member-sessions are in `verdict.md`'s
   provenance.
6. **DRIFT-096 filed** (analyst book silent on a candidate under `required_history_bars`); no
   `laws.md` edited; no clause moved (law-cycle answer: No).

---

## Return 1 — the planner's ruling on Return note 1, and the follow-up handover (2026-10-01)

**The finding is confirmed and accepted.** *[measured by the planner on the licensed cache]* The
harness window holds **194–198** sessions on every session of 2017–2023 (1,760 of 1,760 under 200),
**196–203** in 2024 (74 of 252 under 200), and 202–203 from 2025. The cause is the one the builder
named: `agents/provider/domain/market_calendar.py` lists NYSE closures for 2024–2027 only. The spec's
rule was written against a window the planner assumed held about 203 sessions and did not measure by
year; that is the spec's miss, not the builder's.

**Ruling: repair (a).** Extend the holiday table back to 2016 and add 2025-01-09. Ruled out: (b)
cutting the harness window from the cache's own sessions, which leaves the calendar wrong and makes
the harness stop calling the fleet's own `declared_lookback_days`.

**What the rest of the handback gets:** accepted as built, pending the planner's own verification.
Return note 2 stands as coded (Appendix P binds). Notes 3 to 6 are accepted.

**The closures to add** *[measured: every weekday from 2016-01-04 to 2026-09-25 that is not a session
in the cache; public NYSE record]*. Sessions a year must then count 252, 251, 251, 252, 253, 252,
251, 250, 252, 250 for 2016–2025.

| Year | Closures (MM-DD) |
| --- | --- |
| 2016 | 01-01, 01-18, 02-15, 03-25, 05-30, 07-04, 09-05, 11-24, 12-26 |
| 2017 | 01-02, 01-16, 02-20, 04-14, 05-29, 07-04, 09-04, 11-23, 12-25 |
| 2018 | 01-01, 01-15, 02-19, 03-30, 05-28, 07-04, 09-03, 11-22, 12-05, 12-25 |
| 2019 | 01-01, 01-21, 02-18, 04-19, 05-27, 07-04, 09-02, 11-28, 12-25 |
| 2020 | 01-01, 01-20, 02-17, 04-10, 05-25, 07-03, 09-07, 11-26, 12-25 |
| 2021 | 01-01, 01-18, 02-15, 04-02, 05-31, 07-05, 09-06, 11-25, 12-24 |
| 2022 | 01-17, 02-21, 04-15, 05-30, 06-20, 07-04, 09-05, 11-24, 12-26 |
| 2023 | 01-02, 01-16, 02-20, 04-07, 05-29, 06-19, 07-04, 09-04, 11-23, 12-25 |
| 2025 | 01-09 (added to the ten already listed) |

2016-01-01 precedes the cache and is from the public record, not measured. The 40 dates already in
the table are all correct: none is a session in the cache.

### Follow-up handover — paste this to the Claude cloud session

```text
Sprint 250, return 1. Continue on the branch that holds your S250 work (the planner pushed one
commit to it: this section). Read "Return 1" at the bottom of
docs/sprints/sprint-250-a-replays-excess-return-comes-with-an-interval-and-a-verdict.md, whole.
Same constraints as before: no .env, no gh, no cache, nobody will answer follow-ups.

Your Return note 1 is confirmed and the planner chose repair (a). This lifts the earlier ban for
exactly one file: agents/provider/domain/market_calendar.py (93 lines) and its tests.

Build:
1. Failing test first: per-year session counts 2016-2025 from trading_sessions_between equal
   252, 251, 251, 252, 253, 252, 251, 250, 252, 250, and each closure in the Return 1 table is not a
   trading session. Red on the current table for 2016-2023 and 2025. Paste it.
2. Add the closures of the Return 1 table to _NYSE_HOLIDAYS (74 dates for 2016-2023, plus
   2025-01-09). Do not change a date already there. calendar_window_end() must return what it
   returns today. Keep the module under 200 lines; if the table needs its own module, split it and
   keep the public functions where they are.
3. Prove the harness consequence: for every weekday-session as-of from 2017-01-03 to 2026-09-25
   (use the calendar itself, no cache), the window declared_lookback_days gives holds at least
   required_history_bars(AnalystSettings()) sessions. Your tests/test_replay_history_calendar.py
   flips: rewrite it to assert the repaired behaviour and say so.
4. Read agents/provider/laws/laws.md and test-plan.md again for any clause that depends on the
   calendar's coverage (staleness in sessions, the declared lookback of PROV-TRG-05). Expected: no
   clause changes, because the guarantee is unchanged and the table is data. If a clause names the
   table's range, do the law cycle for it and say so. Cite the clause the new test proves, if one.
5. An existing test that pinned the old fallback (a pre-2024 weekday holiday counted as a session)
   may change its expected value. Name each such test and why in the handback. No other expected
   value changes.
6. DL-70 plants, each red, pasted, restored: (a) drop one added closure (for example 2018-12-05):
   the count test red; (b) drop 2025-01-09: red.
7. Record the repair under your DL-258 as an amendment, with (b) as the rejected alternative.
8. make ci redirected to a file, exit 0, 100.00 %. Coverage DOES read agents/.

DO NOT touch any other file under agents/, contracts/, kernel/, orchestration/ or surfaces/; change
the rule's threshold or Appendix P; or run or claim F1, F2 or GATE PROVEN.

Handback, appended under Return 1 in the same spec file:
[ ] the red run, then the green run;
[ ] the two plants, red output, restored;
[ ] every existing test whose expected value changed, with the reason, or "none";
[ ] the law reading for the provider book: clauses read, whether any changed;
[ ] line counts of every file touched;
[ ] make ci: file, exit code, passed/skipped, coverage, dependency audit, detect-secrets;
[ ] pyproject.toml and uv.lock untouched, stated;
[ ] Status stays BUILT; the README row gains "return 1: holiday table repaired".
```

### Return 1 — handback (builder, 2026-10-01)

**Tree:** a claude.ai cloud container, `/home/user/trading-agents`, on branch
`claude/hopeful-davinci-oob51b` from `9c9fc67` (the planner's Return 1 commit). No `.env`, no `gh`,
no cache. Status stays **BUILT**.

**What was built.** `agents/provider/domain/market_calendar.py`: `_NYSE_HOLIDAYS` gains Return 1's
74 closures for 2016-2023 and 2025-01-09, in date order, with a reason comment on the two national
days of mourning (2018-12-05 and 2025-01-09). No existing date changed: the diff removes only three
module-docstring lines, which are rewrapped to say the table now spans 2016-2027. The table stayed in
the module at 178 lines, so no split was needed, and the public functions are untouched.
`calendar_window_end()` still returns 2027-12-31, asserted by the new test.

**The red run, then the green run** (`agents/provider/tests/test_market_calendar_history.py`, written
first, against the old table):

```text
FAILED test_each_year_holds_nyses_sessions[2016-252]   E   assert 261 == 252
FAILED test_each_year_holds_nyses_sessions[2017-251]   E   assert 260 == 251
FAILED test_each_year_holds_nyses_sessions[2018-251]   E   assert 261 == 251
FAILED test_each_year_holds_nyses_sessions[2019-252]   E   assert 261 == 252
FAILED test_each_year_holds_nyses_sessions[2020-253]   E   assert 262 == 253
FAILED test_each_year_holds_nyses_sessions[2021-252]   E   assert 261 == 252
FAILED test_each_year_holds_nyses_sessions[2022-251]   E   assert 260 == 251
FAILED test_each_year_holds_nyses_sessions[2023-250]   E   assert 260 == 250
FAILED test_each_year_holds_nyses_sessions[2025-250]   E   assert 251 == 250
FAILED test_each_measured_closure_is_not_a_session[2016-01-01] ... [2025-01-09]   (75 of 75, E   assert True is False)
84 failed, 2 passed in 0.60s          (2024 and test_the_table_still_ends_where_it_did passed)
```

After the repair:

```text
agents/provider/tests/test_market_calendar_history.py + test_market_calendar.py
90 passed in 0.42s
```

**Harness consequence (step 3).** `tests/test_replay_history_calendar.py` **flipped**. It was
rewritten to assert the repaired behaviour, and its module docstring says so.
`test_every_sessions_declared_window_holds_the_required_bars` walks the calendar itself (no cache)
over every session from 2017-01-03 to 2026-09-25, **2,446 sessions** (EXP-014's own count). On each
one, the window `declared_lookback_days(AnalystSettings(), as_of, staleness_buffer_sessions=3)` gives
holds at least `required_history_bars` (200), and in fact exactly 203. `test_a_full_line_is_offered_on_2019_12_31`
replaces the pinned hazard: the 2019 cache's full line now holds 203 bars in the window and is
offered, with 0 withheld. Against the old table both tests are red (`assert 2511 == 2446`: weekdays
counted as sessions; `assert 197 == 203`), so neither is vacuous. **Fleet effect, measured:** over
2025-2027 the declared lookback differs from the old table only for an as-of between 2025-01-09 and
2025-10-29. Today's (2026-10-01) is 295 days under both, so no run the fleet places now reads a
different window.

**The two plants**, each red and restored (`cmp` against the saved file: identical):

```text
(a) removed date(2018, 12, 5):
FAILED test_each_measured_closure_is_not_a_session[2018-12-05]   E   assert True is False
FAILED test_each_year_holds_nyses_sessions[2018-251]             E   assert 252 == 251
2 failed, 84 passed in 0.49s
(b) removed date(2025, 1, 9):
FAILED test_each_measured_closure_is_not_a_session[2025-01-09]   E   assert True is False
FAILED test_each_year_holds_nyses_sessions[2025-250]             E   assert 251 == 250
2 failed, 84 passed in 0.44s
restored: 86 passed in 0.40s
```

**Existing tests whose expected value changed:** one, `tests/test_replay_history_calendar.py`. Its
single test pinned the old fallback (a 2019 window of 203 weekdays, 197 bars, the line withheld) and
was replaced by the two tests above, as step 3 required. **No other expected value changed.** With
only the table edited, the full suite had exactly one failure, that test. In
`tests/replay_history_fixtures.py` only two comments changed: they said the calendar lists no 2019
closure. `sessions_2019()` now yields 252 sessions without `closures`; no assertion depends on 261.

**Law reading, provider book (step 4).** I read `agents/provider/laws/laws.md` (v1.7 on this branch)
and `test-plan.md` again for every mention of calendar, session, holiday, staleness, lookback and the
years. The clauses that depend on session counting are `PROV-TRG-05` (the declared lookback checked
against the sessions up to the as-of), `PROV-STA-04` and `PROV-OUT-03` (staleness flagged), the
`max_staleness_days` `PARAM` row ("three sessions"), and `PROV-OUT-08`/`barrier_history_sessions`,
whose window is a calendar-day formula that does not read the table. **None names the table's range,
so no clause changed and there was no law cycle.** The new tests cite `PROV-TRG-05` (with DL-10),
the clause whose session-counted lookback they make true before 2024. *Follow-up, at the operator's
"go for it":* the `PROV-TRG-05` test-plan row now cites
`test_market_calendar_history.py::test_each_year_holds_nyses_sessions` and
`tests/test_replay_history_calendar.py::test_every_sessions_declared_window_holds_the_required_bars`.
That is a row edit only: the clause text, its status (🟩) and the rollup (24 / 67 on `main`) are unchanged.

**Decision record:** DL-258 gains an amendment (repair (a) as built, measured). The rejected
alternative is (b), cutting the harness window from the cache's sessions: it leaves the calendar
wrong, stops calling `declared_lookback_days`, and would break F1's rule-off byte-identity by design.

**Line counts of every file touched:**

| File | Lines |
| --- | ---: |
| `agents/provider/domain/market_calendar.py` | 178 (was 93; above the 150 warning, under the 200 block) |
| `agents/provider/tests/test_market_calendar_history.py` | 75 (new) |
| `tests/test_replay_history_calendar.py` | 103 (was 71) |
| `tests/replay_history_fixtures.py` | 155 (was 154; comments only) |
| `docs/design-log.md` | DL-258 amendment |
| `docs/sprints/README.md` | S250 row |
| this file | this section |

**`make ci`:** `make ci > <scratchpad>/ci-r1.txt 2>&1; echo $?` gave **exit 0**, with every step of
the `ci:` target green: ruff, format (1,537 files), mypy (no issues in 1,135 files), import-linter
(5 kept, 0 broken), module size (`market_calendar.py` warns at 178), module header, law coverage,
PARAM sync, sprint status, markdown links, version scheme, pytest **3,915 passed, 8 skipped,
coverage 100.00 %** (it reads `agents/`; `market_calendar.py` is 100.00 %), dependency audit
(*"No unaccepted vulnerabilities; 1 accepted advisory re-checked"*), detect-secrets **Passed**, and
untracked secrets (1 new file) **Passed**.

**`pyproject.toml` and `uv.lock`:** **untouched**, both.

**Not done, by design:** F1, F2 and EXP-014 were not run; no GATE PROVEN is claimed; the rule's
threshold and Appendix P are unchanged. No other file under `agents/`, `contracts/`, `kernel/`,
`orchestration/` or `surfaces/` was touched. Owed to the planner, as before: `uv lock` with the MINOR
bump, Windows `make ci`, `make gate-ran`, the merge, then F1 and F2.

### Planner, at merge (2026-10-01)

- **Scope held.** The first handback touches `scripts/`, `tests/` and docs only; the return touches `agents/provider/domain/market_calendar.py` and its tests, as Return 1 allowed. No existing test's expected value changed except `tests/test_replay_history_calendar.py`, which pinned the defect.
- **Proven.** Windows `make ci` exit 0 (3,915 passed, 8 skipped, 100.00 %); `GATE PROVEN` for `96b03d52` from the proving worktree, printed SHA equal to `HEAD`; fast-forwarded after a rebase onto `main`; the branch's open CodeQL alerts equal the last merged branch's (131, 0 added); the lock's package set is unchanged.
- **Read and re-proved by the planner.** `exp014_arms.json` equals Appendix P; the verdict rule and the bootstrap read correct; two plants of the planner's own (the paired condition dropped; resampling without blocks) each turned a test red and were restored.
- **The repaired calendar, measured on the cache.** It equals the cache's sessions on every day from 2016-01-04 to 2026-09-25 (0 differences), and the declared window holds 203 sessions on all 2,446 scored sessions.
- **F1 PASS** ([functionality-checks](../laws/functionality-checks.md)). The byte-identity limb written in this spec no longer applies: the calendar repair changes rule-off replays too, by design.
- **The spec's miss, recorded in DL-257's amendment:** the rule was specified against a window the planner assumed held about 203 sessions and did not measure by year. The builder measured it and stopped, which is what the handover asked for.
- **Carried forward:** every earlier replay on this harness gave the analyst at most 198 bars before 2024. S235's smoke result and anything scored on it predate the repair.
- **Return note 2** (H1's wording against Appendix P): Appendix P binds, as coded. **DRIFT-096** (the analyst's book is silent on a candidate under `required_history_bars`) is added to S251's table.
- **Owed:** F2, EXP-014 itself, after the fidelity re-run reads PASS.
