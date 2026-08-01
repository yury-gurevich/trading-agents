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

> ## ⚠️ Resolved before you start: the operator's LLM claim
>
> The first delegated attempt at this sprint stopped and reported a genuine contradiction — correctly,
> and before writing any code. `OPR-IDN-01` claimed the operator was *"the sole LLM boundary"* and
> `OPR-IDN-02` claimed single-writer ownership of `LLMCall` (a **green** clause), which this sprint's
> `ANTHROPIC_API_KEY` and success factor 5 would both have broken.
>
> **It is now settled and merged — you are not blocked.**
> [ADR-0020](../decisions/0020-llmcall-is-substrate-not-the-operators.md) makes `LLMCall` a
> **substrate-level audit record**: any agent may call a model under its own laws, and every LLM
> caller writes its own `LLMCall` into the one shared cost ledger. `chore-llmcall-substrate` shipped
> the amendment (operator laws **v1 → v1.1**, `owns_graph` narrowed, `v0.84.07`).
>
> **What this means for you:** write `LLMCall` nodes directly from the deliberator — that is now the
> declared design, not a violation. Do **not** invent a `DeliberationLLMCall`; a per-agent label was
> considered and rejected because `surfaces/dashboard/llm_costs.py` and the `/audit-costs` skill both
> enumerate `LLMCall` only, and fragmenting it would hide the system's largest LLM spender from the
> bill. Do **not** re-amend the operator law; that work is done.

## Scope

> Fill in the `**Result:**` line under each item as you complete it, **in place**.

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

   **Result:** _fill at handback_

2. **`contracts/deliberator.py`** — typed request/reply for one debate turn and one verdict.
   Substrate/pack discipline (ADR-0012): the *mechanism* is domain-free; the trading proposition is
   the payload.
   **Result:** _fill at handback_

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
   **Result:** _fill at handback_

4. **`kernel/deliberation.py` is demoted, not rewritten** — it becomes the shared reasoning core the
   three instances call. **No change to debate behaviour**: same rounds, same prompts byte-for-byte,
   same verdict parsing. `orchestration/veto_context.py` keeps building the evidence packet.
   `orchestration/veto.py` stops being the runner; `local_pipeline.py` keeps working.
   **Result:** _fill at handback_

