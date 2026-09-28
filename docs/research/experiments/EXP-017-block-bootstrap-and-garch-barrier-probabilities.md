# EXP-017 — Do block-bootstrap or GARCH paths forecast stop-first / target-first better than today's bootstrap, on the history the fleet actually has?

**Status:** COMPLETE 2026-09-28 · **GARCH is the only model with real skill, but its formal verdict is
INSUFFICIENT and no model yet clears the bar for the live ledger.** GARCH beats the plain bootstrap (H1b:
−0.0082 [−0.0124, −0.0041]) and, on the fleet's 203 bars, beats climatology (−0.0094 [−0.0141, −0.0046]), with
skill **+2.26 %** on full history and **+1.47 %** on 203 bars. But **6.2 %** of its fits fell back, above the
pre-registered 2 % limit. Almost all of those are estimates on the persistence boundary (α + β = 1), which the
pre-registered acceptance rule rejected, not optimiser failures. The block bootstrap is worse than the plain
one (H1a fails). The plain bootstrap has **no** skill on 203 bars (−0.49 %). Cost $0. Pre-registered at
`b314ce53`.
**Decision / origin:** [DL-240](../../design-log.md) · operator, 2026-09-28: *"EXP-017"* · work-queue **92** ·
follows [EXP-016](EXP-016-jev-barrier-probabilities.md) · **Cost:** $0 (local simulation).

## 1. Why we needed this experiment

DL-240 builds a ledger of declared against realised probabilities, then lets the PM size positions on them.
EXP-016 ruled out Jev and pointed at simulation models. The best simulation so far (EXP-011's plain
bootstrap) beat climatology by only ~1 %, with an interval nearly touching zero, and it drew on up to ten
years of each stock's history, while the live fleet sees about **203 bars** per stock. Two questions decided
whether the live ledger is worth building, and how: do models that keep **volatility clustering** (calm and
stormy stretches, not independent days) forecast better, and does anything still work on the history the
fleet actually has?

## 2. Hypothesis

- **H1a:** a stationary block bootstrap (`B5`, full history) has a lower 3-outcome Brier than the plain
  bootstrap (`B1`, full history); 95 % interval below zero.
