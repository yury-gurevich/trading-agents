# Sprint 106 — LLM remediation planner, bounded catalogue (DL-36 Piece C)

**Phase:** Credential-validated activation (DL-36)
**Branch:** `sprint-106-remediation-planner`
**Status:** shipped (0.46.00 → 0.47.00)
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

- **Execution (Piece D):** the executors/tests/rollbacks, the test→execute→production→documentation
  pipeline, and the one-automatic-shot firing. C only records the plan and its `auto_eligible` flag.
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

Against **real Aura + the real GPT-5.5** — the agreed LLM-in-the-loop model (same one the deliberation /
challenger-veto use), built from `.env` the way `scripts/deliberate.py::_build_llm` does. **Not a fake:**
FakeLLMClient is for the unit tests (CI is offline); the live check must exercise the real model, because
the LLM's *selection* is the whole point of Piece C. Steps: trigger a credential failure → `Escalation`
written → **GPT-5.5 selects a catalogue remediation + justifies it** → assert the choice is a valid
catalogue member (the enum/membership guardrail held) and a **`RemediationPlan` is durably written** and
linked to the `Escalation`, with the correct `auto_eligible` under `safe_only`. Then set
`auto_remediation_scope=all` and confirm a destructive remediation becomes auto-eligible. Capture GPT-5.5's
chosen remediation + rationale as evidence. **Tear down** (DETACH DELETE) → Aura to prior count. Record in
`docs/laws/functionality-checks.md`.

**Closeout evidence (2026-07-02):** live check passed on Aura `bce05bd6` with real GPT-5.5. GPT selected
`refetch-from-key-vault` for the safe-only case (`auto_eligible=True`) and `rotate-credential` for the
destructive/all case (`auto_eligible=True`). Both plans were durably written and linked from
`Escalation`; teardown returned Aura from 0 nodes back to 0.

## Dependencies

- **S104** (`Escalation` + refuse), DL-36. Reuses `kernel/deliberation.py`/`kernel/llm.py` (LLM) and the
  challenger-veto asymmetry precedent (LLM proposes within rails; deterministic code/humans decide).

## Version bump

New capability (LLM remediation planner). **0.46.00 → 0.47.00** (feat → MINOR).

## Execution notes (for the coding agent — cold-start handover)

**Start.** From `main` (`git pull`; HEAD ≥ `598804a`): `git checkout -b sprint-106-remediation-planner`.
Read `agents/master/{agent.py,secret_map.py,credential_test.py,store.py,settings.py,key_vault.py,
http_server.py}`, `contracts/master.py`, `kernel/llm.py`, and `scripts/deliberate.py` to match patterns
(S104 built the `Escalation` + `ActivationRefused` path this extends).

**Gate.** `make ci` green — 9 steps, **100% coverage**, modules ≤ 200 lines, coding-agent headers.
Bump `pyproject.toml` 0.46.00 → 0.47.00 and run `uv lock`.

**Boundaries.** The master substrate imports **no** agent/probe code (agent independence); the catalogue
is **injected** as pack data (`orchestration/packs/trading_remediations.json`, loaded by path — ADR-0012).
`owns_graph += RemediationPlan` (single-writer; keep `tests/test_boundary_map.py` green).

**Commit.** Branch-per-sprint; commit only your own files; conventional message ending with
`Co-Authored-By: …`. Do **not** merge/push to `main` without operator confirmation.

**Session gotchas (all hit this cycle — save yourself the time):**

1. **detect-secrets** (pre-commit + `make ci`) false-positives on a `password`/`secret`/`key`/`token`
   keyword next to a string literal in test fixtures — use neutral names or `# pragma: allowlist secret`.
2. **`InMemoryGraphStore` normalizes list props to tuples** — assert `list(node.props["x"]) == [...]`.
3. **mypy `--strict` covers agent tests** (`agents/**`) — annotate them; move annotation-only imports into
   `if TYPE_CHECKING:` (ruff TC001/TC003).
4. **Agent test files under `agents/**/tests/` need the `Agent:`/`Role:` header**; root `tests/` do not.
5. **`build_graph_from_env()` returns `InMemoryGraphStore` unless `NEO4J_URI` is in `os.environ`.** A
   scratch check-script outside the repo tree must `load_dotenv("<repo>/.env")` by explicit path and
   `assert isinstance(graph, Neo4jGraphStore)` before trusting a "real" result.
6. **Aura** = instance `bce05bd6` (`.env` + `infra/aura-instance.local.json`); **user AND database are the
   instance id `bce05bd6`, not `neo4j`** (db `neo4j` → `DatabaseNotFound`).
7. **Real LLM = GPT-5.5** via `scripts/deliberate.py::_build_llm` (reads `.env`) — used in the live
   functionality check; unit tests use `FakeLLMClient`.
8. **`ActivationRefused(ValueError)` → HTTP 422** in `handle_ehlo` (already wired; don't change it).
9. **Pre-commit stashes unstaged changes and can race/roll back** when the other agent edits the shared
   tree concurrently — commit with a clean unstaged tree (stage all your files; leave nothing unstaged).
10. `jq` is installed + allowed (`Bash(jq:*)`); `gh --jq` also works. Tear down all Aura test nodes after
    the check (`MATCH (n) DETACH DELETE n` → prior count).

## Notes

C makes the failure *diagnosable and plannable* within rails; **D** makes it *actionable* (execute →
production → document, one automatic shot). The `auto_remediation_scope` parameter is the operator's dial
between conservative (safe-only auto) and aggressive (all auto) self-healing.
