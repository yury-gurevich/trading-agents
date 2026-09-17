# EXP-011 - Is the regime a Markov chain, and do simulated stop/target probabilities come true?

**Date:** 2026-09-17 · **Status:** complete. The raw VIX regime label is **not** Markov, but a sticky one is.
Regime-weighted barrier simulation adds about **1 %** skill over base rates. S211's "median target is reached
half the time" came true (**50.2 %**). S211's target/stop ratio **does not predict returns**, and a 0.80
floor would historically have rejected a median **49 %** of names per night. Operator ruled the gate
**disclosure-only** · **Feeds:** [ADR-0027](../../decisions/0027-reward-risk-compares-measured-upside-against-measured-downside.md)
*Correction 2*, [S211](../../sprints/sprint-211-reward-risk-compares-two-measured-quantities.md),
[ADR-0028](../../decisions/0028-the-regime-reads-vix-from-fmp-and-says-when-it-cannot.md) /
[S213](../../sprints/sprint-213-a-regime-says-what-vix-it-measured.md) (label design), work-queue items **64**
and **70**, and a proposed forward-simulation track

## Purpose

The operator's direction (2026-09-17): *derive the quantity, then compare it with probability.* The candidate
design is a pre-trade forward simulation: a bootstrap Monte Carlo over historical paths, weighted by a Markov
chain of regime transitions, emitting P(stop first), P(target first) and P(neither) per trade. A running
record of declared against realised probabilities would then check it.

Nothing like it exists in this repo. Before any ADR, three questions:

1. **Is the regime label actually a Markov chain?** If not, a transition matrix mis-states its own forecasts.
2. **Do simulated barrier probabilities come true** for S211's real stop and target, and does regime
   weighting improve them?
3. **What do S211's own quantities predict?** The median-target claim, and the target/stop ratio the new
   gate filters on.

## Process

**Data** (read-only, free):

- **VIX:** Cboe's public daily history (ADR-0028's validation oracle), **9,274 sessions,
  1990-01-02 → 2026-09-16**. Labelled with the provider's live thresholds (`agents/provider/domain/regime.py`):
  risk_on ≤ 15, neutral, risk_off ≥ 20, high_vol ≥ 25, extreme ≥ 35.
- **Prices:** Alpaca daily bars, split- and dividend-adjusted, **SIP** (consolidated tape) feed, for the
  **98 names** in `sched-2026-09-16`'s snapshot. **263,005 bars**, 2016-01-04 → 2026-09-16 (LIN from 2018-10).
  Production reads the IEX feed. Part D shows the ratio agrees across feeds on the same night.

**S211's barriers, recomputed exactly:**

- **stop:** clamp(2 × mean true range over 14 bars ÷ close, 2.5 %, 8 %)
- **target:** median over the 120 prior settled windows of the best close-to-high rise within 10 sessions

**Decisions and outcomes:** a decision at the close of every 5th session from 2017-01-03, per name:
**47,485 cases** (486 dates × 98 names). Over the next 10 sessions the low is checked before the high, so a day
touching both counts as a stop. Exit at stop, target, or the 10th close.

**Part A - the regime chain (1990-2026):**

- **A1:** one-session transition matrix, overall and by decade.
- **A2:** G-test of first-order against second-order (does yesterday add information beyond today?).
- **A3:** spell lengths and exit hazard by age (a Markov chain implies geometric spells and a flat hazard).
- **A4:** out of sample (fit 1990-2014, test 2015-2026). Forecast the state 10 sessions ahead three ways and
  score with Brier: climatology, the Markov chain's P^10, and 10-step frequencies counted directly (no Markov
  assumption).
- **A5:** repeat for a **sticky** label that switches only after k consecutive closes in the new band.

**Part B - barrier simulation, 1,000 paths per case:** daily moves (high, low, close relative to the prior
close) resampled from the name's own history, all dated at or before the decision:

| Model | Samples from |
| --- | --- |
| `recent250` | the last 250 sessions |
| `all_history` | all prior sessions |
| `regime_today` | prior sessions with today's regime label |
| `regime_markov` | each simulated day's regime drawn from the 1990-2014 Markov chain, then a prior session with that label |
| `climatology` (baseline) | no simulation: realised outcome shares of all prior years |

Scored 2018-2026 with a 3-outcome Brier score and calibration buckets. Confidence intervals resample **whole
decision dates**, because names on one date move together.

**Part C - S211's quantities, no simulation:**

- the touch rate of the median target;
- outcome shares and **realised trade return** by target/stop ratio bucket, with the full payoff (−stop,
  +target, or the 10th-close return);
- 2017-2021 and 2022-2026 separately.

**Part D - the ratio across feeds and time:** same-night SIP against the production IEX snapshot, and the
nightly share below 0.80 by year.

## Delivery

- This record, with the scripts and full output in the appendices. Everything is read-only, needs `.env`
  only for the loader, and cost nothing. No LLM was used.

### Result A - the raw regime label is not Markov; a sticky one is

**A1 - one-session transition matrix, 1990-2026:**

| from \ to | risk_on | neutral | risk_off | high_vol | extreme | days |
| --- | --- | --- | --- | --- | --- | --- |
| risk_on | **0.926** | 0.074 | 0 | 0 | 0 | 2,972 |
| neutral | 0.077 | **0.834** | 0.086 | 0.002 | 0 | 2,868 |
| risk_off | 0 | 0.139 | **0.772** | 0.087 | 0.001 | 1,829 |
| high_vol | 0 | 0 | 0.134 | **0.829** | 0.037 | 1,251 |
| extreme | 0 | 0 | 0 | 0.139 | **0.861** | 353 |

Persistence isn't stable: risk_off P(stay) was 0.81-0.82 in the 1990s and 2000s, **0.67** in the 2010s and
0.71 in the 2020s.

**A2/A3 - memory the chain doesn't have:**

- **Yesterday matters** (G = 705, p ≈ 10⁻¹³⁰). A neutral day that was risk_on yesterday stays neutral with
  probability **0.66**, against **0.86** if it was neutral yesterday.
- **The exit hazard falls with age**, where Markov says it is flat. risk_on: **33.5 %** on day 1, 5.2 % at
  6-20 days, 2.1 % after 60.
- **Spell shape is wrong** even though the mean matches by construction:
  - risk_on spells last beyond 10 days **26 %** of the time, against the chain's 46 %;
  - they last beyond 40 days **8.6 %** of the time, against 4.5 %.
  - The label flickers at the thresholds, and calm spells run very long.

**A4 - out of sample, the state 10 sessions ahead (2,966 test days):**

| Forecast | Brier (lower is better) |
| --- | --- |
| climatology | 0.723 |
| Markov P^10 | 0.572 |
| direct 10-step counts | **0.547** |

- The chain beats ignoring today by a wide margin.
- But the direct count beats the chain, and the chain is **miscalibrated**: when it said 0.21 the outcome
  happened 14 % of the time; when it said 0.60, **76 %**. Compounding one-day flicker overstates how fast
  regimes change.

**A5 - a sticky label:**

| Label | Switches / year | 2nd-order G (p) | Brier Markov | Brier direct | Markov − direct |
| --- | --- | --- | --- | --- | --- |
| raw | 37.4 | 705 (10⁻¹³⁰) | 0.572 | 0.547 | +0.025 |
| sticky k=2 | 18.3 | 124 (10⁻¹⁰) | 0.512 | 0.520 | −0.008 |
| **sticky k=3** | **12.1** | **52 (p = 0.30)** | 0.489 | 0.494 | **−0.005** |
| sticky k=5 | 7.1 | 18 (p = 1.0) | 0.434 | 0.433 | +0.001 |

With **three consecutive closes** required to switch, the second-order test no longer rejects, and the chain
forecasts as well as the direct count. Brier scores aren't comparable *across* rows (stickier labels are
easier to forecast); the last column is. Some duration dependence remains (risk_on hazard 4.2 % at 6-20 days
against 2.0 % at 21-60).

### Result B - simulated barrier probabilities add about 1 % over base rates

Realised 2017-2026: stop first **28.5 %**, target first **48.0 %**, neither **23.5 %**.

| Model (2018-2026) | Brier | vs climatology (95 % CI) |
| --- | --- | --- |
| climatology | 0.6360 | - |
| `all_history` | **0.6300** | −0.0060 [−0.0111, −0.0003] |
| `regime_markov` | 0.6306 | −0.0055 [−0.0111, +0.0003] |
| `recent250` | 0.6394 | +0.0034 [−0.0023, +0.0093] |
| `regime_today` | 0.6445 | +0.0084 [+0.0005, +0.0164] |

- **P(target first) is well calibrated:** `regime_markov` said 0.45 → got 0.46, said 0.54 → 0.54,
  said 0.64 → 0.63.
- **P(stop first) is not.** The simulation spreads it far wider than reality:
  - `recent250` said 0.07 → got 0.21, and said 0.53 → got 0.41;
  - `regime_markov` said 0.53 → got 0.28.
  - Realised stop rates stay within 0.19-0.41 while the declared values range from 0.07 to 0.63. The stop is already sized to
    ATR, so the simulation's variation is mostly noise.
- **Regime conditioning points the wrong way in high volatility:**

  | Regime at decision | Cases | Realised stop / target | `regime_markov` said | `all_history` said |
  | --- | --- | --- | --- | --- |
  | risk_on | 10,151 | 0.305 / 0.435 | 0.226 / 0.489 | 0.337 / 0.473 |
  | neutral | 17,018 | 0.309 / 0.449 | 0.266 / 0.478 | 0.296 / 0.477 |
  | risk_off | 8,218 | 0.263 / 0.504 | 0.345 / 0.444 | 0.265 / 0.459 |
  | high_vol | 5,877 (60 dates) | 0.269 / **0.542** | 0.354 / 0.482 | 0.210 / 0.458 |
  | extreme | 1,274 (**13 dates**) | 0.246 / **0.715** | 0.355 / 0.509 | 0.134 / 0.495 |

  After a VIX spike, targets were hit *more* often (rebounds) and stops no more often. The regime-weighted
  simulation predicted more stops. The extreme row is 13 dates in two episodes (2020, 2025-04), so it is
  suggestive only.
- **Regime base rates don't transfer either:** prior years' outcome shares per regime scored **worse** than
  plain climatology (+0.0063 [+0.0034, +0.0093]).

### Result C - S211's quantities

**C1 - the median target claim holds.** Over 47,485 out-of-sample decisions, the price touched S211's target
within 10 sessions **50.2 %** of the time. By construction it was reached in 50 % of *prior* windows. The
estimator is honest.

**C2 - the ratio does not predict returns.** Mean trade return with the full payoff; 95 % CIs resample
whole dates.

| Target/stop ratio | Cases | 2017-2026 | 2017-2021 | 2022-2026 |
| --- | --- | --- | --- | --- |
| < 0.6 | 10,308 | +0.31 % | +0.33 % | +0.30 % |
| 0.6-0.7 | 6,382 | +0.39 % | +0.50 % | +0.29 % |
| 0.7-0.8 | 6,987 | +0.36 % | +0.49 % | +0.24 % |
| 0.8-0.9 | 6,484 | +0.44 % | +0.60 % | +0.26 % |
| 0.9-1.0 | 5,496 | +0.37 % | +0.49 % | +0.23 % |
| 1.0-1.2 | 7,013 | +0.34 % | +0.44 % | +0.21 % |
| ≥ 1.2 | 4,815 | +0.36 % | +0.55 % | +0.04 % |
| **passed (≥ 0.80) − rejected** | | **+0.03 % [−0.17, +0.23]** | +0.10 % [−0.19, +0.43] | **−0.08 %** [−0.35, +0.17] |

- No bucket stands out, and the sign flips between periods.
- A lower ratio does mean the target is hit first more often (**65 %** below 0.6, against 29 % at 1.2 and
  above). That's mechanical: a nearer barrier is reached sooner, and the payoff balances it out.
- 🪤 **An earlier cut of this table scored "neither" as zero, in stop units.** It appeared to show rejected
  names doing *better*. That was an artefact of the scoring and is recorded here so it isn't rediscovered.

### Result D - the rejection share at 0.80 is a moving target

- **Across feeds, same night (2026-09-16):** SIP median ratio **0.918**, with **21 %** below 0.80. EXP-010's
  production IEX snapshot gave 0.934 and 18 %. The feed isn't the difference.
- **Across time:**

| Year | Median ratio | Nightly share below 0.80: mean (min-max) |
| --- | --- | --- |
| 2017 | 0.81 | 49 % (19-72) |
| 2018 | 0.75 | 57 % (13-99) |
| 2019 | 0.85 | 43 % (11-99) |
| 2020 | 0.84 | 46 % (0-98) |
| 2021 | 0.88 | 39 % (4-95) |
| 2022 | **0.68** | **70 %** (10-96) |
| 2023 | 0.84 | 45 % (11-82) |
| 2024 | 0.86 | 41 % (14-91) |
| 2025 | 0.80 | 51 % (12-99) |
| 2026 | 0.71 | 64 % (22-88) |

Across all 486 nights the share below 0.80 has p10 / median / p90 of **18 % / 49 % / 89 %**. **47 %** of
nights would reject more than half the book. EXP-010's three nights (16-18 %) sit at the **10th percentile**.

## Interpretation

1. **The raw daily label is the wrong object for a Markov chain.** It flickers at fixed thresholds: 37
   switches a year, with a 33 % chance of leaving on day one. A chain fitted to it forecasts better than
   ignoring the regime, but is miscalibrated. **A three-close sticky label behaves as Markov**, and the chain
   then forecasts as well as direct counting. If the regime is ever to drive a number, it should be sticky.
   That is a label-design decision for the provider, not something S213 needs in order to supply VIX.
2. **The forward simulation as designed doesn't earn its keep yet.**
   - Its only well-calibrated output is P(target first), and S211's median target already carries that
     information (50.2 %).
   - Its P(stop first) is over-dispersed.
   - Regime weighting adds nothing over unconditional resampling, and points the wrong way after volatility
     spikes.
   - **Build nothing into the pipeline on this evidence.** The obvious next model is a resampler that keeps
     volatility clustering (block bootstrap or GARCH), but it should come from an explicit need for P(stop)
     in a decision, not from the design's momentum.
