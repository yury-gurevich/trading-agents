# LAW-01 · Continuous Improvement — THE FIRST LAW

> The supreme law. It is the only law that is not itself a proposal. Every other law,
> boundary, charter, gate, and script **is** a proposal — open to question and revision.

## Statement

**Nothing here is final except the duty to improve it.** Every decision is a *proposal*:
it must be questioned, it exposes **dials** (parameters / "if-this-then-this" choices), and
it may be changed when evidence shows a better setting. Boundaries between departments,
the contents of charters, the order of steps — all are modifiable.

## Clauses

- **CI-01 · Everything is a proposal.** No charter, gate, or runbook is "locked forever".
  (Contrast ADRs, which close a question *until* re-opened by this law with new evidence.)
- **CI-02 · Decisions expose dials.** A decision that can't be parameterized or reversed is
  suspect; prefer "if X then A, else B" with X named, so the dial is visible and tunable.
- **CI-03 · Evidence moves dials, the operator turns them.** Changes are justified by the
  ledger (`maintenance/ledger.md`) and proposed by the tuning loop; the operator approves.
  No blind auto-tuning. (Same shape as ADR-0010 champion–challenger.)
- **CI-04 · Improvement is recorded.** Every dial moved cites the evidence that moved it and
  links to a `LAW-05` defendable-decision record. Change without rationale is forbidden.
- **CI-05 · Graduation to automation is earned.** A human-gated step becomes automatic only
  after it has demonstrated a clean track record in the ledger — never by assumption.

## Why it is first

A one-person product cannot afford frozen decisions made when less was known. This law
guarantees the system can always be *re-questioned and re-tuned* without guilt — and that
every other law in `ops/` inherits a built-in revision path instead of calcifying.
