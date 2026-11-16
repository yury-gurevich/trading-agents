# EXP-040 — Does selling a held stock the analyst would not buy today earn more, or lose less, than the stop alone?

**Status:** PRE-REGISTERED 2026-11-16 (planner, `e33e5108`) · COMPLETE 2026-11-16 · **BEHIND: selling what the analyst would not buy today earns 9.47 pts a year less than the stop alone, 95 % interval [−17.31, −2.14], behind in both halves; the floor stays 0.50**
**Decision / origin:** the operator, 2026-11-16: *"for the stock i have purchased in the past - would i buy
it today? Does it trend in the growth direction? If not then we have to sell to minimise loss. Am i
right?"*, then *"check that this can run at $0 with the existing harness and pre-register it"*;
[DL-323](../../design-log.md); work-queue 92 (DL-240) · **Cost:** $0 (the replay on this laptop, about
five hours of machine time)

## 1. Why we needed this experiment

The operator's rule for a held stock is to ask each day whether the fleet would buy it today, and to sell
when it would not. The fleet has that exit ([ADR-0017](../../decisions/0017-exit-authority-alpha-proposes-risk-disposes.md)):
the analyst sells a held name whose confidence falls below `exit_confidence_floor`. It buys at a
confidence of 0.60 or more (`base_min_confidence`).

**Measured 2026-11-16, and it corrects DL-240:** the floor is **0.50**, in the code default and in the
pack (`ANALYST_EXIT_CONFIDENCE_FLOOR`), not 0 as DL-240 recorded. On the live graph, of 2,396 hold
recommendations the lowest confidence is 0.509, so the exit has never been reachable at 0.50; 317 holds
(13.2 %) sit below 0.60, the names the fleet held and would not have bought that day, and 28 below 0.55.
(Ten recorded thesis sells all belong to one run, at confidences of 0.59 to 0.71: a run under another
floor, *[not investigated]*.) In EXP-022's sealed stops arm the 0.50 floor sold 13 times in ten years, at
+158.7 % on average after a median 862 sessions: it sold old winners, not losers.

Earlier evidence leans against the rule without testing it: the analyst's score does not rank names
([EXP-023](EXP-023-which-of-the-technical-scores-rules-carry-its-rank-ic.md)), and every exit besides the
stop earned less ([EXP-022](EXP-022-does-an-exit-besides-the-stop-make-the-book-earn-more.md)). Neither ran
the rule itself. The harness can: the floor is one setting, an arm carries overrides, and the replay
already fills the analyst's sells.

## 2. Hypothesis

**Arms**, each the real pipeline on the S235 cache, 2017-01-03 → 2026-09-25, differing from the champion
only in the floor:

| Arm | `ANALYST_EXIT_CONFIDENCE_FLOOR` | Cost a side | Scored against |
| --- | --- | --- | --- |
| `thesis60-25` (primary) | 0.60: sell what would not be bought today | 25 bps | EXP-022's sealed `stops-25` (0.50) |
| `thesis55-25` | 0.55: a margin against selling and re-buying | 25 bps | sealed `stops-25` |
| `thesis60-10` | 0.60 | 10 bps | sealed `stops-10` |
| `stops-25` (control) | 0.50 | 25 bps | must reproduce the sealed `stops-25` |

**Statistic:** dR, the arm's annualised return minus the stops arm's, EXP-022's.

- **AHEAD:** the 95 % interval of dR for `thesis60-25` lies above 0, and dR is above 0 in each half of
  the window (the session pairs cut in two).
- **BEHIND:** the interval lies below 0. **H0:** otherwise.

**Reported, no bar** (the operator asks about loss, so these are read beside dR): each arm's maximum
drawdown, average exposure and buys a year; round trips by the reason that closed them (count, share
losing, mean return, mean loss of the losers, worst, median sessions held); the secondaries' dR, interval
and halves.

**What follows, fixed now:** on AHEAD the planner proposes moving the live floor, a pack edit that
changes trading and restarts the fidelity count: the operator's decision. On H0 or BEHIND the floor stays
0.50 and the rule is closed for the price-only pipeline. A shallower drawdown that comes only with lower
exposure is not counted as protection: it is the same book held smaller.

## 3. Data

