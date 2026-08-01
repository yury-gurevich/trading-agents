<!-- Agent: planning | Role: sprint handover -->
# Sprint 153 — The deliberator agent: the LLM veto becomes a fleet participant

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-153-deliberator-agent`
**Status:** SPEC — packaged 2026-07-31, **refreshed 2026-08-01** against the live spine and the
S152/S154 merges; ready to hand to a coding agent
**Version:** feat → **0.85.00** (MINOR: two middle digits — a new agent is a new capability).
Base is **0.84.06** at time of writing; if `main` has moved, bump from wherever it actually is —
a MINOR zeroes the patch group either way
**Effort:** L
**Decisions:** [DL-80](../design-log.md) **(read this first — it is the whole reason)** ·
[sprint-109](sprint-109-heterogeneous-deliberation-models.md) the Defender/Challenger/Judge
structure and per-role models · [ADR-0012](../decisions/0012-platform-domain-separation.md)
substrate vs pack · [ops/agent-genesis.md](../../ops/agent-genesis.md) **the bundle method this
sprint must follow** · [DL-53](../design-log.md) the Azure SAS rule cap · [DL-57](../design-log.md)
a gate that cannot fail proves nothing · [LAW-02](../../ops/laws/LAW-02-successful-execution.md) ·
[LAW-06](../../ops/laws/LAW-06-capture.md)

---

## Why this sprint exists

**The LLM veto has never run in production. Not once.** Zero `DeliberationRun` nodes; all 25
`LLMCall` nodes are operator chat, newest 2026-07-15. `_drop_vetoed` is documented fail-open, so
**every order this system has ever sent to the broker went unvetoed** — the fail-open branch is the
only branch that has ever executed. Full evidence in [DL-80](../design-log.md).

The cause is not a bug. The debate itself is built and faithful to the design: bounded rounds, each
side seeing the running transcript, the Judge ruling afterwards with a verdict and rationale,
identical evidence assembled from the whole provider→scanner→analyst→PM lineage, and every turn
persisted. What went wrong is **embodiment**: the three roles were built as system prompts inside
`kernel/deliberation.py`, invoked from `orchestration/veto.py`. A kernel harness only runs where
something calls it, and the only caller is `orchestration/local_pipeline.py` — the *local* runner.
The fleet has never had a way to run it.

The operator's design — recorded only now, LAW-06 — was always three agent instances. **Three agent
instances would have been fleet-native by construction.** That is what this sprint builds.

## The design (operator-confirmed 2026-07-31)

The Manager activates two peers. All three receive **identical** evidence — external feeds plus the
quant research done inside the app. They deliberate over **rounds**, narrowing to the major points
of influence. The peers return recommendations; the **Manager adds its own VERDICT based on the
facts discussed** and hands off to the next stage. **The narrative is a first-class output** — the
point of exposure for what was actually argued, not a debug artifact.

Because the three roles are so similar, they ship as **one image with the role distributed**, and
**one instance activates the other two**.

> **Why a new agent and not the researcher.** "Three copies of the researcher" was the operator's
> phrasing, but the `researcher` that exists owns a different remit — *mine accumulated evidence
> for parameter and strategy improvements and propose bounded changes into the human-review queue,
> **never apply them*** — with `Experiment`/`ParamChange` and LOCKED v1 laws. Adversarial review of
> a live order is not that mission. Operator chose a **new `deliberator` agent reusing the
> one-image-many-roles pattern** (DL-80 option b), leaving the researcher intact and avoiding a
> sixth LOCKED-law amendment on top of the five already owed in [S152](sprint-152-law-amendment-cycle.md).

## Shape

| Instance | Role | Work source |
| --- | --- | --- |
| `deliberator-manager` | Judge / Manager | **graph-pull** — `PMRun` nodes with no `DeliberationRun` (`veto.find_pending` is already exactly this query) |
| `deliberator-proponent` | Defender | **served** — answers one debate turn per request |
| `deliberator-opponent` | Challenger | **served** — answers one debate turn per request |

One image, one Dockerfile, one bundle; the role arrives as a bounded setting. The Manager drives the
rounds by requesting a turn from each peer in order, then rules. Both patterns already exist in this
repo — graph-pull (the seven pipeline agents) and served request/reply (proven over Service Bus in
S102) — so **no new transport and no new orchestration concept is introduced.**

## Scope

1. **The acceptance gate learns to fail on an absent stage — do this FIRST.**
   `trading_acceptance.py`, `trading_boundaries.py` and `trading_observatory.py` reference neither
   deliberation nor the forecaster, which is why every run scored `ACCEPTANCE PASS` with both
   missing. Add a check that **fails when a declared stage produces no artifact**, and prove it
   fails by replaying a historical run — **all 23 lack a `DeliberationRun`** (re-verified against the
   live spine 2026-08-01: 23 `PMRun`, 23 `RunRequest`, **0** `DeliberationRun`). Without this, the
   new agent can rot exactly as the old one did, with the same green verdict. **It must be observed
   failing (DL-57/DL-70).**

   > **This check has a second consumer, added after packaging.** [DL-82](../design-log.md) made it
   > the **named precondition for revisiting DL-46 option A** (a deploy step in CI). Automating
   > deploy while a declared stage can produce nothing and still score `ACCEPTANCE PASS` would
   > automate the propagation of green-but-inert releases. So item 1 is not only this sprint's
   > guardrail — it is what unblocks a separate deferred decision. Build it accordingly.
2. **`contracts/deliberator.py`** — typed request/reply for one debate turn and one verdict.
   Substrate/pack discipline (ADR-0012): the *mechanism* is domain-free; the trading proposition is
   the payload.
3. **The bundle**, to [agent-genesis](../../ops/agent-genesis.md): `agents/deliberator/` with
   `mission.md`, `laws/laws.md` copied from **`docs/laws/_TEMPLATE.md`** (never from provider's),
   `laws/test-plan.md`, `settings.py` (role + `max_rounds` + per-role model as `tunable()`),
   `poll.py`, `store.py`, `agent.py`, `entrypoint.py`, `Dockerfile`, `tests/`. Every clause starts
   ⬜ and earns 🟩 only with a test citing its ID.

   > **Follow the S152 standing convention when writing the new law** (merged 2026-08-01, in
   > [sprint-152](sprint-152-law-amendment-cycle.md)): declare the capability this sprint *decides*,
   > name the deciding ADR/DL in the changelog, and leave every clause ⬜ — **declaring is never
   > proving**. A brand-new agent starts at `0 / N`, and that is the honest number. Also add a
   > `test-plan.md` **row for every clause**, not only for the ones you write tests for:
   > hardening-backlog row **O** exists because the older law books have clauses with no row at all,
   > which makes them invisible rather than unproven. Do not reproduce that in a new bundle.
4. **`kernel/deliberation.py` is demoted, not rewritten** — it becomes the shared reasoning core the
   three instances call. **No change to debate behaviour**: same rounds, same prompts byte-for-byte,
   same verdict parsing. `orchestration/veto_context.py` keeps building the evidence packet.
   `orchestration/veto.py` stops being the runner; `local_pipeline.py` keeps working.
5. **Fleet wiring** — this is the long tail and it is where the sprint will actually be spent:
   three app names in `$AGENTS` (`infra/deploy-agents.ps1`) sharing one image suffix; grants in
   `trading_grants.json`; **`ANTHROPIC_API_KEY` in `trading_secrets.json`** (the deliberator is the
   first *pipeline* agent needing an LLM key — check the master's min-privilege delivery); three
   `ta_deliberator_*` Postgres roles (S131); three scoped Service Bus SAS identities (S133);
   KEDA scale windows; import-linter (agents are islands — the deliberator must not import
   `orchestration` or another agent).
6. **Vocabulary** — `DeliberationRun` is a declared label and `PMRun -DELIBERATED_BY->
   DeliberationRun` was declared in 0.84.04, but `DeliberationRun` has **no declared property
   list**, and the S144 guard is now **live on the fleet**. Declare its properties (including the
   transcript/narrative shape) and prove the superset with `scripts/vocabulary_properties.py`,
   or the first real write fails closed.
7. **Ledger + INDEX rows** for the new agent in `docs/laws/ledger.md` and `docs/laws/INDEX.md`.

## Non-goals — do not do these

- **Do not change what the debate decides.** Rounds, prompts, verdict parsing and the fail-open
  contract in `_drop_vetoed` all stay. This sprint changes *where the roles live*, nothing else.
- **Do not touch the `researcher` agent**, its mission, or its LOCKED laws.
- **Do not fix the forecaster or the curator.** They are inert for the same structural reason
  (DL-80) and deserve their own decision — one at a time.
- **Do not remove the fail-open behaviour.** An absent or failed review must still never block
  trading. Making the veto mandatory is a separate, operator-gated decision.
- **Do not turn new clauses green** without a test citing the clause ID.

## Success factors (LAW-02 — the definition of done)

1. `make ci` green (9/9, 100.00% coverage); remote gates green on the pushed branch **before** any
   merge (DL-56), with a run asserted to exist for the SHA (hardening-backlog row M).
2. The acceptance check is **observed failing** on a historical run that has no `DeliberationRun`,
   and passing once one exists.
3. Three instances deploy and are **verified on tag**, with the vocabulary guard still enabled and
   config intact (`minReplicas=0`, KEDA rules, secretRefs).
4. **A real `DeliberationRun` node exists on the live spine**, written by the deployed Manager,
   carrying a verdict, a rationale, and a turn-by-turn transcript with both peers' contributions
   across more than one round. **This is the sprint. Anything short of it is intent, not outcome.**
5. An `LLMCall` node dated *after* this deploy, on **`claude-opus-5`** — which also closes DL-63's
   never-executed default.
6. The functionality-check row is written with teardown, and the fail-open path is re-proven: a
   forced LLM failure leaves trading unblocked.

## Risks

| Risk | Why it matters | Mitigation |
| --- | --- | --- |
| **Azure SAS rule cap** | DL-53: Azure caps 12 rules per namespace *and* per entity; the fleet already carries 33 rules across 13 agents. Three more bus identities may not fit. | Count before building. If it does not fit, the peers answering over the bus is the part to redesign, not the agent. |
| **LLM cost per run** | Three roles × rounds × every approved order. Previously zero because it never ran; this makes real spend appear for the first time. | Price it before enabling: `max_rounds` and per-role model are `tunable()`. Run `/audit-costs` after the first live run. |
| **Fail-closed vocabulary** | The S144 guard is live now. An undeclared `DeliberationRun` property raises inside a fault boundary and can stall a run (S148 pattern). | Scope item 6 is a prerequisite, not a cleanup. |
| **Deliberation slows the run** | A stage that talks to an LLM sits between the PM and execution. | Bounded rounds; the fail-open path already covers timeout. |
| **The peers are "similar enough" to collapse** | The temptation is to run all three prompts in one process — which is exactly the harness that stranded this capability. | Three instances is the point; per-role models (S109) and independent identities are the reason. |

## Closeout — evidence

> **Fill this in at handback. Do not return the sprint with this block unedited.**

- `make ci` result (pass count, coverage) and the remote gate run IDs:
- The acceptance check observed **failing** (which run, what it said):
- Bundle inventory against `ops/agent-genesis.md` — every part present, with its path:
- Clause counts added (all ⬜) in `ledger.md` / `laws/INDEX.md` / `test-plan.md`:
- Deploy: tag, all instances verified on it, `DeployRecord`, config intact:
- **The live `DeliberationRun`**: node key, verdict, rationale, round count, both peers' turns:
- The post-deploy `LLMCall` node and its model:
- Fail-open re-proof (forced LLM failure, trading unblocked):
- Functionality-check row + teardown:
