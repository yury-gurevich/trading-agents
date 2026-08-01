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

**Law versions before → after.** `execution` LOCKED **v1 → v1.1**; `analyst` LOCKED **v1 → v1.1**.
Each carries a changelog entry naming, per clause, *what* was declared and *which ADR/DL decided it*.

**Clause IDs added, with the decision that warrants each.** All are **new IDs** — nothing was
renumbered, reused or repurposed, and **no existing clause was amended in place.** That was a
deliberate choice: widening a green clause (adding labels to `EXEC-IDN-02`, say) would silently
extend what an already-passing test is claimed to prove. New IDs keep the existing greens honest.

| Clause | Declares | Decided by | Drift |
| --- | --- | --- | --- |
| `EXEC-IDN-03` | owns `BrokerStopOrder`, `BrokerPositionSnapshot`, `BrokerOrderStatus` | ADR-0015 §3, DL-44 | 024, 025 |
| `EXEC-TRG-07` | run-start `position_sync` writes one snapshot before scoring | DL-44 (+ DL-79 containment) | 025 |
| `EXEC-OUT-07` | `dropped` distinct from `rejected`/`skipped`; append-safe drop evidence | ADR-0018 (shape: S151/DL-79) | 026 |
| `EXEC-OUT-08` | applied + counterfactual tolerance evidence on submitted orders | ADR-0013 | 027 |
| `EXEC-STA-05` | broker-status refresh terminates; `partial` still refreshes | ADR-0014 implication, DL-44 | 029 |
| `EXEC-STA-06` | unresolvable realized PnL recorded once via `pnl_unresolved_at` | S154 spec + DL-81 | 029 |
| `EXEC-OBS-03` | stop lifecycle reconstructable; `UnprotectedPosition` retried | ADR-0015 §3 (S146) | 024 |
| `EXEC-DEP-04` | graph append-write for the 3 labels; broker cancel + stop placement | ADR-0015 §3, ADR-0018, DL-44 | 024/025/026 |
| `ANLZ-OUT-07` | selectable `flat`/`scaled` mode; target scaled in lockstep; ATR-absent degrade | ADR-0013 | 028 |
| `ANLZ-OUT-08` | applied vs counterfactual proposal evidence | ADR-0013 | 028 |
| `ANLZ-OBS-03` | proposal reconstructable without re-running the agent | ADR-0013 | 028 |

Plus the `CAP` block widened (execution) and `PARAM` rows added to both, **copied from the
`tunable()` declarations in `settings.py` rather than restated from memory**. Two of those rows are
marked **NO (mode selector)**: `order_price_tolerance_mode` and `stop_target_mode` select *which
formula runs*, not a value within one, so they are not tunables and must not be moved by experiment.

**Per-clause decided-vs-appeared verdict.** Five of six rows are unambiguously **decided** — an ADR
or DL settled the capability *before* the code existed, and only the declaration was skipped:
024 (ADR-0015 §3), 025 (DL-44), 026 (ADR-0018), 027 (ADR-0013), 028 (ADR-0013).

**DRIFT-029 is decided on a weaker warrant, and that is recorded rather than smoothed over.** Its
first half — a terminating refresh — is implied by ADR-0014's append-only model and was named as an
open defect in DL-44 itself (*"nothing ever refreshes broker order status after run end"*), so it is
properly decided. Its second half, the `pnl_unresolved_at` marker, has **no ADR**: it was decided in
the S154 sprint spec and DL-81, planning artifacts written before the code, which satisfies
*decided-before-built* but on thinner authority. Declared, with the distinction written into the
drift row so a later reader sees the weaker basis rather than a sixth tidy amendment.

**No row was kept OPEN.** All six move to CORRECTED. One item stays deliberately open *inside*
DRIFT-029: `broker_status="partial"` cannot upgrade to `filled` under the write-once property model,
so that case still refreshes indefinitely. Zero production fills are in it today, and the fix is a
current-status read model derived from `BrokerOrderStatus` facts — a design change, not a law edit.

**Clause counters before → after, with the arithmetic.** Counted by unique IDs in each `laws.md`,
not by trusting the previous number:

| File | execution | analyst |
| --- | --- | --- |
| `laws.md` unique IDs | 49 → **57** (+8) | 43 → **46** (+3) |
| `docs/laws/ledger.md` | `30 / 49` → **`30 / 57`** | `26 / 43` → **`26 / 46`** |
| `docs/laws/INDEX.md` | `30 / 49` → **`30 / 57`** | `26 / 43` → **`26 / 46`** |
| `test-plan.md` rows | 36 → **44** (+8) | 31 → **34** (+3) |

