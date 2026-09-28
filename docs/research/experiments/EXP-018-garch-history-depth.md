# EXP-018 — With boundary fits accepted, does GARCH clear the bar on a history the fleet can supply?

**Status:** COMPLETE 2026-09-28 · **H1 passes at 756 bars: GARCH(1,1) on ~3 years of history is the first model to
clear the bar** (skill **+2.67 %** over climatology, 95 % interval [+1.88, +3.48], 0.39 % failed fits). At the
fleet's 203 bars it has real skill (+1.57 %) but falls short; three years beats ten. A live 756-bar SIP fetch
costs 8 pages and 19 seconds. Pre-registered at `0e3f6b03`; $0.
**Decision / origin:** [DL-240](../../design-log.md) · operator, 2026-09-28: *"run EXP-018"* · work-queue **92** ·
follows [EXP-017](EXP-017-block-bootstrap-and-garch-barrier-probabilities.md) · **Cost:** $0 (local simulation;
one read-only Alpaca request for the side measurement).

## 1. Why we needed this experiment

EXP-017 found GARCH(1,1) the only model with skill on the fleet's 203 bars (+1.47 % over climatology; +2.26 %
on full history), but its verdict was INSUFFICIENT: 6.2 % of fits fell back, against a 2 % limit. A check after
scoring showed almost all of them were estimates on the persistence boundary (α + β = 1), which the acceptance
rule rejected by requiring α + β strictly below 1, not optimiser failures. And no model cleared the 2 % bar on
the history production has. Since S238 the provider can fetch SIP bars with a safe `end`, so a longer history
per run is possible. This experiment settles whether GARCH, fitted properly, clears the bar on a depth
production can supply, and what that depth costs to fetch. It decides whether item 92's live ledger is built,
and on which model and depth.

## 2. Hypothesis

For each depth *d* in {**203** bars (today's fleet), **756** bars (~3 years)}:

- **H1(d):** GARCH at depth *d* has Brier skill against climatology of at least **2 %** (1 − Brier ÷
  Brier_climatology), with the 95 % interval's lower bound above zero, **and** at most 2 % failed fits.
- **H2:** GARCH at 756 bars has a lower Brier than at 203 bars, 95 % interval of the difference below zero
  (more history helps).
- **Production candidate:** the shallowest depth for which H1 holds. If neither holds, the full-history result
  is reported for reference only, and the ledger is not built on GARCH as it stands.
- **H0:** H1 fails at both depths.

## 3. Data

The replay cache, exactly as in EXP-016 and EXP-017: `bars.csv.gz` (sha-256 prefix `12374e3e5493`), 263,005
SIP split- and dividend-adjusted daily bars, 98 names, 2016-01-04 → 2026-09-16; `vix.csv.gz` (prefix
`e5d4fe621031`). EXP-011's decisions rebuilt from it (reproduction check: **47,485** cases, realised 0.285 /
0.480 / 0.235, else the run stops).

**Scored set (primary):** decisions dated 2018–2026 that have at least **756** prior daily moves, so every depth
exists for every scored case (from about 2019-01 for most stocks). The same cases for every model.
**Secondary (for comparison with EXP-017):** 203 bars and full history on all 2018–2026 decisions.

**Side measurement (live, read-only):** one fetch through the fleet's own provider code
(`market_source_from_settings`, SIP default, main at the run) of the 99 live universe names plus SPY over a
window ending today that holds 756 sessions: pages, bars, bytes, seconds, and any refusal.

## 4. Tools and setup

As EXP-017: Intel Core i7-7660U (2 cores / 4 threads), 15.9 GB RAM, Windows 10 Pro 19045; Python 3.13.2 through
uv 0.8.14; numpy 2.4.6; arch 8.0.0, scipy 1.17.1, statsmodels 0.15.0 loaded for the run only; 4 worker
processes, one per stock. **Seeds:** paths `default_rng([20260928, stock_index])`; interval resampling
`20260929`, 1,000 resamples of whole decision dates.

## 5. How it was conducted

**Model:** GARCH(1,1), Student-t innovations, filtered historical simulation, exactly as EXP-017's `G` (fitted
per stock and calendar month on the history available at the month's first decision; volatility follows the
recursion; each simulated day's close, high and low are a past day's standardised shape rescaled; 1,000 paths
× 10 sessions per case), with **one change to fit acceptance:**

