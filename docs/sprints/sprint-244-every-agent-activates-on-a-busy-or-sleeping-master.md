<!-- Agent: planning | Role: sprint handover -->
# Sprint 244 — every agent activates, whether master is busy or asleep, and a retried EHLO is one activation

**Phase:** Etalon-first continuous improvement (DL-19) · work-queue 95 (live defect)
**Branch:** `sprint-244-every-agent-activates-on-a-busy-or-sleeping-master`
**Status:** BUILT 2026-09-29 by a cloud session on `claude/loving-gates-f8vfsd` (the session's forced branch; cut from `main` `8cef3ac`), not merged — C1–C11 green, six DL-70 plants red and restored, `make ci` exit 0 in the container (3,687 passed, 100.00 %); owed to the planner: `uv lock`, Windows `make ci`, `make gate-ran`, retag, F1, F2
**Version:** `0.119.03` (PATCH)
**Effort:** M
**Decisions:** [DL-248](../design-log.md) (the defect, measured, and the direction) · R004
([a2a-boundary](../research/a2a-boundary/a2a-boundary.md), why A2A is not the fix) · the builder's
decisions go to the **next free DL** (`DL-249` at spec time) · opens **DRIFT-091**

> **Why this bump kind.** No new capability: master's law book already declares an EHLO resend
> budget (`handshake_max_retries`, two timeouts) that no code reads, and the fleet crashes where
> that budget should have held. A fix, so PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build**, except the amendments this spec names. Anything else you believe is wrong is a `drift-register.md` row plus a report |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: master **`TRG`**, **`ORD`**, **`STA`**, **`IDM`**, **`NEV`** (`MST-NEV-02`,
`MST-NEV-06`), **`FAIL`**, **`SEC`**, **`PARAM`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered here: **YES**

This sprint adds guarantees master's book does not make (a repeated boot id is one activation;
EHLOs are served concurrently; an agent resends within a budget and fails loud when it runs out) and
corrects clauses that describe a fleet that no longer exists. It owes, in the same unit of work:

- **Master `laws.md` v1.7** (Changelog line):
  - `MST-TRG-01` amended — EHLO arrives as `POST /ehlo` over HTTP (not a "handshake queue"); an agent
    resends on a transport failure with the same boot id, within the kernel's budget; a 4xx or a bad
    signature is final.
  - `MST-ORD-02` amended — master may be asleep or busy when an agent boots (scale-to-zero, one
    activation wave per window); ordering is achieved by the agent's resend, never assumed.
  - `MST-STA-02` amended — one `AgentInstance` **per boot id**, not per EHLO message.
  - **New `MST-IDM-03`** — a repeated EHLO with the same `ephemeral_boot_id` **and** `agent_type`
    within the replay window returns the same ACTIVATE (same `instance_id`) and writes nothing new; the
    same boot id with a **different** `agent_type` is refused and hands out nothing (`MST-NEV-02`).
  - **New clause for concurrency** (your ID, in the fitting section) — master serves EHLOs
    concurrently, so one slow activation does not hold the others behind it, and its listen backlog
    holds a whole activation wave.
  - **New `MST-FAIL-06`** — an agent whose EHLO budget runs out exits non-zero with one line naming
    the attempts, the elapsed time and the last cause; nothing is swallowed.
  - `PARAM`: `handshake_timeout_1_seconds` and `handshake_max_retries` **leave** `MasterSettings` and
    the PARAM table (they describe the agent's side, which master cannot enforce; they move to the
    kernel). `handshake_timeout_2_seconds` stays, re-worded as **master's replay window**, which must
    be ≥ the kernel's EHLO budget. Add the backlog tunable's row.
- `test-plan.md` rows per new/amended clause; clause IDs in docstrings; rollups in **both**
  `docs/laws/ledger.md` and `docs/laws/INDEX.md` (let `make ci` compute the count); **DRIFT-091**:
  declared resend budget unread by any code, `MST-ORD-02` assumed a master that is up first, 54 + 5
  crashes measured (DL-248).

🪤 **The rollup is derived, not declared.** `MST-TRG-01` and `MST-ORD-02` are ⬜ today; proving them
moves the count too.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `kernel/bootstrap.py` (112) + a new kernel module for the retry and its settings | `agents/master/laws/laws.md` + `test-plan.md` (the handshake is master's protocol); `docs/laws/conventions.md` | `MST-TRG-01`, `MST-ORD-02`, `MST-SEC-01` (signature verified on the final answer), new `MST-FAIL-06` |
| `agents/master/http_server.py` (90) | same | new concurrency clause; `MST-IN-03` (malformed EHLO still 400, no write) |
| `agents/master/agent.py` (**182**) + a new master module for the replay | same | `MST-STA-02`, `MST-IDM-01`, new `MST-IDM-03`, `MST-NEV-02`, `MST-NEV-06` (a replay hands out only what was tested and granted for that type) |
| `agents/master/settings.py` (139), `agents/master/entrypoint.py` (**195**) | same, `PARAM` table | `handshake_*` rows; the backlog tunable |
| `agents/master/credential_test.py` (149) `PassCache`, `agents/master/key_vault.py` (138) `CachingSecretStore` | same | shared by concurrent activations now; `MST-NEV-06` |
| `kernel/graph_postgres.py` (147) `_run` reconnect path | `docs/laws/conventions.md`; ADR-0014 | the one connection master's threads now share |

⚠️ **The one invariant: a replay never hands one agent type another type's credentials, and never
hands out a credential whose test has not passed (`MST-NEV-02`, `MST-NEV-06`).** If your replay cache
could return an ACTIVATE for a different `agent_type`, or outlive the credential pass it was built on,
stop and report.

---

## Goal

When master is asleep, starting, or busy with a wave of 15 simultaneous EHLOs, every agent still
activates on its first boot: it resends within a bounded budget instead of crashing, master answers
a resend with the same activation instead of minting a second identity, and master works on EHLOs in
parallel instead of one at a time.

## Why (context)

Every nightly run starts with all 15 agents waking at 22:30 UTC and sending EHLO at once. Master
answers them one at a time, the last few pass their single 30-second attempt, crash, and come back
~90 s later after a container restart. Outside the window the same crash follows every deploy, test
run and restart, because master is at zero then. It has recovered every time so far, but only
because Container Apps restarts the container: an uncaught crash per boot is how a queue reads as a
fault, it mints an orphan `AgentInstance` each time, and it costs the run a minute and a half at its
very start. Master's own law book already promised the fix (a resend budget) and nothing implemented
it. The operator asked whether Google's A2A would have prevented this: it would not (R004 stands,
DL-248), and this sprint adopts the standard patterns that do — retry with backoff and jitter on
transient failures only, an idempotency key, and a concurrent server.

