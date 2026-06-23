---
department: experimentation
tier: x cross-cutting
owner: operator + AI tuning loop
status: draft
version: 0.1
implements_with: [docs/decisions/0013-continuous-improvement-system.md, docs/sprints/sprint-90-ci1-parameter-catalogue.md, scripts/run_local.py]
---

# Charter — Experimentation & Tuning (the trading-pipeline improvement loop)

> The operational law for **how a parameter is changed by evidence**. LAW-01 makes every
> decision a tunable proposal moved by the ledger and turned by the operator; this charter is
> the concrete process that earns the right to move a dial in the **trading pipeline**.
> `ops/maintenance/loop.md` already governs *infrastructure* tuning (charters, runbooks,
> measured by failure-rate / duration / cost). This charter governs *pipeline* tuning (ingest,
> scanner, analyst, PM, execution, monitor, forecaster, operator), measured by `RunMetrics` on
> the graph. **Same loop (LAW-01), different subject and store.** It implements ADR-0013.

## OPS-IDN · Identity

Cross-cutting. The single place that governs how a `tunable()`'s value is changed by evidence:
register a hypothesis → run champion vs challenger under control → measure on the graph →
compare → gate → promote or retire. It owns the **method**, not the parameters (those are owned
by each agent via `tunable()`) nor the meaning of a metric (each process defines its own). It
exists so no dial moves on a hunch and every move is recorded (LAW-01 CI-04, LAW-05).

### What is IN / OUT (the expectation boundary)

**IN — eligible for the loop:**
- Any value declared via `tunable()` with finite `ge/le` bounds and an owning process.
- Any change with a **measurable target metric** and **at least one guardrail metric**.
- Champion↔challenger comparison, sweeps within bounds, promotion of a winning `ParameterSet`.

**OUT — not an experiment:**
- Structural/code change (new agent, graph schema, message contract) → a **sprint + ADR**, not a dial.
- Unbounded or safety-critical constants (risk caps, capital limits, PNR guards) → changed **only by ADR**, never by the loop.
- Anything with no metric or no guardrail — if you cannot show better/worse, it is not an experiment.
- Blind auto-promotion — the operator is always the gate (LAW-01 CI-03; graduation to automation is *earned*, CI-05).

## OPS-OWN · Owns (single-writer)

- The `Experiment`, `RunMetrics`, `ParameterSet`, `Promotion` graph nodes (ADR-0013) — the experiment record.
- The experiment rows in `ops/maintenance/ledger.md` (one per experiment, one per promotion).
- This charter (the method). It does **not** own the parameters (agents do) or metric definitions (each process does).

## OPS-UP · Upstream (needs)

- **CI-1 catalogue** — the bounds a challenger is validated against.
- **CI-2 RunMetrics** on the graph (`DEP-NEO4J` green) — the measurement substrate.
- **A reproducible harness** — `run_local` / the live pipeline — and a fixed `as_of` for control.
- **The owning process's metric** — what "better" means there (ingest: degradation rate ↓; forecaster: IC ↑; …).

## OPS-DOWN · Downstream (blast radius)

- Promotion flips the **active** `ParameterSet` delivered via ACTIVATE → changes live agent behaviour.
  Blast radius = whatever the promoted set governs (ingest pacing → data quality → every downstream stage;
  PM sizing → capital at risk).
- A wrong metric or a missing guardrail can promote a regression — contained by OPS-GATE + N-trial variance.

## OPS-GATE · Preflight gates (GO / NO-GO)

| Gate ID | Check | Pass criteria | On fail |
| --- | --- | --- | --- |
| G-HYP | hypothesis recorded (dial, expected direction, why) | present | block |
| G-MET | target metric named with direction (↑/↓) | present + computable from RunMetrics | block |
| G-GRD | ≥1 guardrail metric, each with a max-regression | present | block |
| G-BND | challenger overrides within each tunable's ge/le | all in-bounds (CI-1) | block |
| G-CTL | champion + challenger run on the **same** `as_of` | equal as_of | block |
| G-VAR | trials N ≥ required for variance-prone / rate-limited metrics | N met | warn |

## OPS-ACT · Actions / Runbooks (the experiment lifecycle)

| Action | Gates required | Idempotent | Dry-run | Postcondition (proof) | Rollback | Blast radius |
| --- | --- | --- | --- | --- | --- | --- |
| register experiment | G-HYP/MET/GRD | yes | n/a | `Experiment` node created | delete node | none |
| run challenger | G-BND/CTL/VAR | yes (per run_id) | `--whatif` | `RunMetrics` written + linked | none (read-only on prod state) | reads feeds only |
| compare | — | yes | n/a | comparison table; PASS/FAIL vs gate | none | none |
| promote | gate PASS + operator confirm | no (see PNR) | preview | champion flipped; ACTIVATE delivers | demote prior champion (recorded) | the governed process |
| retire | — | yes | n/a | set `status=retired` | restore status | none |

**Lifecycle:** register → run champion+challenger (same `as_of`, N trials) → measure (`RunMetrics`)
→ compare → gate → operator confirm → promote | retire → ledger row. This is the DL-17 hand-loop,
made into a recorded, repeatable operation.

## OPS-PNR · Points of no return

| PNR ID | Irreversible step | Why it can't be undone | Guard |
| --- | --- | --- | --- |
| PNR-EXP-01 | promote a set governing **capital-at-risk** behaviour (PM sizing, execution) to champion | live orders change before a revert can land | gate PASS + blast radius shown + snapshot of current champion + interactive confirm |

Ingest/scanner/analyst-only promotions are reversible (demote restores the prior champion) → they are
**Rollbacks, not PNRs**.

## OPS-REC · Recovery

- **Backup:** the prior champion `ParameterSet` is retained (`status=retired`, never deleted); every
  promotion writes a `Promotion` node.
- **Restore:** re-promote the prior champion id; ACTIVATE redelivers it.
- **RPO / RTO:** RPO = the last champion (always retained); RTO = one ACTIVATE cycle.

## OPS-NEV · Never

- Never promote without a **passing gate** *and* an **operator confirmation** (LAW-01 CI-03).
- Never compare champion vs challenger on **different `as_of`** (uncontrolled — invalid result).
- Never move a value **outside its `tunable` bounds** (CI-1 rejects it).
- Never run a capital/safety cap through the loop — those change by **ADR only**.
- Never edit a past `ledger` row or `RunMetrics` node — append-only (LAW-06).

## OPS-OBS · Observability (how we keep track + where it is housed)

- **State (graph):** `Experiment` / `RunMetrics` / `ParameterSet` / `Promotion` nodes — the queryable
  "which knobs produced which outcome" lineage. This is the durable record.
- **Audit (ledger):** one `ops/maintenance/ledger.md` row per experiment and per promotion — the
  Loop-2 training input.
- **Decisions (docs):** a **method** change (a new metric, a new guardrail policy, a new in/out rule)
  is an ADR or design-log entry — not an experiment. The charter records the standing process.
- **Surfaces:** `experiment <id>` (compare table), `metrics --process <p>`, `paramset --active`.

## OPS-TUNE · Tuning (the loop assessing itself — LAW-01 applied to LAW-01)

- **Assess:** experiment→promotion ratio, regressions the guardrails caught (vs missed), time-to-decision,
  number of blind reverts.
- **Improve:** tighten a guardrail that let a regression through; raise N where variance bit (DL-17 run 3);
  retire a dial that never moves its metric. Operator approves every change.

## OPS-PARAM · Parameters (meta-knobs of the experimentation system itself)

| Param | Default | Range / options | Effect |
| --- | --- | --- | --- |
| `trials_per_experiment` (N) | 3 | 1–20 | variance control for rate-limited / noisy metrics |
| `min_delta` | per-metric | ≥ 0 | how much better the challenger must be to win |
| `sweep_grid` | per-target | within CI-1 bounds | candidate generation for the CI-6 optimiser |

## OPS-MNT · Maintenance trigger

**When you touch `agents/**/settings*.py`** (add/retire a `tunable`) → refresh the CI-1 catalogue and,
if the dial becomes loop-eligible, this charter's IN/OUT list. **When you add a metric** → register it in
CI-2 and name its direction (↑/↓ = better) here. Re-verify the OPS-DOWN neighbours (the governed process).

## Changelog

| Version | Date | Change |
| --- | --- | --- |
| 0.1 | 2026-06-24 | initial draft — operationalizes LAW-01 for the trading pipeline; implements ADR-0013 |
