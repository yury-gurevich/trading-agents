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
| provider | ✅ LOCKED v1.3 (DL-203) | 17 / 62 | DL-203 reconciles `PARAM` only; S213 adds FMP `^VIX` regime freshness evidence and proves `PROV-OUT-03` without adding clauses; S187 adds PARAM rows only; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
| analyst | ✅ LOCKED v1.6 (DL-203) | 26 / 49 | DL-203 reconciles `PARAM` only; S211 adds and proves `ANLZ-OBS-06` for decision-time favourable-excursion target evidence and missing-estimate rejection; S205 rewrites `ANLZ-TYP-01` into required fields without moving the count; S198 declares and proves `ANLZ-OBS-05`; S156 citation check plus S186's `ANLZ-OBS-04`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
| scanner | ✅ LOCKED v1.3 (DL-203) | 18 / 41 | DL-203 reconciles `PARAM` only; S205 rewrites `SCAN-TYP-01` into required fields and closes DRIFT-047 without moving the count; S183's `SCAN-OUT-06`/`SCAN-OUT-07`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
| portfolio_manager | ✅ LOCKED v1 (S70), amended **v1.9** (DL-203) | 31 / 50 | DL-203 reconciles `PARAM` only; S220 amends and re-proves `PM-NEV-08` / `PM-OBS-03`: correlated issuers contribute on the ADR-0030 `0.50..0.90` ramp and gate detail renders applied weights; S211 adds and proves `PM-OBS-05`: reward-risk compares measured target evidence against stop risk and can reject measured upside below measured downside at the configured floor; S210 amends `PM-NEV-06`/`PM-NEV-08`/`PM-NEV-09` so concentration ratios use deployed capital and deployment-floor evidence is explicit without moving the count; S208 declares and proves `PM-OBS-04`; S197 declared and proved `PM-OBS-03`; S184 made PM-NEV-07/08/09 green and closed the v1.3 widened PM-NEV-06 and PM-TYP-03 rows; S204 gives every clause a row and makes rowless clauses a hard gate |
| deliberator | ✅ LOCKED v1.9 (DL-203) | 23 / 56 | DL-203 reconciles `PARAM` only; S222 moves the vendor adapters to `kernel/` and proves `DLIB-SEC-02` key containment; S214 narrows `vetoed_tickers` to `overturn` verdicts only, routes unreadable judge answers through loud fail-open, and proves `DLIB-OUT-04`; S206 adds and proves `DLIB-NEV-08`; S205 rewrites and proves `DLIB-TYP-01`; S200 adds `DLIB-OBS-07` and turns `DLIB-IDM-02` green by hashing the system prompt too; S199 adds `DLIB-OBS-05`/`DLIB-OBS-06`; S172 proves concurrent-order record order and pending-reply handling; S194 added `DLIB-OBS-04`; S189 added stop-reason audit evidence; S167 added `DLIB-OBS-03` proof |
| execution | ✅ LOCKED **v1.9** (S230) | 37 / 63 | S230 adds/proves `EXEC-OBS-06`: the broker stop is the PM-decided stop, read through the shared resolver, and a mismatched live stop is replaced in place with `replaced_at`/`replaces` markers; S227 adds/proves `EXEC-NEV-07`: degraded `RunRequest`s hold buys without deliberation wait while exits and protective stops continue; DL-203 reconciles `PARAM` only; S209 amends `EXEC-OBS-05` so the stale-order sweep compares stop identity, not liveness views, without moving the count; S205 rewrites `EXEC-TYP-03` into required fields and records DRIFT-060/DRIFT-061; S190 adds/proves `EXEC-OBS-05`, the missing `EXEC-OBS-03` liveness limb, and `EXEC-STA-05`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
| monitor | ✅ LOCKED v1.1 (S205) | 21 / 46 | S205 rewrites and proves `MON-TYP-01`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
| reporter | ✅ LOCKED v1.2 (S226) | 25 / 42 | S226 adds benchmark-relative `performance_metrics`, as-of bounded graph reads, contained performance failure, and backward-compatible snapshots; S205 rewrites `RPT-TYP-01`; S156 removed orphan `RPT-OBS-03`; S204 gives every clause a row and makes rowless clauses a hard gate |
| forecaster | ✅ LOCKED v1.3 (DL-203) | 17 / 45 | DL-203 reconciles `PARAM` only; S205 rewrites and proves `FORE-TYP-01`; counters are clauses proven / clauses declared |
| operator | ✅ LOCKED v1.3 (S205) | 18 / 50 | S222 proves `OPR-SEC-01` key containment and `OPR-DEP-01` Anthropic-only dependency; S205 rewrites and proves `OPR-TYP-01`; counters are clauses proven / clauses declared |
| supervisor | ✅ LOCKED v1.1 (S205) | 22 / 48 | S205 rewrites and proves `SUP-TYP-01`; S179 proves append-only `FaultResolution` retirement (`SUP-OBS-03`); counters are clauses proven / clauses declared |
| curator | ✅ LOCKED v1.1 (S205) | 23 / 47 | S205 rewrites and proves `CUR-TYP-01`; counters are clauses proven / clauses declared |
| researcher | ✅ LOCKED v1.2 (DL-203) | 20 / 43 | DL-203 reconciles `PARAM` only; S205 rewrites and proves `RES-TYP-01`; counters are clauses proven / clauses declared |
| master | ✅ LOCKED v1.6 (S232) | 19 / 47 | S232 adds and proves `MST-DEP-05` (substrate-only imports) and corrects `MST-NEV-01`/`MST-SEC-03`/`MST-DEP-03` to name the pack data actually consulted; DL-203 reconciles `PARAM` only; S217 adds and proves `MST-OUT-04` whole-fleet readiness and `MST-FAIL-05` classification; S205 rewrites and proves `MST-TYP-01`; S188 adds and proves credential-test handover guards; RSA/Key Vault clauses deferred S74; S204 gives every clause a row and makes rowless clauses a hard gate |
| dispatcher | ✅ LOCKED v1 (S229) | 25 / 30 | Component book under `orchestration/laws/dispatcher/`; scheduled placement and human-hold loop only; `orchestration.dispatcher.Dispatcher` named out of scope by DL-221; closes DRIFT-068 and DRIFT-069 |
| surfaces | ✅ LOCKED v1.1 (S229, S228) | 28 / 35 | Component book under `surfaces/laws/`; dashboard, CLI, MCP, chat and operator-intent write boundaries; selected-run scoping cites corrected DRIFT-022 |

See [ledger.md](ledger.md) for the canonical version of this table.

---

## Adding a new agent law

1. Copy `_TEMPLATE.md` to `agents/<name>/laws/laws.md`.
2. Copy `_TEMPLATE.md` test-plan stub to `agents/<name>/laws/test-plan.md`.
3. Author all clauses from first principles (do not copy from another agent's `laws.md`).
4. Run the full author → reconcile → test → green cycle.
5. Lock (`DRAFT → LOCKED v1`) only when the cycle is complete.
6. Update [ledger.md](ledger.md) and this INDEX.