### Measured, 2026-09-29 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| EHLO crashes, 2026-09-01 → 09-29 | **54** `TimeoutError` containers on **19** days, **5** `HTTP 503`, across 8 apps | *[measured]* Log Analytics `ContainerAppConsoleLogs_CL`, the error line joined to a traceback through `activate_agent` in the same container |
| …of which inside the agent window (master up) | **~10** (09-12, 09-17, 09-19 at 22:30; 09-01, 09-05, 09-28, 09-29 during in-window deploys) | *[measured]* same query, bucketed against the KEDA windows |
| Master windows | master cron `25 20 * * *`–`00 3 * * *`; agents `30 22 * * *`–`00 3 * * *` (UTC); master was `25 22` before ~09-20 | *[measured]* `az containerapp show … scale.rules` |
| Master stays up through the window | no `KEDAScaleTargetDeactivated` for master between its start and 22:40 on 09-12 and 09-28 | *[measured]* `ContainerAppSystemLogs_CL` |
| The 22:30 wave, serialised | 09-24: 12 activations 22:30:16 → :41 (~2 s apart), 3 more at 22:32:06–09; 09-25: 12 by 22:30:55, 3 at 22:32:17–51 | *[measured]* `AgentInstance.started_at` on Neon |
| Per-activation service time | ~2–6 s (06:23:44 → :50 → :52.7 → :55.9 → :58.0 on the `s243` retag) | *[measured]* same |
| Master cold start | ~21 s (KEDA activation 06:23:22 → serving 06:23:44) | *[measured]* system + console logs |
| Master's server | `socketserver.TCPServer`, single-threaded; `request_queue_size` **5** | *[measured]* `agents/master/http_server.py:89`; Python default |
| Agent side | one `POST /ehlo`, `urlopen(timeout=30)`, no retry | *[measured]* `kernel/bootstrap.py:110` |
| Declared but unread | `handshake_timeout_1_seconds` 10, `handshake_max_retries` 5, `handshake_timeout_2_seconds` 300 in `MasterSettings`; read by no production code | *[measured]* grep; only `test_master_entrypoint.py:42` sets one |
| Orphans | a timed-out EHLO still completes on master: 3 extra `AgentInstance`s on the retag | *[measured]* Neon |
| Graph connection under threads | one psycopg 3 connection, `autocommit=True`, a cursor per statement; psycopg 3 serialises concurrent use of a connection; master's preflight thread already shares it | *[measured]* `kernel/graph_postgres.py:89–147`; psycopg 3 docs |
| In-window 503 mechanism | the ingress failing to connect past the 5-slot backlog | *[ASSUMED — not measured]* nothing in this sprint depends on it; F2 shows whether 503s stop |

---

## Scope — and what is deliberately NOT here

1. **The agent resends (kernel).** `activate_agent` makes up to `ehlo_max_attempts` attempts, each
   with `ehlo_attempt_timeout_seconds`, all inside `ehlo_budget_seconds`, with exponential backoff and
   **full jitter** between attempts, **one `ephemeral_boot_id` for all of them**. Retry only a
   transport failure: timeout, refused/reset/aborted connection, `RemoteDisconnected`, or HTTP
   **502/503/504**. **Never retry** a 4xx (400 malformed, 404, 422 refused, including a credential
   refusal) or a signature failure. One stderr line per failed attempt; on exhaustion raise a named
   error carrying attempts, elapsed and the last cause (the entrypoint exits non-zero, as today). The
   settings live in a kernel settings class with bounds and a `why=`; env keys stay unset, so the
   deploy is a retag. Every agent entrypoint gets this without an edit.
2. **Master replays a repeated boot id (`MST-IDM-03`).** The first EHLO for a boot id activates as
   today; a later one with the same boot id and `agent_type` inside `handshake_timeout_2_seconds`
   returns the stored ACTIVATE (same `instance_id`, same grants, same config, validly signed) and
   writes nothing. Same boot id, different `agent_type` → refused (422), nothing returned, nothing
   written. Two **concurrent** EHLOs with one boot id produce one activation (an in-flight guard, not
   just a dictionary). Entries expire with the window; the cache holds credentials only as long as the
   secret cache already does.
3. **Master serves EHLOs concurrently.** A threading server with daemon threads and a listen backlog
   from a new bounded master tunable (≥ one full wave). Make everything the activation path shares
   safe under threads: the instance counter (already locked), `PassCache` and `CachingSecretStore`
   (a lock; a duplicate live probe is waste, not a bug, but say which you chose), the replay cache, and
   the graph store's reconnect-after-drop path (two threads must not both replace `self._conn`).
   Split the server's construction from `serve_forever` so a unit test can run a real server on
   port 0.
4. **Law cycle** (master v1.7, as listed above) and DRIFT-091.

### Out of scope (do NOT build this sprint)

- **No change to the KEDA windows or `minReplicas`** (infra, not code; ruled out in DL-248).
- **No change to what an activation grants or tests** (`MST-NEV-02/06` semantics, the credential-test
  pack, remediation). A replay returns what the first activation granted; it never re-decides.
- **No pool of graph connections.** The shared connection is serialised by psycopg; measure the
  concurrent wave in C8 before asking for more.
- **No A2A.** R004 stands; the operator's question is answered in DL-248.
- **No ADR reversal.**

### The road not taken (LAW-06)

- **Master always on (`minReplicas 1`).** Rejected: a standing bill against LLM-tight funds, and it
  fixes neither the in-window wave nor a master restart or deploy.
- **Stagger the agents' cron windows.** Rejected: hides the queue, couples scheduling to master's
  throughput, and every deploy still wakes the whole fleet at once.
- **Only a longer single timeout.** Rejected: still one attempt, still dies on a 503 or a reset.
- **Retry without idempotency.** Rejected: a timed-out EHLO still completes on master, so each retry
  would mint another `AgentInstance` and add work to the queue it is waiting behind.
- **Replay from the graph (`AgentInstance` by boot id) instead of memory.** Rejected for now: needs a
  find-by-property on the kernel port; the window is minutes and master has one replica, so memory
  suffices. A master restart inside a boot's budget costs one extra instance: named, not hidden.
- **A2A as the handshake.** Rejected (R004, DL-248): no controller-issued-credentials handshake, and
  its discovery is the same HTTP call against a sleeping endpoint.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` under the next free DL with rejected alternatives BEFORE
implementing (LAW-06).** Take `DL-249` if it is still free on `main`; re-check at handback.

1. **The retry envelope's numbers and names** — defaults, bounds and `why=` for the kernel settings.
   The planner's starting point: attempt timeout **30 s** (today's value, so no attempt is ever shorter
   than now), **6** attempts, budget **300 s** (= master's replay window), backoff base 1 s doubling,
   capped at 30 s, full jitter. Deviate only with a reason.
2. **Which exceptions are transient** — the exact classification, as one pure, fully covered function.
   🪤 `urllib.error.HTTPError` **is a subclass of** `URLError`: classify by status first.
3. **The replay store** — key, expiry, in-flight guard, what it stores (the signed ACTIVATE), and how it
   never serves a different `agent_type`.
4. **Thread safety** — per shared object: lock, or accept-and-say-why.
5. **Where the new modules go** so `agent.py` (182) and `entrypoint.py` (195) do not cross 200.

---

## Blast radius — measured 2026-09-29

| What | Detail |
| --- | --- |
| Files changed | `kernel/bootstrap.py` (112) + new kernel retry/settings module(s); `agents/master/http_server.py` (90), `agent.py` (**182**), `settings.py` (139), `entrypoint.py` (**195**), `credential_test.py` (149), `key_vault.py` (138) + a new replay module; `kernel/graph_postgres.py` (147); master `laws.md` + `test-plan.md`; `docs/laws/ledger.md`, `INDEX.md`, `drift-register.md`; `docs/design-log.md`; tests |
| Agents affected | every agent (the kernel bootstrap is in every image) and master; none imports another |
| Contract change? | no `contracts/` change; `kernel/handshake.py`'s messages unchanged |
| Graph vocabulary change? | no (`AgentInstance`, `CapabilityGrant` props unchanged) |
| New env keys / tunables | new kernel tunables and one master tunable, **all defaulted, no env key set** |
| Deploy implication | image-only retag (all images rebuild; no pack, env or vocabulary change) |
| Rollback | retag to `s243`. Nothing else to undo: `AgentInstance` nodes are append-only and harmless, no schema, env, pack or broker state changes |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** under the next free DL.
3. **Plant the failing tests first** (C1, C5, C6, C8) and watch them fail. Paste the red output.
4. **Implement**: kernel retry → master replay → concurrent server → thread safety.
5. **Law cycle** — master v1.7, test-plan rows, docstring citations, rollups, DRIFT-091.
6. **Prove the guards can fail (DL-70)** — the plants below, each red, pasted, restored.
7. **`make ci` green** — redirected to a file, never piped.
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

Inject the sender, the sleep, the clock and the jitter source; **no test may reach the network**
(C8/C9 bind `127.0.0.1` on port 0 only) and no test may really sleep more than a few seconds.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| C1 | 🎯 a transient failure is resent | sender raises `TimeoutError` twice, then answers | `activate_agent` returns the ACTIVATE after 3 sends, **the same boot id each time**, backoff delays within bounds |
| C2 | each transient class is resent | `TimeoutError`, refused/reset connection, `RemoteDisconnected`, HTTP 502/503/504 | each retried |
| C3 | 🪤 a final answer is never resent | HTTP 400/404/422; a bad signature | exactly one send, raises at once |
| C4 | the budget ends loud | sender always times out; fake clock | stops at ≤ max attempts and ≤ budget; the error names attempts, elapsed, last cause; one stderr line per failed attempt |
| C5 | 🎯 a repeated boot id is one activation | two EHLOs, same boot id + type | same `instance_id`; one `AgentInstance`; grants written once; credential tests run once |
| C6 | 🪤 a boot id cannot fetch another type's credentials | same boot id, different `agent_type` | refused (422), nothing returned, nothing written |
| C7 | the replay window expires | fake clock past `handshake_timeout_2_seconds` | a fresh activation (new instance, tests re-run) |
| C8 | 🎯 a wave is served in parallel | real threading server on port 0, in-memory graph, activation made to take ~0.5 s; 15 concurrent `activate_agent` calls | all 15 activate; wall time well under 15 × 0.5 s; 15 `AgentInstance`s |
| C9 | concurrent resends of one boot id | two simultaneous EHLOs, one boot id | one activation, both get the same `instance_id` |
| C10 | the budgets agree | kernel and master defaults | kernel EHLO budget ≤ master replay window; backlog ≥ one wave |
| C11 | the graph reconnect is single | two threads hit a dropped connection | one replacement connection |

**DL-70 plants (each red, pasted, restored):** (1) max attempts 1 → C1 red; (2) 422 treated as
transient → C3 red; (3) a new boot id per attempt → C1 red; (4) replay removed → C5 red; (5) replay
keyed on boot id alone → C6 red; (6) `TCPServer` restored → C8 red.

---

## Success factors

- [ ] An agent that meets a sleeping, starting or busy master activates inside its budget, with one
      boot id, and never crashes on a transient failure (C1, C2, C8).
- [ ] A 4xx or a bad signature is final (C3); a spent budget exits loud (C4).
- [ ] A repeated boot id is one activation, and never another type's credentials (C5, C6, C9).
- [ ] Master serves a 15-agent wave in parallel (C8).
- [ ] Master v1.7 law cycle done; DRIFT-091 filed; rollups computed by `make ci`.
- [ ] Design decisions recorded with rejected alternatives.
- [ ] Every DL-70 plant red, pasted, restored.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **`HTTPError` is a `URLError`.** Catch-order bugs retry a 422. Classify by status first.
🪤 **A timed-out request is not a cancelled one.** Master finishes an EHLO whose caller has gone; that
is exactly why the replay must exist before the retry is safe. Build C5 before trusting C1 in the
field.
🪤 **A replay cache is a credential cache.** It must key on boot id **and** type, expire with the
window, and never outlive the pass it was built on.
🪤 **`serve()` is `# pragma: no cover` today.** Moving to a threading server without a real-socket test
leaves the fix unproven: split construction out and test it (C8).
🪤 **`agent.py` is 182 and `entrypoint.py` 195.** New logic goes in new modules.
🪤 **Do not grow the sprint into a connection pool.** Measure C8 on the shared connection first.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass a rule.
  📌 Current sizes: `agent.py` **182**, `entrypoint.py` **195**, `credential_test.py` 149,
  `graph_postgres.py` 147, `settings.py` 139, `key_vault.py` 138, `bootstrap.py` 112, `http_server.py` 90.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds.
- Faults, not silent failure — `kernel.fault_boundary` on master; the agent side has no sink before
  activation, so its record is the stderr line and the named error.
- `make ci` **every step** green, **100.00 % coverage floor**, redirected to a file.
- Version bump PATCH, next available at merge. Secrets never through the worktree.

---

## Sequencing after merge

1. Planner: `uv lock` with the PATCH bump, Windows `make ci`, push, **`make gate-ran`** from the
   worktree at the branch's `HEAD` (check the printed SHA), merge, post-merge CodeQL.
2. **Deploy: image-only retag** (operator's call). Rollback `s243`.
3. **F1 — the retag is the test.** Every revision boots at once against a cold master. From the
   retag's start: **0** EHLO `TimeoutError` / `HTTP 503` tracebacks in `ContainerAppConsoleLogs_CL`;
   retry lines where master was still waking; exactly one `AgentInstance` per container start (no
   orphans).
4. **F2 — the next 22:30 wave.** All 15 activations within ~60 s of the first, no ~90 s tail; 0 EHLO
   tracebacks. Record both in `docs/laws/functionality-checks.md`.

---

## Handover — paste this to the Claude cloud session

```text
Sprint 244 — every agent activates, whether master is busy or asleep, and a retried EHLO is one
activation. Spec: docs/sprints/sprint-244-every-agent-activates-on-a-busy-or-sleeping-master.md on
main (read ALL of it, then CLAUDE.md). Repo: yury-gurevich/trading-agents.

Branch: sprint-244-every-agent-activates-on-a-busy-or-sleeping-master, cut from main. Never main. If
your session forces another branch name, use it and name it in the handback.
You have NO .env, NO gh, NO Azure and no route to download.pytorch.org. Every proof is a unit test
(C8/C9 may bind 127.0.0.1 port 0; nothing else touches a socket). You cannot run `make gate-ran`: it
is owed to the planner. Leave uv.lock untouched and say so. Take the next free DL (DL-249 at spec
time; re-check on main).

This handover is complete: nobody will send you follow-up messages. If something in the spec is wrong
or blocked, record it in the handback (Return notes, "not done") and stop; do not wait.

What and why: kernel/bootstrap.py activate_agent sends ONE POST /ehlo (urlopen timeout 30) and the
agent crashes on any failure. Master (agents/master/http_server.py) serves on a single-threaded
socketserver.TCPServer with a backlog of 5, and each activation takes ~2-6 s. So at 22:30 UTC, when all
15 agents wake together, the last 3 time out, crash and return ~90 s later; outside the window every
deploy/restart meets a master at zero. Measured 2026-09-01..29: 54 EHLO TimeoutError crashes on 19
days + 5 HTTP 503 (DL-248). Master's own law book declares a resend budget (handshake_* in
MasterSettings) that no code reads. A timed-out EHLO still completes on master, minting an orphan
AgentInstance.

MUST RULE before any code: read, whole, agents/master/laws/laws.md + test-plan.md,
docs/laws/conventions.md, docs/laws/drift-register.md. Fill the Law reading record first.

Law-cycle answer: YES. Master v1.7: amend MST-TRG-01 (HTTP /ehlo; the agent resends transport failures
with one boot id within the kernel budget; 4xx/bad signature final), MST-ORD-02 (master may be asleep
or busy; ordering by resend), MST-STA-02 (one AgentInstance per boot id); new MST-IDM-03 (same boot id
+ type within the replay window -> same ACTIVATE, no writes; same boot id + other type -> 422, nothing
returned), a new concurrency clause, new MST-FAIL-06 (budget spent -> exit non-zero with attempts,
elapsed, last cause). PARAM: handshake_timeout_1_seconds and handshake_max_retries leave MasterSettings
and the table (moved to a kernel settings class); handshake_timeout_2_seconds becomes master's replay
window (>= the kernel budget); add the backlog tunable. test-plan rows, clause IDs in docstrings,
rollups in docs/laws/ledger.md AND docs/laws/INDEX.md, DRIFT-091.

Build:
1. Kernel: up to N attempts, per-attempt timeout, total budget, exponential backoff + full jitter, ONE
   boot id. Retry only timeout / refused / reset / RemoteDisconnected / HTTP 502-503-504. Never a 4xx
   or a signature failure. One stderr line per failed attempt; a named error on exhaustion. Settings in
   a kernel settings class (starting point: 30 s, 6 attempts, 300 s, base 1 s x2 capped 30 s).
2. Master: replay a repeated boot id (key boot id AND type, expiry = handshake_timeout_2_seconds,
   in-flight guard for concurrent duplicates).
3. Master: a threading server with a backlog tunable; make PassCache, CachingSecretStore, the replay
   store and the graph store's reconnect path safe under threads. Split server construction from
   serve_forever so a real server on port 0 is unit-tested.
4. Law cycle.

Order: next free DL (decisions 1-5 with rejected alternatives) -> red C1, C5, C6, C8 (paste) ->
implement -> law cycle -> DL-70 plants (max attempts 1; 422 retried; new boot id per attempt; replay
removed; replay keyed on boot id alone; TCPServer restored: each red, paste, restore) -> make ci
redirected to a file, exit 0, 100.00 %.

DO NOT:
- retry a 4xx or a signature failure; generate a new boot id per attempt.
- let a replay return another agent type's ACTIVATE, or outlive the replay window.
- change what an activation grants or tests, the credential-test pack, remediation, KEDA, minReplicas.
- add a graph connection pool, a contract change, a label, a property or an env key that must be set.
- grow any module past 200 (agent.py 182, entrypoint.py 195); # noqa to bypass a rule.
- let any test reach the network or sleep for real beyond a few seconds.
- claim a live proof or GATE PROVEN: F1, F2 and the gate are the planner's.
- pin a version: PATCH, next available at merge.

Handback — the planner returns it if ANY of these is missing:
[ ] Law reading record filled, including the law-cycle answer and contradictions/silences found.
[ ] Test plan results: C1-C11, each with final test name, file, PASS, clause IDs cited.
[ ] Closeout: the red run pasted before the fix; the green run after.
[ ] Each of the six DL-70 plants: what was planted, its red output, restored.
[ ] Thread safety: per shared object, locked or accepted, and why.
[ ] Module line counts for every file touched (all < 200).
[ ] make ci: the file, exit code, passed/skipped, coverage 100.00 %, dependency audit, detect-secrets.
[ ] Exactly how uv.lock was touched (untouched and owed, or re-resolved).
[ ] The design decisions under the DL you took, with rejected alternatives.
[ ] Return notes: scope held or moved; what you disagreed with after reading the laws; C8's measured
    wall time for the 15-agent wave.
[ ] Status: BUILT on the spec, and this sprint's README.md row leads with BUILT, in the same commit.
[ ] Owed items named: uv lock, make gate-ran, Windows make ci, retag, F1, F2.
Commit on the branch and PUSH it, then stop: no merge. Anything not met: "not done", never a
Result: for work not done.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| `kernel/bootstrap.py` + new `kernel/ehlo_retry.py`, `kernel/ehlo_settings.py` | `agents/master/laws/laws.md` (whole, v1.6) + `test-plan.md` (whole); `docs/laws/conventions.md` (whole) | `MST-TRG-01` (⬜, names a "handshake queue" that does not exist), `MST-ORD-02` (⬜, assumes master is up first), `MST-SEC-01` (⬜; the signature is verified on the final answer only), `MST-IN-01`; the `PARAM` rows `handshake_timeout_1_seconds` / `handshake_max_retries` describe the agent's side and are read by no code | **Yes.** The retry loop only wraps the *send*: signature verification stays outside it, so a bad signature can never be resent (`MST-SEC-01`). The budget's per-attempt timeout is clipped to what is left of the budget, so an agent never overruns master's replay window. |
| `agents/master/http_server.py` + new `agents/master/activation_replay.py` | same + `MST-IN-03`, `MST-NEV-02`, `MST-NEV-06`, `MST-STA-02`, `MST-IDM-01` | a malformed EHLO is still 400 with no write (`MST-IN-03`); a replay is the HTTP layer's (it holds the *signed* ACTIVATE), so `MasterAgent.activate()` keeps its v1.6 behaviour and every existing activation test | **Yes.** `MST-NEV-06` makes the replay a credential cache: its lifetime is capped by the credential-pass and secret-cache TTLs as well as the window (DL-249 D3), not the window alone. |
| `agents/master/agent.py` (182) | same | `MST-STA-02`, `MST-IDM-01`, `MST-OBS-01` | **Yes** — untouched. The replay lives outside it, so `agent.py` stays at 182. |
| `agents/master/settings.py`, `entrypoint.py` | same, `PARAM` table | `PARAM` rows; the new backlog tunable | No. `entrypoint.py` passes `settings` to `serve()` (the same line count). |
| `agents/master/credential_test.py` `PassCache`, `key_vault.py` `CachingSecretStore` | same | `MST-NEV-06` (a fresh costly-pass entry is a pass), `MST-FAIL-04` (a transport failure caches nothing) | **Yes** — the lock guards the dictionaries only, never the live probe/fetch: holding it across a probe would serialise every activation behind the slowest one (a duplicate probe is waste, not a violation of `NEV-06`). |
| `kernel/graph_postgres.py` `_run` | `docs/laws/conventions.md`; ADR-0014 | none of master's; the store is kernel | No. |
| — | `docs/laws/drift-register.md` (header, the whole Master and System-level sections, the Provider/Scanner/Forecaster rows up to DRIFT-090; the other agents' sections skimmed for master references: none) | DRIFT-059 (master laws silent on remediation; untouched here), DRIFT-030/086 (retry cadence is a neighbouring kernel gap) | Next free is **DRIFT-091**. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** **YES** (the
spec's answer, confirmed). No `contracts/` or `kernel/handshake.py` change; new guarantees: a
repeated boot id is one activation (`MST-IDM-03`), EHLOs are served concurrently (`MST-ORD-03`), an
agent resends within a budget and fails loud when it runs out (`MST-FAIL-06`). Amended: `MST-TRG-01`,
`MST-ORD-02`, `MST-STA-02`, and `MST-IDM-01` (see below). Master v1.7.

**Contradictions found between a law and this spec:** one, inside the book rather than against the
spec. **`MST-IDM-01`** reads *"Two EHLO messages from the same `agent_type` produce two distinct
`instance_id` values"* — read literally, the new `MST-IDM-03` (same boot id → same `instance_id`)
breaks it. The spec's amendment list omits `IDM-01`. Resolved by the smallest amendment that keeps
its intent (multiple instances of one type): *"…with different `ephemeral_boot_id`s…"*, recorded in
the v1.7 changelog. Not a STOP: the spec's own `MST-IDM-03` requires it, and the existing
`IDM-01` test already uses two boot ids.

**Laws found silent where a decision was needed:** (1) no clause says how long a credential that
passed may be *re-delivered* without a re-test; `MST-NEV-06` speaks of a "fresh costly-pass cache
entry" only. Decided in DL-249 D3 (replay lifetime ≤ pass TTL and secret TTL) and written into
`MST-IDM-03`. (2) `MST-FAIL-01` says a graph failure leaves *"the EHLO … not acknowledged"* but not
what the agent does next; `MST-TRG-01` v1.7 now says (a dropped connection is a transport failure
and is resent). (3) The `CAP` block still names `channel: handshake_queue`; the spec does not list
it and `CAP` is not a clause, so it is recorded in DRIFT-091 rather than edited.

**Clauses that were ⬜ and are now proven:** `MST-TRG-01`, `MST-ORD-02` (both amended, then proven);
new `MST-IDM-03`, `MST-ORD-03`, `MST-FAIL-06` added proven. `MST-STA-02` and `MST-IDM-01` were 🟩
and are re-proven on their amended text.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| C1 | `test_a_timed_out_ehlo_is_resent_with_one_boot_id` | `tests/test_ehlo_retry.py` | PASS | `MST-TRG-01`, `MST-ORD-02` |
| C2 | `test_each_transient_failure_is_resent` (10 cases: `TimeoutError`, refused, reset, aborted, `RemoteDisconnected`, `URLError`(refused), `URLError`(timeout), 502, 503, 504) | `tests/test_ehlo_retry.py` | PASS | `MST-TRG-01`, `MST-ORD-02` |
| C3 | `test_a_final_answer_is_never_resent` (400, 404, 422, 500, DNS `URLError`, `ValueError`, `BrokenPipeError`); `test_a_bad_signature_is_never_resent` | `tests/test_ehlo_retry.py` | PASS | `MST-TRG-01`, `MST-SEC-01` (cited; row stays ⬜, see Return notes) |
| C4 | `test_a_spent_attempt_budget_ends_loud`; `test_the_budget_stops_resends_before_the_attempt_cap` | `tests/test_ehlo_budget.py` | PASS | `MST-FAIL-06`, `MST-TRG-01` |
| C5 | `test_a_repeated_boot_id_is_one_activation` | `agents/master/tests/test_activation_replay.py` | PASS | `MST-IDM-03`, `MST-STA-02` |
| C6 | `test_a_boot_id_cannot_fetch_another_types_credentials` | `agents/master/tests/test_activation_replay.py` | PASS | `MST-IDM-03`, `MST-NEV-02`, `MST-NEV-06` |
| C7 | `test_the_replay_window_expires` | `agents/master/tests/test_activation_replay.py` | PASS | `MST-IDM-03` |
| C8 | `test_an_activation_wave_is_served_in_parallel` (real `ThreadingTCPServer` on 127.0.0.1:0, real kernel client, signatures verified) | `agents/master/tests/test_ehlo_server.py` | PASS | `MST-ORD-03`, `MST-TRG-01` |
| C9 | `test_concurrent_resends_of_one_boot_id_are_one_activation` | `agents/master/tests/test_activation_replay.py` | PASS | `MST-IDM-03`, `MST-ORD-03` |
| C10 | `test_the_kernel_budget_fits_inside_the_replay_window`; `test_the_listen_backlog_holds_one_wave` | `agents/master/tests/test_ehlo_budgets.py` | PASS | `MST-IDM-03`, `MST-TRG-01`, `MST-ORD-03` |
| C11 | `test_two_threads_on_a_dropped_connection_make_one_replacement` | `tests/test_graph_postgres_reconnect.py` | PASS | none (kernel store; cites `C11 (S244, DL-249 D4)`) |

**Tests added beyond the plan:** `tests/test_ehlo_budget.py::test_a_spent_budget_exits_the_process_non_zero`
(`MST-FAIL-06`: a real interpreter, fake sender, exits non-zero and its last stderr line is the named
error); `agents/master/tests/test_activation_replay_store.py` — `test_a_refusal_is_never_remembered`,
`test_a_waiter_on_a_failed_first_attempt_mints_its_own`, `test_another_type_is_refused_while_the_first_is_in_flight`,
`test_a_replayed_answer_is_a_copy` (`MST-IDM-03`); `test_ehlo_budgets.py::test_the_replay_never_outlives_a_credential_pass_or_a_cached_secret`
(`MST-IDM-03`/`MST-NEV-06`); `test_ehlo_server.py::test_the_listen_backlog_is_the_tunable`,
`test_a_server_that_cannot_bind_releases_its_socket`; `test_ehlo_server_routes.py::test_the_server_answers_health_and_refuses_the_rest`,
`test_serve_builds_its_server_from_master_settings` (`MST-ORD-03`/`MST-IDM-03`; `serve()` is no longer
`# pragma: no cover`). Changed: `tests/test_bootstrap.py` senders take the new `timeout` argument;
`test_master_entrypoint.py::test_build_app_accepts_custom_settings` sets `handshake_timeout_2_seconds`
(the field it used left `MasterSettings`); the `MST-IDM-01` docstring names the two boot ids.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** the claude.ai cloud container's clone, branch `claude/loving-gates-f8vfsd`
(the session forced this name; the spec's `sprint-244-…` branch was not created), cut from `main`
`8cef3ac`; **no `.env`**, no `gh`, no Azure, no route to `download.pytorch.org`. Python 3.13.12, Linux.

**Result:** an agent resends a transient EHLO failure with one boot id inside a 6-attempt / 300 s
budget and exits loud when it is spent; master replays a repeated boot id (same signed ACTIVATE, no
write, no test), refuses it to another type with a 422, and serves EHLOs on a threading server with a
64-deep backlog — a 15-agent wave with 0.5 s activations took **1.37–1.46 s** on loopback (serial:
8.34–8.48 s). Master laws v1.7 (24 / 50), DRIFT-091, DL-249. Unit- and loopback-proven only: no live proof.

**Files changed:** kernel — `bootstrap.py`, `graph_postgres.py`, new `ehlo_retry.py`, `ehlo_settings.py`;
master — `http_server.py`, `settings.py`, `entrypoint.py` (one argument), `credential_test.py`,
`key_vault.py`, new `activation_replay.py`; tests — new `tests/test_ehlo_retry.py`,
`tests/test_ehlo_budget.py`, `tests/ehlo_fakes.py`, `agents/master/tests/test_activation_replay.py`,
`test_activation_replay_store.py`, `test_ehlo_budgets.py`, `test_ehlo_server.py`,
`test_ehlo_server_routes.py`, `ehlo_server_support.py`; edited `tests/test_bootstrap.py`,
`tests/test_graph_postgres_reconnect.py`, `agents/master/tests/test_master_entrypoint.py`,
`test_master_agent.py` (docstring); laws — master `laws.md` + `test-plan.md` v1.7,
`docs/laws/ledger.md`, `docs/laws/INDEX.md`, `docs/laws/drift-register.md` (DRIFT-091); docs —
`docs/design-log.md` (DL-249), this spec, `docs/sprints/README.md`. `agents/master/agent.py` untouched.
`uv.lock` and `pyproject.toml` untouched (no version bump: PATCH at merge).

**Design decisions:** [DL-249](../design-log.md) — D1 envelope (30 s / 6 / 300 s / 1 s ×2 cap 30 s, full
jitter; the planner's starting point kept), D2 transient classification (status first), D3 replay
store (boot id with a type check, signed answer, in-flight guard, lifetime capped by the credential
TTLs), D4 thread safety, D5 module placement; each with its rejected alternatives in DL-249.

**Proof — the red run first** (the four planted tests against `main` `8cef3ac` before any
implementation; they cannot import because nothing they test exists — the behavioural reds of the
same guarantees are plants 1, 3, 4, 5 and 6 below, each of which restores the pre-S244 behaviour):

```text
$ uv run --frozen pytest tests/test_ehlo_retry.py agents/master/tests/test_activation_replay.py agents/master/tests/test_ehlo_server.py -q --no-cov
tests/test_ehlo_retry.py:21: in <module>
    from kernel.ehlo_retry import EhloBudgetExhaustedError, RetryHooks
E   ModuleNotFoundError: No module named 'kernel.ehlo_retry'
agents/master/tests/test_activation_replay.py:16: in <module>
    from agents.master.activation_replay import ActivationReplay
E   ModuleNotFoundError: No module named 'agents.master.activation_replay'
agents/master/tests/test_ehlo_server.py:20: in <module>
    from agents.master.activation_replay import ActivationReplay
E   ModuleNotFoundError: No module named 'agents.master.activation_replay'
ERROR tests/test_ehlo_retry.py
ERROR agents/master/tests/test_activation_replay.py
ERROR agents/master/tests/test_ehlo_server.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
3 errors in 0.44s
```

(C1 then lived in `tests/test_ehlo_retry.py`; C4 moved to `tests/test_ehlo_budget.py` when the file
crossed 200 lines.)

**Proof — the green run:**

```text
$ uv run --frozen pytest <the S244 files> -v -s --no-cov
tests/test_ehlo_retry.py::test_a_timed_out_ehlo_is_resent_with_one_boot_id PASSED
tests/test_ehlo_retry.py::test_each_transient_failure_is_resent[...] PASSED   (10 cases)
tests/test_ehlo_retry.py::test_a_final_answer_is_never_resent[...] PASSED     (7 cases)
tests/test_ehlo_retry.py::test_a_bad_signature_is_never_resent PASSED
tests/test_ehlo_budget.py::test_a_spent_attempt_budget_ends_loud PASSED
tests/test_ehlo_budget.py::test_the_budget_stops_resends_before_the_attempt_cap PASSED
tests/test_ehlo_budget.py::test_a_spent_budget_exits_the_process_non_zero PASSED
agents/master/tests/test_activation_replay.py::test_a_repeated_boot_id_is_one_activation PASSED
agents/master/tests/test_activation_replay.py::test_a_boot_id_cannot_fetch_another_types_credentials PASSED
agents/master/tests/test_activation_replay.py::test_the_replay_window_expires PASSED
agents/master/tests/test_activation_replay.py::test_concurrent_resends_of_one_boot_id_are_one_activation PASSED
agents/master/tests/test_activation_replay_store.py::test_a_refusal_is_never_remembered PASSED
agents/master/tests/test_activation_replay_store.py::test_a_waiter_on_a_failed_first_attempt_mints_its_own PASSED
agents/master/tests/test_activation_replay_store.py::test_another_type_is_refused_while_the_first_is_in_flight PASSED
agents/master/tests/test_activation_replay_store.py::test_a_replayed_answer_is_a_copy PASSED
agents/master/tests/test_ehlo_budgets.py::test_the_kernel_budget_fits_inside_the_replay_window PASSED
agents/master/tests/test_ehlo_budgets.py::test_the_listen_backlog_holds_one_wave PASSED
agents/master/tests/test_ehlo_budgets.py::test_the_replay_never_outlives_a_credential_pass_or_a_cached_secret PASSED
agents/master/tests/test_ehlo_server.py::test_an_activation_wave_is_served_in_parallel C8 wave: 15 activations in 1.43s
PASSED
agents/master/tests/test_ehlo_server.py::test_the_listen_backlog_is_the_tunable PASSED
agents/master/tests/test_ehlo_server.py::test_a_server_that_cannot_bind_releases_its_socket PASSED
agents/master/tests/test_ehlo_server_routes.py::test_the_server_answers_health_and_refuses_the_rest PASSED
agents/master/tests/test_ehlo_server_routes.py::test_serve_builds_its_server_from_master_settings PASSED
tests/test_graph_postgres_reconnect.py::test_two_threads_on_a_dropped_connection_make_one_replacement PASSED
============================== 39 passed in 3.56s ==============================
```

**Guards planted** (DL-70; each plant applied to the working tree, its test run with
`PYTHONDONTWRITEBYTECODE=1`, the file restored from a copy and its SHA-256 compared: all six
`restored: yes`):

1. **max attempts 1** (`kernel/ehlo_settings.py` default 6 → 1) → C1 red:
   `E   kernel.ehlo_retry.EhloBudgetExhaustedError: EHLO to http://master:8000/ehlo failed after 1 attempt(s) in 30.0s; last cause: TimeoutError: timed out` — `1 failed`.
2. **422 treated as transient** (`_TRANSIENT_STATUSES` gains 422) → C3 red:
   `E   Failed: DID NOT RAISE HTTPError` — `FAILED …test_a_final_answer_is_never_resent[<HTTPError 422: 'status'>]`, `1 failed, 2 passed`.
3. **a new boot id per attempt** (`bootstrap.py` wraps the sender to mint `uuid4()` per send) → C1 red:
   `E   AssertionError: assert 3 == 1` / `where 3 = len({'46c0e1f4…', 'c2788443…', 'c8c8938f…'})` — `1 failed`.
4. **replay removed** (`handle_ehlo`: `if replay is None:` → `if True:`) → C5 red:
   `E   AssertionError: assert {'instance_id…} == {'instance_id…}` / `Differing items: {'signature': …}, {'instance_id': 'scanner:…:1'} != …:0` — `1 failed`.
5. **replay keyed on boot id alone** (the type check → `if False:`) → C6 red: `E   assert 200 == 422` — `1 failed`.
6. **`TCPServer` restored** (`EhloServer` base → `socketserver.TCPServer`) → C8 red:
   `C8 wave: 15 activations in 8.48s` / `E   AssertionError: assert 8.480150721999962 < ((15 * 0.5) / 2)` — `1 failed in 9.49s`.

🪤 **A first pass of plants 2 and 3 went red for the wrong reason** and was discarded: plant 1's
same-size edit (`6` → `1`) was restored inside the same second, so Python's mtime/size `.pyc` check
kept serving the planted bytecode (`failed after 1 attempt(s)` in plants 2 and 3). All `__pycache__`
directories were deleted and the six re-run with bytecode writing off; the reds above are that run.

**Module line counts** (every file touched; all < 200): `kernel/bootstrap.py` 125, `kernel/ehlo_retry.py`
140, `kernel/ehlo_settings.py` 60, `kernel/graph_postgres.py` **155** (warn; was 147),
`agents/master/http_server.py` 143, `activation_replay.py` 114, `settings.py` 139, `entrypoint.py` 195
(unchanged), `agent.py` 182 (untouched), `credential_test.py` **157** (warn; was 149), `key_vault.py` 144;
tests: `tests/test_ehlo_retry.py` 123, `tests/test_ehlo_budget.py` 108, `tests/ehlo_fakes.py` 71,
`tests/test_bootstrap.py` 179, `tests/test_graph_postgres_reconnect.py` 130,
`agents/master/tests/test_activation_replay.py` 182, `test_activation_replay_store.py` 94,
`test_ehlo_budgets.py` 54, `test_ehlo_server.py` 115, `test_ehlo_server_routes.py` 62,
`ehlo_server_support.py` 70, `test_master_entrypoint.py` 146, `test_master_agent.py` 197 (unchanged).

**`make ci`:** `UV_FROZEN=1 make ci > ci.txt 2>&1; echo exit=$?` (the session's scratchpad
`ci.txt`, not committed) → **exit 0**, all 15 steps: ruff, format (1,485 files), mypy (1,118 files, no
issues), import-linter (5 kept, 0 broken), module size (warnings only), module header, law coverage,
PARAM sync (two pre-existing PM envelope warnings), sprint status, markdown links, version scheme,
pytest **3,687 passed, 8 skipped**, coverage **100.00 %** (19,755 statements, 4,208 branches, 0 missed),
dependency audit (no unaccepted vulnerabilities; 1 accepted advisory re-checked, PYSEC-2026-2447),
detect-secrets Passed, untracked secrets Passed (12 new files scanned). Linux only; Windows `make ci`
owed.

**`make gate-ran`:** owed to the planner.

**Planner verification (2026-09-29):** code reviewed against the spec: classification is by status
first; one body goes out on every attempt; the replay checks the type before it returns anything and
never remembers a failed mint; `MasterAgent`'s only per-activation mutable state is the already-locked
instance counter; the graph store runs autocommit single statements with no transactions, so sharing
the connection is safe. PATCH bump `0.119.02` → `0.119.03`. `uv lock` changed only the package's own version line
(`Updated trading-agents v0.119.2 -> v0.119.3`, 180 packages resolved). Windows `make ci` in worktree
`trading-agents-s244`, redirected to a file: **exit 0**, 3,687 passed, 8 skipped, 100.00 %,
dependency audit and detect-secrets passed. Committed on `sprint-244-every-agent-activates-on-a-busy-or-sleeping-master`
(the conventional name) above the builder's `e2b7b68`.

**Not met / verified failing:** nothing in the spec's build list is unmet. **Not done (owed, by
design):** `uv lock` with the PATCH bump (`uv.lock` untouched, `UV_FROZEN=1` throughout), Windows
`make ci`, `make gate-ran`, the retag, F1, F2. No live proof of any kind was run.

---

## Return notes

- **Scope held.** Everything in Scope 1–4 was built; nothing out of scope was touched (no KEDA,
  `minReplicas`, credential-test pack, remediation, grants, contract, label, property, env key or
  pool). One addition beyond the spec's list: `MST-IDM-01` was amended (law reading record: read
  literally, it contradicted the new `MST-IDM-03`).
- **Branch.** The session forced `claude/loving-gates-f8vfsd`; the spec's
  `sprint-244-every-agent-activates-on-a-busy-or-sleeping-master` was not created. Rename on merge if
  the convention needs it.
- **Disagreed with, after reading the laws.** (1) The planner's replay expiry = the window alone
  would let a replay re-deliver a credential longer than its pass or its cached secret is trusted if
  an operator shortens either TTL; the lifetime is `min(window, pass TTL, secret TTL)` over non-zero
  TTLs (DL-249 D3). All three default to 300 s, so nothing changes at the defaults. (2) The spec's
  `handshake_timeout_1_seconds` 10 s was not reused as the per-attempt timeout (DL-249 D1 (d)).
  (3) `MST-SEC-01` is cited by the bad-signature test but its row stays ⬜: its text still describes the
  S73 stub and the S74 wiring, and the test proves only the agent-side "verify before accepting" half.
  (4) The `CAP` block's `channel: handshake_queue` is stale (DRIFT-091, left for the next amendment).
- **C8's measured wall time for the 15-agent wave:** **1.37–1.46 s** over five runs (0.5 s per
  activation; the rest is RSA-PSS sign/verify, ~45–70 ms per activation measured alone). With
  `TCPServer` restored: **8.34–8.48 s**. The shared psycopg connection was not in the loop (C8 uses
  the in-memory graph), so the wave on Neon is F2's to measure; nothing here asks for a pool.
- **Thread safety, per shared object** (DL-249 D4): `ActivationReplay` — locked + a per-entry event
  (in-flight guard); `PassCache` — locked (map only; a raced duplicate costly probe accepted as waste);
  `CachingSecretStore` — locked (map only; a raced duplicate Key Vault fetch accepted); graph
  `_run` reconnect — locked + identity check (C11: one replacement); instance counter — already locked;
  psycopg connection — accepted, psycopg 3 serialises a connection; `CollectingFaultSink` — accepted,
  `list.append` is atomic and the preflight thread already shares it; `InMemoryGraphStore` — accepted,
  `MASTER_GRAPH=memory` dev mode only; Azure `SecretClient` — accepted, the SDK documents clients as
  thread-safe; credential-probe transports — accepted, a fresh `urllib` request per call.
- **Env and deploy.** Every new tunable is defaulted and no env key must be set; the kernel's
  `EhloSettings` has no prefix (`EHLO_MAX_ATTEMPTS`, …) should the operator ever want one. Removing
  `handshake_timeout_1_seconds` / `handshake_max_retries` from `MasterSettings` is harmless if a stray
  `MASTER_HANDSHAKE_*` is set (`extra="ignore"`); none is in `infra/`. Image-only retag, as specced.
- **A master restart inside a boot's budget** still mints one extra `AgentInstance` for that boot
  (the replay is in memory), as the spec's road-not-taken already names.
- **`docs/STATE.md` was not edited** — the planner owns the live tracker and it moved on `main` during
  this session (`3e97e61`).
- **Owed to the planner:** `uv lock` (PATCH bump), `make gate-ran` from the branch's HEAD, Windows
  `make ci`, retag, F1 (retag against a cold master: 0 EHLO tracebacks, retry lines, one
  `AgentInstance` per container start), F2 (the next 22:30 wave inside ~60 s).
