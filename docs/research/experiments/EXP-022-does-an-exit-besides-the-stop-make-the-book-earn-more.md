# EXP-022 — Does an exit besides the stop make the book earn more than stops alone, at the same cost?

**Status:** PRE-REGISTERED 2026-10-16 (planner). **Scored 2026-10-26 under Amendment 2, provisional until the fidelity PASS: CHAMPION HOLDS.** Sections
1–5 and Appendix P are fixed before the first one; a change of design after it is a new experiment.
**Decision / origin:** work-queue **92** · direction [DL-240](../../design-log.md) step 3 (the operator,
2026-09-28: *"we need to sell at profit"*) · the replay's exits [DL-304](../../design-log.md),
[S281](../../sprints/sprint-281-a-replay-arm-declares-how-its-positions-exit.md) · this design
[DL-305](../../design-log.md) · scorer
[S282](../../sprints/sprint-282-each-exit-arm-is-scored-against-stops-only-on-the-same-days.md) ·
fidelity gate [DL-237](../../design-log.md) · **Cost:** $0 of LLM spend; about 17 hours of local compute
(twelve arms of about 84 minutes each, two or three at a time).

**Amendment 1 — 2026-10-21 22:20 AEDT, approved by the operator, recorded before any arm starts.** The
gate moves from *running* the arms to *reading* them. Appendix P stays as frozen; this overrides its
**Gate** line and section 5 step 1 in that one respect, and changes nothing that is computed.

- **Run now.** The twelve arms run before the fidelity verdict, from one clean detached checkout at
  `v0.128.06` (`f7e7ac21`), the commit the fidelity count is pinned to from `sched-2026-10-20`.
  `git diff --name-only v0.128.06 45a2fdc1 -- <DECISION_PATHS>` is empty *[measured 2026-10-21]*.
- **Blind until PASS.** The scorer does not run, and no arm's `summary.json`, `equity.csv`,
  `fills.csv`, `sessions.csv` or `benchmark.csv` is opened; the run's logs strip the equity figure
  from every progress line. When the twelve finish, the SHA-256 of every file goes into a seal, and the
  seal's digest into Appendix R, before anything is scored.
- **On PASS** read at a commit whose decision paths equal `v0.128.06`'s: verify the seal, then score by
  section 5 steps 4–8. **On FAIL**, or if the count restarts on decision paths that differ from
  `v0.128.06`'s, the arms are deleted unread and this experiment runs as section 5 says.
- **Why.** The replay has no randomness and reads no live state, so an arm run now computes exactly
  what it would compute on PASS. The gate exists so that no exit verdict comes from a replay not shown
  faithful, and so that no one knows the result while the gate is open; both hold, because nothing is
  scored or read before PASS. It moves about 17 hours of compute from after PASS to before it.
  **Ruled out:** scoring now (knowing the result would colour any later call on the fidelity count);
  waiting (the same computation, 17 hours later).

**Amendment 2 — 2026-10-26 13:29 AEDT, the operator's word, recorded before anything is scored.** The operator lifted the seal before the fidelity PASS: *"whatever file. i want to see results"*. The fidelity read of 2026-10-26 (through `sched-2026-10-23`, replayed from `v0.128.06`) was INSUFFICIENT on the PM's floor alone: 8 of 10 judged recommendations, with 4 of 4 clean sessions, scanner 100 / 100, analyst 151 / 151 and PM 8 / 8 in agreement and 0 unexplained (OneDrive `fidelity/2026-10-26/`). Earlier the same day the operator opened one sealed file (which one was not said); just before scoring, every sealed file re-hashed identical to the seal (72 of 72 here; 30 of 30 in EXP-014).

- **Scored now,** by section 5 steps 4–8 unchanged, from `../ta-exp022` at `v0.128.06`.
- **The verdict is provisional until the fidelity PASS.** It becomes final only if the count reads PASS on decision paths equal to `v0.128.06`'s, under DL-237's rule unchanged. On FAIL, or if the count restarts on other decision paths, the verdict is void and recorded as void; the arms are no longer deleted unread, because they have been read.
- **What it costs.** The result is now known, so every call left on the fidelity count (its floor, the timing of a retag, a restart) is made by the written rule alone.
- **Ruled out:** waiting for the PASS, expected within one or two sessions (the operator chose not to wait).

## 1. Why we needed this experiment

**The decision that waits.** Which exit, if any, the fleet builds first (DL-240 step 4). Today the only
exit that fires is the protective stop: losses are realised automatically and gains never are. The
planner's estimate for building exits live is one to two sprints for a take-profit, one for a time
exit, and more for trimming and adding; none should start on an exit that loses money.

**What building without it would risk.** Selling winners early. An exit that cuts a winner at its
target gives up the rest of its move, and every extra round trip pays the spread twice. Whether the
recycled capital earns that back is an empirical question the replay can answer at no LLM cost.

**What earlier evidence says.**

- **Live** (S241's F4, 2026-10-16): on 21 settled buys the stop came first **47.6 %** of the time
  against **29.4 %** declared; skill over climatology +5.69 % [+1.74, +19.13] on 4 dates. Thin, and it
  scores probabilities, not exits.
- **EXP-011** (on today's survivors): the median target is reached within 10 sessions about half the
  time (50.2 %).
- **S281's proof window, seen by the planner before this design** (2024-01-02 → 2024-06-28, 124
  sessions, 10 bps, history rule on; `wq92-2026-10-16/f1_proto.txt`, OneDrive): from $100,000 the
  stops-only replay ended at **$104,840.51**; take-profit $103,651.45, time exit at 10 sessions
  $103,374.25, trailing stop $102,805.34, cool-down 3 $104,887.51, all four together $101,481.50.
  Exits multiplied the buys: 91 stops-only, 376 take-profit, 353 time exit, 290 trailing, 500 all
  four. Six months, one cost and no interval: not evidence, but it is why this design scores at two
  costs (section 2).

## 2. Hypothesis

**The statistic.** *The paired difference in annualised return*, in percentage points a year:

`dR(X) = R(X) − R(stops at X's slippage)`, with `R = ((1 + P/100)^(252/n) − 1) × 100`

where `P` is `portfolio_return_pct` and `n` is `performance_sessions`, both as returned by
`agents/reporter/domain/performance.calculate_performance`, the function the live `Snapshot` uses.
Cash earns 0 %, as it does in the paper account.

**The arms.** One champion and five challengers, each at **25** and at **10** bps of slippage a side
(twelve arms): `stops` (the fleet today), `target` (a take-profit at the PM's `target_pct`), `time10`
(a time exit after 10 sessions), `trail` (a trailing stop), `target-time10` (both of those), `cool5`
(a stopped line sits out 5 runs). Each exit is simulated by DL-304's rules.

- **H1 — an exit wins.** For a challenger `X` at 25 bps, the lower bound of `dR(X)`'s interval is above
  0 **and** `dR(X)` is above 0 in each half of the window.
- **H2 — an exit wins at low cost.** H1 fails for every challenger, and it holds for one at 10 bps.
- **H0 — the champion holds.** Neither. Each challenger is read *behind* (upper bound below 0),
  *split* (lower bound above 0, a half at or below 0) or *indistinguishable*.

**The verdict** is EXIT WINS (H1), EXIT WINS AT LOW COST (H2) or CHAMPION HOLDS (H0). Under H1 or H2
the **leader** is the winning challenger with the largest `dR`, the first in the order above on a tie.

**Why this bar.**

- *Return, not excess over exposure-matched SPY.* The question is whether an exit makes the book more
  money. An exit changes how much of the book is invested; excess over exposure-matched SPY scores
  return per unit invested, so an exit that sells winners and sits in cash could score well while
  earning less. `dA`, the same difference in EXP-014's statistic, is reported beside it.
- *Paired, on the same days.* Every arm sees the same market; only the exit differs. Pairing removes
  the market's variance from the comparison, which a separate interval per arm would not.
- *95 % over the family.* Five challengers are five chances to pass by luck, so each interval is the
  Bonferroni one for five: the 0.5th and 99.5th percentiles.
- *Both halves.* An exit can earn its whole lead in one regime. Requiring the lead in each half of the
  decade rules out building on one stretch.
- *Two costs.* 25 bps a side is EXP-014's bar and the plan's; the fleet's real slippage has never been
  measured. Exits multiply turnover three to five times (section 1), so the cost alone could decide the
  answer. A win only at 10 bps builds nothing: it makes measuring the live slippage the next step.

## 3. Data

**Source.** The S235 cache in OneDrive `trading-agents-data`, exactly as EXP-014 froze it (never the
repo: the repo is public and SIP bars are licensed). Alpaca SIP daily bars, `adjustment=all`, for the
stocks and SPY alike.

**Universe.** The S&P 500 as it stood each day (S231, S233): **732** membership episodes, **721** lines
with bars, **1,360,156** bars, 2016-01-04 → 2026-09-25, **2,698** sessions *[measured 2026-10-01, EXP-014
§3]*.

**Files, frozen for this experiment** (SHA-256 prefix, bytes), re-measured 2026-10-16, identical to
EXP-014's:

| File | SHA-256 prefix | Bytes |
| --- | --- | --- |
| `sp500_bars.csv.gz` | `198cffbb3542` | 22,675,629 |
| `sp500_benchmark.csv.gz` | `f40b8b60506a` | 50,036 |
| `sp500_coverage.json` | `0ba083a797d2` | 19,041 |
| `sp500_membership.csv.gz` | `db971f1b3b95` | 5,474 |
| `sp500_sessions.csv.gz` | `15ba1326e091` | 5,417 |
| `sp500_vix.csv.gz` | `f80fa60b3ed9` | 12,567 |
| `sp500_sectors.csv.gz` | `7a6801c55f21` | 4,638 |

**The scored window.** 2017-01-03 → 2026-09-25: **2,446** sessions. 2016 is history only.

**Known defects**, each as EXP-014 §3 lists them and counted in every arm's summary: no bars before a
line joins the index or after it leaves; no fundamentals, sentiment, news, earnings dates or
deliberator (the replay is price-only); today's sectors; four Alpaca adjustment errors rebased.

## 4. Tools and setup

- **Machine.** Intel Core (family 6, model 142), 4 logical cores, 16 GB RAM, Windows 10 Pro.
- **Software.** Python 3.13.2, uv 0.8.14; the scoring uses the standard library and the reporter's
  `calculate_performance`.
- **Repo commit.** One commit for all twelve arms, at or after S282's merge, whose decision paths
  (`scripts/replay_fidelity_git.py::DECISION_PATHS`) are identical to those of the commit the fidelity
  PASS was read on. Each arm writes its commit to `arm.json`, and the scorer refuses a mix.
- **Random seed.** 0, for the bootstrap. The replay has no randomness.
- **External services.** None. No network, no LLM call, no broker.
- **Cost cap.** $0.

## 5. How it was conducted

1. **Gate.** The first arm starts only when the fidelity verdict reads **PASS** (DL-237), as for
   EXP-014. On FAIL this experiment does not run.
2. **Arms.** `uv run python scripts/replay_arms.py run --arm <name> --manifest scripts/exp022_arms.json
   --out-root <OUT> --cache <CACHE>` for each of the twelve arms of Appendix P, from one clean
   checkout. Each replays the point-in-time index from 2017-01-03 to the cache's last session with the
   history rule on, the fleet's committed pack settings and no override.
3. **What each arm receives.** As EXP-014 §5.3: the fleet's scanner, analyst and PM functions decide
   each session; the harness fills DAY limits on the next session, stops when touched, and moves every
   fill against the trader by the arm's slippage. An arm's exits are DL-304's: a take-profit rests at
   entry × (1 + `target_pct`) beside the stop (a bar touching both is the stop); a time exit sells by a
   DAY limit what has closed 10 sessions in the book; a trailing stop rises to the stop price of each
   session's high; a stopped line is left out of the next 5 runs.
4. **Scoring.** `uv run python scripts/exit_verdict.py score --out-root <OUT>`. Each arm's daily equity
   and invested value go through `calculate_performance` with the cached SPY closes, over the whole
   window, each calendar year and each half (the halves share their middle session).
5. **Interval.** EXP-014's stationary block bootstrap over session pairs: mean block 20, 10,000
   resamples, seed 0, wrapping. **One set of index draws for all twelve arms.** For each challenger the
   paired difference is taken draw by draw; its interval is the 0.5th and 99.5th percentiles,
   `v[k]` and `v[B − 1 − k]` with `k = B × 25 // (1000 × 5)`.
6. **Verdict.** Section 2's rule, applied by code (`scripts/exit_verdict_rule.py`).
7. **Controls.** (a) Every arm, rebuilt from its own session pairs in their own order, scores its own
   `R` and `A` within 1e-6 points. (b) Scoring twice gives byte-identical output.
8. **Failure handling.** No verdict, and the reason named, when: the manifest is not Appendix P's
   twelve arms; an arm is missing or lacks a file; arms differ in commit, cache checksums, sessions or
   SPY closes; an arm's recorded exits differ from the manifest's; an arm ran from a dirty worktree;
   an arm has a gap session; or a control fails. A failed or interrupted replay is re-run whole.
9. **Reported, not barred.** `dA` with its interval; each arm's `R`, `A`, portfolio return, average
   exposure, maximum drawdown and buys a year; round trips by the reason that closed them (count,
   share with a gain, mean return, median sessions held); `dR` by year; every absent-input counter.
10. **Pilot.** S282's functionality check runs the twelve arms over 2016-03-01 → 2016-12-30 with the
    history rule off (`s282_pilot_arms.py`), outside the scored window, to prove the scorer on real
    arm folders. It is not evidence (2016 decisions run on short history).

**What this experiment cannot claim, stated before the result.**

- **It speaks for the price-only pipeline**, as EXP-014 does.
- **The replay recycles capital faster than the fleet.** The replayed book trades the S&P 500 and is
  about 78 % invested; the live book trades a 99-name list and is about 22 % invested. Capital an exit
  frees is re-spent sooner in the replay, which favours the exits: a win is weaker evidence than a
  loss.
- **Daily bars.** A bar that touches both stop and target is counted as the stop, which favours the
  champion; an open beyond a barrier fills at the open.
- **One target per buy, the PM's.** It does not test another target, a partial sale, or adding.
- **No weekend profile.** A Friday-to-Monday hold is a choice of which buys to hold briefly, an entry
  profile the replay cannot express (DL-305); it is not tested here.
- **The interval assumes the future resembles the decade resampled.**

## 6. Results

*Provisional (Amendment 2): final only on the fidelity PASS.* Scored 2026-10-26 13:30–13:43 AEDT by
`scripts/exit_verdict.py` at `v0.128.06` over the sealed arms (72 of 72 re-hashed identical just
before); `verdict.md` SHA-256 `5f2ffe0c…`, `verdict.json` `e00e568e…`, beside the arms in OneDrive
`exp022-2026-10-21/arms/`. The control passed (largest deviation 0).

- **Verdict: CHAMPION HOLDS.** Every exit earns less than stops alone. At 25 bps all five are
  *behind*: the take-profit dR = −10.90 pts a year [−21.72, −0.89], the 10-session time exit −10.88,
  the trailing stop −10.56, both together −11.33, the 5-run cool-down −1.26 [−2.47, −0.08]; each is
  behind in both halves. At 10 bps the four exits are *indistinguishable* (dR about −9.4, upper bounds
  +0.55 to +0.85) and the cool-down is behind (−1.40).
- **Why:** the exits cut the average exposure from 75.8 % to 19–23 % and raise the buys from 70 to
  550–870 a year. Stops alone earn from a few long holds: 13 round trips closed by a limit sale averaged
  +158.7 % over a median 862 sessions, while its 604 stops averaged −5.7 %.
- `stops-25`: R = +10.64 % a year and A = −0.02, the same arm as EXP-014's `base-25`.
- **What follows:** the fleet's exit, the stop alone, stays; nothing changes in the code.

## 7. Conclusions

*Pending.*

## 8. Recommended code changes, and how to implement them

*Pending. A winning exit is built live in increments (DL-240 step 4), the leader first.*

## Appendix P — Pre-registration (frozen)

Frozen at the commit that adds this file (`git log --diff-filter=A` on this path). Never edited.

- **Statistic.** `dR(X) = R(X) − R(stops-<bps>)`, `R = ((1 + P/100)^(252/n) − 1) × 100`, `P` and `n`
  from `calculate_performance` over the scored window.
- **Scored window.** 2017-01-03 → 2026-09-25, 2,446 sessions, on the cache files and checksums of
  section 3.
- **Arms.** `scripts/exp022_arms.json`, as merged by S282: experiment `EXP-022`, start `2017-01-03`,
  history rule on, no overrides; at 25 and at 10 bps a side: `stops` (no exits), `target`
  (`take_profit`), `time10` (`time_exit_sessions` 10), `trail` (`trailing_stop`), `target-time10`
  (`take_profit`, `time_exit_sessions` 10), `cool5` (`reentry_cooldown_sessions` 5).
- **Interval.** Stationary block bootstrap over session pairs, mean block 20, 10,000 resamples, seed
  0, one set of draws for all twelve arms; each challenger's paired difference at percentiles 0.5 /
  99.5 (`k = B × 25 // 5000`).
- **Verdict.** A challenger wins when its lower bound > 0 and `dR` > 0 in each half. EXIT WINS when one
  wins at 25 bps; else EXIT WINS AT LOW COST when one wins at 10 bps; else CHAMPION HOLDS. Leader: the
  winner with the largest `dR`, the first in the arm order on a tie.
- **Gate.** The fidelity verdict reads PASS before the first arm starts; all arms run from one commit
  whose decision paths equal those of the commit that PASS was read on.
- **Controls.** Each arm's in-order rebuild scores its own `R` and `A` within 1e-6; scoring is
  byte-stable.
- **No verdict** when the manifest differs from these arms, an arm or a file is missing, the arms differ
  in commit, cache, sessions or SPY closes, an arm's exits differ from the manifest's, an arm ran dirty,
  an arm has a gap session, or a control fails.

## Appendix R — Run record

*The arms under Amendment 1: run and sealed, not scored. Nothing below is a result.*

- **Commit.** `f7e7ac21` (`v0.128.06`), a detached clean checkout; every `arm.json` reads `dirty: false`,
  and all twelve name the one commit.
- **Machine and software.** As section 4: Intel Core i7-7660U (2 cores, 4 threads), 16 GB, Windows 10 Pro;
  Python 3.13.2, uv 0.8.14.
- **Arms.** The twelve of `scripts/exp022_arms.json`, each 2017-01-03 → 2026-09-25, 2,446 sessions, history
  rule on, exits as the manifest declares; one cache, its seven checksums those of section 3.
- **When.** 2026-10-21 22:50 AEDT → 2026-10-22 12:49 AEDT, one arm at a time, 67 to 75 minutes each. A first
  start two at a time (22:24) was stopped after 7 minutes because the machine overheated; its two partial
  arms were deleted and run again whole (section 5 step 8). A guard logged the CPU's throttle counters
  every minute (`thermal.csv`, 834 samples with an arm running): the performance limit never fell below 100 %.
- **Seal.** `seal.txt` lists the SHA-256, size and path of the 72 files (six per arm); its own SHA-256 is
  `020ebb5ed68cedc65ec2e0162556fd63d361115136e69157e66b1ed5ba3a2627`. Outputs in OneDrive
  `trading-agents-data/exp022-2026-10-21/`: `arms/`, `logs/` (the equity figure stripped from every line),
  `status/` (exit codes, all 0), `run.log`, `thermal.csv`.
- **Not done.** Scoring: it waits for the fidelity PASS; the seal is verified first.

## Appendix S — Scripts

The scripts are S281's and S282's, in `scripts/`. Each arm ran as its own process, from the checkout's
root: `uv run --no-sync python -B scripts/replay_arms.py run --arm <name> --manifest
scripts/exp022_arms.json --out-root <OneDrive>/exp022-2026-10-21/arms --cache <OneDrive>/trading-agents-data`,
started by `run_exp022_arms.ps1` beside the outputs (one arm at a time, below-normal priority, the seal at
the end). Scoring, on PASS: `uv run python scripts/exit_verdict.py score --out-root <the same arms folder>`.
