# EXP-016 — Does Jev say how often a trade reaches its target before its stop, and is it right?

**Status:** COMPLETE 2026-09-28 · **H0: Jev earns no place as a forecaster in the ledger.** Both arms
score far *worse* than the cheap baselines (Brier +0.24, intervals well above zero). On features alone,
Jev's probabilities point the wrong way (it calls stop-first 0.84 where stops came first 15 %); given the
bootstrap's estimate, it copies the likeliest outcome at ~0.96. The bootstrap reproduces EXP-011's small
edge over climatology. Cost **$0.39**. Pre-registered 2026-09-28 (`4745c2e3`) before any scored call.
**Decision:** [DL-240](../../design-log.md) (the book as a distribution; the ledger comes first) · operator,
2026-09-28: *"I want to try JEV AI on it"* · work-queue **92** · the Jev idea in [ideas.md](../../ideas.md)
(2026-09-23/24) · test bed from [EXP-011](EXP-011-regime-markov-and-barrier-calibration.md).
**Cost:** Jev bills input only, $0.042 per million tokens; the run is capped at 10 M input tokens ($0.42).

## 1. Why we needed this experiment

The operator set the direction on 2026-09-28 ([DL-240](../../design-log.md), work-queue 92): manage the book
as a distribution. Every candidate and every held stock carries the probability of reaching its target
first, its stop first, or neither, and drop / trim / add / take-profit decisions follow from those
probabilities. Nothing may size a position on a probability until a ledger shows the probability comes
true. [EXP-011](EXP-011-regime-markov-and-barrier-calibration.md) had already found the best cheap model (a
bootstrap over each stock's own past days) beats simply quoting past outcome shares by only ~1 %. The
operator asked to try **TypeSafe's Jev** (*"I want to try JEV AI on it"*): a model that returns a calibrated
probability for each option of a typed question in one call, for fractions of a cent. Its vendor measures
calibration against frontier models' agreement, not against real outcomes, so the question was open.

## 2. Hypothesis

- **H1 (primary):** Jev given the features **and** the bootstrap's estimate (arm J2) scores a lower 3-outcome
  Brier than the bootstrap alone; the 95 % interval of the difference lies below zero.
- **H2 (secondary):** Jev given the features only (arm J1) scores a lower Brier than climatology (the
  outcome shares of all earlier years); interval below zero.
- **H0:** neither. Jev then earns no place as a forecaster in the ledger.

The Brier score measures how far a stated probability is from what happened (0 is perfect; lower is better).
The interval comes from resampling whole decision dates, because stocks on one date move together.

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
- **Test sample:** 60 decision dates drawn at random from 2018–2026 (seed `20260928`), every stock on each:
  **5,862** cases. **Pilot:** 30 cases from 2017, never scored.
- **Sent to Jev:** only features computed in code, rounded to 2 decimals, with **no ticker, date or sector**:
  stop and target distance, their ratio, ATR %, 20-session volatility against its 1-year median, returns
  over 5 / 20 / 60 / 250 sessions, distance from the 50- and 200-session averages and from the 250-session
  high, VIX and its regime label. J2 also received the bootstrap's three probabilities.
- Derived files (`exp016_sample.pkl`, prefix `1056bd7b2b29`; answers `exp016_jev_test.jsonl`, prefix
  `79cb0522035b`) are in OneDrive `trading-agents-data/exp016/`.

## 4. Tools and setup

- **Machine:** Intel Core i7-7660U (2 cores / 4 threads, 2.5 GHz), 15.9 GB RAM, Windows 10 Pro 19045.
- **Python** 3.13.2 run through **uv** 0.8.14; **numpy** 2.4.6.
- **Jev:** TypeSafe System One API, `POST https://api.typesafe.ai/v1/systemone`, model alias `jev-latest`,
  served by **`jev-1.13.0`** on every call; one `choice` question with three options per case. Key from
  `.env` (`TYPESAFE_API_KEY`), never in the repo.
- **Concurrency:** 6 parallel requests (4 for the pilot), 3 attempts per request, a hard stop at 10 M input
  tokens.
- **Seeds:** sample `20260928`; the bootstrap's paths `20260917` (1,000 paths per case); interval resampling
  `20260928` (1,000 resamples).
- **Repo:** pre-registered at `4745c2e3`; run and recorded from `main` the same day.
- **Cost:** **$0.39** (9.3 M input tokens at $0.042 per million; output is free), pilots $0.004. Median
  latency 0.28 s, 0 errors in 11,724 requests.

## 5. How it was conducted

1. Pre-registered the question, arms, sample, scoring and bar, and committed before any scored call.
2. Rebuilt EXP-011's 47,485 decisions from the cache and checked the reproduction.
3. Computed each test case's features, its climatology and its bootstrap estimate.
4. Ran the **pilot** (30 cases × 2 arms). Version 1 showed J2 collapsing onto the bootstrap's likeliest
   outcome (mean top probability 0.98). One rewording was allowed: ask for "the probability it would have
   across many such positions, not a verdict on the likeliest one". J2 moved only to 0.93, and the prompt
   was frozen there rather than tuned further.
5. Sent all 5,862 test cases through both arms (11,724 calls).
6. Scored the four models on the same cases: Brier, the two pre-registered differences with date-resampled
   intervals, calibration buckets, Brier by year, and Jev's confidence against its accuracy.

Two build defects were found and fixed before any call (neither changes the design): a rolling window that
read before a stock's first bar, and DOW's undefined volatility ratio, sent as `null`. Details in Appendix R.

## 6. Results

| Model | 3-outcome Brier (lower is better) |
| --- | --- |
| Bootstrap (`all_history`) | **0.6056** |
| Climatology | 0.6157 |
| Jev J2 (features + bootstrap estimate) | 0.8435 |
| Jev J1 (features only) | 0.8546 |

- **H1: fails.** J2 − bootstrap = **+0.238**, interval [+0.188, +0.289] (positive means worse).
- **H2: fails.** J1 − climatology = **+0.239**, interval [+0.172, +0.309].
- **J1's calibration runs backwards:** when it said stop-first 0.84 the stop came first 15 % of the time;
  when it said target-first 0.07 the target came first 62 %. At its highest confidence its top choice was
  right 12 % of the time.
- **J2 copies the likeliest outcome at ~0.96** (4,807 of 5,862 answers at confidence ≥ 0.8), right 55 % of the
  time there.
- The bootstrap beats climatology by −0.0101 [−0.0197, +0.0001]: EXP-011's small edge again.
- No period where Jev does well (best J1 year 0.743; worst climatology year 0.674), so recall of history does
  not explain it.

## 7. Conclusions

- **Jev is not a forecaster of these probabilities.** On numbers alone it applies a "risky-looking, so the
  stop comes first" intuition, where this repo has twice measured the opposite (EXP-012, EXP-013: volatile
  and stressed names returned more). Given a model's estimate it does not blend; it picks.
