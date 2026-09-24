<!-- Agent: planning | Role: sprint handover -->
# Sprint 227 — an LLM-only outage holds the buys, not the run

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-227-an-llm-outage-holds-the-buys-not-the-run`
**Status:** BUILT
**Version:** *next available MINOR at merge*
**Effort:** M
**Decisions:** [DL-214](../design-log.md) (the proposal) · work-queue item **85** · partially reverses item **58** (operator-approved, 2026-09-24) · touches DRIFT-068 (the dispatcher has no law book)

> **Why this bump kind.** The dispatcher gains a run posture it did not have, and execution gains a
> buy outcome it did not have. That is a MINOR.

**Builder:** Codex. Every behaviour is pinned by a row in the test plan.
**If a number you measure differs from one written here, stop and report. Do not adjust and continue.**

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: execution **`EXEC-TRG-07`** (run-start reconciliation reads `RunRequest`),
**`EXEC-NEV-01`** (execution never decides what to trade), the deliberation-gate clauses around
S147/S166/S185, and master **`MST-OUT-04`** / **`MST-FAIL-05`** (what a failing fleet check means).

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### The law-cycle question — answered here, confirm it

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Yes, for execution.** Execution gains a guarantee: *on a run whose `RunRequest` declares the
degraded posture, a buy is never submitted and exits are never delayed.* That owes a law cycle in
`agents/execution/laws/laws.md` (new clause, version bump, Changelog line), a `test-plan.md` row, the
clause ID cited in the test docstring, and the rollup in **both** `docs/laws/ledger.md` and
`docs/laws/INDEX.md`. If you add a posture constant to `contracts/` (recommended, see Design
decision 2), that is part of the same cycle.

**The dispatcher has no law book** — DRIFT-068 is still OPEN. Do **not** create one here; append to
DRIFT-068's row (or add a new drift row) naming the new guarantee *"a degraded posture is placed only
when every failing check belongs to a pack-declared degradable agent"*.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `orchestration/fleet_readiness.py`, `scheduled_dispatch.py`, `scheduled_dispatch_gate.py`, `scheduled_dispatch_human.py` | `agents/master/laws/laws.md` (fleet-check section) + `docs/laws/drift-register.md` DRIFT-068 | `MST-OUT-04`, `MST-FAIL-05` define what the failures mean; DRIFT-068 records that no dispatcher law exists |
| `orchestration/packs/` (new degradable-agents declaration) | ADR-0012 (platform/pack wall) | No trading agent name may be hard-coded in orchestration code |
| `agents/execution/pm_execution.py`, `deliberation_gate.py`, `deliberation_posture.py`, `deliberation_faults.py` | `agents/execution/laws/laws.md` + `test-plan.md` | `EXEC-TRG-07`, `EXEC-NEV-01`, the S147/S166/S185 deliberation-gate clauses; ADR-0017, ADR-0022 |
| `surfaces/queries/fleet_check.py`, `surfaces/dashboard/…` | none (surfaces has no law book) | DL-211–DL-213 wording rules |

⚠️ **Exits must never wait and never be blocked.** ADR-0022 (*the veto gates buys, never exits*),
ADR-0017 and S147 all say so. If any change would delay or drop a sell or a protective stop, stop and
report.

---

## Goal

When the only failing fleet checks belong to agents the protective path does not need — today the
three deliberator peers and the operator — the dispatcher **places the run in a declared degraded
posture instead of holding it**. That run syncs with the broker, records fills, places protective
stops and runs the monitor; execution **submits no buy** and does not wait the deliberation grace;
the operator is told once, and the dashboard says *no new buys tonight* instead of *held*. Any other
failure — a data feed, the broker, the vault, master itself, an unparseable failure, or a stale check
— still holds the run exactly as today.

## Why (context)

On 2026-09-24 the Anthropic key ran out of credit ([DL-210](../design-log.md)). The master's fleet
check failed on four agents — `operator`, `deliberator-manager`, `deliberator-opponent`,
`deliberator-proponent`, all `anthropic … http_400` — and the S218 gate held `sched-2026-09-24` and
`sched-2026-09-25` **entirely**. That also stopped everything that uses no model: broker sync, fill
recording, **protective stop placement**, the monitor. Live consequence: `sched-2026-09-23`'s BMY buy
(16 @ limit 61.82, day) was at the broker and could fill at the open, with its stop waiting for the
first un-held run — `sched-2026-09-28`. The operator asked for this sprint on 2026-09-24 (*"yes, create
a sprint for Codex"*), which is the approval DL-214 said the spec needed to reverse part of item 58.

### Measured, 2026-09-24 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Failures on the drain, verbatim | `unrecoverable:deliberator-manager:anthropic:unrecoverable:http_400`, same for `deliberator-opponent`, `deliberator-proponent`, `operator` | *[measured 2026-09-24]* `FleetPreflight` rows at 23:26 and 00:26 UTC |
| Failure string shape | `<kind>:<agent_type>:<check>:<reason…>` | *[measured]* `agents/master/fleet_preflight.py:118` and the rows above; `transient:master:vault:TimeoutError` also occurs in tests |
| Deployed execution posture | `deliberation_posture = "binding"` | *[measured]* `agents/execution/settings.py`; `ExecutionRun` rows carry `binding` since S185 |
| Binding + no `DeliberationRun` + a buy | buys **dropped** after `deliberation_grace_seconds` (**900**), status `proceeded_unvetoed`, an **error** `DeliberationGraceExpired` fault | *[measured from code]* `deliberation_posture.py`, `deliberation_faults.py:92` |
| …and has that path ever run in production? | **No** — `ExecutionRun` by (status, posture): `applied/binding` 3, never `proceeded_unvetoed/binding` | *[measured 2026-09-24]* group-by over all `ExecutionRun` nodes |
| A mixed PMRun (buys + sells) waits the grace **as a whole** | sells delayed up to 900 s | *[measured from code]* `is_waiting` keys on `has_buy(order_set)` |
| Is `RunRequest` property-enforced by the vocabulary pack? | **No** — enforced labels are `AgentInstance, BrokerPositionSnapshot, DeliberationRun, ExecutionRun, Fill, FleetPreflight, LLMCall, Recommendation, RunHold, RunHoldAnswer` | *[measured]* `trading_graph_vocabulary.json` `properties` keys |
| Does execution already read `RunRequest`? | **Yes** — `EXEC-TRG-07` position sync | *[measured]* `agents/execution/laws/laws.md:63` |
| Batch trace stages | **8**, deliberation **not** among them | *[measured]* `orchestration/batch_trace.py:21` (`_COMPLETE_KEYS`) |
| Dashboard stage view | **9**, deliberation **is** one (`trading_observatory_views.py:120`) | *[measured]* — a degraded run would read *8/9 needs attention* unless handled |
| Deliberator/operator containers on a degraded night | refused activation by master (`ActivationRefused`), never write a `DeliberationRun` | *[measured from code]* `agents/master/activation_credentials.py` |
| What acceptance (`accept.py` / `RunSnapshot` verdict) says with no `DeliberationRun` | **unknown** | *[ASSUMED — not measured]* **Measure this first** (Step 3) on an in-memory cascade and paste the result |

---

## Scope — and what is deliberately NOT here

1. **A pack declares which agents a run can go without.** A new orchestration pack entry (e.g.
   `orchestration/packs/trading_run_postures.json`, baked into the image, **not** injected) lists the
   degradable agent types with a reason each: the three deliberator peers (*the veto gates buys only —
   ADR-0022*) and `operator` (*chat and explanation; no pipeline stage*). No agent name appears in
   orchestration code (ADR-0012).
2. **Readiness gains a `degraded` state.** `fleet_readiness` (or a function beside it) returns
   `degraded` when the latest fresh check failed **and every** failure parses as
   `<kind>:<agent>:<check>:<reason>` with `<agent>` in the degradable set. Anything else that fails —
   an agent outside the set, an unparseable string, a master-level failure — stays `failing`. A stale
   or missing check stays `unknown`. **Both still hold.**
3. **The dispatcher places a degraded run.** On `degraded`, `place_scheduled_run` places the
   `RunRequest` with `run_posture: "degraded"` and `degraded_by: [<failures>]`, releases any active
   hold as a `ready` check would, and returns `placed` with the posture. A normal run carries
   `run_posture: "normal"` (or the property is absent and read as normal — decide and record).
4. **Execution holds buys on a degraded run — immediately, not after the grace.** When the PMRun's
   `RunRequest` declares `degraded`: every `buy` is dropped **without waiting**, sells and protective
   stops proceed at once, `ExecutionRun.deliberation_status = "held_degraded"` with the dropped count,
   and the fault is a **warning** naming the posture (an expected outcome must not read as an error —
   DL-125). Normal runs are byte-for-byte unchanged. **Law cycle owed** (see above).
5. **The operator is told once.** One Telegram notice per degraded run — informational, **no answer
   buttons** — naming the failing checks and *"no new buys tonight; sync, stops and the monitor run"*.
   Fault-safe like the hold notice; record `degraded_notified_at` so a second dispatcher tick sends
   nothing. Deadline times follow DL-216 (`operator_timezone`).
6. **The dashboard says it.** The fleet banner, while the latest check is `degraded`, reads *"Tonight's
   run will place no new buys unless the next fleet check passes"* (not *held*); the *next fire* chip
   reads *"— no new buys"*; the deliberation stage of a degraded run reads *skipped — degraded run*
   and does **not** count as unreached. *System status* (DL-212) follows the banner.

### Out of scope (do NOT build this sprint)

- **Making the operator or deliberators themselves degrade** (e.g. switching provider) — that is the
  `llm_provider` switch (DL-100), a separate decision.
- **A standalone broker poller outside runs.** Rejected in DL-214: it would duplicate execution's fill
  path and lineage writes.
- **A dispatcher law book.** DRIFT-068 stays open; append to it.
- **Any change to the injected packs** (`trading_graph_vocabulary.json`, `trading_credential_tests.json`,
  `trading_issuer_map.json`). If you find you need one, stop and report — it changes the deploy to a
  full `up`.
- **No ADR reversal.** Item 58 is a work-queue decision, not an ADR; the operator approved this change.

### The road not taken (LAW-06)

- **Let execution's existing binding path handle it (no execution change).** Rejected: it waits the
  full 900 s grace, which delays every exit in a mixed PMRun, and it writes an **error** fault every
  degraded night — a truthful alarm that trains the operator to ignore faults (DL-125).
- **Hard-code the four agent names in the dispatcher.** Rejected: ADR-0012; the next pack's LLM agents
  would need a code change.
- **Degrade on *any* failure and hold only on "critical" ones.** Rejected: fails open. The safe
  default stays *hold*; only a declared, enumerated set degrades.
- **Have PM approve no buys instead of execution dropping them.** Rejected: PM would need to read
  run posture (a new read label and a PM law cycle) and the veto's existing seam is execution
  (ADR-0022, S166, S185).

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Where the degradable set lives and its shape** — a new baked pack file vs a key inside an
   existing non-injected pack. It must not be an injected pack (deploy stays image-only).
2. **How the posture is named** — a `RUN_POSTURE_*` constant pair in `contracts/` (recommended:
   execution and orchestration both read it, and `contracts` is the shared vocabulary) vs string
   literals. If in `contracts/`, the law cycle covers it.
3. **Absent `run_posture`** — every `RunRequest` written before this sprint has none. It must read as
   `normal`. Decide whether new normal runs write `"normal"` or omit it, and pin it.
4. **What counts as a parseable degradable failure** — only `unrecoverable:`? also `transient:`? A
   transient failure of a degradable agent is still an LLM agent that cannot start; decide and pin it.

🪤 **Take the next free DL number, then re-check it at merge.** On 2026-09-24, S226's builder took
`DL-210` while `main` gave `DL-210` to something else in the same hours; the planner had to renumber it
`DL-215` at merge. `main` is at **DL-216** as this spec is written.

---

## Blast radius — measured 2026-09-24

| What | Detail |
| --- | --- |
| Files changed | `orchestration/fleet_readiness.py` **64**, `scheduled_dispatch.py` **147**, `scheduled_dispatch_gate.py` **71**, `scheduled_dispatch_human.py` **132**, `telegram_client.py` / `telegram_port.py`; `agents/execution/pm_execution.py` **101**, `deliberation_gate.py` **147**, `deliberation_posture.py` **46**, `deliberation_faults.py`; `surfaces/queries/fleet_check.py` **128**, `surfaces/dashboard/projections_verdict.py`, `projections_vitals.py`, `static/verdict.js`, the stage-view pack; a new pack file |
| Agents affected | execution only (plus orchestration and surfaces, which are not agents). No agent imports another |
| Contract change? | **Likely yes** (posture constants) → law cycle, already required by the new execution guarantee |
| Graph vocabulary change? | **No** — `RunRequest` and `ExecutionRun.deliberation_status` values are not property-enforced… 🪤 **but `ExecutionRun` *is* an enforced label.** If you add a **new property** to `ExecutionRun` (not just a new value of `deliberation_status`), the vocabulary pack moves and the deploy becomes a full `up`. Prefer new values of existing properties; if you must add one, say so in the handback |
| New env keys / tunables | none expected |
| Deploy implication | **image-only retag** (`s227`), unless the row above changes |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md`.
3. **Measure what acceptance and the dashboard say today** for a run with a buy-carrying PMRun and no
   `DeliberationRun` (in-memory cascade, no `.env` needed). Paste it into the Closeout. This fills the
   one ASSUMED row above.
