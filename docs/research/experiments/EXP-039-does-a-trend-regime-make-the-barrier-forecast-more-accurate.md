# EXP-039 — Does a sticky bull / sideways / bear regime make the barrier forecast more accurate?

**Status:** PRE-REGISTERED 2026-11-16 (planner, `48344da7`) · COMPLETE 2026-11-16 · **H0: the trend regime adds nothing to the forecast; R1 over R0 −0.20 % [−0.97, +0.48], the halves disagree (−0.90 %, +0.37 %)**
**Decision / origin:** the operator, 2026-11-16, on how far the book is from being managed as a
distribution: *"how about introduction of a regime. There were three regimes in trading from my
memory"*, then *"run it as a $0 experiment"*; [DL-322](../../design-log.md); work-queue 92 (DL-240) ·
**Cost:** $0 (EXP-018's saved decisions and SPY's closes, read on this laptop)

## 1. Why we needed this experiment

Step 5 of work-queue 92, the PM sizing over distributions, waits on the forecaster's claims being
calibrated. Read 2026-11-16 from the live ledger: the held claims are (return bias +0.08 %
[−0.27, +0.46]), the buy claims are not (skill −7.1 % [−15.1, −1.1] against climatology, realised
return +3.26 % [+2.59, +3.80] above declared, 65 claims on 23 dates from 2026-09-28). A forecast that
knows whether the market is trending up, sideways or down could shift its base rates where a single
model cannot.

The fleet's regime today is VIX alone, five bands ([ADR-0028](../../decisions/0028-the-regime-reads-vix-from-fmp-and-says-when-it-cannot.md));
it sets the analyst's starting stop, target and confidence floor. The project's earlier system
classified trend as well (SPY's 20-session return with VIX: bull, sideways, bear), which this repo
never carried over. What is already measured: the raw VIX label is not a Markov chain and its median
run is 2 sessions against a 10-session horizon, while a label that changes only after 3 closes is
([EXP-011](EXP-011-regime-markov-and-barrier-calibration.md)); scaling size by the VIX label loses
([EXP-013](EXP-013-regime-scaled-sizing-replay.md)); a take-profit below SPY's 200-session mean does
not help ([EXP-037](EXP-037-does-a-take-profit-earn-more-than-the-stop-alone-in-falling-markets.md)).
No experiment has asked whether a trend regime improves the forecast itself.

## 2. Hypothesis

**The label**, per decision date from SPY's close on that date: *bull* if the close is at or above the
mean of its last 200 closes and its 20-session return is above +2 %; *bear* if it is below that mean
and its 20-session return is below −2 %; *sideways* otherwise. The label in force changes only when a
new raw label has held for 3 consecutive closes.

**The arms**, each the production model's probabilities (GARCH(1,1) on 756 sessions, `G_756`, as
[EXP-018](EXP-018-garch-history-depth.md) computed them) shifted by the gap between realised and
declared outcome shares, learned only from decisions dated before 15 December of the year before the
one scored (so every outcome learned from had settled):

- **R0, the baseline:** one shift, pooled over all regimes.
- **R1, the trend regime:** one shift per label; a label with fewer than 500 training cases uses R0's.

**Primary:** R1's Brier skill over R0, 1 − Brier(R1) / Brier(R0), on 2020-01-01 onward.

- **H1:** the skill is at least **+0.5 %**, its 95 % interval's lower bound is above 0, and it is above
  0 in both halves (2020–2022 and 2023–2026).
- **WORSE:** the interval's upper bound is below 0. **H0:** otherwise.

**Why +0.5 %:** GARCH itself clears climatology by +2.67 % (EXP-018) and VIX weighting added about 1 %
(EXP-011); a regime worth a new decision input should add a fifth of the model's own skill, and
anything smaller is lost in the live ledger's interval for months.

**Reported, no bar:** R1 and R0 over the raw `G_756`; **R2**, the same shift per the fleet's VIX
label (the five live bands, raw); `G_756` over climatology; climatology per trend label over pooled
climatology; per label: cases, realised shares, declared shares, R1 over R0.

**What follows, fixed now:** on H1 the planner specs a trend-regime correction as a shadow challenger
in the forecaster's ledger (a sprint for Codex), and the live scorecard decides; nothing sizes on it.
On H0 or WORSE the forecast takes no trend regime, and the buy claims' bias is looked for elsewhere.

## 3. Data

- **EXP-018's decisions**, OneDrive `trading-agents-data/exp018/exp018_sim.pkl` (SHA-256
  `88a4e8991314…`): 47,485 decisions (98 names, every 5th session, S211's stop and target, 10-session
  outcome low before high), of which **37,587** carry `G_756` (2019-01-07 → 2026-08-27), EXP-018's
  primary set. Built from the replay cache (Alpaca SIP, split-adjusted, survivorship-biased: today's
  names). Licensed bars stay in OneDrive, never the repo.
- **SPY's closes**, `trading-agents-data/sp500_benchmark.csv.gz` (SHA-256 `f40b8b60…`), 2016-01-04 →
  2026-09-25; the label exists from 2016-10-17.
- **Measured before this commit by `count`, which reads dates and SPY only:** every decision date has
  a label; 140 switches (14.0 a year), median run **16 sessions**; sessions 42.0 % bull, 48.8 %
  sideways, 9.2 % bear. Cases by year (bull / sideways / bear): 2019 2,522 / 2,231 / 97; 2020
  2,619 / 1,843 / 485; 2021 2,332 / 2,526 / 0; 2022 490 / 2,450 / 1,960; 2023 2,352 / 2,450 / 98;
  2024 3,136 / 1,862 / 0; 2025 2,156 / 2,058 / 686; 2026 1,078 / 1,862 / 294. 2020's bear cell has 97
  training cases, so it takes the pooled shift. The last label, 2026-09-25, is sideways.
- **Seen before:** EXP-018's scores by year and by VIX label (its Appendix R). This is a new rule on
  probabilities already scored pooled; no trend split of them has been read.

## 4. Tools and setup

Intel Core i7-7660U (2 cores / 4 threads), 15.9 GB RAM, Windows 10 Pro 19045; Python 3.12.2 from the
repo's venv (`python -I`), numpy 2.5.3; uv 0.8.14. Repo `main` at the pre-registration commit. Script
`exp039_score.py` in OneDrive `trading-agents-data/exp039-2026-11-16/`, SHA-256 in Appendix P.
Interval: 1,000 resamples of whole decision dates, seed `20261116`, percentile 95 % (EXP-018's
method). Shifted probabilities are clipped at 0.001 and renormalised.

## 5. How it was conducted

1. `count` printed the split above (section 3), reading no outcome or probability. Done before this
   commit.
2. This record is committed: the pre-registration.
3. `score` runs once. It refuses if any decision date lacks a label. For each scored year it learns
   R0, R1 and R2's shifts and both climatologies from the decisions dated before 15 December of the
   year before, then scores Brier per case and the date-resampled intervals.
4. Sections 6–8 are written from the output, with no change to the rule.

## 6. Results

All MEASURED, `exp039.json` (SHA-256 `d7e248a78bff…`), one scored run: 32,737 decisions on 335 dates,
2020-01-03 → 2026-08-27.

- **Primary: H0.** R1's Brier skill over R0 = **−0.20 %, 95 % interval [−0.97, +0.48]**; by half,
  2020–2022 **−0.90 %**, 2023–2026 **+0.37 %**. Brier R1 0.62202, R0 0.62079.
- **Secondaries, no bar:**

  | Comparison | Skill | 95 % interval |
  | --- | --- | --- |
  | R0 (pooled shift) over raw `G_756` | −0.26 % | [−0.54, +0.01] |
  | R1 (trend shift) over raw `G_756` | −0.46 % | [−1.27, +0.26] |
  | R2 (VIX shift) over R0 | −0.09 % | [−0.46, +0.27] |
  | Raw `G_756` over climatology | **+2.64 %** | [+1.81, +3.53] |
  | Climatology per trend label over pooled climatology | +0.28 % | [−0.58, +1.08] |

- **Per label** (stop first / target first / neither):

  | Label | Cases | Realised | `G_756` declared | R1 over R0 |
  | --- | --- | --- | --- | --- |
  | bull | 14,163 | 0.311 / 0.422 / 0.268 | 0.305 / 0.444 / 0.251 | +0.35 % |
  | sideways | 15,051 | 0.281 / 0.498 / 0.221 | 0.276 / 0.479 / 0.245 | −0.77 % |
  | bear | 3,523 | 0.289 / 0.600 / 0.111 | 0.240 / 0.550 / 0.210 | −0.12 % |

- **Unexpected:** in bull markets the target was reached *less* often than declared (42.2 % against
  44.4 %), and in bear markets *more* often (60.0 % against 55.0 %), with fewer names ending between the
  barriers (11.1 % against 21.0 %). Each label's shift learned from earlier years did not carry into the
  next: bear years differ from one another (2020's crash and rebound, 2022's grind, April 2025).

## 7. Conclusions

A trend regime does not make the barrier forecast more accurate. The production model already clears
climatology by +2.64 % on these years, and even a single pooled shift makes it slightly worse, so on
average it is calibrated; splitting the shift three ways only adds noise. GARCH's volatility state and
S211's per-stock target, set from each name's own recent rises, already carry what the regime knows.
The VIX label as a shift does no better (R2).

So the live buy claims' bias (realised +3.26 % above declared, skill −7.1 %, read 2026-11-16) is not a
regime effect by this test. The live window's last cached label (2026-09-25) is sideways, where the
model's declared and realised shares sit within two points. *[not measured]* The likelier causes are
that the live claims are the analyst's selected buys, where the test bed scores every name every fifth
session, and that 65 claims on 23 dates is a small sample of one market stretch.

What this does not say: it tests the regime as a correction to probabilities, not as a switch for
strategies, sizing (EXP-013) or exits (EXP-037); nor a long decline like 2000–02 or 2007–09, absent
from the cache; nor a fitted hidden Markov model (ruled out in DL-322).

## 8. Recommended code changes, and how to implement them

None. By the rule fixed in section 2, on H0 the forecast takes no trend regime, and the buy claims'
bias is looked for elsewhere. The next measurement (planner, $0): score the test bed's `G_756` on the
decisions the analyst would have approved, to see whether selection, not the market, is what the live
buy claims' bias reflects. That question waits until the buy ledger has more dates; it is a re-read, not
a build.

## Appendix P — Pre-registration (frozen)

Primary: Brier skill of R1 (`G_756` + a realised-minus-declared shift per sticky SPY trend label:
bull at or above the 200-close mean with a 20-session return above +2 %, bear below it with one below
−2 %, sideways otherwise, changing after 3 consecutive closes) over R0 (the same shift pooled), each
learned from decisions dated before 15 December of the prior year, a cell under 500 cases taking the
pooled shift; scored on EXP-018's 37,587 `G_756` decisions from 2020-01-01; 1,000 date resamples, seed
20261116. H1 if skill ≥ +0.5 %, lower bound > 0 and above 0 in 2020–2022 and 2023–2026; WORSE if
the upper bound < 0; H0 otherwise. H1 → a shadow challenger in the forecaster's ledger is specced; H0
or WORSE → no trend regime in the forecast. Script SHA-256
`89f09195898c6f11d09ec628ac779d96ab48478537cb394896b0039935c5533d`.

## Appendix R — Run record

2026-11-16, this laptop. `count` ran before the pre-registration (output `count.log`, section 3).

**Defect found at the first `score` run, fixed before any score was printed.** The run raised in the
line that formats the scored date range (`str(d.min())` on a numpy string array: `_UFuncNoLoopError`),
after the arithmetic and before any output; nothing was printed or written (`score-crash-1.log` holds
the traceback). Fixed by one line, `str(d.min()), str(d.max())` → `str(ud[0]), str(ud[-1])` (the sorted
unique dates). The rule, the arms and the statistics are unchanged. Script SHA-256 before the fix
`89f09195…` (= Appendix P), after `fac95d3ef03b1da3fd941f220e5954b40fc6c353dc56b2cf92bc65ec7851714b`
(Appendix S).

`score` then ran once in 3 s, exit 0; `exp039.json` SHA-256 `d7e248a78bffa452…` and `score.log`, in
OneDrive `trading-agents-data/exp039-2026-11-16/`. Full output:

```json
{
 "scored": [
  32737,
  335,
  "2020-01-03",
  "2026-08-27"
 ],
 "brier": {
  "R0": 0.62079,
  "R1": 0.62202,
  "R2": 0.62135,
  "clim": 0.63599,
  "clim_trend": 0.63423,
  "G": 0.6192
 },
 "primary_R1_over_R0_pct": [
  -0.199,
  -0.969,
  0.482
 ],
 "halves_R1_over_R0_pct": {
  "2020-2022": -0.904,
  "2023-2026": 0.372
 },
 "verdict": "H0",
 "secondary_pct": {
  "R1_over_G": [
   -0.456,
   -1.267,
   0.255
  ],
  "R0_over_G": [
   -0.257,
   -0.541,
   0.009
  ],
  "R2_over_R0": [
   -0.091,
   -0.462,
   0.271
  ],
  "G_over_clim": [
   2.641,
   1.812,
   3.526
  ],
  "clim_trend_over_clim": [
   0.277,
   -0.578,
   1.08
  ]
 },
 "per_label": {
  "bull": {
   "n": 14163,
   "realised": [
    0.311,
    0.422,
    0.268
   ],
   "G_declared": [
    0.305,
    0.444,
    0.251
   ],
   "R1_over_R0_pct": 0.352
  },
  "sideways": {
   "n": 15051,
   "realised": [
    0.281,
    0.498,
    0.221
   ],
   "G_declared": [
    0.276,
    0.479,
    0.245
   ],
   "R1_over_R0_pct": -0.768
  },
  "bear": {
   "n": 3523,
   "realised": [
    0.289,
    0.6,
    0.111
   ],
   "G_declared": [
    0.24,
    0.55,
    0.21
   ],
   "R1_over_R0_pct": -0.116
  }
 }
}
```

