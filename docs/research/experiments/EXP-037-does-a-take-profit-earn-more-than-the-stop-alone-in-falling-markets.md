# EXP-037 — Does a take-profit earn more than the stop alone in falling markets?

**Status:** PRE-REGISTERED 2026-10-27 (planner, `a68a5f76`) · COMPLETE 2026-10-27 · **H0: no sign a take-profit helps below SPY's trend; dR −15.61 pts a year [−48.85, +9.25], every exit behind on its point estimate**
**Decision / origin:** the operator, 2026-10-27, on the caveat that EXP-022's window was mostly a
rising market: *"that wud be great if we run an experiment"*; [DL-320](../../design-log.md) ·
**Cost:** $0 (EXP-022's sealed arms, read on this laptop)

## 1. Why we needed this experiment

[EXP-022](EXP-022-does-an-exit-besides-the-stop-make-the-book-earn-more.md) (final 2026-10-27) found
every exit besides the stop behind it over 2017–2026: the take-profit by −10.90 pts a year
[−21.72, −0.89] at 25 bps. The book earns from a few long holds, and a take-profit sells them early.
That window is mostly a rising market, which rewards holding. In a falling market there are few long
winners to cut, and a take-profit banks the rallies, so the sign could turn. ADR-0033 keeps the stop
alone until an experiment shows otherwise; this asks whether falling markets are that case.

A stock-level test of 2000–02 and 2007–09 was ruled out (DL-320): the replay cache starts
2016-01-04, and Tiingo serves no prices for the names that failed then (LEH, BSC, ENRNQ answer with
no dates; `WM` now means Waste Management), so that test would drop the worst losers.

## 2. Hypothesis

On **falling sessions**, a session whose previous SPY close sits below the mean of SPY's 200 closes
up to and including that one:

- **H1:** `target-25` (take-profit, 25 bps a side) earns more than `stops-25` (the stop alone, same
  cost): dR, the difference in annualised return on falling sessions, has a 95 % interval wholly
  above 0.
- **BEHIND:** the interval is wholly below 0. **H0:** otherwise (indistinguishable).
- **Reported, no bar:** the same dR for `target-10`, `time10-25`, `trail-25`, `target-time10-25`,
  `cool5-25` (each against the stops arm of its cost); the primary pair on rising sessions; each
  arm's mean exposure and SPY's annualised return on falling and rising sessions.

**What follows, fixed now:** on H1, the planner specs a regime-switched arm (take-profit only while
SPY sits below its 200-session mean) for the S281 harness, and the operator decides whether to build
it; nothing in the fleet changes on this result alone, because every cached session has been read.
On H0 or BEHIND, the stop alone stays (ADR-0033), and the question reopens only with survivorship-free
stock data before 2016.

## 3. Data

- **EXP-022's twelve sealed arms**, OneDrive `exp022-2026-10-21/arms/`: each `equity.csv` (date,
  `equity_cents`, `long_cents`), 2017-01-03 → 2026-09-25, from the real pipeline at `v0.128.06` on
  the survivorship-free S&P 500 cache. Seal `seal.txt` SHA-256 `020ebb5e…`, re-hashed before scoring.
- **SPY closes**, `sp500_benchmark.csv.gz` (SHA-256 `f40b8b60…`), 2016-01-04 →, so the 200-session
  mean exists from the first scored session.
- **The split, measured from SPY alone before any arm is read:** 2,445 session pairs; **404 falling**
  (2018: 43, 2019: 28, 2020: 59, 2022: 203, 2023: 17, 2025: 42, 2026: 12), 2,041 rising.
- **Seen before:** EXP-022's verdict (read 2026-10-26) gave each arm's whole-window and half-window
  dR, and its report has a per-year table; 2022 holds half the falling sessions. So this is a
  fixed-rule reading of arms already scored, not a blind test, and it cannot confirm anything alone.

## 4. Tools and setup

Intel i7-7660U, Windows 10, Python 3.12 (`python -I`, standard library only). Script
`exp037_score.py` in OneDrive `exp037-2026-10-27/`, SHA-256 `8a4f2096…` (Appendix S). Stationary
bootstrap as EXP-022's: 10,000 resamples, mean block 20, seed 0, one draw for every pair in a
family, percentile interval. Annualised return = exp(mean daily log return × 252) − 1, in points.

## 5. How it was conducted

1. `count` mode reads SPY only and prints the split (section 3). Done before this commit.
2. This record is committed: the pre-registration.
3. The EXP-022 seal is re-hashed (72 of 72 lines must match), then `score` runs once. It refuses if
   any arm lacks a window session.
4. Each arm's daily log return on session *t* is log(equity *t* / equity *t−1*); exposure is
   `long_cents / equity_cents` at *t−1*. The falling sessions are bootstrapped as one sequence.
5. Sections 6–8 are written from the output, with no change to the rule.