- A `choice` answer's probabilities are Jev's belief about which option is the answer, not a frequency; the
  wording could not change that. That fits its own documentation ("keep the arithmetic in code").
- **What it does not say:** nothing about Jev on typed judgements over text, which is what it is built for
  (the deliberator-verdict and sentiment shadow path in [ideas.md](../../ideas.md)).
- The ledger's challengers are **simulation models**, which led to
  [EXP-017](EXP-017-block-bootstrap-and-garch-barrier-probabilities.md).

## 8. Recommended code changes, and how to implement them

1. **No change to the fleet's code.** Do not add Jev as a probability source in the forecaster or the PM.
2. **Move the barrier test bed into the repo** (`scripts/barrier_testbed.py`): the decision builder,
   outcome rule, climatology and the date-resampled scorer that EXP-011, EXP-016 and EXP-017 each carried as
   appendix code. *How:* a chore on its own branch (`chore-barrier-testbed`), the logic extracted from
   Appendix S unchanged; unit tests on a synthetic three-stock fixture (low-before-high, a 0 % target,
   neither); the reproduction (47,485 cases, 0.285 / 0.480 / 0.235) as the planner's live check from the
   main checkout; module size under 200; full `make ci` and gate; PATCH bump. No deploy (scripts ship in no
   image). The planner decides; it is tooling.
3. **Jev's typed-text shadow path stays a separate, unranked idea** ([ideas.md](../../ideas.md)); this result
   neither blocks nor supports it.

## Appendix P — Pre-registration (frozen)

Verbatim as committed at `4745c2e3`, before any scored call.

### Purpose

**Question.** For the fleet's own stop and target on a trade, does TypeSafe's **Jev** (`jev-latest`) give
probabilities for *stop first / target first / neither within 10 sessions* that come true, better than the
cheap baselines EXP-011 already scored?