4. **Plant the failing tests first** (A1–A3, B1, C1) and watch them fail. Paste the red output.
5. **Implement.**
6. **Law cycle** — execution clause, test-plan row, docstring citation, rollups, drift row for the
   dispatcher.
7. **Prove the guards can fail (DL-70)** — for A2 and C2 at least: break the implementation, watch
   the guard go red, restore.
8. **`make ci` green** — every step, **redirected to a file, never piped**.
9. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 an LLM-only failing check places a degraded run | fresh `FleetPreflight` failing with exactly the four drain strings above | dispatcher returns `placed`; `RunRequest.run_posture == "degraded"`; `degraded_by` equals the four strings; no active `RunHold` |
| A2 | 🪤 one non-degradable failure still holds | the four drain strings **plus** `unrecoverable:provider:fmp:unrecoverable:http_402` | `held`, a `RunHold` written, **no** `RunRequest` |
| A3 | 🪤 unparseable, master-level, stale and missing checks still hold | separately: `not-structured`; `transient:master:vault:TimeoutError`; a degradable-only failure older than `preflight_max_age_minutes`; no check at all | each `held` (the stale and missing ones as `unknown`), no `RunRequest` |
| A4 | a passing check is unchanged | passing `FleetPreflight` | `placed`, posture `normal` (or absent, per decision 3) — byte-identical to today's `RunRequest` otherwise |
| A5 | the degradable set comes from the pack | a test pack that omits `operator` | an `operator`-only failure **holds** |
| B1 | 🎯 execution drops buys at once on a degraded run | degraded `RunRequest`; PMRun approving 1 buy + 1 sell; **no** `DeliberationRun`; PMRun `created_at` = now | sell submitted on the **first** poll (no grace wait); buy not submitted; `ExecutionRun.deliberation_status == "held_degraded"`, dropped count 1; one **warning** fault |
| B2 | 🪤 a normal run is unchanged | same PMRun, `RunRequest` with no posture | behaviour identical to today: `waiting` inside grace, then `proceeded_unvetoed` + buys dropped under binding + **error** fault |
| B3 | 🪤 protective stops on a degraded run | degraded run with a filled position lacking a stop | the stop is placed exactly as on a normal run |
| C1 | 🎯 one informational Telegram notice per degraded run | two dispatcher ticks on the same degraded day | exactly one notice, no buttons, `degraded_notified_at` recorded; a Telegram failure does not stop placement |
| D1 | the banner and status say *no new buys* | failing degradable-only check | banner headline and *System status* line use the degraded wording; next-fire chip *— no new buys* |
| D2 | the deliberation stage of a degraded run is *skipped*, not unreached | degraded run's chain without `DeliberationRun` | the stage view reads skipped; the pipeline card does not say *needs attention* for it |

---

## Success factors

- [ ] A1–A5, B1–B3, C1, D1–D2 pass; each cited clause ID is in its docstring.
- [ ] Normal runs unchanged (A4, B2) — shown, not asserted.
- [ ] The ASSUMED acceptance row is measured and pasted (Step 3), and a degraded run does not read as a failed or stalled run on any surface.
- [ ] Design decisions 1–4 recorded with rejected alternatives, at a DL number free on `main` at merge.
- [ ] Execution law cycle done (clause, version, Changelog, test-plan row, both rollups); DRIFT-068 appended.
- [ ] No injected pack changed; deploy stays image-only — or the handback says why not.
- [ ] Guards planted, watched to fail, restored — at least A2 and B1.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **"Every failure belongs to a degradable agent" must be checked on every failure, not on any.**
`any()` where `all()` is meant turns a broker outage plus an LLM outage into a degraded run that
trades blind. A2 exists for this — make it red first.
🪤 **A stale degradable-only check is not degraded.** The dispatcher's `preflight_max_age_minutes`
(70) still applies at fire time; `unknown` holds. Do not reuse the display horizon from DL-213 (1440).
🪤 **Execution must read the posture from the `RunRequest`, not infer it from a missing
`DeliberationRun`.** A missing veto on a normal night is exactly what S166/S185 exist to wait for.
🪤 **Do not add a property to `ExecutionRun`** unless you accept a full `up` — see Blast radius.
🪤 **`sched-*` run ids are day-keyed and merge-deduped.** A degraded placement and a later human
`run_now` on the same day must not create two runs — check how `place_override` and a degraded
placement interact, and pin it.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `deliberation_gate.py` **147**, `scheduled_dispatch.py` **147**,
  `scheduled_dispatch_human.py` **132**, `surfaces/queries/fleet_check.py` **128**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- Version bump MINOR, `uv.lock` staged with it.
- Secrets never through the worktree — a worktree has **no `.env`**. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0** from the worktree whose `HEAD`
   is the commit — check the printed SHA against `git rev-parse HEAD`.
2. The planner merges (merging `main` in first if it moved) and gates the merge commit.
3. **Post-merge CodeQL** on `main`.
4. **Deploy** as an image-only retag `s227` — unless the handback reports an injected-pack or
   `ExecutionRun` property change, in which case a full `up`.
5. **Live proof:** the next night the fleet check fails only on LLM agents (or a controlled test with
   the KEDA window widened — pre-prod test runs are allowed) — a degraded run is placed, stops are
   placed, no buy is submitted, one Telegram notice arrives.

---

## Handover — paste this to Codex

```text
Sprint 227 — an LLM-only outage holds the buys, not the run.
Spec: docs/sprints/sprint-227-an-llm-outage-holds-the-buys-not-the-run.md (read it whole).
Branch: sprint-227-an-llm-outage-holds-the-buys-not-the-run, in its own worktree, cut from main.
Never commit to main. Do not merge or deploy.

MUST RULE: read agents/execution/laws/laws.md + test-plan.md, the fleet-check section of
agents/master/laws/laws.md, docs/laws/conventions.md and docs/laws/drift-register.md (DRIFT-068)
BEFORE any code, and fill the Law reading record first.

Law cycle: YES for execution (new guarantee: on a degraded RunRequest no buy is submitted and
exits never wait). New clause + version + Changelog + test-plan row + clause IDs in docstrings +
rollups in docs/laws/ledger.md AND docs/laws/INDEX.md. The dispatcher has no law book: append to
DRIFT-068, do not create one.

Order: record design decisions 1-4 in docs/design-log.md (take the next free DL number; main is
at DL-216 now; re-check at handback) -> Step 3 measure what acceptance/dashboard say today for a
buy PMRun with no DeliberationRun and paste it -> plant A1-A3, B1, C1 red and paste the red run ->
implement -> law cycle -> break/restore A2 and B1 -> make ci redirected to a file -> fill every
handback section, Status: BUILT.

DO NOT: hard-code agent names in orchestration (pack-declare them, ADR-0012); degrade on any()
failure instead of all(); degrade on a stale or missing check; infer the posture from a missing
DeliberationRun; delay or drop any sell or protective stop; change any injected pack; add a new
property to ExecutionRun (it is vocabulary-enforced -> full up) without saying so; pipe make ci.

If a measured number differs from the spec, stop and report.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`, and lead this sprint's `README.md` row with `BUILT` in the same commit.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| Dispatcher fleet posture and run placement | `agents/master/laws/laws.md` fleet-check section; `docs/laws/drift-register.md` DRIFT-068 | `MST-OUT-04`, `MST-FAIL-05`; DRIFT-068 says dispatcher placement has no law home | Yes. Master law still treats unrecoverable/unexpected/transient failures as failed fleet checks; degradation must be a dispatcher placement posture only, fresh-check bounded, and only when every failure parses to a pack-declared degradable agent. DRIFT-068 must be appended rather than creating dispatcher laws here. |
| Execution degraded-run behaviour | `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md` | `EXEC-TRG-07`, `EXEC-NEV-01`, `EXEC-NEV-06`, `EXEC-OUT-09`, `EXEC-OBS-03`, `EXEC-OBS-04` | Yes. Execution must read the posture from the existing `RunRequest`, keep sells and protective stops immediate, avoid any new `ExecutionRun` property, and add/prove a new execution clause for degraded runs rather than relying on missing `DeliberationRun` inference. |
| Law amendment and proof rules | `docs/laws/conventions.md`; `agents/execution/laws/test-plan.md`; `docs/laws/INDEX.md` | Conventions §2, §3, §4, §7, §7a; execution ledger row in `docs/laws/INDEX.md` | Yes. The new guarantee needs an append-only clause ID, version/changelog movement, a faithful test-plan row, clause IDs in functional-test docstrings, and rollup updates in both law index surfaces. |
| Dispatcher law silence | `docs/laws/drift-register.md` DRIFT-068 | DRIFT-068 | Yes. The missing dispatcher law book is tracked drift; this sprint only appends the new degraded-posture guarantee to DRIFT-068. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?**

