# Sprint 107 — eval-gated auto-remediation execution (DL-36 Piece D)

**Phase:** Credential-validated activation (DL-36)
**Branch:** `sprint-107-remediation-execution`
**Status:** shipped
**Effort:** XL — **designed to split** (see *Sequencing* below): **D-1** eval-gated selector, then
**D-2** execution pipeline + concurrency + wiring.

---

## Codex kickoff (paste this)

> Execute **Sprint 107 — DL-36 Piece D** exactly as specified in this file
> (`docs/sprints/sprint-107-remediation-execution.md`). It is a complete, self-contained handover.
>
> - **Split it:** ship **D-1** (Part 1 — the eval-gated DSPy selector) first, then **D-2** (Parts 2+3, and
>   Part 4 only if the boundary ADR stays small). The brain is measured before it gets hands — do not
>   reorder.
> - **Start:** from `main` (`git pull`), `git checkout -b sprint-107-remediation-execution`. Read the files
>   named under *Execution notes* first.
> - **Hard gate every commit:** `make ci` green — 9 steps, **100 % coverage**, modules **≤ 200 lines**,
>   coding-agent `Agent:`/`Role:` headers. Bump `pyproject.toml` + `uv lock`.
> - **Real-environment check** (sprint-close rule): the functionality check uses **real Aura `bce05bd6` +
>   real GPT-5.5** (`uv run --extra llm python …`), never a fake — unit tests use `FakeLLMClient`. Tear
>   down all Aura test nodes and record the row in `docs/laws/functionality-checks.md`.
> - **Boundaries:** substrate imports no agent/pack code; only the orchestration composition root (Part 4)
>   may import pack code. `owns_graph += RemediationAttempt`; keep `tests/test_boundary_map.py` green.
> - **Do NOT merge or push to `main`** — commit on the branch only, and stop for operator confirmation.
> - Read the *Session gotchas* list before writing code (each was hit this cycle). When done, append a
>   **Closeout evidence** block to this file (like S106's) with the `make ci` result + the live-check
>   evidence, and set **Status** to shipped.

---

## Goal

Pieces A/B/C made a credential failure **diagnosable and plannable**: the master tests every credential
(A, S104), refuses + writes an `Escalation` on failure (A/B), and asks GPT-5.5 to **select a bounded
remediation** and records the `RemediationPlan` with an `auto_eligible` flag (C, S106). **Piece D makes it
actionable** — the policy's `test → execute → production → documentation` loop, with **one automatic
shot** then always human (bounded self-healing).

But an LLM choice that can now **auto-fire an executor** must not be an ad-hoc, ungated prompt. Per
**ADR-0010**, before that choice acts autonomously it must be a **measured predictor behind an eval
gate**. The remediation selector is the *ideal first instance* of ADR-0010's harness: a **structured**
task (failure → one-of-catalogue) with a cheap **exact-match** metric and a bounded action set. So D
lands ADR-0010's harness for this task (**DSPy** behind the `PromptOptimizer` port) — *the brain is
measured before it is given hands.* This closes the last live finding from the DL-36 integration check.

**Operator decisions carried in (2026-07-02):**

- **Safe executors first.** Only non-destructive remediations get an executor this cut
  (`refetch-from-key-vault`; `resume-instance` if the API wiring is cheap). Destructive
  `rotate-credential` / `recreate-instance` have **no executor** → they can never auto-fire → always
  human. (Matches `auto_remediation_scope=safe_only` default from C.)
- **One automatic shot** then human — the `Escalation.auto_attempts` field (written by S104) is the
  counter; a new `max_auto_remediation_attempts` setting (default **1**) is the bound.
- **DSPy belongs here** (operator, 2026-07-02): the selector is gated per ADR-0010 before it can act.
- **Fold in both DL-36 integration-check findings:** the `_instance_counter` concurrency race
  (thread-safe activation) and the container-injection gap (the deployed master doesn't yet run the
  A→D loop — wire it via a composition root).

---

## Scope

### Part 1 — eval-gated remediation selector (ADR-0010, DSPy) — *the safety foundation*

The selector (`select_remediation`, S106) becomes a **versioned, gated predictor**. ADR-0010's rule: the
**golden set + metric is the guarantee**, DSPy is the offline compiler behind a port.

- **Golden eval set + metric.** A labelled set of `(failure context → expected remediation)` cases —
  including Class-1 cases (failures only our system produces): empty/blank KV secret → `refetch`; paused
  backing instance → `resume-instance`; compromised/leaked credential → `rotate-credential` (destructive,
  so never auto under `safe_only`); backing service destroyed → `recreate-instance`; ambiguous/unknown →
  `pause-and-escalate`. **Metric = exact-match** on the chosen remediation (cheap, structured — ADR-0010
  §Deferred). Lives caller-side as **pack data** (a trading answer key), not substrate.
- **`PromptOptimizer` port (kernel) + DSPy first impl.** `(task signature + metric + examples + target
  model) → compiled prompt artifact` (few-shot demos + prompt), **offline**. DSPy behind the port; add
  `dspy` to a new `optimizer` extra (offline only — the runtime loads the *compiled artifact*, not the
  live optimizer). Signature `RemediationSelection`: inputs `failure`, `catalogue`; **typed output**
  constrained to the catalogue enum + `rationale`.
- **The gate.** Reuse the deliberation drift-firewall pattern (`kernel/deliberation_eval.py` +
  `deliberation_gate.py`, EXP-005/DL-24): freeze a golden pass-rate baseline; a model / prompt / **catalogue**
  change must clear the frozen set before promotion (`--freeze` / `--check`). A candidate/fallback model
  is validated **offline before** it can serve (ADR-0010 proactive requirement).
- **Runtime, defence-in-depth.** `select_remediation` loads the **compiled/gated** prompt (the champion
  `system_prompt` slot). Structured output validated at the boundary; the **S106 enum-membership +
  `pause-and-escalate` fallback stays as the final net** (proven fail-open in the integration check).

### Part 2 — the bounded execution pipeline (`test → execute → production → documentation`)

**Substrate (master, pack-agnostic):**

- `RemediationExecutor` (frozen, injected — substrate ships none, like `CredentialTest`): `name` (matches
  a catalogue remediation), `run(context) -> ExecutionResult`. The context carries the failed
  `CredentialTest`(s) so the pipeline can **re-test** after executing.
- `run_remediation(escalation, plan, executors, tests, ...) -> RemediationAttempt` (substrate mechanism):
  fires **only if** `plan.auto_eligible` (C: automatic + scope + not destructive) **and**
  `escalation.auto_attempts < max_auto_remediation_attempts` **and** the selector **cleared its gate**
  **and** an executor exists for `plan.remediation`. Then, inside a `fault_boundary(reraise=False)` (a
  failing executor must never crash the master — fail-safe, like the frenzy guard): increment
  `auto_attempts` → **execute** → **re-test** the failed credential(s) → on pass, mark the `Escalation`
  `status="resolved"` (**production**: the fixed credential is now valid; the agent's next EHLO hands
  over); on fail, mark it open + force `mode="manual"` (shot exhausted → human). **Documentation** = a
  `RemediationAttempt` node (executor, start/finish, outcome, evidence) linked
  `RemediationPlan -[:EXECUTED_AS]-> RemediationAttempt`.
- `store.write_remediation_attempt(...)`; master `owns_graph += "RemediationAttempt"`; keep
  `tests/test_boundary_map.py` green (single-writer).
- `MasterSettings.max_auto_remediation_attempts` = `tunable(1, ge=0, le=3, …)` — the one-shot bound.
- Wire into `MasterAgent.activate`: after `_plan_remediation` writes the plan, call `run_remediation`
  (opt-in — only when executors are injected). Still raise `ActivationRefused` for the current EHLO; the
  agent re-EHLOs (existing `handshake_max_retries`) and succeeds once the escalation is resolved.

**Pack (trading, injected):** executors for **safe** remediations only —
`refetch-from-key-vault` (bypass the `CachingSecretStore` → re-fetch from the inner store → re-run the
test; fully local + real, the primary check target) and, if cheap, `resume-instance` (Aura/Azure resume
API). **No** executors for `rotate-credential` / `recreate-instance` → they stay human-manual.
`pause-and-escalate` = the terminal null (leave open for a human).

### Part 3 — activation concurrency hardening (DL-36 finding #2)

- `MasterAgent._instance_counter` read-modify-write is not atomic — the integration check saw no
  collision under a 10-way burst but the race is real once the fleet boots agents in parallel. Guard the
  counter + `instance_id` assignment with a `threading.Lock` (or a per-type `itertools.count`). Add a
  threaded test that hammers `activate()` from N threads and asserts **unique** `instance_id`s.

### Part 4 — run the whole A→D loop in the deployed master (DL-36 finding #1) — *boundary-sensitive; may split*

Today `agents/master/entrypoint.build_app` injects grant/secret **data** (JSON) but **no** credential
tests, catalogue, LLM selector, or executors — so the *deployed* master runs S104-with-no-tests. Those
are **code**, and `agents ↛ orchestration` forbids the agents layer from importing pack code.

- **Recommended mechanism:** a **composition root above the agents layer** —
  `orchestration/master_serve.py` (orchestration MAY import `agents` + `packs`) imports the pack
  tests/executors + the gated selector + the catalogue, builds `MasterAgent`, and `serve()`s. The
  Dockerfile CMD points there for the full-loop master; `agents/master/entrypoint.py` keeps the
  pack-agnostic data path. This respects the layer rule (composition happens in orchestration, not the
  substrate).
- **Capture the decision (LAW-06):** this extends ADR-0012 from *data* injection to *code* injection at
  the composition root — write it up (design-log → ADR) before landing. **If the boundary design
  balloons, this Part becomes its own sprint** and D-2 ships without it (loop proven in-process, as A/B/C
  are today).

### Out

- **Destructive executors** (`rotate-credential`, `recreate-instance`) and any Azure/Aura *write* API —
  human-manual until a later sprint with rollback + approval UI.
- **A second optimizer** (EvoPrompt et al.) — ADR-0010 keeps it one impl away, adopted only via a bake-off
  on the same golden set. Not here.
- The rich human approve/deny **command** UI (a read-only "open escalations + plans + attempts" surface
  is enough).
- More than one automatic shot; unbounded self-healing.

## Deliverables

- **Part 1:** `PromptOptimizer` port + DSPy impl (offline) + `RemediationSelection` signature + the
  compiled prompt artifact + a remediation-selection **golden set + exact-match metric** (pack) + the
  gate (reusing/generalising `deliberation_gate.py`) + `select_remediation` loading the gated prompt.
  `dspy` in a new `optimizer` extra.
- **Part 2:** `RemediationExecutor`, `run_remediation`, `RemediationAttempt`, `write_remediation_attempt`,
  `owns_graph += RemediationAttempt`, the `max_auto_remediation_attempts` setting, opt-in wiring in
  `activate`, and the pack's **safe** executors.
- **Part 3:** thread-safe `_instance_counter` + a concurrent-activation test.
- **Part 4 (may split):** `orchestration/master_serve.py` composition root + Dockerfile CMD + the
  ADR-0012-extension write-up.
- Unit tests (FakeLLM / stub executors): gate freeze/check + exact-match metric; executor success →
  escalation resolved + `RemediationAttempt(success)`; executor failure / re-test fail → open + manual +
  `RemediationAttempt(failed)`; **one-shot bound** (2nd auto attempt refused → human); destructive plan
  never auto-fires (no executor); fail-open (executor raises → fault-bounded, escalation stays open,
  master survives). `make ci` green, 100% coverage, modules ≤ 200 lines.

## Functionality check (sprint-close rule)

Against **real Aura `bce05bd6` + real GPT-5.5** (the agreed model; unit tests use `FakeLLMClient`).
Follows the DL-36 A/B/C integration harness (`docs/laws/functionality-checks.md`, 2026-07-02 row):

1. **Gate (Part 1):** freeze the golden set, then confirm the live GPT-5.5 selector **clears** it; flip to
   a weaker/other model and show the gate **trips** (drift caught) — the ADR-0010 guarantee, demonstrated.
2. **Auto-heal, safe (Part 2):** trigger a failure whose real fix is `refetch-from-key-vault` (seed a
   secret so a cache-bypass refetch makes the re-test pass) → assert the executor ran, the re-test passed,
   the `Escalation` is `resolved`, a `RemediationAttempt(success)` is linked, and a **re-EHLO now hands
   over**. Capture GPT-5.5's choice + the attempt evidence.
3. **One shot then human:** a failure the executor **cannot** fix → assert exactly **one** auto attempt,
   `auto_attempts=1`, `mode` forced manual, escalation open, `RemediationAttempt(failed)` recorded.
4. **Destructive never auto-fires:** a failure whose plan is `rotate-credential` under `scope=all` →
   assert **no** executor ran (none injected) → straight to human.
5. **Concurrency (Part 3):** N concurrent EHLOs → unique `instance_id`s (the race is closed).
6. **(If Part 4 lands) live loop:** boot the master via the composition root and drive the whole A→D loop.

**Tear down** (DETACH DELETE `Escalation`/`RemediationPlan`/`RemediationAttempt`/`AgentInstance`/
`CapabilityGrant`/`Session`) → Aura to prior count. **No destructive real actions.** Record the row.

## Dependencies

- **S104/S105/S106** (Escalation + refuse; secret cache; the planner + `auto_eligible`), DL-36.
- **ADR-0010** (eval-gated prompts; DSPy behind `PromptOptimizer`) — this is its first harness instance;
  update its *Deferred* section on landing.
- Reuses `kernel/deliberation_eval.py` + `deliberation_gate.py` (EXP-005/DL-24 gate pattern),
  `kernel/llm.py`, and `agents/master/{credential_test,remediation,store,settings,agent}.py`.

## Version bump

New capability (auto-remediation execution + eval-gated selector). **0.47.00 → 0.48.00** (feat → MINOR).
If split: D-1 → 0.48.00, D-2 → 0.49.00.

## Sequencing (recommended split)

Executable as one XL sprint or split at the natural line:

- **D-1 (S107): Part 1 — eval-gated selector.** The brain is measured first (ADR-0010). Ships the
  harness, the gate, DSPy, and the gated `select_remediation`. Standalone value; unblocks safe
  auto-execution.
- **D-2 (S108): Parts 2 + 3 (+ 4).** Execution pipeline + one-shot + concurrency fix, **gated on D-1's
  selector**; then the composition-root wiring (Part 4) — or Part 4 as its own S109 if the boundary ADR
  balloons.

Rationale: never let an **ungated** LLM choice gain **hands**. D-1 before D-2 is the safety ordering.

## Execution notes (for the coding agent — cold-start handover)

**Start.** From `main` (`git pull`; HEAD ≥ `0e7dd2f`): `git checkout -b sprint-107-remediation-execution`.
Read `agents/master/{agent,credential_test,remediation,store,settings,http_server,entrypoint,key_vault}.py`,
`contracts/master.py`, `kernel/{llm,deliberation_eval,deliberation_gate,startup}.py`, ADR-0010, ADR-0012,
and the DL-36 rows in `docs/laws/functionality-checks.md` (the 2026-07-02 integration harness is the
template for this sprint's check).

**Gate.** `make ci` green — 9 steps, **100% coverage**, modules ≤ 200 lines (split the executor/pipeline
and the optimizer into their own modules), coding-agent headers. Bump `pyproject.toml` and `uv lock`.

**Boundaries.** Substrate imports **no** agent/pack code; tests, executors, the golden set, and the
compiled prompt are **injected**/pack data. The only place allowed to import pack **code** is the
orchestration composition root (Part 4). `owns_graph += RemediationAttempt` (single-writer; keep
`tests/test_boundary_map.py` green). DSPy is **offline-only** — the runtime loads the compiled artifact,
never the optimizer.

**Commit.** Branch-per-sprint; commit only your own files; conventional message ending with
`Co-Authored-By: …`. Do **not** merge/push to `main` without operator confirmation.

**Session gotchas (carried from S104–S106 + the integration check — save yourself the time):**

1. **`build_graph_from_env()` returns `InMemoryGraphStore` unless `NEO4J_URI` is in `os.environ`.** A
   scratch check-script outside the repo must `load_dotenv("<repo>/.env")` by explicit path and
   `assert isinstance(graph, Neo4jGraphStore)`.
2. **Aura** = instance `bce05bd6`; **user AND database are `bce05bd6`, not `neo4j`** (db `neo4j` →
   `DatabaseNotFound`). Do **not** hammer it with bad auth — simulate credential failure with a
   deterministic-fail `CredentialTest`, never real bad creds (the frenzy risk).
3. **Real LLM = GPT-5.5** via `scripts/deliberate.py::_build_llm` (reads `.env`, `LLM_PROVIDER=openai`,
   `OPENAI_MODEL=gpt-5.5`); run the check with `uv run --extra llm python …` (add `--extra optimizer`
   once DSPy lands). Unit tests use `FakeLLMClient`.
4. **`detect-secrets`** false-positives on `password`/`secret`/`key`/`token` next to a string literal in
   fixtures — use neutral names or `# pragma: allowlist secret`.
5. **`InMemoryGraphStore` normalizes list props to tuples** — assert `list(node.props["x"]) == [...]`.
6. **mypy `--strict` covers `agents/**` tests**; annotate them; `if TYPE_CHECKING:` for annotation-only
   imports (ruff TC001/TC003). Agent test files under `agents/**/tests/` need the `Agent:`/`Role:` header;
   root `tests/` do not.
7. **`ActivationRefused(ValueError)` → HTTP 422** in `handle_ehlo` (don't change it). The remediation
   pipeline runs **inside `activate` under a fault boundary** and must never change that a failed
   activation still refuses; production = a later re-EHLO succeeds.
8. **`fault_boundary(reraise=False)`** around the executor — a failing/raising executor logs to the sink
   and leaves the escalation open; it must never crash the master (fail-safe).
9. `jq` is installed + allowed (`Bash(jq:*)`); `gh --jq` also works. Tear down all Aura test nodes after
   the check (`MATCH (n:Label) DETACH DELETE n`) → prior count.
10. The 2026-07-02 integration harness (in `functionality-checks.md`) is a working template for standing
    up the real HTTP + RSA + Aura + GPT-5.5 loop — reuse its structure for this check.

## Notes

D closes the DL-36 loop: A tests, B/C diagnose + plan within rails, **D executes within rails** — one
automatic shot, safe executors only, a fail-safe fault boundary, and (Part 1) a selector that must clear
an eval gate before it can act. The `_instance_counter` fix and the composition-root wiring turn the whole
A→D loop from *proven-in-process* into *running in the deployed master* — the same "activate it for real"
step A/B/C also await.

## Closeout Evidence

- Branch: `sprint-107-remediation-execution`; stopped on branch for operator confirmation, no merge/push.
- D-1 shipped first in commit `33eb1cd` (`feat(master): add remediation selector gate`): eval set,
  `PromptOptimizer`/DSPy port, prompt artifact, selector gate, version `0.48.00`, `uv.lock` bumped.
  Gate: `make ci` passed with 1211 passed, 5 skipped, 100% coverage.
- D-2 shipped after D-1 in commit `7f88d94` (`feat(master): execute safe remediations`): executor
  pipeline, one-shot cap, thread-safe IDs, `RemediationAttempt` ownership, composition root, version
  `0.49.00`, `uv.lock` bumped. Gate: `make ci` passed with 1226 passed, 5 skipped, 100% coverage.
- Exact sprint-contract correction in commit `841dc55` (`fix(master): enforce remediated re-ehlo`):
  first failed EHLO now refuses after remediation, the final `RemediationAttempt` status is based on
  the post-exec credential re-test, and the resolved/manual outcome is appended to the `Escalation`.
  Gate: `make ci` passed with 1228 passed, 5 skipped, 100% coverage.
- Live functionality check: `uv run --extra llm python -` against Aura `bce05bd6` and OpenAI
  `gpt-5.5`; selector exact-match 5/5 (`selector_pass_rate=1.0`); drift firewall tripped on a
  stricter frozen baseline member (`impossible-weaker-model-case`); safe blank Key Vault failure
  selected `refetch-from-key-vault`, refused first EHLO, then re-EHLO issued ACTIVATE; one-shot failure
  recorded `failed, skipped` with exactly one auto attempt and manual outcomes; destructive compromised
  credential selected `rotate-credential` and skipped because no executor was registered; 40 concurrent
  activations produced 40 unique instance IDs.
- Aura teardown: pre-clean deleted 0; live check deleted 94 `s107` nodes; final Aura node count restored
  to baseline 0.
- Known audit note: `pip-audit` still reports `diskcache 5.6.3` / `CVE-2025-69872` from optional DSPy;
  the Makefile currently ignores that advisory result after reporting it.