5. **Fleet wiring** — this is the long tail and it is where the sprint will actually be spent:
   three app names in `$AGENTS` (`infra/deploy-agents.ps1`) sharing one image suffix; grants in
   `trading_grants.json`; **`ANTHROPIC_API_KEY` in `trading_secrets.json`** (the deliberator is the
   first *pipeline* agent needing an LLM key — check the master's min-privilege delivery); three
   `ta_deliberator_*` Postgres roles (S131); three scoped Service Bus SAS identities (S133);
   KEDA scale windows; import-linter (agents are islands — the deliberator must not import
   `orchestration` or another agent).
   **Result:** _fill at handback_

6. **Vocabulary** — `DeliberationRun` is a declared label and `PMRun -DELIBERATED_BY->
   DeliberationRun` was declared in 0.84.04, but `DeliberationRun` has **no declared property
   list**, and the S144 guard is now **live on the fleet**. Declare its properties (including the
   transcript/narrative shape) and prove the superset with `scripts/vocabulary_properties.py`,
   or the first real write fails closed.

   **Also decide `LLMCall`'s shape here** — [ADR-0020](../decisions/0020-llmcall-is-substrate-not-the-operators.md)
   deliberately left it to this sprint, as the first non-operator writer. Two questions: whether
   `LLMCall` gains a declared property list under the guard (it is not property-enforced today —
   only `Fill` and `Recommendation` are), and **how the calling agent is identified** — a new
   property, or derivable from edges. Whichever you choose, the cost consumers
   (`surfaces/dashboard/llm_costs.py`, `/audit-costs`) must still be able to attribute spend per
   agent, because attributing the new spend is the entire reason the label stayed shared.

   **Result:** _fill at handback_

7. **Ledger + INDEX rows** for the new agent in `docs/laws/ledger.md` and `docs/laws/INDEX.md`.

   **Result:** _fill at handback_

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

### Scope boundary — what is NOT yours, and why "done" is smaller than it looks

**You have no credentials.** `.env` is not in this worktree, by design (CLAUDE.md: credentials never
exist as files inside the repo tree). So **success factors 3, 4, 5 and 6 are not yours** — deploying
the three instances, the live `DeliberationRun`, the post-deploy `LLMCall`, and the functionality
check are **operator sequencing after merge**, exactly as in S151 and S154.

**Your definition of done is:** scope items 1–7, `make ci` green, the four remote gates green, and
every placeholder section at the bottom of this file filled in.

Do **not** attempt to reach the live graph, Azure, or Alpaca, and do not work around a missing
credential. If something appears to require one, say so in the Return notes and stop.

**Hold on to this:** a fully green handback does **not** close [DL-80](../design-log.md). The LLM
veto will still never have run in production until the deploy and the live proof happen. Green code
is honest progress, not the outcome — report it that way.

## Risks

| Risk | Why it matters | Mitigation |
| --- | --- | --- |
| **Azure SAS rule cap** | DL-53: Azure caps 12 rules per namespace *and* per entity; the fleet already carries 33 rules across 13 agents. Three more bus identities may not fit. | Count before building. If it does not fit, the peers answering over the bus is the part to redesign, not the agent. |
| **LLM cost per run** | Three roles × rounds × every approved order. Previously zero because it never ran; this makes real spend appear for the first time. | Price it before enabling: `max_rounds` and per-role model are `tunable()`. Run `/audit-costs` after the first live run. |
| **Fail-closed vocabulary** | The S144 guard is live now. An undeclared `DeliberationRun` property raises inside a fault boundary and can stall a run (S148 pattern). | Scope item 6 is a prerequisite, not a cleanup. |
| **Deliberation slows the run** | A stage that talks to an LLM sits between the PM and execution. | Bounded rounds; the fail-open path already covers timeout. |
| **The peers are "similar enough" to collapse** | The temptation is to run all three prompts in one process — which is exactly the harness that stranded this capability. | Three instances is the point; per-role models (S109) and independent identities are the reason. |

---

## Handback contract — MANDATORY

**Append your results INSIDE this file, at the bottom, in the placeholder sections below.**
Not a separate report file. Not chat-only. Not a summary that points elsewhere. This document is the
one artifact: spec at the top, proof at the bottom.

Specifically:

1. Fill the **Law reading record** *before* your first code change.
2. Fill the `**Result:**` line under **each** of the seven scope items above, in place.
3. Fill the **Test plan results** table — one row per test, with its final name and status. A test
   you chose not to write needs a reason, not a blank.
4. Fill the **Closeout — evidence** block with real command output pasted in: `make ci` counts, the
   remote gate job results and run IDs, and the planted-violation runs.
5. Fill the **Return notes** block.
6. State any success factor you did **not** meet plainly, as "verified failing" or "not done"
   (LAW-02 — intent is never restated as outcome; a proven failure is a valid handback, a silent
   gap is not). Success factors 3-6 are operator sequencing and should be recorded as such, not as
   omissions.

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? (yes + what / no) |
| --- | --- | --- | --- |
| `agents/deliberator/laws/laws.md` (new, from `_TEMPLATE.md`) | `docs/laws/_TEMPLATE.md`; `ops/agent-genesis.md`; S153 scope item 3; S152 convention from `docs/laws/conventions.md` | Template categories `IDN/IN/TRG/OUT/NEV/STA/IDM/ORD/FAIL/TYP/SEC/DEP/OBS/PERF/CAP/PARAM`; conventions sections 2, 3, 5, 10; agent-genesis "one source of truth" and "nothing blind" invariants | Yes - author a new `DLIB` law from first principles, leave every clause gray, add a test-plan row for every clause, and do not copy another agent's constitution. |
| `agents/operator/laws/laws.md` (v1.1 — read `OPR-IDN-01/02` and ADR-0020) | `agents/operator/laws/laws.md`; `docs/decisions/0020-llmcall-is-substrate-not-the-operators.md` | `OPR-IDN-01`; `OPR-IDN-02`; `OPR-STA-03`; `OPR-DEP-01`; ADR-0020 decision/consequences | Yes - the deliberator may write shared `LLMCall` nodes directly, but must not invent `DeliberationLLMCall` or re-amend operator ownership. |
| `orchestration/veto.py` / `kernel/deliberation.py` callers | `ops/laws/LAW-02-successful-execution.md`; `ops/laws/LAW-06-capture.md`; `docs/design-log.md` DL-80/DL-57/DL-70/DL-82; `docs/sprints/sprint-109-heterogeneous-deliberation-models.md`; current `orchestration/veto.py`, `kernel/deliberation.py`, `orchestration/local_pipeline.py`, `agents/execution/poll.py` | LAW-02 `SE-02/SE-05`; LAW-06 `CP-01..05`; S109 "two judges" decision; S153 non-goals; execution fail-open contract documented in `_drop_vetoed` | Yes - demote the old runner into shared/core-adjacent helpers, keep prompts/rounds/verdict parsing byte-identical, and keep fail-open visible instead of making deliberation mandatory. |
| `docs/laws/conventions.md` | `docs/laws/conventions.md`; `docs/laws/INDEX.md` | Sections 2, 3, 4, 5, 7, 10 | Yes - new IDs are append-only, independence means no named peer-agent behaviour inside the law, and no clause turns green without a citing functional test. |
| `docs/laws/dependencies.md` (`DEP-LLM`, `DEP-BUS`) | `docs/laws/dependencies.md`; DL-53 | `DEP-LLM-01/02`; `DEP-BUS-01/02/03/04`; `DEP-POSTGRES-04`; `DEP-CONFIG-02` | Yes - peer turn request/reply stays on the existing bus pattern, LLM failures degrade/fail-open, and three identities must fit scoped bus/Postgres delivery rather than a shared credential. |
| `docs/laws/drift-register.md` | `docs/laws/drift-register.md`; DL-80/DL-82/DL-83 | Conventions section 9; no open deliberator row exists; S152-corrected rows establish "declaring is not proving" | No contradiction found after ADR-0020; record any newly discovered law/code mismatch instead of silently widening S153. |

---

## Test plan results — fill at handback

| # | What it proves | Test | Status | Planted-failure observed? |
| --- | --- | --- | --- | --- |
| 1 | Acceptance fails when a declared stage produces no artifact | | | |
| 2 | Acceptance passes once a `DeliberationRun` exists | | | |
| 3 | Manager pulls `PMRun`s with no `DeliberationRun` | | | |
| 4 | Peers answer one turn per request (served) | | | |
| 5 | Debate behaviour unchanged (rounds/prompts/verdict parsing) | | | |
| 6 | Fail-open holds: LLM failure never blocks trading | | | |
| 7 | Vocabulary: `DeliberationRun` properties declared, superset proven | | | |
| 8 | `LLMCall` written by a non-operator agent, spend attributable | | | |
| 9 | import-linter: deliberator imports neither `orchestration` nor another agent | | | |

---

## Closeout — evidence

> **Fill this in at handback. Do not return the sprint with this block unedited.**

- Files changed:
- Version bump (`pyproject.toml`, and `uv.lock` restaged):
- `make ci` result — pass count, skips, coverage:
- Planted-failure observations (scope item 1 especially):
- Remote gate run IDs **and job conclusions**, with the assertion that a run exists for the head SHA:
- New agent's clause count (`0 / N` is the correct honest number):
- Not met / operator sequencing:

---

## Return notes

- Branch and base commit:
- Every red remote run hit on the way (run ID + cause + fix):
- Anything the laws or this spec contradicted:
- Anything found and deliberately not fixed:
