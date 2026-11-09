# EXP-038 — Do the 212 published stock-return predictors still earn after publication, outside micro caps?

**Status:** PRE-REGISTERED 2026-11-09 (planner)
**Decision / origin:** the operator, 2026-11-09, after browsing QuantConnect's strategy library (more
than 400 strategies with code, a small-cap turnover long-short among them): *"Would something like this
… be beneficial for us? Maybe inspire us to test them?"*, then *"fix first, then the rest"* ·
[R011](../where-an-edge-can-exist/INDEX.md) named this screen on 2026-10-24 and it was never run ·
[R012](../idea-testing-foundation/INDEX.md) funnel ([DL-319](../../design-log.md)) · [DL-321](../../design-log.md) ·
**Cost:** $0 (free data, a laptop script).

## 1. Why we needed this experiment

Most of QuantConnect's library is published academic predictors written as code. Testing them one at a
time would take weeks and would mostly re-measure a known result: Chen and Welch (2026, R011) found that
about 200 published long-short portfolios earn a median 7 bp a month outside micro caps after 2005, and
McLean and Pontiff found returns fall by about 58 % after publication. This project's own tests agree:
none of 17 stock-level signals sorted the S&P 500 (EXP-030), and none of nine published allocation
strategies beat its benchmark after publication (EXP-026).

Chen and Zimmermann's Open Source Asset Pricing (OSAP) replicates 212 published predictors as monthly
portfolio returns through December 2025, in several implementations, each with its paper's publication
year. One pass over that data answers for the whole set at once: does any published cross-sectional
predictor still earn after publication in stocks the fleet could trade, so that a replay on the fleet's
own data is worth pre-registering? If none does, QuantConnect's ports of these predictors need not be
tested one by one. The operator's example, the small-cap turnover effect, is OSAP's `ShareVol` (Datar,
Naik and Radcliffe, 1998); `DolVol`, `VolMkt` and `std_turn` are its neighbours.

## 2. Hypothesis

**Unit.** Each predictor's monthly long-short return, OSAP's `LS` (long the top decile, short the bottom,
signed so that the top decile is the one the paper predicts will earn more), in the ex-micro
implementation (only stocks above the NYSE 20th percentile of market equity: OSAP
`LiqScreen_ME_gt_NYSE20pct`), in percent a month.

**H1, per predictor:** the mean `LS` return after publication is above zero.

1. **Discovery.** Each predictor's months from the January after its publication year through
   2015-12. Eligible with at least 24 months (198 of 212). One-sided Newey–West t (Bartlett, 12 lags),
   p from Student's t with n − 1 degrees of freedom; **Benjamini–Hochberg at q = 10 %** across the
   eligible predictors.
2. **Confirmation.** 2016-01 → 2025-12 (120 months, which the discovery step never reads), the same
   test on the discovery passers, **Holm at 5 %** across them.
3. **Economic bar, confirmed predictors only.** The long leg alone (the top decile held long-only, as the
   fleet trades) minus the market (Ken French Mkt-RF + RF), 2016-01 → 2025-12: mean at least **+0.25 % a
   month** (3 % a year, enough to rebalance a decile monthly at about 25 bps a side with up to half of it
   turning over) **and** one-sided Newey–West t at least **1.645**. OSAP reports no turnover, so this
   bar is a gate to a replay, not a verdict on a trade.

**H0:** no predictor confirms.

**Verdicts, by code:**

- **EDGE CANDIDATE:** confirmed and over the economic bar. The next step is a separate pre-registered
  replay on the fleet's S&P 500 cache with real costs, on the operator's word.
- **CONFIRMED, NOT ECONOMIC:** the long-short survives but the long leg does not clear the bar. No use to
  a long-only fleet.
- **NONE:** nothing confirms. Published cross-sectional predictors give this project no edge outside
  micro caps after publication.

**Why this bar:** R012's funnel (DL-319 D2). Of 198 predictors with no effect, about ten pass a 5 % test
by luck; the false-discovery rate and an untouched confirmation period keep that out.

**Reported, not barred:**

- The medians across predictors of the mean `LS` in each paper's own sample, after publication, and over
  2016–2025: the decay on this data.
- The rows of `ShareVol`, `DolVol`, `VolMkt` and `std_turn`, whatever they show.
- The same screen on three other implementations: each paper's original method (micro caps included),
  value weights forced, and value-weighted deciles (179 predictors).
- The 14 predictors published 2014–2016 with fewer than 24 discovery months: their 2016–2025 figures only.

## 3. Data

| File (OSAP release 2026.10 unless noted) | What | sha256 prefix |
| --- | --- | --- |
| `AltPorts_LiqScreen_ME_gt_NYSE20pct.parquet` | **primary**: 212 predictors, deciles + `LS`, ex-micro, 1926-01 → 2025-12, 1,238,068 rows | `fcd2ae40` |
| `PredictorPortsFull_OP.parquet` | each paper's own method, 212 predictors | `76599d94` |
| `AltPorts_LiqScreen_VWforce.parquet` | value weights forced, 212 predictors | `e64df0fc` |
| `AltPorts_DecilesVW.parquet` | value-weighted deciles, 179 predictors | `95409cb1` |
| `SignalDoc.csv` | 331 rows, 212 `Predictor`: acronym, authors, publication year (1973–2016, median 2006), sign, sample years | `0ceb1102` |
| `F-F_Research_Data_Factors.csv` (Ken French, CRSP 202609) | monthly Mkt-RF and RF, 1926-07 → 2026-09 | `a3894d74` |

