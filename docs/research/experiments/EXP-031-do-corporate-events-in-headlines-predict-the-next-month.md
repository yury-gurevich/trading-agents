# EXP-031 — Do corporate events named in headlines (analyst calls, buybacks, dividends, guidance, beats, approvals) predict the next month?

**Status:** PRE-REGISTERED 2026-10-24 (planner). Sections 1–5 and Appendix P are fixed before any return
is computed.
**Decision / origin:** [R012](../idea-testing-foundation/INDEX.md) batch 4a · [DL-319](../../design-log.md)
· the operator, 2026-10-24: *"Let's test every idea"* · **Cost:** $0.

## 1. Why we needed this experiment

Event studies hold some of finance's best-documented drifts: after analyst upgrades and downgrades
(Womack 1996), earnings surprises (post-earnings drift), buyback announcements (Ikenberry, Lakonishok
and Vermaelen 1995), dividend changes, stock splits, guidance changes. The project has the events in its
own news archive: Benzinga headlines name them in fixed phrases ("X Upgrades Y to Buy", "Y Beats Q3 EPS
Estimates"). This batch reads sixteen event types by keyword and asks whether a stock drifts after one,
as the fleet could trade it (the next open).

## 2. Hypothesis

**The statistic.** For each event type, the mean **20-session excess return** of the stocks it names:
from the open after the event's decision session (the 18:30 ET rule of EXP-028) to the close 20
sessions later, minus the S&P 500 members' equal-weighted mean over the same window. Events are averaged
per session, and the t-statistic is Newey–West (20 lags) over the session series.

**Discovery** (decision sessions 2016-10-03 → 2021-06-30): Benjamini–Hochberg at q = 10 % over the 16
two-sided p-values. **Confirmation** (2021-07-01 → 2026-08-26): one-sided in the discovery's direction,
Holm at 5 %. **Economic bar** for a confirmed positive event: buying it at the next open and selling 20
sessions later, 25 bps a side, earns a mean net excess above 0 with t above 1.65 on the confirmation
sessions; a confirmed negative event is an avoid rule and is reported only.

## 3. Data

The Benzinga archive (EXP-024; 2016-10 → 2026-10-23), headlines naming exactly one symbol that is an S&P
500 member on the decision session, de-duplicated by symbol, session and event; the S235 cache bars
(opens and closes) and membership.

## 4. Tools and setup

Machine as EXP-026; Python 3.13.2, numpy, pandas; no repo code; no randomness; $0.

## 5. How it was conducted

1. Each headline is matched against Appendix P's sixteen patterns (case-insensitive); a stock-session is
   an event of a type if any of its headlines match.
2. Returns: open(*t*+1) → close(*t*+20), minus the members' mean over the same window; also 1 and 5
   sessions (reported).
3. Discovery, confirmation and the economic bar as section 2 fixes; types with under 100 events in
   discovery read INSUFFICIENT.
4. **Reported, not barred:** counts, 1- and 5-session excess, hit rates, examples of matched headlines.

**What this cannot claim.** Keywords miss and mis-read some headlines (the pilot reports examples).
Benzinga's timestamps are its own; the open after the decision session is later than a fast trader's
entry, so a fail here does not rule out a faster reader.

## 6. Results

*Pending.*

## 7. Conclusions

*Pending.*

## 8. Recommended code changes, and how to implement them

*Pending.*

## Appendix P — Pre-registration (frozen)

| # | Event | Pattern (Python `re`, case-insensitive, on the headline) | Predicted |
| --- | --- | --- | --- |
| E1 | Analyst upgrade | `\bupgrade[sd]?\b` and not `downgrad` | + |
| E2 | Analyst downgrade | `\bdowngrade[sd]?\b` | − |
| E3 | Price target raised | `price target (raised\|increased\|boosted\|lifted\|bumped)\|(raises\|lifts\|boosts\|bumps\|increases) (its \|the )?price target` | + |
| E4 | Price target cut | `price target (lowered\|cut\|reduced\|trimmed\|slashed)\|(lowers\|cuts\|trims\|reduces\|slashes) (its \|the )?price target` | − |
| E5 | Coverage initiated at buy | `initiat\w* .*\b(buy\|outperform\|overweight)\b` | + |
| E6 | Buyback announced | `\b(buyback\|repurchase)\b` and `\b(announc\|authoriz\|approv\|new\|launch)` | + |
| E7 | Dividend raised | `\b(raises\|increases\|hikes\|boosts\|lifts)\b.*\bdividend\|\bdividend (increase\|hike\|raise)` | + |
| E8 | Dividend cut | `\b(cuts\|slashes\|suspends\|reduces\|eliminates\|halts)\b.*\bdividend\|\bdividend (cut\|suspension)` | − |
| E9 | Stock split announced | `\bstock split\b\|\b\d+-for-\d+\b` | + |
| E10 | Guidance raised | `\b(raises\|boosts\|lifts\|increases\|ups\|hikes)\b.*\b(guidance\|outlook\|forecast)\|\b(guidance\|outlook)\b.*\b(raised\|above)\b` | + |
| E11 | Guidance cut | `\b(lowers\|cuts\|reduces\|slashes\|trims)\b.*\b(guidance\|outlook\|forecast)\|\b(guidance\|outlook)\b.*\b(lowered\|below)\b` | − |
| E12 | Earnings beat | `\b(beats\|tops\|exceeds\|surpasses)\b.*\b(estimate\|consensus\|eps\|expectations)` | + |
| E13 | Earnings miss | `\b(misses\|falls short\|miss)\b.*\b(estimate\|consensus\|eps\|expectations)` | − |
| E14 | CEO departure | `\bceo\b.*\b(resign\|steps? down\|depart\|to exit\|retire\|ousted\|fired\|leaving)` | − |
| E15 | FDA approval | `\bfda\b.*\b(approv\|clears\|clearance\|grants)` | + |
| E16 | Legal trouble | `\b(sec probe\|investigation\|subpoena\|lawsuit\|sues\|sued\|class action\|antitrust)\b` | − |

Discovery BH q = 10 % over 16; confirmation Holm 5 % one-sided; economic for positive events: next-open
buy, 20-session hold, 25 bps a side, mean net excess > 0 with t > 1.65.

## Appendix R — Run record

*Pending.*

## Appendix S — Scripts

*Pending.*