- **The S235 cache**, OneDrive `trading-agents-data`, as EXP-022 §3 froze it (seven files, checksums in
  every `arm.json`; the scorer refuses an arm whose commit, cache or sessions differ from its baseline's).
  Licensed SIP bars: never in the repo.
- **EXP-022's sealed arms** `stops-25` and `stops-10`, OneDrive `exp022-2026-10-21/arms/` (seal
  `020ebb5ed68cedc6…`, the two arms' twelve files re-hashed before scoring).
- **Seen before:** all of EXP-022's results, including both baselines. The thesis arms have never run on
  the scored window.
- **Pilot, before this commit, outside the scored window:** `thesis60-25` over 2016-03-01 → 2016-12-30
  with the history rule off: 498 buys, **309 thesis sells**, 163 stops, in 271 s. The override reaches
  the analyst and the replay sells on it. Only fill counts were read.
- **Scorer self-test, before this commit, on sealed arms only:** `target-25 − stops-25` = −10.90 pts a
  year, EXP-022's published figure; `stops-25` R +10.64 %, exposure 75.8 %, 604 stops at −5.69 %.

## 4. Tools and setup

Intel Core i7-7660U (2 cores / 4 threads), 16 GB, Windows 10 Pro 19045. Arms: the pinned clean checkout
`ta-exp022` at `f7e7ac21` (`v0.128.06`, the commit of EXP-022's arms and of the fidelity PASS), Python
3.13.2, uv 0.8.14, `uv run --no-sync`. Scorer: Python 3.12.2, `python -I`, standard library only.
Bootstrap as EXP-022's: stationary, mean block 20, 10,000 resamples, seed 0, one draw for every pair;
percentile 95 %. The replay has no randomness. No network, no LLM, no broker. Kit in OneDrive
`trading-agents-data/exp040-2026-11-16/`, checksums in Appendix P.

## 5. How it was conducted

1. Pilot and scorer self-test (section 3). Done before this commit.
2. This record is committed: the pre-registration.
3. `run_exp040_arms.ps1` (EXP-022's runner with this kit's manifest) runs the four arms from the pinned
   checkout, one at a time at below-normal priority, strips the equity figure from every log line and
   seals the outputs by SHA-256. A failed or interrupted arm is re-run whole.
4. The EXP-022 seal's lines for `stops-25` and `stops-10` are re-hashed. Then `score` runs once. It refuses
   unless the control's `equity.csv` equals the sealed one byte for byte.
5. Sections 6–8 are written from the output, with no change to the rule.

**What this cannot claim, stated before the result.** It speaks for the price-only pipeline: the replay's
confidence comes from the technical score alone, where the live one also reads fundamentals and sentiment.
The replayed book is about 76 % invested, far more than the live book, so freed capital is re-spent
sooner than live. A thesis sale is a DAY limit on the next session and may not fill. One decade, which
rewarded holding. It does not test "sell when the stock's own trend turns down" as a separate rule: the
technical score carries trend, but that rule alone would need a new arm kind.

## 6. Results

All MEASURED, `exp040.json` (SHA-256 `4cb85e200c55…`), one scored run over 2,445 session pairs,
2017-01-03 → 2026-09-25. The control reproduced the sealed `stops-25` byte for byte.

- **Primary: BEHIND.** `thesis60-25` earned **+1.17 % a year** against `stops-25`'s **+10.64 %**:
  **dR = −9.47 pts a year, 95 % interval [−17.31, −2.14]**; first half −7.28, second half −11.69.
- **Secondaries, no bar:** both also lie below zero.

  | Pair | dR, pts a year | 95 % interval | First half | Second half |
  | --- | --- | --- | --- | --- |
  | `thesis60-25` − `stops-25` (primary) | **−9.47** | [−17.31, −2.14] | −7.28 | −11.69 |
  | `thesis55-25` − `stops-25` | −6.17 | [−12.07, −0.83] | −4.87 | −7.49 |
  | `thesis60-10` − `stops-10` | −8.43 | [−16.14, −1.18] | −6.29 | −10.61 |

- **The arms:**

  | Arm | Return a year | Average exposure | Maximum drawdown | Buys a year | Round trips | Share losing | Mean trip |
  | --- | --- | --- | --- | --- | --- | --- | --- |
  | `stops-25` (floor 0.50) | +10.64 % | 75.8 % | −22.92 % | 70 | 629 | 96.5 % | −1.77 % |
  | `thesis55-25` | +4.47 % | 44.2 % | −13.98 % | 150 | 1,418 | 79.3 % | +1.83 % |
  | `thesis60-25` | +1.17 % | 23.5 % | −11.45 % | 475 | 4,595 | 56.8 % | +0.24 % |
  | `stops-10` (floor 0.50) | +11.01 % | 76.1 % | −23.14 % | 68 | 608 | 96.5 % | −1.50 % |
  | `thesis60-10` | +2.58 % | 23.8 % | −8.51 % | 470 | 4,541 | 53.4 % | +0.55 % |

- **Round trips by what closed them** (25 bps arms; `limit` is the thesis sale):

  | Arm | Closed by | Trips | Share losing | Mean return | Mean loss of the losers | Worst | Median sessions held |
  | --- | --- | --- | --- | --- | --- | --- | --- |
  | `stops-25` | stop | 604 | 100 % | −5.69 % | −5.69 % | −24.91 % | 18 |
  | `stops-25` | thesis sale | 13 | 0 % | +158.68 % | none | +2.56 % | 862 |
  | `thesis55-25` | stop | 1,106 | 100 % | −6.06 % | −6.06 % | −30.22 % | 11 |
  | `thesis55-25` | thesis sale | 296 | 4.1 % | +31.22 % | −0.84 % | −2.49 % | 161.5 |
  | `thesis60-25` | stop | 1,802 | 100 % | −5.85 % | −5.85 % | −24.91 % | 5 |
  | `thesis60-25` | thesis sale | 2,781 | 28.9 % | +4.18 % | −1.35 % | −6.78 % | 5 |

  The remaining trips of each arm (index removals and positions open at the end of the data, 12 to 16 an
  arm) are in Appendix R.

- **Loss, the operator's question.** The rule did not sell losers: **71 % of the 2,781 thesis sales at
  0.60 were at a gain**, and the ones at a loss averaged −1.35 %. The losses still left through the
  stop, at the same average (−5.85 % against −5.69 %) and the same worst trip (−24.91 %), and there were
  **three times as many of them** (1,802 against 604), because the freed money bought again and each
  new buy could stop out. At 0.55 the worst trip was deeper (−30.22 %).
- **The drawdown is the smaller book, not protection** (derived after the run by division, not
  pre-registered). `thesis60-25`'s drawdown is half the stop arm's on less than a third of the
  exposure: per unit of exposure it is deeper (11.45 / 23.5 = 0.49 against 22.92 / 75.8 = 0.30), and so
  is `thesis55-25`'s (0.32). By the sentence fixed in section 2 this is not counted as protection.
- **Unexpected:** the size of the turnover. At 0.60 the median holding fell from 18 sessions to 5 and
  the buys rose from 70 to 475 a year, yet the book sat 76 % in cash. *[not investigated]* why the
  freed cash was not re-spent faster. Cost is not the cause of the verdict: at 10 bps a side the gap
  is −8.43 pts.

## 7. Conclusions

Selling a held name the analyst would not buy today earns less than the stop alone, by about nine and a
half points a year, in both halves of the decade, at both floors and at both costs. The rule is closed
for the price-only pipeline, as section 2 fixed.

Why, in the stop arm's own figures: 604 of its 629 trips end at the stop for −5.69 %, and its whole
profit comes from the few it never sells, 13 names held a median 862 sessions for +158.68 %. A name's
confidence falls below 0.60 within days of the buy, so the rule sells those names too, at +4.18 % after
five sessions. It turns the book into the operator's intended style (hold about a week, take a small
gain) and that book is close to flat: six trips in ten take +4.18 %, four in ten stop at −5.85 %, and
the mean trip is +0.24 % after cost.

The answer to the operator's question is in two parts. *Cap the loss:* the stop already does it, and
this rule did not make the loss smaller, per trip or at worst. *Would I buy it today:* the question is
sound, but the analyst's confidence is not a measure that answers it. It does not rank names
([EXP-023](EXP-023-which-of-the-technical-scores-rules-carry-its-rank-ic.md)), so a fall below 0.60 says
little about what the stock does next, and acting on it sells what was working.

With [EXP-022](EXP-022-does-an-exit-besides-the-stop-make-the-book-earn-more.md) (take-profit and time
exit, both behind) and
[EXP-037](EXP-037-does-a-take-profit-earn-more-than-the-stop-alone-in-falling-markets.md) (a take-profit
in falling markets, H0), every exit rule the replay can run has now been measured behind or level with
the stop alone. An exit reshapes what the buys earn; it does not add to it. A week-long, small-gain
style needs buys that win clearly more often than the six in ten measured here (break-even at these
sizes is 58 in 100), which is an entry signal the fleet does not have.

What this does not say: nothing about the live confidence, which also reads fundamentals and sentiment;
nothing about a rule on the stock's own trend alone; and one decade that rewarded holding.

## 8. Recommended code changes, and how to implement them

None. By the rule fixed in section 2, on BEHIND `ANALYST_EXIT_CONFIDENCE_FLOOR` stays 0.50 in the pack
and the code default, and no sprint follows. The live exit stays as it is: reachable only by a
confidence the fleet has not yet produced (lowest live hold 0.509).

The next measurement is on the buy side, at the operator's horizon: whether any signal available at $0
picks names that rise over the next five to ten sessions. That is a new experiment and the operator's
call to start.

## Appendix P — Pre-registration (frozen)

Primary: dR = annualised return of `thesis60-25` (`ANALYST_EXIT_CONFIDENCE_FLOOR=0.60`, 25 bps) minus
EXP-022's sealed `stops-25`, 2017-01-03 → 2026-09-25, pinned commit `f7e7ac21`; stationary bootstrap
10,000, mean block 20, seed 0, 95 % percentile interval. AHEAD if the lower bound > 0 and dR > 0 in each
half; BEHIND if the upper bound < 0; H0 otherwise. Secondaries `thesis55-25` (0.55) against `stops-25`
and `thesis60-10` against `stops-10`, and the loss measures, reported without a bar. Control: the re-run
`stops-25` must reproduce the sealed `equity.csv`. AHEAD → the planner proposes the live floor, the
operator decides; H0 or BEHIND → the floor stays 0.50. SHA-256: `exp040_arms.json`
`0682821461d0247a1e4c4ff3728441852741b81af2abbc98e84a66285cb1af6a`, `exp040_score.py`
`64b54c46d5f62ac40aa533f15de10c4444a292b22d307fa62267f7475c27f7d6`, `run_exp040_arms.ps1`
`3b712efc0b9aba04d39af91f0c77e0d70f8ca9945abb85321b03baf97e0c8023`.

## Appendix R — Run record

2026-11-16, this laptop. Pilot and scorer self-test ran before the pre-registration (section 3).

**Arms.** `run_exp040_arms.ps1` from the pinned checkout (`f7e7ac21bf7c…`, clean), one arm at a time.
Runner START 03:12:25Z, SEALED 07:38:11Z (4 h 26 min), exit 0; every arm exit 0 on its first attempt,
2,446 sessions each.

| Arm | Started (UTC) | Ended (UTC) | Replay seconds |
| --- | --- | --- | --- |
| `stops-25` (control) | 03:12:25 | 04:21:21 | 4,120 |
| `thesis60-25` | 04:21:21 | 05:24:47 | 3,792 |
| `thesis55-25` | 05:24:47 | 06:32:03 | 4,022 |
| `thesis60-10` | 06:32:03 | 07:38:11 | 3,948 |

**Seal.** `seal.txt`, 24 files, SHA-256 `878d1b0f236e03cb9b8136f006f5d112395cdb4990d53d3028f94fe14869ad63`;
all 24 re-hashed against it before scoring, none differed. EXP-022's seal (`020ebb5ed68cedc6…`, 72
lines): the twelve lines of `stops-25` and `stops-10` re-hashed, all equal.

**Control.** The re-run `stops-25` equals the sealed arm in `equity.csv` (`47ae6f5c79cf…`),
`fills.csv`, `sessions.csv`, `summary.json` and `benchmark.csv`; `arm.json` differs only in the
experiment's name. The replay is deterministic at this commit and cache.

**Kit.** `exp040_arms.json`, `exp040_score.py` and `run_exp040_arms.ps1` re-hashed after the arms and
before scoring: the three SHA-256 of Appendix P, unchanged. No defect, no re-run, no edit.

**Score.** `python -I exp040_score.py score --sealed ../exp022-2026-10-21/arms --arms arms --out
exp040.json`, run once, exit 0. `exp040.json` SHA-256
`4cb85e200c55395c608e0709403dd1f1bb301dd36c08c987bf00c9fd4966d117`, `score.log`
`549d2b6234f874682c826d79462b1875761f21dbec86107f2b08495166624a07`, both in OneDrive
`trading-agents-data/exp040-2026-11-16/`. The content of `exp040.json`, laid out one row a line (checked
equal to the file after parsing):

```json
{
 "control_stops25_equity_identical": true,
 "verdict": "BEHIND",
 "sessions": 2445,
 "pairs": {
  "thesis60-25 - stops-25": {"dR_pts": -9.47, "interval_95": [-17.31, -2.14], "first_half": -7.28, "second_half": -11.69, "verdict": "BEHIND"},
  "thesis55-25 - stops-25": {"dR_pts": -6.17, "interval_95": [-12.07, -0.83], "first_half": -4.87, "second_half": -7.49, "verdict": "BEHIND"},
  "thesis60-10 - stops-10": {"dR_pts": -8.43, "interval_95": [-16.14, -1.18], "first_half": -6.29, "second_half": -10.61, "verdict": "BEHIND"}
 },
 "arms": {
  "stops-25": {"R_pct_a_year": 10.64, "exposure_pct": 75.8, "max_drawdown_pct": -22.92, "buys_a_year": 70, "round_trips": {
    "data_end": {"trips": 6, "share_losing": 0.333, "mean_return_pct": 25.68, "mean_loss_of_losers_pct": -0.33, "worst_pct": -0.38, "median_sessions": 187.0},
    "limit": {"trips": 13, "share_losing": 0.0, "mean_return_pct": 158.68, "mean_loss_of_losers_pct": null, "worst_pct": 2.56, "median_sessions": 862},
    "membership_end": {"trips": 6, "share_losing": 0.167, "mean_return_pct": 17.66, "mean_loss_of_losers_pct": -2.51, "worst_pct": -2.51, "median_sessions": 32.5},
    "stop": {"trips": 604, "share_losing": 1.0, "mean_return_pct": -5.69, "mean_loss_of_losers_pct": -5.69, "worst_pct": -24.91, "median_sessions": 18.0},
    "all": {"trips": 629, "share_losing": 0.965, "mean_return_pct": -1.77, "worst_pct": -24.91}
  }},
  "stops-10": {"R_pct_a_year": 11.01, "exposure_pct": 76.1, "max_drawdown_pct": -23.14, "buys_a_year": 68, "round_trips": {
    "data_end": {"trips": 6, "share_losing": 0.333, "mean_return_pct": 26.77, "mean_loss_of_losers_pct": -0.17, "worst_pct": -0.21, "median_sessions": 237.0},
    "limit": {"trips": 12, "share_losing": 0.0, "mean_return_pct": 170.55, "mean_loss_of_losers_pct": null, "worst_pct": 2.87, "median_sessions": 902.0},
    "membership_end": {"trips": 6, "share_losing": 0.167, "mean_return_pct": 18.22, "mean_loss_of_losers_pct": -2.37, "worst_pct": -2.37, "median_sessions": 32.5},
    "stop": {"trips": 584, "share_losing": 1.0, "mean_return_pct": -5.53, "mean_loss_of_losers_pct": -5.53, "worst_pct": -24.69, "median_sessions": 18.0},
    "all": {"trips": 608, "share_losing": 0.965, "mean_return_pct": -1.5, "worst_pct": -24.69}
  }},
  "thesis60-25": {"R_pct_a_year": 1.17, "exposure_pct": 23.5, "max_drawdown_pct": -11.45, "buys_a_year": 475, "round_trips": {
    "data_end": {"trips": 6, "share_losing": 0.5, "mean_return_pct": 1.65, "mean_loss_of_losers_pct": -1.53, "worst_pct": -4.15, "median_sessions": 5.5},
    "limit": {"trips": 2781, "share_losing": 0.289, "mean_return_pct": 4.18, "mean_loss_of_losers_pct": -1.35, "worst_pct": -6.78, "median_sessions": 5},
    "membership_end": {"trips": 6, "share_losing": 0.167, "mean_return_pct": 2.74, "mean_loss_of_losers_pct": -4.41, "worst_pct": -4.41, "median_sessions": 14.0},
    "stop": {"trips": 1802, "share_losing": 1.0, "mean_return_pct": -5.85, "mean_loss_of_losers_pct": -5.85, "worst_pct": -24.91, "median_sessions": 5.0},
    "all": {"trips": 4595, "share_losing": 0.568, "mean_return_pct": 0.24, "worst_pct": -24.91}
  }},
  "thesis55-25": {"R_pct_a_year": 4.47, "exposure_pct": 44.2, "max_drawdown_pct": -13.98, "buys_a_year": 150, "round_trips": {
    "data_end": {"trips": 9, "share_losing": 0.444, "mean_return_pct": 3.93, "mean_loss_of_losers_pct": -1.25, "worst_pct": -4.15, "median_sessions": 54},
    "limit": {"trips": 296, "share_losing": 0.041, "mean_return_pct": 31.22, "mean_loss_of_losers_pct": -0.84, "worst_pct": -2.49, "median_sessions": 161.5},
    "membership_end": {"trips": 7, "share_losing": 0.286, "mean_return_pct": 1.94, "mean_loss_of_losers_pct": -3.46, "worst_pct": -4.41, "median_sessions": 17},
    "stop": {"trips": 1106, "share_losing": 1.0, "mean_return_pct": -6.06, "mean_loss_of_losers_pct": -6.06, "worst_pct": -30.22, "median_sessions": 11.0},
    "all": {"trips": 1418, "share_losing": 0.793, "mean_return_pct": 1.83, "worst_pct": -30.22}
  }},
  "thesis60-10": {"R_pct_a_year": 2.58, "exposure_pct": 23.8, "max_drawdown_pct": -8.51, "buys_a_year": 470, "round_trips": {
    "data_end": {"trips": 6, "share_losing": 0.5, "mean_return_pct": 1.81, "mean_loss_of_losers_pct": -1.38, "worst_pct": -4.01, "median_sessions": 5.5},
    "limit": {"trips": 2799, "share_losing": 0.247, "mean_return_pct": 4.42, "mean_loss_of_losers_pct": -1.29, "worst_pct": -6.5, "median_sessions": 5},
    "membership_end": {"trips": 6, "share_losing": 0.167, "mean_return_pct": 2.89, "mean_loss_of_losers_pct": -4.26, "worst_pct": -4.26, "median_sessions": 14.0},
    "stop": {"trips": 1730, "share_losing": 1.0, "mean_return_pct": -5.72, "mean_loss_of_losers_pct": -5.72, "worst_pct": -24.69, "median_sessions": 5.0},
    "all": {"trips": 4541, "share_losing": 0.534, "mean_return_pct": 0.55, "worst_pct": -24.69}
  }}
 }
}
```

