<!-- Agent: planning | Role: sprint handover -->
# Sprint 218 — a fleet whose last check failed gets no run, and the dashboard says why

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-218-a-broken-fleet-gets-no-run`
**Status:** MERGED — merged to `main` in `69f36016` (item 22 review, 2026-09-23); the line read: BUILT — amendment **R1** is locally proven (2026-09-20); its final handback SHA still requires remote gate proof. Do not merge or deploy.
**Version:** *next available MINOR at merge*
**Effort:** M
**Decisions:** [DL-179](../design-log.md) §6–§9 (the schedule and the three-sprint plan) · second of three sprints for work-queue item **58** · builds on S217 / DL-180

> **Why this bump kind.** The dispatcher gains a gate it did not have, and the dashboard gains a state
> it could not show. That is a MINOR.

**Builder:** GitHub Copilot. Every behaviour is pinned by a row in the test plan.
**If a number you measure differs from one written here, stop and report. Do not adjust and continue.**

🚨 **This sprint does not deploy on its own.** S219 (Telegram, and the answer buttons) is what tells
the human. Deploying S218 without it would hold runs with nobody told.

---

## 🔴 AMENDMENT R1 — returned 2026-09-20, read this before anything else

The build is good and the gate is green: `GATE PROVEN` for the branch tip `a9fcc4c` (CI + Security
Findings), worktree clean. The append-only correction you found and recorded in **DL-181** is right,
and both readers correctly go through `is_active_run_hold`. **Two defects remain, both measured on
your branch, both in the dashboard half — the half this sprint's title promises.**

### R1-a — a run held a second time the same day writes nothing, and can go unannounced

`hold_unready_run` returns early on `existing is not None` **without asking whether that hold is
still active**. So hold → release → hold again reuses the released node: nothing is written, and the
returned `DispatchHold` carries the **first** hold's `readiness_state`, `preflight_key` and
`failures`, while `released_at` stays set.

Measured on `a9fcc4c`, three dispatcher fires in one day:

| 3rd fire | Dispatcher | Dashboard | Node evidence |
| --- | --- | --- | --- |
| check **failing** | HELD | RED | `released_at` still set; `readiness_state` from hold #1 |
| check **stale / unknown** | HELD | **GREEN** | `released_at` still set; `readiness_state` from hold #1 |

🎯 **Row 2 is this sprint's goal failing:** the run is held and the dashboard is silent. It is
fail-safe in direction — a run is wrongly *held*, never wrongly placed — so it is not urgent, but
**S219 builds its notification on this record**, so a wrong record propagates into the human channel.

Reachability: the cron fires once, so this needs a manual re-fire — i.e. an incident, which is
exactly when the dashboard is being watched.

### R1-b — a held run with no fleet check tells the operator that nothing is failing

`_override` renders `"Tonight's run is held: {len(failures)} check(s) failing"`. When readiness is
`unknown` there are **no** failures, so **B3's own scenario** (no `FleetPreflight` at all) renders:

```text
Tonight's run is held: 0 check(s) failing - no failure detail recorded
```

**"0 check(s) failing" reads as "nothing is wrong" while the run is held.** This is live on your
branch today, independent of R1-a, and B11/B15 do not catch it because both plant failures. DL-47
asks for plain words at a glance; this is the opposite.

### Reproduce both, in this worktree, with no `.env`

```python
from datetime import UTC, datetime, timedelta
from kernel.graph_memory import InMemoryGraphStore
from orchestration.scheduled_dispatch_gate import hold_unready_run
from surfaces.dashboard.projections_readiness import readiness_override

g, RUN = InMemoryGraphStore(), "run-probe"
t0 = datetime(2026, 9, 21, 22, 30, tzinfo=UTC)

def preflight(key, passed, when, failures=()):
    g.merge_node("FleetPreflight", key, {
        "checked_at": when.isoformat(), "passed": passed,
        "failure_count": len(failures), "failures": list(failures),
        "agent_types_checked": ["scanner"]})