**Why it matters.** DL-240 makes the book a distribution: each position carries the chance of reaching its
target first, its stop first, or neither. Nothing may size on a probability until a ledger shows it comes
true. EXP-011 found the best cheap model (`all_history`, a bootstrap over the name's own past days) beats
climatology by only **0.0060** Brier. Jev returns a calibrated distribution over typed options in one call
for fractions of a cent, so it is the cheapest candidate to try as a challenger. Jev's vendor measures
calibration against frontier models' agreement, not against outcomes; this measures it against outcomes.

**Hypotheses.**

- **H1 (primary): Jev adds to the simulation.** Arm **J2** (features plus the `all_history` estimate) has a
  lower 3-outcome Brier score than `all_history` alone, and the 95 % confidence interval of the difference
  lies below zero.
- **H2 (secondary): Jev forecasts on its own.** Arm **J1** (features only) has a lower Brier score than
  climatology, 95 % interval below zero.
- **H0.** Neither holds. Jev then earns no place as a forecaster in the ledger. That says nothing about the
  other typed decisions the ideas entry proposes to shadow.

Two arms are tested, and each hypothesis names its own arm and baseline; neither is re-labelled after the
fact.

### Process

Everything below is fixed now.

**Test bed: EXP-011's decisions, rebuilt from the replay cache** (`scripts/replay_dataset.py`, OneDrive
`trading-agents-data`: 263,005 SIP bars, 98 names, 2016-01-04 → 2026-09-16; never the repo). A decision at
the close of every 5th session from 2017-01-03, per name. S211's barriers exactly as EXP-011 computed them:
stop = clamp(2 × ATR14 ÷ close, 2.5 %, 8 %); target = median best close-to-high rise within 10 sessions over
the 120 prior settled windows. Outcome over the next 10 sessions: the low is checked before the high (a day
touching both counts as a stop); otherwise neither. **Reproduction check before any scored call:** 47,485
cases with realised shares 0.285 / 0.480 / 0.235. A mismatch stops the run and is reported.

**Test sample.** **60 decision dates** drawn uniformly without replacement from the 2018–2026 decision dates
(seed `20260928`), with every name on each drawn date: about 5,900 cases. Whole dates, because names on one
date move together.

**Pilot (not scored).** Up to **30 cases** from 2017 dates, to check the request and response shapes and the
feature rendering. The prompt is then frozen and recorded in *Delivery*. Pilot answers are never scored.

**Baselines, on the same test cases:**

