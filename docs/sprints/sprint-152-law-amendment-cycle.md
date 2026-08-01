<!-- Agent: planning | Role: sprint handover -->
# Sprint 152 — One amendment cycle for five drift rows: the law book catches up with its own decisions

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-152-law-amendment-cycle`
**Status:** SPEC — packaged 2026-07-31, **not yet handed to a coding agent**
**Version:** fix → next available **PATCH** (`0.84.04` if `0.84.02`/`0.84.03` have landed; confirm
against `main` before starting — two chores were in flight when this was written)
**Effort:** M
**Decisions:** [ADR-0015](../decisions/0015-exit-lifecycle-and-stop-ownership.md) §3 broker stops ·
[ADR-0018](../decisions/0018-decision-validity-same-session-or-dropped.md) bounded orders + drop
sweep · [ADR-0013](../decisions/0013-continuous-improvement-system.md) champion–challenger ·
[conventions §4](../laws/conventions.md) locking & amendment **(the rule this sprint must satisfy —
read it first)** · [LAW-02](../../ops/laws/LAW-02-successful-execution.md) success is proven

---

## Why this is one sprint and not five register rows

Six consecutive sprints each opened exactly one law-gap drift row and each deferred the amendment:

| ID | Agent | What the LOCKED law does not declare | Opened by |
| --- | --- | --- | --- |
| DRIFT-024 | execution | `BrokerStopOrder` state + the broker-stop fallback parameter | S146 |
| DRIFT-025 | execution | `BrokerPositionSnapshot` ownership + the run-start snapshot trigger | S147 |
| DRIFT-026 | execution | order-price tolerance tunable, dropped-decision output, drop evidence | S148 / S151 |
| DRIFT-027 | execution | selectable tolerance *mode*, scaled tunables, counterfactual evidence | S149 |
| DRIFT-028 | **analyst** | stop-scaling mode, scaled stop/target tunables, experiment evidence | S150 |
| DRIFT-029 | execution | terminal-status refresh boundary + the unresolved-PnL marker | S154 |

Five are execution; DRIFT-028 crossed into the analyst. **That crossing is the reason this is a
sprint.** While every row sat in one agent it read as one constitution lagging its code. Spanning
two agents, the same pattern in six straight sprints is evidence about **how laws are maintained**,
not about any single law. DRIFT-029 (S154, 2026-08-01) is the sixth and was opened *after* this sprint was packaged — the rate did not change while the sprint sat queued, which is the argument for it. A seventh row would record the symptom again and fix nothing.

## The trap that actually caused this — read before planning

[conventions §4](../laws/conventions.md) says:

> Amend a law only when functionality is genuinely *lacking* (discovered during reconciliation or
> testing) — **not to match whatever the code currently does.**

Every one of the six rows proposes, in its own words, "a later law amendment should declare
\<what the code already does\>". Read literally, §4 forbids exactly that, and each sprint doc hands
its coding agent the instruction **"LOCKED v1. Read-only. Never edit."**

So the deferral was not laziness. Each sprint hit a rule that made its own amendment look
illegitimate, took the only sanctioned action — append to the drift register — and moved on. That is
why the debt accrued at a fixed rate of one row per sprint.

**The resolution, and it must be stated in the sprint's own return notes so it stops being
re-litigated:** §4 exists to stop *code drift* being rubber-stamped into law — a behaviour that
appeared by accident, then got blessed after the fact. None of these six are that. Each is a
capability that was **deliberately decided in an ADR, then built** (ADR-0015 §3, ADR-0018,
ADR-0013), where only the constitutional declaration was skipped. The law is genuinely *lacking* a
declaration of a decided capability. That is inside §4, not around it.

**The distinction to apply per clause:** was this behaviour *decided* (ADR/DL, before the code) or
did it *appear* (code first, rationalised after)? Decided → amend. Appeared → it stays a drift row
and becomes a code fix, not a law edit. **Do not assume all six pass this test — apply it to each
clause and report any that fail.** An honest "this one is code drift, not a lacking declaration" is
a better outcome than six tidy amendments.

## 🔴 MUST RULE — this sprint inverts the usual one

Every other sprint says *never edit `laws.md`*. **This sprint is the authorised exception, and only
within this scope:**

| Path | Normally | In this sprint |
| --- | --- | --- |
| `agents/execution/laws/laws.md` | read-only | **may be amended** — bump `LOCKED v1` → `v1.1`, changelog line per change |
| `agents/analyst/laws/laws.md` | read-only | **may be amended** — same |
| `agents/*/laws/laws.md` (any other) | read-only | **still read-only.** Out of scope |
| `agents/*/laws/test-plan.md` | read-only | may gain clause rows for new clauses only |
| `docs/laws/drift-register.md` | append-only | rows 024–029 move to **CORRECTED** with the amendment cited |
| `docs/laws/ledger.md`, `docs/laws/INDEX.md` | — | clause **totals** change if clauses are added; counts must stay consistent across all three |

**ID stability is absolute ([conventions §2](../laws/conventions.md), "the most important rule").**
Never renumber, never reuse, never repurpose an existing clause ID. A new declaration is a **new
clause ID**; an existing clause whose wording is genuinely incomplete is amended *in place* with its
ID kept and the change recorded in the changelog.

## Scope

1. **Amend `agents/execution/laws/laws.md`** to declare, across `IDN` / `DEP` / `OUT` / `OBS` /
   `PARAM` / `CAP` as each belongs: `BrokerStopOrder` and `BrokerPositionSnapshot` as
   execution-owned durable labels; the run-start snapshot trigger; the broker-stop fallback stop
   percent; the order-price tolerance tunable and its selectable mode with scaled bounds; the
   dropped-decision outcome as distinct from rejected/skipped; and the durable drop evidence shape
   S151 settled (`Fill.drop_reason` / `Fill.dropped_at` plus an append-only `BrokerOrderStatus`
   drop fact, **with no raw terminal reason written into `Fill.broker_status`** — that collision was
   the outage).
   Also from S154: **when broker-status refresh terminates** (a `Fill` whose `broker_status` is
   `filled`/`rejected` is settled and must not be re-read or re-written) and the **unresolved-PnL
   marker** `Fill.pnl_unresolved_at` that makes an unresolvable realized-PnL conclusion durable
   rather than retried forever.
2. **Amend `agents/analyst/laws/laws.md`** for the stop-scaling mode, the scaled stop/target
   tunables, and durable applied-vs-counterfactual proposal evidence.
3. **Close DRIFT-024…029** as CORRECTED, each citing the amended clause IDs and the law version.
4. **Reconcile the three clause counters** — `ledger.md`, `laws/INDEX.md`, and each agent's
   `test-plan.md` — so they agree. They disagreed once already this month (S151's `EXEC-FAIL-03`).

## Non-goals — do not do these

- **Do not turn new clauses green.** A newly declared clause starts ⬜ like any other and needs a
  functional test citing its ID ([conventions §3/§7](../laws/conventions.md)). Declaring a clause and
  marking it proven in the same stroke is the S151 over-claim, one level up. **Expect the green
  totals to stay flat while the denominators rise** — that is the correct, honest outcome, and the
  return notes must say so explicitly rather than presenting a worse ratio as a regression.
- **Do not change any behaviour.** No production source edits. If an amendment seems to require a
  code change, that is the signal the clause is *code drift* — stop and report it.
- **Do not touch the other eleven agents' laws**, the `_TEMPLATE.md`, or the provider law (LOCKED v1,
  S69).
- **Do not re-open the ADRs.** ADR-0015 §3, ADR-0018 and ADR-0013 are settled; this sprint declares
  what they decided, it does not revisit it.

## Success factors (LAW-02 — the definition of done)

1. Both `laws.md` files carry a bumped version and a changelog line per change, stating *what
   changed and why*, naming the ADR that decided the capability.
2. Every one of DRIFT-024…029 is **CORRECTED** with its amending clause IDs cited — or is
   explicitly **kept OPEN with a written reason** (the "this one is code drift" outcome).
3. `ledger.md`, `laws/INDEX.md` and both `test-plan.md` files agree on clause counts, and the
   arithmetic is shown in the return notes.
4. No production source file changed. `git diff --stat` in the return notes proves it.
5. `make ci` green (9/9, 100.00% coverage) and the remote gates green on the pushed branch before
   any merge (DL-56 — pushing *is* the gate). Assert a run **exists** for the SHA before merging
   (hardening-backlog row M).
6. The §4 reasoning above is restated in the return notes as a **standing convention**, so the sixth
   occurrence is decided by precedent instead of deferred again.

## Risks

| Risk | Why it matters | Mitigation |
| --- | --- | --- |
| Amending to match code | The exact failure §4 forbids; would legitimise real drift as law | The decided-vs-appeared test, applied per clause and reported per clause |
| Renumbering clauses | Breaks every existing test citation and the ledger | ID stability is absolute; new declaration = new ID |
| Counter drift across three files | Already happened this month | Success factor 3 requires the arithmetic shown |
| Silent scope creep into other agents | Eleven other LOCKED laws are one `sed` away | The scope table above is exhaustive |

## Closeout — evidence

> **Fill this in at handback. Do not return the sprint with this block unedited.**

- Law versions before → after (both agents):
- Clause IDs added / amended, each with the ADR that decided it:
- Per-clause decided-vs-appeared verdict (and any row kept OPEN, with its reason):
- Clause counters before → after, in all three files, with the arithmetic:
- `git diff --stat` proving no production source changed:
- `make ci` result (pass count, coverage):
- Remote gate run IDs, and the assertion that runs exist for the merge SHA:
- The standing convention as written into the return notes:
