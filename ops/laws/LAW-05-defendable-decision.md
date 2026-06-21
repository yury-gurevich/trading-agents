# LAW-05 · Defendable Decision — every choice has a recorded "why"

> You must always be able to answer "why did we do it this way?" — to an auditor, a
> regulator, a future you, or the LLM proposing the next improvement.

## Statement

No operational decision is made without a **defendable record**: the choice, the
alternatives weighed, the dial settings, and a link to the evidence that justified it.
Undocumented or wrongly-documented behaviour is treated as a defect, not a detail.

## Clauses

- **DD-01 · Rationale is mandatory.** Every decision records *why this and not the
  alternatives*. "It worked" is not a rationale; "chose Aura trial over a VM because it's
  $0 for 8 days and the GraphStore interface makes the swap a config change" is.
- **DD-02 · Right-sized record.** Big/durable decisions → an ADR (`docs/decisions/`).
  Routine actions → a `ledger.md` note. Either way it is written down at decision time, not
  reconstructed later.
- **DD-03 · Dial settings are part of the record.** When `LAW-01` exposes a dial, the chosen
  setting and its trigger condition are captured ("if cost > $X, prefer Free tier").
- **DD-04 · Evidence-linked.** A decision cites the gate result, ledger rows, or metric that
  backs it — so it can be *re-evaluated* when the evidence changes (closing the loop to
  `LAW-01`).
- **DD-05 · Defensible under challenge.** Any decision must survive the question "show me why"
  with a pointer to the record. If it can't, it is re-opened, not defended by memory.
- **DD-06 · Wrong documentation is a bug.** Docs that disagree with reality are filed and
  fixed like code defects (ties to the maintenance loop's "charter must match reality").

## Why

This is the law that protects a too-big-for-one-head project from its own forgotten choices,
and the system from regulatory/audit exposure (e.g. proving *why* data sits in a given
region — see the GRC department + data-residency runbooks).
