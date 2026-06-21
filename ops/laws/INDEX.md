# `ops/laws/` — the operational constitution

Cross-cutting laws that bind **every** department, charter, gate, and runbook. Where a
per-department charter says *what* a subsystem does, these laws say *how every operation
must behave*. A charter may add stricter rules; it may never contradict a law.

| Law | Governs | One line |
| --- | --- | --- |
| [LAW-01](LAW-01-continuous-improvement.md) | **everything** | THE FIRST LAW — every decision is a tunable proposal; evidence moves dials, the operator turns them |
| [LAW-02](LAW-02-successful-execution.md) | what "done" means | success is *proven* (postcondition + ledger), never assumed from exit 0 |
| [LAW-03](LAW-03-recovery.md) | getting back | every action is reversible (rollback) or a flagged Point of No Return |
| [LAW-04](LAW-04-communication.md) | legibility | confirm before spend/PNR; show live progress; failures explain themselves |
| [LAW-05](LAW-05-defendable-decision.md) | accountability | every choice has a recorded, evidence-linked "why" |

## Precedence

1. **LAW-01 is supreme** — it grants the right to revise all others (with a recorded rationale).
2. The other four are co-equal constraints every action must satisfy simultaneously:
   *prove it worked (02), be able to undo it (03), say what you're doing (04), record why (05).*
3. A department charter is **subordinate**: stricter-or-equal, never looser.

## How a law changes

Per LAW-01: propose → cite ledger evidence → record a LAW-05 rationale (ADR for a law-level
change) → update the law + its changelog. Laws are living, but never silently.
