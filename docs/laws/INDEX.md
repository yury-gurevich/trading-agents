# Laws index — what each file in this folder does

**How to use:** before editing any law file, check the "Owned by" and "Change procedure"
columns. Most files are governed by a convention that requires a logged amendment or
a new ADR. See [conventions.md](conventions.md) for the full rules.

---

## Umbrella files (system-level knowledge)

| File | Purpose | Change procedure |
| --- | --- | --- |
| [README.md](README.md) | Law book philosophy: why laws exist, independence rule, relation to PRD | Edit freely; no ADR required |
| [conventions.md](conventions.md) | Clause-ID scheme, stability levels, gray→green definition, lock rules, independence rule | Amend only via a new ADR or RFC; log the change |
| [_TEMPLATE.md](_TEMPLATE.md) | Law schema every agent follows — **LOCKED v1 (S69)** | Do not edit without completing a new full author→reconcile→test→green cycle on `provider/laws/laws.md` first |
| [flow.md](flow.md) | The inter-agent choreography — the **only** place `A → B` relationships are recorded | Edit only when the message contract between two agents changes; update `ledger.md` |
| [dependencies.md](dependencies.md) | Layer-0 dependency charter: `DEP-NEO4J`, `DEP-BUS`, `DEP-FEED`, `DEP-BROKER`; the "green bill of health" that must pass before any agent can be green | Amend when a new external dependency is added or retired |
| [stack.md](stack.md) | Layer-0 technology stack charter: Azure-native rule + Neo4j exception + SaaS vendor list + transitional retirement triggers | Governed by ADR-0009; requires a new ADR to change any rule |
| [drift-register.md](drift-register.md) | Central worklist of every law-vs-code drift (OPEN / CORRECTED / CLOSED); **the escalation point for discovered gaps** | Add rows freely; update status when a sprint corrects a drift |
| [ledger.md](ledger.md) | Gray→green rollup across all agents — "the landscape"; how many clauses are 🟩 per agent | Update after each sprint that closes green clauses; add a row when a new agent law is authored |

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
| provider | ✅ LOCKED v1 (S69) | 23 / 43 | Template stress-test complete; pattern is now the reference copy |
| analyst | ✅ LOCKED v1 (S70) | 24 / 43 | |
| scanner | ✅ LOCKED v1 (S70) | 18 / 39 | |
| portfolio_manager | ✅ LOCKED v1 (S70) | 23 / 43 | |
| execution | ✅ LOCKED v1 (S70) | 30 / 49 | |
| monitor | ✅ LOCKED v1 (S71) | 19 / 40 | |
| reporter | ✅ LOCKED v1 (S71) | 17 / 40 | |
| forecaster | ✅ LOCKED v1 (S71) | 15 / 46 | |
| operator | ✅ LOCKED v1 (S71) | 14 / 51 | |
| supervisor | ✅ LOCKED v1 (S71) | 21 / 49 | |
| curator | ✅ LOCKED v1 (S71) | 20 / 48 | |
| researcher | ✅ LOCKED v1 (S71) | 18 / 44 | |

See [ledger.md](ledger.md) for the canonical version of this table.

---

## Adding a new agent law

1. Copy `_TEMPLATE.md` to `agents/<name>/laws/laws.md`.
2. Copy `_TEMPLATE.md` test-plan stub to `agents/<name>/laws/test-plan.md`.
3. Author all clauses from first principles (do not copy from another agent's `laws.md`).
4. Run the full author → reconcile → test → green cycle.
5. Lock (`DRAFT → LOCKED v1`) only when the cycle is complete.
6. Update [ledger.md](ledger.md) and this INDEX.
