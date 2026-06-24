# `ops/` index — laws, departments, and how to navigate

**How to use:** before you touch anything operational — (1) the **laws** bind every action,
(2) find the **department** that owns it and run its gates *before* acting, (3) if you change
how it works, update its charter in the same change (`maintenance/loop.md`).

## The constitution (binds everything)

| File | Answers |
| --- | --- |
| [laws/INDEX.md](laws/INDEX.md) | The 6 cross-cutting laws — what every operation must obey |
| [laws/LAW-01…](laws/LAW-01-continuous-improvement.md) | THE FIRST LAW: continuous improvement (everything is a tunable proposal) |

## Departments (the IT silos)

| Department | Charter | Status |
| --- | --- | --- |
| [Security & IAM](departments/security-iam/charter.md) | ✅ drafted | worked example |
| [Experimentation & Tuning](departments/experimentation/charter.md) | ✅ drafted | cross-cutting; governs trading-pipeline parameter tuning (ADR-0013, LAW-01) |
| [Housekeeping & Navigability](departments/housekeeping/charter.md) | ✅ drafted | cross-cutting; keeps the repo legible — INDEX/README/root/folder/git-size hygiene. Future **Librarian** agent |
| Release Engineering (CI-CD) | ⬜ stub | charter pending |
| Platform / Infrastructure | ⬜ stub | charter pending |
| Data & Storage (DBA) | ⬜ stub | charter pending (Aura→VM lives here) |
| Networking | ⬜ stub | charter pending (custom domains) |
| SRE / Observability | ⬜ stub | charter pending |
| GRC (Governance/Risk/Compliance) | ⬜ stub | charter pending (residency, audit, ledger) |
| Service Desk | ⬜ stub | charter pending (the `ta` CLI UX) |

## Operator CLI

`pwsh infra/ta.ps1` is the one entry point that drives all of this — run it with no args for the
menu. `ta status` (dashboard), `ta doctor` (preflight gates), `ta deploy up|down`, `ta aura …`,
`ta graph`. Policy lives here in `ops/`; `ta` is the driver.

## Framework files

| File | Answers |
| --- | --- |
| [README.md](README.md) | What is this realm, why it exists, the principles |
| [org-map.md](org-map.md) | The departments, their remit, the dependency direction |
| [scenarios.md](scenarios.md) | The situations we must be ready for (disaster, growth, cost, compliance…) |
| [_template/charter.md](_template/charter.md) | The charter schema every department fills |
| [maintenance/loop.md](maintenance/loop.md) | The maintenance + LLM tuning loop |
| [maintenance/ledger.md](maintenance/ledger.md) | Append-only trace of every action |
| [maintenance/points-of-no-return.md](maintenance/points-of-no-return.md) | Every irreversible step, system-wide |

## Adding a department charter

1. Copy `_template/charter.md` → `departments/<name>/charter.md`; fill every section.
2. Add its remit to `org-map.md`; list its Points of No Return.
3. Wire its gates into `ta <dept> preflight`.
4. Confirm it satisfies all 6 laws (stricter-or-equal, never looser).
