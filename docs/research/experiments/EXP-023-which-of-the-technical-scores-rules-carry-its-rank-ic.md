# EXP-023 — Which of the technical score's rules carry its rank IC, and does the scanner's filter pick names that beat the ones it turns away?

**Status:** PRE-REGISTERED 2026-10-23 (planner). **No component has been scored.** Sections 1–5 and
Appendix P are fixed by the commit that adds this file; sections 6–8 are written after the run.
**Decision / origin:** [DL-314](../../design-log.md) · work-queue **137** · the operator, 2026-10-23,
on EXP-015's reported reading of the technical score: *"yes it is"* (worth a follow-up for the edge
question) · **Cost:** $0 (no LLM, no vendor; local CPU only).

## 1. Why we needed this experiment

[EXP-015](EXP-015-price-only-ensemble-vs-technical-score.md) failed its bar, and it reported one
reading it was not built to test. Over 1,761 test sessions from 2018 to 2024, the analyst's
technical score has a mean rank IC of **−0.0099** against the 10-session forward excess return on
the scanner's survivors, and **−0.0070** on 2025-01-02 → 2026-09-25. In the price-only replay the
composite *is* the technical score (no fundamentals or news), so that score is what ranks the
replay's buys.

The score is not one rule. `score_candidate`'s `technical_score` is
`0.8 × (mean of the available rule sub-scores / 100) + 0.2 × (rs_score / 100)`, or the mean alone
when relative strength cannot compute. It averages **15 banded rules**: four that reward trend
(`sma_distance_pct`, `ema_spread_pct`, `macd_histogram`, `golden_cross`), five that reward weakness
(`rsi`, `rsi2`, `bollinger_position`, `stochastic_k`, `williams_r`) and six others (`atr_pct`,
`choppiness`, `obv`, `nw_deviation_pct`, `geometric_pattern`, `turnaround`). Relative strength
(`rs_score`) is the sixteenth component. If trend and weakness rules carry opposite signs, their
equal-weight mean cancels, and a zero says nothing about what its parts know.

**The decision that waits on the answer:**

- Should a re-specified technical score be pre-registered (a new experiment, on data no experiment
  has read)?
- Or does the price-only ranking have nothing to give, so that work stops there?

A second, cheaper question shares the data. Does the scanner's filter itself pick names that beat
the members it turns away? If the pipeline has an edge (EXP-014 will say, after the fidelity PASS),
that is where a price-only one could live.

**Nothing in the fleet changes on this result.** `agents/analyst/` and `agents/scanner/` are decision
paths of the fidelity count (`scripts/replay_fidelity_git.py`), so no change to either ships before
the fidelity PASS, whatever this reads.

## 2. Hypothesis

This is a descriptive decomposition with a family-wise test. It has no promotion bar.

- **Q1 — the components (16).** For each component *c*, its 0–100 score's mean per-session Spearman
  rank IC against the 10-session forward excess return over SPY, on the scanner's survivors, over the
  **scored window 2018-01-02 → 2024-12-31**. *c* **carries** when its bootstrap test rejects a zero
  mean after **Holm's step-down across all 16 at a family-wise 5 %**. A positive sign means the
  component's bullish reading earns; a negative sign means it points the wrong way. H0 for each *c*:
  mean IC 0.
- **Q2 — the scanner's selection.** Among offered members with at least 253 bars of their own: per
  session, the mean 10-session forward excess return of the survivors minus that of the
  non-survivors, averaged over the scored window. It **carries** when its bootstrap 95 % interval
  excludes 0. H0: the difference is 0.
- **Why this bar.** Holm, because 16 components are tested at once: at an unadjusted 5 %, about 0.8
  of them would carry by chance alone. The interval and the sessions are EXP-015's, so the two
  experiments read the same evidence the same way.

**Reported, not tested:**

- Each component's raw indicator value's IC, before banding: does the banding lose or invert what
  the indicator knows?
- Horizons 5 and 20.
- Per-year means.
- Each component's coverage: the share of survivor rows where it computes.
- 2025-01-02 → 2026-09-25 apart, marked as already read in aggregate by EXP-015.

## 3. Data

- **The S235 cache:** OneDrive `trading-agents-data`, never the repo, licensed SIP bars. File
  checksums as EXP-015's `panel.json`: `sp500_bars` `198cffbb3542`, `sp500_benchmark`
  `f40b8b60506a`, `sp500_coverage` `0ba083a797d2`, `sp500_membership` `db971f1b3b95`,
  `sp500_sectors` `7a6801c55f21`, `sp500_sessions` `15ba1326e091`, `sp500_vix` `f80fa60b3ed9`.
- **EXP-015's panel:** OneDrive `trading-agents-data/experiments/EXP-015/panel.npz`, file SHA-256
  `c9cf472f…`, panel digest `aff1a727…`. It holds 1,209,946 rows (715,852 survivors), each row's
  session, line, survivor and 253-bar flags, the technical score, and the forward returns at 5, 10
  and 20 sessions with SPY's. Q2 reads it alone.
- **Q1's components** are recomputed by the analyst's own `score_candidate`, on the window the panel
  stage used, and aligned to the panel's rows.
- **Known defects:** EXP-015's: the four adjustment errors masked by DL-313, and today's sector
  labels. Q1 and Q2 read no sector.

## 4. Tools and setup

- **Machine:** i7-7660U (2 cores, 4 threads), Windows 10.
- **Software:** Python 3.13.2 and numpy 2.5.3, the main checkout's venv.
- **Code:** the repo at this file's commit: code identical to `1c91c21e`, EXP-015's, since only docs
  moved. It runs from a detached worktree.
- **The script:** a planner's read-only script, `exp023_components.py`, in OneDrive
  `trading-agents-data/exp023-2026-10-23/`. It reuses `scripts/exp015_*` for offering, IC and the
  interval. It goes verbatim into Appendix S, with its SHA-256 in Appendix R.
- **Seed and cap:** bootstrap seed 0. Cost cap $0.

## 5. How it was conducted

1. **Pilot, not scored:** the F1 pilot window (the first 40 lines, 2016-01-04 → 2017-12-29). It proves
   the alignment and the run time and reads nothing from 2018 on. The script may be fixed after the
   pilot. After the first scored run it is frozen.
2. **Q1's rows.** For every session, the panel stage's loop exactly: members, the visible window,
   `offer_lines`, `apply_filters` with the pack's settings. Then, for each survivor,
   `score_candidate(...).metrics`. From it the script keeps the 15 `{rule}_score` values and
   `rs_score`, and each raw value (`{rule}`, `relative_strength`); NaN where a component did not
   compute.
3. **Alignment, a stop condition.** Each survivor row is matched to the panel by session and line.
   Its `technical_score` must equal the panel's baseline, and the 0.8 / 0.2 blend rebuilt from its
   components must equal it too, within 1e-12. One mismatch stops the run as `STOPPED`, unscored.
4. **IC.** `exp015_ranks.session_ic` per component per session: at least 10 rows with both values,
   and a session where the component is flat (one band) has no IC.
5. **Interval and test.** `exp015_rule.interval`'s method, the same draws for both:
   - every 10th session;
   - stationary bootstrap, mean block 20, 10,000 resamples, seed 0;
   - percentile 95 % interval;
   - two-sided bootstrap p = min(1, 2 × (1 + resampled means on the far side of 0) / 10,001).

   Holm then runs over the 16 p-values.
6. **Q2** from `panel.npz`: among rows with the 253-bar flag, per session with at least 10 survivors
   and 10 non-survivors, the survivors' mean excess return minus the non-survivors'. The interval is
   the same.
7. **Outputs** go to OneDrive `trading-agents-data/experiments/EXP-023/`: a JSON record and a page.
   Nothing licensed goes in the repo.

## 6. Results

*Pending.*

## 7. Conclusions

*Pending.* Written only from the recorded results, on this reading, fixed now:

- **Components carry with opposite signs:** cancellation explains the zero. A re-specified score is
  a new pre-registered experiment on sessions after 2026-09-25, which no experiment has read.
- **None carries:** the price-only technical pillar shows no information at these horizons. Whether
  it keeps ranking is the operator's call, after EXP-014 scores.
- **Q2 carries:** the scanner's filter is where price-only information lives.

## 8. Recommended code changes, and how to implement them

*Pending.*

## Appendix P — Pre-registration (frozen)

Frozen at the commit that adds this file (`git log --diff-filter=A` on this path). Never edited.

- **Components (16):** `rsi`, `macd_histogram`, `bollinger_position`, `sma_distance_pct`,
  `ema_spread_pct`, `atr_pct`, `stochastic_k`, `williams_r`, `choppiness`, `obv`, `golden_cross`,
  `rsi2`, `nw_deviation_pct`, `geometric_pattern`, `turnaround` (each `{name}_score`), and `rs_score`.
- **Universe:** the scanner's survivors per session, as EXP-015's panel stage offers them.
- **Target:** the 10-session forward excess return over SPY, next open to the tenth close (EXP-015's
  `returns − spy` at horizon 10).
- **Scored window:** 2018-01-02 → 2024-12-31. 2025-01-02 → 2026-09-25 is reported apart.
- **Statistic:** the mean of per-session Spearman ICs (`session_ic`, at least 10 rows, flat sessions
  excluded).
- **Interval and test:** every 10th session; stationary bootstrap, mean block 20, 10,000 resamples,
  seed 0; percentile 95 %; two-sided p = min(1, 2 × (1 + far-side count) / 10,001); Holm across the
  16 at 0.05.
- **Q2:** survivors' minus non-survivors' mean 10-session excess return, among rows with at least 253
  bars, per session with at least 10 of each; same window and interval; carries when the interval
  excludes 0.
- **Stop:** any survivor row whose recomputed `technical_score`, or the blend rebuilt from its
  components, differs from the panel's baseline by more than 1e-12.
- **Pilot:** the first 40 lines, 2016-01-04 → 2017-12-29, not scored.

## Appendix R — Run record

*Pending.*

## Appendix S — Scripts

*Pending.*