Yes. This sprint adds a new execution guarantee: on a degraded `RunRequest`, execution submits no buys and exits/protective stops do not wait. It may also add shared run-posture constants in `contracts/`; that stays inside the same execution law cycle.

**Contradictions found between a law and this spec:**

None found. The master law continues to say all fleet-check failures fail the check; the spec changes dispatcher run placement for a narrow, declared degraded posture rather than redefining master readiness.

**Laws found silent where a decision was needed:**

Dispatcher placement has no law book for the new guarantee that degraded posture is allowed only when every failing check belongs to a pack-declared degradable agent. DRIFT-068 is the required home for that silence this sprint.

**Clauses that were ⬜ and are now proven:**

`EXEC-NEV-07` is now declared and proven green.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_llm_only_failing_check_places_degraded_run_and_releases_hold` | `orchestration/tests/test_scheduled_dispatch_degraded_readiness.py` | PASS | `MST-OUT-04`, `MST-FAIL-05`, `DRIFT-068` |
| A2 | `test_non_degradable_failure_keeps_llm_outage_held` | `orchestration/tests/test_scheduled_dispatch_degraded_readiness.py` | PASS | `MST-FAIL-05`, `DRIFT-068` |
| A3 | `test_unparseable_master_stale_and_missing_checks_still_hold` | `orchestration/tests/test_scheduled_dispatch_degraded_readiness.py` | PASS | `MST-OUT-04`, `MST-FAIL-05`, `DRIFT-068` |
| A4 | `test_passing_check_places_normal_run_without_posture_property` | `orchestration/tests/test_scheduled_dispatch_degraded_readiness.py` | PASS | `DRIFT-068` |
| A5 | `test_degradable_set_comes_from_the_pack_declaration` | `orchestration/tests/test_scheduled_dispatch_degraded_readiness.py` | PASS | `DRIFT-068` |
| B1 | `test_degraded_run_drops_buys_without_waiting_and_submits_sell` | `agents/execution/tests/test_deliberation_posture_degraded.py` | PASS | `EXEC-OUT-09`, `EXEC-NEV-07`, `EXEC-OBS-04` |
| B2 | `test_normal_run_still_waits_then_blocks_buy_after_grace` | `agents/execution/tests/test_deliberation_posture_degraded.py` | PASS | `EXEC-NEV-06`, `EXEC-OBS-04` |
| B3 | `test_degraded_run_still_places_protective_stops` | `agents/execution/tests/test_deliberation_posture_degraded.py` | PASS | `EXEC-NEV-07`, `EXEC-OBS-03` |
| C1 | `test_degraded_run_sends_one_informational_notice_and_no_hold`; `test_degraded_notice_has_no_callback_buttons` | `orchestration/tests/test_scheduled_dispatch_degraded_notices.py` | PASS | `DRIFT-068` |
| D1 | `test_degraded_preflight_says_no_new_buys_without_holding`; `test_status_names_degraded_fleet_check_as_no_new_buys` | `surfaces/tests/test_dashboard_degraded_readiness.py`; `surfaces/tests/test_status_fleet_check.py` | PASS | `DRIFT-068` |
| D2 | `test_degraded_run_deliberation_stage_is_skipped_not_unreached` | `surfaces/tests/test_dashboard_projections.py` | PASS | `DRIFT-068` |

**Tests added beyond the plan:**

Support coverage beyond the plan: `test_malformed_posture_pack_degrades_nothing`; `test_degraded_notice_missing_message_id_does_not_mark_notified`; `test_degraded_notice_records_missing_message_id`; and the existing dispatcher-image copy guard now covers the new posture-pack module/resource.

---

## Closeout — evidence

**Status:**

BUILT.

**Tree the proofs ran in (and `.env` present?):**

Worktree `C:\Users\yury_\Downloads\project\trading-agents-sprint-227-llm-outage-holds-buys`, branch `sprint-227-an-llm-outage-holds-the-buys-not-the-run`, starting SHA `687954494f1327ef66e44a89eeb164d02e95b7b7`; `.env present: no`.

**Step 3 measurement (acceptance and dashboard with no `DeliberationRun`, before the change):**

```text
cascade=position_sync:1, provider:1, scanner:1, analyst:1, forecaster:1, portfolio_manager:1, execution:1, monitor:1, reporter:1
pm_approved=[('AAPL', 'buy'), ('MSFT', 'buy')]
deliberation_runs=0
execution_status=proceeded_unvetoed
execution_submitted=0
execution_blocked=2
acceptance_verdict=FAIL
acceptance_passed=False
ACCEPTANCE  FAIL
  FAIL  deliberation.*stage*: NOT REACHED