preflight("p1", False, t0 - timedelta(minutes=5), ("unrecoverable:provider:fmp:http_402",))
hold_unready_run(g, run_id=RUN, as_of=t0.date(), now=t0, max_age_minutes=70)   # held
t1 = t0 + timedelta(minutes=60)
preflight("p2", True, t1 - timedelta(minutes=5))
hold_unready_run(g, run_id=RUN, as_of=t0.date(), now=t1, max_age_minutes=70)   # released, placed
t2 = t1 + timedelta(minutes=120)                                               # p2 now stale
h = hold_unready_run(g, run_id=RUN, as_of=t0.date(), now=t2, max_age_minutes=70)
o = readiness_override(g, now=t2, max_age_minutes=70)
print("dispatch:", "HELD" if h else "placed", "| dashboard:", "RED" if o else "GREEN")
# R1-a today: dispatch: HELD | dashboard: GREEN
```

### Scope item 8 — the fix (both halves)

1. **A released hold is not a hold.** When readiness is not `ready` and the existing node fails
   `is_active_run_hold`, write a **new** append-only hold node instead of reusing the released one.
   Key it so it can never collide with a released node — `hold:<run_id>:<n>` with `n` the count of
   existing holds for that run, keeping the first at `hold:<run_id>` for B2/B6/B7 compatibility, or
   an equivalent scheme you can state in one line. `DispatchHold.node_key` must name the node
   actually written, never a stale one.
   🪰 **B6 is unaffected:** a re-fire while *continuously* failing finds an active hold and
   still reuses it, so "exactly one `RunHold` node" remains true for that case. If your key scheme
   changes that, stop and report rather than editing B6.
2. **Say what is actually wrong.** When a hold's `readiness_state` is `unknown`, the summary must
   say the fleet check is **missing or stale**, not count failures. Suggested wording, adjust for
   plain English but keep it free of ids: `"Tonight's run is held: no recent fleet check"`. The
   `failing` wording is unchanged.

**No new tunable, no vocabulary change, no law change** — `released_at` is already declared and
DRIFT-068 already covers the dispatcher guarantee.

### Tests to add

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| B16 | 🎯 re-hold after a release is a new, active hold | fire failing, fire passing (releases), fire failing again | a **second** `RunHold` exists and is active; `DispatchHold.node_key` names it; its `readiness_state` and `failures` are the **new** ones, not hold #1's; dashboard RED |
| B17 | 🎯 a stale check after a release still turns the light RED | as B16 but the third fire has **no fresh check** (`unknown`) | dispatcher holds **and** `/api/verdict` is `light="RED"` — the case that is GREEN today |
| B18 | 🪤 a held run with no check says so in plain words | B3's scenario: no `FleetPreflight` at all | summary does **not** contain `0 check(s)`; it names a missing or stale check; still passes B14's no-internal-ids check |

**Guard to plant (step 7, additional):** (e) restore the `existing is not None` early return, so B16
and B17 go red; (f) restore the failure-count wording for `unknown`, so B18 goes red.

### Success factors (added to the list below)

- [ ] A run held again after a release writes a new active hold carrying the new evidence (B16).
- [ ] A held run is never invisible on the dashboard, including when the check is stale (B17).
- [ ] A held run with no check explains itself without saying "0 check(s) failing" (B18).

### What does **not** change

Everything else in this spec stands, and every B1–B15 row must stay green. The version `0.100.00`
is **correct**: the middle group was widened to three digits (operator, 2026-09-20), so `0.100.00`
follows `0.99.00` and no re-bump is needed. Do not deploy; S219 still owns the human channel.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/master/laws/laws.md` (v1.4) | The master's locked constitution, including S217's `MST-OUT-04` and `MST-FAIL-05` | **LOCKED.** Read-only in this sprint |
| `docs/laws/flow.md` | The umbrella law for the run's flow; the dispatcher is described at line 69 | Read-only |
| `docs/laws/drift-register.md` | The one law-adjacent file you may append to | You will add one row (scope item 6) |

### The rule

1. **Before writing code**, read `agents/master/laws/laws.md`, `docs/laws/flow.md`,
   [`docs/laws/conventions.md`](../laws/conventions.md) and [`docs/laws/drift-register.md`](../laws/drift-register.md).
2. **Answer the law-cycle question below.**
3. **Write the Law reading record** (at the bottom) **before** your first code change.
4. **If a law contradicts this spec, STOP and report.**
5. Tests for behaviour a clause governs cite the clause ID in their docstring (conventions §3).

### 🩹 The law-cycle question — answered **NO, with one drift row**

No `contracts/` file changes, and no agent makes a new guarantee: the master's behaviour is unchanged
except the fault count (scope item 5), which no clause governs. The dispatcher and the dashboard have
**no law book**, so the new dispatcher guarantee has nowhere to live. That silence is a finding: add a
`drift-register.md` row (scope item 6). Do not create a law book in this sprint.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `orchestration/fleet_readiness.py` (new) | `agents/master/laws/laws.md` `MST-OUT-04`, `MST-IDN-02` | reads the master-owned `FleetPreflight`; must never write it |
| `orchestration/scheduled_dispatch.py`, `scripts/dispatch_scheduled_run.py` | `docs/laws/flow.md` | the run's entry point |
| `agents/master/fleet_preflight.py` | master `MST-OUT-04` | the fault fix only |
| `surfaces/dashboard/projections_readiness.py` (new), `projections_verdict.py` | `docs/laws/flow.md` | read-only projection |
| `infra/deploy-agents.ps1` | none | master window start |

⚠️ **The one invariant: a ready fleet runs exactly as today.** When the latest `FleetPreflight`
passed and is fresh, the dispatcher places the same `RunRequest` with the same id as before. If your
change alters any existing dispatcher test for that case, stop and report.

---

## Goal

After this sprint the dispatcher places the night's run **only if the master's latest fleet check
passed and is fresh**. Otherwise it writes a `RunHold` node and places nothing. The dashboard's
verdict light turns RED when the latest check failed or tonight's run is held, and its summary names
what failed. The master wakes at 20:25 UTC instead of 22:25, so its hourly checks at about 20:25,
21:25 and 22:25 give two retries before the 22:30 dispatch (DL-179 §6).

## Why (context)

Operator, 2026-09-19 (DL-179): *"fleet should not start. […] If anything is not funded or is not
accessible then the start should be delayed first for one hour then for another hour, Human needs to
notified and the human answer should determine if/when fleet runs."* And: *"It should show on the
dashboard as well."* S217 made the master record the check. Nothing acts on it yet.

### Measured, 2026-09-19 — on `main` @ `9f1955a`

| Claim | Value | How it was measured |
| --- | --- | --- |
| Agents' scale window | `start 30 22`, `end 30 00` UTC | *[measured]* `az containerapp show -n scanner … scale.rules[0].custom.metadata` |
| Master window start | `'25 22 * * *'` | *[measured]* `infra/deploy-agents.ps1:20` (`$MasterScaleStart`) |
| Dispatcher cron | `30 22 * * 1-5` | *[measured]* `orchestration/packs/trading_tunables.json` → `dispatcher.cron` |
| Master fleet-check interval | 60 min (`fleet_preflight_interval_minutes`) | *[measured]* S217, `agents/master/settings.py` |
| S217 faults per failed check | **one per failed probe**; the S217 spec said one per failed check | *[measured]* `agents/master/fleet_preflight.py`, loop over `failures` calling `sink.submit` |
| `FleetPreflight` key / props | `preflight:<checked_at ISO>`; `checked_at`, `passed`, `failure_count`, `failures`, `agent_types_checked` | *[measured]* `agents/master/fleet_preflight.py` |
| Module sizes | `scheduled_dispatch.py` **126**, `scripts/dispatch_scheduled_run.py` **107**, `orchestration/settings.py` **69**, `projections_verdict.py` **157**, `app.py` **181**, `fleet_preflight.py` **145** | *[measured]* `wc -l` |
| How the dashboard shows the verdict | the server sends `light` and `summary`; `static/verdict.js` renders them as given | *[measured]* `surfaces/dashboard/static/verdict.js` `render()` |
| A dispatcher law book | **none exists** | *[measured]* no `laws.md` covers `orchestration/scheduled_dispatch.py` |

---

## Scope — and what is deliberately NOT here

1. **`orchestration/fleet_readiness.py` (new, under 120 lines).**
   - `@dataclass(frozen=True) class Readiness: state: Literal["ready", "failing", "unknown"]; preflight_key: str; checked_at: str; failures: tuple[str, ...]`.
   - `fleet_readiness(graph, *, now, max_age_minutes) -> Readiness` reads `graph.list_nodes("FleetPreflight")`
     and picks the latest by `checked_at`. There are three outcomes:
     - None exists, or the latest is older than `max_age_minutes`: `unknown`, with an empty key when none exists.
     - The latest has `passed` true: `ready`.
     - Otherwise: `failing`, with its `failures`.
   - Read only. It never writes `FleetPreflight` (`MST-IDN-02`).
2. **The dispatcher gate.**
   - Add `preflight_max_age_minutes: int = tunable(70, ge=10, le=240, unit="minutes", why=...)`
     to `OrchestratorSettings`.
   - In the placement path, after the calendar says `place`, read `fleet_readiness`:
     - `ready` → place the run exactly as today. If a `RunHold` for this run id has `state="held"`
       and no `released_at`, merge `released_at` onto it. An active hold has `state="held"` and no
       `released_at`; `state` remains append-only `"held"` evidence.
     - `failing` or `unknown` → **do not place.** Merge a `RunHold` node with key `hold:<run_id>` and
       props `run_id`, `as_of`, `held_at`, `state="held"`, `readiness_state`, `preflight_key` and
       `failures`.
   - Print `held <run_id> reason=<readiness_state> failures=<n>` and exit **0**. A hold is a decision,
     not a crash. Put the gate in a new module if `scheduled_dispatch.py` would pass 150 lines.
   - Re-firing the dispatcher the same day merges the same `hold:<run_id>` key (no duplicates). If the
     fleet has become ready in the meantime, re-firing places the run and releases the hold.
3. **Vocabulary.** Add `RunHold` to `labels` and its props (`run_id`, `as_of`, `held_at`, `state`,
   `readiness_state`, `preflight_key`, `failures`, `released_at`) to `properties` in
   `trading_graph_vocabulary.json`.
4. **Dashboard.** New `surfaces/dashboard/projections_readiness.py` with a function
   `readiness_override(graph, *, now, max_age_minutes)`. It returns `None` when there is nothing to
   show. Otherwise it returns `{"state", "summary", "failures"}`, choosing the **first matching** case:
   - A `RunHold` with `state="held"` whose `as_of` is the latest held day: summary
     `"Tonight's run is held: <n> check(s) failing — <first failure>"`.
   - The latest `FleetPreflight` failed and is at most 180 minutes old: summary
     `"Fleet check failing (<n>) — <first failure>; next check in about an hour"`.

   In `verdict_projection`, when the override is not `None`, force `light="RED"`, replace `summary`,
   and add `readiness` to the payload. Otherwise the payload is unchanged, with no `readiness` key.
   Keep `projections_verdict.py` under 170 lines by putting the logic in the new module. **No
   frontend change**: `verdict.js` already renders the server's light and summary.
   🪤 **UI wording carries no sprint numbers, DL ids or internal jargon** (DL-47). Show failure
   strings as recorded (for example `unrecoverable:provider:fmp:unrecoverable:http_402`); prettifying
   them is S219's.
5. **S217 fault fix.** `run_fleet_preflight` submits **one** `critical` fault per **failed check**,
   not per failed probe. The message names `failure_count=<n>` and the classes present, and `context`
   carries the `failures` list. A passing check submits none.
6. **Drift row.** Append to `docs/laws/drift-register.md`: the dispatcher now guarantees "no run
   placed unless the latest fleet check passed within `preflight_max_age_minutes`", and **no law book
   declares it**. Resolution: a law home for the dispatcher (a later sprint).
7. **Master window.** In `infra/deploy-agents.ps1`, change the default `$MasterScaleStart` from
   `'25 22 * * *'` to `'25 20 * * *'` and add a comment citing DL-179 §6. If a test in
   `tests/test_deploy_script_invariants.py` pins the old value, update it and say so. Parse-check the
   script: `pwsh -NoProfile -Command "$null = [scriptblock]::Create((Get-Content -Raw infra/deploy-agents.ps1))"`.
8. **🔴 See AMENDMENT R1 at the top of this spec** — a released hold is not a hold, and a
   held run with no fleet check must say so instead of reporting `0 check(s) failing`. Tests B16–B18.

### Out of scope (do NOT build this sprint)

- **Telegram, notifications, answer buttons.** S219. No button, link or control is added to the
  dashboard: an unwired control is forbidden (DL-47).
- **Any "run at a later time" answer.** DL-179 §8.
- **Waking the fleet on demand.** DL-179 §8.
- **A law book for the dispatcher.** Only the drift row (scope item 6).
- **Deploying.** The full `up` happens after S219.

### The road not taken (LAW-06)

- **The dispatcher runs the probes itself.** Rejected in DL-179: only the master touches Key Vault (`MST-IDN-03`).
- **A hold exits non-zero.** Rejected: the job would show as failed in Azure and trigger its retry
  policy. A hold is a correct decision. The stdout line and the `RunHold` node are the evidence.
- **A frontend banner.** Rejected: the verdict hero already renders server wording. A second surface
  for the same fact is a second thing to keep true.

---

## The design decisions this sprint has to make

Record in `docs/design-log.md` (next free number; **DL-180 is the latest on `main`**, re-check at
merge), with rejected alternatives, **before implementing**:

1. **Freshness bound (70 minutes).** The check is hourly, so 70 minutes means "the most recent check",
   with 10 minutes of slack. Rejected alternative: no bound, where a check from yesterday would pass
   tonight.
2. **`unknown` holds, like `failing`.** No evidence is not evidence of readiness. Rejected
   alternative: `unknown` places the run, which would reopen the "a check that never ran reads as
   passed" hole (S183, item 28).

---

## Blast radius — measured 2026-09-19

| What | Detail |
| --- | --- |
| Files changed | `orchestration/fleet_readiness.py` (new), `orchestration/scheduled_dispatch.py` (126) or a new gate module, `orchestration/settings.py` (69), `scripts/dispatch_scheduled_run.py` (107), `agents/master/fleet_preflight.py` (145), `surfaces/dashboard/projections_readiness.py` (new), `surfaces/dashboard/projections_verdict.py` (157), `orchestration/packs/trading_graph_vocabulary.json`, `infra/deploy-agents.ps1`, `docs/laws/drift-register.md`, `docs/design-log.md`, tests |
| Agents affected | master (fault count only); no agent imports another |
| Contract change? | no |
| Graph vocabulary change? | **yes**, `RunHold`, so the deploy is a full `up` (after S219) |
| New env keys / tunables | `ORCHESTRATOR_PREFLIGHT_MAX_AGE_MINUTES` (default 70) |
| Deploy implication | **none now**; full `up` after S219 |

---

## Steps, in order

| # | Do | Expected |
| --- | --- | --- |
| 1 | `git worktree add ../trading-agents-sprint-218-a-broken-fleet-gets-no-run -b sprint-218-a-broken-fleet-gets-no-run origin/main`, then open **that folder** as the workspace | a worktree with **no** `.env` |
| 2 | Read the laws; fill the Law reading record | — |
| 3 | Record the design decisions in `docs/design-log.md` | — |
| 4 | Write tests B1–B15. Run `uv run pytest orchestration/tests surfaces/tests agents/master/tests tests/test_dispatch_scheduled_run.py -q --no-cov` | **red**, and paste it. Each new test fails for the missing behaviour |
| 5 | Implement scope items 1–7 | — |
| 6 | Same pytest command | **green** |
| 7 | **DL-70.** Plant each break below, watch its test go red, and restore it. Paste each red line | see "Guards to plant" |
| 8 | `make ci > ci.txt 2>&1; echo $?`, **never piped** | exit **0**, 100.00 % coverage |
| 9 | Push the branch; `make gate-ran` from the worktree | `GATE PROVEN`, and the printed SHA equals `git rev-parse HEAD` |
| 10 | Fill the handback sections; set **Status:** `BUILT`; commit, push, `make gate-ran` again | `GATE PROVEN` for the final SHA |

**Guards to plant (step 7):** (a) let `unknown` place the run, so B3 goes red; (b) drop the freshness
bound, so B4 goes red; (c) submit faults per probe again, so B10 goes red; (d) remove the verdict
override, so B11 goes red.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| B1 | 🎯 ready fleet runs as today | latest `FleetPreflight` passed, 5 min old | the same `RunRequest` id is placed as before this sprint; **no** `RunHold` node |
| B2 | 🎯 failing fleet is held | latest failed, 5 min old, 2 failures | no `RunRequest`; `RunHold` `hold:<run_id>` with `state="held"`, `readiness_state="failing"`, both failure strings; stdout `held <run_id> reason=failing failures=2`; exit 0 |
| B3 | 🪤 no check at all is held | no `FleetPreflight` nodes | held, `readiness_state="unknown"`, `preflight_key=""` |
| B4 | 🪤 a stale pass is held | latest passed, **71** min old, `max_age_minutes=70` | held, `readiness_state="unknown"` |
| B5 | latest wins | an older failed check and a newer passed one | placed |
| B6 | re-fire is idempotent | fire twice while failing | exactly one `RunHold` node, still `held` |
| B7 | re-fire after recovery releases | fire while failing, then add a passing check and fire again | run placed; `released_at` is set and `is_active_run_hold` returns false |
| B8 | the calendar still wins | a non-session day with a failing check | `skipped`, and **no** `RunHold` |
| B9 | the readiness reader never writes | a spy graph | `fleet_readiness` performs zero writes |
| B10 | one fault per failed check (S217 fix) | three probes fail in one check | exactly **one** `critical` fault, message contains `failure_count=3`, context carries all three |
| B11 | 🎯 dashboard: held turns the light RED | a `held` `RunHold` for the latest day | `/api/verdict` → `light="RED"`, summary starts `Tonight's run is held: 2 check(s) failing`, payload has `readiness.state="held"` |
| B12 | dashboard: failing check turns it RED | latest check failed 30 min ago, no hold | `light="RED"`, summary starts `Fleet check failing (1)` |
| B13 | dashboard: nothing to show leaves it unchanged | latest check passed | the payload is identical to the pre-sprint projection, with **no** `readiness` key |
| B14 | 🪤 UI wording carries no internal ids | B11's and B12's summaries | no match for `S\d{3}`, `DL-\d+` or `MST-` |
| B15 | 🪤 released hold no longer overrides verdict | a `RunHold` with `state="held"` and `released_at` | payload unchanged, with no `readiness` key |

---

## Success factors

- [ ] A ready fleet gets the same run as before (B1). A failing, missing or stale check gets a `RunHold` and no run (B2–B4).
- [ ] Holds are idempotent and released on recovery (B6, B7). The calendar still decides first (B8).
- [ ] One fault per failed check (B10).
- [ ] Dashboard RED with a plain-words reason when held or failing, and unchanged otherwise (B11–B14).
- [ ] Master window default is `'25 20 * * *'`; the script parses.
- [ ] Drift row filed; design decisions recorded with rejected alternatives.
- [ ] Every guard planted, watched red, restored (step 7), stated per guard.
- [ ] Every touched module < 200 lines; new modules < 150.
- [ ] **R1:** a re-hold after a release is a new active hold with the new evidence (B16); a held
      run is never invisible, including on a stale check (B17); a held run with no check does not
      say `0 check(s) failing` (B18).
- [ ] `make ci` exit 0, 100.00 % coverage; `GATE PROVEN` for the final SHA.

---

## Traps

🪤 **Compare timestamps as datetimes, not strings.** `checked_at` is ISO with an offset. Parse it.
Sorting strings works only while every value has the same format.
🪤 **`now` is injected everywhere.** No test may depend on the wall clock.
🪤 **Don't break the calendar skip.** A weekend must still print `skipped` and write nothing (B8).
🪤 **The dashboard reads through `CachingGraphStore`.** Build tests through the WSGI app as the
existing `surfaces/tests/test_dashboard_app.py` tests do, not only through the pure function.
🪤 **No `.env` in the worktree.** Every proof is a unit test. State that in the closeout.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass size.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: `kernel.tunable(..., why=...)` with bounds. The 180-minute dashboard window is
  a dashboard setting, not a literal.
- Faults, not silent failure: `kernel.fault_boundary`.
- `make ci` **all 12 steps** green, **100.00 % coverage floor**. **Never measure the gate through a pipe.**
- Version bump: MINOR, `uv.lock` staged with it.
- Every file you write ends with a newline.

---

## Sequencing after merge

1. `make gate-ran` exits 0 for the handback SHA (the planner verifies).
2. Merge to `main` (the planner).
3. **No deploy.** One full `up` after S219 merges (DL-179 §9).

---

## Handover — paste this to Copilot

🔴 **This is a RETURN, not a fresh build.** S218 is already implemented and its gate is green
(`a9fcc4c`: CI + Security Findings). Do **not** rebuild it, re-run the B1–B15 cycle, or re-bump the
version. The original build brief is kept below for reference only.

```text
S218 is BUILT and gate-proven, and is being returned for one amendment.

Branch: sprint-218-a-broken-fleet-gets-no-run, in its own worktree. Open THAT folder.
Pull first: the amendment is commit e7b1a41 on that branch.

Read AMENDMENT R1 at the TOP of docs/sprints/sprint-218-a-broken-fleet-gets-no-run.md
before anything else. It has two defects, a runnable reproduction, and scope item 8.

Order is binding:
1. Run the reproduction in R1 ("Reproduce both"). Confirm you see:
     dispatch: HELD | dashboard: GREEN
   If you see anything else, STOP and report - do not proceed on a different symptom.
2. Write tests B16, B17 and B18 FIRST. Paste the red run.
3. Implement scope item 8, both halves:
     (a) a released hold is not a hold - write a NEW append-only hold node rather than
         reusing a released one; DispatchHold.node_key must name the node written;
     (b) when readiness_state is "unknown", the summary must say the fleet check is
         missing or stale, not count failures.
4. Paste the green run. B1-B15 must ALL still be green - if any goes red, STOP and report
   rather than editing that row. B6 in particular should be unaffected.
5. Plant guards (e) and (f) from R1, paste each red line, restore.
6. make ci > ci.txt 2>&1; echo $?   - never through a pipe. Exit 0, 100.00% coverage.
7. Push, then make gate-ran from the worktree. Printed SHA must equal git rev-parse HEAD.
8. Update the Closeout, set Status: BUILT, commit, push, make gate-ran again on the
   final SHA. Say in the Closeout which key scheme you chose for (a) and why.

DO NOT:
- change pyproject.toml. 0.100.00 is CORRECT: the version scheme's middle group was
  widened to three digits on 2026-09-20, so 0.100.00 follows 0.99.00. No re-bump.
- touch the graph vocabulary (released_at is already declared), the laws, or DRIFT-068.
- add a tunable, a button, a link or any dashboard control.
- put sprint numbers, DL ids or MST- ids in UI text (B14 still applies to B18's wording).
- deploy or merge. S219 owns the human notification channel.
- let a test read the wall clock.
Every file you write ends with a newline.
If any measured number differs from the spec, or a law contradicts it: STOP and report.
```

<details>
<summary>Original build brief (superseded — kept for provenance)</summary>

```text
Build sprint S218 exactly as written in docs/sprints/sprint-218-a-broken-fleet-gets-no-run.md.

Branch: sprint-218-a-broken-fleet-gets-no-run, in its own worktree (step 1). Open THAT folder as your
workspace before doing anything else.

Order is binding:
1. Read agents/master/laws/laws.md, docs/laws/flow.md, conventions.md and drift-register.md.
   Fill the Law reading record BEFORE any code. The law-cycle answer is NO, plus one drift row.
2. Record the two design decisions in docs/design-log.md (next free DL number; DL-180 is the latest).
3. Write tests B1–B15 first and paste the red run.
4. Implement scope items 1–7. Paste the green run.
5. Plant the four guards (step 7), paste each red line, restore.
6. make ci > ci.txt 2>&1; echo $?   — never through a pipe. Exit 0, 100.00% coverage.
7. Push, then make gate-ran from the worktree. The printed SHA must equal git rev-parse HEAD.
8. Fill every handback section, Status: BUILT, commit, push, make gate-ran again.

DO NOT: deploy; merge; add any button, link or control to the dashboard; put sprint numbers or DL ids
in UI text; write FleetPreflight from outside the master; make a hold exit non-zero; let a test read
the wall clock. Every file you write ends with a newline.
If any measured number differs from the spec, or a law contradicts it: STOP and report.
```

</details>

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**. **Name every place you deviated from the spec**, even if you think it is
   harmless. S217's handback left one out.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02).

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| `orchestration/fleet_readiness.py` | `agents/master/laws/laws.md`; `docs/laws/conventions.md` | `MST-IDN-02`; `MST-OUT-04` | Yes. The reader is projection-only and never writes the master-owned `FleetPreflight` label. |
| Dispatcher placement | `docs/laws/flow.md`; `docs/laws/conventions.md` | No dispatcher clause exists | Yes. The missing law home is recorded as DRIFT-068 rather than creating a law book in this sprint. |
| Fleet preflight fault aggregation | `agents/master/laws/laws.md`; `docs/laws/conventions.md` | `MST-OUT-04`; `MST-FAIL-05` | No. The check still records one `FleetPreflight`; aggregation changes only its fault evidence. |
| Dashboard readiness projection | `docs/laws/flow.md`; `docs/laws/conventions.md` | No dashboard clause exists | No. It remains a read-only view of the graph and introduces no new control. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No `contracts/` file changes and no agent receives a new guarantee. The dispatcher gains an undeclared placement guarantee, recorded as DRIFT-068; a dispatcher law home is deferred. Recovery preserves append-only `RunHold` evidence and adds `released_at`; overwriting `state` is rejected by the graph-store invariant.

**Contradictions found between a law and this spec:** None.

**Laws found silent where a decision was needed:** The dispatcher placement gate has no law home. Recorded as DRIFT-068.

**Clauses that were ⬜ and are now proven:** None. This sprint cites existing master clauses for the reader and preflight regression tests but adds no clause.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| B1 | `test_latest_preflight_wins_over_an_older_failure` | `orchestration/tests/test_scheduled_dispatch_readiness.py` | PASS | DRIFT-068 |
| B2 | `test_failing_fleet_holds_run_and_records_both_failures` | `orchestration/tests/test_scheduled_dispatch_readiness.py` | PASS | DRIFT-068 |
| B3 | `test_absent_preflight_holds_with_unknown_readiness` | `orchestration/tests/test_scheduled_dispatch_readiness.py` | PASS | DRIFT-068 |
| B4 | `test_stale_passing_preflight_holds_as_unknown` | `orchestration/tests/test_scheduled_dispatch_readiness.py` | PASS | DRIFT-068 |
| B5 | `test_latest_preflight_wins_over_an_older_failure` | `orchestration/tests/test_scheduled_dispatch_readiness.py` | PASS | DRIFT-068 |
| B6 | `test_failing_refire_merges_one_hold` | `orchestration/tests/test_scheduled_dispatch_readiness.py` | PASS | DRIFT-068 |
| B7 | `test_recovery_releases_hold_and_places_run` | `orchestration/tests/test_scheduled_dispatch_readiness.py` | PASS | DRIFT-068 |
| B8 | `test_calendar_skip_writes_no_hold_when_fleet_is_failing` | `orchestration/tests/test_scheduled_dispatch_readiness.py` | PASS | DRIFT-068 |
| B9 | `test_readiness_reader_never_writes_master_owned_preflight` | `orchestration/tests/test_scheduled_dispatch_readiness.py` | PASS | `MST-IDN-02` |
| B10 | `test_many_failed_probes_emit_one_fleet_preflight_fault` | `agents/master/tests/test_fleet_preflight_faults.py` | PASS | `MST-OUT-04`; `MST-FAIL-05` |
| B11 | `test_held_run_forces_red_dashboard_readiness_verdict` | `surfaces/tests/test_dashboard_readiness.py` | PASS | none; no dashboard law home |
| B12 | `test_recent_failing_preflight_forces_red_dashboard_readiness_verdict` | `surfaces/tests/test_dashboard_readiness.py` | PASS | none; no dashboard law home |
| B13 | `test_passing_preflight_leaves_existing_verdict_payload_unchanged` | `surfaces/tests/test_dashboard_readiness.py` | PASS | none; no dashboard law home |
| B14 | `test_readiness_summary_has_no_sprint_law_or_design_identifiers` | `surfaces/tests/test_dashboard_readiness.py` | PASS | none; no dashboard law home |
| B15 | `test_released_hold_leaves_existing_verdict_payload_unchanged` | `surfaces/tests/test_dashboard_readiness.py` | PASS | none; no dashboard law home |
| B16 | `test_rehold_after_release_creates_active_hold_with_new_evidence` | `surfaces/tests/test_dashboard_reholds.py` | PASS | DRIFT-068 |
| B17 | `test_stale_check_after_release_keeps_dashboard_red` | `surfaces/tests/test_dashboard_reholds.py` | PASS | DRIFT-068 |
| B18 | `test_held_run_with_no_check_names_missing_fleet_check` | `surfaces/tests/test_dashboard_reholds.py` | PASS | DRIFT-068 |

**Tests added beyond the plan:** `test_invalid_or_out_of_order_preflight_facts_do_not_displace_latest`, `test_held_run_without_failure_list_uses_a_safe_summary`, and `test_failure_helper_handles_non_mapping_properties` cover malformed graph evidence and restore 100.00 % coverage. R1 adds B16-B18 in `test_dashboard_reholds.py`.

---

## Closeout — evidence