- **climatology:** outcome shares of all cases in earlier years (EXP-011's yearly refit);
- **`all_history`:** 1,000 simulated 10-session paths per case, resampling the name's own daily moves dated
  at or before the decision (EXP-011's code; seed `20260917`).

**Arms.** One Jev request per case, one `choice` question with three options:

- **`stop_first`**: the low reaches the stop level on some day before the high reaches the target level
  (a day touching both counts here);
- **`target_first`**: the high reaches the target level first;
- **`neither`**: neither level is reached within 10 sessions.

The `state` holds only features computed in code, rounded to 2 decimals, with no ticker, date, sector or
name (Jev's documentation advises keeping arithmetic in code, and anonymity keeps it from recalling a
famous stock's history):

- the barriers: stop distance %, target distance %, target-to-stop ratio;
- volatility: ATR14 % of price; 20-session realised volatility ÷ its 250-session median;
- trend: returns over 5, 20, 60 and 250 sessions %; close against its 50- and 200-session averages %;
  distance below the 250-session high %;
- market: VIX close and the provider's regime label for it.

**J1** sends those features. **J2** sends the same plus the `all_history` probabilities, labelled as a
historical resampling estimate. Nothing else differs.

**Scoring** (test sample only):

- 3-outcome Brier for J1, J2, climatology and `all_history`;
- differences J2 − `all_history` (H1) and J1 − climatology (H2), each with a 95 % interval from 1,000
  resamples of whole dates (seed `20260928`);
- calibration: for P(stop first) and P(target first), declared against realised share in buckets of 0.1,
  shown where a bucket holds at least 50 cases;
- Brier by year, as a check on period effects or recall;
- Jev's `confidence` against its accuracy, descriptive only;
- tokens, cost, latency and errors.

**Failure handling.** A request that fails after 3 attempts is recorded as missing. If more than 2 % of the
test cases are missing, the verdict is INSUFFICIENT. Otherwise the missing cases are dropped from all four
models alike.

## Appendix R — Run record

**Run 2026-09-28**, planner, from the main checkout with `.env` (`TYPESAFE_API_KEY`), data in OneDrive
`trading-agents-data/exp016/` (never the repo). Served by **`jev-1.13.0`** throughout.

**Reproduction check: passed.** The rebuilt test bed gives **47,485** cases (486 dates × 98 names) and
realised shares **0.285 / 0.480 / 0.235**, EXP-011's exactly.

**Test sample:** 60 dates, 2018-01-08 → 2026-08-20, **5,862** cases; realised stop / target / neither
**0.208 / 0.524 / 0.268**. **0 missing** (11,724 requests, 0 errors), so all four models are scored on the
same 5,862 cases.

**Two build defects, fixed before any call** (neither changes the design):

- The 20-session volatility ratio's rolling window reached before a name's first bar for the earliest
  decisions, and a negative slice returned `NaN`. The median now runs over full 20-return windows only.
- **DOW** has flat placeholder bars in the cache for 2018 (it listed in 2019), so 15 test cases have an
  undefined volatility ratio, 14 of them a 0 % target. The ratio is sent as `null`; the cases stay in,
  scored alike by all four models. They are in EXP-011's set too.

**Pilot (30 cases from 2017, not scored), two versions:**

| Version | J1 mean probabilities (stop / target / neither) | J1 mean top probability | J2 mean top probability |
| --- | --- | --- | --- |
| v1: "which happens first?" | 0.37 / 0.33 / 0.30 | 0.45 | **0.98** |
| v2 (frozen): adds "give each outcome the probability it would have across many such positions, not a verdict on the likeliest one"; the estimate labelled "frequencies from an imperfect model" | 0.40 / 0.33 / 0.27 | 0.45 | **0.93** |

v1 showed J2 collapsing onto the bootstrap's likeliest outcome. v2 was the one rewording allowed; it barely
moved J2, and the prompt was frozen there rather than tuned further. Pilot cost $0.004.

**Scored output** (`exp016_score.py`):

```text
test cases 5862, missing 0 (0.00 %)
scored 5862 cases on 60 dates; realised stop/target/neither [0.208 0.524 0.268]

Brier (3-outcome, lower is better):
   0.8546  J1   mean declared [0.526 0.248 0.226]
   0.8435  J2   mean declared [0.126 0.758 0.116]
   0.6056  all_history   mean declared [0.282 0.467 0.251]
   0.6157  climatology   mean declared [0.268 0.486 0.246]

Pre-registered differences (negative = better), 95 % interval resampling whole dates:
   H1  J2 - all_history           +0.2380  [+0.1882, +0.2888]  fail
   H2  J1 - climatology           +0.2389  [+0.1718, +0.3093]  fail
   --  all_history - climatology  -0.0101  [-0.0197, +0.0001]
   --  J1 - all_history           +0.2491  [+0.1783, +0.3218]

Calibration - declared bucket -> realised share (buckets with >= 50 cases):
   J1 P(stop first): said 0.28 got 0.19 (n=407); said 0.35 got 0.25 (n=1268); said 0.44 got 0.25 (n=1219); said 0.54 got 0.20 (n=983); said 0.65 got 0.18 (n=727); said 0.75 got 0.17 (n=662); said 0.84 got 0.15 (n=492)
   J1 P(target first): said 0.07 got 0.62 (n=855); said 0.14 got 0.55 (n=1514); said 0.25 got 0.49 (n=1541); said 0.35 got 0.48 (n=995); said 0.44 got 0.49 (n=710); said 0.53 got 0.49 (n=222)
   J2 P(stop first): said 0.04 got 0.19 (n=4655); said 0.13 got 0.27 (n=561); said 0.24 got 0.30 (n=141); said 0.98 got 0.31 (n=426)
   J2 P(target first): said 0.02 got 0.29 (n=755); said 0.14 got 0.46 (n=286); said 0.24 got 0.54 (n=140); said 0.34 got 0.46 (n=72); said 0.76 got 0.29 (n=77); said 0.86 got 0.41 (n=407); said 0.96 got 0.59 (n=4043)
   all_history P(stop first): said 0.07 got 0.09 (n=138); said 0.16 got 0.13 (n=1072); said 0.25 got 0.18 (n=2082); said 0.35 got 0.24 (n=1925); said 0.43 got 0.34 (n=625)
   all_history P(target first): said 0.17 got 0.22 (n=58); said 0.26 got 0.29 (n=272); said 0.36 got 0.41 (n=1108); said 0.45 got 0.50 (n=2115); said 0.54 got 0.60 (n=1813); said 0.63 got 0.74 (n=442)

Brier by year:
   year     n     J1     J2  all_hist  climat
   2018   776  0.8273  0.8571  0.6093  0.6035
   2019   970  0.8012  0.8787  0.6019  0.6200
   2020  1078  0.8765  0.7713  0.5927  0.5965
   2021   784  0.7892  0.9941  0.6521  0.6738
   2022   490  1.2125  0.5704  0.5107  0.5352
   2023   294  0.9046  0.8335  0.5896  0.6150
   2024   588  0.7431  0.9210  0.6443  0.6516
   2025   294  0.7569  0.8887  0.6320  0.6365
   2026   588  0.8631  0.8321  0.6031  0.6032

Confidence vs accuracy (descriptive):
   J1 confidence 0.0-0.2: n= 2114  top choice right 0.323
   J1 confidence 0.2-0.5: n= 2293  top choice right 0.256
   J1 confidence 0.5-0.8: n= 1324  top choice right 0.167
   J1 confidence 0.8-1.0: n=  131  top choice right 0.122
   J2 confidence 0.0-0.2: n=    1  top choice right 1.000
   J2 confidence 0.2-0.5: n=  190  top choice right 0.432
   J2 confidence 0.5-0.8: n=  864  top choice right 0.370
   J2 confidence 0.8-1.0: n= 4807  top choice right 0.553

requests 11724, errors 0, input tokens 9,299,767 ($0.3906), latency median 0.28s p95 0.34s, models ['jev-1.13.0']
degenerate DOW cases (0 % target) kept in all four models: 14
```

### Reproducing

Data: the replay cache (`scripts/replay_dataset.py --describe`: 263,005 bars, 98 names). From the repo root:
`PYTHONPATH=. uv run python exp016_build.py <dir>` (writes `exp016_sample.pkl`), then
`uv run --env-file .env python exp016_jev.py <dir> pilot|test 6` (resumable JSONL; capped at 10 M input
tokens), then `uv run python exp016_score.py <dir>`. Seeds are fixed; Jev's answers are its own and may
drift across model versions.

## Appendix S — Scripts

### `exp016_build.py`

```python
"""EXP-016 step 1 - rebuild EXP-011's decisions from the replay cache; features, baselines, sample.

PYTHONPATH=<repo> uv run python exp016_build.py <out_dir>
Decision at the close of day t; everything computed is dated <= t. Barriers and outcome exactly EXP-011's.
"""
import pickle
import sys
from pathlib import Path

import numpy as np

from scripts.replay_dataset import load

H, LOOKBACK, ATR_N, N_PATHS, STEP, RECENT = 10, 120, 14, 1000, 5, 250
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
vix, bars = load()


def label(v):
    return 4 if v >= 35 else 3 if v >= 25 else 2 if v >= 20 else 0 if v <= 15 else 1


REGIME = ("risk_on", "neutral", "risk_off", "high_vol", "extreme")
vixlab = {k: label(v) for k, v in vix.items()}
calendar = sorted({b[0] for rows in bars.values() for b in rows})
decision_dates = set(calendar[calendar.index("2017-01-03")::STEP])

cases = []  # one dict per decision
for sym, rows in sorted(bars.items()):
    dates = [r[0] for r in rows]
    hi, lo, cl = (np.array([r[k] for r in rows]) for k in (2, 3, 4))
    tr = np.maximum.reduce([hi[1:] - lo[1:], abs(hi[1:] - cl[:-1]), abs(lo[1:] - cl[:-1])])
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
        cases.append({"sym": sym, "day": day, "t": t, "stop": stop, "target": target,
                      "atr_pct": atr_pct, "outcome": outcome})

Y = np.eye(3)[[c["outcome"] for c in cases]]
days = np.array([c["day"] for c in cases])
years = np.array([int(d[:4]) for d in days])
print(f"cases {len(cases)} ({len(set(days))} dates x {len({c['sym'] for c in cases})} names)")
print("realised: stop first {:.3f}  target first {:.3f}  neither {:.3f}".format(*Y.mean(0)))

# climatology: outcome shares of all earlier years (EXP-011's yearly refit)
clim = np.zeros_like(Y)
for i, y in enumerate(years):
    prior = years < y
    clim[i] = Y[prior].mean(0) if prior.sum() > 500 else Y[:500].mean(0)

# the test sample: 60 whole dates from 2018-2026; the pilot: 30 cases from 2017
rng = np.random.default_rng(20260928)
test_dates = sorted(rng.choice(sorted({d for d in days if d >= "2018"}), 60, replace=False))
test_idx = [i for i, d in enumerate(days) if d in set(test_dates)]
pilot_pool = [i for i, d in enumerate(days) if d < "2018"]
pilot_idx = sorted(rng.choice(pilot_pool, 30, replace=False).tolist())
print(f"test: {len(test_dates)} dates, {len(test_idx)} cases ({test_dates[0]} .. {test_dates[-1]}); pilot {len(pilot_idx)}")

sim_rng = np.random.default_rng(20260917)
by_sym = {sym: rows for sym, rows in bars.items()}


def features(c):
    rows = by_sym[c["sym"]]
    t = c["t"]
    hi, cl = (np.array([r[k] for r in rows[: t + 1]]) for k in (2, 4))
    lr = np.log(cl[1:] / cl[:-1])
    vol = [lr[j - 20:j].std() for j in range(max(20, t - 249), t + 1)]  # full 20-return windows only
    f = {
        "stop_distance_pct": 100 * c["stop"],
        "target_distance_pct": 100 * c["target"],
        "target_to_stop_ratio": c["target"] / c["stop"],
        "atr14_pct_of_price": 100 * c["atr_pct"],
        "volatility_20d_vs_its_1y_median": (vol[-1] / float(np.median(vol))) if float(np.median(vol)) > 0 else None,
        "return_5d_pct": 100 * (cl[t] / cl[t - 5] - 1),
        "return_20d_pct": 100 * (cl[t] / cl[t - 20] - 1),
        "return_60d_pct": 100 * (cl[t] / cl[t - 60] - 1),
        "return_250d_pct": 100 * (cl[t] / cl[t - 250] - 1),
        "close_vs_50d_average_pct": 100 * (cl[t] / cl[t - 49:t + 1].mean() - 1),
        "close_vs_200d_average_pct": 100 * (cl[t] / cl[t - 199:t + 1].mean() - 1),
        "below_250d_high_pct": 100 * (1 - cl[t] / hi[t - 249:t + 1].max()),
        "vix_close": vix[c["day"]],
        "vix_regime": REGIME[vixlab[c["day"]]],
    }
    out = {k: (v if v is None or isinstance(v, str) else round(float(v), 2)) for k, v in f.items()}
    assert all(v is None or isinstance(v, str) or np.isfinite(v) for v in out.values()), (c['sym'], c['day'], out)
    return out


def all_history(c):
    rows = by_sym[c["sym"]]
    t = c["t"]
    hi, lo, cl = (np.array([r[k] for r in rows]) for k in (2, 3, 4))
    rh, rl, rc = hi[1:] / cl[:-1], lo[1:] / cl[:-1], cl[1:] / cl[:-1]
    idx = sim_rng.choice(np.arange(0, t), (N_PATHS, H))
    cc = np.cumprod(rc[idx], axis=1)
    prev = np.concatenate([np.ones((N_PATHS, 1)), cc[:, :-1]], axis=1)
    hit_s = prev * rl[idx] <= 1 - c["stop"]
    hit_t = prev * rh[idx] >= 1 + c["target"]
    fs = np.where(hit_s.any(1), hit_s.argmax(1), H)
    ft = np.where(hit_t.any(1), hit_t.argmax(1), H)
    p_stop = float(np.mean((fs < H) & (fs <= ft)))
    p_target = float(np.mean((ft < H) & (ft < fs)))
    return (p_stop, p_target, 1 - p_stop - p_target)


sample = {}
for i in pilot_idx + test_idx:
    c = cases[i]
    sample[i] = {**{k: c[k] for k in ("sym", "day", "outcome")}, "features": features(c),
                 "all_history": all_history(c), "climatology": tuple(clim[i]),
                 "role": "pilot" if i in pilot_idx else "test"}
pickle.dump({"sample": sample, "test_dates": test_dates, "n_cases": len(cases),
             "realised": tuple(Y.mean(0))}, open(OUT / "exp016_sample.pkl", "wb"))
print("wrote", OUT / "exp016_sample.pkl", len(sample))
print("example features:", sample[test_idx[0]]["features"])
nulls = [(s["sym"], s["day"], s["role"]) for s in sample.values() if s["features"]["volatility_20d_vs_its_1y_median"] is None]
print("undefined volatility ratio:", len(nulls), sorted({x[0] for x in nulls}), "test:", sum(x[2] == "test" for x in nulls))
flat = [s for s in sample.values() if s["role"] == "test" and s["features"]["target_distance_pct"] == 0]
print("test cases with a 0 % target (degenerate):", len(flat), sorted({s["sym"] for s in flat}))
```

### `exp016_jev.py` (the frozen v2 prompt)

```python
"""EXP-016 step 2 - ask Jev, one choice question per case and arm; resumable JSONL.

uv run --env-file <repo>/.env python exp016_jev.py <out_dir> <pilot|test> [workers]
"""
import json
import os
import pickle
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

OUT = Path(sys.argv[1])
ROLE = sys.argv[2]
WORKERS = int(sys.argv[3]) if len(sys.argv) > 3 else 4
TOKEN_CAP = 10_000_000
KEY = os.environ["TYPESAFE_API_KEY"]
URL = "https://api.typesafe.ai/v1/systemone"

INSTRUCTIONS = {
    "question": (
        "A long position in one stock is entered at today's close. Over the next 10 trading sessions, "
        "which happens first? Stock prices are highly uncertain: many positions that look alike end "
        "differently, so give each outcome the probability it would have across many such positions, "
        "not a verdict on the likeliest one."
    ),
    "rules": (
        "The stop level is stop_distance_pct percent below today's close. The target level is "
        "target_distance_pct percent above today's close. Sessions are checked in order. In each session "
        "the low is checked before the high: if the session's low reaches the stop level, the stop comes "
        "first, even if the same session's high also reaches the target level. If neither level is reached "
        "within 10 sessions, the answer is neither."
    ),
}
CRITERIA = {
    "stop_first": "The price falls to the stop level before it rises to the target level "
    "(a session that touches both counts as stop first).",
    "target_first": "The price rises to the target level before it falls to the stop level.",
    "neither": "Neither the stop level nor the target level is reached within 10 trading sessions.",
}
ESTIMATE_NOTE = (
    "Share of 1,000 simulated 10-session paths, built by resampling this stock's own past daily moves, "
    "that end in each outcome. These are frequencies from an imperfect model, not a prediction that "
    "the largest one will happen."
)


def body(case, arm):
    state = {"position": case["features"]}
    if arm == "J2":
        p = case["all_history"]
        state["historical_resampling_estimate"] = {
            "note": ESTIMATE_NOTE,
            "stop_first": round(p[0], 3),
            "target_first": round(p[1], 3),
            "neither": round(p[2], 3),
        }
    return {
        "state": state,
        "model": "jev-latest",
        "questions": {"first_barrier": {"type": "choice", "instructions": INSTRUCTIONS, "criteria": CRITERIA}},
    }


def ask(payload):
    data = json.dumps(payload).encode()
    last = ""
    for attempt in range(3):
        req = urllib.request.Request(
            URL, data=data, method="POST",
            headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        )
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read()), time.time() - t0, None
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code} {e.read()[:200]!r}"
            time.sleep(2 ** attempt * (5 if e.code == 429 else 1))
        except Exception as e:  # noqa: BLE001 - recorded, retried
            last = f"{type(e).__name__}: {e}"
            time.sleep(2 ** attempt)
    return None, None, last


def main():
    d = pickle.load(open(OUT / "exp016_sample.pkl", "rb"))
    todo_cases = {i: c for i, c in d["sample"].items() if c["role"] == ROLE}
    log = OUT / f"exp016_jev_{ROLE}.jsonl"
    done = set()
    tokens = 0
    if log.exists():
        for line in log.read_text().splitlines():
            r = json.loads(line)
            if r.get("answer"):
                done.add((r["case"], r["arm"]))
            tokens += r.get("input_tokens") or 0
    jobs = [(i, arm) for i in sorted(todo_cases) for arm in ("J1", "J2") if (i, arm) not in done]
    print(f"{ROLE}: {len(todo_cases)} cases, {len(jobs)} requests to send, {tokens:,} input tokens so far", flush=True)
    lock = threading.Lock()
    state = {"tokens": tokens, "n": 0, "fail": 0}

    def run(job):
        i, arm = job
        with lock:
            if state["tokens"] > TOKEN_CAP:
                return
        resp, secs, err = ask(body(todo_cases[i], arm))
        rec = {"case": i, "arm": arm, "secs": secs, "error": err}
        if resp:
            a = resp["answers"]["first_barrier"]
            rec.update(model=resp.get("model"), answer=a.get("probabilities"), choice=a.get("choice"),
                       confidence=a.get("confidence"), input_tokens=resp["usage"]["input_tokens"],
                       output_tokens=resp["usage"]["output_tokens"])
        with lock:
            state["tokens"] += rec.get("input_tokens") or 0
            state["n"] += 1
            state["fail"] += 0 if resp else 1
            with log.open("a") as f:
                f.write(json.dumps(rec) + "\n")
            if state["n"] % 250 == 0:
                print(f"  {state['n']}/{len(jobs)} sent, {state['fail']} failed, {state['tokens']:,} tokens", flush=True)

    with ThreadPoolExecutor(WORKERS) as pool:
        list(pool.map(run, jobs))
    print(f"done: {state['n']} sent, {state['fail']} failed, {state['tokens']:,} input tokens "
          f"(${state['tokens'] * 0.042 / 1e6:.4f})", flush=True)


main()
```

### `exp016_score.py`

```python
"""EXP-016 step 3 - score the test sample exactly as pre-registered.

uv run python exp016_score.py <out_dir>
"""
import json
import pickle
import sys
from pathlib import Path

import numpy as np

OUT = Path(sys.argv[1])
d = pickle.load(open(OUT / "exp016_sample.pkl", "rb"))
test = {i: c for i, c in d["sample"].items() if c["role"] == "test"}
K = ("stop_first", "target_first", "neither")
ans = {}
recs = [json.loads(line) for line in (OUT / "exp016_jev_test.jsonl").read_text().splitlines()]
for r in recs:
    if r.get("answer"):
        ans[(r["case"], r["arm"])] = [r["answer"][k] for k in K]
missing = [i for i in test if (i, "J1") not in ans or (i, "J2") not in ans]
print(f"test cases {len(test)}, missing {len(missing)} ({100 * len(missing) / len(test):.2f} %)")
if len(missing) > 0.02 * len(test):
    print("VERDICT: INSUFFICIENT (more than 2 % missing)")
keep = sorted(i for i in test if i not in set(missing))
Y = np.eye(3)[[test[i]["outcome"] for i in keep]]
F = {
    "J1": np.array([ans[(i, "J1")] for i in keep]),
    "J2": np.array([ans[(i, "J2")] for i in keep]),
    "all_history": np.array([test[i]["all_history"] for i in keep]),
    "climatology": np.array([test[i]["climatology"] for i in keep]),
}
dates = np.array([test[i]["day"] for i in keep])
years = np.array([int(x[:4]) for x in dates])
loss = {m: ((P - Y) ** 2).sum(1) for m, P in F.items()}
print(f"scored {len(keep)} cases on {len(set(dates))} dates; realised stop/target/neither {Y.mean(0).round(3)}")
print("\nBrier (3-outcome, lower is better):")
for m in F:
    print(f"   {loss[m].mean():.4f}  {m}   mean declared {F[m].mean(0).round(3)}")

rng = np.random.default_rng(20260928)
udates = np.unique(dates)
by_date = {u: np.where(dates == u)[0] for u in udates}
draws = [np.concatenate([by_date[u] for u in rng.choice(udates, len(udates))]) for _ in range(1000)]


def diff(a, b):
    point = loss[a].mean() - loss[b].mean()
    boots = [loss[a][s].mean() - loss[b][s].mean() for s in draws]
    return point, np.percentile(boots, 2.5), np.percentile(boots, 97.5)


print("\nPre-registered differences (negative = better), 95 % interval resampling whole dates:")
for name, a, b in (("H1  J2 - all_history", "J2", "all_history"), ("H2  J1 - climatology", "J1", "climatology"),
                   ("--  all_history - climatology", "all_history", "climatology"),
                   ("--  J1 - all_history", "J1", "all_history")):
    p, lo, hi = diff(a, b)
    verdict = "PASS" if hi < 0 else "fail"
    print(f"   {name:<30} {p:+.4f}  [{lo:+.4f}, {hi:+.4f}]  {verdict if name.startswith('H') else ''}")

print("\nCalibration - declared bucket -> realised share (buckets with >= 50 cases):")
for m in ("J1", "J2", "all_history"):
    for k, name in ((0, "P(stop first)"), (1, "P(target first)")):
        p, y = F[m][:, k], Y[:, k]
        cells = []
        for lo_ in np.arange(0, 1, 0.1):
            sel = (p >= lo_) & (p < lo_ + 0.1 + (1e-9 if lo_ >= 0.9 else 0))
            if sel.sum() >= 50:
                cells.append(f"said {p[sel].mean():.2f} got {y[sel].mean():.2f} (n={sel.sum()})")
        print(f"   {m} {name}: " + "; ".join(cells))

print("\nBrier by year:")
print("   year     n     J1     J2  all_hist  climat")
for y in sorted(set(years)):
    s = years == y
    print(f"   {y}  {s.sum():4d}  " + "  ".join(f"{loss[m][s].mean():.4f}" for m in ("J1", "J2", "all_history", "climatology")))

conf = {arm: np.array([r["confidence"] for r in recs if r["arm"] == arm and r.get("answer") and r["case"] in set(keep)])
        for arm in ("J1", "J2")}
print("\nConfidence vs accuracy (descriptive):")
for arm in ("J1", "J2"):
    cases = [r for r in recs if r["arm"] == arm and r.get("answer") and r["case"] in set(keep)]
    c = np.array([r["confidence"] for r in cases])
    hit = np.array([K.index(r["choice"]) == test[r["case"]]["outcome"] for r in cases])
    for lo_, hi_ in ((0, .2), (.2, .5), (.5, .8), (.8, 1.01)):
        s = (c >= lo_) & (c < hi_)
        if s.sum():
            print(f"   {arm} confidence {lo_:.1f}-{min(hi_, 1):.1f}: n={s.sum():5d}  top choice right {hit[s].mean():.3f}")
tok = sum(r.get("input_tokens") or 0 for r in recs)
secs = sorted(r["secs"] for r in recs if r.get("secs"))
print(f"\nrequests {len(recs)}, errors {sum(1 for r in recs if r['error'])}, input tokens {tok:,} (${tok * 0.042 / 1e6:.4f}), "
      f"latency median {secs[len(secs) // 2]:.2f}s p95 {secs[int(len(secs) * .95)]:.2f}s, models {sorted({r.get('model') for r in recs if r.get('model')})}")
dow = [i for i in keep if test[i]["features"]["target_distance_pct"] == 0]
print(f"degenerate DOW cases (0 % target) kept in all four models: {len(dow)}")
```
