# EXP-036 — Do S&P 500 firms that change their annual report's wording underperform those that do not ("Lazy Prices")?

**Status:** PRE-REGISTERED 2026-10-24 (planner). Sections 1–5 and Appendix P are fixed before any return
is computed; the filings may be downloaded and their similarities computed first (they are not
outcomes).
**Decision / origin:** [R011](../where-an-edge-can-exist/INDEX.md), [R012](../idea-testing-foundation/INDEX.md)
batch 4 · the operator, 2026-10-24, offered the last five queued ideas: *"only the annual-report wording
test."* · [DL-319](../../design-log.md) · **Cost:** $0 (SEC EDGAR, the operator's address in the
User-Agent by their word).

## 1. Why we needed this experiment

Cohen, Malloy and Nguyen (*Lazy Prices*, JF 2020; 1995–2014) found that firms whose 10-K or 10-Q language
changes most from the year before underperform those that change least, by up to 188 bps a month long-
short, and that the return arrives over months as the news the changes foreshadow comes out: investors
do not read the changes. It is the one queued idea whose mechanism the project's other tests have not
ruled out: EXP-028 and EXP-034 showed that headlines are priced within minutes, but a change buried in a
200-page filing is information of a slower kind. Every year scored here is after the paper's sample.

## 2. Hypothesis

**The signal.** For each firm's 10-K, the cosine similarity of its word-count vector with the firm's
previous 10-K (filed 9 to 15 months earlier). Low similarity = a "changer".

**The statistic.** Each month-end from 2017-01 to 2026-07, S&P 500 members with a 10-K filed in the last
12 months (by the month-end) are sorted into similarity quintiles; the next month's equal-weighted return
of the most similar quintile (Q5, "non-changers") minus the least similar (Q1). Monthly series;
Newey–West t (3 lags).

- **H1 — the effect holds:** the mean monthly Q5 − Q1 spread is above 0 with t above 1.96.
- **H0:** otherwise.

**Economic bar (for H1 only):** Q5 held long-only, rebalanced monthly, 25 bps a side on its turnover,
beats the equal-weighted universe: mean net monthly excess above 0 with t above 1.65.

**Why this bar.** One hypothesis, scored entirely after the paper's sample: no correction is needed, and
the paper's own sign is the prediction.

## 3. Data

- **Filings:** every 10-K (form `10-K`; amendments excluded) of firms that were S&P 500 members at any
  time 2016–2026, filed 2015-01-01 → 2026-09-25, from EDGAR (`data.sec.gov` submissions JSON, then
  each filing's primary document). The text is reduced to lowercase words; only the text is kept
  (outside the repo and OneDrive, `C:/Users/yury_/ta-local/exp036/`), with a manifest in the kit.
- **Tickers to CIKs:** the SEC's `company_tickers.json` (current tickers) and the Form 345 data sets
  2016 Q4 → 2021 Q4 (issuer symbol and CIK, for firms that have since left or been renamed).
- **Returns and membership:** the S235 cache (as EXP-030).

## 4. Tools and setup

Machine as EXP-026; Python 3.13.2, numpy, pandas; no repo code; no LLM; $0.

## 5. How it was conducted

1. Map each S&P 500 line's tickers to a CIK; fetch its 10-K list; download each primary document;
   strip tags, scripts and the inline-XBRL header; keep the words (`[a-z]+`).
2. Similarity: cosine of word-count vectors between a 10-K and the same CIK's previous 10-K filed 270 to
   450 days earlier.
3. Formation as section 2; the filing must be dated on or before the month-end; returns as EXP-030
   (month-end close to month-end close; a stock whose bars end exits at its last close).
4. **Pilot (before scoring):** coverage only: lines with a CIK, 10-Ks found and downloaded, similarities
   computed, members with a similarity each month.
5. **Reported, not barred:** the Q5 and Q1 legs against the universe; each year; the spread in the
   second to sixth month after formation (the paper's slow drift).

**What this cannot claim.** Large caps only, where the paper found the effect weaker; one similarity
measure of the paper's four; 10-Ks only, not 10-Qs.

## 6. Results

*Pending.*

## 7. Conclusions

*Pending.*

## 8. Recommended code changes, and how to implement them

*Pending.*

## Appendix P — Pre-registration (frozen)

- Signal: cosine similarity of word counts (`[a-z]+`, lowercased, tags and inline-XBRL header removed)
  between a 10-K and the same firm's previous 10-K filed 270–450 days earlier.
- Formation: month-ends 2017-01 → 2026-07; S&P 500 members with a 10-K filed within the last 12 months on
  or before the month-end; quintiles; next month's equal-weighted return.
- **H1:** mean monthly Q5 − Q1 > 0 with Newey–West (3 lags) t > 1.96. Else H0.
- Economic (only under H1): Q5 long-only, 25 bps a side on turnover, mean net excess over the
  equal-weighted universe > 0 with t > 1.65.

## Appendix R — Run record

*Pending.*

## Appendix S — Scripts

*Pending.*
