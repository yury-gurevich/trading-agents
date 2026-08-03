<!-- Agent: planning | Role: sprint handover -->
# Sprint 158 — An artifact that records its own failure is not proof of work

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-158-fail-open-must-be-loud`
**Status:** SPEC — packaged 2026-08-03 from a live finding on the `:s155` fleet
**Version:** fix → **0.86.01** (PATCH: last two digits)
**Effort:** M
**Decisions:** [DL-80](../design-log.md) the LLM veto has never run · [DL-57](../design-log.md)/[DL-59](../design-log.md)
*didn't look* must not render as *looked and found nothing* · [DL-70](../design-log.md) plant the
violation · [ADR-0020](../decisions/0020-llmcall-is-substrate-not-the-operators.md) `LLMCall` is the
one ledger · [S147 item 2](sprint-147-fresh-book-before-decision.md) **fail-visible, not fail-closed**
(the rationale this sprint preserves) · [LAW-02](../../ops/laws/LAW-02-successful-execution.md)
success is proven, never assumed

> **Why PATCH and not MINOR.** No new agent, no new stage, no new endpoint. Three existing behaviours
> are wrong: a config fallback that hides a misconfiguration, a record that hides its own failure,
> and a gate that accepts that record. `0.86.00` → **`0.86.01`**. If you disagree after reading the
> CLAUDE.md rule, say so in the return notes rather than silently choosing differently.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

This repo is governed by a **law book**. It is not documentation — it is the constitution the code
must satisfy, and it outranks this document.

| Location | How to treat it |
| --- | --- |
| `agents/<name>/laws/laws.md` | ☠️ **LOCKED. Read-only. Never edit.** A clause you believe is wrong is a `docs/laws/drift-register.md` row plus a report |
| `agents/<name>/laws/test-plan.md` | Read it to learn whether the behaviour you are changing is *proven* (🟩) or merely *asserted* (⬜). **You may add or update rows for clauses this sprint proves** — and [ADR-0021](../decisions/0021-clause-summary-mirrors-the-law.md) binds you: a clause summary mirrors `laws.md`, never the test |
| `docs/laws/*.md` | Umbrella laws. `drift-register.md` is the one law-adjacent file you may append to |

**New since S156:** `make ci` now runs `scripts/check_law_coverage.py`. If you mark a row 🟩 and the
cited test does not exist, or its docstring does not name the clause ID, **the gate fails**. Green
means what §3 always said it meant. Do not fight the checker — satisfy it or leave the row ⬜.

### Element → law map (read all of these)

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `kernel/bus_azure_config.py`, `kernel/bus_azure.py` (item 1) | `docs/laws/dependencies.md` (`DEP-BUS-*`), `docs/laws/conventions.md` | The bus is Layer-0. A dependency that degrades silently is exactly what `DEP-*` clauses exist to forbid |
| `agents/deliberator/poll.py`, `store.py` (items 2, 4) | `agents/deliberator/laws/laws.md` + `test-plan.md` | The deliberator is **0 / 48** — every clause you touch is ⬜, so you may be the first to prove one. `IDN` (what it exclusively writes), `OBS` (what must be observable), `FAIL` (what degradation is lawful) |
| `orchestration/packs/trading_deliberation_view.py` + acceptance (item 3) | `docs/laws/conventions.md`, `docs/laws/functionality-checks.md` | Orchestration has no agent law; umbrella conventions govern it |
| `orchestration/packs/trading_graph_vocabulary.json` (item 2) | S143/S144 discipline | **Any new prop on a property-enforced label must be declared or the guard raises on first write** |

**Fill the Law reading record** (template near the bottom) **before** your first code change.
**If a law contradicts this spec, STOP and report** — a contradiction you surface is a success.

---

## Why this sprint — what happened on 2026-08-02

[DL-80](../design-log.md) said the LLM veto had never run in production: zero `DeliberationRun`
nodes, every order ever submitted unvetoed, `_drop_vetoed` documented fail-open. S153 built the
deliberator as a real fleet agent to close it. It deployed with `:s155`.

**On 2026-08-02 at 08:01 UTC it ran, and `DeliberationRun` went 0 → 23.** Read one:

```text
verdict:        uphold
turns:          ()
transcript:     ()
rationale:      'llm unavailable (fail-open)'
vetoed_tickers: ()
role_models:    judge/defender/challenger = claude-opus-5
```

All 23 identical. And the ledger is **unchanged** — still 25 `LLMCall` nodes, all
`claude-sonnet-4-6`, newest **2026-07-15**. **Zero new model calls.** The `claude-opus-5` default is
correctly in place; the call never happened.

The cause, from the one `Fault` written that minute:

```text
source_agent:  deliberator-manager
source_module: agents.deliberator.poll      capability: review_pm_node
ValueError: The topic name provided does not match the EntityPath in the
            connection string used to construct the ServiceBusClient.
```

The manager must send to two peer topics. S133 gave each target an **entity-scoped** SAS string plus
a per-topic bundle. The namespace side is correct — `deliberator-proponent.requests` and
`deliberator-opponent.requests` both carry the `ta-deliberator-manager` rule, and the bundle secret
exists and is delivered. The bundle simply does not resolve those two topics, and
`connection_string_for_topic()` **silently returns the primary** when a topic is missing from the
map. So the manager addressed a peer topic with its own entity-scoped string.

### The three defects, in the order they compound

**1 · A missing bundle entry is indistinguishable from no bundle at all.**
`kernel/bus_azure_config.py::connection_string_for_topic` falls back to the primary on *every*
miss — no bundle configured, malformed JSON, topic absent. The first is legitimate; the third is a
misconfiguration that should never reach a send call.

**2 · The failure is recorded only as a string.** `_fail_open()` returns
`OrderReview("uphold", "llm unavailable (fail-open)", (), ())`. The single durable signal that no
debate happened is a **substring of a rationale**. Nothing downstream can ask "did this run actually
deliberate?" without string-matching English prose.

**3 · The acceptance gate accepts it.** `trading_deliberation_view.deliberation` observes
`reviewed` (from `verdicts`) and `debates` (from `debates`), and both are `Check(..., "required")`.
A fail-open run has one verdict and one debate entry per ticker, so **both checks pass**. S153's
whole point was a gate that fails when a declared stage produces nothing — and this stage now
produces something: a record of its own failure.

> **This is DL-57 one layer deeper, and it is worse than the original.** Before S153, deliberation
> was absent and the gate could not see it. Now deliberation is *present*, *green*, and *inert*. The
> project traded the invisible failure for a **confidently green** one.

**And the cost was not hypothetical.** The store is append-only, so those 23 `PMRun`s are now
permanently marked deliberated. **The backlog was consumed by a silent failure** — they cannot be
re-deliberated. That is what a fault-boundaried, string-only failure buys you.

---

## What ships (spec)

> Fill in the `**Result:**` line under each item as you complete it. Results go in this file.

### 1 · A configured bundle that does not cover a topic is an error, not a fallback

In `kernel/bus_azure_config.py`, separate the three cases that `connection_string_for_topic`
currently collapses:

| Case | Correct behaviour |
| --- | --- |
| No bundle configured (`connection_strings_json is None`) | Use the primary. **Legitimate** — single-entity deployments and local dev rely on it |
| Bundle configured, **topic present** | Use the topic's connection string |
| Bundle configured, **topic absent** | ☠️ **Raise**, naming the topic and the keys the bundle *does* carry |
| Bundle configured, **malformed JSON** | ☠️ **Raise**, naming the parse error |

The last two must **not** silently return the primary. A deployment that went to the trouble of
declaring a bundle has asserted that the bundle is the authority for topic routing; a miss is a
provisioning bug, and the whole point is that it stops being discovered at send time inside somebody
else's fault boundary.

Choose the exception type deliberately and say why in the return notes — a `ValueError` matching the
Azure SDK's own shape, or a named `BusConfigError`. **Do not** reuse a generic exception that a
caller's `except Exception` would swallow indistinguishably from a transport blip.

**Result:** Implemented `BusConfigError(ValueError)` and made `connection_string_for_topic()` distinguish no bundle (`None`, keep primary) from a configured-but-bad bundle. A configured bundle now raises on absent topics, malformed JSON, non-object JSON, and entries without a non-empty `connection_string`; the absent-topic error names both the requested topic and configured keys. A1-A5 pass.

### 2 · The manager checks it can address its peers *before* consuming work

The 23 lost `PMRun`s are the argument for this item. A preflight at manager construction
(`agents/deliberator/entrypoint.py::build_manager`, or the first poll pass — your call, state which)
resolves the connection string for **both** peer topics. If either cannot be resolved, the manager
must **not** mark work as deliberated: it should fault loudly and leave the `PMRun` unconsumed for a
later, healthy pass.

🚨 **This is the item with real blast radius. Get the failure direction right:** a manager that
cannot reach its peers must become *inert and loud*, never *productive and wrong*. Leaving work
unconsumed is correct here precisely because the store is append-only — an unconsumed `PMRun` can be
deliberated tomorrow; a fail-open record cannot be withdrawn.

**Result:** Implemented peer addressability preflight in the first poll pass, before `review_pm_node()` reads and consumes the `PMRun` into a `DeliberationRun`. `PeerClient.preflight()` is now part of the manager port, `ServiceBusPeerClient.preflight()` resolves both peer request topics, and preflight failures are captured as `peer_preflight` faults while leaving the `PMRun` pending and writing no half-clean deliberation record. Fail-open remains for LLM/debate failures after a successful preflight.

### 3 · A `DeliberationRun` records whether a debate actually happened

Make the fail-open state a **first-class, queryable fact** on the node rather than prose. Suggested
shape — take a better one if you find it, and record why:

- a count of tickers reviewed **with** a real transcript, and a count that **failed open**
- the failed-open tickers themselves, so the record names what went unvetoed
- keep `narrative` and `rationale` exactly as they are — they are for humans, and they were not wrong

**Any new prop must be declared in `orchestration/packs/trading_graph_vocabulary.json`** or the S144
guard raises fail-closed on the first real write. That guard is **armed on the fleet**. Re-run
`scripts/vocabulary_coverage.py` and `scripts/vocabulary_signatures.py` and paste the output.

**Result:** Added first-class `DeliberationRun` fields `real_debate_count`, `failed_open_count`, and `failed_open_tickers`; per-ticker debate payloads also carry `failed_open`. Human `narrative` and the exact `llm unavailable (fail-open)` rationale are preserved. The new props are declared in `trading_graph_vocabulary.json`; both vocabulary scripts exit 0 with no stdout, and C1-C3 pass including the planted missing-declaration failure.

### 4 · The acceptance gate stops calling an inert veto a pass

`trading_deliberation_view.deliberation` must distinguish *a debate happened* from *a record
exists*. A run whose reviews all failed open **must not** satisfy the stage's required checks.

**The verdict is FAIL, and that is a planning decision — implement it, do not re-litigate it.**
A fail-open deliberation means every order in that run reached the broker unvetoed, which is the
exact condition DL-80 exists to name. DL-59's third verdict `UNPROVEN` was created for a *timing*
state (orders placed, not yet filled — a run that will resolve itself), and this is not that: it is a
completed run whose risk-review layer did not execute.

**The DL-47 objection, answered rather than ignored:** a nightly false RED trains the operator to
ignore the light. This RED is not false — it is a real, live, unvetoed-order condition, and it is
bounded, because the underlying cause is a config fix, not a standing state. A gate that goes green
on "the veto did not run" is worth far less than one that goes red honestly.

**Result:** Implemented the planned FAIL verdict: the deliberation view now observes `debate_coverage` and `failed_open_count`, requires full real-debate coverage, and requires zero failed-open reviews. All-fail-open and mixed fail-open runs fail acceptance; a real deliberation still passes; the old 2026-08-02 empty-transcript artifact shape cannot pass.

### 5 · Prove every check can fail (DL-70)

No presence assertions. See the test plan; every test plants its violation.

**Result:** Proved failure paths with planted violations: absent/malformed bundle entries raise, peer preflight leaves work unconsumed and faults, fail-open records are queryable without string matching, missing vocabulary declaration raises `VocabularyError`, and a controlled mutation removing the new acceptance checks makes the 2026-08-02 regression test fail with `PASS` instead of `FAIL`.

---

## Test plan — every test I want, and why

**Ground rules.** Every test citing a law clause names the ID in its docstring — and since S156 the
gate enforces it. Every test **plants the violation and requires the failure**. Names are
descriptive, not prescriptive. **If you conclude a test is wrong or untestable, say so with a
reason — do not silently drop it.**

### A · Bus configuration (item 1)

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | no bundle → primary, unchanged | `connection_strings_json is None` | returns the primary; **this is the regression guard for local dev and single-entity deploys** |
| A2 | **bundle present, topic absent → raises** | bundle with topic `a`, ask for topic `b` | raises; message names `b` **and** lists the keys the bundle carries. Assert both — an error that does not say what *is* configured costs an hour |
| A3 | bundle present, topic present → that entry | bundle with `b` | returns `b`'s string, not the primary |
| A4 | malformed JSON → raises | `connection_strings_json = "{oops"` | raises naming the parse failure, **never** silently falls back |
| A5 | 🎯 **the 2026-08-02 regression** | manager-shaped bundle lacking `deliberator-proponent.requests` | the failure happens at **config resolution**, not inside `get_topic_sender`. Name the date in the docstring |

### B · Manager preflight (item 2)

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| B1 | unreachable peer → work stays unconsumed | peer topic unresolvable | **no `DeliberationRun` is written**; the `PMRun` is still pending for a later pass; exactly one `Fault` |
| B2 | healthy peers → normal operation | resolvable peers | a real debate runs and is recorded — **proves B1 did not just disable the agent** |
| B3 | one peer bad, one good | proponent resolvable, opponent not | still inert and loud; **no half-debate is recorded as a verdict** |

### C · The record (item 3)

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| C1 | fail-open is queryable without string-matching | a review that fails open | the node carries the counts/tickers; assert **without** reading `narrative` or `rationale` |
| C2 | a real debate is not marked failed-open | a working debate | counts say so; transcript non-empty; `LLMCall` keys recorded |
| C3 | new props are declared | the new prop shape | a `GuardedGraphStore` accepts the write; **then remove the declaration and require `VocabularyError`** — otherwise you have only proven the guard is quiet |

### D · The gate (item 4)

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| D1 | 🎯 **all-fail-open run does not pass** | the exact 2026-08-02 node shape: 1 verdict, 1 debate entry, empty transcript | the deliberation stage check **fails**; the run is not `ACCEPTANCE PASS`. **This is the test that would have caught it** |
| D2 | a real deliberation still passes | working debate with transcript | passes — **proves D1 did not just break the gate for everyone** |
| D3 | mixed run | 2 tickers, one real one fail-open | fails; the output names which ticker went unvetoed |
| D4 | the old shape cannot come back | remove the new check | D1 fails. Plant it and observe (DL-70) |

---

## Explicit non-goals

- ☠️ **No Azure, no Key Vault, no secrets, no deploy.** You have no `.env` and no credentials. The
  actual bundle repair is **operator work after merge** and is not yours — see *Sequencing*. Do not
  attempt it, do not simulate it, do not claim it.
- **Do not make the veto fail-closed.** Fail-open stays. S147 item 2 settled the reasoning: blocking
  a run on an LLM outage blocks *exits*, and exits are the risk-reducing side of the book. This
  sprint makes fail-open **loud**, not fatal.
- **No re-deliberation of the 23 consumed `PMRun`s.** Append-only; that history stands. Anything else
  is a rewrite of a settled record.
- **No change to `_drop_vetoed`'s policy** in `orchestration/veto.py`.
- **No new agent, no new stage, no schema migration.**
- **No `laws.md` edits.** Drift rows only.

### The road not taken (LAW-06)

Record any further options you rule out during implementation.

- **Fail-closed on an unreachable peer (block the run).** Rejected: it converts an LLM/transport
  outage into a trading outage, and the first thing it would block is selling. S147 already weighed
  this and chose fail-visible; nothing here changes that trade.
- **Detect fail-open by string-matching `rationale`.** It is a two-line diff and it works today.
  Rejected: the gate would then depend on the exact wording of a human-facing sentence, so a copy
  edit silently disables a safety check. That is the S151 shape — evidence reshaped to fit an
  available test.
- **Make `connection_string_for_topic` raise on *every* miss, including no-bundle.** Rejected: it
  breaks local dev and any single-entity deployment, which legitimately have no bundle. The defect is
  the *silent* part, not the fallback itself.
- **Have the manager retry the peer call.** Rejected as insufficient rather than wrong: a retry loop
  against a misconfigured connection string never succeeds, and would have burned the same 23
  `PMRun`s more slowly. Preflight is the fix; retry is a later, separate question.

---

## Sequencing after merge

1. `make ci` green locally (**10 steps now**), branch pushed, all four remote gates green **before**
   merging locally (DL-56 — pushing is the gate; no PR required).
2. **Operator, not the coding agent:** repair
   `servicebus-connection-strings-deliberator-manager` in `trading-agents-kv` so the bundle resolves
   `deliberator-proponent.requests` and `deliberator-opponent.requests`, then re-set the app secret.
   With item 1 shipped, a bad bundle now fails loudly instead of upholding everything.
3. Retag the fleet so items 1–4 are live. **Until then the gate change is not protecting anything** —
   the fleet is on `:s155`.
4. Watch the first scheduled run after the retag: expect a real `DeliberationRun` with a non-empty
   transcript and — the DL-80 proof — **a `claude-opus-5` `LLMCall` dated after the deploy**.
5. Record the functionality check in [`docs/laws/functionality-checks.md`](../laws/functionality-checks.md).

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds, never a bare literal.
- Faults, not silent failure — `kernel.fault_boundary`, errors redirected with provenance.
- `make ci` all **10** steps green, **100.00 % coverage floor**, before handback. Never lower it.
- Version bump in `pyproject.toml` to **0.86.01**, `uv.lock` staged with it.
- Any law clause your tests cover cites the clause ID in the docstring — **now gate-enforced**.
- If `main` has moved when you finish: merge `main` into the branch, resolve, re-run `make ci`, and
  **say so in the return notes** (DL-48).
- Secrets never through the worktree — chat or gitignored `.env` only.

---

## Handback contract — MANDATORY

**Append your results INSIDE this file, in the placeholders below.** Not a separate report, not
chat-only.

1. Fill the **Law reading record** *before* your first code change.
2. Fill the `**Result:**` line under **each** of the five spec items, in place.
3. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
4. Fill the **Closeout — evidence** block with real pasted output: `make ci` counts, the planted-
   violation runs, the vocabulary script output, the remote gate job results.
5. Fill the **Return notes**, including the exception-type decision from item 1 and the preflight
   placement from item 2.
6. State any success factor you did **not** meet plainly, as "verified failing" or "not done"
   (LAW-02). A proven failure is a valid handback; a silent gap is not.

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? (yes + what / no) |
| --- | --- | --- | --- |
| `kernel/bus_azure_config.py` | `docs/INDEX.md`, `docs/laws/INDEX.md`, `docs/laws/dependencies.md`, `docs/laws/conventions.md` | `DEP-BUS-04`, `DEP-CONFIG-01`, `DEP-CONFIG-02`, dependency pre-flight sequencing, conventions section 3 | yes - a configured per-topic SAS bundle is authoritative config, so a missing topic or malformed JSON must fail loudly before a send path can hide it as transport noise |
| `agents/deliberator/poll.py` + `entrypoint.py` | `agents/deliberator/laws/laws.md`, `agents/deliberator/laws/test-plan.md`, `docs/laws/dependencies.md`, `docs/laws/conventions.md` | `DLIB-TRG-01`, `DLIB-DEP-02`, `DLIB-DEP-04`, `DLIB-FAIL-01`, `DLIB-FAIL-03`, `DLIB-NEV-06`, `DEP-BUS-04`, `DEP-CONFIG-01` | yes - the peer-addressability check belongs before any `PMRun` is marked deliberated; on bad config the manager should be inert and fault-loud so the append-only backlog remains retryable |
| `agents/deliberator/store.py` (the record) | `agents/deliberator/laws/laws.md`, `agents/deliberator/laws/test-plan.md`, `docs/laws/conventions.md` | `DLIB-OUT-01`, `DLIB-OUT-02`, `DLIB-STA-02`, `DLIB-FAIL-01`, `DLIB-NEV-06`, `DLIB-OBS-01`, `DLIB-OBS-03` | yes - keep the human rationale/narrative intact, but add first-class queryable fail-open counts and tickers so a failed debate is not hidden inside prose |
| `orchestration/packs/trading_deliberation_view.py` | `docs/INDEX.md`, `docs/laws/INDEX.md`, `docs/laws/conventions.md`, `docs/laws/functionality-checks.md`, `docs/design-log.md` (`DL-57`, `DL-59`, `DL-70`, `DL-80`) | conventions section 3, LAW-02 proof discipline, DL-57/DL-59 distinction between "did not look" and "looked and found nothing" | no contradiction; implement the sprint's planned FAIL verdict for all-fail-open or mixed fail-open runs rather than reclassifying the completed inert veto as `UNPROVEN` |
| `trading_graph_vocabulary.json` | `docs/sprints/INDEX.md`, `docs/sprints/sprint-143-graph-vocabulary.md`, `docs/sprints/sprint-144-vocabulary-live.md`, `docs/laws/functionality-checks.md`, `docs/design-log.md` (`DL-68`, `DL-70`) | S143 closed vocabulary, S144 deployable guard/property discipline, DL-70 planted-failure requirement | yes - new `DeliberationRun` props must be declared in the pack and proven with the vocabulary scripts plus a planted missing-declaration failure |

**Contradictions found between a law and this spec** (a contradiction is a success — name it):

None found.

**Laws found silent where a decision was needed** (each needs a `drift-register.md` row):

None found.

**Clauses that were ⬜ and are now proven by this sprint's tests** (the deliberator is 0 / 48 — if
you prove any, add the row and let `check_law_coverage.py` confirm it):

`DLIB-OUT-01`, `DLIB-OUT-02`, `DLIB-NEV-06`, and `DLIB-FAIL-01` are now green in `agents/deliberator/laws/test-plan.md`. `scripts/check_law_coverage.py` exits 0; the remaining warnings are the pre-existing non-deliberator missing-row backlog.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_settings_no_bundle_uses_primary_connection_string` | `tests/test_bus_azure_config.py` | passed | n/a |
| A2 | `test_settings_bundle_topic_absent_raises_with_configured_keys` | `tests/test_bus_azure_config.py` | passed | n/a |
| A3 | `test_settings_resolves_topic_scoped_connection_string` | `tests/test_bus_azure_config.py` | passed | n/a |
| A4 | `test_settings_malformed_topic_bundle_raises_parse_error`; `test_settings_topic_bundle_must_be_json_object` | `tests/test_bus_azure_config.py` | passed | n/a |
| A5 | `test_2026_08_02_manager_bundle_missing_peer_topic_fails_config` | `tests/test_bus_azure_config.py` | passed | n/a |
| B1 | `test_unreachable_peer_preflight_leaves_pmrun_unconsumed` | `agents/deliberator/tests/test_manager_preflight.py` | passed | `DLIB-NEV-06` |
| B2 | `test_healthy_peer_preflight_still_records_real_debate`; `test_servicebus_peer_client_preflight_resolves_peer_topics` | `agents/deliberator/tests/test_manager_preflight.py` | passed | `DLIB-OUT-01`, `DLIB-NEV-06` |
| B3 | `test_one_bad_peer_preflight_records_no_half_debate` | `agents/deliberator/tests/test_manager_preflight.py` | passed | `DLIB-NEV-06` |
| C1 | `test_manager_fail_open_records_visible_rationale` | `agents/deliberator/tests/test_deliberator_agent.py` | passed | `DLIB-FAIL-01`, `DLIB-NEV-06` |
| C2 | `test_manager_reviews_pending_pmrun_with_two_peer_rounds_and_llm_costs` | `agents/deliberator/tests/test_deliberator_agent.py` | passed | `DLIB-OUT-01`, `DLIB-OUT-02` |
| C3 | `test_deliberation_run_props_are_declared_and_unknown_prop_fails` | `tests/test_graph_vocabulary_deliberation.py` | passed | `DL-80`, `DL-70` |
| D1 | `test_all_fail_open_deliberation_run_fails_acceptance` | `orchestration/tests/test_trading_acceptance_deliberation.py` | passed | `DLIB-NEV-06`, `DL-70` |
| D2 | `test_clean_cascade_is_accepted_with_deliberation_present` | `orchestration/tests/test_trading_acceptance_deliberation.py` | passed | `SUP-OBS-01`, `DL-70` |
| D3 | `test_mixed_fail_open_deliberation_run_fails_acceptance` | `orchestration/tests/test_trading_acceptance_deliberation.py` | passed | `DLIB-NEV-06`, `DL-70` |
| D4 | `test_old_empty_transcript_shape_fails_deliberation_checks`; controlled mutation of `trading_deliberation_view.py` removing the two new checks | `orchestration/tests/test_trading_deliberation_view.py`; mutation run against `orchestration/tests/test_trading_acceptance_deliberation.py::test_all_fail_open_deliberation_run_fails_acceptance` | passed; mutation verified failing | `DL-70` |

**Tests added beyond the plan:**

- `test_settings_topic_bundle_must_be_json_object` covers configured bundle JSON that parses but has the wrong shape; it closed the 100% coverage gap on `BusConfigError`.
- `test_servicebus_peer_client_preflight_resolves_peer_topics` covers the live `ServiceBusPeerClient.preflight()` resolver path without opening a network connection.
- Existing runtime/veto tests were extended to assert the new deliberation fields on idempotent writes, upheld real debates, and LLM-outage fail-open records.

---

## Closeout — evidence

**Files changed:**

- `kernel/bus_azure_config.py`, `kernel/__init__.py`
- `agents/deliberator/peer_client.py`, `agents/deliberator/poll.py`, `agents/deliberator/review_record.py`, `agents/deliberator/store.py`
- `orchestration/packs/trading_deliberation_view.py`, `orchestration/packs/trading_graph_vocabulary.json`
- Tests under `tests/`, `agents/deliberator/tests/`, and `orchestration/tests/`
- Law/test-plan docs: `agents/deliberator/laws/test-plan.md`, `docs/laws/INDEX.md`, `docs/laws/ledger.md`
- Sprint handback plus version files: this document, `pyproject.toml`, `uv.lock`

**Proven (LAW-02):**

- Initial worktree setup:

```text
> uv sync --extra azure
completed successfully before code changes; .venv included optional Azure dependencies
```

- Focused sprint suite:

```text
> uv run pytest tests\test_bus_azure_config.py agents\deliberator\tests\test_manager_preflight.py agents\deliberator\tests\test_deliberator_agent.py tests\test_deliberator_runtime.py tests\test_graph_vocabulary_deliberation.py tests\test_graph_vocabulary_properties.py orchestration\tests\test_trading_deliberation_view.py orchestration\tests\test_trading_acceptance_deliberation.py orchestration\tests\test_veto_stage.py --no-cov
collected 44 items
tests\test_bus_azure_config.py ..........                                [ 22%]
agents\deliberator\tests\test_manager_preflight.py ....                  [ 31%]
agents\deliberator\tests\test_deliberator_agent.py ...                   [ 38%]
tests\test_deliberator_runtime.py .....                                  [ 50%]
tests\test_graph_vocabulary_deliberation.py ..                           [ 54%]
tests\test_graph_vocabulary_properties.py ......                         [ 68%]
orchestration\tests\test_trading_deliberation_view.py ..                 [ 72%]
orchestration\tests\test_trading_acceptance_deliberation.py ....         [ 81%]
orchestration\tests\test_veto_stage.py ........                          [100%]
44 passed in 6.86s
```

- Planted acceptance mutation (removed `debate_coverage` and `failed_open_count` checks, then restored them):

```text
> uv run pytest orchestration\tests\test_trading_acceptance_deliberation.py::test_all_fail_open_deliberation_run_fails_acceptance --no-cov
collected 1 item
orchestration\tests\test_trading_acceptance_deliberation.py F            [100%]
FAILED orchestration/tests/test_trading_acceptance_deliberation.py::test_all_fail_open_deliberation_run_fails_acceptance
E   AssertionError: assert 'PASS' == 'FAIL'
```

```text
> uv run pytest orchestration\tests\test_trading_acceptance_deliberation.py::test_all_fail_open_deliberation_run_fails_acceptance --no-cov
collected 1 item
orchestration\tests\test_trading_acceptance_deliberation.py .            [100%]
1 passed in 1.19s
```

- Vocabulary scripts:

```text
> uv run python scripts\vocabulary_coverage.py
exit 0; stdout was empty

> uv run python scripts\vocabulary_signatures.py
exit 0; stdout was empty
```

- Law coverage:

```text
> uv run python scripts\check_law_coverage.py
[WARN] law coverage: 101 clause(s) have no test-plan row (assertion E warn-only)
[WARN] agents/analyst/laws/test-plan.md: 12 missing row(s): ANLZ-DEP-01, ANLZ-DEP-02, ANLZ-DEP-03, ANLZ-IDN-01, ANLZ-IDN-02, ANLZ-IN-04, ANLZ-NEV-04, ANLZ-ORD-01, ANLZ-ORD-02, ANLZ-PERF-01, ANLZ-SEC-01, ANLZ-SEC-03
[WARN] agents/execution/laws/test-plan.md: 13 missing row(s): EXEC-DEP-01, EXEC-DEP-02, EXEC-DEP-03, EXEC-FAIL-04, EXEC-IDN-01, EXEC-IDN-02, EXEC-ORD-01, EXEC-ORD-02, EXEC-PERF-01, EXEC-SEC-02, EXEC-SEC-05, EXEC-STA-04, EXEC-TRG-04
[WARN] agents/master/laws/test-plan.md: 21 missing row(s): MST-DEP-03, MST-FAIL-01, MST-FAIL-02, MST-FAIL-03, MST-IDM-02, MST-IN-01, MST-IN-02, MST-NEV-05, MST-OBS-01, MST-OBS-02, MST-OBS-03, MST-ORD-01, MST-ORD-02, MST-OUT-03, MST-PERF-01, MST-SEC-02, MST-SEC-03, MST-TRG-01, MST-TRG-02, MST-TYP-01, MST-TYP-02
[WARN] agents/monitor/laws/test-plan.md: 7 missing row(s): MON-IN-04, MON-NEV-05, MON-OBS-03, MON-ORD-02, MON-PERF-02, MON-SEC-02, MON-SEC-03
[WARN] agents/portfolio_manager/laws/test-plan.md: 12 missing row(s): PM-DEP-01, PM-DEP-02, PM-DEP-03, PM-FAIL-03, PM-IDN-01, PM-IDN-02, PM-ORD-01, PM-ORD-02, PM-PERF-01, PM-SEC-01, PM-SEC-03, PM-STA-04
[WARN] agents/provider/laws/test-plan.md: 22 missing row(s): PROV-DEP-01, PROV-DEP-02, PROV-DEP-03, PROV-DEP-04, PROV-DEP-05, PROV-FAIL-04, PROV-IDN-01, PROV-IDN-02, PROV-IDN-03, PROV-IN-02, PROV-NEV-02, PROV-OBS-01, PROV-ORD-01, PROV-ORD-03, PROV-OUT-03, PROV-PERF-02, PROV-SEC-03, PROV-SEC-06, PROV-SEC-08, PROV-STA-02, PROV-STA-05, PROV-TRG-03
[WARN] agents/reporter/laws/test-plan.md: 1 missing row(s): RPT-TYP-03
[WARN] agents/scanner/laws/test-plan.md: 13 missing row(s): SCAN-DEP-01, SCAN-DEP-02, SCAN-DEP-03, SCAN-FAIL-03, SCAN-IDN-01, SCAN-IDN-02, SCAN-NEV-04, SCAN-NEV-05, SCAN-ORD-02, SCAN-PERF-01, SCAN-SEC-01, SCAN-SEC-03
```

- Local `make ci`:

```text
> make ci
uv run ruff check . --output-format=github
uv run ruff format --check .
911 files already formatted
uv run mypy kernel contracts agents orchestration surfaces
Success: no issues found in 752 source files
uv run lint-imports
Contracts: 4 kept, 0 broken.
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests
[WARN] agents\deliberator\tests\test_manager_preflight.py: 198 lines (warn 150, hard block 200)
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run python scripts/check_law_coverage.py
uv run pytest
TOTAL                                                13787      0   2908      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
2097 passed, 5 skipped in 81.99s
uv run pip-audit
No known vulnerabilities found
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 2 new file(s)
```

- Version/lock:

```text
> Select-String -Path pyproject.toml -Pattern '^version = '
pyproject.toml:3:version = "0.86.01"

> uv lock
Resolved 174 packages in 2.93s
Updated trading-agents v0.86.0 -> v0.86.1
```

- Remote gate job results for pushed commit `717caf4e2145e0f55daae2ecde193a56410dc9e1`:

```text
> git push -u origin sprint-158-fail-open-must-be-loud
branch 'sprint-158-fail-open-must-be-loud' set up to track 'origin/sprint-158-fail-open-must-be-loud'.
To https://github.com/yury-gurevich/trading-agents.git
 * [new branch]      sprint-158-fail-open-must-be-loud -> sprint-158-fail-open-must-be-loud

> gh run watch 30792465337 --exit-status
✓ sprint-158-fail-open-must-be-loud CI · 30792465337
✓ quality in 36s (ID 91618718103)
✓ security in 2m42s (ID 91618718113)
✓ test in 1m1s (ID 91618834561)

> gh run watch 30792465339 --exit-status
Run Security Findings (30792465339) has already completed with 'success'
```

**Not met / verified failing:**

- Azure, Key Vault, SAS-bundle repair, deployment, fleet retag, live-spine proof, functionality check, and re-deliberation of the 23 consumed `PMRun`s: not done by explicit sprint non-goal.

---

## Return notes

- Exception type choice: chose `BusConfigError`, subclassing `ValueError`. It keeps the Azure SDK's config-error shape while giving callers and tests a specific type that is not indistinguishable from a transport blip.
- Preflight placement: first poll pass in `agents/deliberator/poll.py::review_pm_node`, before the `PMRun` is converted into a `DeliberationRun`. I did not put it only in `build_manager()` because the first poll pass records a durable `peer_preflight` fault through the injected sink and guarantees the append-only `PMRun` remains retryable.
- Fail-open policy preserved: LLM/debate failure still writes an uphold/fail-open record after a healthy peer preflight; unreachable peers make the manager inert and loud before consumption.
- Item 4 verdict implemented as `FAIL`, not `UNPROVEN`: all-fail-open and mixed fail-open deliberation runs now breach acceptance.
- Deliberator law coverage moved from 0 / 48 to 4 / 48. I left broader dependency clauses gray rather than overstating partial evidence.
- No secrets were printed or written. No Azure, Key Vault, deploy, retag, live proof, functionality check, or re-deliberation was attempted.
