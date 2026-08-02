# Laws index — what each file in this folder does

**How to use:** before editing any law file, check the "Owned by" and "Change procedure"
columns. Most files are governed by a convention that requires a logged amendment or
a new ADR. See [conventions.md](conventions.md) for the full rules.

---

## Umbrella files (system-level knowledge)

| File | Purpose | Change procedure |
| --- | --- | --- |
| [README.md](README.md) | Law book philosophy: why laws exist, independence rule, relation to PRD | Edit freely; no ADR required |
| [conventions.md](conventions.md) | Clause-ID scheme, stability levels, gray→green definition, lock rules, independence rule, clause-summary fidelity (§7a) | Amend only via a new ADR or RFC; log the change |
| [_TEMPLATE.md](_TEMPLATE.md) | Law schema every agent follows — **LOCKED v1 (S69)** | Do not edit without completing a new full author→reconcile→test→green cycle on `provider/laws/laws.md` first |
| [flow.md](flow.md) | The inter-agent choreography — the **only** place `A → B` relationships are recorded | Edit only when the message contract between two agents changes; update `ledger.md` |
| [dependencies.md](dependencies.md) | Layer-0 dependency charter: `DEP-POSTGRES`, `DEP-BUS`, `DEP-FEED`, `DEP-BROKER`; the "green bill of health" that must pass before any agent can be green | Amend when a new external dependency is added or retired |
| [stack.md](stack.md) | Layer-0 technology stack charter: Azure-native rule + ADR-0014 PostgreSQL exception + SaaS vendor list + transitional retirement triggers | Governed by ADR-0009; requires a new ADR to change any rule |
| [drift-register.md](drift-register.md) | Central worklist of every law-vs-code drift (OPEN / CORRECTED / CLOSED); **the escalation point for discovered gaps** | Add rows freely; update status when a sprint corrects a drift |
| [ledger.md](ledger.md) | Gray→green rollup across all agents — "the landscape"; how many clauses are 🟩 per agent | Update after each sprint that closes green clauses; add a row when a new agent law is authored |
| [functionality-checks.md](functionality-checks.md) | Per-sprint real-environment functionality checks — what was exercised live, the result, and teardown confirmation (LAW-02) | Append a row at the close of every sprint; tear down test artifacts first |
| [cage-audit.md](cage-audit.md) | DL-19 "no cages" audit: classifies every agent's prohibition surface as boundary vs cage; verdict = not a cage, plus the discovery-surface gap | Re-run when an agent's law surface changes materially |
| [discovery-surfaces.md](discovery-surfaces.md) | DL-19 register: names what each discoverer agent is free to discover (Owns / Walls / Search / gate); the creative space made legible | Update when an agent's owned space, dials, or bounding clauses change |

---

## Per-agent law files (live with each agent)

Each agent's law files live at `agents/<name>/laws/`:

| File | Purpose |
| --- | --- |
| `laws.md` | The locked constitution for that agent — every clause is ID'd and stability-rated |
| `test-plan.md` | Living citation map — each clause row cites a test that proves it (gray ⬜ → green 🟩) |

**Status:**

| Agent | `laws.md` | Green clauses | Notes |
| --- | --- | --- | --- |
| provider | ✅ LOCKED v1 (S69) | 20 / 43 | S156 citation check reconciled to test-plan rows; 22 law clauses still have no row (S157 warn-only backlog) |
| analyst | ✅ LOCKED **v1.1** (S152) | 24 / 34 | S156 citation check reconciled to test-plan rows; 12 law clauses still have no row (S157 warn-only backlog) |
| scanner | ✅ LOCKED v1 (S70) | 16 / 26 | S156 citation check reconciled to test-plan rows; 13 law clauses still have no row (S157 warn-only backlog) |
| portfolio_manager | ✅ LOCKED v1 (S70) | 30 / 39 | S156 citation check reconciled to test-plan rows; 12 law clauses still have no row (S157 warn-only backlog) |
| deliberator | ✅ LOCKED v1 (S153) | 0 / 48 | New DL-80/ADR-0020 agent; all clauses start ⬜ |
| execution | ✅ LOCKED **v1.1** (S152) | 28 / 44 | S156 citation check reconciled to test-plan rows; 13 law clauses still have no row (S157 warn-only backlog) |
| monitor | ✅ LOCKED v1 (S71) | 20 / 39 | S156 citation check reconciled to test-plan rows; 7 law clauses still have no row (S157 warn-only backlog) |
| reporter | ✅ LOCKED v1 (S71) | 20 / 38 | S156 removed orphan `RPT-OBS-03`; `RPT-TYP-03` still has no row (S157 warn-only backlog) |
| forecaster | ✅ LOCKED v1 (S71) | 16 / 45 | S156 citation check reconciled to test-plan rows |
| operator | ✅ LOCKED v1 (S71) | 15 / 50 | S156 citation check reconciled to test-plan rows |
| supervisor | ✅ LOCKED v1 (S71) | 20 / 48 | S156 citation check reconciled to test-plan rows |
| curator | ✅ LOCKED v1 (S71) | 22 / 47 | S156 citation check reconciled to test-plan rows |
| researcher | ✅ LOCKED v1 (S71) | 19 / 43 | S156 citation check reconciled to test-plan rows |
| master | ✅ LOCKED v1 (S73) | 10 / 18 | P15 bootstrap agent; RSA/Key Vault clauses deferred S74 |

See [ledger.md](ledger.md) for the canonical version of this table.

---

## Adding a new agent law

1. Copy `_TEMPLATE.md` to `agents/<name>/laws/laws.md`.
2. Copy `_TEMPLATE.md` test-plan stub to `agents/<name>/laws/test-plan.md`.
3. Author all clauses from first principles (do not copy from another agent's `laws.md`).
4. Run the full author → reconcile → test → green cycle.
5. Lock (`DRAFT → LOCKED v1`) only when the cycle is complete.
6. Update [ledger.md](ledger.md) and this INDEX.