## 6. Results

All MEASURED, `exp037.json` (SHA-256 `ec37e5a8…`), one run.

- **Primary, falling sessions (404): H0.** `target-25` − `stops-25`: dR = **−15.61 pts a year,
  95 % interval [−48.85, +9.25]**. The take-profit arm earned −0.44 % a year on those sessions, the
  stop alone +15.16 %; mean exposure 16 % against 74 %.
- **SPY on the falling sessions earned +21.06 % a year** (on rising sessions +14.16 %). In this
  window, sessions below the 200-session mean were mostly rebounds: 2020's recovery, 2022's rallies,
  April 2025.
- **Secondaries, falling sessions, no bar:**

  | Exit − stops | dR, pts a year | 95 % interval | Exposure |
  | --- | --- | --- | --- |
  | `target-10` − `stops-10` | −14.20 | [−47.52, +10.59] | 17 % vs 74 % |
  | `time10-25` | −15.50 | [−49.26, +9.72] | 17 % |
  | `trail-25` | −14.62 | [−48.19, +10.72] | 18 % |
  | `target-time10-25` | −15.83 | [−49.02, +8.82] | 15 % |
  | `cool5-25` | −4.34 | [−8.17, −1.56] | 70 % |

- **Rising sessions (2,041), primary pair:** dR −9.99 [−17.17, −3.10], behind, as EXP-022 found.

## 7. Conclusions

There is no sign that a take-profit helps when SPY is below its trend: every exit is behind on its
point estimate, and the interval is wide because 404 sessions are few. The reason is EXP-022's
again: the stop alone stays invested (74 %) through the rebounds that follow a break below trend,
while the exits sit mostly in cash (15–18 %).

What it does not say: this window has no long grinding decline like 2000–02 or 2007–09; SPY rose on
these sessions. A test of that needs survivorship-free stock data before 2016, which we do not have
(DL-320). The reading is also not blind (section 3).

## 8. Recommended code changes, and how to implement them

None. By the rule fixed in section 2, on H0 the stop alone stays
([ADR-0033](../../decisions/0033-the-fleet-is-a-paper-test-bed.md) decision 4), and the question
reopens only with survivorship-free stock data before 2016. The fleet's defence in a long decline is
better sought in the 200-day trend guard (EXP-025, EXP-026), not in a take-profit.

## Appendix P — Pre-registration (frozen)

Primary: dR = annualised return of `target-25` minus `stops-25` over EXP-022's falling sessions (the
previous SPY close below the mean of its last 200 closes), 404 sessions; stationary bootstrap 10,000,
mean block 20, seed 0. H1 if the 95 % interval's lower bound > 0, BEHIND if its upper bound < 0, H0
otherwise. Secondaries reported without a bar. H1 → a regime-switched arm is specced, the operator
decides on building; H0 or BEHIND → the stop alone stays. Script SHA-256
`8a4f20962f8118c81b902a2795eb833dcc0b6d3168162cfb0d3fb16e6e7076b5`.

## Appendix R — Run record

2026-10-27 ~19:25 AEDT, this laptop. EXP-022's seal re-hashed first: 72 of 72 lines match
(`seal.txt` `020ebb5e…`). Script SHA-256 `8a4f2096…` (= Appendix P). `score` ran once in 9.9 s,
exit 0; output `exp037.json` SHA-256 `ec37e5a8d77e3698…` and `score.log`, in OneDrive
`exp037-2026-10-27/`. No defect found; nothing re-run.

## Appendix S — Scripts

`exp037_score.py`, OneDrive `exp037-2026-10-27/`; run from that folder:
`python -I exp037_score.py count --spy ../sp500_benchmark.csv.gz`, then
`python -I exp037_score.py score --spy ../sp500_benchmark.csv.gz --arms ../exp022-2026-10-21/arms --out exp037.json`.

