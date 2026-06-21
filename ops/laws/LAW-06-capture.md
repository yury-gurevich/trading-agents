# LAW-06 · Capture — the conversation is part of the work

> Decision-rich discussion is not a side-channel to the implementation; it **is** part of
> it. A meaningful conversation that ends in chat and not in the repo is unfinished work.

## Statement

When a conversation produces a **decision, a trade-off, a discovered constraint, or a
ruled-out option**, capturing it in the repo is part of that unit of work — done *while the
reasoning is fresh*, not "later". Chat logs are volatile; the repo is the memory.

## Clauses

- **CP-01 · Capture is a deliverable.** A discussion that moved a decision is not "done" until
  its outcome and reasoning are in `docs/design-log.md` (in-flight) or an ADR (closed
  question). Same standard as "a law clause is not green until a test cites it."
- **CP-02 · Record the road *not* taken.** Capture the **ruled-out** options and *why* — the
  rejected branches are the most valuable and the first thing lost. ("We didn't tunnel
  because…" is worth more later than "we chose in-memory.")
- **CP-03 · Capture at the moment of insight.** Don't wait for the feature to ship; context
  and chat evaporate (and get summarised away). Write it down when it's understood.
- **CP-04 · Distil, don't transcribe.** Capture the *decision, options, rationale, status* —
  not the full back-and-forth. The design-log is a log of conclusions, not a chat dump.
- **CP-05 · Uncaptured = unmade.** A decision discussed but not recorded is treated as
  not-yet-made: it cannot be defended (LAW-05) and is liable to be silently re-litigated.

## Why it exists (operator insight, 2026-06-21)

This project regularly produces decision-rich conversations — boundaries, residency models,
platform/pack walls, backup trade-offs — that shaped the system more than any single commit.
A one-person product cannot afford to keep that reasoning in a chat transcript. This law
makes "write it down" a *step of the work*, closing the exact gap that LAW-05 only implies:
LAW-05 says every decision has a recorded *why*; LAW-06 says **producing that record is part
of doing the thing**, including the options you discarded along the way.

## Mechanism

- `docs/design-log.md` — in-flight threads (options, ruled-out, status OPEN/DRAFT/DECIDED).
- `docs/decisions/` (ADR) — when a thread closes a question "forever" (until LAW-01 re-opens).
- Graduation: a `design-log` entry that resolves becomes an ADR and is marked CLOSED.
