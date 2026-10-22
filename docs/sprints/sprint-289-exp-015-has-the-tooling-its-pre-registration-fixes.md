<!-- Agent: planning | Role: sprint handover template -->
# Sprint 289 — EXP-015 has the tooling its pre-registration fixes, and the holdout can be touched only once

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-289-exp-015-has-the-tooling-its-pre-registration-fixes`
**Status:** SPEC
**Version:** *no bump*
**Effort:** L
**Decisions:** [DL-313](../design-log.md) (this sprint, twelve decisions, the gaps the
pre-registration leaves) ·
[EXP-015](../research/experiments/EXP-015-price-only-ensemble-vs-technical-score.md) (the frozen
pre-registration this tooling applies) · [DL-236](../design-log.md) (the operator's decision) ·
work-queue 90

> **Why no bump.** Every changed file is under `scripts/` or `tests/`. No file under `kernel`,
> `contracts`, `agents`, `orchestration` or `surfaces` changes, so the package ships nothing new
> (S281's and S282's precedent). The full cycle still applies: it adds Python, so branch, `make ci`
> and the gate.

> 🔥 **Start only after EXP-014 has sealed** (operator, 2026-10-22: *"the sprint will run after the
> current session experiment finishes"*). EXP-014's replay arms run on this laptop until its
> `run.log` reads `SEALED`; this sprint's `make ci` and break runs are heavy, and two heavy jobs at
> once overheated the machine on 2026-10-21. The handover block repeats this.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

### The rule

1. Read the law books of the agents whose code this tooling **calls** (it changes none of them):
   `agents/scanner/laws/laws.md` (the filters, `apply_filters`), `agents/analyst/laws/laws.md`
   (the score, `score_candidate`), and `docs/laws/conventions.md`.
2. Read [DL-313](../design-log.md) whole and EXP-015 whole. EXP-015's *Purpose* and *Process* are
   frozen: never edit them.
3. Fill the **Law reading record** below before the first test.

### 🩹 The law-cycle question — answered

**No.** Nothing under `contracts/` changes and no agent gains a guarantee: the tooling is scripts
that call the scanner's and the analyst's existing functions as the S235 replay does. No law
amendment, no ledger row, no drift row.

### Element → law map

| Element | Laws to read | Clause it touches | Why |
| --- | --- | --- | --- |
| The primary universe | `agents/scanner/laws/laws.md` | none changed; `apply_filters` is called as `scripts/replay_day.py` calls it | the survivors are the universe EXP-015 ranks |
| The baseline | `agents/analyst/laws/laws.md` | none changed; `score_candidate(...).technical_score` | the baseline is the fleet's own score, never re-implemented |
| Statistics and stages | `docs/laws/conventions.md` | none | scripts carry no agent clause (S282's precedent) |

---

## Goal

One command per stage runs EXP-015 as its pre-registration fixes it: **`panel`** builds a row for
every line and session of the S235 cache (the scanner's survivors as the primary universe, the lines
with 253 bars as the secondary, the analyst's technical score as the baseline, the twenty features
and the forward returns); **`walk-forward`** fits the three models on seven expanding annual folds
with the purge and embargo, scores the ensemble against the baseline, runs the shuffled-target
control and writes bars 1 and 2; **`holdout`** touches 2025-01-02 onward once, only after a recorded
walk-forward whose control passed, and writes bar 3 and the verdict. Outputs stay outside the repo.

## Why (context)

EXP-015 was pre-registered on 2026-09-27 (DL-236, work-queue 90) and has never run: no code exists
for it. It is the one large measurement that does not wait for the fidelity PASS (its question does
not depend on the replay matching the fleet), and its tooling is scripts only, so it touches no
fidelity decision path. A pass enters the forecaster's shadow loop (a later sprint); a fail builds
nothing.

### Measured, 2026-10-22 — read these before designing

| Fact | Value | Source |
| --- | --- | --- |
| The analyst's per-name score | `score_candidate(...)` blends `score_technical` with relative strength at the pack's weight (0.20); the replay's recommendations carry its `technical_score` | *[measured, read]* `agents/analyst/domain/scoring.py:52-130`, `recommend.py:167` |
| The fleet's analyst scores only the scanner's top 25 | `SCANNER_CANDIDATE_CAP` 25 | *[measured]* `orchestration/packs/trading_tunables.json:6` |
| One `score_candidate` call on 300 bars | 2.43 ms | *[measured]* main venv, 50 calls |
| The prototype's panel on a synthetic cache | 240 rows (201 primary) in 1.16 s, 4.8 ms a row | *[measured]* `build_panel`, 8 lines × 20 sessions |
| The full panel | about 1.2 M rows, 1.5 to 2 hours in one process | *[estimate]* 480 lines × 2,446 scored sessions at 4.8 ms |
| LightGBM | 4.7.0 in the `forecaster` extra only; CI's `uv sync --frozen` installs the dev group, without it; scikit-learn in no environment | *[measured]* `pyproject.toml:30`, `.github/workflows/ci.yml`, import checks |
| numpy and SciPy | numpy ≥ 2.4 in the dev group; SciPy absent in CI | *[measured]* `pyproject.toml` |
| What the gate reads in `scripts/` | ruff, format, module size (200) and module headers; not mypy, not coverage | *[measured]* `Makefile` `PKGS`, `pyproject.toml` `--cov` list |
| Known adjustment errors | 4: TGNA 2017-06-01, RTX 2020-04-03, APTV 2017-12-05, SW 2016-05-16 | *[measured]* `scripts/sp500_known_moves.csv` |
| The relative-strength feature | `rs_120` ranks identically to `ret_120` within a session (SPY's return is the same for every name) | *[derived]* kept: the feature list is frozen |
| S250's bootstrap | `seeded`, `stationary_draws`, `percentile_interval` in `scripts/replay_verdict_stats.py`, reused unchanged | *[measured, read]* |
| The prototype | `make ci` exit 0: 5,321 passed, 9 skipped, 100.00 %, audit clean | *[measured]* `../ta-s289-proto` `e6a231f2`, after EXP-014 sealed |
| The planted breaks against the planner's tests | 36 of 36 red (the first run 33 of 36: B23, B25 and B28 stayed green, so A14 and A16 were strengthened; the Test plan rows say how) | *[measured]* `s289_breaks.py` on `27190561` |
| F1, the 2016–17 pilot | 8,804 rows (6,928 primary, 7,463 secondary); panel `3266c6dc67fa059d`, record `d519ce88f41e0274`; a rerun byte-identical; control passed | *[measured]* `s289_f1.py`, main venv (LightGBM 4.7.0) |

## Scope — and what is deliberately NOT here

Thirteen new files under `scripts/` (the Appendix) and the builder's tests under `tests/`. Nothing
else changes.

### Out of scope (do NOT build this sprint)

- **Running EXP-015.** The planner runs it after the merge (Sequencing), one heavy job at a time.
- **The shadow loop.** A pass feeds a later spec; live shadowing waits on work-queue 89.
- **Any agent, contract or pack change**, and any change to S235's, S250's or S281's scripts.

### The road not taken (LAW-06)

Recorded in DL-313 with each decision: re-implementing the technical score (the pre-registration
forbids it); scoring only the capped 25 (the pre-registration names the survivors); scikit-learn's
LightGBM wrapper (installed nowhere); a CSV panel (about 1.2 M rows); a pilot inside the scored
folds (it would read test data before the run).

---

## The design decisions — made, and recorded in DL-313

D1 the panel offers each session as the replay does; D2 the baseline is `score_candidate`'s
`technical_score`; D3 the feature definitions the list leaves open; D4 missing values; D5 the four
adjustment errors; D6 ranks and the IC floor; D7 LightGBM's call; D8 the composite's signs; D9 the
folds; D10 inference, the bar and the long-only top decile; D11 the stages and their guards; D12 no
bump. Read them in [DL-313](../design-log.md).

---

## Blast radius — measured 2026-10-22

| Path | Change | Who else reads it |
| --- | --- | --- |
| `scripts/exp015*.py` (13 new) | the tooling | nothing: new files |
| `tests/test_exp015_*.py`, `tests/exp015_fixtures.py` (new) | the builder's tests | `make ci` |
| `scripts/replay_*`, `scripts/sp500_*` | read, imported, unchanged | S235's replay, EXP-014, EXP-022 |
| `agents/scanner`, `agents/analyst` | imported, unchanged | the fleet |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. DL-313 and EXP-015 are already recorded; read them. Do not edit either.
3. **Write the tests first** under the names and files of the Test plan, and run them on the unchanged
   tree: every one is red (each file fails to import `scripts.exp015*`). Paste the output.
4. **Apply the Appendix exactly.** Change nothing else under `scripts/`.
5. **Plant the breaks** B01 to B36 (Traps), one at a time; each must turn at least one of your tests
   red.
6. **`make ci` green**, redirected to a file.
7. **Fill the handback sections.**

---

## Test plan

Files: `tests/test_exp015_features.py` (A1–A4), `tests/test_exp015_ranks.py` (A5–A8),
`tests/test_exp015_models.py` (A9–A12), `tests/test_exp015_measure.py` (A13–A17),
`tests/test_exp015_panel.py` (A18–A20), `tests/test_exp015_stages.py` (A21–A24), and a helper
`tests/exp015_fixtures.py` (seeded synthetic bars, a small `ReplayContext` the replay's own code
reads, and a panel with a planted signal in `ret_5`). LightGBM is not installed in CI: test the
models through an injected trainer, and A12 through a stand-in `lightgbm` module in `sys.modules`.
Every test is red on the unchanged tree. Each docstring cites its ID (`S289-A<n>`).

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | returns and the history they need | a seeded walk of 300 bars | `ret_5`, `ret_252_21` (the close 21 back over the close 252 back), `dist_252_high` (over 252 highs), `rs_120` by hand; NaN before each has its history; the fifteen names in `LINE_FEATURES` order |
| A2 | risk, volume and beta | a line whose returns are twice SPY's; volumes 1, 2, 3 … | `vol_20` (log returns, ddof 1), `beta_60` 2 and `resvol_60` 0, NaN at bar 59, `volratio_5_60`, `dollar_volume` (close × volume, 20), `atr_pct` (14-bar mean true range over the close) |
| A3 | 🎯 no feature reads a later bar | every bar after session d tripled | every feature at and before d unchanged |
| A4 | forward returns and masks | 40 sessions; one bar removed; a move at session 20 | d+1's open to d+h's close at 5 and 10; NaN past the calendar and across a missing bar; features masked from the move for 252 sessions, targets when (d, d+20] holds it |
| A5 | ranks within groups | ties, a NaN, two lone values | average ranks scaled to [0, 1]; NaN and a lone value 0.5 |
| A6 | twenty ranked features, sector ranks | 3 sessions × 8 lines, two sectors and none | 20 columns in `FEATURES` order; a line column ranked within the session; a return ranked within its sector; no sector 0.5 |
| A7 | per-session rank IC | four sessions | +1 same order, −1 reversed; 9 names: no IC; flat prediction: no IC |
| A8 | 🎯 folds, purge, embargo, holdout | 1,300 weekdays from 2016-01-04 | test 2018 trains through the 16th session before its first; the train window expands from the first session; holdout to the last session; a year with no session refused |
| A9 | the composite's signs | a planted signal; its mirror `1 − x` | the signal's sign +1, the mirror's −1; the mirror's composite equals the original's |
| A10 | ridge is closed form | the planted panel | β solves (XᶜᵀXᶜ + λI)β = Xᶜᵀ(y − ȳ) on the target's per-session ranks, λ = 1.0 |
| A11 | the ensemble | the planted panel, a stub booster | four predictions in order; the ensemble the mean of the three per-session ranks; its IC above 0.3 |
| A12 | 🎯 LightGBM's fixed settings | a stand-in `lightgbm` module | `train(LGBM_PARAMS, Dataset(x, label=y), num_boost_round=200)`; depth 3, rate 0.05, 31 leaves, 500 per leaf, fraction 0.8, seed 0 |
| A13 | the decile spread | 20 names, and a session of 9 | the top tenth's mean target minus the bottom's; the 9-name session skipped |
| A14 | 🎯 the net top decile | two rebalances; names with different returns; the same name, then another | the top-ranked name is the one held, never the bottom; 25 bps on each unit of weight traded; a held name trades nothing; a swap trades two units |
| A15 | the bootstrap takes every 10th session | 300 differences | S250's draws on every 10th, seed 0: the interval equals `percentile_interval` of those means |
| A16 | 🎯 bars and verdicts | seven folds; a null and a leaking control; a small steady gain; a failed holdout | bar 1 at 0.01 with its interval (a mean of 0.005 whose interval is above 0 is not bar 1); bar 2 at 5 of 7; bar 3; `PENDING HOLDOUT`, `PASS`, `FAIL` (bars 1 and 2 with bar 3 failed), `STOPPED` |
| A17 | the control shuffles within sessions | 5 sessions × 12 lines | each session keeps its own returns, reordered; features and baseline unchanged; the same seed, the same order |
| A18 | 🎯 the primary rows are the scanner's survivors | a synthetic cache, 6 sessions | per session, primary = `apply_filters` on the replay's offered bars; some rows not primary |
| A19 | 🎯 the baseline is the replay's | the same | each recommendation's `technical_score` from `run_replay_day` equals the row's baseline |
| A20 | secondary, features, masks, sectors | the same, a move on L03 | the 253-bar flag; the row's features equal `line_features` at its bar; L03's rows from the move masked; `rows_without_sector` counted |
| A21 | the panel stage's record | a stubbed cache loader and checksums | `panel.json` names the commit, the checksums and the saved panel's digest |
| A22 | 🎯 a stable walk-forward | a planted panel, two folds, a stub booster | two runs write the same bytes and return the file's SHA-256; control passed; bars read; `PENDING HOLDOUT` |
| A23 | 🎯 the holdout is touched once, when earned | the walk-forward of A22 | a wrong digest refused; a second touch refused; a `STOPPED` walk-forward refused |
| A24 | a dirty tree and the command line | `RepoState(dirty=True)`; argv | refused as uncommitted; an `--out` inside the worktree refused; `panel` without `--cache` and `holdout` without its digest exit 2 |

---

## Success factors

- [ ] On the F1 pilot (planner, `s289_f1.py`) the built tree prints the prototype's panel and record
      digests, byte for byte (`3266c6dc…`, `d519ce88…`).
- [ ] A1–A24 pass, each docstring citing its ID.
- [ ] B01–B36 each turn at least one of the builder's tests red (planner re-runs `s289_breaks.py`).
- [ ] The Appendix applied exactly: all 13 production blobs equal the prototype's.
- [ ] No existing file changed; every new module under 200 lines after formatting.
- [ ] `make ci` exit 0 (the remote gate).

---

## Traps

🪤 **The baseline is called, never written.** `score_candidate(...).technical_score` with no
fundamentals and no news; reading `score_technical` directly misses the relative-strength blend
(A19, B31).
🪤 **The primary universe is every survivor**, not the capped 25 the analyst would see (A18, B30).
🪤 **No feature reads a bar after its session** (A3, B05). The forward returns read the future by
design and only as targets.
🪤 **The train window ends fifteen sessions before the test begins** (purge 10, embargo 5; A8, B16).
🪤 **Inference takes every 10th session** (A15, B24); the point estimate takes them all.
🪤 **The control passes when its interval contains 0**; a failed control stops the experiment and
the holdout refuses (A16, A23).
🪤 **The holdout is touched once.** The stage refuses a second touch, a walk-forward file whose
SHA-256 is not the one given, and a `STOPPED` walk-forward (A23).
🪤 **LightGBM is absent in CI** and is imported only inside `lightgbm_trainer`; never import it at
module level, and never add it to a group.
🪤 **Scripts are outside coverage and mypy**: only your tests and the breaks prove a line is reached.
🪤 **Ruff format grows files**: measure module size after formatting.

The breaks, each an exact replacement applied alone to the built tree (the planner re-runs them with
`s289_breaks.py` against your tests alone):

| # | File | Replace | With |
| --- | --- | --- | --- |
| B01 | `exp015_features.py` | `_shift(closes, 21) / _shift(closes, 252)` | `_shift(closes, 20) / _shift(closes, 252)` |
| B02 | `exp015_features.py` | `closes / _trailing(np.max, highs, 252)` | `closes / _trailing(np.max, highs, 251)` |
| B03 | `exp015_features.py` | `return np.std(windows, axis=axis, ddof=1)` | `return np.std(windows, axis=axis, ddof=0)` |
| B04 | `exp015_features.py` | `_beta_residual(simple, spy_simple, 60)` | `_beta_residual(simple, spy_simple, 59)` |
| B05 | `exp015_features.py` | `closes / _trailing(np.max, highs, 252) - 1.0` | `closes / np.maximum(_trailing(np.max, highs, 252), np.r_[highs[1:], highs[-1]]) - 1.0` |
| B06 | `exp015_spec.py` | `ATR_SESSIONS = 14` | `ATR_SESSIONS = 13` |
| B07 | `exp015_features.py` | `_trailing(np.mean, volumes, 5), _trailing(np.mean, volumes, 60)` | `_trailing(np.mean, volumes, 10), _trailing(np.mean, volumes, 60)` |
| B08 | `exp015_features.py` | `_trailing(np.mean, closes * volumes, DOLLAR_VOLUME_SESSIONS)` | `_trailing(np.mean, volumes, DOLLAR_VOLUME_SESSIONS)` |
| B09 | `exp015_targets.py` | `position.get(sessions[j + 1]) if` | `position.get(sessions[j]) if` |
| B10 | `exp015_targets.py` | `position.get(sessions[j + horizon])` | `position.get(sessions[j + horizon - 1])` |
| B11 | `exp015_targets.py` | `targets[i] \|= j < m <= j + longest` | `targets[i] \|= j <= m <= j + longest` |
| B12 | `exp015_ranks.py` | `out = np.full(len(values), 0.5)` | `out = np.full(len(values), 0.0)` |
| B13 | `exp015_ranks.py` | `np.where(size > 1, average / np.maximum(size - 1, 1), 0.5)` | `np.where(size > 1, position / np.maximum(size - 1, 1), 0.5)` |
| B14 | `exp015_ranks.py` | `ranked[no_sector] = 0.5` | *(delete the line)* |
| B15 | `exp015_spec.py` | `MIN_NAMES = 10` | `MIN_NAMES = 9` |
| B16 | `exp015_folds.py` | `gap = PURGE_SESSIONS + EMBARGO_SESSIONS` | `gap = PURGE_SESSIONS` |
| B17 | `exp015_models.py` | `(x - 0.5) @ self.signs / len(self.signs)` | `(x - 0.5) @ np.abs(self.signs) / len(self.signs)` |
| B18 | `exp015_models.py` | `centred.T @ centred + RIDGE_LAMBDA * np.eye` | `centred.T @ centred + 0.0 * np.eye` |
| B19 | `exp015_models.py` | `centred.T @ (y - y.mean())` | `centred.T @ (target - target.mean())` |
| B20 | `exp015_models.py` | `ranks = [group_ranks(value, sessions) for value in models.values()]` | `ranks = list(models.values())` |
| B21 | `exp015_spec.py` | `"min_data_in_leaf": 500,` | `"min_data_in_leaf": 20,` |
| B22 | `exp015_evaluate.py` | `value *= 1.0 + gross - traded * COST_BPS / 10_000` | `value *= 1.0 + gross - COST_BPS / 10_000` |
| B23 | `exp015_evaluate.py` | `top = rows[np.argsort(-prediction[rows], kind="stable")[:k]]` | `top = rows[np.argsort(prediction[rows], kind="stable")[:k]]` |
| B24 | `exp015_rule.py` | `values = list(diffs.values())[::STEP_SESSIONS]` | `values = list(diffs.values())` |
| B25 | `exp015_rule.py` | `bar1 = mean >= BAR_IC_DIFFERENCE and` | `bar1 = mean >= 0.0 and` |
| B26 | `exp015_rule.py` | `"bar2": won >= BAR_FOLDS_WON,` | `"bar2": won > BAR_FOLDS_WON,` |
| B27 | `exp015_rule.py` | `isinstance(low, float) and isinstance(high, float) and low <= 0.0 <= high` | `True` |
| B28 | `exp015_rule.py` | `walk["bar1"] and walk["bar2"] and holdout["bar3"]` | `walk["bar1"] and walk["bar2"]` |
| B29 | `exp015_store.py` | `order[begin:end] = begin + rng.permutation(end - begin)` | `order[:] = rng.permutation(len(order))` |
| B30 | `exp015_panel.py` | `primary = {survivor.ticker for survivor in survivors}` | `primary = set(offered.members)` |
| B31 | `exp015_panel.py` | `).technical_score` | `).confidence` |
| B32 | `exp015_panel.py` | `features[feature_mask] = np.nan` | *(delete the line)* |
| B33 | `exp015_stages.py` | `if (out / HOLDOUT).exists():` | `if False:` |
| B34 | `exp015_stages.py` | `or hashlib.sha256(path.read_bytes()).hexdigest() != walk_forward_sha256` | `or False` |
| B35 | `exp015_stages.py` | `if state.dirty:` | `if False:` |
| B36 | `exp015.py` | `out = refuse_worktree_out(args.out)` | `out = args.out` |

---

## Guardrails (every sprint)

- No network; never a bare `uv sync`. No change outside `scripts/exp015*.py`, `tests/`, this spec and
  its README row.
- No `noqa` beyond the Appendix's; no `# type: ignore` in production code; no module at 200 lines.
- Never measure `make ci` through a pipe: redirect to a file and read the file.
- Never write output inside the worktree.

