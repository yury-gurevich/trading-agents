# EXP-0NN — <the question, as a question>

<!--
HOW TO USE THIS FILE (operator, 2026-09-28: every experiment is recorded with these eight sections)
  Copy to `EXP-0NN-<slug>.md` and add the INDEX.md row. Write sections 1–5 and Appendix P BEFORE the
  first scored run and commit them: that commit is the pre-registration. After it, sections 1–5 may be
  clarified but never changed in substance; Appendix P is never edited. A change of design after the
  first scored run is a new experiment. Sections 6–8 are written after the run.
  Delete every HTML comment before committing.
-->

**Status:** PRE-REGISTERED <date> | COMPLETE <date> · <one-line verdict once complete>
**Decision / origin:** <DL, work-queue item, operator words> · **Cost:** <$ and what it was spent on>

## 1. Why we needed this experiment

<The decision that waits on the answer, what building without it would risk, and what earlier evidence
(EXP, DL) already says.>

## 2. Hypothesis

<H1, H2 …, each naming its arm and baseline; H0; the bar (statistic, interval, threshold) and why that bar.>

## 3. Data

<Source, feed and adjustment, universe, date range, row counts, where it lives (never licensed data in
the repo), a checksum prefix of each file, and any known defect in it.>

## 4. Tools and setup

<Machine (CPU, cores, RAM, OS), Python and package versions, external services with their model or API
version, repo commit, random seeds, and the cost cap.>

## 5. How it was conducted

<Step by step: how cases were built, what each model or arm received, pilot and freeze, scoring and
confidence intervals, failure handling. Enough for someone else to repeat it.>

## 6. Results

<The numbers the hypotheses name, first, with their intervals; then calibration, breakdowns and anything
unexpected. Mark each MEASURED; the full output lives in Appendix R.>

## 7. Conclusions

<What the result means for the decision in section 1, what it does not say, and what it rules in or out.>

## 8. Recommended code changes, and how to implement them

<Each change: what, where, why this result supports it, how to build it (sprint or chore, branch, tests,
law cycle, deploy kind), and who decides. "None" is an answer; say why.>

## Appendix P — Pre-registration (frozen)

<Verbatim as committed before the first scored run; name the commit.>

## Appendix R — Run record

<Full output, pilot notes, defects found and fixed before scoring.>

## Appendix S — Scripts

<Every script, verbatim, with how to run it.>
