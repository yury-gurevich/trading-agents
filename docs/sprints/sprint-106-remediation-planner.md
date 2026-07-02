# Sprint 106 — LLM remediation planner, bounded catalogue (DL-36 Piece C)

**Phase:** Credential-validated activation (DL-36)
**Branch:** `sprint-106-remediation-planner`
**Status:** planned
**Effort:** L

---

## Goal

When a credential test fails, S104 writes an `Escalation` and refuses activation. **Piece C** adds
the *diagnosis + plan*: the master asks the deliberation LLM to **select a remediation from a bounded
catalogue** (never free-form) and justify it, records the plan on the `Escalation`, and marks whether
it is **auto-eligible**. C **plans + records + gates**; it does **not** execute — execution is **Piece D**.

**Operator decisions (2026-07-01):**
- **Auto-boundary is a configurable parameter.** `MasterSettings.auto_remediation_scope` ∈
  `{safe_only, all}` (default `safe_only`). Combined with each remediation's `destructive` tag it
  decides auto-eligibility: `auto_eligible = (mode == automatic) and (scope == "all" or not destructive)`.
  So the operator can dial between "only safe/idempotent remediations may auto-run" and "any catalogue
  remediation may auto-run (one shot)". **Document it.**
- **C first, D next.**

## Scope

### In

**Substrate (master, pack-agnostic):**

- `agents/master/remediation.py`:
  - `Remediation` (frozen): `name`, `description`, `destructive: bool`. (Executors/tests/rollbacks are
    **D** — C's catalogue is metadata only, so it can be pack **data**, not code.)
  - `RemediationPlan` (frozen): `remediation` (name), `rationale`, `auto_eligible: bool`, `status`.
  - `select_remediation(failure, catalogue, llm) -> str`: build a bounded prompt (the failure + the
    catalogue names/descriptions), call `llm.complete` with a tool schema whose `remediation` field is an
    **enum of catalogue names**, parse the choice. **Validate the choice ∈ catalogue**; on an invalid /
    unparseable choice **fall back to the safe null** (`pause-and-escalate`). The LLM can never invent an
    action — the guardrail is the enum + the membership check.
  - `plan_remediation(escalation, catalogue, llm, *, scope, mode) -> RemediationPlan`: select, compute
    `auto_eligible` from `scope`/`mode`/`destructive`, return the plan. Fail-open: an LLM error yields a
    `pause-and-escalate` plan (never blocks the escalation).
- `MasterSettings.auto_remediation_scope` = `tunable("safe_only", ...)` documenting the two dials.
- `store.write_remediation_plan(graph, escalation_key, plan)` → a `RemediationPlan` node linked
  `Escalation -[:PLANNED_BY]-> RemediationPlan`; master `owns_graph += RemediationPlan`.

**Wiring:** `MasterAgent` gains optional `remediation_llm` + `remediation_catalogue` (opt-in, like the
cascade veto). In `activate`, after `write_escalation`, **if both are present**, run `plan_remediation`
inside a fault boundary and `write_remediation_plan`, then still raise `ActivationRefused`. Default (no
LLM injected) = S104 behaviour unchanged.

**Pack (trading, injected — ADR-0012):** `orchestration/packs/trading_remediations.json` — the catalogue:
`refetch-from-key-vault` (safe), `resume-instance` (safe), `rotate-credential` (destructive),
`recreate-instance` (destructive), `pause-and-escalate` (safe null). Loader `load_remediations`.

### Out

- **Execution (Piece D):** the executors/tests/rollbacks + test→execute→production→documentation pipeline
  + the one-automatic-shot firing. C only records the plan and its `auto_eligible` flag; nothing runs.
- The rich human approve/deny **command** UI (a read-only "open escalations + plans" surface is enough).

## Deliverables

- `remediation.py` (planner) + `write_remediation_plan` + `auto_remediation_scope` setting +
  `owns_graph += RemediationPlan` + opt-in wiring in `activate`.
- `orchestration/packs/trading_remediations.json` + `load_remediations`.
- Unit tests (FakeLLMClient): valid selection recorded; an invalid/unknown choice falls back to
  `pause-and-escalate`; `auto_eligible` truth table over `scope × mode × destructive`; LLM-error →
  fail-open safe plan.
- `make ci` green, 100% coverage, modules ≤ 200 lines.

## Functionality check (sprint-close rule)

Against real Aura + a **FakeLLMClient** (live LLM is cost-gated — DEP-LLM): trigger a credential failure
→ `Escalation` written → planner selects a catalogue remediation → **`RemediationPlan` durably written**
and linked to the `Escalation`, with the correct `auto_eligible` under `safe_only`. Then flip
`auto_remediation_scope=all` and confirm a destructive remediation becomes auto-eligible. **Tear down**
(DETACH DELETE) → Aura to prior count. Record in `docs/laws/functionality-checks.md`. *(Optional, gated:
one real-LLM selection to sanity-check the prompt — only if the operator approves the spend.)*

## Dependencies

- **S104** (`Escalation` + refuse), DL-36. Reuses `kernel/deliberation.py`/`kernel/llm.py` (LLM) and the
  challenger-veto asymmetry precedent (LLM proposes within rails; deterministic code/humans decide).

## Version bump

New capability (LLM remediation planner). **0.46.00 → 0.47.00** (feat → MINOR).

## Notes

C makes the failure *diagnosable and plannable* within rails; **D** makes it *actionable* (execute →
production → document, one automatic shot). The `auto_remediation_scope` parameter is the operator's dial
between conservative (safe-only auto) and aggressive (all auto) self-healing.