## Appendix S — Scripts

`exp039_score.py`, OneDrive `trading-agents-data/exp039-2026-11-16/`; run from that folder with the
repo's venv (the version that scored, SHA-256 `fac95d3e…`; Appendix R names the one-line fix):
`python -I exp039_score.py count --sim ../exp018/exp018_sim.pkl --spy ../sp500_benchmark.csv.gz`, then
`python -I exp039_score.py score --sim ../exp018/exp018_sim.pkl --spy ../sp500_benchmark.csv.gz --out exp039.json`.

```python
"""EXP-039: does a sticky three-state trend regime make the barrier forecast more accurate?

Reads EXP-018's saved decisions (each with GARCH-756's stop / target / neither probabilities and the
realised outcome) and SPY's closes. Labels each decision date bull / sideways / bear from SPY, then
compares a bias correction learned per regime (R1) with the same correction learned pooled (R0),
both learned only from decisions dated before 15 December of the year before the one scored.

  uv run --no-sync python -I exp039_score.py count --sim <exp018_sim.pkl> --spy <sp500_benchmark.csv.gz>
  uv run --no-sync python -I exp039_score.py score --sim <exp018_sim.pkl> --spy <...> --out <json>

`count` reads the case dates and SPY only: never an outcome or a probability.
"""

import argparse
import csv
import gzip
import json
import pickle
import statistics
from collections import Counter
from pathlib import Path

import numpy as np

LABELS = ("bull", "sideways", "bear")
VIX_LABELS = ("risk_on", "neutral", "risk_off", "high_vol", "extreme")
SMA_N, RET_N, BAND, STICK = 200, 20, 0.02, 3
FIRST_SCORED, MIN_CELL, BAR = 2020, 500, 0.005
SEED, DRAWS = 20261116, 1000
HALVES = ((2020, 2022), (2023, 2026))


def spy_closes(path):
    with gzip.open(path, "rt", newline="") as fh:
        return [(r["date"], float(r["close"])) for r in csv.DictReader(fh) if r["symbol"] == "SPY"]


def raw_label(cl, i):
    sma = sum(cl[i - SMA_N + 1 : i + 1]) / SMA_N
    ret = cl[i] / cl[i - RET_N] - 1
    if cl[i] >= sma and ret > BAND:
        return "bull"
    if cl[i] < sma and ret < -BAND:
        return "bear"
    return "sideways"


def sticky_labels(closes):
    """Label per date; a new raw label takes over on its STICK-th consecutive close."""
    days, cl = [d for d, _ in closes], [c for _, c in closes]
    out, cur, run_lab, run = {}, None, None, 0
    for i in range(SMA_N - 1, len(cl)):
        r = raw_label(cl, i)
        if cur is None:
            cur = r
        run, run_lab = (run + 1, r) if r == run_lab else (1, r)
        if r != cur and run >= STICK:
            cur = r
        out[days[i]] = cur
    return out


def load_cases(sim):
    cases = pickle.load(open(sim, "rb"))["cases"]
    return [c for c in cases if c.get("G_756") is not None]


def describe(lab, cases):
    days = sorted(lab)
    switches = sum(1 for a, b in zip(days, days[1:]) if lab[a] != lab[b])
    runs, n = [], 1
    for a, b in zip(days, days[1:]):
        if lab[a] == lab[b]:
            n += 1
        else:
            runs.append(n)
            n = 1
    runs.append(n)
    years = (int(days[-1][:4]) - int(days[0][:4])) or 1
    missing = sorted({c["day"] for c in cases if c["day"] not in lab})
    by_year = Counter((c["day"][:4], lab.get(c["day"])) for c in cases)
    return {
        "spy_labelled": [days[0], days[-1], len(days)],
        "switches": switches, "switches_per_year": round(switches / years, 1),
        "median_run_sessions": statistics.median(runs),
        "session_share": {k: round(sum(v == k for v in lab.values()) / len(lab), 3) for k in LABELS},
        "cases": len(cases), "case_dates_missing_from_spy": missing[:5], "n_missing": len(missing),
        "cases_by_year_label": {f"{y} {k}": n for (y, k), n in sorted(by_year.items())},
        "last_label": [days[-1], lab[days[-1]]],
    }


def corrected(P, Y, groups, train, test):
    """P + (realised - declared) learned on train, per group (pooled if a cell < MIN_CELL)."""
    pooled = Y[train].mean(0) - P[train].mean(0)
    out = P[test].copy()
    for g in np.unique(groups[test]):
        cell = train & (groups == g)
        shift = Y[cell].mean(0) - P[cell].mean(0) if cell.sum() >= MIN_CELL else pooled
        out[groups[test] == g] += shift
    out = np.clip(out, 1e-3, None)
    return out / out.sum(1, keepdims=True)


def score(cases, lab):
    P = np.array([c["G_756"] for c in cases], dtype=float)
    Y = np.eye(3)[[c["outcome"] for c in cases]]
    days = np.array([c["day"] for c in cases])
    years = np.array([int(d[:4]) for d in days])
    trend = np.array([lab[d] for d in days])
    vix = np.array([VIX_LABELS[c["regime"]] for c in cases])
    none = np.array(["all"] * len(cases))
    scored = years >= FIRST_SCORED
    F = {k: np.zeros_like(P) for k in ("R0", "R1", "R2", "clim", "clim_trend")}
    for y in sorted(set(years[scored])):
        test = years == y
        train = days < f"{y - 1}-12-15"
        F["R0"][test] = corrected(P, Y, none, train, test)
        F["R1"][test] = corrected(P, Y, trend, train, test)
        F["R2"][test] = corrected(P, Y, vix, train, test)
        zero = np.zeros_like(P)
        F["clim"][test] = corrected(zero, Y, none, train, test)
        F["clim_trend"][test] = corrected(zero, Y, trend, train, test)
    F["G"] = P
    idx = np.where(scored)[0]
    loss = {k: ((v[idx] - Y[idx]) ** 2).sum(1) for k, v in F.items()}
    d = days[idx]
    rng = np.random.default_rng(SEED)
    ud = np.unique(d)
    by = {u: np.where(d == u)[0] for u in ud}
    draws = [np.concatenate([by[u] for u in rng.choice(ud, len(ud))]) for _ in range(DRAWS)]

    def sk(a, b, sel=None):
        s = np.arange(len(idx)) if sel is None else sel
        point = 1 - loss[a][s].mean() / loss[b][s].mean()
        if sel is not None:
            return round(100 * point, 3)
        vals = [1 - loss[a][x].mean() / loss[b][x].mean() for x in draws]
        return [round(100 * point, 3), round(100 * np.percentile(vals, 2.5), 3),
                round(100 * np.percentile(vals, 97.5), 3)]

    yi = years[idx]
    halves = {f"{a}-{b}": sk("R1", "R0", np.where((yi >= a) & (yi <= b))[0]) for a, b in HALVES}
    primary = sk("R1", "R0")
    verdict = ("H1" if primary[0] >= 100 * BAR and primary[1] > 0 and min(halves.values()) > 0
               else "WORSE" if primary[2] < 0 else "H0")
    tr = trend[idx]
    per_label = {}
    for k in LABELS:
        s = tr == k
        per_label[k] = {"n": int(s.sum()), "realised": Y[idx][s].mean(0).round(3).tolist(),
                        "G_declared": P[idx][s].mean(0).round(3).tolist(),
                        "R1_over_R0_pct": sk("R1", "R0", np.where(s)[0])}
    return {
        "scored": [int(len(idx)), int(len(ud)), str(ud[0]), str(ud[-1])],
        "brier": {k: round(float(v.mean()), 5) for k, v in loss.items()},
        "primary_R1_over_R0_pct": primary, "halves_R1_over_R0_pct": halves, "verdict": verdict,
        "secondary_pct": {"R1_over_G": sk("R1", "G"), "R0_over_G": sk("R0", "G"),
                          "R2_over_R0": sk("R2", "R0"), "G_over_clim": sk("G", "clim"),
                          "clim_trend_over_clim": sk("clim_trend", "clim")},
        "per_label": per_label,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("count", "score"))
    ap.add_argument("--sim", type=Path, required=True)
    ap.add_argument("--spy", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    lab, cases = sticky_labels(spy_closes(a.spy)), load_cases(a.sim)
    if a.mode == "count":
        print(json.dumps(describe(lab, cases), indent=1))
        return 0
    if any(c["day"] not in lab for c in cases):
        raise SystemExit("refused: a decision date has no SPY label")
    result = score(cases, lab)
    a.out.write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