**Status:** BUILT; no deploy. R1 is locally proven; this final handback SHA still requires its own remote proof.

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\Downloads\project\trading-agents-sprint-218-a-broken-fleet-gets-no-run`; no `.env` was present.

**Result:** A fresh passing `FleetPreflight` preserves existing placement. Failing, absent, stale, malformed, or superseded preflight evidence prevents placement and persists one immutable `RunHold`; recovery adds `released_at`. The dashboard reports held or recent failing evidence as RED. The master emits one aggregate critical fault per failed check. Master scale start is `25 20 * * *`. R1 ensures a re-hold after release writes a new active fact, including when its readiness is stale, and explains unknown readiness as a missing recent fleet check.

**Files changed:** Dispatcher readiness reader/gate/settings and tests; master preflight fault aggregation and tests; dashboard readiness projection/settings/tests; dispatch script; graph vocabulary and dispatcher Dockerfile closure; master scale schedule; version and lockfile; design/drift/sprint/state records.

**Design decisions:** DL-181 records the 70-minute freshness bound, unknown-as-hold, and append-only `released_at` representation. DRIFT-068 records the dispatcher guarantee's missing law home.

**R1 key scheme:** The first hold remains `hold:<run_id>` for B2/B6/B7 compatibility. When no active hold remains, the next fact is `hold:<run_id>:<n>`, where `n` is the current count of holds for that run; it cannot collide with a released fact and `DispatchHold.node_key` names the fact just written.

**Proof — the red run first:**

```text
17 failed, 660 passed
```

**Proof — R1 reproduction and red run:**

```text
dispatch: HELD | dashboard: GREEN
3 failed in 2.18s
B16: assert 'hold:sched-2026-09-20' == 'hold:sched-2026-09-20:1'
B17: assert 'GREEN' == 'RED'
B18: assert '0 check(s)' not in "Tonight's run is held: 0 check(s) failing — no failure detail recorded"
```

**Proof — the green run:**

```text
Focused implementation suite: 690 passed in 21.70s.
Final full suite: 2903 passed, 6 skipped in 117.31s; total coverage 100.00%.
R1 focused S218 suite: 684 passed in 14.71s; B16-B18: 3 passed in 1.74s.
```

**Guards planted:** (a) allowing absent preflight evidence to place failed B3 (`placed` rather than `held`); (b) removing the freshness bound failed B4 (`placed` rather than `held`); (c) restoring one fault per failed probe failed B10 (3 faults rather than 1); (d) removing the verdict override failed B11 (`GREEN` rather than `RED`). R1 (e) restored the released-base-hold early return: B16 reused `hold:sched-2026-09-20` and B17 was `GREEN` rather than `RED` (`2 failed, 1 deselected in 2.28s`). R1 (f) restored failure-count wording for unknown: B18 rendered `0 check(s) failing` (`1 failed, 2 deselected in 2.20s`). Each break was restored and its focused check passed.

**Module line counts:** `fleet_readiness.py` 64; `scheduled_dispatch_gate.py` 60; `scheduled_dispatch.py` 147; `fleet_preflight.py` 141; `projections_readiness.py` 52; `projections_verdict.py` 167; `app.py` 184; `dispatch_scheduled_run.py` 118; R1 `test_dashboard_reholds.py` 127. The size gate passed; the original 214-line master test module was split to 193 lines plus a focused 34-line module.

**`make ci`:** Exit 0 from the S218 worktree. `2903 passed, 6 skipped`; `TOTAL ... 100.00%`; `pip-audit`, tracked detect-secrets, and untracked detect-secrets passed.

**R1 `make ci`:** Exit 0 from the S218 worktree. `2906 passed, 6 skipped in 93.49s`; `TOTAL ... 100.00%`; `pip-audit`, tracked detect-secrets, and untracked detect-secrets passed.

**`make gate-ran`:**

```text
uv run python scripts/assert_gate_ran.py
GATE PROVEN for aea47810e1cc18008aa3f11f6d868c21c953b39a:
  CI: success (attempt 1)
  Security Findings: success (attempt 1)
```

**Deviations from the spec:** The original state transition `held` to `released` is impossible under append-only graph properties. The corrected representation retains immutable `state="held"`, adds `released_at`, and defines active holds as held nodes without that property. The scope's vocabulary kept `released_at`; B15 was added. This builder-found spec defect is recorded in DL-181.

**Not met / verified failing:** Deployment is intentionally not done; S219 supplies the human notification path. The R1 handback commit and its own remote `make gate-ran` proof are pending.

---

## Return notes

- The local full CI gate is proven at 100.00 % coverage, and the implementation SHA `aea47810e1cc18008aa3f11f6d868c21c953b39a` is remotely proven by CI and Security Findings. No `.env` was present and no live probe ran.
- The state-transition defect was found against the actual append-only `GraphStore`, corrected before implementation, and recorded in DL-181.
- R1 preserves released evidence and writes a later hold under a numbered key, so a stale re-hold cannot be invisible to the dashboard or S219's future notification path.
- Do not deploy or merge this branch. Commit and push this R1 handback, then prove that final SHA with `make gate-ran` from this worktree.