---

## Sequencing after merge (the planner's)

1. Review: CodeQL set-diff against the last merged branch; production blobs equal
   `prototype_blobs.txt`; the planner's tests on the built tree; the breaks against the builder's
   tests alone.
2. F1 from the main checkout against the built tree (`s289_f1.py`): must equal `f1_proto.txt`.
3. `make gate-ran` from `../ta-s289`; fast-forward `main`; no tag (no bump). No deploy.
4. **The run** (planner, one heavy job at a time on this laptop): `panel` (about 1.5 to 2 hours
   *[estimate]*), then `walk-forward`; record its result in EXP-015 *before* the holdout; then
   `holdout` once with the recorded SHA-256. Outputs in OneDrive
   `trading-agents-data/experiments/EXP-015/`.

---

## Handover — paste this to Codex

```text
Start only after EXP-014's arms have sealed: the last line of
C:\Users\yury_\OneDrive\trading-agents-data\exp014-2026-10-21\run.log must read SEALED. Read that
one line and nothing else in that folder. If it does not read SEALED, stop and say so. This laptop
overheats with two heavy jobs at once, and your make ci is a heavy job.

You are building Sprint 289 in the worktree ../ta-s289, on the branch
sprint-289-exp-015-has-the-tooling-its-pre-registration-fixes. Never work on main. The worktree
and its venv are ready; never run a bare `uv sync` (it needs the network and you have none).

Read docs/sprints/sprint-289-exp-015-has-the-tooling-its-pre-registration-fixes.md, whole, before
anything else. It is the spec, and its bottom sections are your handback. The Appendix holds the
production code, which you apply exactly. Your work is the tests and the evidence.

In order:
1. Read agents/scanner/laws/laws.md, agents/analyst/laws/laws.md, docs/laws/conventions.md, DL-313
   in docs/design-log.md and
   docs/research/experiments/EXP-015-price-only-ensemble-vs-technical-score.md. Fill the Law
   reading record in the spec BEFORE any code. The law-cycle answer is No.
2. Write tests/exp015_fixtures.py and the tests A1 to A24 under the files the Test plan names, each
   docstring citing its ID (S289-A<n>). Run them on the unchanged tree and paste the output into
   the Closeout: every one is red, by import.
3. Apply the Appendix exactly (thirteen new files under scripts/). Change no existing file.
4. Plant the breaks B01 to B36 one at a time (the table in the spec's Traps). Each must turn at
   least one of your tests red; restore each before the next. Record each in the Closeout.
5. No version bump, no uv.lock change. Run make ci redirected to a file and read the file. If the
   dependency audit is the only step that fails for want of network, say so; the planner runs it.
   Paste only each step's command and verdict line into the Closeout, not the whole log.
6. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in the sprint's
   row of docs/sprints/README.md. Commit on the branch if your sandbox lets you write the
   repository's git directory; if not, leave the tree uncommitted and say so. Do not edit
   docs/STATE.md, docs/design-log.md, docs/work-queue.md or EXP-015.

DO NOT: reach the network; change anything under kernel/, contracts/, agents/, orchestration/ or
surfaces/; change any existing file under scripts/ or tests/; bump the version; import lightgbm
anywhere but where the Appendix does; let any module, test files included, reach 200 lines;
measure make ci through a pipe; write output inside the worktree.

Traps: the baseline is score_candidate's technical_score, never re-implemented; the primary
universe is every survivor; no feature reads a later bar; the train window ends fifteen sessions
before the test; inference takes every 10th session; the holdout is touched once; LightGBM is not
installed in CI, so stub the trainer and stand in for the module in A12; scripts are outside
coverage, so only the tests and the breaks prove a line is reached; ruff format grows files.

Two tiers when something does not fit. A wrong command, count, path or line number whose intent is
plain: correct it, record it in Return notes, and carry on. A law that contradicts the spec, an
existing test failing, or a measurement in the spec that does not reproduce: STOP and report. State
anything not done as "not done" or "verified failing". Never write a Result for work you have not
done.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output (step lines and verdicts, not whole logs).
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Laws read (file + sections) | Clause(s) that govern it | What the law requires that the code must honour |
| --- | --- | --- | --- |
| The primary universe | | | |
| The baseline | | | |
| Statistics and stages | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** <Yes/No + what it owed and what was done>

**Contradictions found between a law and this spec:** <none | what, and what you did>

**Laws found silent where a decision was needed:** <none | what, and the drift row filed>

**Clauses that were ⬜ and are now proven:** <IDs, and the rollup in ledger.md + INDEX.md>

---

## Test plan results — fill at handback

| # | Test name | Pass/Fail | Notes |
| --- | --- | --- | --- |
| A1 … A24 | | | |

**Tests added beyond the plan:** <none | what and why>

---

## Closeout — evidence

**Status:** <BUILT | MERGED>

**Tree the proofs ran in (and `.env` present?):** <path, branch, .env yes/no>

**Result:** <what is now true, in the artefact's own words — not the intent restated>

**Files changed:** <list>

**Design decisions:** recorded as [`DL-313`](../design-log.md).

**Proof — the red run first:** <the unchanged-tree run, pasted>

**Proof — the green run:** <the applied-tree run, pasted>

**Guards planted:** <B01–B36: what was planted, that it failed, that it was restored>

**Module line counts:** <file **n**, …>

**Not met / verified failing:** <plainly, or "none">

---

## Return notes

<corrections made under the first tier, and anything the planner should know>

---

## Appendix — the change, measured on the planner's prototype

Apply with `git apply` from the worktree root. Thirteen new files; no existing file changes.

```diff
diff --git a/scripts/exp015.py b/scripts/exp015.py
new file mode 100644
index 00000000..dd9efae1
--- /dev/null
+++ b/scripts/exp015.py
@@ -0,0 +1,53 @@
+"""Run EXP-015's stages: the panel, the walk-forward, then the holdout once (S289).
+
+Agent: tooling
+Role: the command line for the three stages, each writing outside the worktree.
+External I/O: reads the S235 cache; writes the stages' files under --out.
+
+  uv run python scripts/exp015.py panel --cache <CACHE> --out <OUT>
+  uv run python scripts/exp015.py walk-forward --out <OUT>
+  uv run python scripts/exp015.py holdout --out <OUT> --walk-forward-sha256 <hex>
+"""
+
+from __future__ import annotations
+
+import argparse
+import sys
+from pathlib import Path
+
+sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
+
+from scripts.exp015_stages import (
+    holdout_stage,
+    panel_stage,
+    walk_forward_stage,
+)
+from scripts.replay_outputs import refuse_worktree_out
+
+
+def main(argv: list[str]) -> int:
+    parser = argparse.ArgumentParser(description="Run EXP-015's stages.")
+    parser.add_argument("stage", choices=("panel", "walk-forward", "holdout"))
+    parser.add_argument("--out", type=Path, required=True)
+    parser.add_argument("--cache", type=Path)
+    parser.add_argument("--walk-forward-sha256")
+    args = parser.parse_args(argv)
+    out = refuse_worktree_out(args.out)
+    out.mkdir(parents=True, exist_ok=True)
+    if args.stage == "panel":
+        if args.cache is None:
+            parser.error("panel needs --cache")
+        record = panel_stage(args.cache, out)
+        print(f"panel {record['rows']} rows, sha256 {record['panel_sha256']}")
+    elif args.stage == "walk-forward":
+        print(f"walk_forward.json sha256 {walk_forward_stage(out)}")
+    else:
+        if not args.walk_forward_sha256:
+            parser.error("holdout needs --walk-forward-sha256")
+        record = holdout_stage(out, args.walk_forward_sha256)
+        print(f"holdout written; verdict {record['verdict']}")
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main(sys.argv[1:]))
diff --git a/scripts/exp015_evaluate.py b/scripts/exp015_evaluate.py
new file mode 100644
index 00000000..62056268
--- /dev/null
+++ b/scripts/exp015_evaluate.py
@@ -0,0 +1,118 @@
+"""Score one EXP-015 fold: fit on its train sessions, measure its test (S289).
+
+Agent: tooling
+Role: a fold's per-session rank ICs (ensemble, baseline, components, decay at 5 and
+      20), its decile spreads, its net long-only top deciles, LightGBM's importances.
+External I/O: none.
+"""
+
+from __future__ import annotations
+
+import math
+from typing import TYPE_CHECKING
+
+import numpy as np
+from scripts.exp015_models import Trainer, fit
+from scripts.exp015_ranks import session_ic
+from scripts.exp015_spec import (
+    COST_BPS,
+    DECILES,
+    HORIZON,
+    HORIZONS,
+    MIN_NAMES,
+    STEP_SESSIONS,
+)
+
+if TYPE_CHECKING:
+    from scripts.exp015_folds import Fold
+    from scripts.exp015_store import Panel
+
+_BARRED = HORIZONS.index(HORIZON)
+
+
+def score_fold(
+    panel: Panel, x: np.ndarray, fold: Fold, trainer: Trainer
+) -> dict[str, object]:
+    """One fold's record; `x` is the universe's ranked features, row for row."""
+    train = np.isin(panel.sessions, fold.train)
+    test = np.isin(panel.sessions, fold.test)
+    excess = panel.excess
+    fitted = fit(x[train], excess[train, _BARRED], panel.sessions[train], trainer)
+    days, lines = panel.sessions[test], panel.lines[test]
+    scores = fitted.predict(x[test], days) | {"baseline": panel.baseline[test]}
+    target = excess[test, _BARRED]
+    ic = {name: session_ic(value, target, days) for name, value in scores.items()}
+    decay = {
+        f"{name}_h{h}": session_ic(scores[name], excess[test, k], days)
+        for name in ("ensemble", "baseline")
+        for k, h in enumerate(HORIZONS)
+        if h != HORIZON
+    }
+    rebalances = tuple(sorted(set(days.tolist())))[::STEP_SESSIONS]
+    raw = panel.returns[test, _BARRED]
+    return {
+        **fold.record(),
+        "rows_train": int(train.sum()),
+        "rows_test": int(test.sum()),
+        "ic": ic,
+        "decay": decay,
+        "decile_spread": {
+            name: decile_spread(scores[name], target, days)
+            for name in ("ensemble", "baseline")
+        },
+        "top_decile": {
+            name: top_decile(scores[name], raw, days, lines, rebalances)
+            for name in ("ensemble", "baseline")
+        },
+        "importances": fitted.importances(),
+    }
+
+
+def decile_spread(
+    prediction: np.ndarray, target: np.ndarray, days: np.ndarray
+) -> float:
+    """Mean over sessions of the top decile's mean target minus the bottom decile's."""
+    spreads = []
+    for day in sorted(set(days.tolist())):
+        rows = np.flatnonzero(
+            (days == day) & np.isfinite(prediction) & np.isfinite(target)
+        )
+        if len(rows) < MIN_NAMES:
+            continue
+        k = math.ceil(len(rows) / DECILES)
+        ordered = rows[np.argsort(-prediction[rows], kind="stable")]
+        spreads.append(float(target[ordered[:k]].mean() - target[ordered[-k:]].mean()))
+    return float(np.mean(spreads)) if spreads else math.nan
+
+
+def top_decile(
+    prediction: np.ndarray,
+    raw: np.ndarray,
+    days: np.ndarray,
+    lines: np.ndarray,
+    rebalances: tuple[str, ...],
+) -> dict[str, float]:
+    """Equal weight in the top decile at each rebalance, COST_BPS a side."""
+    weights: dict[str, float] = {}
+    value, gross_value, periods = 1.0, 1.0, 0
+    for day in rebalances:
+        rows = np.flatnonzero(
+            (days == day) & np.isfinite(prediction) & np.isfinite(raw)
+        )
+        if len(rows) < MIN_NAMES:
+            continue
+        k = math.ceil(len(rows) / DECILES)
+        top = rows[np.argsort(-prediction[rows], kind="stable")[:k]]
+        new = {str(line): 1.0 / k for line in lines[top]}
+        traded = sum(
+            abs(new.get(n, 0.0) - weights.get(n, 0.0)) for n in set(new) | set(weights)
+        )
+        gross = float(raw[top].mean())
+        value *= 1.0 + gross - traded * COST_BPS / 10_000
+        gross_value *= 1.0 + gross
+        weights, periods = new, periods + 1
+    return {
+        "net_return": value - 1.0,
+        "gross_return": gross_value - 1.0,
+        "periods": periods,
+    }
diff --git a/scripts/exp015_features.py b/scripts/exp015_features.py
new file mode 100644
index 00000000..7bcea5f6
--- /dev/null
+++ b/scripts/exp015_features.py
@@ -0,0 +1,121 @@
+"""EXP-015's fifteen line features, read only from bars up to each session (S289).
+
+Agent: tooling
+Role: turn one line's bars into one array per feature, aligned to its bars; a value
+      that needs more history than the line has is NaN.
+External I/O: none.
+"""
+
+from __future__ import annotations
+
+from typing import TYPE_CHECKING
+
+import numpy as np
+from numpy.lib.stride_tricks import sliding_window_view
+from scripts.exp015_spec import ATR_SESSIONS, DOLLAR_VOLUME_SESSIONS, LINE_FEATURES
+
+if TYPE_CHECKING:
+    from collections.abc import Callable
+
+
+def line_features(
+    highs: np.ndarray,
+    lows: np.ndarray,
+    closes: np.ndarray,
+    volumes: np.ndarray,
+    spy_closes: np.ndarray,
+) -> dict[str, np.ndarray]:
+    """The line features by name, per bar; `spy_closes` is SPY on the line's dates."""
+    returns = {k: _back_return(closes, k) for k in (5, 20, 60, 120)}
+    simple = _back_return(closes, 1)
+    logs = np.log(closes / _shift(closes, 1))
+    spy_simple = _back_return(spy_closes, 1)
+    beta, residual = _beta_residual(simple, spy_simple, 60)
+    features = {
+        "ret_5": returns[5],
+        "ret_20": returns[20],
+        "ret_60": returns[60],
+        "ret_120": returns[120],
+        "ret_252_21": _shift(closes, 21) / _shift(closes, 252) - 1.0,
+        "dist_252_high": closes / _trailing(np.max, highs, 252) - 1.0,
+        "vol_20": _trailing(_std, logs, 20),
+        "vol_60": _trailing(_std, logs, 60),
+        "atr_pct": _trailing(np.mean, _true_range(highs, lows, closes), ATR_SESSIONS)
+        / closes,
+        "beta_60": beta,
+        "resvol_60": residual,
+        "volratio_5_60": _ratio(
+            _trailing(np.mean, volumes, 5), _trailing(np.mean, volumes, 60)
+        ),
+        "volratio_20_120": _ratio(
+            _trailing(np.mean, volumes, 20), _trailing(np.mean, volumes, 120)
+        ),
+        "dollar_volume": _trailing(np.mean, closes * volumes, DOLLAR_VOLUME_SESSIONS),
+        "rs_120": (1.0 + returns[120]) / (1.0 + _back_return(spy_closes, 120)) - 1.0,
+    }
+    return {name: features[name] for name in LINE_FEATURES}
+
+
+def _shift(values: np.ndarray, lag: int) -> np.ndarray:
+    """values[i - lag] at i, NaN where i < lag."""
+    out = np.full(values.shape, np.nan)
+    if lag < len(values):
+        out[lag:] = values[: len(values) - lag]
+    return out
+
+
+def _back_return(values: np.ndarray, lag: int) -> np.ndarray:
+    return values / _shift(values, lag) - 1.0
+
+
+def _trailing(
+    reduce: Callable[..., np.ndarray], values: np.ndarray, window: int
+) -> np.ndarray:
+    """The trailing reduce over `window` values; NaN before a full window or a NaN."""
+    out = np.full(values.shape, np.nan)
+    if len(values) >= window:
+        out[window - 1 :] = reduce(sliding_window_view(values, window), axis=1)
+    return out
+
+
+def _std(windows: np.ndarray, axis: int) -> np.ndarray:
+    return np.std(windows, axis=axis, ddof=1)
+
+
+def _true_range(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> np.ndarray:
+    previous = _shift(closes, 1)
+    ranges = np.vstack(
+        (highs - lows, np.abs(highs - previous), np.abs(lows - previous))
+    )
+    out = np.max(ranges, axis=0)
+    out[0] = np.nan  # the first bar has no previous close
+    return out
+
+
+def _ratio(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
+    with np.errstate(divide="ignore", invalid="ignore"):
+        out = numerator / denominator
+    out[~np.isfinite(out)] = np.nan
+    return out
+
+
+def _beta_residual(
+    returns: np.ndarray, market: np.ndarray, window: int
+) -> tuple[np.ndarray, np.ndarray]:
+    """The trailing OLS beta on the market, and the residuals' standard deviation."""
+    beta = np.full(returns.shape, np.nan)
+    residual = np.full(returns.shape, np.nan)
+    if len(returns) < window:
+        return beta, residual
+    y = sliding_window_view(returns, window)
+    x = sliding_window_view(market, window)
+    xc = x - x.mean(axis=1, keepdims=True)
+    yc = y - y.mean(axis=1, keepdims=True)
+    with np.errstate(divide="ignore", invalid="ignore"):
+        slope = (xc * yc).sum(axis=1) / (xc * xc).sum(axis=1)
+    spread = np.std(yc - slope[:, None] * xc, axis=1, ddof=1)
+    beta[window - 1 :] = slope
+    residual[window - 1 :] = spread
+    beta[~np.isfinite(beta)] = np.nan
+    residual[~np.isfinite(beta)] = np.nan
+    return beta, residual
diff --git a/scripts/exp015_folds.py b/scripts/exp015_folds.py
new file mode 100644
index 00000000..e290da99
--- /dev/null
+++ b/scripts/exp015_folds.py
@@ -0,0 +1,63 @@
+"""EXP-015's folds: expanding train, purge and embargo before each test (S289).
+
+Agent: tooling
+Role: name each fold's train and test sessions from the panel's calendar, the train
+      window ending PURGE + EMBARGO sessions before the test begins.
+External I/O: none.
+"""
+
+from __future__ import annotations
+
+from dataclasses import dataclass
+from datetime import date
+from typing import TYPE_CHECKING
+
+from scripts.exp015_spec import EMBARGO_SESSIONS, PURGE_SESSIONS
+
+if TYPE_CHECKING:
+    from collections.abc import Sequence
+
+
+@dataclass(frozen=True)
+class Fold:
+    name: str
+    train: tuple[str, ...]  # ISO sessions
+    test: tuple[str, ...]
+
+    def record(self) -> dict[str, object]:
+        """The fold's date ranges and sizes, as the results record them."""
+        return {
+            "name": self.name,
+            "train_first": self.train[0] if self.train else None,
+            "train_last": self.train[-1] if self.train else None,
+            "train_sessions": len(self.train),
+            "test_first": self.test[0] if self.test else None,
+            "test_last": self.test[-1] if self.test else None,
+            "test_sessions": len(self.test),
+        }
+
+
+def fold(name: str, sessions: Sequence[date], first: date, last: date) -> Fold:
+    """Test on [first, last]; train on every earlier session but purge and embargo."""
+    test = [day for day in sessions if first <= day <= last]
+    if not test:
+        raise ValueError(f"fold {name}: no session in {first}..{last}")
+    start = list(sessions).index(test[0])
+    gap = PURGE_SESSIONS + EMBARGO_SESSIONS
+    train = sessions[: max(start - gap, 0)]
+    return Fold(
+        name, tuple(d.isoformat() for d in train), tuple(d.isoformat() for d in test)
+    )
+
+
+def walk_forward(sessions: Sequence[date], years: Sequence[int]) -> tuple[Fold, ...]:
+    """One annual test fold per year, each with its own expanding train window."""
+    return tuple(
+        fold(str(year), sessions, date(year, 1, 1), date(year, 12, 31))
+        for year in years
+    )
+
+
+def holdout(sessions: Sequence[date], start: date) -> Fold:
+    """The holdout: `start` to the last session, trained on everything before it."""
+    return fold("holdout", sessions, start, sessions[-1])
diff --git a/scripts/exp015_models.py b/scripts/exp015_models.py
new file mode 100644
index 00000000..cc9a51aa
--- /dev/null
+++ b/scripts/exp015_models.py
@@ -0,0 +1,78 @@
+"""EXP-015's three models and their ensemble, at fixed settings (S289).
+
+Agent: tooling
+Role: fit the rank composite, the ridge and the LightGBM regressor on a train fold's
+      ranked features, predict a test fold, and average the three ranks per session.
+External I/O: none; LightGBM is imported only when the real trainer runs.
+"""
+
+from __future__ import annotations
+
+from collections.abc import Callable
+from dataclasses import dataclass
+from typing import Any, Protocol
+
+import numpy as np
+from scripts.exp015_ranks import group_ranks, session_ic
+from scripts.exp015_spec import FEATURES, LGBM_PARAMS, LGBM_ROUNDS, RIDGE_LAMBDA
+
+
+class Booster(Protocol):
+    def predict(self, data: np.ndarray) -> np.ndarray: ...
+    def feature_importance(self, importance_type: str) -> np.ndarray: ...
+
+
+Trainer = Callable[[np.ndarray, np.ndarray], Booster]
+
+
+@dataclass(frozen=True)
+class Fitted:
+    signs: np.ndarray  # the composite's sign per feature, by its train IC
+    ridge_mean: np.ndarray
+    ridge_beta: np.ndarray
+    booster: Booster
+
+    def predict(self, x: np.ndarray, sessions: np.ndarray) -> dict[str, np.ndarray]:
+        """Each model's prediction, and the ensemble: the three ranks' mean."""
+        models = {
+            "composite": (x - 0.5) @ self.signs / len(self.signs),
+            "ridge": (x - self.ridge_mean) @ self.ridge_beta,
+            "lightgbm": np.asarray(self.booster.predict(x), dtype=float),
+        }
+        ranks = [group_ranks(value, sessions) for value in models.values()]
+        return models | {"ensemble": np.mean(ranks, axis=0)}
+
+    def importances(self) -> dict[str, float]:
+        gains = self.booster.feature_importance("gain")
+        return {name: float(gain) for name, gain in zip(FEATURES, gains, strict=True)}
+
+
+def fit(
+    x: np.ndarray, target: np.ndarray, sessions: np.ndarray, trainer: Trainer
+) -> Fitted:
+    """Fit the three on rows with a target; ridge and LightGBM learn its rank."""
+    usable = np.isfinite(target)
+    x, target, sessions = x[usable], target[usable], sessions[usable]
+    signs = np.array([_sign(x[:, k], target, sessions) for k in range(x.shape[1])])
+    y = group_ranks(target, sessions)
+    mean = x.mean(axis=0)
+    centred = x - mean
+    gram = centred.T @ centred + RIDGE_LAMBDA * np.eye(x.shape[1])
+    beta = np.linalg.solve(gram, centred.T @ (y - y.mean()))
+    return Fitted(signs, mean, beta, trainer(x, y))
+
+
+def _sign(feature: np.ndarray, target: np.ndarray, sessions: np.ndarray) -> float:
+    """+1 when the feature's mean train IC is at least 0, else -1 (DL-313 D8)."""
+    ics = list(session_ic(feature, target, sessions).values())
+    return 1.0 if not ics or float(np.mean(ics)) >= 0.0 else -1.0
+
+
+def lightgbm_trainer(x: np.ndarray, y: np.ndarray) -> Booster:
+    """LightGBM's native API at LGBM_PARAMS for LGBM_ROUNDS rounds (no scikit-learn)."""
+    import lightgbm  # the forecaster extra: CI never installs it, so import it here
+
+    params: dict[str, Any] = dict(LGBM_PARAMS)
+    dataset = lightgbm.Dataset(x, label=y, params={"verbosity": -1})
+    booster: Booster = lightgbm.train(params, dataset, num_boost_round=LGBM_ROUNDS)
+    return booster
diff --git a/scripts/exp015_panel.py b/scripts/exp015_panel.py
new file mode 100644
index 00000000..6559e1fd
--- /dev/null
+++ b/scripts/exp015_panel.py
@@ -0,0 +1,161 @@
+"""Build EXP-015's panel from the S235 cache as the replay offers it (S289).
+
+Agent: tooling
+Role: offer each session's members as the replay does (the declared lookback and
+      the history rule), keep the scanner's survivors (primary) and the lines with 253
+      bars (secondary), score each by the analyst's code, attach features and returns.
+External I/O: progress lines on stderr; the cache is read by the caller.
+"""
+
+from __future__ import annotations
+
+import sys
+from collections import Counter
+from dataclasses import dataclass
+from typing import TYPE_CHECKING
+
+import numpy as np
+from scripts.exp015_features import line_features
+from scripts.exp015_spec import HORIZONS, LINE_FEATURES, MIN_SECONDARY_BARS
+from scripts.exp015_store import Panel
+from scripts.exp015_targets import adjustment_masks, forward_returns
+from scripts.replay_history import offer_lines, visible_window
+from scripts.replay_series import benchmark_window, contract_bars, members_on
+
+from agents.analyst.domain.scoring import score_candidate
+from agents.scanner.domain.filters import apply_filters
+from contracts.scanner import Candidate
+
+if TYPE_CHECKING:
+    from collections.abc import Collection, Sequence
+    from datetime import date
+
+    from scripts.replay_cache import ReplayContext
+    from scripts.replay_settings import ReplaySettings
+    from scripts.sp500_bars import BarRow
+
+    from contracts.provider import OHLCVBar
+
+
+@dataclass(frozen=True)
+class _Line:
+    features: np.ndarray  # bars x LINE_FEATURES
+    returns: np.ndarray  # bars x HORIZONS
+    position: dict[date, int]
+
+
+def build_panel(
+    context: ReplayContext,
+    settings: ReplaySettings,
+    line_bars: dict[str, tuple[BarRow, ...]],
+    adjustment_errors: dict[str, tuple[date, ...]],
+    sessions: Sequence[date],
+    lines: Collection[str] | None = None,
+) -> tuple[Panel, dict[str, int]]:
+    """The panel over `sessions`, members limited to `lines` when given; its counts."""
+    every = context.universe.sessions
+    index = {day: j for j, day in enumerate(every)}
+    spy = _spy_forward(context, every, index)
+    prepared = {
+        line: _prepare(rows, context, adjustment_errors.get(line, ()), index, every)
+        for line, rows in line_bars.items()
+        if lines is None or line in lines
+    }
+    rows: list[tuple[object, ...]] = []
+    counts: Counter[str] = Counter()
+    for n, session in enumerate(sessions):
+        members = tuple(
+            m for m in members_on(context.universe, session) if m in prepared
+        )
+        window = visible_window(settings, line_bars, members, session)
+        offered = offer_lines(settings, members, window, ())
+        contract = contract_bars(offered.bars)
+        bench = benchmark_window(context.benchmark, session, offered.bars)
+        survivors, _ = apply_filters(
+            offered.members,
+            contract,
+            bench,
+            {},
+            session,
+            settings.scanner,
+            earnings_horizon_days=None,
+        )
+        primary = {survivor.ticker for survivor in survivors}
+        by_line: dict[str, list[OHLCVBar]] = {}
+        for bar in contract:
+            by_line.setdefault(bar.ticker, []).append(bar)
+        counts["members_not_offered"] += len(members) - len(offered.members)
+        for line in offered.members:
+            prep = prepared[line]
+            pos = prep.position.get(session)
+            if pos is None:
+                continue
+            secondary = pos + 1 >= MIN_SECONDARY_BARS
+            if line not in primary and not secondary:
+                continue
+            candidate = Candidate(ticker=line, rank=1, score=0.0, survived_filters=())
+            score = score_candidate(
+                candidate, tuple(by_line[line]), {}, bench, (), settings.analyst
+            ).technical_score
+            sector = context.sectors.get(line) or ""
+            counts["rows_without_sector"] += not sector
+            flags = (line in primary, secondary, score)
+            arrays = (prep.features[pos], prep.returns[pos], spy[session])
+            rows.append((session.isoformat(), line, sector, *flags, *arrays))
+        if (n + 1) % 100 == 0 or n + 1 == len(sessions):
+            line_out = (
+                f"exp015 panel {session} {n + 1}/{len(sessions)} rows={len(rows)}"
+            )
+            print(line_out, file=sys.stderr, flush=True)
+    return _panel(rows), dict(sorted(counts.items()))
+
+
+def _prepare(
+    rows: tuple[BarRow, ...],
+    context: ReplayContext,
+    moves: tuple[date, ...],
+    index: dict[date, int],
+    every: tuple[date, ...],
+) -> _Line:
+    dates = [row.date for row in rows]
+    column = {
+        name: np.array([getattr(row, name) for row in rows], dtype=float)
+        for name in ("open", "high", "low", "close", "volume")
+    }
+    spy_closes = np.array([context.spy_closes.get(day, np.nan) for day in dates])
+    named = line_features(
+        column["high"], column["low"], column["close"], column["volume"], spy_closes
+    )
+    features = np.column_stack([named[name] for name in LINE_FEATURES])
+    returns = forward_returns(dates, column["open"], column["close"], index, every)
+    feature_mask, target_mask = adjustment_masks(dates, moves, index)
+    features[feature_mask] = np.nan
+    returns[target_mask] = np.nan
+    return _Line(features, returns, {day: i for i, day in enumerate(dates)})
+
+
+def _spy_forward(
+    context: ReplayContext, every: tuple[date, ...], index: dict[date, int]
+) -> dict[date, np.ndarray]:
+    days = [day for day in every if day in context.benchmark]
+    opens = np.array([context.benchmark[day].open for day in days])
+    closes = np.array([context.benchmark[day].close for day in days])
+    returns = forward_returns(days, opens, closes, index, every)
+    out = {day: np.full(len(HORIZONS), np.nan) for day in every}
+    out.update({day: returns[i] for i, day in enumerate(days)})
+    return out
+
+
+def _panel(rows: list[tuple[object, ...]]) -> Panel:
+    columns = list(zip(*rows, strict=True)) if rows else [()] * 9
+    return Panel(
+        np.array(columns[0], dtype=str),
+        np.array(columns[1], dtype=str),
+        np.array(columns[2], dtype=str),
+        np.array(columns[3], dtype=bool),
+        np.array(columns[4], dtype=bool),
+        np.array(columns[5], dtype=float),
+        np.array(columns[6], dtype=float).reshape(-1, len(LINE_FEATURES)),
+        np.array(columns[7], dtype=float).reshape(-1, len(HORIZONS)),
+        np.array(columns[8], dtype=float).reshape(-1, len(HORIZONS)),
+    )
diff --git a/scripts/exp015_ranks.py b/scripts/exp015_ranks.py
new file mode 100644
index 00000000..ea0c96ef
--- /dev/null
+++ b/scripts/exp015_ranks.py
@@ -0,0 +1,84 @@
+"""EXP-015's cross-sectional ranks and per-session Spearman rank IC (S289).
+
+Agent: tooling
+Role: rank a value within each group to [0, 1] (ties averaged; NaN or alone 0.5),
+      build the twenty ranked features of a universe, and give each session's rank IC.
+External I/O: none.
+"""
+
+from __future__ import annotations
+
+from typing import TYPE_CHECKING
+
+import numpy as np
+from scripts.exp015_spec import LINE_FEATURES, MIN_NAMES, RETURN_FEATURES
+
+if TYPE_CHECKING:
+    from scripts.exp015_store import Panel
+
+
+def group_ranks(values: np.ndarray, groups: np.ndarray) -> np.ndarray:
+    """Average rank within each group, scaled to [0, 1]; NaN and singletons 0.5."""
+    out = np.full(len(values), 0.5)
+    finite = np.flatnonzero(np.isfinite(values))
+    if not len(finite):
+        return out
+    codes = np.unique(groups[finite], return_inverse=True)[1]
+    vals = values[finite]
+    order = np.lexsort((vals, codes))
+    s_codes, s_vals = codes[order], vals[order]
+    group_start = np.r_[True, s_codes[1:] != s_codes[:-1]]
+    gid = np.cumsum(group_start) - 1
+    starts = np.flatnonzero(group_start)
+    sizes = np.diff(np.r_[starts, len(order)])
+    position = np.arange(len(order)) - starts[gid]
+    tie_start = group_start | np.r_[True, s_vals[1:] != s_vals[:-1]]
+    tid = np.cumsum(tie_start) - 1
+    average = (np.bincount(tid, weights=position) / np.bincount(tid))[tid]
+    size = sizes[gid]
+    out[finite[order]] = np.where(size > 1, average / np.maximum(size - 1, 1), 0.5)
+    return out
+
+
+def ranked_features(panel: Panel) -> np.ndarray:
+    """rows x FEATURES: line features ranked per session, returns per sector."""
+    columns = [
+        group_ranks(panel.features[:, k], panel.sessions)
+        for k in range(len(LINE_FEATURES))
+    ]
+    sector_groups = np.char.add(np.char.add(panel.sessions, "|"), panel.sectors)
+    no_sector = panel.sectors == ""
+    for name in RETURN_FEATURES:
+        ranked = group_ranks(
+            panel.features[:, LINE_FEATURES.index(name)], sector_groups
+        )
+        ranked[no_sector] = 0.5
+        columns.append(ranked)
+    return np.column_stack(columns)
+
+
+def session_ic(
+    prediction: np.ndarray, target: np.ndarray, sessions: np.ndarray
+) -> dict[str, float]:
+    """Spearman IC per session; at least MIN_NAMES rows with both values, not flat."""
+    usable = np.isfinite(prediction) & np.isfinite(target)
+    days = sessions[usable]
+    if not len(days):
+        return {}
+    x = group_ranks(prediction[usable], days)
+    y = group_ranks(target[usable], days)
+    keys, codes = np.unique(days, return_inverse=True)
+
+    def total(values: np.ndarray) -> np.ndarray:
+        return np.bincount(codes, weights=values, minlength=len(keys))
+
+    n = np.bincount(codes, minlength=len(keys)).astype(float)
+    sx, sy = total(x), total(y)
+    cov = total(x * y) - sx * sy / n
+    vx = total(x * x) - sx * sx / n
+    vy = total(y * y) - sy * sy / n
+    out: dict[str, float] = {}
+    for k, key in enumerate(keys):
+        if n[k] >= MIN_NAMES and vx[k] > 1e-12 and vy[k] > 1e-12:
+            out[str(key)] = float(cov[k] / np.sqrt(vx[k] * vy[k]))
+    return out
diff --git a/scripts/exp015_report.py b/scripts/exp015_report.py
new file mode 100644
index 00000000..fe810d5c
--- /dev/null
+++ b/scripts/exp015_report.py
@@ -0,0 +1,92 @@
+"""EXP-015's result pages: the walk-forward, then the holdout and verdict (S289).
+
+Agent: tooling
+Role: render a stage's JSON record as one Markdown page to check against the bar.
+External I/O: none.
+"""
+
+from __future__ import annotations
+
+from typing import TYPE_CHECKING, Any
+
+from scripts.exp015_spec import BAR_FOLDS_WON, BAR_IC_DIFFERENCE, EXPERIMENT
+
+if TYPE_CHECKING:
+    from collections.abc import Mapping
+
+_HEADER = "| Fold | Train | Test | Ensemble IC | Baseline IC | Spread (ens / base) |"
+_RULE = "| --- | --- | --- | --- | --- | --- |"
+
+
+def walk_forward_page(record: Mapping[str, Any]) -> str:
+    """The walk-forward page: bars 1 and 2, the control, and a row per fold."""
+    reading = record["reading"]
+    boot, control = reading["bootstrap"], reading["control"]
+    lines = [
+        f"# {EXPERIMENT} walk-forward — {record['verdict']}",
+        "",
+        f"Commit `{record['commit']}`, panel `{record['panel_sha256'][:16]}`.",
+        "",
+        "| Bar | Reading | Holds |",
+        "| --- | --- | --- |",
+        f"| 1: mean IC difference >= {BAR_IC_DIFFERENCE}, CI low > 0 | "
+        f"{_num(reading['mean_ic_difference'])} over {reading['sessions']} sessions; "
+        f"[{_num(boot['low'])}, {_num(boot['high'])}] on {boot['sessions']} | "
+        f"{_yes(reading['bar1'])} |",
+        f"| 2: ensemble ahead in >= {BAR_FOLDS_WON} of {reading['folds']} folds | "
+        f"{reading['folds_won']} | {_yes(reading['bar2'])} |",
+        f"| control: shuffled target, CI contains 0 | [{_num(control['low'])}, "
+        f"{_num(control['high'])}] | {_yes(control['passed'])} |",
+        "",
+        _HEADER,
+        _RULE,
+    ]
+    lines += [_fold_row(fold) for fold in record["folds"]]
+    lines += ["", "Secondary universe (descriptive):", ""]
+    lines += [_fold_row(fold) for fold in record["secondary"]]
+    return "\n".join(lines) + "\n"
+
+
+def holdout_page(walk: Mapping[str, Any], record: Mapping[str, Any]) -> str:
+    """The verdict page: bar 3 on the holdout, its net top deciles, the verdict."""
+    reading, fold = record["reading"], record["holdout"]
+    top, bars = fold["top_decile"], walk["reading"]
+    lines = [
+        f"# {EXPERIMENT} — {record['verdict']}",
+        "",
+        f"Walk-forward `{record['walk_forward_sha256'][:16]}` "
+        f"(bars 1 and 2: {_yes(bars['bar1'])}, {_yes(bars['bar2'])}).",
+        "",
+        f"Bar 3: holdout IC difference {_num(reading['mean_ic_difference'])} over "
+        f"{reading['sessions']} sessions; net top decile ensemble "
+        f"{_num(top['ensemble']['net_return'])} vs baseline "
+        f"{_num(top['baseline']['net_return'])}: {_yes(reading['bar3'])}.",
+        "",
+        _HEADER,
+        _RULE,
+        _fold_row(fold),
+        _fold_row(record["secondary"]),
+    ]
+    return "\n".join(lines) + "\n"
+
+
+def _fold_row(fold: Mapping[str, Any]) -> str:
+    ic, spread = fold["ic"], fold["decile_spread"]
+    return (
+        f"| {fold['name']} | {fold['train_first']}..{fold['train_last']} | "
+        f"{fold['test_first']}..{fold['test_last']} | {_num(_mean(ic['ensemble']))} | "
+        f"{_num(_mean(ic['baseline']))} | {_num(spread['ensemble'])} / "
+        f"{_num(spread['baseline'])} |"
+    )
+
+
+def _mean(values: Mapping[str, float]) -> float | None:
+    return sum(values.values()) / len(values) if values else None
+
+
+def _num(value: float | None) -> str:
+    return "n/a" if value is None or value != value else f"{value:.4f}"
+
+
+def _yes(flag: bool) -> str:
+    return "yes" if flag else "no"
diff --git a/scripts/exp015_rule.py b/scripts/exp015_rule.py
new file mode 100644
index 00000000..ae11e4aa
--- /dev/null
+++ b/scripts/exp015_rule.py
@@ -0,0 +1,124 @@
+"""EXP-015's inference and bar: IC differences, bootstrap, folds, holdout (S289).
+
+Agent: tooling
+Role: pool the folds' per-session IC differences, bootstrap every 10th session, read
+      bars 1 and 2 and the shuffled-target control, then bar 3 on the holdout.
+External I/O: none.
+"""
+
+from __future__ import annotations
+
+from typing import TYPE_CHECKING
+
+from scripts.exp015_spec import (
+    BAR_FOLDS_WON,
+    BAR_IC_DIFFERENCE,
+    BLOCK,
+    RESAMPLES,
+    SEED,
+    STEP_SESSIONS,
+)
+from scripts.replay_verdict_stats import percentile_interval, seeded, stationary_draws
+
+if TYPE_CHECKING:
+    from collections.abc import Mapping, Sequence
+
+
+def differences(folds: Sequence[Mapping[str, object]]) -> dict[str, float]:
+    """Ensemble IC minus baseline IC on each test session both have, across folds."""
+    out: dict[str, float] = {}
+    for record in folds:
+        ic = record["ic"]
+        assert isinstance(ic, dict)
+        ensemble, baseline = ic["ensemble"], ic["baseline"]
+        out.update(
+            {day: ensemble[day] - baseline[day] for day in ensemble if day in baseline}
+        )
+    return dict(sorted(out.items()))
+
+
+def interval(
+    diffs: Mapping[str, float], resamples: int = RESAMPLES, seed: int = SEED
+) -> dict[str, object]:
+    """Every STEP_SESSIONS-th difference: its mean and stationary-bootstrap 95 % CI."""
+    values = list(diffs.values())[::STEP_SESSIONS]
+    if not values:
+        return {"sessions": 0, "mean": None, "low": None, "high": None}
+    rng = seeded(seed)
+    means = [
+        sum(values[i] for i in stationary_draws(len(values), BLOCK, rng)) / len(values)
+        for _ in range(resamples)
+    ]
+    low, high = percentile_interval(means)
+    return {
+        "sessions": len(values),
+        "mean": sum(values) / len(values),
+        "low": low,
+        "high": high,
+    }
+
+
+def walk_forward_reading(
+    folds: Sequence[Mapping[str, object]],
+    control: Sequence[Mapping[str, object]],
+    resamples: int = RESAMPLES,
+) -> dict[str, object]:
+    """Bars 1 and 2 on the folds, and the control: its interval must contain 0."""
+    diffs = differences(folds)
+    mean = sum(diffs.values()) / len(diffs) if diffs else float("nan")
+    boot = interval(diffs, resamples)
+    won = sum(
+        1
+        for record in folds
+        if _fold_mean(record, "ensemble") > _fold_mean(record, "baseline")
+    )
+    shuffled = interval(differences(control), resamples)
+    low, high = shuffled["low"], shuffled["high"]
+    control_ok = (
+        isinstance(low, float) and isinstance(high, float) and low <= 0.0 <= high
+    )
+    boot_low = boot["low"]
+    bar1 = mean >= BAR_IC_DIFFERENCE and isinstance(boot_low, float) and boot_low > 0.0
+    return {
+        "mean_ic_difference": mean,
+        "sessions": len(diffs),
+        "bootstrap": boot,
+        "folds_won": won,
+        "folds": len(folds),
+        "bar1": bool(bar1),
+        "bar2": won >= BAR_FOLDS_WON,
+        "control": shuffled | {"passed": bool(control_ok)},
+    }
+
+
+def verdict(walk: Mapping[str, object], holdout: Mapping[str, object] | None) -> str:
+    """STOPPED on a failed control; PASS only when all three bars hold; else FAIL."""
+    control = walk["control"]
+    assert isinstance(control, dict)
+    if not control["passed"]:
+        return "STOPPED"
+    if holdout is None:
+        return "PENDING HOLDOUT"
+    return "PASS" if walk["bar1"] and walk["bar2"] and holdout["bar3"] else "FAIL"
+
+
+def holdout_reading(record: Mapping[str, object]) -> dict[str, object]:
+    """Bar 3: the holdout's mean IC difference above 0, and the net top decile ahead."""
+    diffs = differences([record])
+    mean = sum(diffs.values()) / len(diffs) if diffs else float("nan")
+    top = record["top_decile"]
+    assert isinstance(top, dict)
+    ahead = top["ensemble"]["net_return"] > top["baseline"]["net_return"]
+    return {
+        "mean_ic_difference": mean,
+        "sessions": len(diffs),
+        "net_ahead": bool(ahead),
+        "bar3": bool(mean > 0.0 and ahead),
+    }
+
+
+def _fold_mean(record: Mapping[str, object], name: str) -> float:
+    ic = record["ic"]
+    assert isinstance(ic, dict)
+    values = list(ic[name].values())
+    return sum(values) / len(values) if values else float("-inf")
diff --git a/scripts/exp015_spec.py b/scripts/exp015_spec.py
new file mode 100644
index 00000000..3c638b00
--- /dev/null
+++ b/scripts/exp015_spec.py
@@ -0,0 +1,67 @@
+"""EXP-015's fixed constants: the features, folds, models, inference and bar (S289).
+
+Agent: tooling
+Role: hold every number EXP-015's Process fixes, and the gaps DL-313 filled.
+External I/O: none.
+"""
+
+from __future__ import annotations
+
+from datetime import date
+
+EXPERIMENT = "EXP-015"
+# The fifteen line features, then the five return features ranked within the sector.
+RETURN_FEATURES = ("ret_5", "ret_20", "ret_60", "ret_120", "ret_252_21")
+LINE_FEATURES = (
+    *RETURN_FEATURES,
+    "dist_252_high",
+    "vol_20",
+    "vol_60",
+    "atr_pct",
+    "beta_60",
+    "resvol_60",
+    "volratio_5_60",
+    "volratio_20_120",
+    "dollar_volume",
+    "rs_120",
+)
+SECTOR_FEATURES = tuple(f"sector_{name}" for name in RETURN_FEATURES)
+FEATURES = LINE_FEATURES + SECTOR_FEATURES
+FEATURE_LOOKBACK = 252  # sessions the longest feature reads (DL-313 D4)
+ATR_SESSIONS = 14  # DL-313 D3: the pre-registration names ATR % without a window
+DOLLAR_VOLUME_SESSIONS = 20  # DL-313 D3
+
+HORIZON = 10
+HORIZONS = (5, 10, 20)  # 10 is barred; 5 and 20 report decay
+MIN_SECONDARY_BARS = 253
+FOLD_YEARS = tuple(range(2018, 2025))
+HOLDOUT_START = date(2025, 1, 2)
+PURGE_SESSIONS = 10
+EMBARGO_SESSIONS = 5
+
+RIDGE_LAMBDA = 1.0
+LGBM_ROUNDS = 200
+LGBM_PARAMS = {
+    "objective": "regression",
+    "max_depth": 3,
+    "learning_rate": 0.05,
+    "num_leaves": 31,
+    "min_data_in_leaf": 500,
+    "feature_fraction": 0.8,
+    "seed": 0,
+    "deterministic": True,  # DL-313 D7: reproducible, not a tuning choice
+    "num_threads": 1,
+    "force_col_wise": True,
+    "verbosity": -1,
+}
+MODELS = ("composite", "ridge", "lightgbm")
+
+MIN_NAMES = 10  # DL-313 D6: a session ranks at least ten names, or it has no IC
+STEP_SESSIONS = 10  # every 10th session: non-overlapping for inference and rebalancing
+BLOCK = 20
+RESAMPLES = 10_000
+SEED = 0
+COST_BPS = 25
+DECILES = 10
+BAR_IC_DIFFERENCE = 0.01
+BAR_FOLDS_WON = 5
diff --git a/scripts/exp015_stages.py b/scripts/exp015_stages.py
new file mode 100644
index 00000000..272dc456
--- /dev/null
+++ b/scripts/exp015_stages.py
@@ -0,0 +1,172 @@
+"""EXP-015's stages: the panel, the walk-forward and its control, the holdout once.
+
+Agent: tooling
+Role: run each stage from the files the one before wrote, record the commit and the
+      inputs' digests beside the result, refuse a holdout the walk-forward did not earn.
+External I/O: reads the S235 cache; reads and writes the stages' files in an output
+      directory outside the worktree.
+"""
+
+from __future__ import annotations
+
+import hashlib
+import json
+from datetime import date
+from typing import TYPE_CHECKING
+
+from scripts.exp015_evaluate import score_fold
+from scripts.exp015_folds import holdout, walk_forward
+from scripts.exp015_models import Trainer, lightgbm_trainer
+from scripts.exp015_panel import build_panel
+from scripts.exp015_ranks import ranked_features
+from scripts.exp015_report import holdout_page, walk_forward_page
+from scripts.exp015_rule import holdout_reading, verdict, walk_forward_reading
+from scripts.exp015_spec import EXPERIMENT, FOLD_YEARS, HOLDOUT_START, SEED
+from scripts.exp015_store import (
+    Panel,
+    load_panel,
+    panel_digest,
+    save_panel,
+    shuffled,
+)
+from scripts.replay_arms_record import cache_checksums, read_repo_state
+from scripts.replay_cache import load_replay_cache
+from scripts.replay_series import bars_by_line
+from scripts.replay_settings import build_effective_settings
+from scripts.sp500_guards import load_known_moves
+
+if TYPE_CHECKING:
+    from collections.abc import Sequence
+    from pathlib import Path
+
+WALK_FORWARD = "walk_forward.json"
+HOLDOUT = "holdout.json"
+
+
+def panel_stage(cache: Path, out: Path) -> dict[str, object]:
+    """Build and save the panel over every cached session, and what built it."""
+    commit = _clean_commit()
+    context = load_replay_cache(cache)
+    errors: dict[str, tuple[date, ...]] = {}
+    for move in load_known_moves():
+        if move.kind == "adjustment-error":
+            errors[move.line] = (*errors.get(move.line, ()), move.date)
+    panel, counts = build_panel(
+        context,
+        build_effective_settings(()),
+        bars_by_line(context.universe.bars),
+        errors,
+        context.universe.sessions,
+    )
+    save_panel(out, panel)
+    record = {
+        "experiment": EXPERIMENT,
+        "commit": commit,
+        "cache": cache_checksums(cache),
+        "panel_sha256": panel_digest(panel),
+        "rows": len(panel.lines),
+        "primary_rows": int(panel.primary.sum()),
+        "secondary_rows": int(panel.secondary.sum()),
+        "first_session": str(panel.sessions[0]) if len(panel.lines) else None,
+        "last_session": str(panel.sessions[-1]) if len(panel.lines) else None,
+        "counts": counts,
+    }
+    _write(out / "panel.json", record)
+    return record
+
+
+def walk_forward_stage(
+    out: Path,
+    trainer: Trainer = lightgbm_trainer,
+    years: Sequence[int] = FOLD_YEARS,
+    resamples: int | None = None,
+) -> str:
+    """Score the folds (primary, shuffled control, secondary); the file's SHA-256."""
+    commit, panel = _clean_commit(), load_panel(out)
+    calendar = _calendar(panel)
+    folds = walk_forward(calendar, years)
+    primary = _scored(panel.take(panel.primary), folds, trainer)
+    control = _scored(shuffled(panel.take(panel.primary), SEED), folds, trainer)
+    secondary = _scored(panel.take(panel.secondary), folds, trainer)
+    reading = walk_forward_reading(primary, control, **_boot(resamples))
+    record = {
+        "experiment": EXPERIMENT,
+        "commit": commit,
+        "panel_sha256": panel_digest(panel),
+        "folds": primary,
+        "control": control,
+        "secondary": secondary,
+        "reading": reading,
+        "verdict": verdict(reading, None),
+    }
+    path = _write(out / WALK_FORWARD, record)
+    (out / "walk_forward.md").write_text(walk_forward_page(record), encoding="utf-8")
+    return hashlib.sha256(path.read_bytes()).hexdigest()
+
+
+def holdout_stage(
+    out: Path,
+    walk_forward_sha256: str,
+    trainer: Trainer = lightgbm_trainer,
+    start: date = HOLDOUT_START,
+) -> dict[str, object]:
+    """Touch the holdout once: after a recorded walk-forward whose control passed."""
+    if (out / HOLDOUT).exists():
+        raise ValueError("the holdout was touched already: holdout.json exists")
+    path = out / WALK_FORWARD
+    if (
+        not path.exists()
+        or hashlib.sha256(path.read_bytes()).hexdigest() != walk_forward_sha256
+    ):
+        raise ValueError("walk_forward.json is missing or is not the recorded one")
+    walk = json.loads(path.read_text(encoding="utf-8"))
+    if walk["verdict"] == "STOPPED":
+        raise ValueError("the shuffled-target control failed: the experiment stopped")
+    commit, panel = _clean_commit(), load_panel(out)
+    fold = holdout(_calendar(panel), start)
+    primary = _scored(panel.take(panel.primary), (fold,), trainer)[0]
+    secondary = _scored(panel.take(panel.secondary), (fold,), trainer)[0]
+    reading = holdout_reading(primary)
+    record = {
+        "experiment": EXPERIMENT,
+        "commit": commit,
+        "walk_forward_sha256": walk_forward_sha256,
+        "holdout": primary,
+        "secondary": secondary,
+        "reading": reading,
+        "verdict": verdict(walk["reading"], reading),
+    }
+    _write(out / HOLDOUT, record)
+    (out / "verdict.md").write_text(holdout_page(walk, record), encoding="utf-8")
+    return record
+
+
+def _scored(panel: Panel, folds: Sequence, trainer: Trainer) -> list[dict[str, object]]:
+    x = ranked_features(panel)
+    return [score_fold(panel, x, fold, trainer) for fold in folds]
+
+
+def _calendar(panel: Panel) -> tuple[date, ...]:
+    return tuple(
+        date.fromisoformat(day) for day in sorted(set(panel.sessions.tolist()))
+    )
+
+
+def _boot(resamples: int | None) -> dict[str, int]:
+    return {} if resamples is None else {"resamples": resamples}
+
+
+def _clean_commit() -> str:
+    state = read_repo_state()
+    if state.dirty:
+        raise ValueError(
+            "refusing to run EXP-015: the worktree has uncommitted changes"
+        )
+    return state.commit
+
+
+def _write(path: Path, record: dict[str, object]) -> Path:
+    path.write_text(
+        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
+    )
+    return path
diff --git a/scripts/exp015_store.py b/scripts/exp015_store.py
new file mode 100644
index 00000000..d21ffd8a
--- /dev/null
+++ b/scripts/exp015_store.py
@@ -0,0 +1,91 @@
+"""EXP-015's panel: one row per line and session, kept as arrays in one .npz (S289).
+
+Agent: tooling
+Role: hold the panel's rows (universe flags, baseline, raw line features, raw forward
+      returns, SPY's), save it outside the repo, read it back, and digest it.
+External I/O: reads and writes `panel.npz` in the output directory it is given.
+"""
+
+from __future__ import annotations
+
+import hashlib
+import itertools
+from dataclasses import dataclass
+from typing import TYPE_CHECKING
+
+import numpy as np
+
+if TYPE_CHECKING:
+    from pathlib import Path
+
+PANEL_FILE = "panel.npz"
+_FIELDS = (
+    "sessions", "lines", "sectors", "primary", "secondary", "baseline", "features",
+    "returns", "spy",
+)  # fmt: skip
+
+
+@dataclass(frozen=True)
+class Panel:
+    """Rows in session order, then line order; `features` and `returns` are 2-D."""
+
+    sessions: np.ndarray  # ISO dates, '<U10'
+    lines: np.ndarray
+    sectors: np.ndarray  # '' when the line has no sector
+    primary: np.ndarray  # passed the scanner's filters that session
+    secondary: np.ndarray  # held at least MIN_SECONDARY_BARS bars
+    baseline: np.ndarray  # the analyst's technical score
+    features: np.ndarray  # rows x LINE_FEATURES, raw
+    returns: np.ndarray  # rows x HORIZONS, raw forward returns
+    spy: np.ndarray  # rows x HORIZONS, SPY over the same sessions
+
+    @property
+    def excess(self) -> np.ndarray:
+        """The forward excess return over SPY, rows x HORIZONS."""
+        return self.returns - self.spy
+
+    def take(self, mask: np.ndarray) -> Panel:
+        """The rows where mask holds, in order."""
+        return Panel(*(getattr(self, name)[mask] for name in _FIELDS))
+
+
+def save_panel(out_dir: Path, panel: Panel) -> Path:
+    path = out_dir / PANEL_FILE
+    np.savez_compressed(path, **{name: getattr(panel, name) for name in _FIELDS})
+    return path
+
+
+def load_panel(out_dir: Path) -> Panel:
+    with np.load(out_dir / PANEL_FILE, allow_pickle=False) as data:
+        return Panel(*(data[name] for name in _FIELDS))
+
+
+def panel_digest(panel: Panel) -> str:
+    """SHA-256 of every array's dtype, shape and bytes in field order (no zip time)."""
+    digest = hashlib.sha256()
+    for name in _FIELDS:
+        array = np.ascontiguousarray(getattr(panel, name))
+        digest.update(f"{name}|{array.dtype.str}|{array.shape}|".encode())
+        digest.update(array.tobytes())
+    return digest.hexdigest()
+
+
+def shuffled(panel: Panel, seed: int) -> Panel:
+    """The panel with each session's forward returns permuted among its rows."""
+    rng = np.random.default_rng(seed)
+    order = np.arange(len(panel.lines))
+    _, starts = np.unique(panel.sessions, return_index=True)
+    bounds = [*sorted(starts.tolist()), len(order)]
+    for begin, end in itertools.pairwise(bounds):
+        order[begin:end] = begin + rng.permutation(end - begin)
+    return Panel(
+        panel.sessions,
+        panel.lines,
+        panel.sectors,
+        panel.primary,
+        panel.secondary,
+        panel.baseline,
+        panel.features,
+        panel.returns[order],
+        panel.spy[order],
+    )
diff --git a/scripts/exp015_targets.py b/scripts/exp015_targets.py
new file mode 100644
index 00000000..323505eb
--- /dev/null
+++ b/scripts/exp015_targets.py
@@ -0,0 +1,60 @@
+"""EXP-015's forward returns, session d+1's open to d+h's close, and masks (S289).
+
+Agent: tooling
+Role: give each line bar its raw forward return at each horizon, SPY's over the
+      same sessions, and the bars whose windows span a known adjustment error.
+External I/O: none.
+"""
+
+from __future__ import annotations
+
+from typing import TYPE_CHECKING
+
+import numpy as np
+from scripts.exp015_spec import FEATURE_LOOKBACK, HORIZONS
+
+if TYPE_CHECKING:
+    from collections.abc import Iterable, Sequence
+    from datetime import date
+
+
+def forward_returns(
+    dates: Sequence[date],
+    opens: np.ndarray,
+    closes: np.ndarray,
+    session_index: dict[date, int],
+    sessions: Sequence[date],
+) -> np.ndarray:
+    """(bars x horizons) raw returns; NaN unless the line has a bar on both sessions."""
+    position = {day: i for i, day in enumerate(dates)}
+    out = np.full((len(dates), len(HORIZONS)), np.nan)
+    for i, day in enumerate(dates):
+        j = session_index[day]
+        entry = position.get(sessions[j + 1]) if j + 1 < len(sessions) else None
+        for k, horizon in enumerate(HORIZONS):
+            if entry is None or j + horizon >= len(sessions):
+                continue
+            exit_ = position.get(sessions[j + horizon])
+            if exit_ is not None:
+                out[i, k] = closes[exit_] / opens[entry] - 1.0
+    return out
+
+
+def adjustment_masks(
+    dates: Sequence[date], moves: Iterable[date], session_index: dict[date, int]
+) -> tuple[np.ndarray, np.ndarray]:
+    """(features masked, targets masked) per bar, for the line's adjustment-error dates.
+
+    A bar's features read FEATURE_LOOKBACK sessions back; its targets read the next
+    max(HORIZONS) sessions: a move inside either window masks it (DL-313 D5).
+    """
+    features = np.zeros(len(dates), dtype=bool)
+    targets = np.zeros(len(dates), dtype=bool)
+    longest = max(HORIZONS)
+    for move in moves:
+        m = session_index[move]
+        for i, day in enumerate(dates):
+            j = session_index[day]
+            features[i] |= m <= j <= m + FEATURE_LOOKBACK
+            targets[i] |= j < m <= j + longest
+    return features, targets
```
