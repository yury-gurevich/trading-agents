# LAW-04 · Communication — the process is always legible

> You should never wonder what the system is about to do, is doing, did, or needs. In a
> chargeable era, surprise equals risk.

## Statement

Every operation communicates at **four levels**, and stops for the operator before spending
money or crossing a Point of No Return.

## The four communication levels

| Level | When | Form | Example |
| --- | --- | --- | --- |
| **CONFIRM** | before spend or a PNR | interactive stop, shows blast radius + cost estimate | "Delete RG `trading-agents`? 13 resources. [y/N]" |
| **INFORM** | during a run | live visual progress (the boards) | `[OK] master  [OK] scanner …` |
| **RECORD** | after each action | a `ledger.md` row + postcondition evidence | "fleet up · 12/12 · ~cents" |
| **ALERT** | on failure / overage | cause + next step, not a stack trace | "deploy halted at analyst: image pull 403 → check GHCR_PAT" |

## Clauses

- **CM-01 · No silent spend.** No action that costs money or resumes a billable resource runs
  without a CONFIRM showing the estimated cost. (Your founding rule: don't go in blind.)
- **CM-02 · No silent irreversibility.** Every PNR shows blast radius and requires an explicit
  typed/clicked confirmation — never a default-yes.
- **CM-03 · Progress is visual.** Long actions show a live board (status/deploy style), not a
  spinner — the operator can see *which* gear is moving and where it stalled.
- **CM-04 · Failures explain themselves.** An ALERT states what failed, the likely cause, the
  state it left behind, and the single next action. Raw errors go to the log, not the human.
- **CM-05 · Status is one command away.** `ta status` / `ta doctor` answer "what's running,
  what's healthy, what's it costing" without reading any docs.
- **CM-06 · Graduated quiet.** Under `LAW-01`, a CONFIRM may be downgraded to an INFORM once
  the action has earned trust in the ledger — recorded as a deliberate dial move.

## Why

The biggest hidden cost of a CI/CD product is the human time spent reading help-files to
understand undocumented behaviour. This law makes the process *narrate itself* so the
operator leads from the dashboard, not the manual.