**Greens are unchanged at 30 and 26 — the ratios got worse, and that is the correct outcome.**
Declaring a clause is not proving one; every new clause starts ⬜ with `_tbd_` as its test.

**A pre-existing gap found while reconciling, not introduced here:** the test-plans still carry fewer
rows than their laws have clauses (execution 44 rows vs 57 clauses; analyst 34 vs 46). That predates
this sprint — the scope permits rows *for new clauses only* — but it means "all three files agree"
holds for the **counters**, not for row-per-clause completeness. Worth its own pass.

**`git diff --stat` — no production source changed:**

```text
 agents/analyst/laws/laws.md        |  36 ++++++++++++-
 agents/analyst/laws/test-plan.md   |   3 ++
 agents/execution/laws/laws.md      | 100 +++++++++++++++++++++++++++++++++++--
 agents/execution/laws/test-plan.md |   8 +++
 docs/laws/INDEX.md                 |   4 +-
 docs/laws/drift-register.md        |  12 ++---
 docs/laws/ledger.md                |   4 +-
 7 files changed, 153 insertions(+), 14 deletions(-)
```

Asserted by `git diff --name-only` filtered for source extensions returning nothing.

**`make ci`:** exit 0 — **2001 passed, 6 skipped, 100.00% coverage**; import-linter `4 kept, 0
broken`; pip-audit `No known vulnerabilities found`; detect-secrets tracked + untracked clean.

**No version bump.** `pyproject.toml` is untouched: this sprint ships no code, so neither a MINOR nor
a PATCH applies. The law files carry their own `v1 → v1.1`, which is the change that actually
happened.

**Remote gate run IDs, and the assertion that runs exist for the merge SHA:** recorded below in
*Return notes* after the push.

---

## The standing convention (success factor 6)

> **A law-gap drift row is closed by amendment when the capability was *decided* — in an ADR or a
> design-log entry written before the code — and the constitution merely failed to declare it.**
> [conventions §4](../laws/conventions.md) forbids amending a law *to match whatever the code
> currently does*; it does not forbid declaring a capability the project already decided to build.
> The test is **provenance, not chronology of the file**: did a decision precede the code?
>
> - **Decided → amend**, with a new clause ID, the deciding ADR/DL named in the changelog, and the
>   clause starting ⬜.
> - **Appeared → do not amend.** It stays a drift row and becomes a *code* fix. Blessing accidental
>   behaviour into law is exactly what §4 exists to prevent.
> - **Declaring is never proving.** A newly declared clause is ⬜ until a functional test cites its
>   ID. Expect denominators to rise while greens stay flat, and say so rather than presenting the
>   worse ratio as a regression.
> - **Prefer a new ID over widening a green clause.** Extending an existing clause silently extends
>   what an already-passing test is claimed to prove.
> - **State a weak warrant instead of hiding it.** DRIFT-029 was declared on a sprint spec plus a
>   design-log entry rather than an ADR; that is recorded in the row.
>
> Six consecutive sprints deferred under the opposite reading. This precedent is what stops a
> seventh.

---

## Return notes

**Remote gates, verified by SHA rather than by quoted run ID.** Branch tip `737f779`:

| Workflow | Job | Run ID | Conclusion |
| --- | --- | --- | --- |
| CI | `quality` | `30684671619` | success |
| CI | `test` | `30684671619` | success |
| CI | `security` | `30684671619` | success |
| Security Findings | `gate` | `30684671621` | success |

Both runs were confirmed to carry `headSha=737f779` — a run **exists** for the merge SHA, which is
the hardening-backlog assertion, not merely that some run was green.

**Executed by the planning agent, not handed to a coding agent.** S152 ships no production code and
its subject is the law book, which is planning-owned; the usual *"never edit `laws.md`"* instruction
exists to stop a coding agent doing this unsupervised, and inverting it for a coding agent would have
been the riskier arrangement.

**What I would flag for the next reader.** The `partial` case named inside DRIFT-029 is the one live
loose end: it is a *read-model* problem (derive current status from `BrokerOrderStatus` facts) that
no law edit can close, and it will re-surface the moment a partial fill occurs in production. Zero
fills are in that state today, which is the only reason it is not urgent.
- The standing convention as written into the return notes:
