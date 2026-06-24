---
department: experimentation
tier: x cross-cutting
owner: operator + AI tuning loop
status: draft
version: 0.3
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

### What is IN / OUT (the boundary — every clause is a testable predicate)

**IN — an experiment is admissible only when ALL of these hold:**

1. the dial is declared via `tunable()` with **finite `ge` *and* `le`** and exactly **one owning process**;
2. the challenger value is the dial's **declared type** and lies **within `[ge, le]`**;
3. a **target metric** exists, is **computable from `RunMetrics`**, and has a **declared direction** (↑ or ↓ = better);
4. **≥ 1 guardrail metric**, each with a **numeric `max_regression`**;
5. it can run on a **controlled `as_of` that has data**, repeatably, for **N trials**;
6. the change is **reversible** (demote restores the prior champion) **or** registered as a **PNR** with a snapshot.

**OUT — refuse as an experiment if ANY of these holds (route it elsewhere):**

1. no finite bounds, or the value is unbounded / free-text → not loop-tunable;
2. it touches a **capital-at-risk amount, risk cap, PNR guard, or safety limit** → **ADR only**, never the loop;
3. it changes **code, graph schema, or a message contract** → **sprint + ADR**;
4. it has **no computable metric** or **no guardrail** → unmeasurable, so not an experiment;
5. it **cannot be placed on a controlled `as_of`** → the result is not evidence.

> The IN clauses are exactly the OPS-GATE checks (G-BND/MET/GRD/CTL); admissibility is *machine-decided*
> at registration, not argued case-by-case. Blind auto-promotion is always OUT — the operator is the gate
> (LAW-01 CI-03; automation is *earned*, CI-05).

### Two kinds of experiment (the IN/OUT above governs kind 1)

1. **Parameter experiment** — moves a `tunable()` dial by champion-vs-challenger evidence. Governed by
   the IN/OUT + gates here; recorded as the **experiment report** (OPS-OBS) on the graph.
2. **Research probe** — asks a *question about the system* ("does the LLM understand our parameters?",
   "does feed X cover name Y?"). It does **not** move a dial; it *informs* one. Recorded in the
   **[experiments log](../../../docs/research/experiments/INDEX.md)** under **Purpose · Process ·
   Delivery · Interpretation**. A probe whose *Interpretation* recommends a dial change then hands off
   to a parameter experiment — the probe never moves the dial itself.

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

**Validate-then-run.** Every gate below is checked **before any feed call or graph write**. The
governing rule: *no runtime error for anything we can anticipate at runtime* — a foreseeable failure is
a **red gate**, never a mid-run stack trace. The two groups are **admissibility** (is this a valid
experiment?) and **readiness** (can it actually run cleanly right now?).

**Admissibility gates** (these *are* the IN clauses — machine-decided at registration):

| Gate ID | Check | Pass criteria | On fail |
| --- | --- | --- | --- |
| G-HYP | hypothesis recorded (dial, expected direction, why) | present | block |
| G-MET | target metric named with direction (↑/↓) | present + computable from RunMetrics | block |
| G-GRD | ≥ 1 guardrail metric, each with a numeric max-regression | present | block |
| G-BND | challenger overrides are the right **type** and within each tunable's `ge/le` | all valid (CI-1) | block |
| G-CTL | champion + challenger run on the **same** `as_of` | equal as_of | block |

**Readiness gates** (anticipate the runtime failure; fail fast with a specific message):

| Gate ID | Anticipated failure | Pass criteria | On fail |
| --- | --- | --- | --- |
| G-DEP | graph / the experiment's feed unreachable or uncredentialed | `DEP-NEO4J` + the needed `DEP-FEED` green | block (name the dep) |
| G-DATA | the chosen `as_of` returns nothing for the universe | non-empty bars for the run window | block ("no data at as_of") |
| G-REG | target / guardrail metric not registered or not computable | every named metric resolves in CI-2 | block (name the metric) |
| G-CHMP | no current champion to compare against / roll back to | a champion ParameterSet exists | block (seed one first) |
| G-BUDGET | N trials would exhaust an API rate/budget (the DL-17 429 lesson) | headroom ≥ N × per-run cost | warn + suggest pacing/N |

**Fail-safe at run time.** If a fault still occurs after gates pass (network blip, partial feed), the
trial **aborts cleanly**: its `RunMetrics` is marked `invalid` with the cause, no partial batch is
written, and the experiment continues with the remaining trials (or reports `INCONCLUSIVE`). A fault is
data, not a crash.

## OPS-ACT · Actions / Runbooks (the experiment lifecycle)

| Action | Gates required | Idempotent | Dry-run | Postcondition (proof) | Rollback | Blast radius |
| --- | --- | --- | --- | --- | --- | --- |
| register experiment | G-HYP/MET/GRD/BND/CTL | yes | n/a | `Experiment` node created (admissible) | delete node | none |
| run trials | G-DEP/DATA/REG/CHMP/BUDGET | yes (per run_id) | `--whatif` | `RunMetrics` per trial, linked (or `invalid`) | none (read-only on prod state) | reads feeds only |
| compare | — | yes | n/a | **the experiment report** (below) + PASS/FAIL vs gate | none | none |
| promote | report PASS + operator confirm | no (see PNR) | preview | champion flipped; ACTIVATE delivers; report + ledger row written | demote prior champion (recorded) | the governed process |
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

- Never **start a run with an unmet gate** — validate-then-run; an anticipatable failure is a red gate,
  never a mid-run error or a half-written batch (a real fault aborts the trial as `invalid`, recorded).
- Never **promote without a `PROMOTE` report** (what changed / why / the gain / guardrails) *and* an
  operator confirmation (LAW-01 CI-03). No silent dial moves.
- Never compare champion vs challenger on **different `as_of`** (uncontrolled — invalid result).
- Never move a value **outside its `tunable` bounds** or of the wrong type (G-BND rejects it).
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

### The experiment report (mandatory output of every experiment)

Every experiment ends in **one concise report** — the artifact the operator reads to turn (or refuse)
the dial. It is generated from the graph and condensed into a single ledger row. Fixed fields:

| Field | Content |
| --- | --- |
| **What changed** | the dial(s) and **champion → challenger** value(s); the two `ParameterSet` ids |
| **Why** | the hypothesis — expected direction + rationale (G-HYP) |
| **Did it deliver?** | target metric: **champion vs challenger**, the **absolute delta and % gain**, over **N trials** (mean ± spread), against the declared direction |
| **Guardrails** | each guardrail: champion vs challenger value, within `max_regression`? (✓ / ✗) |
| **Verdict** | `PROMOTE` / `REJECT` / `INCONCLUSIVE` (spread ≥ delta) + a one-line reason |
| **Provenance** | experiment id, run ids, `as_of`, N, parameter_set ids, ledger row ref (LAW-05) |

Rules: state the gain **in the metric's own units *and* as a %**; `INCONCLUSIVE` (variance swamps the
delta — the DL-17 run-3 case) is a **first-class outcome**, not a failure; **no promotion without a
`PROMOTE` report + operator confirm**. The report is the LAW-05 defendable-decision record for the dial.

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

**When you touch `agents/**/settings*.py`** (add/retire a `tunable`) → the CI-1 catalogue updates
*automatically* (auto-registration), and the CI completeness gate fails if a settings class escapes it
— so the only manual duty is registering the dial's **metric** in CI-2 (the `G-REG` gate) to make it
loop-eligible. **When you add a metric** → name its direction (↑/↓ = better) here. Re-verify the
OPS-DOWN neighbours (the governed process).

## Changelog

| Version | Date | Change |
| --- | --- | --- |
| 0.1 | 2026-06-24 | initial draft — operationalizes LAW-01 for the trading pipeline; implements ADR-0013 |
| 0.2 | 2026-06-24 | tightened IN/OUT to testable predicates; added readiness gates (validate-then-run, no anticipatable runtime error) + fail-safe abort; made the concise experiment report a mandatory output |
| 0.3 | 2026-06-24 | distinguished two experiment kinds — *parameter experiment* (the report) vs *research probe* (purpose/process/delivery/interpretation, in the experiments log); a probe informs a dial, it never moves it |