dashboard_deliberation_stage={'name': 'deliberation', 'trigger': 'PMRun(pm)', 'reached': False, 'observed': {}, 'outputs': [], 'checks': []}
dashboard_light=RED
dashboard_summary=Run stopped before deliberation � 8/9 stages completed.
dashboard_faults=[{'code': 'acceptance', 'message': 'Acceptance failed'}, {'code': 'stalled', 'message': 'Run stalled before deliberation'}]
dashboard_warning_count=0
```

**Result:**

Implemented the degraded posture end to end. A fresh fleet check with only pack-declared LLM/operator failures now places a degraded `RunRequest` with `run_posture="degraded"` and `degraded_by`, releases active holds, sends one informational Telegram notice with no answer buttons, and renders dashboard/status wording as "no new buys" instead of "held". Stale, missing, unparseable, master-level, and non-degradable failures still hold.

Execution reads degraded posture only from the linked `RunRequest`, never from a missing `DeliberationRun`; on degraded runs it holds buys immediately, submits sells, places protective stops, records `deliberation_status="held_degraded"`, and emits a warning fault. Normal runs omit `run_posture`, and no new `ExecutionRun` property or injected pack was added.

**Files changed:**

Code: `contracts/run_posture.py`; `orchestration/Dockerfile`; `orchestration/fleet_readiness.py`; `orchestration/scheduled_dispatch*.py`; `orchestration/telegram_*.py`; `orchestration/packs/trading_run_postures.*`; `orchestration/packs/trading_deliberation_view.py`; `orchestration/packs/trading_observatory.py`; `agents/execution/deliberation_*.py`; `agents/execution/pm_execution.py`; `surfaces/queries/fleet_check.py`; `surfaces/dashboard/projections_vitals.py`; `surfaces/dashboard/static/verdict.js`.

Tests/docs: dispatcher readiness/notice tests, execution deliberation-posture tests, dashboard/status tests, execution laws/test-plan, law rollups, DRIFT-068, DL-217, sprint README/state/spec handback, version `0.111.00` and `uv.lock`.

**Design decisions:**

Recorded as `DL-217` after re-checking that the next free design-log number was still 217. Decisions 1-4 are pinned there: baked orchestration posture pack; shared `contracts/run_posture.py` constants; normal runs omit `run_posture` and absent reads normal; degradable parsing requires every fresh failure to parse as `<kind>:<agent>:<check>:<reason>` for a pack-declared agent, with `unrecoverable`, `unexpected`, and `transient` accepted.

**Proof — the red run first:**

Captured before the later module-size split; the same planned assertions now live in the final files named in the test-plan table.

```text
uv run pytest --no-cov orchestration/tests/test_scheduled_dispatch_readiness.py::test_llm_only_failing_check_places_degraded_run_and_releases_hold orchestration/tests/test_scheduled_dispatch_readiness.py::test_non_degradable_failure_keeps_llm_outage_held orchestration/tests/test_scheduled_dispatch_readiness.py::test_unparseable_master_stale_and_missing_checks_still_hold agents/execution/tests/test_deliberation_posture.py::test_degraded_run_drops_buys_without_waiting_and_submits_sell orchestration/tests/test_scheduled_dispatch_notices.py::test_degraded_run_sends_one_informational_notice_and_no_hold

collected 5 items
orchestration\tests\test_scheduled_dispatch_readiness.py F..             [ 60%]
agents\execution\tests\test_deliberation_posture.py F                    [ 80%]
orchestration\tests\test_scheduled_dispatch_notices.py F                 [100%]

FAILED orchestration/tests/test_scheduled_dispatch_readiness.py::test_llm_only_failing_check_places_degraded_run_and_releases_hold
E   AssertionError: assert 'held' == 'placed'
FAILED agents/execution/tests/test_deliberation_posture.py::test_degraded_run_drops_buys_without_waiting_and_submits_sell
E   AssertionError: assert [] == ['pm-run-fixture']
FAILED orchestration/tests/test_scheduled_dispatch_notices.py::test_degraded_run_sends_one_informational_notice_and_no_hold
E   AssertionError: assert ('held', 'held') == ('placed', 'placed')
3 failed, 2 passed in 19.38s
```

**Proof — the green run:**

```text
uv run pytest --no-cov orchestration/tests/test_scheduled_dispatch_readiness.py orchestration/tests/test_scheduled_dispatch_degraded_readiness.py agents/execution/tests/test_deliberation_posture.py agents/execution/tests/test_deliberation_posture_degraded.py orchestration/tests/test_scheduled_dispatch_notices.py orchestration/tests/test_scheduled_dispatch_degraded_notices.py surfaces/tests/test_dashboard_projections.py::test_degraded_run_deliberation_stage_is_skipped_not_unreached surfaces/tests/test_dashboard_degraded_readiness.py::test_degraded_preflight_says_no_new_buys_without_holding surfaces/tests/test_status_fleet_check.py::test_status_names_a_failing_fleet_check_above_the_health_line surfaces/tests/test_status_fleet_check.py::test_status_names_degraded_fleet_check_as_no_new_buys tests/test_dispatch_scheduled_run.py::test_dispatcher_image_copies_everything_its_entrypoint_imports orchestration/tests/test_scheduled_dispatch_human_edges.py::test_fault_safe_records_port_reported_error

collected 42 items
orchestration\tests\test_scheduled_dispatch_readiness.py .........       [ 21%]
orchestration\tests\test_scheduled_dispatch_degraded_readiness.py ...... [ 35%]
agents\execution\tests\test_deliberation_posture.py .......              [ 52%]
agents\execution\tests\test_deliberation_posture_degraded.py ...         [ 59%]
orchestration\tests\test_scheduled_dispatch_notices.py .......           [ 76%]
orchestration\tests\test_scheduled_dispatch_degraded_notices.py ....     [ 85%]
surfaces\tests\test_dashboard_projections.py .                           [ 88%]
surfaces\tests\test_dashboard_degraded_readiness.py .                    [ 90%]
surfaces\tests\test_status_fleet_check.py ..                             [ 95%]
tests\test_dispatch_scheduled_run.py .                                   [ 97%]
orchestration\tests\test_scheduled_dispatch_human_edges.py .             [100%]

42 passed in 3.25s
```

**Guards planted:**

A2 guard break/restore:

```text
Mutation: changed _all_failures_degradable from all(...) to any(...).

uv run pytest --no-cov orchestration/tests/test_scheduled_dispatch_degraded_readiness.py::test_non_degradable_failure_keeps_llm_outage_held

FAILED orchestration/tests/test_scheduled_dispatch_degraded_readiness.py::test_non_degradable_failure_keeps_llm_outage_held
E   AssertionError: assert 'placed' == 'held'
1 failed in 1.58s

Restored all(...):
1 passed in 1.29s
```

B1 guard break/restore:

```text
Mutation: disabled the execution degraded-posture branch.

uv run pytest --no-cov agents/execution/tests/test_deliberation_posture_degraded.py::test_degraded_run_drops_buys_without_waiting_and_submits_sell

FAILED agents/execution/tests/test_deliberation_posture_degraded.py::test_degraded_run_drops_buys_without_waiting_and_submits_sell
E   AssertionError: assert [] == ['pm-run-fixture']
1 failed in 1.68s

Restored degraded-posture branch:
1 passed in 1.31s
```

**Module line counts:**

```text
contracts/run_posture.py 25
orchestration/packs/trading_run_postures.py 28
orchestration/fleet_readiness.py 95
orchestration/scheduled_dispatch_gate.py 77
orchestration/scheduled_dispatch.py 179
orchestration/telegram_port.py 41
orchestration/telegram_client.py 120
orchestration/scheduled_dispatch_human.py 164
agents/execution/deliberation_gate.py 162
agents/execution/deliberation_posture.py 48
agents/execution/deliberation_faults.py 124
agents/execution/pm_execution.py 109
orchestration/packs/trading_deliberation_view.py 162
orchestration/packs/trading_observatory.py 41
surfaces/queries/fleet_check.py 140
surfaces/dashboard/projections_vitals.py 136
agents/execution/tests/test_deliberation_posture.py 199
agents/execution/tests/test_deliberation_posture_degraded.py 135
orchestration/tests/test_scheduled_dispatch_readiness.py 190
orchestration/tests/test_scheduled_dispatch_degraded_readiness.py 171
orchestration/tests/test_scheduled_dispatch_notices.py 163
orchestration/tests/test_scheduled_dispatch_degraded_notices.py 106
surfaces/tests/test_dashboard_readiness.py 191
surfaces/tests/test_dashboard_degraded_readiness.py 68
surfaces/tests/test_dashboard_projections.py 198
surfaces/tests/test_status_fleet_check.py 153
```

**`make ci`:**

```text
make ci > C:\Users\yury_\Downloads\project\sprint-227-make-ci.txt 2>&1
exit code: 0

TOTAL                                                           17900      0   3898      0  100.00%
Coverage HTML written to dir htmlcov
Required test coverage of 100.0% reached. Total coverage: 100.00%
================= 3154 passed, 6 skipped in 144.07s (0:02:24) =================
uv run python scripts/check_dependency_audit.py
accepted: PYSEC-2026-2447 (diskcache 5.6.3) - reachable only via the 'optimizer' extra, installed by 0 of 15 Dockerfiles; no fix release exists, nothing imports dspy, and the attack needs write access to the cache directory - which is code execution already [DL-184] - retire when diskcache publishes a fixed release, or the optimizer extra is dropped
No unaccepted vulnerabilities; 1 accepted advisory re-checked
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 7 new file(s)
```

**`make gate-ran`:**

```text
not run: branch is BUILT only, not pushed/gated; merge/deploy are explicitly forbidden for this handback.
```

**Not met / verified failing:**

Remote gate, `make gate-ran`, merge, deploy, and live proof are not done. This handback is BUILT only.

---

## Return notes

- BUILT on the isolated sprint worktree, not merged or deployed.
- Version bumped to `0.111.00`; `uv.lock` updated.
- Execution law cycle completed as `v1.8`: added/proved `EXEC-NEV-07`, amended `EXEC-OUT-09`, updated Changelog, test-plan row, `docs/laws/ledger.md`, and `docs/laws/INDEX.md`.
- Dispatcher guarantee remains in DRIFT-068; no dispatcher law book was created.
- No injected pack changed and no new `ExecutionRun` property was added, so deploy implication remains image-only retag after normal remote gates.
