<!-- Agent: planning | Role: research folder index -->
# R008 — Survivorship-free S&P 500 universe (E17.1)

**Status:** ✅ Measured 2026-09-25 · **Decision:** [DL-226](../../design-log.md) · **Consumer:** P17's
E17.2 ([next-leg plan](../../next-leg-plan.md))

**Answers:** Can we source point-in-time S&P 500 membership and bars for removed names on our current
vendor plans? Is the ~90 % member-day coverage bar met?

**Summary:** FMP and Finnhub do not sell us membership (402/403). Wikipedia's *Historical components of
the S&P 500* change log reconciles to within ~3 names back to 2016. Alpaca SIP daily bars cover
**95.3 %** of member-days (removed names 93.4 %), about 99 % once six ticker renames are mapped; the
uncovered residue is 0.2 %. P17 proceeds survivorship-free.

| File | What |
| --- | --- |
| [measurement.md](measurement.md) | Method, numbers, the identity check, and what E17.2 must build |