```python
"""EXP-037: does a take-profit earn more than the stop alone in falling markets?

Reads EXP-022's sealed arms (equity.csv) and SPY's closes; scores each exit arm against the stops
arm of its cost on the sessions where SPY's previous close sat below its 200-session mean.

  python -I exp037_score.py count --spy <sp500_benchmark.csv.gz>
  python -I exp037_score.py score --spy <sp500_benchmark.csv.gz> --arms <exp022 arms dir> --out <json>

`count` reads SPY only (the regime split), never an arm. Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import random
import sys
from pathlib import Path

FIRST, LAST = "2017-01-03", "2026-09-25"  # EXP-022's window
SMA = 200
RESAMPLES, MEAN_BLOCK, SEED = 10_000, 20, 0  # EXP-022's interval
YEAR = 252
PRIMARY = ("target-25", "stops-25")
SECONDARY = (
    ("target-10", "stops-10"),
    ("time10-25", "stops-25"),
    ("trail-25", "stops-25"),
    ("target-time10-25", "stops-25"),
    ("cool5-25", "stops-25"),
)


def spy_closes(path: Path) -> list[tuple[str, float]]:
    with gzip.open(path, "rt", newline="") as fh:
        rows = [(r["date"], float(r["close"])) for r in csv.DictReader(fh) if r["symbol"] == "SPY"]
    return sorted(rows)


def falling_by_session(closes: list[tuple[str, float]]) -> dict[str, bool]:
    """Session -> True when the PREVIOUS session's close is below the mean of its last 200 closes."""
    out: dict[str, bool] = {}
    for i in range(SMA, len(closes)):
        prev = [c for _, c in closes[i - SMA : i]]
        out[closes[i][0]] = closes[i - 1][1] < sum(prev) / SMA
    return out


def arm_returns(arms: Path, name: str) -> dict[str, tuple[float, float]]:
    """Session -> (log return of equity from the previous session, previous session's exposure)."""
    with (arms / name / "equity.csv").open(newline="") as fh:
        rows = [(r["date"], int(r["equity_cents"]), int(r["long_cents"])) for r in csv.DictReader(fh)]
    out = {}
    for (_, e0, l0), (d1, e1, _) in zip(rows, rows[1:]):
        out[d1] = (math.log(e1 / e0), l0 / e0)
    return out


def stationary_draws(count: int, rng: random.Random) -> list[int]:
    """One stationary-bootstrap resample (scripts/replay_verdict_stats.py, copied)."""
    restart = 1.0 / MEAN_BLOCK
    index = rng.randrange(count)
    draws = [index]
    while len(draws) < count:
        index = rng.randrange(count) if rng.random() < restart else (index + 1) % count
        draws.append(index)
    return draws


def annual(logs: list[float]) -> float:
    return 100.0 * (math.exp(sum(logs) * YEAR / len(logs)) - 1.0)


def family(sessions: list[str], pairs: list[tuple[str, str]], arm: dict) -> dict:
    rng = random.Random(SEED)
    n = len(sessions)
    series = {name: [arm[name][s][0] for s in sessions] for p in pairs for name in p}
    diffs: dict[str, list[float]] = {f"{a} - {b}": [] for a, b in pairs}
    for _ in range(RESAMPLES):
        order = stationary_draws(n, rng)  # one draw for every pair
        for a, b in pairs:
            ra = annual([series[a][i] for i in order])
            rb = annual([series[b][i] for i in order])
            diffs[f"{a} - {b}"].append(ra - rb)
    out = {"sessions": n}
    for a, b in pairs:
        key = f"{a} - {b}"
        draws = sorted(diffs[key])
        out[key] = {
            "dR_pts": annual(series[a]) - annual(series[b]),
            "interval": [draws[int(0.025 * RESAMPLES)], draws[int(0.975 * RESAMPLES) - 1]],
            "R_challenger": annual(series[a]),
            "R_stops": annual(series[b]),
            "exposure_challenger": sum(arm[a][s][1] for s in sessions) / n,
            "exposure_stops": sum(arm[b][s][1] for s in sessions) / n,
        }
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("count", "score"))
    ap.add_argument("--spy", type=Path, required=True)
    ap.add_argument("--arms", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    closes = spy_closes(a.spy)
    falling = falling_by_session(closes)
    window = [d for d, _ in closes if FIRST < d <= LAST]  # first pair ends on the second session
    fall = [d for d in window if falling[d]]
    rise = [d for d in window if not falling[d]]
    counts = {"window_sessions": len(window), "falling": len(fall), "rising": len(rise)}
    years: dict[str, int] = {}
    for d in fall:
        years[d[:4]] = years.get(d[:4], 0) + 1
    counts["falling_by_year"] = years
    if a.mode == "count":
        print(json.dumps(counts, indent=1))
        return 0
    names = {n for p in (PRIMARY, *SECONDARY) for n in p}
    arm = {n: arm_returns(a.arms, n) for n in sorted(names)}
    for n, series in arm.items():
        missing = [d for d in window if d not in series]
        if missing:
            raise SystemExit(f"{n}: {len(missing)} window sessions missing, first {missing[0]}")
    spy = dict(closes)
    spy_log = {d1: math.log(spy[d1] / spy[d0]) for (d0, _), (d1, _) in zip(closes, closes[1:])}
    result = {
        "counts": counts,
        "spy_R": {"falling": annual([spy_log[d] for d in fall]), "rising": annual([spy_log[d] for d in rise])},
        "falling": family(fall, [PRIMARY, *SECONDARY], arm),
        "rising": family(rise, [PRIMARY], arm),
    }
    p = result["falling"][f"{PRIMARY[0]} - {PRIMARY[1]}"]
    result["verdict"] = "H1" if p["interval"][0] > 0 else ("BEHIND" if p["interval"][1] < 0 else "H0")
    a.out.write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```