- **H1b:** GARCH(1,1) (`G`, full history) has a lower Brier than `B1`; interval below zero.
- **H2 (production):** at least one model on the **203-bar** history beats climatology; interval below zero.
- **Materiality bar for building the live ledger:** Brier skill against climatology of at least **2 %**
  (double today's best), interval above zero, **on the history depth production would give it**.
- **Fit reliability:** more than 2 % failed GARCH fits makes `G` INSUFFICIENT.
- **H0:** nothing passes; exits would then be chosen by replaying simple rules, without a probability model.

## 3. Data

- **Daily bars:** the replay cache built by `scripts/replay_dataset.py` (OneDrive `trading-agents-data/`, never
  the repo: the data is licensed and the repo is public). `bars.csv.gz` (sha-256 prefix `12374e3e5493`):
  **263,005** Alpaca daily bars, **SIP** (consolidated tape), split- and dividend-adjusted, for **98** names
  (the live universe on 2026-09-16), 2016-01-04 → 2026-09-16 (LIN from 2018-10).
- **VIX:** `vix.csv.gz` (prefix `e5d4fe621031`), Cboe's public daily history, 9,277 sessions, 1990-01-02 →
  2026-09-21, labelled with the provider's live regime thresholds.
- **Decisions:** EXP-011's test bed, rebuilt from those files: a decision at the close of every 5th session
  from 2017-01-03, per name: **47,485** cases (486 dates × 98 names). Stop = clamp(2 × ATR14 ÷ close, 2.5 %,
  8 %); target = median best 10-session close-to-high rise over the 120 prior settled windows. Outcome over
  the next 10 sessions, the low checked before the high: stop first, target first, or neither. Reproduced
  exactly (realised 0.285 / 0.480 / 0.235) before each run.
- **Known defect:** DOW has flat placeholder bars for 2018 (it listed in 2019): a handful of degenerate
  cases (0 % target), kept and scored alike by every model.
- **Scored:** every case dated 2018–2026 (2017 feeds climatology only): **42,538** cases; 82 have no GARCH
  estimate (their stock's first fit failed with no earlier one to fall back on), so all seven models are
  scored on the same **42,456** cases over **435** dates.
- Derived file `exp017_sim.pkl` (every model's probabilities per case) in OneDrive `trading-agents-data/exp017/`.

## 4. Tools and setup

- **Machine:** Intel Core i7-7660U (2 cores / 4 threads, 2.5 GHz), 15.9 GB RAM, Windows 10 Pro 19045.
- **Python** 3.13.2 run through **uv** 0.8.14; **numpy** 2.4.6.
- **arch** 8.0.0 (GARCH estimation), **scipy** 1.17.1 (the variance recursion via `lfilter`), **statsmodels**
  0.15.0 (pulled in by arch). Loaded for the run only with `uv run --with arch --with scipy`; **not** added to
  the repo's dependencies.
- **Parallelism:** one process per stock, 4 workers; **508 s** wall time for all 47,485 cases.
- **Seeds:** paths derived per stock from the pre-registered `20260917` as `default_rng([20260917,
  stock_index])` (needed once the work was split across processes); interval resampling `20260928`, 1,000
  resamples.
- **Checks before the run:** a one-stock smoke test (AAPL 2018: sensible probabilities, 24 of 24 fits
  converged); the vectorised variance recursion equal to the plain loop to **0.0** difference.
- **Repo:** pre-registered at `b314ce53`; run the same day. **Cost:** $0.

## 5. How it was conducted

1. Pre-registered the models, depths, scoring and bars, and committed before simulating.
2. Rebuilt EXP-011's decisions and checked the reproduction.
3. For every scored case, simulated **1,000 ten-session paths** under each model at each depth, and counted
   the share ending stop-first, target-first or neither:
   - **`B1` plain bootstrap:** each simulated day an independent draw of a past day's (high, low, close)
     relative to the prior close;
   - **`B5` stationary block bootstrap:** runs of consecutive past days, mean length 5;
   - **`G` GARCH(1,1), Student-t, filtered historical simulation:** fitted per stock and calendar month on
     the history available at the month's first decision; each simulated day's volatility follows the GARCH
     recursion, and the day's shape (close, high, low) is a past day resampled and rescaled to that
     volatility. A failed fit (non-convergence, or α + β not below 1) reused the previous month's parameters.
4. Each model ran on **full** history (up to ~10 years) and on the **last 203** days.
5. Scored all seven (six models + climatology) on the same cases: Brier and skill with date-resampled
   intervals, the pre-registered differences, calibration buckets, Brier by year and by VIX regime.
6. After scoring, a **descriptive** check of 400 random refits to learn why fits failed (Appendix R).

## 6. Results

| Model | History | Brier | Skill vs climatology | 95 % interval |
| --- | --- | --- | --- | --- |
| GARCH (`G`) | full | **0.6218** | **+2.26 %** | [+1.50, +3.02] |
| GARCH (`G`) | 203 bars | 0.6268 | +1.47 % | [+0.72, +2.20] |
| Plain bootstrap (`B1`) | full | 0.6300 | +0.97 % | [+0.08, +1.74] |
| Block bootstrap (`B5`) | 203 bars | 0.6343 | +0.29 % | [−0.46, +1.08] |
| Climatology | — | 0.6361 | 0 | — |
| Block bootstrap (`B5`) | full | 0.6361 | −0.00 % | [−0.95, +0.83] |
| Plain bootstrap (`B1`) | 203 bars | 0.6392 | **−0.49 %** | [−1.38, +0.48] |

- **H1a fails:** block − plain = +0.0062 [+0.0035, +0.0088]; the block bootstrap is *worse*.
- **H1b passes numerically:** GARCH − plain = **−0.0082** [−0.0124, −0.0041].
- **H2 passes numerically for GARCH only:** GARCH (203 bars) − climatology = **−0.0094** [−0.0141, −0.0046];
  both bootstraps fail on 203 bars.
- **Fit reliability fails:** 19,060 fits accepted, **1,260** fell back and 20 had nothing to fall back on:
  **6.2 %**, above the 2 % limit, so GARCH is formally **INSUFFICIENT**. The descriptive check of 400 random
  refits: **379** fine, **20** with α + β = **1.0** (the persistence boundary), 1 non-converged. The failures
  are boundary estimates, which the acceptance rule rejected by requiring α + β strictly below 1.
- **Materiality:** GARCH reaches 2 % skill only on full history (+2.26 %, lower bound +1.50 %). On the fleet's
  203 bars it reaches +1.47 %. No model clears the bar on the history production has today.
- **GARCH's edge is largest in stress:** VIX `extreme` Brier 0.479 against climatology's 0.523; `high_vol`
  0.586 against 0.607. In calm markets (`risk_on`) the block bootstrap is best (0.636).
- **Calibration:** GARCH's target-first probabilities sit near the diagonal from 0.26 to 0.64 (said 0.54 →
  got 0.56); every model over-states its lowest stop-first bucket (said 0.06–0.07 → got 0.15–0.21).

## 7. Conclusions

- **Volatility clustering matters, and GARCH captures it; resampling blocks of days does not.** GARCH is the
  only model with skill that survives on the fleet's 203 bars.
- **The plain bootstrap, today's best, works only with long history.** On 203 bars it has no skill, so a
  production model must be GARCH-like, or the fleet must see more history.
- **Not yet enough to build the live ledger on:** the formal GARCH verdict is INSUFFICIENT (a too-strict
  acceptance rule, set before the run and kept), and no model clears 2 % skill on production's depth.
- **The gap is narrow and specific:** accept boundary fits properly, and give the model more history than
  203 bars. S238 made that possible: SIP requests with a clamped end now work, so the provider can fetch
  longer histories.

## 8. Recommended code changes, and how to implement them

1. **No change to the fleet's code yet.** Nothing has cleared the bar on a history the fleet can supply.
2. **Run EXP-018 next** (pre-registered, $0, planner): GARCH with boundary fits accepted (α + β ≤ 1, with
   persistence capped at 0.999 inside the recursion so variance stays finite), at three depths: **203 bars**
   (today), **756 bars** (~3 years, fetchable per run over SIP since S238) and full history. Same scoring,
   same 2 % bar, same 2 % fit-failure limit. Also measure the size and time of a 99-stock × 756-bar SIP
   request, so the production cost is known before any build.
3. **If EXP-018 clears the bar at a depth production can supply**, build in three increments, each a sprint
   for a cloud session with its law cycle:
   - **Provider:** serve the forecaster the longer history (a history-depth setting, or a second bars
     request), with a `PARAM` row and a measured request budget.
   - **Forecaster:** a shadow model `barrier_garch` that states P(stop first), P(target first) and P(neither)
     for each approved buy with the PM's own stop and target, stored as a ledger record. `arch` joins the
     forecaster's optional dependencies (like `lightgbm`); check the image size. A new graph record means a
     vocabulary change, so the deploy is a full `up`.
   - **Settlement and scorecard:** after 10 sessions the realised outcome is recorded against each claim;
     Brier, skill and calibration per model on the dashboard; promotion only through the ADR-0010 registry,
     advisory until its scorecard earns it. Sizing on it stays the operator's capital-risk decision, after
     item 91.
4. **Never put the plain bootstrap on 203 bars into production** (−0.49 % skill).
5. **The shared test bed as a repo script** (EXP-016 section 8, item 2), before EXP-018, so EXP-018 imports it
   instead of copying appendix code.

## Appendix P — Pre-registration (frozen)

Verbatim as committed at `b314ce53`, before any path was simulated.

### Purpose

**Question.** For the fleet's own stop and target, do simulated 10-session paths that keep volatility
clustering, from a **stationary block bootstrap** or a **GARCH(1,1)** model, give better stop-first /
target-first / neither probabilities than the plain per-day bootstrap (`all_history`, EXP-011's best)? And
does any of them still beat climatology when it only sees the **~203 bars** the live fleet has per name?

**Why it matters.** DL-240 builds a ledger of declared against realised probabilities, then lets the PM size
on them. So far the best model beats climatology by only 0.006–0.010 Brier (about 1 % skill), with an
interval that nearly touches zero. A ledger for a model that barely beats averages gives the PM nothing to
size on. This decides whether the live ledger is worth building, and on which model and history depth.

**Hypotheses** (each names its arm and baseline; none is re-labelled afterwards):

- **H1a:** the block bootstrap (`B5`, full history) has a lower 3-outcome Brier than the plain bootstrap
  (`B1`, full history), 95 % interval of the difference below zero.
- **H1b:** GARCH (`G`, full history) has a lower Brier than `B1`, 95 % interval below zero.
- **H2 (production):** at least one model on the **203-bar** history beats climatology, 95 % interval below
  zero.
- **Materiality bar for building the live ledger on a model:** Brier skill against climatology
  (1 − Brier ÷ Brier_climatology) of at least **2 %**, with its 95 % interval above zero, on the history depth
  production would give it. 2 % is double today's best; it is a judgement, set now.
- **H0.** No model meets its hypothesis. Then daily-path models cannot do much better than averages here,
  and exits are chosen by replaying simple rules instead (DL-240 step 5 without a probability model).

Two primary tests (H1a, H1b) are run at 95 % each; that is stated, not corrected, and read with it in mind.

### Process

Everything below is fixed now.

**Test bed.** EXP-011's decisions rebuilt from the replay cache exactly as in EXP-016 (reproduction check:
**47,485** cases, realised 0.285 / 0.480 / 0.235, else the run stops). Barriers: stop = clamp(2 × ATR14 ÷
close, 2.5 %, 8 %); target = median best 10-session close-to-high rise over the 120 prior settled windows.
Outcome over the next 10 sessions, low before high. **Scored:** every case dated 2018–2026 (2017 feeds
climatology only). Every decision has at least 251 prior bars, so both history depths exist for every case.

**Daily moves.** For a name, each session *j* is the triple (high, low, close) relative to the prior close.
Everything a model uses is dated at or before the decision.

**Models** (1,000 paths × 10 sessions per case; a path's barrier rule is the test bed's):

- **`B1` — plain bootstrap** (EXP-011's `all_history`): each simulated day is an independent draw of a past
  session's triple.
- **`B5` — stationary block bootstrap** (Politis–Romano, mean block length **5**): a path starts at a random
  past session and continues through consecutive sessions, jumping to a new random start with probability
  1/5 each day (and whenever it would run past the decision).
- **`G` — GARCH(1,1) with Student-t innovations, filtered historical simulation.** Fitted with `arch`
  (constant mean, returns in %) per name and calendar month on the history available at the month's first
  decision date; decisions later that month reuse those parameters, with the variance recursion run on data
  up to the decision. Standardised residuals z = (r − μ) ÷ σ, and each day's high and low as
  log-distances from the prior close ÷ σ, are resampled together from the fitted history; each simulated
  day's σ follows the GARCH recursion from the decision-day forecast, and its close, high and low are the
  resampled day's scaled by that σ (high and low never cross the close).
- **`climatology`** (baseline): outcome shares of all cases in earlier years.

**History depths.** `full`: everything at or before the decision (up to ~10 years). `short`: the last **203**
sessions only (the live fleet's window). Each of `B1`, `B5`, `G` runs at both depths: six models plus
climatology.

**Scoring** (2018–2026):

- 3-outcome Brier and Brier skill against climatology for all seven;
- H1a (`B5_full` − `B1_full`), H1b (`G_full` − `B1_full`), H2 (each `*_short` − climatology) and the skill
  intervals, from **1,000** resamples of whole decision dates (seed `20260928`);
- calibration of P(stop first) and P(target first) in 0.1 buckets with at least 100 cases;
- Brier by year, and by regime at decision;
- fit failures (a failed fit falls back to the previous month's parameters for that name; the count is
  reported, and more than 2 % failed fits makes `G` INSUFFICIENT).

**Seeds.** Paths: `20260917` (as EXP-011). Date resampling: `20260928`.

## Appendix R — Run record

**Simulation log (last lines):** 98 of 98 stocks, 508 s; `cases 47485; realised [0.285 0.48 0.235]; garch fits
{'ok': 19060, 'fallback': 1260, 'failed_first': 20}`.

**Scored output** (`exp017_score.py`):

```text
cases 47485 (scored 2018-2026: 42538); realised all [0.285 0.48  0.235], scored [0.292 0.477 0.231]
GARCH fits {'ok': 19060, 'fallback': 1260, 'failed_first': 20}; failed-and-fell-back 6.19 %; cases with no G at all 82
G: INSUFFICIENT (more than 2 % failed fits)

scored 42456 cases on 435 dates

Brier (3-outcome) and skill vs climatology (1 - B/B_clim), 95 % interval resampling whole dates:
   B1_full      Brier 0.6300   skill +0.97 %  [+0.08, +1.74]   mean declared [0.284 0.471 0.246]
   B5_full      Brier 0.6361   skill -0.00 %  [-0.95, +0.83]   mean declared [0.257 0.441 0.302]
   G_full       Brier 0.6218   skill +2.26 %  [+1.50, +3.02]   mean declared [0.266 0.458 0.276]
   B1_short     Brier 0.6392   skill -0.49 %  [-1.38, +0.48]   mean declared [0.307 0.499 0.195]
   B5_short     Brier 0.6343   skill +0.29 %  [-0.46, +1.08]   mean declared [0.294 0.482 0.223]
   G_short      Brier 0.6268   skill +1.47 %  [+0.72, +2.20]   mean declared [0.285 0.484 0.231]
   climatology  Brier 0.6361   skill +0.00 %  [+0.00, +0.00]   mean declared [0.27  0.484 0.246]

Pre-registered differences (negative = better):
   H1a B5_full - B1_full        +0.0062  [+0.0035, +0.0088]  fail
   H1b G_full - B1_full         -0.0082  [-0.0124, -0.0041]  PASS
   H2  B1_short - climatology   +0.0031  [-0.0031, +0.0088]  fail
   H2  B5_short - climatology   -0.0018  [-0.0069, +0.0029]  fail
   H2  G_short - climatology    -0.0094  [-0.0141, -0.0046]  PASS
   --  B1_full - climatology    -0.0061  [-0.0110, -0.0005]
   --  B5_short - B1_short      -0.0050  [-0.0073, -0.0027]
   --  G_short - B1_short       -0.0125  [-0.0163, -0.0088]
   --  G_full - B5_full         -0.0144  [-0.0187, -0.0102]

Calibration - declared bucket -> realised share (buckets with >= 100 cases):
   B1_full   P(stop first)    0.07->0.20 (1547)  0.16->0.23 (7406)  0.25->0.27 (14050)  0.35->0.32 (14286)  0.43->0.39 (4925)  0.52->0.41 (239)
   B1_full   P(target first)  0.17->0.27 (350)  0.26->0.29 (1993)  0.36->0.37 (7888)  0.45->0.45 (14984)  0.54->0.54 (13051)  0.63->0.65 (3724)  0.72->0.72 (287)
   B5_full   P(stop first)    0.07->0.20 (1935)  0.16->0.23 (10014)  0.25->0.29 (16156)  0.34->0.34 (12029)  0.43->0.41 (2264)
   B5_full   P(target first)  0.16->0.29 (751)  0.26->0.32 (3610)  0.36->0.40 (10044)  0.45->0.48 (15170)  0.54->0.56 (10178)  0.63->0.66 (2401)  0.72->0.72 (145)
   G_full    P(stop first)    0.06->0.15 (302)  0.17->0.23 (6011)  0.25->0.29 (23676)  0.34->0.33 (11405)  0.43->0.37 (991)
   G_full    P(target first)  0.16->0.24 (749)  0.26->0.30 (3686)  0.36->0.38 (9064)  0.45->0.46 (13106)  0.54->0.56 (10483)  0.64->0.67 (4244)  0.73->0.69 (903)
   B1_short  P(stop first)    0.07->0.20 (905)  0.16->0.27 (5937)  0.25->0.27 (12894)  0.35->0.29 (14730)  0.44->0.34 (6938)  0.53->0.42 (1037)
   B1_short  P(target first)  0.28->0.23 (120)  0.37->0.33 (4097)  0.46->0.43 (17068)  0.54->0.52 (17485)  0.63->0.62 (3458)
   B5_short  P(stop first)    0.07->0.21 (974)  0.16->0.26 (6585)  0.25->0.27 (14059)  0.35->0.30 (14791)  0.44->0.36 (5550)  0.52->0.48 (494)
   B5_short  P(target first)  0.28->0.27 (156)  0.37->0.35 (5047)  0.46->0.45 (19940)  0.54->0.53 (15588)  0.62->0.64 (1575)
   G_short   P(stop first)    0.07->0.16 (712)  0.16->0.26 (6412)  0.25->0.28 (16979)  0.34->0.30 (14207)  0.43->0.37 (3876)  0.53->0.45 (265)
   G_short   P(target first)  0.16->0.27 (175)  0.27->0.28 (933)  0.36->0.36 (6173)  0.45->0.45 (16662)  0.54->0.53 (14559)  0.63->0.63 (3479)  0.73->0.64 (316)

Brier by year:
   year      n    B1_full    B5_full     G_full   B1_short   B5_short    G_short  climatology
   2018   4768     0.6386     0.6496     0.6308     0.6382     0.6404     0.6384     0.6424
   2019   4858     0.6203     0.6186     0.6130     0.6341     0.6271     0.6222     0.6367
   2020   4998     0.6374     0.6649     0.6092     0.6685     0.6421     0.6119     0.6286
   2021   4900     0.6429     0.6366     0.6278     0.6660     0.6557     0.6482     0.6536
   2022   4900     0.6258     0.6513     0.6200     0.6281     0.6304     0.6220     0.6275
   2023   4900     0.6328     0.6253     0.6356     0.6538     0.6511     0.6449     0.6502
   2024   4998     0.6253     0.6184     0.6286     0.6215     0.6216     0.6234     0.6384
   2025   4900     0.6268     0.6286     0.6192     0.6286     0.6253     0.6195     0.6287
   2026   3234     0.6147     0.6294     0.6068     0.6012     0.6053     0.6029     0.6102

Brier by regime at decision:
     risk_on n=10101  B1_full=0.6428  B5_full=0.6356  G_full=0.6400  B1_short=0.6524  B5_short=0.6474  G_short=0.6464  climatology=0.6567
     neutral n=16997  B1_full=0.6408  B5_full=0.6400  G_full=0.6371  B1_short=0.6486  B5_short=0.6449  G_short=0.6421  climatology=0.6480
    risk_off n= 8210  B1_full=0.6134  B5_full=0.6246  G_full=0.6154  B1_short=0.6426  B5_short=0.6327  G_short=0.6218  climatology=0.6245
    high_vol n= 5874  B1_full=0.6000  B5_full=0.6319  G_full=0.5860  B1_short=0.6069  B5_short=0.5958  G_short=0.5854  climatology=0.6068
     extreme n= 1274  B1_full=0.6297  B5_full=0.6809  G_full=0.4786  B1_short=0.5373  B5_short=0.5752  G_short=0.4884  climatology=0.5229
```

**Descriptive fit diagnosis (after scoring):** 400 random refits, half on 203 bars and half on full history.
`ok` 379, `alpha+beta>=1` 20 (every one exactly 1.0, on both depths), non-converged 1 (scipy SLSQP code 4,
"Inequality constraints incompatible"), `omega<=0` 0, exceptions 0.

### Reproducing

From the repo root: `PYTHONPATH=. uv run --with arch --with scipy python exp017_sim.py <dir> 4` (writes
`exp017_sim.pkl`, ~9 minutes on 4 workers), then `uv run python exp017_score.py <dir>`. Seeds are fixed.

## Appendix S — Scripts

### `exp017_sim.py`

```python
"""EXP-017 step 1 - simulate barrier probabilities: B1, B5 (stationary block), G (GARCH-t FHS) x full/short.

PYTHONPATH=<repo> uv run --with arch python exp017_sim.py <out_dir> [workers]
Decision at the close of bar t; every model uses moves dated <= t. One process per name; per-name seeds are
derived from the pre-registered 20260917 as default_rng([20260917, name_index]).
"""
import pickle
import sys
import time
import warnings
from multiprocessing import Pool
from pathlib import Path

import numpy as np

H, LOOKBACK, ATR_N, N_PATHS, STEP, RECENT, SHORT, MEAN_BLOCK = 10, 120, 14, 1000, 5, 250, 203, 5
OUT = Path(sys.argv[1])
MODELS = ("B1_full", "B5_full", "G_full", "B1_short", "B5_short", "G_short")


def label(v):
    return 4 if v >= 35 else 3 if v >= 25 else 2 if v >= 20 else 0 if v <= 15 else 1


def barrier_probs(prev, lh, ll, stop, target):
    """prev: path level before each day; lh/ll: that day's high/low relative to the prior close."""
    hit_s = prev * ll <= 1 - stop
    hit_t = prev * lh >= 1 + target
    fs = np.where(hit_s.any(1), hit_s.argmax(1), H)
    ft = np.where(hit_t.any(1), hit_t.argmax(1), H)
    p_stop = float(np.mean((fs < H) & (fs <= ft)))
    p_target = float(np.mean((ft < H) & (ft < fs)))
    return (p_stop, p_target, 1 - p_stop - p_target)


def from_index(rh, rl, rc, idx, stop, target):
    cc = np.cumprod(rc[idx], axis=1)
    prev = np.concatenate([np.ones((idx.shape[0], 1)), cc[:, :-1]], axis=1)
    return barrier_probs(prev, rh[idx], rl[idx], stop, target)


def stationary_index(rng, lo, hi):
    """Politis-Romano: continue the block with prob 1 - 1/MEAN_BLOCK, else jump; never run past hi."""
    idx = np.empty((N_PATHS, H), dtype=int)
    cur = rng.integers(lo, hi, N_PATHS)
    for k in range(H):
        idx[:, k] = cur
        nxt = cur + 1
        jump = (rng.random(N_PATHS) < 1 / MEAN_BLOCK) | (nxt >= hi)
        nxt[jump] = rng.integers(lo, hi, jump.sum())
        cur = nxt
    return idx


def garch_fit(r):
    from arch import arch_model

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = arch_model(r, mean="Constant", vol="GARCH", p=1, q=1, dist="t").fit(disp="off")
    p = res.params
    ok = res.convergence_flag == 0 and p["alpha[1]"] + p["beta[1]"] < 1 and p["omega"] > 0
    return (float(p["mu"]), float(p["omega"]), float(p["alpha[1]"]), float(p["beta[1]"])), ok


def garch_path_probs(rng, params, r, lh_pct, ll_pct, lo, t, stop, target):
    """Filtered historical simulation over moves lo..t-1 (r in % log returns, index k = move into bar k+1)."""
    mu, omega, alpha, beta = params
    seg = r[lo:t]
    from scipy.signal import lfilter

    s2_0 = seg.var()
    # s2[k+1] = omega + alpha * (seg[k] - mu)^2 + beta * s2[k], computed in C
    s2 = np.concatenate([[s2_0], lfilter([1.0], [1.0, -beta], omega + alpha * (seg - mu) ** 2, zi=[beta * s2_0])[0]])
    sig = np.sqrt(s2[:-1])
    z = (seg - mu) / sig
    uh, ul = lh_pct[lo:t] / sig, ll_pct[lo:t] / sig
    s2_next = np.full(N_PATHS, s2[-1])
    level = np.ones(N_PATHS)
    prev_all = np.empty((N_PATHS, H))
    hh = np.empty((N_PATHS, H))
    llw = np.empty((N_PATHS, H))
    for k in range(H):
        j = rng.integers(0, len(seg), N_PATHS)
        s = np.sqrt(s2_next)
        rr = mu + s * z[j]
        hi_pct = np.maximum(s * uh[j], rr)
        lo_pct = np.minimum(s * ul[j], rr)
        prev_all[:, k] = level
        hh[:, k] = np.exp(hi_pct / 100)
        llw[:, k] = np.exp(lo_pct / 100)
        level = level * np.exp(rr / 100)
        s2_next = omega + alpha * (rr - mu) ** 2 + beta * s2_next
    return barrier_probs(prev_all, hh, llw, stop, target)


def run_name(job):
    name_index, sym, rows, decision_dates, vixlab = job
    rng = np.random.default_rng([20260917, name_index])
    dates = [x[0] for x in rows]
    hi, lo, cl = (np.array([x[k] for x in rows]) for k in (2, 3, 4))
    rh, rl, rc = hi[1:] / cl[:-1], lo[1:] / cl[:-1], cl[1:] / cl[:-1]
    r = 100 * np.log(rc)
    lh_pct, ll_pct = 100 * np.log(rh), 100 * np.log(rl)
    tr = np.maximum.reduce([hi[1:] - lo[1:], abs(hi[1:] - cl[:-1]), abs(lo[1:] - cl[:-1])])
    out, fits = [], {"full": {}, "short": {}}
    fit_counts = {"ok": 0, "fallback": 0, "failed_first": 0}
    last_params = {"full": None, "short": None}
    for t, day in enumerate(dates):
        if day not in decision_dates or t < RECENT + 1 or t + H >= len(rows) or day not in vixlab:
            continue
        atr_pct = tr[t - ATR_N:t].mean() / cl[t]
        stop = min(max(2 * atr_pct, 0.025), 0.08)
        anchors = range(t - H - LOOKBACK + 1, t - H + 1)
        exc = [max(hi[a + 1:a + 1 + H].max() / cl[a] - 1, 0.0) for a in anchors]
        target = min(float(np.median(exc)), 1.0)
        lvl_s, lvl_t = cl[t] * (1 - stop), cl[t] * (1 + target)
        outcome = 2
        for k in range(t + 1, t + H + 1):
            if lo[k] <= lvl_s:
                outcome = 0
                break
            if hi[k] >= lvl_t:
                outcome = 1
                break
        rec = {"sym": sym, "day": day, "outcome": outcome, "regime": vixlab[day]}
        if day >= "2018":
            month = day[:7]
            for depth, lo_i in (("full", 0), ("short", t - SHORT)):
                rec[f"B1_{depth}"] = from_index(rh, rl, rc, rng.integers(lo_i, t, (N_PATHS, H)), stop, target)
                rec[f"B5_{depth}"] = from_index(rh, rl, rc, stationary_index(rng, lo_i, t), stop, target)
                if month not in fits[depth]:
                    try:
                        params, ok = garch_fit(r[lo_i:t])
                    except Exception:  # noqa: BLE001 - counted as a failed fit
                        params, ok = None, False
                    if ok:
                        fit_counts["ok"] += 1
                        last_params[depth] = params
                    elif last_params[depth] is not None:
                        fit_counts["fallback"] += 1
                    else:
                        fit_counts["failed_first"] += 1
                    fits[depth][month] = last_params[depth]
                params = fits[depth][month]
                rec[f"G_{depth}"] = (
                    garch_path_probs(rng, params, r, lh_pct, ll_pct, lo_i, t, stop, target) if params else None
                )
        out.append(rec)
    return sym, out, fit_counts


def main():
    from scripts.replay_dataset import load

    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    vix, bars = load()
    vixlab = {k: label(v) for k, v in vix.items()}
    calendar = sorted({b[0] for rows in bars.values() for b in rows})
    decision_dates = set(calendar[calendar.index("2017-01-03")::STEP])
    jobs = [(i, sym, rows, decision_dates, vixlab) for i, (sym, rows) in enumerate(sorted(bars.items()))]
    t0 = time.time()
    cases, counts = [], {"ok": 0, "fallback": 0, "failed_first": 0}
    with Pool(workers) as pool:
        for n, (sym, out, fc) in enumerate(pool.imap_unordered(run_name, jobs), 1):
            cases.extend(out)
            for k in counts:
                counts[k] += fc[k]
            print(f"  {n}/{len(jobs)} {sym} {len(out)} cases, {time.time() - t0:.0f}s", flush=True)
    cases.sort(key=lambda c: (c["sym"], c["day"]))
    Y = np.eye(3)[[c["outcome"] for c in cases]]
    print(f"cases {len(cases)}; realised {Y.mean(0).round(3)}; garch fits {counts}")
    pickle.dump({"cases": cases, "fit_counts": counts}, open(OUT / "exp017_sim.pkl", "wb"))
    print("wrote", OUT / "exp017_sim.pkl", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
```

### `exp017_score.py`

```python
"""EXP-017 step 2 - score exactly as pre-registered.

uv run python exp017_score.py <out_dir>
"""
import pickle
import sys
from pathlib import Path

import numpy as np

OUT = Path(sys.argv[1])
d = pickle.load(open(OUT / "exp017_sim.pkl", "rb"))
cases = d["cases"]
MODELS = ("B1_full", "B5_full", "G_full", "B1_short", "B5_short", "G_short")
Y_all = np.eye(3)[[c["outcome"] for c in cases]]
years_all = np.array([int(c["day"][:4]) for c in cases])
clim_all = np.zeros_like(Y_all)
for i, y in enumerate(years_all):
    prior = years_all < y
    clim_all[i] = Y_all[prior].mean(0) if prior.sum() > 500 else Y_all[:500].mean(0)

ev = years_all >= 2018
g_missing = sum(1 for c, e in zip(cases, ev) if e and (c.get("G_full") is None or c.get("G_short") is None))
fc = d["fit_counts"]
fits = sum(fc.values())
print(f"cases {len(cases)} (scored 2018-2026: {ev.sum()}); realised all {Y_all.mean(0).round(3)}, scored {Y_all[ev].mean(0).round(3)}")
print(f"GARCH fits {fc}; failed-and-fell-back {100 * fc['fallback'] / fits:.2f} %; cases with no G at all {g_missing}")
if (fc["fallback"] + fc["failed_first"]) > 0.02 * fits:
    print("G: INSUFFICIENT (more than 2 % failed fits)")
keep = np.where(ev)[0]
keep = np.array([i for i in keep if cases[i].get("G_full") is not None and cases[i].get("G_short") is not None])
Y = Y_all[keep]
F = {m: np.array([cases[i][m] for i in keep]) for m in MODELS}
F["climatology"] = clim_all[keep]
dates = np.array([cases[i]["day"] for i in keep])
years = years_all[keep]
regs = np.array([cases[i]["regime"] for i in keep])
loss = {m: ((P - Y) ** 2).sum(1) for m, P in F.items()}
bc = loss["climatology"].mean()

rng = np.random.default_rng(20260928)
udates = np.unique(dates)
by_date = {u: np.where(dates == u)[0] for u in udates}
draws = [np.concatenate([by_date[u] for u in rng.choice(udates, len(udates))]) for _ in range(1000)]

print(f"\nscored {len(keep)} cases on {len(udates)} dates")
print("\nBrier (3-outcome) and skill vs climatology (1 - B/B_clim), 95 % interval resampling whole dates:")
for m in (*MODELS, "climatology"):
    b = loss[m].mean()
    sk = [1 - loss[m][s].mean() / loss["climatology"][s].mean() for s in draws]
    print(f"   {m:<12} Brier {b:.4f}   skill {100 * (1 - b / bc):+.2f} %  [{100 * np.percentile(sk, 2.5):+.2f}, {100 * np.percentile(sk, 97.5):+.2f}]"
          f"   mean declared {F[m].mean(0).round(3)}")


def diff(a, b):
    point = loss[a].mean() - loss[b].mean()
    boots = [loss[a][s].mean() - loss[b][s].mean() for s in draws]
    return point, np.percentile(boots, 2.5), np.percentile(boots, 97.5)


print("\nPre-registered differences (negative = better):")
tests = (("H1a B5_full - B1_full", "B5_full", "B1_full"), ("H1b G_full - B1_full", "G_full", "B1_full"),
         ("H2  B1_short - climatology", "B1_short", "climatology"), ("H2  B5_short - climatology", "B5_short", "climatology"),
         ("H2  G_short - climatology", "G_short", "climatology"),
         ("--  B1_full - climatology", "B1_full", "climatology"), ("--  B5_short - B1_short", "B5_short", "B1_short"),
         ("--  G_short - B1_short", "G_short", "B1_short"), ("--  G_full - B5_full", "G_full", "B5_full"))
for name, a, b in tests:
    p, lo, hi = diff(a, b)
    tag = ("PASS" if hi < 0 else "fail") if not name.startswith("--") else ""
    print(f"   {name:<28} {p:+.4f}  [{lo:+.4f}, {hi:+.4f}]  {tag}")

print("\nCalibration - declared bucket -> realised share (buckets with >= 100 cases):")
for m in MODELS:
    for k, name in ((0, "P(stop first)"), (1, "P(target first)")):
        p, y = F[m][:, k], Y[:, k]
        cells = []
        for lo_ in np.arange(0, 1, 0.1):
            sel = (p >= lo_) & (p < lo_ + 0.1 + (1e-9 if lo_ >= 0.9 else 0))
            if sel.sum() >= 100:
                cells.append(f"{p[sel].mean():.2f}->{y[sel].mean():.2f} ({sel.sum()})")
        print(f"   {m:<9} {name:<16} " + "  ".join(cells))

print("\nBrier by year:")
print("   year      n  " + "  ".join(f"{m:>9}" for m in (*MODELS, "climatology")))
for y in sorted(set(years)):
    s = years == y
    print(f"   {y}  {s.sum():5d}  " + "  ".join(f"{loss[m][s].mean():9.4f}" for m in (*MODELS, "climatology")))

names = ("risk_on", "neutral", "risk_off", "high_vol", "extreme")
print("\nBrier by regime at decision:")
for r in range(5):
    s = regs == r
    if s.sum() >= 200:
        print(f"   {names[r]:>9} n={s.sum():5d}  " + "  ".join(f"{m}={loss[m][s].mean():.4f}" for m in (*MODELS, "climatology")))
```
