---
type: Architecture Decision
status: accepted
closes: "When the monitor's mechanical exit and the analyst's thesis disagree on a held position, which decider wins? What happens to target and time exits?"
tags: [exits, analyst, monitor, execution, stops, risk, decisions, adr-0015, adr-0016]
amends: ADR-0016
---

# ADR 0017 — Exit authority: alpha proposes, risk disposes

**Status:** Accepted · **Date:** 2026-07-24 · **Decider:** Yury Gurevich (product owner)

## Context

ADR-0016 made the analyst the single decider that reaches the broker, scoring held names on
the same evidence as entries and emitting `buy` / `sell` / `hold`. ADR-0015's amendment
(2026-07-24) then surfaced the question neither ADR settled, and closed on it explicitly:

> With closure no longer stranding positions, the monitor's stop/target/time closes are
> **re-decided every single run, forever**, because they reach no broker (DL-60) — while the
> analyst, scoring the same names on full evidence, returns `hold`. Two deciders, opposite
> answers, and only one of them is wired to the broker. **Which decider wins is not settled by
> this ADR or by ADR-0016.**

Live in production right now: the monitor decides `close` on HPE / MRVL / CSCO every run while
the analyst says `hold` the same names. Only the analyst reaches the broker, so nothing
executes and the monitor re-decides the same exit forever — noise, not a decision.

The question is not a plumbing detail. It is the boundary between **alpha** (what to own — the
thesis) and **risk** (what you refuse to lose — the stop). A professional desk keeps these
separate and does **not** subordinate risk to alpha on the downside: the portfolio manager
wins discretionary exits, but cannot override a stop in the moment, because the stop is a
pre-commitment made at entry — when the operator is rational — against the exact bias that
grips them when a position is cratering ("the thesis is still good" is the rationalisation, not
a signal). That is why real stops rest at the exchange as bracket/OCO orders (ADR-0015 §3): so
that no model and no human gets to reconsider them when it matters.

## Decision

**Alpha proposes, risk disposes.** The analyst owns discretionary exits; the stop is an
unconditional floor that alpha cannot veto.

### 1 · The analyst is the sole author of *discretionary* exits

A held name exits on a **degraded thesis** — the analyst's existing
`sell if confidence < exit_confidence_floor else hold` at `recommend.decide(held=True)`. This is
the only discretionary exit voice. On any discretionary disagreement with the monitor, the
analyst wins by construction: the monitor no longer authors a competing decision.

### 2 · The stop-loss is an unconditional floor, forced onto the *same* rail

When a held name is at or through its stop threshold, the exit is **forced**: the analyst emits
a `sell` with trigger `stop` that **short-circuits the confidence/thesis check**. The analyst
cannot hold past a stop. Risk overrides alpha on the downside.

The stop rides the **unified rail ADR-0016 already built** (analyst → PM → execution), not a
second close-dispatch path. Reviving that second path is how the sell side got stranded
(DL-60); this ADR does not reopen it. The PM must treat a `sell` carrying trigger `stop` as an
**unconditional full-position exit** — a stop reduces risk and is never sized down or gated
away.

The stop arithmetic (`check_stop`, today in `agents/monitor/domain/exit_rules.py`) moves to a
**shared contracts module** so the analyst can apply it without importing the monitor
(agents never import other agents). Each held position's stop threshold — `opened_price_cents`
and `stop_pct`, carried on the `Position` node — must be threaded to the analyst, which today
receives held names as bare tickers.

### 3 · The monitor stops competing to decide; it observes and surfaces

The monitor no longer authors exit decisions. It keeps **broker reconciliation** (DL-44) and
gains one job: when a held position is at or through its stop but has **not** yet exited, it
records a **`Fault`** ("stop breached on X, still held"). A missing or late stop must be
*visible*, never silent — this is the DL-57 pattern (absent risk control must not look like
present risk control). One decider, one rail, and a watchdog that raises its hand.

### 4 · `target` and `time` exits are retired as mechanics; they become deferred strategy

The monitor's `target` (+take-profit) and `time` (horizon) triggers are **removed as mechanical
exits**. A discretionary book lets winners run and exits on thesis; blindly dumping a +10%
winner or a day-14 hold is exactly the two-deciders-disagree problem one layer down. Genuine
profit-taking — trailing logic, trim policy, time-in-trade, MAE/MFE — is the strategy work
ADR-0016 already sequenced **after** the unified evidence path exists. It lands there, done
properly, not as three constants on a node.

The **stop is the one rule that survives** as a hard floor, because it is risk, not opinion.

### 5 · The durable home of the stop remains the broker (ADR-0015 §3)

Forcing the stop onto the daily rail is the **interim**. Runs fire 22:30 UTC, after the US
close, so a forced stop is a next-open order exposed to a gap-down — the exact weakness
ADR-0015 §3 exists to remove by resting the stop at the exchange as a bracket/OCO order,
enforced continuously. §3 stays outstanding; this ADR does not close it, it makes the interim
safe and visible until §3 ships.

## Consequences

- The analyst's held-name evaluation needs each position's `opened_price_cents` and `stop_pct`,
  not just the ticker. The held-candidate carrier and the analyst's poll/run wiring change.
- A `sell` intent now has two provenances — thesis (`confidence < floor`) and forced (`stop`) —
  and the rationale/trigger must distinguish them so the reporter and acceptance can tell a
  risk exit from a conviction exit.
- The monitor's charter shrinks to reconciliation + stop-breach `Fault`. Its `evaluate_position`
  loses `target`/`time`; `exit_rules` keeps only `check_stop` (relocated to contracts). Monitor
  law files update to match.
- No new order path, idempotency scheme, or reconciliation is added — the forced stop reuses the
  sell rail's existing `exit:{position_ref}:{ticker}:sell` key (0.74.01), so re-forcing a stop
  that has not yet filled does not oversell.
- Until ADR-0015 §3, there is **no continuously-enforced stop**: a gap-down between the 22:30 run
  and the next open is uncovered. Accepted knowingly; surfaced by §3 remaining open.
- Version: **feat** (new exit-authority capability), 0.75.00 → 0.76.00.

## Alternatives rejected

- **Analyst wins *everything*, including the stop (no forced exit).** Deletes the stop-loss: a
  position bleeds past its stop and stays in book on thesis. A desk does not run live capital
  without a stop, and a silent absence of one is the DL-57 trap. Rejected — only tolerable if the
  breach is at least surfaced, which §3 of the decision keeps.
- **Wire the monitor's `stop` CloseDecision to the broker (second rail).** Rebuilds the exact
  close-dispatch path DL-60 showed had stranded the sell side, with its own idempotency and
  reconciliation. Two rails is the original defect. Rejected — the forced stop rides the one
  proven rail instead.
- **Keep `target`/`time` as mechanical monitor exits.** Recreates two-deciders-disagree one layer
  down (analyst holds on thesis while the monitor dumps a +10% winner). Rejected — folded into the
  deferred strategy work where trailing/trim belong.
- **Wait for broker-native stops (ADR-0015 §3) before resolving authority.** Leaves the monitor
  re-deciding forever in the meantime and the alpha/risk boundary unowned. Rejected — the interim
  forced stop is safe, visible, and on the existing rail; §3 is an upgrade, not a prerequisite.
- **Put the stop check in the PM instead of the analyst.** The PM sizes intents; it does not score
  held names against price. The analyst already holds the per-name price and thesis in one place,
  making it the natural site for "thesis, unless the stop is breached." Rejected for locality.
