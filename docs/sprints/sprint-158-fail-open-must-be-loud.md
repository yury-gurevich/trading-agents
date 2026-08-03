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

**Result:**

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

**Result:**

### 3 · A `DeliberationRun` records whether a debate actually happened

Make the fail-open state a **first-class, queryable fact** on the node rather than prose. Suggested
shape — take a better one if you find it, and record why:

- a count of tickers reviewed **with** a real transcript, and a count that **failed open**
- the failed-open tickers themselves, so the record names what went unvetoed
- keep `narrative` and `rationale` exactly as they are — they are for humans, and they were not wrong

**Any new prop must be declared in `orchestration/packs/trading_graph_vocabulary.json`** or the S144
guard raises fail-closed on the first real write. That guard is **armed on the fleet**. Re-run
`scripts/vocabulary_coverage.py` and `scripts/vocabulary_signatures.py` and paste the output.

**Result:**

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

**Result:**

### 5 · Prove every check can fail (DL-70)

No presence assertions. See the test plan; every test plants its violation.

**Result:**

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
| `kernel/bus_azure_config.py` | | | |
| `agents/deliberator/poll.py` + `entrypoint.py` | | | |
| `agents/deliberator/store.py` (the record) | | | |
| `orchestration/packs/trading_deliberation_view.py` | | | |
| `trading_graph_vocabulary.json` | | | |

**Contradictions found between a law and this spec** (a contradiction is a success — name it):

**Laws found silent where a decision was needed** (each needs a `drift-register.md` row):

**Clauses that were ⬜ and are now proven by this sprint's tests** (the deliberator is 0 / 48 — if
you prove any, add the row and let `check_law_coverage.py` confirm it):

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |

**Tests added beyond the plan:**

---

## Closeout — evidence

**Files changed:**

**Proven (LAW-02):**

**Not met / verified failing:**

---

## Return notes
