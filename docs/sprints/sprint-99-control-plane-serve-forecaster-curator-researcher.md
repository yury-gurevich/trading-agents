# Sprint 99 — Control-plane served in-process (2/2): forecaster + curator + researcher

**Phase:** Fleet Activation (DL-30 / DL-35)
**Branch:** `sprint-99-control-plane-serve-forecaster-curator-researcher`
**Status:** shipped (handover refreshed 2026-07-03 for the 0.50.00 codebase; supersedes the pre-S104 draft)
**Effort:** M

---

## Codex kickoff (paste this)

> Execute **Sprint 99 — serve forecaster/curator/researcher** exactly as specified in this file
> (`docs/sprints/sprint-99-control-plane-serve-forecaster-curator-researcher.md`). It is a complete,
> self-contained handover.
>
> - **Start:** from `main` (`git pull`),
>   `git checkout -b sprint-99-control-plane-serve-forecaster-curator-researcher`. Read the files named
>   under *Execution notes* first — S98's supervisor/operator entrypoints + tests are the exact pattern
>   to replicate.
> - **Hard gate every commit:** `make ci` green — 9 steps, **100 % coverage**, modules **≤ 200 lines**,
>   coding-agent `Agent:`/`Role:` headers. Bump `pyproject.toml` 0.50.00 → 0.51.00 + `uv lock`.
> - **Law constraint (do not cross):** all three agents are **request-triggered, never self-triggering**.
>   The forecaster must NOT get a graph-pull `work_loop` (`FORE-TRG-02`); the researcher proposes, never
>   applies; the curator never gates a live decision. Serving tests cite clause IDs in their docstrings.
> - **Real-environment check** (sprint-close rule): serve each agent against **real Aura `bce05bd6`**
>   via `serve_once`, assert the durable artifact from a **separate** connection, tear down to prior
>   count, record the row in `docs/laws/functionality-checks.md`.
> - **Do NOT merge or push to `main`** — commit on the branch only, and stop for operator confirmation.
> - Read the *Session gotchas* before coding. When done, append a **Closeout evidence** block (like
>   S107/S108's) with the `make ci` result + live-check evidence, and set **Status** to shipped.

---

## Goal

Retire the last three `idle_loop()` stubs — **forecaster**, **curator**, **researcher** — by serving each
over the S97 `serve_loop`, exactly as S98 did for supervisor/operator. After this sprint **zero
`idle_loop()` remains**: every agent runs a real loop (trade-spine on `work_loop`, control-plane on
`serve_loop`), so the whole fleet is *serviceable in-process* — the etalon-first-safe milestone. S100 then
swaps the in-process consumer for the Service Bus backend behind the same `RequestConsumer` Protocol.

## Decisions (resolved at planning — do not reopen in-sprint)

- **Forecaster trigger source: unchanged in S99.** In-process, the *orchestrator* remains the only caller
  (`cascade_once`'s forecaster stage, DL-30) — S99 adds the container-facing serve surface
  (`LocalRequestConsumer` inbox), not a new trigger. *Who publishes* `forecast` requests in the
  distributed fleet (orchestrator stage vs. analyst event) is **S100's decision**, to be captured in the
  design log when the Service Bus receiver lands. Recommendation on record: the orchestrator publishes
  per recommendation, so the forecaster never reads the analyst node itself (`FORE-TRG-02`).
- **Curator/researcher cadence: out-of-band, request-triggered only** (operator command or orchestrator).
  No pollers, no schedules in this sprint — consistent with "never influences a live decision".

## Scope

### In

- **Three entrypoints, one proven pattern.** Replace `idle_loop()` in
  `agents/{forecaster,curator,researcher}/entrypoint.py` with the S98 shape (copy
  `agents/supervisor/entrypoint.py`): a covered `build_served_bus(graph) -> MessageBus` that constructs
  the agent with defaults and `.bind()`s it, and a `# pragma: no cover` `main()` that does
  EHLO → verify signed ACTIVATE → `serve_loop(LocalRequestConsumer(), bus)`.
  - Forecaster binds its existing handlers (`forecast`, `forecast_return`, `scorecard`,
    `sentiment_scorecard`, `return_scorecard`). Construct as the cascade does —
    `ForecasterAgent(bus, graph=graph)` (fake models by default; real-model injection is out of scope).
  - Curator binds `build_dataset`, `describe_corpus`, `train_predictor`, `promote_predictor` —
    `CuratorAgent(bus, graph=graph)`.
  - Researcher binds `propose`, `evidence` — `ResearcherAgent(bus, graph=graph)`.
- **Clause-cited serving tests** (mirror `agents/supervisor/tests/test_supervisor_entrypoint.py`): for
  each agent, submit a request to a `LocalRequestConsumer`, `serve_once`, assert the handler answered —
  docstrings citing the relevant `TRG` clause and the NEVER clause the test proves is not crossed
  (forecaster: prediction is `shadow=True` and the PM/execution path is untouched; researcher: proposal
  recorded, nothing applied; curator: no gate touched).
- **Law reconciliation:** touched `TRG` rows in the three `agents/<name>/laws/laws.md` reconciled (only
  if serving changes the trigger contract — expected: no change, serving implements it), `test-plan.md`
  cites the new tests, ledger green-count deltas recorded.
- **Retire the primitive:** delete `idle_loop` from `kernel/bootstrap.py` (zero callers remain) and add a
  guard test asserting no agent entrypoint references `idle_loop`. If anything unexpected still needs it,
  keep the function and the guard test only — but prefer removal (it was the S75 placeholder).

### Out

- The **Service Bus backend** (S100) — `LocalRequestConsumer` is the only consumer here.
- Any change to forecaster/curator/researcher **domain logic**, models, or law semantics — this sprint
  changes *how they are triggered*, not *what they do*.
- Real FinBERT/LightGBM model wiring in the forecaster container (a later, separate concern).

## Deliverables

- Three served entrypoints + `build_served_bus` each; `idle_loop` removed from `kernel/bootstrap.py`;
  guard test.
- Clause-cited in-process serving tests for all three agents.
- Law `test-plan.md` citations + ledger deltas.
- `make ci` green, 100 % coverage, modules ≤ 200 lines. Version 0.50.00 → 0.51.00 + `uv lock`.

## Functionality check (sprint-close rule)

Against **real Aura `bce05bd6`** (`Neo4jGraphStore`, asserted — gotcha #1). No LLM needed (none of these
three serve paths calls one). Mirror the S98 check, once per agent:

1. **Forecaster (flagship):** build the served bus on the real graph, submit a `forecast` request via a
   `LocalRequestConsumer`, `serve_once` → assert accepted; from a **separate raw connection** confirm a
   durable `ShadowPrediction` with `shadow=True`; assert **no** order/PM artifact was created (the
   side-branch invariant, `FORE-NEV` + `FORE-TRG-02`).
2. **Researcher:** serve a `propose` request over a seeded evidence window → durable proposal artifact
   confirmed from a separate connection; nothing applied (no parameter/settings node mutated).
3. **Curator:** serve `describe_corpus` (read-only) → correct summary answer; or `build_dataset` if
   seeding is cheap — then its artifact is confirmed + torn down like the others.

**Tear down** (DETACH DELETE the test nodes) → Aura back to prior count. Record the row in
`docs/laws/functionality-checks.md`.

## Dependencies

- **S97** (`serve_loop`/`serve_once`/`LocalRequestConsumer`), **S98** (the exact entrypoint + test
  pattern, shipped 0.44.00). Respects DL-30 and the forecaster/curator/researcher LOCKED v1 laws (S71).

## Version bump

New capability (final three control-plane agents serve; in-process fleet functionally complete).
**0.50.00 → 0.51.00** (feat → MINOR, HARD RULE).

## Execution notes (for the coding agent — cold-start handover)

**Start.** From `main` (`git pull`; HEAD ≥ `fabab23`):
`git checkout -b sprint-99-control-plane-serve-forecaster-curator-researcher`. Read
`kernel/serve_loop.py`, `agents/supervisor/entrypoint.py` + `agents/supervisor/tests/
test_supervisor_entrypoint.py` and the operator twins (the S98 pattern), the three target entrypoints,
`agents/{forecaster,curator,researcher}/agent.py` (handlers + constructor defaults),
`contracts/{forecaster,curator,researcher}.py` (capability names), and `agents/<name>/laws/laws.md` for
the three (TRG/NEVER clauses to cite).

**Gate.** `make ci` green — 9 steps, **100 % coverage**, modules ≤ 200 lines, coding-agent headers.

**Boundaries.** Agents never import other agents; entrypoints import only their own agent + kernel.
No new graph labels (`owns_graph` unchanged — `tests/test_boundary_map.py` must stay green untouched).

**Commit.** Branch-per-sprint; commit only your own files; conventional message ending with
`Co-Authored-By: …`. Do **not** merge/push to `main` without operator confirmation.

**Session gotchas (carried from S97–S108):**

1. **`build_graph_from_env()` returns `InMemoryGraphStore` unless `NEO4J_URI` is in `os.environ`.** The
   live check must `load_dotenv("<repo>/.env")` by explicit path and
   `assert isinstance(graph, Neo4jGraphStore)` before trusting a "real" result.
2. **Aura** = instance `bce05bd6`; **user AND database are `bce05bd6`, not `neo4j`**. Never hammer it
   with bad auth (the frenzy risk); reads are cheap, teardown by label of the nodes you created.
3. **`FORE-TRG-02`:** the forecaster is RPC-triggered — a graph-pull `work_loop` on it is a law
   violation, not a design option. Serving tests must cite the clause.
4. **Capability names must match the contract exactly** — `bus.request` dispatch is by capability
   string; a typo surfaces as "no handler", not a type error.
5. **`main()` is `# pragma: no cover`; `build_served_bus` is not** — the covered seam is what the tests
   drive (see the supervisor test). Keep the split or the coverage floor breaks.
6. **mypy `--strict` covers `agents/**` tests**; annotate; `if TYPE_CHECKING:` for annotation-only
   imports (ruff TC001/TC003). Agent test files under `agents/**/tests/` need the `Agent:`/`Role:`
   header; root `tests/` do not.
7. **`InMemoryGraphStore` normalizes list props to tuples** — assert `list(node.props["x"]) == [...]`.
8. **`detect-secrets`** false-positives on `password`/`secret`/`key`/`token` near string literals in
   fixtures — neutral names or `# pragma: allowlist secret`.
9. **Pre-commit stashes unstaged changes and can race** when the shared tree is edited concurrently —
   commit with a clean unstaged tree.
10. `jq` is installed + allowed (`Bash(jq:*)`); `gh --jq` also works.

## Notes

At this sprint's exit the **in-process fleet is functionally complete** — every agent activates through
the credential-tested master (DL-36, now seeded from the vault) and runs a real loop. Everything after
(S100+) swaps transports and adds live infra; nothing after this changes what an agent *does*.

## Closeout evidence

- Branch: `sprint-99-control-plane-serve-forecaster-curator-researcher`; stopped on branch for operator
  confirmation, no merge/push.
- Version: `pyproject.toml` bumped to `0.51.00`; `uv.lock` refreshed.
- Gate: `make ci` passed on 2026-07-03 — ruff, format, mypy, import-linter, module-size,
  module-header, pytest, detect-secrets. Pytest result: **1254 passed, 5 skipped, 100.00% coverage**.
  Known non-blocking `pip-audit` warning: `diskcache 5.6.3` / `CVE-2025-69872` (Makefile ignored).
- Scope shipped: `agents/{forecaster,curator,researcher}/entrypoint.py` now expose
  `build_served_bus(graph)` and serve `LocalRequestConsumer()` after EHLO/ACTIVATE; `idle_loop` is
  removed from `kernel/bootstrap.py`; guard test confirms no agent entrypoint references the retired
  symbol.
- Law evidence: new serving tests cite `FORE-TRG-02`, `CUR-TRG-02`, `CUR-TRG-03`, and `RES-TRG-03`;
  ledger deltas recorded as forecaster **16/46**, curator **22/48**, researcher **19/44**.
- Live functionality check: `uv run --extra runtime python -` against Aura `bce05bd6`
  (`Neo4jGraphStore`, db/user `bce05bd6`, asserted) with durability reads from a separate raw Neo4j
  connection. Forecaster served `forecast` and wrote **1** durable `ShadowPrediction` with
  `shadow=true`; researcher served `propose` and wrote **1** durable `Experiment` plus **1**
  `ParamChange`; curator served `build_dataset` and wrote **1** durable `Dataset` plus **6**
  `TrainingExample` nodes.
- Boundary checks: forecaster did not change `OrderIntent`/`PMRun`/`CloseDecision`; researcher did not
  change parameter-setting labels; curator did not change gate labels during dataset build.
- Aura teardown: baseline node count **0**; live check deleted **35** stamped nodes (including the
  transient `Model` created by the check); final Aura node count restored to **0**.
