<!-- Agent: planning | Role: sprint handover -->
# Sprint 217 — the master checks every subsystem the fleet needs, and says which one is broken and whether a retry can fix it

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-217-master-checks-the-fleet`
**Status:** SPEC
**Version:** *next available MINOR at merge*
**Effort:** M
**Decisions:** [DL-179](../design-log.md) (operator decisions on work-queue items 57 and 58, and the three-sprint design) · closes work-queue item **57** · first of three sprints for item **58**

> **Why this bump kind.** The master gains a capability it did not have: one check across the whole
> fleet, recorded on the graph. That is a MINOR.

**Builder:** GitHub Copilot. Every behaviour is pinned by a row in the test plan.
**If a number you measure differs from one written here, stop and report. Do not adjust and continue.**

🚨 **This sprint does not deploy on its own.** It is the first of three (DL-179 §9). S218 adds the gate
that acts on this check and S219 tells the human. Merging is fine; deploying S217 alone is not.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/master/laws/laws.md` | The master's **locked constitution** | **LOCKED.** This sprint owes a law cycle, named below. Any other clause you believe is wrong gets a `drift-register.md` row plus a report, never a quiet edit |
| `agents/master/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it alongside `laws.md` |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | `drift-register.md` is the one law-adjacent file you may append to |

Binding sections: **`MST-IDN-01`**, **`MST-IDN-02`**, **`MST-IDN-03`**, **`MST-NEV-06`**, **`MST-FAIL-04`**, **`MST-OBS-*`**.

### The rule

1. **Before writing code**, read `agents/master/laws/laws.md` and `test-plan.md` in full.
2. Read [`docs/laws/conventions.md`](../laws/conventions.md) and [`docs/laws/drift-register.md`](../laws/drift-register.md).
3. **Answer the law-cycle question below.**
4. **Write the Law reading record** (at the bottom) **before** your first code change.
5. **If a law contradicts this spec, STOP and report.**
6. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered **YES**

This sprint adds a guarantee the master did not make: a fleet-wide check whose failures include
transport failures and probes that used to be optional. The master's law owes:

- **New clause `MST-OUT-04`:** *"`run_fleet_preflight` tests every pack-declared probe for every
  agent type in the grant policy and writes one `FleetPreflight` node per check. The check passes only
  if every probe passed or has a fresh costly-pass cache entry. A credential failure **or** a transport
  failure fails it."*
- **New clause `MST-FAIL-05`:** *"A probe status listed in the probe's `credential_failure_statuses`
  is recorded as `unrecoverable`. Any other 4xx is recorded as `unexpected`. A 5xx, timeout or network
  error is recorded as `transient`. All three fail the fleet check."*
- **Amend `MST-IDN-02`:** add `FleetPreflight` to the labels the master exclusively owns.
- **`MST-FAIL-04` is unchanged.** Per-agent activation keeps its current rule (transport failure does
  not block activation). The fleet check is stricter by design (DL-179 §1), and activation stays as a
  second line. Say this in the Changelog line so the two clauses are not read as a contradiction.
- Bump the law's version, add a Changelog line, add a `test-plan.md` row per new clause, cite the
  IDs in test docstrings, and let `make ci` recompute the rollup in `docs/laws/ledger.md` **and**
  `docs/laws/INDEX.md`.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/master/credential_probes.py` | master `laws.md` + `test-plan.md` | `MST-FAIL-04` today; `MST-FAIL-05` new |
| `agents/master/fleet_preflight.py` (new) | same | `MST-OUT-04` new; `MST-IDN-03` (only the master resolves secrets) |
| `agents/master/entrypoint.py` | same | `MST-ORD-02`, `MST-OUT-03` (start order) |
| `orchestration/packs/trading_credential_tests.json` | `MST-NEV-06` | every probe becomes `required: true` |
| `orchestration/packs/trading_graph_vocabulary.json` | `MST-IDN-02` | new label `FleetPreflight` |

⚠️ **The one invariant: activation behaviour does not change.** `activate()` must refuse and admit
exactly the same EHLOs as before, except where a probe moved from `required: false` to
`required: true` (that change is intended). If a change you make alters any existing activation test
other than those, stop and report.

---

## Goal

After this sprint the master can answer one question on demand: **can the whole fleet run right
now?** `run_fleet_preflight` tests every declared probe for every agent type and writes a
`FleetPreflight` node. The node says whether the check passed and, for each failure, which probe,
which agent type, which class (`unrecoverable`, `unexpected`, `transient`) and the sanitized reason.
The master runs the check once at start and then every `fleet_preflight_interval_minutes` while it is
up. Nothing acts on the result yet. S218 adds that.

## Why (context)

The operator decided on 2026-09-19 (DL-179): *"fleet should not start. MASTER should check EVERY
sub-system for expected functionality."* On item 57: *"make it count. This is an UNRECOVERABLE error
for the runtime."* Today each agent is checked only when it asks for its credentials, and a failure
refuses only that agent, so a run can start with part of the fleet missing. Six of the twelve probes
are `required: false`, including FMP, which S213 made the regime's VIX source.

### Measured, 2026-09-19 — on `main` @ `210f89c`

| Claim | Value | How it was measured |
| --- | --- | --- |
| Probes in the credential pack | **12** entries (tiingo, finnhub, fmp, alpaca-data, alpaca-broker, 4× anthropic, 3× openai) | *[measured]* `grep -o '"name": "[a-z0-9-]*"' orchestration/packs/trading_credential_tests.json` |
| Probes with `required: false` | **6** | *[measured]* `grep -c '"required": false'` on the same file |
| `credential_failure_statuses` changes any outcome today | **no**: every unexpected status below 500 is a credential failure regardless | *[measured]* `agents/master/credential_probes.py:140-148`, pinned by `test_an_unlisted_4xx_still_fails_the_probe` |
| Per-agent runner to reuse | `resolve_and_test_report(agent_type, store, secret_map, tests, cache=)` | *[measured]* `agents/master/credential_test.py:95` |
| Module sizes | `credential_probes.py` **169**, `credential_test.py` **144**, `entrypoint.py` **171**, `settings.py` **129**, `store.py` **194** (no room) | *[measured]* `wc -l` |
| `FleetPreflight` label exists | **no** | *[measured]* not in `labels` of `trading_graph_vocabulary.json` |

---

## Scope — and what is deliberately NOT here

1. **Classification (item 57).** In `credential_probes.py`, an unexpected status is classified as
   follows. A status in `credential_failure_statuses` gives `credential_failed("unrecoverable:http_<n>")`.
   Any other status below 500 gives `credential_failed("unexpected:http_<n>")`. A status `>= 500`
   gives `credential_transport_failed("http_<n>")`, as today. Timeouts and `OSError` stay transport
   failures, as today. Replace the 🪤 comment at `credential_probes.py:142-147` with one that states the
   new rule and cites `MST-FAIL-05`. `test_an_unlisted_4xx_still_fails_the_probe` keeps passing; extend
   it to assert the `unexpected:` prefix.
2. **Every probe required.** Set `"required": true` on all six entries that say `false`. Add a pack
   test asserting that no entry has `"required": false`.
3. **`agents/master/fleet_preflight.py` (new, under 150 lines).**
   - `run_fleet_preflight(*, graph, sink, secret_store, secret_map, grant_policy, credential_tests, pass_cache, now) -> FleetPreflightResult`.
   - For each `agent_type` in `sorted(grant_policy)`, call `resolve_and_test_report(...)`. Collect
     `failed_required`, `failed_optional` and `transport_failures` into a list of `PreflightFailure(probe, agent_type, klass, reason)`.
     `klass` is `unrecoverable` or `unexpected` from the reason prefix, and `transient` for a transport
     failure.
   - A `resolve_config` exception for an agent type (Key Vault unreachable, missing secret) is a failure
     `PreflightFailure(probe="secrets", agent_type=..., klass="transient", reason=<exception type name>)`.
     Never put the exception message in the reason: it can contain a vault URL or secret name.
   - Write **one** `FleetPreflight` node, key `preflight:<now ISO, seconds, UTC>`, with props
     `checked_at`, `passed` (bool), `failure_count`, `failures` (list of `"<class>:<agent_type>:<probe>:<reason>"` strings)
     and `agent_types_checked`.
   - Submit **one** fault with severity `critical` per failed check, naming the classes and counts, and
     no secret values.
   - Deduplicate by probe name **within one agent type only**. The same vendor probe under two agent
     types is two checks, because they use different secrets.
4. **Schedule.** In `entrypoint.main`, after `build_app`, start a daemon thread that runs the check
   once, then sleeps `settings.fleet_preflight_interval_minutes` and repeats. Wrap each iteration in
   `fault_boundary` so an exception is a fault, never a dead thread. Add the tunable to
   `MasterSettings`: `fleet_preflight_interval_minutes: int = tunable(60, ge=5, le=240, why=...)`. Add it
   to the master's PARAM table in `laws.md` (the PARAM/settings sync step checks this).
5. **Vocabulary.** Add `FleetPreflight` to `labels` and its five properties to `properties` in
   `trading_graph_vocabulary.json`.
6. **Law cycle** exactly as the law-cycle section above lists it.

### Out of scope (do NOT build this sprint)

- **Anything that acts on the result.** Holding the run, placement, the dispatcher: that is S218.
- **Telegram, notifications, the dashboard.** S218 and S219.
- **The master's KEDA window.** Moving it to 20:25 UTC is S218, with the schedule it serves.
- **New probe kinds** (Service Bus, Key Vault as a standalone probe). The check covers the pack's
  probes. A vault failure surfaces through `resolve_config` (scope item 3). A Service Bus probe is a
  follow-up row, not this sprint.
- **No change to `activate()`**, beyond what the `required` flip causes.
- **No ADR reversal.**

### The road not taken (LAW-06)

- **Unlisted 4xx becomes a transport (retryable) fault.** Rejected in DL-179: it would stop a probe
  blocking for a status nobody predicted, the opposite of the operator's "unrecoverable".
- **A `/preflight` HTTP endpoint.** Rejected in DL-179: a new unauthenticated route that spends probe
  cost on demand.
- **Delete the `credential_failure_statuses` field instead.** Rejected by the operator's decision:
  "make it count".

---

## The design decisions this sprint has to make

Record these in `docs/design-log.md` as a new entry (next free DL number, re-checked at merge), with
rejected alternatives, **before implementing** (LAW-06).

1. **Where the loop lives:** a daemon thread in the master process, or a separate function the HTTP
   server calls. The spec prescribes the thread; record why.
2. **How the costly-pass cache interacts.** A fresh cached pass counts as a pass (the same rule as
   `MST-NEV-06`). This keeps hourly checks from spending LLM tokens each time.

🪤 **Take the next free DL number, then re-check it at merge.** `DL-179` is the latest on `main` at
spec time.

---

## Blast radius — measured 2026-09-19

| What | Detail |
| --- | --- |
| Files changed | `agents/master/credential_probes.py` (169), `agents/master/fleet_preflight.py` (new), `agents/master/entrypoint.py` (171), `agents/master/settings.py` (129), `orchestration/packs/trading_credential_tests.json`, `orchestration/packs/trading_graph_vocabulary.json`, `agents/master/laws/laws.md`, `agents/master/laws/test-plan.md`, `docs/laws/ledger.md`, `docs/laws/INDEX.md`, `docs/design-log.md`, tests |
| Agents affected | master only; no agent imports another |
| Contract change? | no `contracts/` file changes; the law cycle is owed for the new guarantee |
| Graph vocabulary change? | **yes**, a new label, so the eventual deploy is a full `up` (after S219) |
| New env keys / tunables | `fleet_preflight_interval_minutes` (master) |
| Deploy implication | **none now**; the full `up` happens after S219 |

---

## Steps, in order

| # | Do | Expected |
| --- | --- | --- |
| 1 | `git worktree add ../trading-agents-sprint-217-master-checks-the-fleet -b sprint-217-master-checks-the-fleet origin/main`, then open **that folder** as the workspace | a worktree with **no** `.env` |
| 2 | Read the laws; fill the Law reading record | — |
| 3 | Record the design decisions in `docs/design-log.md` | — |
| 4 | Write the tests in the plan below. Run `uv run pytest agents/master/tests orchestration/tests -q --no-cov` | **red**, and paste it. Every new test fails for the missing behaviour, not for an import typo |
| 5 | Implement scope items 1–5 | — |
| 6 | Law cycle (scope item 6) | — |
| 7 | Same pytest command | **green** |
| 8 | **DL-70.** Plant each break below, watch its test go red, and restore it. Paste each red line | see "Guards planted" |
| 9 | `make ci > ci.txt 2>&1; echo $?`, **never piped** | exit **0**, 100.00 % coverage |
| 10 | Push the branch; `make gate-ran` from the worktree | `GATE PROVEN`, and the printed SHA equals `git rev-parse HEAD` |
| 11 | Fill the handback sections; set **Status:** `BUILT`; commit, push, `make gate-ran` again | `GATE PROVEN` for the final SHA |

**Guards to plant (step 8):** (a) make `credential_failure_statuses` inert again, so A1 goes red;
(b) let a transport failure pass the fleet check, so A5 goes red; (c) set one pack probe back to
`required: false`, so A7 goes red; (d) put the exception text into the `secrets` failure reason, so A8
goes red.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 listed status → `unrecoverable` (`MST-FAIL-05`) | probe with `credential_failure_statuses: [401, 402]`, transport returns **402** | `CredentialCheckResult("credential_failure", "unrecoverable:http_402")` |
| A2 | unlisted 4xx → `unexpected` (`MST-FAIL-05`) | same probe, transport returns **418** | `("credential_failure", "unexpected:http_418")` |
| A3 | 5xx stays transient (`MST-FAIL-05`) | transport returns **503** | `("transport_failure", "http_503")` |
| A4 | 🎯 all pass → `passed=True` (`MST-OUT-04`) | two agent types, every probe passes | one `FleetPreflight` node, `passed=True`, `failure_count=0`, `failures=[]`, both types in `agent_types_checked`, **no** fault |
| A5 | 🎯 transport failure fails the fleet check (`MST-OUT-04`) | one probe raises `TimeoutError` | `passed=False`, failure `transient:<type>:<probe>:TimeoutError`, one `critical` fault |
| A6 | credential failure fails it (`MST-OUT-04`) | one probe returns 401 (listed) | `passed=False`, failure `unrecoverable:<type>:<probe>:unrecoverable:http_401` |
| A7 | every pack probe is required | load the real `trading_credential_tests.json` | no entry has `"required": false`; the count of entries is **12** |
| A8 | 🪤 secret resolution failure is sanitized (`MST-OUT-04`, `MST-NEV-04`) | the secret store raises `RuntimeError("https://vault.example/secrets/KEY")` | failure is `transient:<type>:secrets:RuntimeError`; neither the node nor the fault contains `vault.example` or `KEY` |
| A9 | fresh costly cache counts as a pass (`MST-OUT-04`, `MST-NEV-06`) | a costly probe with a fresh cache entry | the probe is **not** run (spy), and the check passes |
| A10 | same probe under two agent types is two checks | the `anthropic` probe applies to two types and fails | two failures, one per agent type |
| A11 | 🪤 a crashing iteration does not kill the loop | the check function raises on its first call and passes on its second; run two iterations of the loop body with the sleep injected | a fault for the first; a `FleetPreflight` node for the second |
| A12 | activation unchanged (`MST-NEV-06`, `MST-FAIL-04`) | the existing activation tests | pass unmodified, except those that assumed `required: false` for a real pack probe; list any you changed and why |
| A13 | vocabulary declares the label | load the real vocabulary pack | `FleetPreflight` in `labels`; its five properties declared |

---

## Success factors

- [ ] A listed status is `unrecoverable`, an unlisted 4xx is `unexpected`, and 5xx/timeout is `transient` (A1–A3).
- [ ] `run_fleet_preflight` writes one `FleetPreflight` node per check and fails on any credential or transport failure (A4–A6, A10).
- [ ] No pack probe is optional (A7).
- [ ] No secret text reaches the graph or a fault (A8).
- [ ] The loop survives a crashing iteration (A11).
- [ ] Activation behaviour unchanged beyond the intended `required` flip (A12).
- [ ] Law cycle complete: `MST-OUT-04`, `MST-FAIL-05`, the `MST-IDN-02` amendment, version, Changelog, test-plan rows, rollups.
- [ ] Every guard planted, watched red, restored (step 8), stated per guard.
- [ ] Every touched module < 200 lines; `fleet_preflight.py` < 150.
- [ ] `make ci` exit 0, 100.00 % coverage; `GATE PROVEN` for the final SHA.

---

## Traps

🪤 **`required: true` changes activation too.** Once FMP is required, a bad FMP key refuses the
provider's activation. That is intended (DL-179 §5). Do not work around it in tests by leaving a probe
optional. Change the test's fixture pack instead.
🪤 **Do not make the loop sleep in tests.** Inject the sleep and the clock. A test that waits a real
minute will be killed by CI.
🪤 **`store.py` is 194 lines.** Put the node write in `fleet_preflight.py`, not `store.py`.
🪤 **Do not log or store an exception message** from secret resolution. The type name only (A8).
🪤 **The worktree has no `.env`.** Every proof here is a unit test with fakes. No live probe runs in
this sprint. State that in the closeout.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass size.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: `kernel.tunable(..., why=...)` with bounds.
- Faults, not silent failure: `kernel.fault_boundary`.
- `make ci` **all 12 steps** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.**
- Version bump: MINOR, `uv.lock` staged with it.
- Every file you write ends with a newline.

---

## Sequencing after merge

1. `make gate-ran` exits 0 for the handback SHA (the planner verifies).
2. Merge to `main` (the planner).
3. **No deploy.** S217 deploys with S218 and S219, as one full `up` (DL-179 §9).

---

## Handover — paste this to Copilot

```text
Build sprint S217 exactly as written in docs/sprints/sprint-217-the-master-checks-the-whole-fleet.md.

Branch: sprint-217-master-checks-the-fleet, in its own worktree (step 1). Open THAT folder as your
workspace before doing anything else.

Order is binding:
1. Read agents/master/laws/laws.md and test-plan.md in full, plus docs/laws/conventions.md.
   Fill the Law reading record at the bottom of the spec BEFORE any code.
2. This sprint OWES a law cycle (the spec lists it: MST-OUT-04, MST-FAIL-05, the MST-IDN-02 amendment).
3. Record the design decisions in docs/design-log.md (next free DL number; DL-179 is the latest).
4. Write the tests A1–A13 first and paste the red run.
5. Implement. Paste the green run.
6. Plant the four guards (step 8), paste each red line, restore.
7. make ci > ci.txt 2>&1; echo $?   — never through a pipe. Exit 0, 100.00% coverage.
8. Push, then make gate-ran from the worktree. The printed SHA must equal git rev-parse HEAD.
9. Fill every handback section, Status: BUILT, commit, push, make gate-ran again.

DO NOT: deploy; merge; edit any law clause other than the ones named; put an exception message or
secret text in any node, fault or log; make a test sleep for real; add to store.py (194 lines).
Every file you write ends with a newline.
If any measured number differs from the spec, or a law contradicts it: STOP and report.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02).

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| *(builder fills)* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *(builder fills)*

**Contradictions found between a law and this spec:** *(builder fills)*

**Laws found silent where a decision was needed:** *(builder fills)*

**Clauses that were ⬜ and are now proven:** *(builder fills)*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| *(builder fills)* | | | | |

**Tests added beyond the plan:** *(builder fills)*

---

## Closeout — evidence

**Status:** *(builder fills)*

**Tree the proofs ran in (and `.env` present?):** *(builder fills)*

**Result:** *(builder fills)*

**Files changed:** *(builder fills)*

**Design decisions:** *(builder fills)*

**Proof — the red run first:**

```text
(builder fills)
```

**Proof — the green run:**

```text
(builder fills)
```

**Guards planted:** *(builder fills)*

**Module line counts:** *(builder fills)*

**`make ci`:** *(builder fills)*

**`make gate-ran`:**

```text
(builder fills)
```

**Not met / verified failing:** *(builder fills)*

---

## Return notes

- *(builder fills)*
