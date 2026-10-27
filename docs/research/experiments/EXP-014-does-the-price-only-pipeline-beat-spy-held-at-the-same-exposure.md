# EXP-014 — Does the price-only pipeline earn more than SPY held at the same exposure, over the index as it stood?

**Status:** PRE-REGISTERED 2026-10-01 (planner). **Scored 2026-10-26 under Amendment 2: NO EDGE (indistinguishable). FINAL 2026-10-27: the fidelity count read PASS.** Sections
1–5 and Appendix P are fixed before the first one. A change of design after it is a new experiment.
**Decision / origin:** next-leg plan E17.5 ([next-leg-plan.md](../../next-leg-plan.md)), work-queue
**82** · scope [DL-232](../../design-log.md) · fidelity gate [DL-237](../../design-log.md) · this design
[DL-257](../../design-log.md) · tooling
[S250](../../sprints/sprint-250-a-replays-excess-return-comes-with-an-interval-and-a-verdict.md) ·
**Cost:** $0 of LLM spend; about 7 hours of local compute.

**Amendment 1 — 2026-10-21 22:30 AEDT, approved by the operator, recorded before any arm starts.** As
[EXP-022's Amendment 1](EXP-022-does-an-exit-besides-the-stop-make-the-book-earn-more.md): the gate moves from *running* the arms to *reading* them. Appendix P
stays as frozen; this overrides its **Gate** line and section 5 step 1 in that one respect, and changes
nothing that is computed.

- **Run now.** The five arms run before the fidelity verdict, after EXP-022's twelve, from the same
  clean detached checkout at `v0.128.06` (`f7e7ac21`), the fidelity pin since `sched-2026-10-20`.
  [DL-237](../../design-log.md) decision (3) already put EXP-014 on the pinned commit in place of
  section 4's "the commit that merges S250"; `v0.128.06` holds S250's tooling and
  `scripts/exp014_arms.json` as merged.
- **Blind until PASS.** `replay_verdict.py` does not run, and no arm's `summary.json`, `equity.csv`,
  `fills.csv`, `sessions.csv` or `benchmark.csv` is opened; the run's logs strip the equity figure from
  every progress line. When the five finish, the SHA-256 of every file goes into a seal, and the seal's
  digest into Appendix R, before anything is scored.
- **On PASS** read at a commit whose decision paths equal `v0.128.06`'s: verify the seal, then score by
  section 5. **On FAIL**, the arms are deleted unread and section 5 step 1 holds; if the count restarts
  on decision paths that differ from `v0.128.06`'s, they are deleted unread and run again on PASS.
- **Why.** The replay has no randomness and reads no live state, so an arm run now computes exactly
  what it would compute on PASS; nothing is scored or read before PASS, so the gate keeps both its
  purposes. **Ruled out:** scoring now; waiting (the same computation, later); running beside EXP-022's
  arms three at a time (this machine has two cores: every arm and the operator's own use would slow).

**Amendment 2 — 2026-10-26 13:29 AEDT, the operator's word, recorded before anything is scored.** The operator lifted the seal before the fidelity PASS: *"whatever file. i want to see results"*. The fidelity read of 2026-10-26 (through `sched-2026-10-23`, replayed from `v0.128.06`) was INSUFFICIENT on the PM's floor alone: 8 of 10 judged recommendations, with 4 of 4 clean sessions, scanner 100 / 100, analyst 151 / 151 and PM 8 / 8 in agreement and 0 unexplained (OneDrive `fidelity/2026-10-26/`). Earlier the same day the operator opened one sealed file (which one was not said); just before scoring, every sealed file re-hashed identical to the seal (30 of 30 here; 72 of 72 in EXP-022).

- **Scored now,** by section 5 steps 4–8 unchanged, from `../ta-exp022` at `v0.128.06`.
- **The verdict is provisional until the fidelity PASS.** It becomes final only if the count reads PASS on decision paths equal to `v0.128.06`'s, under DL-237's rule unchanged. On FAIL, or if the count restarts on other decision paths, the verdict is void and recorded as void; the arms are no longer deleted unread, because they have been read.
- **What it costs.** The result is now known, so every call left on the fidelity count (its floor, the timing of a retag, a restart) is made by the written rule alone.
- **Ruled out:** waiting for the PASS, expected within one or two sessions (the operator chose not to wait).

## 1. Why we needed this experiment

**The decision that waits.** G-EDGE: the operator chooses between putting an edge to work (P18A:
capital deployment, pillar reweighting, a signal-discovery loop) and freezing the trading pack as the
platform's reference workload (P18B). It is a capital-risk decision and it is the operator's. This
experiment is its input, and nothing else in the next leg can start before it.

**What building without it would risk.** Three more sprints tuning a pipeline that only harvests
market exposure, or freezing one that has an edge nobody measured.

**What earlier evidence says.**

- **Live** (the brief for `sched-2026-09-30`): the book is **−0.60 pts** behind SPY held at the same
  exposure, over **36 sessions** at **22 %** invested. Thirty-six sessions cannot tell skill from luck.
- **One smoke replay** (S235, 2026-09-27, 10 bps, 2016-01-04 → 2026-09-25): portfolio **+217.9 %**,
  exposure-matched SPY **+232.2 %**, excess **−14.3 pts**, average exposure 78.5 %. It was recorded as a
  smoke run, not a verdict, and it has no interval.
- **That smoke run decided on history the fleet never has** *[measured 2026-10-01]*. The cache starts
  on 2016-01-04, so **113 of its 552 buys** were decided on fewer than 200 bars: 103 in 2016, 10 on
  lines that had just joined the index, 57 on fewer than 50 bars, the least on 11. A fleet run
  declares a lookback that covers 200 sessions (`required_history_bars`), and its names arrive with
  203 bars each. This experiment removes that defect before it scores anything.
- **EXP-011, EXP-012, EXP-013** each replayed one mechanism (barrier ratios, volatility sizing, regime
  sizing) on today's 98 survivors. None replayed the whole pipeline, and each carried a survivorship
  caveat. This experiment runs on the index as it stood, so that caveat is closed here.

## 2. Hypothesis

**The statistic.** *Annualised excess return over exposure-matched SPY*, in percentage points a year:

`A = ((1 + P/100)^(252/n) − (1 + E/100)^(252/n)) × 100`

where `P` is `portfolio_return_pct`, `E` is `exposure_matched_return_pct` and `n` is
`performance_sessions`, all three as returned by
`agents/reporter/domain/performance.calculate_performance`, the function the live `Snapshot` uses.
Exposure-matched SPY holds, each session, the fraction of equity the book had invested at the previous
close, and holds the rest in cash at 0 %.

- **H1 — edge.** On the arm `base-25` (the fleet's settings, 25 bps of slippage a side), `A > 0` and
  the lower bound of its 95 % interval is above 0.
- **H2 — edge in one pillar.** H1 fails, and for an ablation arm `X` (`technical-only-25` or
  `relative-strength-only-25`) the lower bound of `A`'s 95 % interval is above 0 **and** the lower
  bound of the paired difference `A(X) − A(base-25)` is above 0.
- **H0 — no edge.** Neither holds. Reported with one of two readings: *behind* (the upper bound of
  `base-25`'s interval is below 0) or *indistinguishable* (the interval contains 0).

**Why this bar.** It is the plan's own rule, written on 2026-09-23 before any replay existed: *"excess
return over exposure-matched SPY, with a lower CI bound above 0, survives 25 bps of slippage."* The
paired condition on H2 is there because two extra arms are two extra chances to pass by luck: an
ablation must beat the full pipeline on the same days, not only beat zero.

## 3. Data

**Source.** The S235 cache in OneDrive `trading-agents-data` (never the repo: the repo is public and
SIP bars are licensed). Alpaca SIP daily bars, `adjustment=all` (splits and dividends) for the stocks
and for SPY alike, so both sides are total-return series *[measured, read:
`scripts/replay_dataset_sources.py:61`, `scripts/sp500_context.py:55`]*.

**Universe.** The S&P 500 as it stood each day (S231, S233): **732** membership episodes, **721**
lines with bars, **1,360,156** bars, 2016-01-04 → 2026-09-25, **2,698** sessions; SPY and VIX on every
session; Finnhub sectors for 724 lines *[measured 2026-10-01]*.

**Files, frozen for this experiment** (SHA-256 prefix, bytes):

| File | SHA-256 prefix | Bytes |
| --- | --- | --- |
| `sp500_bars.csv.gz` | `198cffbb3542` | 22,675,629 |
| `sp500_benchmark.csv.gz` | `f40b8b60506a` | 50,036 |
| `sp500_membership.csv.gz` | `db971f1b3b95` | 5,474 |
| `sp500_sessions.csv.gz` | `15ba1326e091` | 5,417 |
| `sp500_vix.csv.gz` | `f80fa60b3ed9` | 12,567 |
| `sp500_sectors.csv.gz` | `7a6801c55f21` | 4,638 |

**The scored window.** 2017-01-03 → 2026-09-25: **2,446** sessions, 9.7 years. The 252 sessions of
2016 are history only; no decision is made in them.

**Known defects in the data, each counted in every arm's summary.**

- **No bars before a line joins the index.** 187 lines have their first bar after 2016. In the world,
  the fleet would have had their earlier history. Here a line is not offered to the pipeline until its
  window holds the 200 bars the analyst is always given; held lines stay visible. The member-sessions
  this removes are counted.
- **No bars after a line leaves the index.** A held line exits at its last member close (DL-232).
- **No fundamentals, sentiment, news or earnings dates, and no deliberator** (DL-232). The weights
  renormalise as they do live when those feeds degrade.
- **Sectors** are today's Finnhub industries; a delisted line may have none.
- **Four known Alpaca adjustment errors** (S233) are handled by the harness's rebases and counted.

## 4. Tools and setup

- **Machine.** Intel Core (family 6, model 142), 4 logical cores, 16 GB RAM, Windows 10 Pro.
- **Software.** Python 3.13.2, uv 0.8.14. The scoring uses the standard library only; the harness
  uses the repo's own packages.
- **Repo commit.** The commit that merges S250. Each arm writes it to its `arm.json`, and the scorer
  refuses arms from different commits.
- **Random seed.** 0, for the bootstrap. The replay itself has no randomness.
- **External services.** None. No network, no LLM call, no broker.
- **Cost cap.** $0.

## 5. How it was conducted

1. **Gate.** The run starts only when E17.4's fidelity verdict reads **PASS** (`scripts/replay_fidelity.py`,
   DL-237). It reads INSUFFICIENT until four clean sessions exist. On FAIL this experiment does not
   run, and the gap becomes the work (the plan's rule).
2. **Arms.** Five replays, each over the point-in-time index, `--start 2017-01-03`, to the cache's
   last session, with the history rule on and the fleet's committed pack settings:

   | Arm | Slippage a side | Setting changed |
   | --- | --- | --- |
   | `base-05` | 5 bps | none |
   | `base-10` | 10 bps | none |
   | `base-25` | 25 bps | none |
   | `technical-only-25` | 25 bps | `ANALYST_RELATIVE_STRENGTH_WEIGHT=0.0` |
   | `relative-strength-only-25` | 25 bps | `ANALYST_RELATIVE_STRENGTH_WEIGHT=1.0` |

   The analyst blends `(1 − w) × technical + w × relative strength` with `w = 0.20` live
   (`agents/analyst/domain/scoring.py`), so `w = 0` and `w = 1` are the two drop-one ablations of
   DL-232. No other setting moves. The scanner's own relative-strength filter is not part of the
   ablation.
3. **What each arm receives.** Per session: the members' bars up to that session, SPY bars, VIX, the
   book's own holdings and stops, and sectors. The fleet's scanner, analyst and PM functions decide;
   the harness's broker fills day limit orders on the next session and stops when touched, moves every
   fill against the trader by the arm's slippage, and marks the book daily.
4. **Scoring.** Each arm's daily equity and invested value go through `calculate_performance` with
   the cached SPY closes: once over the whole scored window, and once per calendar year (2017 … 2026,
   the last partial). A session pair belongs to the year of its later session. Nothing is fitted, so
   there is no training window and nothing to purge; the years are evaluation blocks.
5. **Interval.** A stationary block bootstrap over session pairs: mean block length **20** sessions,
   **10,000** resamples, seed **0**, wrapping at the end. One set of index draws is applied to every
   arm, so arms are compared on the same resampled days. Each resampled series is rebuilt and scored
   by `calculate_performance`; `A` is computed from its outputs. The interval is the 2.5th and 97.5th
   percentiles of the 10,000 draws.
6. **Verdict.** Section 2's rule, applied by code to the five arms.
7. **Controls.** (a) A replica that earns exactly SPY at `base-25`'s exposure each day must score
   `A = 0` with an interval of [0, 0]. (b) Scoring twice gives byte-identical output.
8. **Failure handling.** The scorer gives no verdict, and says why, when: an arm is missing; arms
   differ in commit, cache checksums, sessions or history rule; an arm has a gap session; or a control
   fails. A failed or interrupted replay is re-run whole; no arm is patched.
9. **Reported, not barred.** `base-05` and `base-10` (the slippage sweep); each arm's return against
   SPY itself; the per-year table and the count of years with positive excess; the two halves of the
   window; maximum drawdown; average exposure; buys a year; exits by reason; every absent-input
   counter, including the member-sessions the history rule removed.

**What this experiment cannot claim, stated before the result.**

- **It speaks for the price-only pipeline.** Live, the price-only and the full pipeline share a median
  57 % of approvals (S237).
- **It is not a clean holdout.** The pack's settings were chosen with this decade in view (EXP-010 to
  EXP-013, on today's survivors). That bias runs toward finding an edge, so it weakens an EDGE
  verdict and leaves a NO EDGE verdict standing.
- **One smoke run was seen first.** Its −14.3 pts came from older code and included the short-history
  buys. The pass bar predates it; the block length, the yearly windows, the annualisation and the
  ablation rule were fixed today, after it.
- **The universe is the S&P 500; the fleet trades a 99-name list.** The replayed book is about 78 %
  invested where the live book is about 22 %.
- **The interval assumes the future resembles the decade resampled.**

## 6. Results

*Final (Amendment 2's condition met): the fidelity count read PASS on 2026-10-27 through `sched-2026-10-26` from `v0.128.06` (5 of 5 clean sessions, PM 16 of 10 judged recommendations, 0 unexplained; OneDrive `fidelity/2026-10-27/`).* Scored 2026-10-26 13:43–13:50 AEDT by
`scripts/replay_verdict.py` at `v0.128.06` over the sealed arms (30 of 30 re-hashed identical just
before); `verdict.md` SHA-256 `33a32fa6…`, `verdict.json` `169df1e0…`, beside the arms in OneDrive
`exp014-2026-10-21/arms/`. The control passed (A = 0, interval [0, 0]).

- **Verdict: NO EDGE, indistinguishable.** `base-25`: A = −0.02 pts a year, 95 % interval
  [−3.85, +4.16], over 2,445 session pairs.
- **The book earned what SPY earns at its exposure:** +166.60 % against +167.13 % for exposure-matched
  SPY (SPY held whole: +297.07 %), at an average exposure of 75.8 % and a maximum drawdown of −22.9 %;
  about 10.6 % a year against SPY's 15.3 % *[annualised from the table over 2,445 sessions]*.
- **Slippage sweep:** A = +0.32 at 5 bps and +0.31 at 10.
- **H2 fails for both ablations.** `technical-only-25`: A = +1.80 [−2.75, +7.08], paired difference
  from `base-25` +1.83 [+0.00, +4.05]; neither lower bound is above 0, and the lead is 2025 (+11.6) and
  2026 (+40.6, partial). `relative-strength-only-25`: A = −1.27 [−3.14, +0.62], at 24 % exposure.
- **Years:** `base-25` has positive excess in 4 of 10; the first half reads −1.34, the second +1.33.
- **What follows ([DL-315](../../design-log.md), fixed 2026-10-23 before the score):** the ranking code
  stays, and the line closes in an ADR written with the verdict, on the PASS.

## 7. Conclusions

*Pending.*

## 8. Recommended code changes, and how to implement them

*Pending. The verdict goes into an ADR, and the planner brings the operator one recommendation for
G-EDGE.*

## Appendix P — Pre-registration (frozen)

Frozen at the commit that adds this file (`git log --diff-filter=A` on this path). Never edited.

- **Statistic.** `A = ((1 + P/100)^(252/n) − (1 + E/100)^(252/n)) × 100`, with `P`, `E`, `n` from
  `calculate_performance` over the scored window.
- **Scored window.** 2017-01-03 → 2026-09-25, 2,446 sessions, on the cache files and checksums of
  section 3.
- **Arms.** `base-05`, `base-10`, `base-25`, `technical-only-25` (`ANALYST_RELATIVE_STRENGTH_WEIGHT=0.0`),
  `relative-strength-only-25` (`ANALYST_RELATIVE_STRENGTH_WEIGHT=1.0`); slippage 5, 10, 25, 25, 25 bps
  a side; point-in-time index; history rule on; the fleet's committed pack settings otherwise.
- **Interval.** Stationary block bootstrap over session pairs, mean block 20, 10,000 resamples, seed
  0, one set of draws for all arms, percentile 2.5 / 97.5.
- **Verdict.** EDGE: `base-25`'s lower bound > 0. EDGE IN A PILLAR: not EDGE, and an ablation arm's
  lower bound > 0 with the lower bound of its paired difference from `base-25` > 0. NO EDGE otherwise,
  read as *behind* when `base-25`'s upper bound < 0 and *indistinguishable* when its interval contains 0.
- **Gate.** E17.4's verdict reads PASS before the first arm starts.
- **Controls.** The exposure-matched replica scores 0 with interval [0, 0]; scoring is byte-stable.
- **No verdict** when an arm is missing or the arms differ in commit, cache, sessions or history rule,
  when an arm has a gap session, or when a control fails.

## Appendix R — Run record

*The arms under Amendment 1: run and sealed, not scored. Nothing below is a result.*

- **Commit.** `f7e7ac21` (`v0.128.06`), the clean detached checkout EXP-022's arms ran from; every
  `arm.json` reads `dirty: false`, and all five name the one commit.
- **Machine and software.** As section 4: Intel Core i7-7660U (2 cores, 4 threads), 16 GB, Windows 10 Pro;
  Python 3.13.2, uv 0.8.14.
- **Arms.** The five of `scripts/exp014_arms.json`, each 2017-01-03 → 2026-09-25, 2,446 sessions, history
  rule on; slippage and overrides as Appendix P names them; the one cache of section 3, the same
  checksums as EXP-022's arms.
- **When.** 2026-10-22 13:04 → 19:38 AEDT, one arm at a time, 76 to 82 minutes each, after EXP-022's twelve
  and a short hold for an unrelated `make ci`. The CPU-throttle guard's 391 samples with an arm running
  never read a performance limit below 100 %.
- **Seal.** `seal.txt` lists the SHA-256, size and path of the 30 files (six per arm); its own SHA-256 is
  `6adf6a46e6a96be798f17e1b155a7d5b9df1a976a0bdc25f9a305170c1cc83d1`. Outputs in OneDrive
  `trading-agents-data/exp014-2026-10-21/`: `arms/`, `logs/` (the equity figure stripped from every line),
  `status/` (exit codes, all 0), `run.log`.
- **A determinism check, from checksums only.** `base-25` and `base-10` declare the same replay as EXP-022's
  `stops-25` and `stops-10`; their `equity.csv` and `fills.csv` are byte for byte identical across the two
  seals.
- **Not done.** Scoring: it waits for the fidelity PASS; the seal is verified first.

## Appendix S — Scripts

The scripts are S250's, in `scripts/`. Each arm ran as its own process, from the checkout's root:
`uv run --no-sync python -B scripts/replay_arms.py run --arm <name> --manifest scripts/exp014_arms.json
--out-root <OneDrive>/exp014-2026-10-21/arms --cache <OneDrive>/trading-agents-data`, started by EXP-022's
`run_exp022_arms.ps1` with `-Manifest scripts/exp014_arms.json`. Scoring, on PASS:
`uv run python scripts/replay_verdict.py` over the same arms folder.