**Source.** Hugging Face `OpenSourceAP/CrossSection`, branch `Data-Release-2026.10` (built from CRSP v2
and Compustat; CRSP keeps delisted firms), and the Ken French data library; downloaded 2026-11-09
19:58–20:02 AEDT into OneDrive `trading-agents-data/exp038-2026-11-09/inputs/`. Not committed: the
portfolios derive from licensed data.

**Known defects** (OSAP release notes): seven option-based predictors end in 2022-12, three governance
predictors in 2007, `PatentsRD` in 2006, `ProbInformedTrading` in 2012. Each is tested on the months it
has, n is reported, and an empty confirmation window counts as not confirmed. 26 predictors were revised
materially against the 2025.10 release (listed in the release notes).

**Read before this pre-registration:** the release notes, `SignalDoc.csv`'s metadata (the papers' own
reported returns were not printed), the files' columns, dates and counts, and the pilot (section 5). No
return after any publication date was computed.

## 4. Tools and setup

Laptop (Intel i7-7660U, 2 cores / 4 threads, Windows 10 Pro 10.0.19045). Python 3.12.2 in an isolated
`uv run --no-project` environment: pandas 3.1.1, numpy 2.5.4, scipy 1.18.1, pyarrow 26.0.1. Script
`exp038_screen.py` (Appendix P digest), kept in the kit folder. No random draws, so no seed. No paid
service. The repo commit is this pre-registration's.

## 5. How it was conducted

1. **Download** (done, section 3).
2. **Pilot** (done 2026-11-09, `pilot.json` in the kit), mechanical only, on data no test reads: all 212
   predictors present in the primary file; for every one, `LS` equals the top decile minus the bottom
   decile month by month (worst miss 5.0e-13), so the long leg is always decile 10; returns are in
   percent (median absolute decile return before 1974: 3.38); the market series covers all 120
   confirmation months; in each paper's own sample years, 205 of 209 predictors point the way the paper
   said (three have no ex-micro data in their sample years).
3. **Freeze.** The script's digest and the parameters are in Appendix P; this commit is the
   pre-registration.
4. **Score once:** from the kit folder,
   `uv run --no-project --with pandas==3.1.1 --with pyarrow==26.0.1 --with scipy==1.18.1 --with numpy==2.5.4 python -I exp038_screen.py score .`
   writes `exp038.json` and prints the summary. Sections 6–8 and Appendix R follow from that output.
5. **Failures.** A crash before output is fixed, recorded in Appendix R and re-run. Changing any number in
   section 2 makes a new experiment.

## 6. Results

Pending the run.

## 7. Conclusions

Pending the run.

## 8. Recommended code changes, and how to implement them

Pending the run.

## Appendix P — Pre-registration (frozen)

Committed before the first scored run.

- Script `exp038_screen.py` sha256 `2e30e4e5527ffb7e65852ad8d17646bc1586062674723307521b03fb40fe2855`.
- Inputs sha256: primary `fcd2ae4053d7262868f5531be051ab6039161f7422091651116cf4a6990f3734`; OP
  `76599d94beab94cc8973d8a126e8efbed98ee79f677738c55b2389f17387ba96`; VW forced
  `e64df0fc189f1a4f4ce3ba39fdbba2ee83dfce871c6bf60f5660cbc9222158db`; deciles VW
  `95409cb1014d6b20d5ddf0468e98baeb8fec68ef514bef0e777565eb884679a8`; SignalDoc
  `0ceb11020c2138c2477b732948beaac2e67ccaad8428753e3a79af2bb5ea0178`; Ken French
  `a3894d74d553cab812eabbe706bdbf443c97eb20b24b05e3e5f3ce47e46b90bb`.
- Unit: OSAP `LS`, ex-micro (`LiqScreen_ME_gt_NYSE20pct`), percent a month.
- Discovery: January after the publication year → 2015-12; at least 24 months; one-sided Newey–West t,
  12 lags, Student's t with n − 1 df; Benjamini–Hochberg q = 0.10.
- Confirmation: 2016-01 → 2025-12; same test on the discovery passers; Holm, alpha 0.05.
- Economic bar: decile 10 minus (Mkt-RF + RF), 2016-01 → 2025-12; mean ≥ 0.25 % a month and t ≥ 1.645.
- Verdicts: EDGE CANDIDATE / CONFIRMED, NOT ECONOMIC / NONE, as in section 2.

## Appendix R — Run record

Pending the run.

## Appendix S — Scripts

`exp038_screen.py` lives in the kit folder with the digest above; it is copied here verbatim with the run
record.