## Appendix S — Scripts

Kit: OneDrive `trading-agents-data/exp040-2026-11-16/`. Arms: `pwsh -File run_exp040_arms.ps1` (EXP-022's
`run_exp022_arms.ps1` with the kit folder and an absolute manifest path; four lines differ). Scoring,
from the kit folder: `python -I exp040_score.py selftest --sealed ../exp022-2026-10-21/arms`, then
`python -I exp040_score.py score --sealed ../exp022-2026-10-21/arms --arms arms --out exp040.json`.

### `exp040_arms.json`

```json
{
  "arms": [
    {"name": "stops-25", "overrides": [], "slippage_bps": 25},
    {"name": "thesis60-25", "overrides": ["ANALYST_EXIT_CONFIDENCE_FLOOR=0.60"], "slippage_bps": 25},
    {"name": "thesis55-25", "overrides": ["ANALYST_EXIT_CONFIDENCE_FLOOR=0.55"], "slippage_bps": 25},
    {"name": "thesis60-10", "overrides": ["ANALYST_EXIT_CONFIDENCE_FLOOR=0.60"], "slippage_bps": 10}
  ],
  "experiment": "EXP-040",
  "require_history": true,
  "start": "2017-01-03"
}
```

### `exp040_score.py`

```python
"""EXP-040: does selling a held name the analyst would not buy today beat the stop alone?

Reads replay arms (equity.csv, fills.csv, arm.json): the thesis arms of this experiment and the
sealed stops arms of EXP-022, and scores each thesis arm against the stops arm of its cost.

  python -I exp040_score.py selftest --sealed <exp022 arms dir>
  python -I exp040_score.py score --sealed <exp022 arms dir> --arms <exp040 arms dir> --out <json>

`selftest` reads EXP-022's sealed arms only and must reproduce its published dR for `target-25`
(-10.90 pts a year). Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import statistics
import sys
from pathlib import Path

RESAMPLES, MEAN_BLOCK, SEED = 10_000, 20, 0  # EXP-022's bootstrap
YEAR = 252
PRIMARY = ("thesis60-25", "stops-25")
SECONDARY = (("thesis55-25", "stops-25"), ("thesis60-10", "stops-10"))
CONTROL = "stops-25"  # re-run here; its equity.csv must equal the sealed one byte for byte


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def equity(folder: Path) -> list[tuple[str, int, int]]:
    with (folder / "equity.csv").open(newline="") as fh:
        return [(r["date"], int(r["equity_cents"]), int(r["long_cents"])) for r in csv.DictReader(fh)]


def logs(rows: list[tuple[str, int, int]]) -> list[float]:
    return [math.log(b[1] / a[1]) for a, b in zip(rows, rows[1:])]


def annual(values: list[float]) -> float:
    return 100.0 * (math.exp(sum(values) * YEAR / len(values)) - 1.0)


def stationary_draws(count: int, rng: random.Random) -> list[int]:
    """One stationary-bootstrap resample (scripts/replay_verdict_stats.py, copied)."""
    restart = 1.0 / MEAN_BLOCK
    index = rng.randrange(count)
    draws = [index]
    while len(draws) < count:
        index = rng.randrange(count) if rng.random() < restart else (index + 1) % count
        draws.append(index)
    return draws


def max_drawdown(rows: list[tuple[str, int, int]]) -> float:
    peak, worst = rows[0][1], 0.0
    for _, eq, _ in rows:
        peak = max(peak, eq)
        worst = min(worst, eq / peak - 1.0)
    return 100.0 * worst


def trips(folder: Path, calendar: list[str]) -> dict:
    """Round trips by the reason that closed them: a line's buys, then the sale that ends them."""
    pos = {d: i for i, d in enumerate(calendar)}
    book: dict[str, list[float]] = {}  # line -> [quantity, cost_cents, first buy session]
    closed: dict[str, list[tuple[float, int]]] = {}
    with (folder / "fills.csv").open(newline="") as fh:
        for r in csv.DictReader(fh):
            qty, price = float(r["quantity"]), float(r["price_cents"])
            if r["side"] == "buy":
                held = book.setdefault(r["line"], [0.0, 0.0, pos[r["date"]]])
                held[0] += qty
                held[1] += qty * price
                continue
            held = book.get(r["line"])
            if not held or held[0] <= 0:
                continue
            cost = held[1] * qty / held[0]
            closed.setdefault(r["reason"], []).append((qty * price / cost - 1.0, pos[r["date"]] - int(held[2])))
            held[0] -= qty
            held[1] -= cost
            if held[0] <= 1e-9:
                del book[r["line"]]
    out = {}
    for reason, rows in sorted(closed.items()):
        rets = [x for x, _ in rows]
        losers = [x for x in rets if x < 0]
        out[reason] = {
            "trips": len(rows),
            "share_losing": round(len(losers) / len(rows), 3),
            "mean_return_pct": round(100 * statistics.mean(rets), 2),
            "mean_loss_of_losers_pct": round(100 * statistics.mean(losers), 2) if losers else None,
            "worst_pct": round(100 * min(rets), 2),
            "median_sessions": statistics.median(n for _, n in rows),
        }
    allr = [x for rows in closed.values() for x, _ in rows]
    out["all"] = {"trips": len(allr), "share_losing": round(sum(x < 0 for x in allr) / len(allr), 3),
                  "mean_return_pct": round(100 * statistics.mean(allr), 2), "worst_pct": round(100 * min(allr), 2)}
    return out


def describe(folder: Path) -> dict:
    rows = equity(folder)
    years = (len(rows) - 1) / YEAR
    with (folder / "fills.csv").open(newline="") as fh:
        buys = sum(r["side"] == "buy" for r in csv.DictReader(fh))
    return {
        "R_pct_a_year": round(annual(logs(rows)), 2),
        "exposure_pct": round(100 * statistics.mean(l / e for _, e, l in rows), 1),
        "max_drawdown_pct": round(max_drawdown(rows), 2),
        "buys_a_year": round(buys / years),
        "round_trips": trips(folder, [d for d, _, _ in rows]),
    }


def compare(pairs: list[tuple[Path, Path, str]]) -> dict:
    """dR per pair, whole window with a 95 % interval (one draw for every pair), and by half."""
    series = {}
    for a, b, _ in pairs:
        for f in (a, b):
            series[str(f)] = logs(equity(f))
    n = len(next(iter(series.values())))
    if any(len(v) != n for v in series.values()):
        raise SystemExit("refused: arms differ in sessions")
    rng = random.Random(SEED)
    boot: dict[str, list[float]] = {key: [] for _, _, key in pairs}
    for _ in range(RESAMPLES):
        order = stationary_draws(n, rng)
        for a, b, key in pairs:
            sa, sb = series[str(a)], series[str(b)]
            boot[key].append(annual([sa[i] for i in order]) - annual([sb[i] for i in order]))
    out, half = {}, n // 2
    for a, b, key in pairs:
        sa, sb = series[str(a)], series[str(b)]
        draws = sorted(boot[key])
        lo, hi = draws[int(0.025 * RESAMPLES)], draws[int(0.975 * RESAMPLES) - 1]
        d = annual(sa) - annual(sb)
        h1, h2 = annual(sa[:half]) - annual(sb[:half]), annual(sa[half:]) - annual(sb[half:])
        verdict = "AHEAD" if lo > 0 and h1 > 0 and h2 > 0 else "BEHIND" if hi < 0 else "H0"
        out[key] = {"dR_pts": round(d, 2), "interval_95": [round(lo, 2), round(hi, 2)],
                    "first_half": round(h1, 2), "second_half": round(h2, 2), "verdict": verdict}
    return {"sessions": n, "pairs": out}


def same_run(a: Path, b: Path) -> None:
    ja, jb = (json.loads((f / "arm.json").read_text("utf-8")) for f in (a, b))
    for key in ("commit", "cache", "sessions", "first_session", "last_session", "require_history"):
        if ja[key] != jb[key]:
            raise SystemExit(f"refused: {a.name} and {b.name} differ in {key}")
    if ja["dirty"] or jb["dirty"]:
        raise SystemExit("refused: an arm ran from a dirty worktree")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("selftest", "score"))
    ap.add_argument("--sealed", type=Path, required=True)
    ap.add_argument("--arms", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    if a.mode == "selftest":
        got = compare([(a.sealed / "target-25", a.sealed / "stops-25", "target-25 - stops-25")])
        print(json.dumps(got, indent=1))
        ok = got["pairs"]["target-25 - stops-25"]["dR_pts"] == -10.90
        print("reproduces EXP-022" if ok else "MISMATCH: EXP-022 published -10.90")
        return 0 if ok else 1
    control = sha(a.arms / CONTROL / "equity.csv") == sha(a.sealed / CONTROL / "equity.csv")
    if not control:
        raise SystemExit("refused: the re-run stops-25 does not reproduce the sealed arm")
    pairs = []
    for challenger, base in (PRIMARY, *SECONDARY):
        same_run(a.arms / challenger, a.sealed / base)
        pairs.append((a.arms / challenger, a.sealed / base, f"{challenger} - {base}"))
    result = {
        "control_stops25_equity_identical": control,
        "compare": compare(pairs),
        "arms": {name: describe(folder) for name, folder in (
            ("stops-25", a.sealed / "stops-25"), ("stops-10", a.sealed / "stops-10"),
            ("thesis60-25", a.arms / "thesis60-25"), ("thesis55-25", a.arms / "thesis55-25"),
            ("thesis60-10", a.arms / "thesis60-10"))},
    }
    result["verdict"] = result["compare"]["pairs"]["thesis60-25 - stops-25"]["verdict"]
    text = json.dumps(result, indent=1)
    a.out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

### `exp040_pilot.py`

```python
"""EXP-040 pilot: one thesis arm over 2016, outside the scored window; prints fill counts only.

Run from the pinned clean checkout's root (a dirty tree refuses):

    uv run --no-sync python -B <kit>/exp040_pilot.py <cache_dir> <out_root> <arm>

The pilot manifest is exp040_arms.json with experiment "EXP-040-pilot", start 2016-03-01 and the
history rule off; the run ends 2016-12-30, so nothing of the scored window (2017-01-03 on) is
replayed. Not evidence: it proves the override reaches the analyst and the replay sells on it.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from scripts.replay_arms import load_manifest, run_arm, select  # noqa: E402
from scripts.replay_runner import run  # noqa: E402

PILOT_END = date(2016, 12, 30)
KIT = Path(__file__).resolve().parent


def bounded(**kwargs: object) -> dict:
    kwargs["end"] = PILOT_END
    return run(**kwargs)


def main(cache: str, out_root: str, arm: str) -> None:
    data = json.loads((KIT / "exp040_arms.json").read_text("utf-8"))
    data.update(experiment="EXP-040-pilot", start="2016-03-01", require_history=False)
    path = KIT / "exp040_pilot_arms.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = load_manifest(path)
    for spec in select(manifest, arm):
        out = run_arm(spec, manifest, cache_dir=Path(cache), out_root=Path(out_root), runner=bounded)
        with (out / "fills.csv").open(newline="") as fh:
            counts = Counter((r["side"], r["reason"]) for r in csv.DictReader(fh))
        print(f"pilot {spec.name} overrides={list(spec.overrides)} fills={sorted(counts.items())}", flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:4])
```