3. **"Derive, then compare with probability" already paid off.** The declared-against-realised comparison
   caught three things a one-off backtest would not have:
   - the target estimator is honest;
   - the stop probability is not;
   - the chain overstates regime change.
   That comparison is the durable asset. A declared-vs-realised ledger for quantities the system already
   states (S211's 50 % target touch first) is cheap, and it is the natural first build of this track.
4. **S211's gate filters on a quantity with no measured value, at a rejection rate that swings from 0 % to
   99 % a night.**
   - **Mechanism, reasoned and consistent with 2018 and 2022:** the stop reads 14 sessions, the target reads
     about 6 months. After a volatility spike the stop widens at once, the target lags, and the ratio
     collapses across the whole book.
   - ADR-0027 §3 accepted a moving rejection rate on the premise that low-ratio names are worse buys.
     **Result C2 measures that premise and doesn't find it.**

**Decision taken:** operator, 2026-09-17, *"Disclosure only"*. S211 ships the measured target, its evidence
and the varying ratio in every gate report, with `min_reward_risk_ratio` = **0** so nothing is rejected on
it. An invalid (non-positive) stop still rejects. Recorded in ADR-0027 *Correction 2*. The gate returns only
on evidence that the ratio predicts returns.

**Caveats:**

- **Survivorship.** The 98 names are today's universe, so every one of them survived to 2026. That inflates
  absolute rates (target first 48 %; holding 10 sessions returned +0.68 % on average against about +0.37 % for
  the barrier trade). Comparisons *within* the universe (ratio buckets, model against model) are less exposed,
  but not immune.
- **Overlap.** 10-session outcomes sampled every 5 sessions overlap by half, and names on a date are
  correlated. Date-clustered intervals handle the second, only partly the first.
- **Resampling.** The simulation resamples days independently, which ignores volatility clustering.
- **Entry at the decision close.** The live pipeline enters at the next open (EXP-009's convention).
- **Baseline leak.** The climatology baseline uses prior calendar years' outcomes. The last decisions of a
  year settle in the next year's first two weeks, a negligible leak.
- **Regime episodes are few.** "extreme" is 13 decision dates across two episodes.
- **The regime chain split is fixed at 2015.** Persistence varies by decade (A1), so a rolling refit could
  score differently.

## Reproducing

The loader needs the repo's `.env` (Alpaca keys, Neon spine) and runs from the repo root:
`PYTHONPATH=. uv run python mc_load.py <repo> <scratch>/mc_data.pkl`. Every other script reads only the pickles
and runs outside the project environment: `uv run --no-project --with numpy --with scipy python <script> <args>`.
Order: `mc_regime.py mc_data.pkl` (writes `mc_regime_fit.pkl`), `mc_regime_smooth.py mc_data.pkl`,
`mc_barrier.py mc_data.pkl mc_regime_fit.pkl` (about 5 minutes), `mc_followup.py mc_data.pkl mc_barrier_res.pkl`,
`mc_ratio_payoff.py mc_data.pkl` (writes `mc_ratio_rows.pkl`), `mc_feed_check.py mc_data.pkl`,
`mc_ratio_years.py mc_ratio_rows.pkl`. Seeds are fixed.

## Appendix A - loader (`mc_load.py`)

```python
"""EXP-011 loader: VIX history (Cboe CSV) + daily bars for the live 98-name universe (Alpaca). Read-only."""
import csv
import io
import os
import pickle
import sys
import time

import requests
from dotenv import load_dotenv

REPO = sys.argv[1]
OUT = sys.argv[2]
load_dotenv(os.path.join(REPO, ".env"))
from agents.portfolio_manager.poll import _market_and_regime  # noqa: E402
from kernel.graph_env import build_graph_from_env  # noqa: E402

# 1 - universe = the names in the latest scheduled run's MarketData snapshot
g = build_graph_from_env()
runs = sorted(g.list_nodes("AnalystRun"), key=lambda n: str(n.props.get("created_at")))
for an in reversed(runs):
    market, regime, run_id = _market_and_regime(g, an)
    if market is not None and run_id.startswith("sched-"):
        break
tickers = sorted({b.ticker.upper() for b in market.bars})
print("universe", run_id, len(tickers))

# 2 - VIX daily history, no key
r = requests.get("https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv", timeout=60)
r.raise_for_status()
vix = {}
for row in csv.DictReader(io.StringIO(r.text)):
    m, d, y = row["DATE"].split("/")
    vix[f"{y}-{int(m):02d}-{int(d):02d}"] = float(row["CLOSE"])
print("vix days", len(vix), min(vix), max(vix))

# 3 - daily bars, split-and-dividend adjusted
base = os.environ["ALPACA_ENDPOINT"].rstrip("/")
hdr = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_API_SECRET"]}


def fetch(feed):
    bars, token = {}, None
    while True:
        params = {"symbols": ",".join(tickers), "timeframe": "1Day", "start": "2016-01-01",
                  "end": "2026-09-16T23:59:00Z", "adjustment": "all", "feed": feed, "limit": 10000}
        if token:
            params["page_token"] = token
        resp = requests.get("https://data.alpaca.markets/v2/stocks/bars", headers=hdr, params=params, timeout=60)
        if resp.status_code != 200:
            return None, f"{resp.status_code} {resp.text[:120]}"
        body = resp.json()
        for sym, rows in (body.get("bars") or {}).items():
            bars.setdefault(sym, []).extend((x["t"][:10], x["o"], x["h"], x["l"], x["c"]) for x in rows)
        token = body.get("next_page_token")
        if not token:
            return bars, "ok"
        time.sleep(0.3)


_ = base
# SIP (consolidated tape) for true highs/lows; the free plan refuses only the last 15 minutes
bars, status = fetch("sip")
feed = "sip"
assert bars is not None, status
print("feed", feed, status, "symbols", len(bars), "bars", sum(len(v) for v in bars.values()))
pickle.dump({"run_id": run_id, "tickers": tickers, "vix": vix, "bars": bars, "feed": feed}, open(OUT, "wb"))
```

## Appendix B - part A - regime chain (`mc_regime.py`)

```python
"""EXP-011 part A - is the VIX regime label a Markov chain, and are its probabilities calibrated?

uv run --no-project --with numpy --with scipy python mc_regime.py <mc_data.pkl>
"""
import pickle
import sys

import numpy as np
from scipy.stats import chi2

STATES = ("risk_on", "neutral", "risk_off", "high_vol", "extreme")
H = 10  # sessions: the analyst's horizon


def label(v):  # agents/provider/domain/regime.py thresholds 15 / 20 / 25 / 35
    if v >= 35: return 4
    if v >= 25: return 3
    if v >= 20: return 2
    if v <= 15: return 0
    return 1


d = pickle.load(open(sys.argv[1], "rb"))
dates = sorted(d["vix"])
s = np.array([label(d["vix"][k]) for k in dates])
years = np.array([int(k[:4]) for k in dates])
K = len(STATES)
print(f"VIX sessions {len(s)}  {dates[0]} -> {dates[-1]}")
print("share of sessions:", {STATES[i]: f"{(s == i).mean():.1%}" for i in range(K)})


def matrix(seq):
    c = np.zeros((K, K))
    np.add.at(c, (seq[:-1], seq[1:]), 1)
    return c, c / np.maximum(c.sum(1, keepdims=True), 1)


# A1 - one-step matrix, and its stability across decades
c1, P = matrix(s)
print("\nA1 one-session transition matrix P(next | today), 1990-2026")
print("            " + " ".join(f"{x:>9}" for x in STATES))
for i in range(K):
    print(f"{STATES[i]:>10}  " + " ".join(f"{P[i, j]:9.3f}" for j in range(K)) + f"   n={int(c1[i].sum())}")
print("\n  P(stay) by decade:")
for lo in (1990, 2000, 2010, 2020):
    m = (years >= lo) & (years < lo + 10)
    _, Pd = matrix(s[m])
    print(f"   {lo}s " + " ".join(f"{STATES[i]}={Pd[i, i]:.3f}" for i in range(K)))

# A2 - order test: does yesterday's state add information beyond today's? (likelihood ratio, G-test)
c2 = np.zeros((K, K, K))
np.add.at(c2, (s[:-2], s[1:-1], s[2:]), 1)
G, dof = 0.0, 0
for j in range(K):
    n_prev = 0
    for i in range(K):
        n_ij = c2[i, j].sum()
        if n_ij == 0:
            continue
        n_prev += 1
        exp = n_ij * P[j]
        obs = c2[i, j]
        m = obs > 0
        G += 2 * (obs[m] * np.log(obs[m] / exp[m])).sum()
    dof += max(n_prev - 1, 0) * (int((P[j] > 0).sum()) - 1)
print(f"\nA2 first-order vs second-order: G = {G:.0f}, dof ~ {dof}, p = {chi2.sf(G, dof):.2e}")
for j in (1, 2):
    rows = [(i, c2[i, j]) for i in range(K) if c2[i, j].sum() >= 30]
    print(f"   P(next | today={STATES[j]}, yesterday=...):  " + "  ".join(
        f"{STATES[i]}->stay {r[j] / r.sum():.3f} (n={int(r.sum())})" for i, r in rows))

# A3 - duration: a Markov chain has a constant exit hazard; spells must be geometric
print("\nA3 spell lengths - observed vs what the Markov chain implies (geometric with P(stay))")
runs = []
start = 0
for t in range(1, len(s) + 1):
    if t == len(s) or s[t] != s[start]:
        runs.append((s[start], t - start))
        start = t
for i in range(K):
    L = np.array([n for st, n in runs if st == i])
    p = P[i, i]
    print(f"   {STATES[i]:>9}: spells={len(L):4d}  mean {L.mean():6.1f} (Markov {1 / (1 - p):6.1f})  "
          f"P(>10) {np.mean(L > 10):.3f} (Markov {p ** 10:.3f})  P(>40) {np.mean(L > 40):.3f} (Markov {p ** 40:.3f})")
print("   exit hazard by days already in the state (Markov says flat):")
buckets = [(1, 1), (2, 5), (6, 20), (21, 60), (61, 10 ** 6)]
for i in (0, 1, 2, 3):
    out = []
    for lo, hi in buckets:
        at_risk = exits = 0
        for st, n in runs:
            if st != i:
                continue
            for age in range(lo, min(hi, n) + 1):
                at_risk += 1
                exits += age == n
        out.append(f"{lo}-{hi if hi < 10 ** 6 else '+'}d {exits / at_risk:.3f}" if at_risk >= 50 else f"{lo}-{hi if hi < 10 ** 6 else '+'}d  n/a ")
    print(f"   {STATES[i]:>9}: " + "  ".join(out))

# A4 - out-of-sample: fit on 1990-2014, forecast the state 10 sessions ahead in 2015-2026
train = years < 2015
_, Ptr = matrix(s[train])
PH = np.linalg.matrix_power(Ptr, H)
cH = np.zeros((K, K))
tr_idx = np.where(train)[0]
tr_idx = tr_idx[tr_idx + H < len(s)]
np.add.at(cH, (s[tr_idx], s[tr_idx + H]), 1)
direct = cH / cH.sum(1, keepdims=True)  # 10-step frequencies counted directly: no Markov assumption
clim = np.bincount(s[train], minlength=K) / train.sum()
test = np.where((years >= 2015) & (np.arange(len(s)) + H < len(s)))[0]
Y = np.eye(K)[s[test + H]]


def brier(F):
    return ((F - Y) ** 2).sum(1).mean()


models = {"climatology (ignore today)": np.tile(clim, (len(test), 1)),
          "Markov P^10": PH[s[test]],
          "direct 10-step counts": direct[s[test]]}
print(f"\nA4 forecast the regime 10 sessions ahead - trained 1990-2014, tested 2015-2026 (n={len(test)} days)")
for name, F in models.items():
    print(f"   Brier {brier(F):.4f}  {name}")
print("   calibration - declared probability bucket -> how often it came true (all states pooled):")
for name in ("Markov P^10", "direct 10-step counts"):
    F = models[name].ravel()
    y = Y.ravel()
    line = []
    for lo, hi in ((0, .1), (.1, .3), (.3, .5), (.5, .7), (.7, .9), (.9, 1.01)):
        m = (F >= lo) & (F < hi)
        if m.sum() >= 30:
            line.append(f"[{lo:.1f}-{min(hi, 1):.1f}) said {F[m].mean():.2f} got {y[m].mean():.2f} n={m.sum()}")
    print(f"   {name}:\n      " + "\n      ".join(line))
pickle.dump({"P_train": Ptr, "clim": clim}, open(sys.argv[1].replace("mc_data", "mc_regime_fit"), "wb"))
```

Output (2026-09-17):

```text
VIX sessions 9274  1990-01-02 -> 2026-09-16
share of sessions: {'risk_on': '32.0%', 'neutral': '30.9%', 'risk_off': '19.7%', 'high_vol': '13.5%', 'extreme': '3.8%'}

A1 one-session transition matrix P(next | today), 1990-2026
              risk_on   neutral  risk_off  high_vol   extreme
   risk_on      0.926     0.074     0.000     0.000     0.000   n=2972
   neutral      0.077     0.834     0.086     0.002     0.000   n=2868
  risk_off      0.000     0.139     0.772     0.087     0.001   n=1829
  high_vol      0.000     0.000     0.134     0.829     0.037   n=1251
   extreme      0.000     0.000     0.000     0.139     0.861   n=353

  P(stay) by decade:
   1990s risk_on=0.939 neutral=0.850 risk_off=0.813 high_vol=0.861 extreme=0.829
   2000s risk_on=0.938 neutral=0.823 risk_off=0.818 high_vol=0.846 extreme=0.929
   2010s risk_on=0.923 neutral=0.809 risk_off=0.672 high_vol=0.753 extreme=0.674
   2020s risk_on=0.872 neutral=0.856 risk_off=0.713 high_vol=0.812 extreme=0.780

A2 first-order vs second-order: G = 705, dof ~ 28, p = 1.58e-130
   P(next | today=neutral, yesterday=...):  risk_on->stay 0.659 (n=220)  neutral->stay 0.862 (n=2392)  risk_off->stay 0.722 (n=255)
   P(next | today=risk_off, yesterday=...):  neutral->stay 0.573 (n=248)  risk_off->stay 0.816 (n=1412)  high_vol->stay 0.702 (n=168)

A3 spell lengths - observed vs what the Markov chain implies (geometric with P(stay))
     risk_on: spells= 221  mean   13.4 (Markov   13.4)  P(>10) 0.262 (Markov 0.462)  P(>40) 0.086 (Markov 0.045)
     neutral: spells= 476  mean    6.0 (Markov    6.0)  P(>10) 0.158 (Markov 0.164)  P(>40) 0.013 (Markov 0.001)
    risk_off: spells= 417  mean    4.4 (Markov    4.4)  P(>10) 0.108 (Markov 0.075)  P(>40) 0.000 (Markov 0.000)
    high_vol: spells= 214  mean    5.8 (Markov    5.8)  P(>10) 0.131 (Markov 0.153)  P(>40) 0.019 (Markov 0.001)
     extreme: spells=  49  mean    7.2 (Markov    7.2)  P(>10) 0.102 (Markov 0.224)  P(>40) 0.020 (Markov 0.003)
   exit hazard by days already in the state (Markov says flat):
     risk_on: 1-1d 0.335  2-5d 0.135  6-20d 0.052  21-60d 0.032  61-+d 0.021
     neutral: 1-1d 0.307  2-5d 0.192  6-20d 0.112  21-60d 0.071  61-+d  n/a
    risk_off: 1-1d 0.376  2-5d 0.239  6-20d 0.122  21-60d 0.182  61-+d  n/a
    high_vol: 1-1d 0.350  2-5d 0.201  6-20d 0.101  21-60d 0.072  61-+d  n/a

A4 forecast the regime 10 sessions ahead - trained 1990-2014, tested 2015-2026 (n=2966 days)
   Brier 0.7227  climatology (ignore today)
   Brier 0.5718  Markov P^10
   Brier 0.5467  direct 10-step counts
   calibration - declared probability bucket -> how often it came true (all states pooled):
   Markov P^10:
      [0.0-0.1) said 0.04 got 0.02 n=6180
      [0.1-0.3) said 0.21 got 0.14 n=3775
      [0.3-0.5) said 0.33 got 0.40 n=3818
      [0.5-0.7) said 0.60 got 0.76 n=1057
   direct 10-step counts:
      [0.0-0.1) said 0.01 got 0.02 n=7384
      [0.1-0.3) said 0.17 got 0.21 n=4085
      [0.3-0.5) said 0.32 got 0.31 n=395
      [0.5-0.7) said 0.62 got 0.52 n=1909
      [0.7-0.9) said 0.83 got 0.76 n=1057
```

## Appendix C - part A5 - sticky label (`mc_regime_smooth.py`)

```python
"""EXP-011 part A5 - does a sticky label (switch only after k consecutive closes in the new band) behave as Markov?

uv run --no-project --with numpy --with scipy python mc_regime_smooth.py <mc_data.pkl>
"""
import pickle
import sys

import numpy as np
from scipy.stats import chi2

K, H = 5, 10
d = pickle.load(open(sys.argv[1], "rb"))
dates = sorted(d["vix"])
raw = np.array([4 if v >= 35 else 3 if v >= 25 else 2 if v >= 20 else 0 if v <= 15 else 1
                for v in (d["vix"][k] for k in dates)])
years = np.array([int(k[:4]) for k in dates])


def sticky(seq, k):
    out, cur, streak, cand = [], seq[0], 0, None
    for x in seq:
        if x == cur:
            streak, cand = 0, None
        elif x == cand:
            streak += 1
        else:
            cand, streak = x, 1
        if cand is not None and streak >= k:
            cur, streak, cand = cand, 0, None
        out.append(cur)
    return np.array(out)


def matrix(seq):
    c = np.zeros((K, K))
    np.add.at(c, (seq[:-1], seq[1:]), 1)
    return c, c / np.maximum(c.sum(1, keepdims=True), 1)


print(f"{'label':>10} {'switches/yr':>11} {'G 2nd-order':>12} {'p':>9} {'Brier Markov':>13} {'Brier direct':>13} {'gap':>7}  hazard risk_on 1d / 6-20d / 21-60d")
for k in (1, 2, 3, 5):
    s = raw if k == 1 else sticky(raw, k)
    c1, P = matrix(s)
    c2 = np.zeros((K, K, K))
    np.add.at(c2, (s[:-2], s[1:-1], s[2:]), 1)
    G, dof = 0.0, 0
    for j in range(K):
        n_prev = 0
        for i in range(K):
            n = c2[i, j].sum()
            if n == 0:
                continue
            n_prev += 1
            obs, exp = c2[i, j], n * P[j]
            m = obs > 0
            G += 2 * (obs[m] * np.log(obs[m] / exp[m])).sum()
        dof += max(n_prev - 1, 0) * (int((P[j] > 0).sum()) - 1)
    train = years < 2015
    _, Ptr = matrix(s[train])
    idx = np.where(train)[0]
    idx = idx[idx + H < len(s)]
    cH = np.zeros((K, K))
    np.add.at(cH, (s[idx], s[idx + H]), 1)
    direct = cH / np.maximum(cH.sum(1, keepdims=True), 1)
    test = np.where((years >= 2015) & (np.arange(len(s)) + H < len(s)))[0]
    Y = np.eye(K)[s[test + H]]
    bm = ((np.linalg.matrix_power(Ptr, H)[s[test]] - Y) ** 2).sum(1).mean()
    bd = ((direct[s[test]] - Y) ** 2).sum(1).mean()
    runs, start = [], 0
    for t in range(1, len(s) + 1):
        if t == len(s) or s[t] != s[start]:
            runs.append((s[start], t - start))
            start = t
    hz = []
    for lo, hi in ((1, 1), (6, 20), (21, 60)):
        at = ex = 0
        for st, n in runs:
            if st == 0:
                for age in range(lo, min(hi, n) + 1):
                    at += 1
                    ex += age == n
        hz.append(ex / at if at else float("nan"))
    switches = (np.diff(s) != 0).sum() / (len(s) / 252)
    name = "raw" if k == 1 else f"sticky k={k}"
    print(f"{name:>10} {switches:11.1f} {G:12.0f} {chi2.sf(G, dof):9.1e} {bm:13.4f} {bd:13.4f} {bm - bd:+7.4f}  "
          + " / ".join(f"{h:.3f}" for h in hz))
```

Output (2026-09-17):

```text
     label switches/yr  G 2nd-order         p  Brier Markov  Brier direct     gap  hazard risk_on 1d / 6-20d / 21-60d
       raw        37.4          705  1.6e-130        0.5718        0.5467 +0.0251  0.335 / 0.052 / 0.032
sticky k=2        18.3          124   9.7e-11        0.5122        0.5200 -0.0078  0.000 / 0.036 / 0.027
sticky k=3        12.1           52   3.0e-01        0.4890        0.4940 -0.0050  0.000 / 0.042 / 0.020
sticky k=5         7.1           18   1.0e+00        0.4339        0.4328 +0.0011  0.000 / 0.026 / 0.017
```

## Appendix D - part B - barrier simulation (`mc_barrier.py`)

```python
"""EXP-011 part B - do simulated barrier probabilities for S211's stop/target come true?

uv run --no-project --with numpy python mc_barrier.py <mc_data.pkl> <mc_regime_fit.pkl>
Decision at the close of day t. Barriers = S211's: stop = clamp(2 x ATR14 %, 2.5 %, 8 %); target = median
10-session favourable excursion over the 120 prior settled windows. Outcome over the next 10 sessions,
low checked before high (a day touching both counts as stop). Everything a model sees is dated <= t.
"""
import pickle
import sys
import time

import numpy as np

H, LOOKBACK, ATR_N, N_PATHS, STEP, RECENT = 10, 120, 14, 1000, 5, 250
rng = np.random.default_rng(20260917)
d = pickle.load(open(sys.argv[1], "rb"))
fit = pickle.load(open(sys.argv[2], "rb"))
cumP = np.cumsum(fit["P_train"], axis=1)  # 1-step regime matrix fitted on 1990-2014 only


def label(v):
    return 4 if v >= 35 else 3 if v >= 25 else 2 if v >= 20 else 0 if v <= 15 else 1


vixlab = {k: label(v) for k, v in d["vix"].items()}
calendar = sorted({b[0] for rows in d["bars"].values() for b in rows})
decision_dates = set(calendar[calendar.index("2017-01-03")::STEP])
MODELS = ("recent250", "all_history", "regime_today", "regime_markov")
rec = {m: [] for m in MODELS}
real, touch, meta = [], [], []


def simulate(h, l, c, pick, stop, target):
    idx = pick
    cc = np.cumprod(c[idx], axis=1)
    prev = np.concatenate([np.ones((idx.shape[0], 1)), cc[:, :-1]], axis=1)
    hit_s = prev * l[idx] <= 1 - stop
    hit_t = prev * h[idx] >= 1 + target
    fs = np.where(hit_s.any(1), hit_s.argmax(1), H)
    ft = np.where(hit_t.any(1), hit_t.argmax(1), H)
    p_stop = np.mean((fs < H) & (fs <= ft))
    p_target = np.mean((ft < H) & (ft < fs))
    return (p_stop, p_target, 1 - p_stop - p_target)


t0 = time.time()
for sym, rows in sorted(d["bars"].items()):
    dates = [r[0] for r in rows]
    o, hi, lo, cl = (np.array([r[k] for r in rows]) for k in (1, 2, 3, 4))
    rh, rl, rc = hi[1:] / cl[:-1], lo[1:] / cl[:-1], cl[1:] / cl[:-1]  # day j+1 relative to close j
    rreg = np.array([vixlab.get(x, -1) for x in dates[1:]])
    tr = np.maximum.reduce([hi[1:] - lo[1:], abs(hi[1:] - cl[:-1]), abs(lo[1:] - cl[:-1])])
    for t, day in enumerate(dates):
        if day not in decision_dates or t < RECENT + 1 or t + H >= len(rows) or day not in vixlab:
            continue
        atr_pct = tr[t - ATR_N:t].mean() / cl[t]  # tr[k] is the true range of bar k+1
        stop = min(max(2 * atr_pct, 0.025), 0.08)
        anchors = range(t - H - LOOKBACK + 1, t - H + 1)
        exc = [max(hi[a + 1:a + 1 + H].max() / cl[a] - 1, 0.0) for a in anchors]
        target = min(float(np.median(exc)), 1.0)
        # realised outcome, entry at the decision close
        lvl_s, lvl_t = cl[t] * (1 - stop), cl[t] * (1 + target)
        outcome, touched = 2, False
        for k in range(t + 1, t + H + 1):
            if lo[k] <= lvl_s:
                outcome = 0
                break
            if hi[k] >= lvl_t:
                outcome = 1
                break
        touched = hi[t + 1:t + H + 1].max() >= lvl_t
        real.append(outcome)
        touch.append(touched)
        meta.append((day, sym, target / stop))
        pool = np.arange(0, t)  # relative moves dated <= t
        recent = np.arange(t - RECENT, t)
        rec["recent250"].append(simulate(rh, rl, rc, rng.choice(recent, (N_PATHS, H)), stop, target))
        rec["all_history"].append(simulate(rh, rl, rc, rng.choice(pool, (N_PATHS, H)), stop, target))
        today = vixlab[day]
        pools = {r: (x if len(x) >= 30 else pool) for r in range(5) for x in [pool[rreg[pool] == r]]}
        pick = rng.choice(pools[today], (N_PATHS, H))
        rec["regime_today"].append(simulate(rh, rl, rc, pick, stop, target))
        # regime path drawn from the Markov chain, each step sampling a day from that regime
        reg = np.full(N_PATHS, today)
        pick = np.empty((N_PATHS, H), dtype=int)
        for k in range(H):
            reg = (rng.random(N_PATHS)[:, None] > cumP[reg]).sum(1).clip(0, 4)
            for r in np.unique(reg):
                m = reg == r
                pick[m, k] = rng.choice(pools[r], m.sum())
        rec["regime_markov"].append(simulate(rh, rl, rc, pick, stop, target))
    print(f"  {sym} done, cases so far {len(real)}, {time.time() - t0:.0f}s", flush=True)

real = np.array(real)
Y = np.eye(3)[real]
dates_arr = np.array([m[0] for m in meta])
years = np.array([int(x[:4]) for x in dates_arr])
print(f"\ncases {len(real)} ({len(set(dates_arr))} decision dates x {len({m[1] for m in meta})} names), 2017-01 -> {max(dates_arr)}")
print("realised:  stop first {:.3f}  target first {:.3f}  neither {:.3f}".format(*Y.mean(0)))
print(f"S211 implicit claim - target touched within 10 sessions (ignoring stop) ~ 0.50:  realised {np.mean(touch):.3f}")
print(f"target/stop ratio: median {np.median([m[2] for m in meta]):.2f}")

# baseline: yearly-refit climatology using only previous years' outcomes (no look-ahead)
clim = np.zeros_like(Y)
for i, y in enumerate(years):
    prior = years < y
    clim[i] = Y[prior].mean(0) if prior.sum() > 500 else Y[:500].mean(0)
F = {m: np.array(v) for m, v in rec.items()}
F["climatology"] = clim


def brier(P, mask=slice(None)):
    return ((P[mask] - Y[mask]) ** 2).sum(1).mean()


ev = years >= 2018  # climatology needs one prior year
print("\nBrier (3-outcome, lower is better), 2018-2026:")
for m, P in F.items():
    print(f"   {brier(P, ev):.4f}  {m}")
# date-clustered bootstrap of Brier differences vs climatology
udates = np.unique(dates_arr[ev])
by_date = {u: np.where((dates_arr == u) & ev)[0] for u in udates}
loss = {m: ((P - Y) ** 2).sum(1) for m, P in F.items()}
print("   difference vs climatology, 95 % CI resampling whole dates (negative = better):")
for m in MODELS:
    diffs = []
    for _ in range(1000):
        sel = np.concatenate([by_date[u] for u in rng.choice(udates, len(udates))])
        diffs.append(loss[m][sel].mean() - loss["climatology"][sel].mean())
    print(f"   {m:>14}: {np.mean(loss[m][ev]) - np.mean(loss['climatology'][ev]):+.4f}  [{np.percentile(diffs, 2.5):+.4f}, {np.percentile(diffs, 97.5):+.4f}]")

print("\nCalibration, 2018-2026 - declared probability bucket -> realised share")
for m in ("recent250", "regime_markov"):
    for k, name in ((0, "P(stop first)"), (1, "P(target first)")):
        p, y = F[m][ev, k], Y[ev, k]
        cells = []
        for lo_, hi_ in ((0, .1), (.1, .2), (.2, .3), (.3, .4), (.4, .5), (.5, .6), (.6, .8), (.8, 1.01)):
            sel = (p >= lo_) & (p < hi_)
            if sel.sum() >= 100:
                cells.append(f"said {p[sel].mean():.2f} got {y[sel].mean():.2f} (n={sel.sum()})")
        print(f"   {m} {name}:\n      " + "\n      ".join(cells))

print("\nBy regime at decision (2018-2026): realised vs declared by regime_markov / all_history")
names = ("risk_on", "neutral", "risk_off", "high_vol", "extreme")
regs = np.array([vixlab[x] for x in dates_arr])
for r in range(5):
    sel = ev & (regs == r)
    if sel.sum() < 200:
        continue
    print(f"   {names[r]:>9} n={sel.sum():5d}  realised stop/target {Y[sel, 0].mean():.3f}/{Y[sel, 1].mean():.3f}   "
          f"markov {F['regime_markov'][sel, 0].mean():.3f}/{F['regime_markov'][sel, 1].mean():.3f}   "
          f"all_history {F['all_history'][sel, 0].mean():.3f}/{F['all_history'][sel, 1].mean():.3f}")
pickle.dump({"F": F, "Y": Y, "meta": meta, "touch": touch}, open(sys.argv[1].replace("mc_data", "mc_barrier_res"), "wb"))
```

Output (2026-09-17):

```text
cases 47485 (486 decision dates x 98 names), 2017-01 -> 2026-08-27
realised:  stop first 0.285  target first 0.480  neither 0.235
S211 implicit claim - target touched within 10 sessions (ignoring stop) ~ 0.50:  realised 0.502
target/stop ratio: median 0.80

Brier (3-outcome, lower is better), 2018-2026:
   0.6394  recent250
   0.6300  all_history
   0.6445  regime_today
   0.6306  regime_markov
   0.6360  climatology
   difference vs climatology, 95 % CI resampling whole dates (negative = better):
        recent250: +0.0034  [-0.0023, +0.0093]
      all_history: -0.0060  [-0.0111, -0.0003]
     regime_today: +0.0084  [+0.0005, +0.0164]
    regime_markov: -0.0055  [-0.0111, +0.0003]

Calibration, 2018-2026 - declared probability bucket -> realised share
   recent250 P(stop first):
      said 0.07 got 0.21 (n=1005)
      said 0.16 got 0.26 (n=5932)
      said 0.25 got 0.27 (n=12684)
      said 0.35 got 0.30 (n=14766)
      said 0.44 got 0.34 (n=7172)
      said 0.53 got 0.41 (n=973)
   recent250 P(target first):
      said 0.28 got 0.28 (n=228)
      said 0.37 got 0.35 (n=4786)
      said 0.46 got 0.43 (n=16855)
      said 0.54 got 0.52 (n=16508)
      said 0.63 got 0.63 (n=4084)
   regime_markov P(stop first):
      said 0.07 got 0.19 (n=991)
      said 0.16 got 0.25 (n=7868)
      said 0.25 got 0.29 (n=15518)
      said 0.34 got 0.32 (n=12025)
      said 0.44 got 0.31 (n=4824)
      said 0.53 got 0.28 (n=1182)
      said 0.63 got 0.29 (n=130)
   regime_markov P(target first):
      said 0.17 got 0.28 (n=272)
      said 0.26 got 0.32 (n=1971)
      said 0.36 got 0.36 (n=7709)
      said 0.45 got 0.46 (n=14787)
      said 0.54 got 0.54 (n=12736)
      said 0.64 got 0.63 (n=4968)

By regime at decision (2018-2026): realised vs declared by regime_markov / all_history
     risk_on n=10151  realised stop/target 0.305/0.435   markov 0.226/0.489   all_history 0.337/0.473
     neutral n=17018  realised stop/target 0.309/0.449   markov 0.266/0.478   all_history 0.296/0.477
    risk_off n= 8218  realised stop/target 0.263/0.504   markov 0.345/0.444   all_history 0.265/0.459
    high_vol n= 5877  realised stop/target 0.269/0.542   markov 0.354/0.482   all_history 0.210/0.458
     extreme n= 1274  realised stop/target 0.246/0.715   markov 0.355/0.509   all_history 0.134/0.495
```

## Appendix E - part C1 - regime base rates (`mc_followup.py`)

```python
"""EXP-011 part C - direct counts vs simulation, and does S211's target/stop ratio predict outcomes?

uv run --no-project --with numpy python mc_followup.py <mc_data.pkl> <mc_barrier_res.pkl>
"""
import pickle
import sys

import numpy as np

rng = np.random.default_rng(7)
d = pickle.load(open(sys.argv[1], "rb"))
res = pickle.load(open(sys.argv[2], "rb"))
F, Y, meta = res["F"], res["Y"], res["meta"]
dates = np.array([m[0] for m in meta])
years = np.array([int(x[:4]) for x in dates])
ratio = np.array([m[2] for m in meta])
lab = {k: (4 if v >= 35 else 3 if v >= 25 else 2 if v >= 20 else 0 if v <= 15 else 1) for k, v in d["vix"].items()}
reg = np.array([lab[x] for x in dates])
ev = years >= 2018

# C1 - regime-conditional base rates from previous years only (no simulation at all)
rc = np.zeros_like(Y)
for i in range(len(Y)):
    prior = (years < years[i]) & (reg == reg[i])
    rc[i] = Y[prior].mean(0) if prior.sum() >= 200 else F["climatology"][i]
loss = {"climatology": ((F["climatology"] - Y) ** 2).sum(1), "all_history sim": ((F["all_history"] - Y) ** 2).sum(1),
        "regime_markov sim": ((F["regime_markov"] - Y) ** 2).sum(1), "regime base rate": ((rc - Y) ** 2).sum(1)}
ud = np.unique(dates[ev])
by = {u: np.where((dates == u) & ev)[0] for u in ud}
print("C1 Brier 2018-2026, and difference vs climatology (95 % CI, whole dates resampled)")
for m, L in loss.items():
    diffs = [L[s].mean() - loss["climatology"][s].mean()
             for s in (np.concatenate([by[u] for u in rng.choice(ud, len(ud))]) for _ in range(1000))]
    print(f"   {L[ev].mean():.4f}  {m:>18}  {L[ev].mean() - loss['climatology'][ev].mean():+.4f} "
          f"[{np.percentile(diffs, 2.5):+.4f}, {np.percentile(diffs, 97.5):+.4f}]")

# C2 - does the ratio S211 gates on predict what happens?  payoff in stop units: +ratio if target first,
# -1 if stop first, 0 if neither (a lower bound on neither's spread, stated as such)
print("\nC2 outcomes by S211 target/stop ratio (all 2017-2026 cases)")
print("   ratio bucket      n   stop-first  target-first  neither   expectancy (stop units, neither=0)")
edges = (0, .6, .7, .8, .9, 1.0, 1.2, 10)
for lo, hi in zip(edges[:-1], edges[1:]):
    m = (ratio >= lo) & (ratio < hi)
    if m.sum() < 200:
        continue
    ps, pt = Y[m, 0].mean(), Y[m, 1].mean()
    e = pt * ratio[m].mean() - ps
    ed = []
    ud_all = np.unique(dates[m])
    idx = {u: np.where(m & (dates == u))[0] for u in ud_all}
    for _ in range(500):
        s = np.concatenate([idx[u] for u in rng.choice(ud_all, len(ud_all))])
        ed.append(Y[s, 1].mean() * ratio[s].mean() - Y[s, 0].mean())
    print(f"   [{lo:.1f}, {hi:>4.1f})  {m.sum():6d}   {ps:.3f}       {pt:.3f}        {1 - ps - pt:.3f}     "
          f"{e:+.3f} [{np.percentile(ed, 2.5):+.3f}, {np.percentile(ed, 97.5):+.3f}]")
below, above = ratio < 0.8, ratio >= 0.8
for name, m in (("below 0.80 (rejected)", below), ("at/above 0.80 (passed)", above)):
    print(f"   {name:>24}: n={m.sum()}  stop {Y[m, 0].mean():.3f}  target {Y[m, 1].mean():.3f}  "
          f"expectancy {Y[m, 1].mean() * ratio[m].mean() - Y[m, 0].mean():+.3f}")
```

Output (2026-09-17):

```text
C1 Brier 2018-2026, and difference vs climatology (95 % CI, whole dates resampled)
   0.6360         climatology  +0.0000 [+0.0000, +0.0000]
   0.6300     all_history sim  -0.0060 [-0.0114, -0.0004]
   0.6306   regime_markov sim  -0.0055 [-0.0114, +0.0004]
   0.6423    regime base rate  +0.0063 [+0.0034, +0.0093]

C2 outcomes by S211 target/stop ratio (all 2017-2026 cases)
   ratio bucket      n   stop-first  target-first  neither   expectancy (stop units, neither=0)
   [0.0,  0.6)   10308   0.216       0.649        0.135     +0.093 [+0.044, +0.140]
   [0.6,  0.7)    6382   0.253       0.546        0.201     +0.103 [+0.069, +0.132]
   [0.7,  0.8)    6987   0.277       0.498        0.225     +0.096 [+0.056, +0.132]
   [0.8,  0.9)    6484   0.281       0.454        0.265     +0.104 [+0.071, +0.139]
   [0.9,  1.0)    5496   0.310       0.419        0.271     +0.087 [+0.049, +0.127]
   [1.0,  1.2)    7013   0.340       0.358        0.302     +0.049 [+0.005, +0.093]
   [1.2, 10.0)    4815   0.383       0.285        0.332     +0.010 [-0.051, +0.074]
      below 0.80 (rejected): n=23677  stop 0.244  target 0.577  expectancy +0.104
     at/above 0.80 (passed): n=23808  stop 0.326  target 0.383  expectancy +0.077
```

## Appendix F - part C2 - ratio and realised return (`mc_ratio_payoff.py`)

```python
"""EXP-011 part C3 - does S211's target/stop ratio predict the realised trade return? (full payoff, no simulation)

uv run --no-project --with numpy python mc_ratio_payoff.py <mc_data.pkl>
Exit: stop (low first) -> -stop; target -> +target; neither -> close at session 10. Entry at the decision close.
Positions are sized by notional (sizing.py: 1 % of equity), so the return in PERCENT is what the book earns.
"""
import pickle
import sys

import numpy as np

H, LOOKBACK, ATR_N, STEP = 10, 120, 14, 5
rng = np.random.default_rng(11)
d = pickle.load(open(sys.argv[1], "rb"))
calendar = sorted({b[0] for rows in d["bars"].values() for b in rows})
dd = set(calendar[calendar.index("2017-01-03")::STEP])
rows_out = []
for sym, rows in sorted(d["bars"].items()):
    dates = [r[0] for r in rows]
    hi, lo, cl = (np.array([r[k] for r in rows]) for k in (2, 3, 4))
    tr = np.maximum.reduce([hi[1:] - lo[1:], abs(hi[1:] - cl[:-1]), abs(lo[1:] - cl[:-1])])
    for t, day in enumerate(dates):
        if day not in dd or t < 251 or t + H >= len(rows):
            continue
        stop = min(max(2 * tr[t - ATR_N:t].mean() / cl[t], 0.025), 0.08)
        target = min(float(np.median([max(hi[a + 1:a + 1 + H].max() / cl[a] - 1, 0.0)
                                      for a in range(t - H - LOOKBACK + 1, t - H + 1)])), 1.0)
        ret = cl[t + H] / cl[t] - 1
        for k in range(t + 1, t + H + 1):
            if lo[k] <= cl[t] * (1 - stop):
                ret = -stop
                break
            if hi[k] >= cl[t] * (1 + target):
                ret = target
                break
        rows_out.append((day, sym, target / stop, ret, stop, cl[t + H] / cl[t] - 1))

dates = np.array([r[0] for r in rows_out])
ratio, ret, stop, hold = (np.array([r[k] for r in rows_out]) for k in (2, 3, 4, 5))
print(f"cases {len(rows_out)}; ratio median {np.median(ratio):.2f}; "
      f"ratio median on 2026-08..09 decision dates {np.median(ratio[dates >= '2026-08-01']):.2f}")


def ci(mask, f):
    ud = np.unique(dates[mask])
    idx = {u: np.where(mask & (dates == u))[0] for u in ud}
    vals = [f(np.concatenate([idx[u] for u in rng.choice(ud, len(ud))])) for _ in range(500)]
    return f(np.where(mask)[0]), np.percentile(vals, 2.5), np.percentile(vals, 97.5)


edges = (0, .6, .7, .8, .9, 1.0, 1.2, 10)
for period, pm in (("2017-2026", np.ones(len(dates), bool)), ("2017-2021", dates < "2022"), ("2022-2026", dates >= "2022")):
    print(f"\n{period}: mean trade return by ratio bucket (95 % CI, whole dates resampled) | buy-and-hold 10 sessions")
    for lo_, hi_ in zip(edges[:-1], edges[1:]):
        m = pm & (ratio >= lo_) & (ratio < hi_)
        if m.sum() < 200:
            continue
        e, a, b = ci(m, lambda s: ret[s].mean())
        print(f"   [{lo_:.1f}, {hi_:>4.1f})  n={m.sum():6d}  trade {e:+.2%} [{a:+.2%}, {b:+.2%}]   "
              f"in stop units {np.mean(ret[m] / stop[m]):+.3f}   hold {hold[m].mean():+.2%}")
    for name, m in (("rejected <0.80", pm & (ratio < .8)), ("passed >=0.80", pm & (ratio >= .8))):
        e, a, b = ci(m, lambda s: ret[s].mean())
        print(f"   {name:>15}  n={m.sum():6d}  trade {e:+.2%} [{a:+.2%}, {b:+.2%}]   hold {hold[m].mean():+.2%}")
    m1, m2 = pm & (ratio < .8), pm & (ratio >= .8)
    ud = np.unique(dates[pm])
    i1 = {u: np.where(m1 & (dates == u))[0] for u in ud}
    i2 = {u: np.where(m2 & (dates == u))[0] for u in ud}
    diffs = []
    for _ in range(500):
        pick = rng.choice(ud, len(ud))
        s1 = np.concatenate([i1[u] for u in pick])
        s2 = np.concatenate([i2[u] for u in pick])
        diffs.append(ret[s2].mean() - ret[s1].mean())
    print(f"   passed minus rejected: {ret[m2].mean() - ret[m1].mean():+.2%} "
          f"[{np.percentile(diffs, 2.5):+.2%}, {np.percentile(diffs, 97.5):+.2%}]")
pickle.dump(rows_out, open(sys.argv[1].replace("mc_data", "mc_ratio_rows"), "wb"))
```

Output (2026-09-17):

```text
cases 47485; ratio median 0.80; ratio median on 2026-08..09 decision dates 0.81

2017-2026: mean trade return by ratio bucket (95 % CI, whole dates resampled) | buy-and-hold 10 sessions
   [0.0,  0.6)  n= 10308  trade +0.31% [+0.01%, +0.58%]   in stop units +0.060   hold +0.69%
   [0.6,  0.7)  n=  6382  trade +0.39% [+0.21%, +0.58%]   in stop units +0.079   hold +0.69%
   [0.7,  0.8)  n=  6987  trade +0.36% [+0.17%, +0.52%]   in stop units +0.078   hold +0.67%
   [0.8,  0.9)  n=  6484  trade +0.44% [+0.26%, +0.60%]   in stop units +0.104   hold +0.70%
   [0.9,  1.0)  n=  5496  trade +0.37% [+0.19%, +0.55%]   in stop units +0.090   hold +0.70%
   [1.0,  1.2)  n=  7013  trade +0.34% [+0.13%, +0.53%]   in stop units +0.078   hold +0.66%
   [1.2, 10.0)  n=  4815  trade +0.36% [+0.09%, +0.63%]   in stop units +0.086   hold +0.62%
    rejected <0.80  n= 23677  trade +0.35% [+0.14%, +0.53%]   hold +0.68%
     passed >=0.80  n= 23808  trade +0.38% [+0.22%, +0.53%]   hold +0.67%
   passed minus rejected: +0.03% [-0.17%, +0.23%]

2017-2021: mean trade return by ratio bucket (95 % CI, whole dates resampled) | buy-and-hold 10 sessions
   [0.0,  0.6)  n=  4965  trade +0.33% [-0.24%, +0.79%]   in stop units +0.068   hold +0.64%
   [0.6,  0.7)  n=  3138  trade +0.50% [+0.26%, +0.72%]   in stop units +0.107   hold +0.79%
   [0.7,  0.8)  n=  3367  trade +0.49% [+0.28%, +0.72%]   in stop units +0.113   hold +0.92%
   [0.8,  0.9)  n=  3345  trade +0.60% [+0.38%, +0.83%]   in stop units +0.150   hold +0.96%
   [0.9,  1.0)  n=  2914  trade +0.49% [+0.25%, +0.74%]   in stop units +0.129   hold +0.98%
   [1.0,  1.2)  n=  3807  trade +0.44% [+0.21%, +0.69%]   in stop units +0.112   hold +0.74%
   [1.2, 10.0)  n=  3017  trade +0.55% [+0.17%, +0.90%]   in stop units +0.139   hold +0.88%
    rejected <0.80  n= 11470  trade +0.42% [+0.09%, +0.71%]   hold +0.77%
     passed >=0.80  n= 13083  trade +0.52% [+0.32%, +0.73%]   hold +0.88%
   passed minus rejected: +0.10% [-0.19%, +0.43%]

2022-2026: mean trade return by ratio bucket (95 % CI, whole dates resampled) | buy-and-hold 10 sessions
   [0.0,  0.6)  n=  5343  trade +0.30% [-0.03%, +0.63%]   in stop units +0.053   hold +0.74%
   [0.6,  0.7)  n=  3244  trade +0.29% [+0.03%, +0.55%]   in stop units +0.053   hold +0.58%
   [0.7,  0.8)  n=  3620  trade +0.24% [-0.02%, +0.49%]   in stop units +0.047   hold +0.44%
   [0.8,  0.9)  n=  3139  trade +0.26% [+0.00%, +0.51%]   in stop units +0.055   hold +0.41%
   [0.9,  1.0)  n=  2582  trade +0.23% [-0.05%, +0.49%]   in stop units +0.047   hold +0.38%
   [1.0,  1.2)  n=  3206  trade +0.21% [-0.07%, +0.49%]   in stop units +0.037   hold +0.57%
   [1.2, 10.0)  n=  1798  trade +0.04% [-0.30%, +0.41%]   in stop units -0.004   hold +0.17%
    rejected <0.80  n= 12207  trade +0.28% [+0.02%, +0.52%]   hold +0.61%
     passed >=0.80  n= 10725  trade +0.20% [-0.04%, +0.42%]   hold +0.41%
   passed minus rejected: -0.08% [-0.35%, +0.17%]
```

## Appendix G - part D - same-night feed check (`mc_feed_check.py`)

```python
"""EXP-011 part D - same night (2026-09-16), same formula: S211 ratio on SIP bars vs the production IEX snapshot."""
import pickle, sys
import numpy as np
d = pickle.load(open(sys.argv[1], "rb"))
H, LB = 10, 120
out = {}
for sym, rows in d["bars"].items():
    rows = [r for r in rows if r[0] <= "2026-09-16"]
    hi, lo, cl = (np.array([r[k] for r in rows]) for k in (2, 3, 4))
    tr = np.maximum.reduce([hi[1:] - lo[1:], abs(hi[1:] - cl[:-1]), abs(lo[1:] - cl[:-1])])
    t = len(rows) - 1
    atr = tr[t - 14:t].mean() / cl[t]
    stop = min(max(2 * atr, 0.025), 0.08)
    target = float(np.median([max(hi[a + 1:a + 1 + H].max() / cl[a] - 1, 0) for a in range(t - H - LB + 1, t - H + 1)]))
    out[sym] = (rows[-1][0], atr, stop, target, target / stop)
r = np.array([v[4] for v in out.values()])
print(f"SIP 2026-09-16  names {len(r)} last bar {min(v[0] for v in out.values())}..{max(v[0] for v in out.values())}")
print(f"   ratio p25/median/p75 {np.percentile(r,25):.3f}/{np.median(r):.3f}/{np.percentile(r,75):.3f}  below 0.80 {np.mean(r<.8):.0%}  below 1.0 {np.mean(r<1):.0%}")
print(f"   median ATR {np.median([v[1] for v in out.values()]):.4f}  stop {np.median([v[2] for v in out.values()]):.4f}  target {np.median([v[3] for v in out.values()]):.4f}")
pickle.dump(out, open(sys.argv[1].replace("mc_data", "mc_sip_0916"), "wb"))
```

Output (2026-09-17):

```text
SIP 2026-09-16  names 98 last bar 2026-09-16..2026-09-16
   ratio p25/median/p75 0.818/0.918/1.005  below 0.80 21%  below 1.0 72%
   median ATR 0.0234  stop 0.0468  target 0.0433
```

## Appendix H - part D - rejection share by year (`mc_ratio_years.py`)

```python
"""EXP-011 part D2 - share of names the 0.80 floor would reject, by year (SIP, every 5th session)."""
import pickle, sys
import numpy as np
rows = pickle.load(open(sys.argv[1], "rb"))
dates = np.array([r[0] for r in rows]); ratio = np.array([r[2] for r in rows])
by_date = {}
for dt, x in zip(dates, ratio):
    by_date.setdefault(dt, []).append(x)
nightly = {dt: np.mean(np.array(v) < .8) for dt, v in by_date.items()}
print("year  median ratio  share below 0.80: mean  min  max (per decision night)")
for y in range(2017, 2027):
    sel = [dt for dt in nightly if dt.startswith(str(y))]
    m = np.array([nightly[dt] for dt in sel])
    print(f"{y}  {np.median(ratio[np.char.startswith(dates, str(y))]):.2f}          {m.mean():.0%}   {m.min():.0%}  {m.max():.0%}")
allv = np.array(list(nightly.values()))
print(f"all nights: share below 0.80 p10/median/p90 {np.percentile(allv,10):.0%}/{np.median(allv):.0%}/{np.percentile(allv,90):.0%}; nights rejecting >50%: {np.mean(allv>.5):.0%}")
```

Output (2026-09-17):

```text
year  median ratio  share below 0.80: mean  min  max (per decision night)
2017  0.81          49%   19%  72%
2018  0.75          57%   13%  99%
2019  0.85          43%   11%  99%
2020  0.84          46%   0%  98%
2021  0.88          39%   4%  95%
2022  0.68          70%   10%  96%
2023  0.84          45%   11%  82%
2024  0.86          41%   14%  91%
2025  0.80          51%   12%  99%
2026  0.71          64%   22%  88%
all nights: share below 0.80 p10/median/p90 18%/49%/89%; nights rejecting >50%: 47%
```