- A fit is **accepted** when the optimiser converges and ω > 0, α ≥ 0, β ≥ 0, **α + β ≤ 1** (the boundary is
  accepted).
- In the recursion and simulation, persistence is capped: if α + β > 0.999, α and β are scaled in proportion
  so that α + β = 0.999, keeping variance finite. The count of capped fits is reported.
- A **failed** fit is non-convergence or an exception; it reuses the previous month's accepted parameters, and
  more than 2 % failed fits at a depth fails H1 at that depth.

**Depths:** 203, 756 and full, each fitted and simulated separately.

**Scoring:** 3-outcome Brier and skill against climatology with date-resampled 95 % intervals for each depth
on the primary set; H2's difference; calibration buckets (≥ 100 cases) for P(stop first) and P(target first);
Brier by year and by VIX regime; fit counts (accepted, capped, failed) per depth. Secondary: 203 and full on
all 2018–2026 decisions.

**Side measurement:** run once, after the simulation, from the main checkout with `.env`.

## 6. Results

**Primary set:** 37,587 decisions on 385 dates, 2019-01-07 → 2026-08-27, every depth present; realised
stop / target / neither 0.287 / 0.477 / 0.236.

| GARCH history | Brier | Skill vs climatology | 95 % interval | Failed fits | Capped fits |
| --- | --- | --- | --- | --- | --- |
| **756 bars (~3 years)** | **0.6183** | **+2.67 %** | [+1.88, +3.48] | 0.39 % | 4.40 % |
| Full history | 0.6204 | +2.35 % | [+1.55, +3.19] | 0.58 % | 6.22 % |
| 203 bars (today's fleet) | 0.6254 | +1.57 % | [+0.83, +2.31] | 0.44 % | 11.49 % |
| Climatology | 0.6353 | 0 | — | — | — |

- **H1(756): PASS.** Skill +2.67 % ≥ 2 %, lower bound +1.88 % > 0, failed fits 0.39 % ≤ 2 %.
- **H1(203): fail.** Real skill (+1.57 %, interval above zero) but short of the 2 % bar.
- **H2: PASS.** 756 − 203 = **−0.0070** [−0.0109, −0.0029]: more history helps.
- **Three years beats ten** (descriptive): full − 756 = +0.0021 [+0.0002, +0.0038]. Older history dilutes the
  current volatility regime.
- **Accepting boundary fits fixed the reliability problem:** failed fits fell from EXP-017's 6.2 % to
  0.39–0.58 %. Short histories hit the persistence cap most often (11.5 % at 203 bars).
- **Calibration at 756 bars** is close to the diagonal for target-first (said 0.26 → got 0.28, 0.45 → 0.45,
  0.55 → 0.55, 0.64 → 0.65) and for the middle of stop-first (0.25 → 0.27, 0.34 → 0.33); its lowest
  stop-first bucket is still over-confident (said 0.07 → got 0.18, 205 cases).
- **Every year** from 2019 to 2025, GARCH at 756 bars beats climatology (2026, a part year: 0.6084 against
  0.6102). The edge is largest in stress: VIX `extreme` 0.487 against 0.523, `high_vol` 0.585 against 0.608.
- **Comparable with EXP-017** (all 2018–2026 decisions): 203 bars +1.49 %, full +2.30 %, matching EXP-017's
  +1.47 % and +2.26 % with the new fit rule.
- **Side measurement (live, 2026-09-28):** one fetch of the 99 live names + SPY over 1,097 calendar days through
  `market_source_from_settings` (SIP default): **8 pages, 75,200 bars, 8.3 MB, 19.1 s**, 100 of 100 names, no
  refusal. It returned **752** bars per name, not 756: the calendar helper's window ending on a non-session
  day falls a few bars short, so production should ask with a small buffer.

## 7. Conclusions

- **GARCH(1,1) on ~3 years of history is the production candidate for item 92's probabilities.** It is the
  first model to clear the pre-registered bar: 2.7 % better than quoting past outcome shares, with the whole
  interval above zero, reliable fits, near-diagonal calibration and an edge in every year.
- **The fleet's 203 bars are not enough,** and ten years is no better than three. The model needs its own,
  longer history, which S238 made cheap: 19 seconds and 8 pages a run.
- **What this does not say:** the skill is modest (about 2.7 % of the Brier score). It says the probabilities
  are honest enough to record and track, not that sizing on them earns money. That is the live ledger's job
  next, and then an exit experiment on these probabilities (DL-240 step 5), before any trading behaviour
  changes.
- **Out-of-sample caveats:** the model is re-fitted monthly on data up to each decision, so there is no
  look-ahead; but the universe is today's 98 names (survivorship), the same test bed as EXP-011, EXP-016 and
  EXP-017.

## 8. Recommended code changes, and how to implement them

Nothing here changes what the fleet buys or sells. It builds the ledger that measures the probabilities
live. Sizing or exits on them come later, each with its own experiment and the operator's decision.

1. **Chore first: the barrier test bed into `scripts/`** (`scripts/barrier_testbed.py`, as EXP-016 §8 and
   EXP-017 §8 recommend): the decision builder, outcome rule, climatology and the date-resampled scorer, with
   GARCH-FHS as a reusable function. Unit tests on a synthetic fixture; the EXP-011 reproduction as the
   planner's live check; full `make ci` and gate; PATCH; no deploy. *Done 2026-09-28 (`v0.117.04`), with one
   change: GARCH lives in the forecaster (S239), not the test bed, which takes any model function.*
2. **Sprint A — the forecaster states barrier probabilities (shadow, advisory).** For a cloud session, with a
   law cycle:
   - The forecaster requests its **own** history for this model: **760 sessions** by default (a new
     `tunable`, PARAM row, bounded), a separate provider request of ~8 pages. It must **not** change
     `orchestration/history_window.py` or the scanner / analyst window: those are decision paths
     (DL-238 D7), and moving them would change what the fleet trades.
   - A model `barrier_garch`: GARCH(1,1), Student-t, filtered historical simulation, 1,000 paths × 10 sessions,
     boundary fits accepted and persistence capped at 0.999, exactly as this experiment. **One deliberate
     difference to name in the spec:** production fits per run rather than per month (no state to keep);
     the ledger measures whether that matters.
   - For each **approved buy**, with the PM's own stop and target, it records P(stop first), P(target first),
     P(neither), the horizon, the barriers, the model id and version and the fitted parameters, as a new
     append-only graph record. `arch` joins the forecaster's optional dependencies (as `lightgbm` did);
     check the image size. A new label is a vocabulary change, so the deploy is a **full `up`**.
3. **Sprint B — settlement and scorecard.** Ten sessions after each claim, the realised outcome is recorded
   by the same low-before-high rule, as its own append-only record; a scorecard (Brier, skill against
   climatology, calibration buckets, running and per month) reaches the dashboard. Promotion only through the
   ADR-0010 registry; advisory until then.
4. **Then an exit experiment on these probabilities** (DL-240 step 5), pre-registered on the replay cache:
   take-profit, time exit and a probability-triggered exit against stops only. Only a result that passes
   becomes a behaviour change, and position sizing on probabilities stays the operator's capital-risk
   decision, after item 91.

## Appendix P — Pre-registration (frozen)

Sections 1–5 above, as committed at `0e3f6b03` before any path was simulated. They were not changed after the
run.

## Appendix R — Run record

**Run 2026-09-28**, planner, main checkout. Simulation 692 s on 4 workers; reproduction check passed.

```text
cases 47485; realised [0.285 0.48  0.235]
fits 203: {'accepted': 8956, 'capped': 1169, 'fallback': 45, 'failed_first': 0}
fits 756: {'accepted': 8552, 'capped': 395, 'fallback': 35, 'failed_first': 0}
fits full: {'accepted': 9478, 'capped': 633, 'fallback': 59, 'failed_first': 0}
wrote C:\Users\yury_\OneDrive\trading-agents-data\exp018\exp018_sim.pkl 692s
```

**Scored output** (`exp018_score.py`; its first draft crashed printing a date range, with numpy refusing a
minimum over strings, and was fixed without touching any number):

```text
cases 47485; realised [0.285 0.48  0.235]
fits  203: {'accepted': 8956, 'capped': 1169, 'fallback': 45, 'failed_first': 0}  failed 0.44 %  capped 11.49 %
fits  756: {'accepted': 8552, 'capped': 395, 'fallback': 35, 'failed_first': 0}  failed 0.39 %  capped 4.40 %
fits full: {'accepted': 9478, 'capped': 633, 'fallback': 59, 'failed_first': 0}  failed 0.58 %  capped 6.22 %

== PRIMARY (>= 756 prior moves, every depth present): 37587 cases on 385 dates, 2019-01-07 .. 2026-08-27; realised [0.287 0.477 0.236]
   G_203        Brier 0.6254  skill +1.57 %  [+0.83, +2.31]  mean declared [0.291 0.484 0.225]
   G_756        Brier 0.6183  skill +2.67 %  [+1.88, +3.48]  mean declared [0.283 0.468 0.249]
   G_full       Brier 0.6204  skill +2.35 %  [+1.55, +3.19]  mean declared [0.27  0.456 0.274]
   climatology  Brier 0.6353  skill +0.00 %  [+0.00, +0.00]  mean declared [0.276 0.482 0.242]

Pre-registered tests:
   H1(203): skill +1.57 % (>= 2 %: False), lower bound +0.83 % (> 0: True), failed fits 0.44 % (<= 2 %: True)  ->  fail
   H1(756): skill +2.67 % (>= 2 %: True), lower bound +1.88 % (> 0: True), failed fits 0.39 % (<= 2 %: True)  ->  PASS
   H2  G_756 - G_203: -0.0070  [-0.0109, -0.0029]  PASS
   --  G_full - G_756: +0.0021  [+0.0002, +0.0038]

Calibration on the primary set - declared bucket -> realised share (>= 100 cases):
   G_203   P(stop first)    0.08->0.19 (419)  0.16->0.24 (5150)  0.25->0.27 (14892)  0.34->0.30 (13145)  0.43->0.37 (3683)  0.52->0.49 (293)
   G_203   P(target first)  0.16->0.26 (182)  0.27->0.29 (865)  0.36->0.36 (5290)  0.45->0.45 (14567)  0.54->0.53 (13024)  0.63->0.64 (3260)  0.73->0.64 (296)
   G_756   P(stop first)    0.07->0.18 (205)  0.17->0.21 (4674)  0.25->0.27 (17644)  0.34->0.33 (12805)  0.43->0.39 (2173)
   G_756   P(target first)  0.16->0.24 (482)  0.26->0.28 (2416)  0.36->0.37 (7449)  0.45->0.45 (12066)  0.55->0.55 (10377)  0.64->0.65 (3896)  0.73->0.69 (727)
   G_full  P(stop first)    0.06->0.18 (135)  0.17->0.23 (4743)  0.25->0.28 (21283)  0.34->0.33 (10434)  0.43->0.37 (926)
   G_full  P(target first)  0.16->0.24 (756)  0.26->0.30 (3384)  0.35->0.38 (8140)  0.45->0.46 (11383)  0.54->0.56 (9090)  0.64->0.66 (3795)  0.73->0.70 (882)

Brier by year (primary):
   year      n    G_203    G_756   G_full  climatology
   2019   4850  0.6217  0.6125  0.6134  0.6367
   2020   4947  0.6119  0.6111  0.6099  0.6289
   2021   4858  0.6493  0.6272  0.6270  0.6534
   2022   4900  0.6223  0.6130  0.6196  0.6275
   2023   4900  0.6450  0.6338  0.6350  0.6502
   2024   4998  0.6232  0.6220  0.6289  0.6384
   2025   4900  0.6195  0.6153  0.6182  0.6287
   2026   3234  0.6024  0.6084  0.6064  0.6102

Brier by regime (primary):
     risk_on n= 7811  G_203=0.6435  G_756=0.6366  G_full=0.6378  climatology=0.6547
     neutral n=15631  G_203=0.6420  G_756=0.6338  G_full=0.6366  climatology=0.6478
    risk_off n= 7319  G_203=0.6253  G_756=0.6140  G_full=0.6170  climatology=0.6281
    high_vol n= 5563  G_203=0.5844  G_756=0.5847  G_full=0.5871  climatology=0.6078
     extreme n= 1263  G_203=0.4876  G_756=0.4865  G_full=0.4787  climatology=0.5233

== SECONDARY (all 2018-2026, for comparison with EXP-017): 42538 cases on 435 dates, 2018-01-08 .. 2026-08-27; realised [0.292 0.477 0.231]
   G_203        Brier 0.6266  skill +1.49 %  [+0.81, +2.26]  mean declared [0.286 0.484 0.23 ]
   G_full       Brier 0.6214  skill +2.30 %  [+1.53, +3.07]  mean declared [0.266 0.458 0.276]
   climatology  Brier 0.6360  skill +0.00 %  [+0.00, +0.00]  mean declared [0.27  0.484 0.246]
```

**Side measurement** (`exp018_fetch.py`, main checkout with `.env`):

```text
feed=sip window=1097 calendar days ending 2026-09-28; names 100/100
pages 8, bars 75200, bytes 8,268,326, total 19.1s, per page [2.61, 2.27, 2.29, 2.26, 2.26, 2.29, 2.27, 1.83]
bars per name: min 752 median 752 max 752
the 203-bar window today for comparison: 297 calendar days
```

### Reproducing

From the repo root: `PYTHONPATH=. uv run --with arch --with scipy python exp018_sim.py <dir> 4` (~12 minutes),
then `uv run python exp018_score.py <dir>`; the side measurement with
`PYTHONPATH=. uv run --env-file .env python exp018_fetch.py`. Seeds are fixed.

## Appendix S — Scripts

### `exp018_sim.py`

```python
"""EXP-018 step 1 - GARCH(1,1)-t filtered historical simulation, boundary fits accepted, at 203 / 756 / full.

PYTHONPATH=<repo> uv run --with arch --with scipy python exp018_sim.py <out_dir> [workers]
EXP-017's G with one change: a converged fit with omega > 0, alpha, beta >= 0 and alpha + beta <= 1 is accepted;
if alpha + beta > 0.999 both are scaled in proportion to sum to 0.999 (counted as capped). Paths are seeded
default_rng([20260928, stock_index]).
"""
import pickle
import sys
import time
import warnings
from multiprocessing import Pool
from pathlib import Path

import numpy as np

H, LOOKBACK, ATR_N, N_PATHS, STEP, RECENT = 10, 120, 14, 1000, 5, 250
DEPTHS = {"203": 203, "756": 756, "full": None}
PERSISTENCE_CAP = 0.999
OUT = Path(sys.argv[1])


def label(v):
    return 4 if v >= 35 else 3 if v >= 25 else 2 if v >= 20 else 0 if v <= 15 else 1


def barrier_probs(prev, lh, ll, stop, target):
    hit_s = prev * ll <= 1 - stop
    hit_t = prev * lh >= 1 + target
    fs = np.where(hit_s.any(1), hit_s.argmax(1), H)
    ft = np.where(hit_t.any(1), hit_t.argmax(1), H)
    p_stop = float(np.mean((fs < H) & (fs <= ft)))
    p_target = float(np.mean((ft < H) & (ft < fs)))
    return (p_stop, p_target, 1 - p_stop - p_target)


def garch_fit(r):
    """Return (params, status) with status in accepted | capped | failed."""
    from arch import arch_model

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = arch_model(r, mean="Constant", vol="GARCH", p=1, q=1, dist="t").fit(disp="off")
    except Exception:  # noqa: BLE001 - counted as a failed fit
        return None, "failed"
    p = res.params
    mu, omega, alpha, beta = float(p["mu"]), float(p["omega"]), float(p["alpha[1]"]), float(p["beta[1]"])
    if res.convergence_flag != 0 or omega <= 0 or alpha < 0 or beta < 0 or alpha + beta > 1 + 1e-9:
        return None, "failed"
    if alpha + beta > PERSISTENCE_CAP:
        scale = PERSISTENCE_CAP / (alpha + beta)
        return (mu, omega, alpha * scale, beta * scale), "capped"
    return (mu, omega, alpha, beta), "accepted"


def garch_path_probs(rng, params, r, lh_pct, ll_pct, lo, t, stop, target):
    from scipy.signal import lfilter

    mu, omega, alpha, beta = params
    seg = r[lo:t]
    s2_0 = seg.var()
    s2 = np.concatenate([[s2_0], lfilter([1.0], [1.0, -beta], omega + alpha * (seg - mu) ** 2, zi=[beta * s2_0])[0]])
    sig = np.sqrt(s2[:-1])
    z = (seg - mu) / sig
    uh, ul = lh_pct[lo:t] / sig, ll_pct[lo:t] / sig
    s2_next = np.full(N_PATHS, s2[-1])
    level = np.ones(N_PATHS)
    prev_all, hh, llw = (np.empty((N_PATHS, H)) for _ in range(3))
    for k in range(H):
        j = rng.integers(0, len(seg), N_PATHS)
        s = np.sqrt(s2_next)
        rr = mu + s * z[j]
        prev_all[:, k] = level
        hh[:, k] = np.exp(np.maximum(s * uh[j], rr) / 100)
        llw[:, k] = np.exp(np.minimum(s * ul[j], rr) / 100)
        level = level * np.exp(rr / 100)
        s2_next = omega + alpha * (rr - mu) ** 2 + beta * s2_next
    return barrier_probs(prev_all, hh, llw, stop, target)


def run_name(job):
    name_index, sym, rows, decision_dates, vixlab = job
    rng = np.random.default_rng([20260928, name_index])
    dates = [x[0] for x in rows]
    hi, lo, cl = (np.array([x[k] for x in rows]) for k in (2, 3, 4))
    rh, rl, rc = hi[1:] / cl[:-1], lo[1:] / cl[:-1], cl[1:] / cl[:-1]
    r = 100 * np.log(rc)
    lh_pct, ll_pct = 100 * np.log(rh), 100 * np.log(rl)
    tr = np.maximum.reduce([hi[1:] - lo[1:], abs(hi[1:] - cl[:-1]), abs(lo[1:] - cl[:-1])])
    out = []
    fits = {d: {} for d in DEPTHS}
    last = {d: None for d in DEPTHS}
    counts = {d: {"accepted": 0, "capped": 0, "fallback": 0, "failed_first": 0} for d in DEPTHS}
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
        rec = {"sym": sym, "day": day, "outcome": outcome, "regime": vixlab[day], "moves": t}
        if day >= "2018":
            month = day[:7]
            for d, depth in DEPTHS.items():
                lo_i = 0 if depth is None else t - depth
                if lo_i < 0:
                    rec[f"G_{d}"] = None
                    continue
                if month not in fits[d]:
                    params, status = garch_fit(r[lo_i:t])
                    if status in ("accepted", "capped"):
                        counts[d][status] += 1
                        last[d] = params
                    elif last[d] is not None:
                        counts[d]["fallback"] += 1
                    else:
                        counts[d]["failed_first"] += 1
                    fits[d][month] = last[d]
                params = fits[d][month]
                rec[f"G_{d}"] = garch_path_probs(rng, params, r, lh_pct, ll_pct, lo_i, t, stop, target) if params else None
        out.append(rec)
    return sym, out, counts


def main():
    from scripts.replay_dataset import load

    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    vix, bars = load()
    vixlab = {k: label(v) for k, v in vix.items()}
    calendar = sorted({b[0] for rows in bars.values() for b in rows})
    decision_dates = set(calendar[calendar.index("2017-01-03")::STEP])
    jobs = [(i, sym, rows, decision_dates, vixlab) for i, (sym, rows) in enumerate(sorted(bars.items()))]
    t0 = time.time()
    cases = []
    counts = {d: {"accepted": 0, "capped": 0, "fallback": 0, "failed_first": 0} for d in DEPTHS}
    with Pool(workers) as pool:
        for n, (sym, out, fc) in enumerate(pool.imap_unordered(run_name, jobs), 1):
            cases.extend(out)
            for d in DEPTHS:
                for k in counts[d]:
                    counts[d][k] += fc[d][k]
            print(f"  {n}/{len(jobs)} {sym} {len(out)} cases, {time.time() - t0:.0f}s", flush=True)
    cases.sort(key=lambda c: (c["sym"], c["day"]))
    Y = np.eye(3)[[c["outcome"] for c in cases]]
    print(f"cases {len(cases)}; realised {Y.mean(0).round(3)}")
    for d in DEPTHS:
        print(f"fits {d}: {counts[d]}")
    pickle.dump({"cases": cases, "fit_counts": counts}, open(OUT / "exp018_sim.pkl", "wb"))
    print("wrote", OUT / "exp018_sim.pkl", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
```

### `exp018_score.py`

```python
"""EXP-018 step 2 - score exactly as pre-registered.

uv run python exp018_score.py <out_dir>
"""
import pickle
import sys
from pathlib import Path

import numpy as np

OUT = Path(sys.argv[1])
d = pickle.load(open(OUT / "exp018_sim.pkl", "rb"))
cases = d["cases"]
DEPTHS = ("203", "756", "full")
Y_all = np.eye(3)[[c["outcome"] for c in cases]]
years_all = np.array([int(c["day"][:4]) for c in cases])
clim_all = np.zeros_like(Y_all)
for i, y in enumerate(years_all):
    prior = years_all < y
    clim_all[i] = Y_all[prior].mean(0) if prior.sum() > 500 else Y_all[:500].mean(0)

print(f"cases {len(cases)}; realised {Y_all.mean(0).round(3)}")
fit_fail = {}
for dp in DEPTHS:
    fc = d["fit_counts"][dp]
    total = sum(fc.values())
    fail = fc["fallback"] + fc["failed_first"]
    fit_fail[dp] = fail / total
    print(f"fits {dp:>4}: {fc}  failed {100 * fail / total:.2f} %  capped {100 * fc['capped'] / total:.2f} %")


def run(label, idx, depths):
    Y = Y_all[idx]
    F = {f"G_{dp}": np.array([cases[i][f"G_{dp}"] for i in idx]) for dp in depths}
    F["climatology"] = clim_all[idx]
    loss = {m: ((P - Y) ** 2).sum(1) for m, P in F.items()}
    dates = np.array([cases[i]["day"] for i in idx])
    rng = np.random.default_rng(20260929)
    udates = np.unique(dates)
    by_date = {u: np.where(dates == u)[0] for u in udates}
    draws = [np.concatenate([by_date[u] for u in rng.choice(udates, len(udates))]) for _ in range(1000)]
    bc = loss["climatology"].mean()
    print(f"\n== {label}: {len(idx)} cases on {len(udates)} dates, {min(dates)} .. {max(dates)}; realised {Y.mean(0).round(3)}")
    res = {}
    for m in F:
        b = loss[m].mean()
        sk = [1 - loss[m][s].mean() / loss["climatology"][s].mean() for s in draws]
        lo, hi = np.percentile(sk, 2.5), np.percentile(sk, 97.5)
        res[m] = (1 - b / bc, lo)
        print(f"   {m:<12} Brier {b:.4f}  skill {100 * (1 - b / bc):+.2f} %  [{100 * lo:+.2f}, {100 * hi:+.2f}]  mean declared {F[m].mean(0).round(3)}")
    return F, Y, loss, draws, res, dates, idx


prim = [i for i, c in enumerate(cases) if years_all[i] >= 2018 and all(c.get(f"G_{dp}") is not None for dp in DEPTHS)]
F, Y, loss, draws, res, dates, idx = run("PRIMARY (>= 756 prior moves, every depth present)", prim, DEPTHS)

print("\nPre-registered tests:")
for dp in ("203", "756"):
    sk, lo = res[f"G_{dp}"]
    ok = sk >= 0.02 and lo > 0 and fit_fail[dp] <= 0.02
    print(f"   H1({dp}): skill {100 * sk:+.2f} % (>= 2 %: {sk >= 0.02}), lower bound {100 * lo:+.2f} % (> 0: {lo > 0}), "
          f"failed fits {100 * fit_fail[dp]:.2f} % (<= 2 %: {fit_fail[dp] <= 0.02})  ->  {'PASS' if ok else 'fail'}")
dif = loss["G_756"].mean() - loss["G_203"].mean()
boots = [loss["G_756"][s].mean() - loss["G_203"][s].mean() for s in draws]
lo, hi = np.percentile(boots, 2.5), np.percentile(boots, 97.5)
print(f"   H2  G_756 - G_203: {dif:+.4f}  [{lo:+.4f}, {hi:+.4f}]  {'PASS' if hi < 0 else 'fail'}")
dif = loss["G_full"].mean() - loss["G_756"].mean()
boots = [loss["G_full"][s].mean() - loss["G_756"][s].mean() for s in draws]
print(f"   --  G_full - G_756: {dif:+.4f}  [{np.percentile(boots, 2.5):+.4f}, {np.percentile(boots, 97.5):+.4f}]")

print("\nCalibration on the primary set - declared bucket -> realised share (>= 100 cases):")
for m in ("G_203", "G_756", "G_full"):
    for k, name in ((0, "P(stop first)"), (1, "P(target first)")):
        p, y = F[m][:, k], Y[:, k]
        cells = []
        for lo_ in np.arange(0, 1, 0.1):
            sel = (p >= lo_) & (p < lo_ + 0.1 + (1e-9 if lo_ >= 0.9 else 0))
            if sel.sum() >= 100:
                cells.append(f"{p[sel].mean():.2f}->{y[sel].mean():.2f} ({sel.sum()})")
        print(f"   {m:<7} {name:<16} " + "  ".join(cells))

years = np.array([int(x[:4]) for x in dates])
print("\nBrier by year (primary):")
print("   year      n    G_203    G_756   G_full  climatology")
for y in sorted(set(years)):
    s = years == y
    print(f"   {y}  {s.sum():5d}  " + "  ".join(f"{loss[m][s].mean():.4f}" for m in ("G_203", "G_756", "G_full", "climatology")))
regs = np.array([cases[i]["regime"] for i in idx])
names = ("risk_on", "neutral", "risk_off", "high_vol", "extreme")
print("\nBrier by regime (primary):")
for r in range(5):
    s = regs == r
    if s.sum() >= 200:
        print(f"   {names[r]:>9} n={s.sum():5d}  " + "  ".join(f"{m}={loss[m][s].mean():.4f}" for m in ("G_203", "G_756", "G_full", "climatology")))

sec = [i for i, c in enumerate(cases) if years_all[i] >= 2018 and c.get("G_203") is not None and c.get("G_full") is not None]
run("SECONDARY (all 2018-2026, for comparison with EXP-017)", sec, ("203", "full"))
```

### `exp018_fetch.py`

```python
"""EXP-018 side measurement - what a 756-session SIP fetch costs through the fleet's own provider code.

PYTHONPATH=<repo> uv run --env-file <repo>/.env python exp018_fetch.py
Read-only: one paginated bars fetch for the live universe + SPY. No graph write, no order.
"""
import os
import time
from datetime import UTC, datetime, timedelta

os.environ.pop("PROVIDER_ALPACA_DATA_FEED", None)
from agents.provider.composite import market_source_from_settings  # noqa: E402
from agents.provider.settings import ProviderSettings  # noqa: E402
from contracts.common import Window  # noqa: E402
from orchestration.history_window import calendar_days_for_sessions  # noqa: E402

universe = tuple(s.strip().upper() for s in open("scripts/universe_sp100.txt") if s.strip() and not s.startswith("#"))
today = datetime.now(UTC).date()
days = calendar_days_for_sessions(756, today)
settings = ProviderSettings()
source = market_source_from_settings(settings)
alpaca = source._price_source
pages, sizes = [], []
orig = alpaca._download_page


def recording(query):
    t0 = time.time()
    body = orig(query)
    pages.append(time.time() - t0)
    sizes.append(len(body))
    return body


alpaca._download_page = recording
t0 = time.time()
bars = source.fetch_ohlcv((*universe, "SPY"), Window(start=today - timedelta(days=days), end=today))
total = time.time() - t0
per = {}
for b in bars:
    per[b.ticker] = per.get(b.ticker, 0) + 1
print(f"feed={settings.alpaca_data_feed} window={days} calendar days ending {today}; names {len(per)}/{len(universe) + 1}")
print(f"pages {len(pages)}, bars {len(bars)}, bytes {sum(sizes):,}, total {total:.1f}s, per page {[round(x, 2) for x in pages]}")
print(f"bars per name: min {min(per.values())} median {sorted(per.values())[len(per) // 2]} max {max(per.values())}")
print("the 203-bar window today for comparison:", calendar_days_for_sessions(203, today), "calendar days")
```
