---
type: decision
status: amended
date: 2026-08-08
closes:
  - "Does the deliberation veto block execution, and if so what does it block?"
  - "How do we tell 'the veto has not run yet' from 'the veto is not deployed'?"
tags: [execution, deliberation, risk, adr]
supersedes: []
amends: [ADR-0017]
---

# ADR-0022 — The veto gates buys, never exits

**Status:** Amended · **Date:** 2026-08-08 · **Amended:** 2026-08-13 · **Decider:** Yury Gurevich

## Context

The deliberation veto has never blocked an order. Until 2026-08-08 that looked like
policy; it was actually a race.

`_drop_vetoed` treated an absent `DeliberationRun` as *execute the full set* — a
deliberate fail-open from S147, whose reasoning still stands: **blocking a run on an
LLM outage blocks exits**, and an unsellable book is precisely how the system froze
for eight days in July–August.

But in graph-pull, execution and the deliberator poll independently, so *absent*
also covers *has not finished yet*. Measured on run `check-s166-flat-book`:

| | time (UTC) |
| --- | --- |
| `PMRun` written, 18 approved | 05:35:56 |
| execution submitted 18 orders to the broker | **05:36:22** |
| `DeliberationRun` written (`real_debate_count=18`) | **05:47:32** |

The veto arrived eleven minutes late, saying *revise*, about orders already live at
the broker. The deliberator is slow because it is doing real work — 18 multi-turn
Opus debates. Execution is fast. The faster poller always wins ([DL-98](../design-log.md)).

This was invisible for weeks because the PM approved **zero** orders on every
scheduled run since 07-31: no orders, nothing to debate, no race to lose. The
deadlock was hiding it.

## Decision

**A PMRun whose approved set contains a `buy` waits for its `DeliberationRun`, for a
bounded grace period. A sell-only PMRun never waits.**

- The wait is expressed by *not consuming* the PMRun: `find_pending` skips it, so the
  next poll retries. No new state, and a restart resumes correctly because the window
  is measured from the PMRun's own `created_at`.
- The bound is `ExecutionSettings.deliberation_grace_seconds` (default **900**,
  `0 ≤ n ≤ 3600`). At `0` the previous behaviour is restored exactly.
- When the grace expires with no veto, the run **still submits** — fail-open is
  unchanged — but records `deliberation_status="proceeded_unvetoed"` on the
  `ExecutionRun` **and** raises a `DeliberationGraceExpired` fault. An absent veto can
  never again look like a clean run.
- `ExecutionRun.deliberation_status` is one of `applied` / `applied_failed_open` /
  `not_required` / `waiting` / `proceeded_unvetoed` — a queryable fact, not a rationale substring
  (the S158 lesson). `applied_failed_open` means a `DeliberationRun` exists, but at least one
  ticker's debate failed open.

## Amendment 2026-08-13 — fail-open is not a clean uphold

S175 found the missing second distinction. ADR-0022 separated *absent veto* from *present veto*, but
execution still treated a present `DeliberationRun` with `failed_open_tickers` as a clean `applied`
uphold. The posture does not change: a failed-open review still permits the order, because S147's
outage reasoning stands. The evidence changes: execution reads the existing `failed_open_tickers`
property, stamps `deliberation_status="applied_failed_open"`, and records a
`DeliberationFailedOpenSubmit` fault. No `DeliberationRun` property is added.

## Why buys and not exits

ADR-0017 §1 makes the analyst the sole author of discretionary exits, and S147
established that an LLM outage must never block one. The asymmetry is not a
compromise — it matches the risk: **delaying a buy costs an opportunity; delaying an
exit costs control of the book.** A fifteen-minute hold on a buy is affordable; the
same hold on an exit reproduces the deadlock this system spent three sprints escaping.

## Consequences

- Buys land up to `deliberation_grace_seconds` later. Orders are `tif=day` and the
  pipeline runs at 22:30 UTC against a market that opens at 13:30 UTC, so a 15-minute
  hold changes nothing about the fill.
- If the deliberator is undeployed or broken, **every** buy-carrying run now takes the
  full grace and raises a fault. That is intended: it is the signal that was missing.
- A PMRun with an unreadable `created_at` proceeds immediately rather than waiting
  forever — an unparseable timestamp must not be able to stall trading.

## Road not taken

- **Make execution wait unconditionally.** Rejected: re-introduces exactly what S147
  refused, and would have blocked the flatten that unfroze the book.
- **Move the veto ahead of the PM.** Rejected for now: the veto reviews *approved
  orders*, so it would have to review recommendations instead — a different feature,
  not a fix for this defect.
- **An `intent-to-deliberate` marker written at PMRun time** so absence and not-yet
  become structurally distinct. Cleaner in principle, but it puts the deliberator's
  contract inside the PM's write path; the grace window achieves the same separation
  with no cross-agent coupling. Revisit if the grace proves too blunt.
