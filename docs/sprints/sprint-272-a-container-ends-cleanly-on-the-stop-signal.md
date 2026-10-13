<!-- Agent: planning | Role: sprint handover -->
# Sprint 272 — a container told to stop ends by itself: it finishes the work in hand, closes what it holds, says so and exits 0

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-272-a-container-ends-cleanly-on-the-stop-signal`
**Status:** MERGED 2026-10-14 — `0.125.09`, fast-forwarded to `497293b8`, tag `v0.125.09`, GATE PROVEN `497293b8` (CI, CodeQL, Security Findings); F1 passed at no cost; not deployed (an image-only retag, on the operator's word); F2 owed on the fleet
**Version:** `0.125.09` (PATCH; `uv lock` updated the project only)
**Effort:** M
**Decisions:** [DL-297](../design-log.md) (this sprint's nine decisions, made and measured) · [DL-283](../design-log.md) decision 5 (the shutdown path, before the container sensor) · [work-queue 116](../work-queue.md) · DRIFT-113 (three master clauses name a recovery path no code holds)

> **Why a PATCH.** Nothing new is offered to a caller. The platform already tells every container
> to stop, and every container ignores it and is killed: a defect in how the process ends.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 4 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/master/laws/laws.md` | The master's **locked constitution**, v1.9 | **This sprint amends it to v1.10**, with exactly the text in the appendix. No other clause changes |
| `agents/master/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Rows added and changed as *Law cycle* below says |
| `agents/{curator,operator,researcher,supervisor,deliberator}/laws/laws.md` | Five agents whose entrypoint gains two arguments | **LOCKED. Read only.** No clause of theirs changes |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | `ledger.md` and `INDEX.md`: the master's row. `drift-register.md`: one new row, DRIFT-113 |

Binding sections here: the master's **`TRG`**, **`OUT`**, **`STA`**, **`IDM`**, **`ORD`**, **`OBS`**
and **`PARAM`**; the deliberator's **`DLIB-IDM-04`**, **`DLIB-DEP-02`** and **`DLIB-PERF-02`** (the
debater's serve call keeps its poll interval of 0 and its graph fault sink).

### The rule

1. **Before writing code**, read `agents/master/laws/laws.md` and its `test-plan.md`, whole.
2. Read the `TRG` section of the curator's, operator's, researcher's, supervisor's and
   deliberator's `laws.md`: each of their entrypoints changes by two arguments.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Write the Law reading record** (bottom of this file) **before** your first change.
5. **If a law contradicts this spec, STOP and report.**
6. Every test for behaviour a clause governs cites the clause ID in its docstring. The clause for
   each planned test is in the *Test plan* table.

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Yes: a guarantee.** No file under `contracts/` changes. Every container gains the guarantee that
it ends by itself on the stop signal. The cycle is owed and is in scope (*Law cycle* below).

🪤 **The rollup is derived, not declared.** `make ci` recomputes it. On the planner's prototype the
master reads **30 / 55** (it is 26 / 52): three new clauses, all proven, and `MST-OUT-03` turning
green. Let the gate tell you the number.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `kernel/stop.py` (new), `kernel/work_loop.py`, `kernel/serve_loop.py` | the master's `laws.md` + `test-plan.md` | new `MST-TRG-03` and `MST-OBS-05`. The kernel has no book of its own; a container's lifecycle is lawed in the master's, as `MST-FAIL-06` already is for an agent's activation budget |
| `kernel/graph_guarded.py`, `kernel/bus_azure_receiver.py` | same | `MST-TRG-03`: what a stopped loop closes |
| `agents/master/http_server.py`, `draining_server.py` (new), `stopping.py` (new), `fleet_preflight_loop.py`, `entrypoint.py` | same | new `MST-ORD-04`; `MST-ORD-03` (a thread per request, the listen backlog) must hold unchanged; `MST-OUT-04` (a crashed fleet check does not end the schedule) must hold unchanged |
| `agents/master/store.py`, `stopping.py` | same | `MST-OUT-03` amended; `MST-STA-01` reworded |
| `agents/master/settings.py` | same, `PARAM` | new row `stop_drain_seconds`; the parameter step of `make ci` compares default and bounds with the code |
| `agents/deliberator/entrypoint.py` | the deliberator's `laws.md` | `DLIB-IDM-04`, `DLIB-DEP-02`, `DLIB-PERF-02`: the existing test that cites them is edited in its fake's signature and two assertions, nothing else |
| `agents/{curator,operator,researcher,supervisor}/entrypoint.py` | each agent's `laws.md`, `TRG` | the serve call gains `graph=` and `agent=`; nothing else on the line changes |

⚠️ **The one invariant this sprint must not break: no decision path changes.** The fidelity count
is running ([DL-237](../design-log.md)), and `scripts/replay_fidelity_git.py` reads these as
decision paths: `agents/scanner/`, `agents/analyst/`, `agents/portfolio_manager/`,
`agents/provider/domain/`, `agents/execution/order_tolerance.py`, `contracts/`,
`orchestration/packs/trading_tunables.json`, `orchestration/packs/trading_issuer_map.json` and
`orchestration/history_window.py`. **The three agents' folders are whole: their `entrypoint.py`,
their `Dockerfile`, their law books and their tests are inside.** Those three containers get the
stop through `kernel/work_loop.py`, which they already call with the graph and their name. If the
build seems to need a change under any of those paths, **stop and report**.

---

## Goal

When the platform tells a container to stop, the process ends by itself inside the grace: it takes
no new work, finishes the item or request in hand, closes what it holds, writes one line saying so
and exits 0. This holds for all 16 containers: the nine that run the graph-pull loop, the six that
run the serve loop, and the master, which also lets the activations in hand finish and records the
end of its session in the graph.

## Why (context)

No process in the fleet handles the stop signal. Each image starts Python as its command, so
Python is process 1 of the container, and Linux does not deliver a signal to process 1 unless it
has installed a handler. The platform waits its grace of 30 seconds and kills the process. Nothing
is closed, nothing is logged, and the master's `Session` never gets the `ended_at` its law names as
the mark of a stop that was not a crash. The container sensor ([work-queue 119](../work-queue.md))
is built after this: it alarms on a kill, and today every stop of the master is one.

### Measured, 2026-10-13 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| The master killed at a stop, 30 days | **54** times, exit code 137, the last 2026-10-11 13:14 UTC (the `s270` retag) | *[measured 2026-10-13]* the platform's event log (`ContainerAppSystemLogs_CL`), read-only |
| A clean exit on record, any app, 30 days | **none**: 1,597 `Stopping container` lines over the 16 apps, and no exit with code 0 | *[measured 2026-10-13]* same query. An ordinary scale-down leaves no exit line, so how an agent ends at night is not in that log |
| Python as process 1 with no handler ignores `SIGTERM` | ignored for the whole 6.1 s watched, then killed | *[measured 2026-10-13]* Linux 5.15, Python 3.12 as process 1 of its own PID namespace, the idle `time.sleep` the loops use today (`pid1_probe.sh`) |
| The same process on the prototype's `kernel/stop.py` | its two lines, exit 0, 0.2 s after the signal | *[measured 2026-10-13]* same script, same position |
| Five process shapes on `main` (`b048d251`) | each ended by the signal's default action: no line, nothing closed, an item cut in the middle, the master's session not ended | *[measured 2026-10-13]* `wq116_stop_paths.py`: child processes, a real `SIGTERM` raised inside each, no network |
| The same five on the prototype | idle graph-pull agent and idle served agent: flushed, closed, exit 0. Three 1 s items: the one in hand finished, the third left pending, exit 0. A graph that refuses to close: exit 1, the error's type named and not its text. The master: `ended_at` and `shutdown_reason: SIGTERM` on its `Session`, exit 0 | *[measured 2026-10-13]* same script. The lines are in the appendix as printed |
| Containers and entrypoint files | 16 containers, 14 entrypoint files (the deliberator's one file runs as three apps) | *[read 2026-10-13]* `$AGENTS` in `infra/deploy-agents.ps1` and each `entrypoint.py` |
| Which loop each runs | graph-pull, 9: scanner, analyst, portfolio-manager, deliberator-manager, execution, monitor, reporter, forecaster, provider. Serve, 6: deliberator-proponent, deliberator-opponent, operator, supervisor, curator, researcher. The master: its own server | *[read 2026-10-13]* every `work_loop(` and `serve_loop(` call under `agents/` |
| What each loop call already hands over | all 9 graph-pull calls pass `graph=` and `agent=`; none of the 5 serve calls does | *[read 2026-10-13]* the same calls |
| The fidelity count's decision paths | the list in the invariant above; `kernel/` is not on it | *[read 2026-10-13]* `DECISION_PATHS` in `scripts/replay_fidelity_git.py` |
| The graph refuses to overwrite a property | `write_session` writes `shutdown_reason: ""` at start, so the end could never be written | *[read 2026-10-13]* `_append_props` in `kernel/graph_support.py` and the merge statement; planted on the prototype (break M08 goes red) |
| The vocabulary and `Session` | the label is declared, with no property list and no owner: `ended_at` needs no pack change | *[read 2026-10-13]* `orchestration/packs/trading_graph_vocabulary.json` |
| The fleet's graph is the guarded store | it has no `close`, so a loop could not close the connection through it | *[read 2026-10-13]* `kernel/graph_env.py`, `kernel/graph_guarded.py` |
| The longest idle wait a loop makes before it looks at the stop | 1 s (the sliced sleep), 5 s (a Service Bus receive), 0.5 s (the master's accept) | *[read 2026-10-13]* `receive_timeout_seconds` defaults to 5.0; the other two are this sprint's constants |
| The platform stops a container with `SIGTERM` to process 1 | *[ASSUMED — not measured]* | The 54 kills at 31 or 32 seconds and the Linux measurement agree with it. Settled by F2, on the fleet |
| What the platform logs for an exit with code 0 | *[ASSUMED — not measured]* nothing is known | It has never had one to log. Settled by F2 |

---

## Scope — and what is deliberately NOT here

1. **`kernel/stop.py`, new.** A `StopSignal` (a flag set once, with the reason and the time; a
   `wait` that sleeps in one-second slices and returns when the flag is set), `install` (routes
   `SIGTERM` to it, on the main thread only; the handler writes one unbuffered line),
   `closing_steps`, `finish` (runs every closing step on its own and writes the closing line) and
   `end_loop` (exit 1 when a step failed).
2. **`kernel/work_loop.py`.** `run_once` starts no further item once told to stop. `work_loop`
   takes an optional `stop`; with no pass limit and no stop handed in it installs the handler
   itself; its idle sleep is the stop's `wait` unless a `sleep` is injected; when it ends on a stop
   it flushes its faults, closes the graph and writes the closing line. A loop that ends by its
   pass limit behaves as today.
3. **`kernel/serve_loop.py`.** `serve_loop` loses its "blocks forever" exemption from coverage,
   takes `graph`, `agent` and `stop`, serves until told to stop, then flushes the sink it was
   given, closes its consumer and the graph and writes the line. `serve_once` does not change: a
   request already taken is answered.
4. **What the loops close.** `GuardedGraphStore.close()` reaches the store it wraps.
   `AzureServiceBusRequestConsumer.close()` closes its receiver and its client.
5. **Five serve calls gain `graph=` and `agent=`**: the curator's, the operator's, the
   researcher's, the supervisor's and the debaters' (`serve_peer`).
6. **The master.** `serve()` accepts in a loop until told to stop, closes its listening socket,
   waits for the activations in hand until `stop_drain_seconds` have passed since the signal and
   returns how many it left. `agents/master/draining_server.py` (new) counts requests in and out.
   `agents/master/stopping.py` (new) waits for a fleet check in hand, writes `ended_at` and
   `shutdown_reason` on the `Session`, closes the graph, writes the line and returns the exit
   code. The fleet check's schedule sleeps on the stop and starts no check after it. `main()`
   installs the handler first, hands the one stop to the schedule and to the server, and exits
   with what `shut_down` returns.
7. **`write_session` writes `started_at` alone.**
8. **Law cycle** (below), and DRIFT-113.

**The production change is given whole in the appendix, as a diff measured on the planner's
prototype.** Build it as given. If you find it wrong, stop and report: do not repair it quietly.
The tests are yours to write, from the *Test plan*.

### Law cycle — owed, in scope

- `agents/master/laws/laws.md` to **v1.10**: the text is in the appendix's diff (status line, new
  `MST-TRG-03`, `MST-ORD-04`, `MST-OBS-05`; `MST-OUT-03` amended; `MST-STA-01`, `MST-TRG-02`,
  `MST-IDM-02` reworded; `PARAM` row `stop_drain_seconds`; Changelog line).
- `agents/master/laws/test-plan.md`: status line to v1.10; a 🟩 row each for `MST-TRG-03`,
  `MST-ORD-04` and `MST-OBS-05`, placed **inside the table** (after the `MST-TRG-02`,
  `MST-ORD-03` and `MST-OBS-04` rows; the file ends with a sentence after the table, and a row
  appended after it is not read); the `MST-OUT-03` row turns 🟩 with your tests; the descriptions
  of the `MST-TRG-02` and `MST-IDM-02` rows follow their new wording and stay ⬜.
- `docs/laws/ledger.md` and `docs/laws/INDEX.md`: the master's row reads v1.10 and the count the
  gate derives. 🪤 The law gate checks the counts and not the version label: read both rows.
- `docs/laws/drift-register.md`: **DRIFT-113**, corrected by this sprint. *Law says:* on the next
  boot the master reads its `Session` nodes, infers a crash from a missing `ended_at`, enters a
  recovery mode and may trigger a drain (`MST-STA-01`, `MST-IDM-02`, `MST-TRG-02`). *Code says:*
  nothing reads a `Session` at boot and nothing calls `drain` at start (read 2026-10-13: no
  module under `agents/master/` reads `ended_at`; before this sprint none wrote it either).
  *Decision:* the three clauses are reworded to what the code does; the recovery path is not
  built.

### Out of scope (do NOT build this sprint)

- **Anything under a decision path** (the invariant above).
- **A stop that arrives before the loop starts.** While a container imports, and while an agent
  activates, no handler is installed; such a container is killed after the grace, as today.
- **A longer stop grace on the apps.** `infra/deploy-agents.ps1` does not change. Work in hand
  that outlasts 30 seconds is still killed, and the handler's line is then the last in its log.
- **An agent's end recorded in the graph.** Only the master has a `Session`.
- **A recovery path at boot.** The three clauses are reworded, nothing is built.
- **Closing the debate manager's reply receivers, the model clients or the DSPy engine.**
- **`kernel/startup.py`**: a master halted on an unreachable graph is still killed at a stop.
- **The dispatcher job and `scripts/`**: a job runs to its end; it has no loop to stop.
- **The container sensor** (work-queue 119).
- **No ADR reversal.**

### The road not taken (LAW-06)

Recorded with their reasons in [DL-297](../design-log.md), *Ruled out*: an exception raised in the
main thread on the signal; a first line in every entrypoint or a launcher as the image's command;
installing at import or inside `activate_agent`; an init process in the images; a longer grace
instead of a handler; `serve_forever` on a second thread, and non-daemon request threads joined at
close; a deadline after which the process exits by itself; each agent recording its own end in the
graph; the `logging` module for the two lines.

---

## The design decisions — made, and recorded in DL-297

The nine decisions (D1 to D9) are in [DL-297](../design-log.md) with what was ruled out. They are
made: do not re-open them in the build. If one cannot be built as decided, stop and report.

---

## Blast radius — measured 2026-10-13

| What | Detail |
| --- | --- |
| Files changed, production | New: `kernel/stop.py` (165 lines), `agents/master/draining_server.py` (51), `agents/master/stopping.py` (68). Changed: `kernel/work_loop.py` (153 → 186), `kernel/serve_loop.py` (104 → 129), `kernel/graph_guarded.py` (81 → 87), `kernel/bus_azure_receiver.py` (160 → 170), `agents/master/http_server.py` (143 → 163), `agents/master/fleet_preflight_loop.py` (64 → 81), `agents/master/entrypoint.py` (156 → 173), `agents/master/settings.py` (144 → 157), `agents/master/store.py` (194, one line), and the five entrypoints named in Scope 5 |
| Files changed, law and docs | the master's `laws.md` and `test-plan.md`; `docs/laws/ledger.md`, `INDEX.md`, `drift-register.md`; this file; `docs/sprints/README.md` (this sprint's row) |
| Existing tests edited | exactly two, each in the lines named in the *Test plan* (E1, E2). No other existing test changes |
| Agents affected | all 16 containers, through the kernel; none imports another |
| Contract change? | no |
| Decision path? | **none changes**: the scope command in the handback checklist prints nothing |
| Graph vocabulary change? | no: `Session` is declared with no property list |
| New env keys / tunables | `stop_drain_seconds` on the master (`MASTER_STOP_DRAIN_SECONDS`), default 20.0. No env key is set anywhere: the default is the value |
| Deploy implication | image-only retag |
| Rollback | retag to the tag before. It undoes everything: no pack, no env key, no migration. A `Session` written by the new image keeps its `ended_at`; an older image writes `shutdown_reason: ""` at start again and reads neither |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Write the two headline tests first** (A1 and A2 in the *Test plan*) and watch them fail on
   the unchanged tree. Paste the red output. 🪤 On the unchanged tree a real `SIGTERM` ends the
   test process itself: run A2 in a child process, or expect pytest to die, and say which.
3. **Apply the appendix's diff**, then the two existing-test edits (E1, E2).
4. **Write the rest of the tests** from the *Test plan*.
5. **Law cycle.**
6. **Prove the guards can fail (DL-70)**: break the built code, watch a test go red, restore.
   State each break in the Closeout.
7. **`make ci` green**, every step, **redirected to a file, never piped**.
8. **Fill the handback sections** at the bottom of this file and set **Status:** `BUILT`.

---

## Test plan

Every new test file stays under 200 lines (the size step reads `tests/` too): the planner's own
needed eight files. A test that installs the handler puts the process's previous `SIGTERM` handler
back when it ends. A real signal is raised with `signal.raise_signal(signal.SIGTERM)` from a
`threading.Timer`, which works on Windows and Linux alike.

| # | Test | Plants | Must prove | Clause |
| --- | --- | --- | --- | --- |
| A1 | 🎯 the master's process, told to stop, ends by itself | a child Python process runs the real `agents.master.entrypoint.main()` with `MASTER_GRAPH=memory`, serving on a loopback port; a timer raises `SIGTERM` inside it once it serves. **The child gets a stripped environment** (`PATH`, `SYSTEMROOT`, `TEMP`, `TMP`, `HOME`, `PYTHONPATH` = the repository root, `MASTER_GRAPH`, `PYTHONUTF8=1`) **and a temporary working directory**, so it can read no `.env` and no pack. A daemon timer in the child ends it with code 99 after 60 s, so a master that does not stop leaves no process behind | exit code 0; its `Session` holds `ended_at` later than `started_at` and `shutdown_reason` `SIGTERM`; stderr holds the signal line and ends with the closing line | `MST-ORD-04`, `MST-OUT-03`, `MST-OBS-05` |
| A2 | 🎯 a graph-pull loop with no stop handed in listens for `SIGTERM` | `work_loop` with no pass limit, nothing pending, a 60 s poll, a graph that counts its closes; the signal 0.2 s later | the call returns; the graph was closed once; stderr holds both lines, the last ending `closed graph; exit 0` | `MST-TRG-03` |
| A3 | a serve loop with no stop handed in listens for `SIGTERM` | `serve_loop` on an empty local inbox, a 60 s poll, `agent="operator"` | returns 0 served; both lines, named `[operator]` | `MST-TRG-03` |
| A4 | a pass starts no item after the stop | three pending items; the stop is asked for while the second is processed | the third is still pending; found 3, attempted 2, advanced 2 | `MST-TRG-03` |
| A5 | a stopped graph-pull loop flushes, closes and says so | a handed-in stop asked for during the first item; an injected `sleep` that records; `flush_faults` that records | one pass; no sleep; faults flushed once; graph closed once; the closing line, exactly | `MST-TRG-03`, `MST-OBS-05` |
| A6 | 🪤 a loop that ends by its pass limit closes nothing | `max_iterations=2`, no stop, no injected sleep, a tiny poll interval | two passes; graph not closed; faults flushed once (as today); nothing on stderr | `MST-TRG-03` |
| A7 | 🪤 a graph that will not close is exit 1 | a graph whose `close` raises `ConnectionError` with a marker word in its text | `SystemExit` with code 1; the line names `ConnectionError`; the marker word is not in it | `MST-TRG-03`, `MST-OBS-05` |
| A8 | a request taken as the stop arrives is still answered | an inbox with one request that asks for the stop on its first poll; a sink with `flush`; a consumer and a graph that count their closes | 1 served; the reply holds the answer; one poll; the line reads `closed faults, requests, graph; exit 0` | `MST-TRG-03` |
| A9 | an idle serve loop polls again until the stop | the stop asked for on the third poll, poll interval 0 | 3 polls, 1 served, consumer closed once | `MST-TRG-03` |
| A10 | the flag | a fake clock | the first request's reason and time are kept; `seconds_left` counts from the signal and stops at 0; a 30 s `wait` ends within seconds when the stop is asked for from a timer; a wait with no stop lasts its time; a negative wait returns at once | `MST-TRG-03`, `MST-ORD-04` |
| A11 | the handler | `install` with an injected writer, then with none (read descriptor 2), then from a second thread | the flag is set, the reason is `SIGTERM`, the line is exact; with no writer the line is on descriptor 2; 🪤 off the main thread nothing is installed and `install` returns `False` | `MST-TRG-03`, `MST-OBS-05` |
| A12 | the closing line | steps that pass, a step that raises with a marker word in its text, work left, no steps | every step runs although one raised; the exact line in each case (the appendix prints them); `end_loop` raises `SystemExit(1)` only when a step failed | `MST-TRG-03`, `MST-OBS-05` |
| A13 | the guarded graph closes the store it wraps | a store with `close`, and one without | closed once; no error for the one without | `MST-TRG-03` |
| A14 | the Service Bus consumer closes its receiver and its client | an injected receiver and client that record `close` | both closed, receiver first; a second `close` does nothing; a later `poll` still answers | `MST-TRG-03` |
| A15 | every agent entrypoint hands its loop the graph and its name | the source of each `agents/*/entrypoint.py` but the master's, read as a syntax tree | 13 files, 14 loop calls (the deliberator has two); every call has `graph` and `agent` keywords. **Read the three frozen files; do not edit them** | `MST-TRG-03` |
| A16 | the master's server ends on the stop | `serve()` on a second thread with a handed-in stop, its server captured through `build_server` | it answers `/health`; after the stop it returns 0 and its socket is closed | `MST-ORD-04` |
| A17 | an activation in hand is answered | a master whose activation takes 0.5 s; the stop 0.2 s into it | the caller gets 200; `serve()` returns 0; one `AgentInstance` | `MST-ORD-04` |
| A18 | 🪤 an activation longer than the drain is reported | `stop_drain_seconds=0`, an activation of 1 s | `serve()` returns 1 | `MST-ORD-04` |
| A19 | the master's server with no stop handed in listens for `SIGTERM` | `serve()` on the main thread, the signal from a timer | returns 0; the signal line names `[master]` | `MST-TRG-03`, `MST-ORD-04` |
| A20 | 🪤 a request whose thread cannot start is counted out | `threading.Thread.start` made to raise | the error propagates; `drain(0)` returns 0 | `MST-ORD-04` |
| A21 | a session starts with its start time alone | `write_session` on an empty graph | the node's properties are `started_at` and nothing else | `MST-OUT-03` |
| A22 | a stopped master ends its session | `shut_down` with nothing left, a finished fleet-check thread, a graph that counts its closes | `ended_at` later than `started_at`; `shutdown_reason` `SIGTERM`; graph closed once; returns 0; the line, exactly | `MST-OUT-03`, `MST-ORD-04`, `MST-OBS-05` |
| A23 | 🪤 work left is named and the session is still ended | 2 activations left, a fleet-check thread still alive, `stop_drain_seconds=0` | returns 1; `ended_at` is written; the line reads `left 2 activation(s), the fleet check; closed session, graph; exit 1` | `MST-ORD-04`, `MST-OUT-03` |
| A24 | 🪤 a session end that cannot be written | a graph that refuses the write | returns 1; the graph is still closed; the line names the step and `ConnectionError` | `MST-ORD-04`, `MST-OBS-05` |
| A25 | a master that never opened a session ends none | `shut_down` on an agent with no `start()` | returns 0; no `Session` node; `nothing to close` | `MST-OUT-03` |
| A26 | a session is ended once | `end_session` twice with different reasons | the second raises (`cannot be overwritten`) | `MST-OUT-03` |
| A27 | the fleet check's schedule ends on the stop | the loop with a `run_once` that asks for the stop; the daemon with a handed-in stop | one check, then none; the thread is alive before the stop and ends within seconds after it | `MST-ORD-04` |
| E1 | **existing, edited:** `tests/test_deliberator_cold_peer_timing.py::test_served_peer_uses_receive_wait_without_extra_idle_sleep` | its fake `serve_loop` takes two more keyword arguments, `graph` and `agent` | two added assertions: the graph is the one handed in, the name is `deliberator-proponent`. Every existing assertion stays | `DLIB-IDM-04`, `DLIB-DEP-02`, `DLIB-PERF-02` |
| E2 | **existing, edited:** `agents/master/tests/test_ehlo_server_routes.py::test_serve_builds_its_server_from_master_settings` | `serve()` no longer calls `serve_forever`, so the server is captured through `build_server` and `serve()` is handed a stop already asked for | its three assertions stay as they are (backlog 32, replay lifetime 120.0, socket closed) | `MST-ORD-03`, `MST-IDM-03` |

---

## Success factors

- [x] The appendix's diff is applied as given: `git hash-object` of each of the 17 production
      files equals the planner's (the planner compares at review; you paste yours).
- [x] A1 and A2 failed on the unchanged tree and pass on the built one.
- [x] Exactly two existing tests are edited, E1 and E2, in the lines named.
- [x] **No decision path changes**: the scope command prints nothing.
- [x] Law cycle done: master v1.10 in four files, DRIFT-113 filed as corrected, every cited test
      exists under the name the row gives.
- [x] Every new guard planted, watched to fail, restored, stated per guard.
- [x] Every touched module under 200 lines; every new test file under 200 lines.
- [x] `make ci` exit 0, sixteen steps, 100.00 % coverage, with no `# pragma: no cover` added
      anywhere but on a line that already carried one.

---

## Traps

🪤 **A real `SIGTERM` in a test that has not installed a handler ends pytest.** On the unchanged
tree that is every test that raises it. Install first, raise second, and restore the previous
handler in a fixture's teardown.

🪤 **A fake clock handed to `StopSignal` must not be used to time `wait`.** `wait` reads the real
monotonic clock; the injected one only times the stop for the closing line.

🪤 **The master's child process must not inherit the test process's environment.** The root
`conftest.py` loads `.env` into it, and in the main checkout that holds the live graph's DSN and
the packs' paths: a child master would connect, and its fleet check would run real probes. A1
gives the child a stripped environment and a temporary working directory.

🪤 **A master that does not stop is a process that never ends.** Met on the planner's own breaks:
with the stop not handed to the server, A1's child served on after pytest was gone (on Windows the
environment's `python.exe` starts a second process, and ending the first leaves the second). The
child therefore ends itself after 60 seconds.

🪤 **Read the child's output as UTF-8, and tell the child to write it so.** The master's own log
lines hold a dash outside ASCII. `make ci` exports `PYTHONUTF8=1`, a bare `pytest` on Windows does
not: the planner's A1 passed alone and failed in the gate, where the parent read the child's
Windows-encoded bytes as UTF-8 and got no text at all. Give the child `PYTHONUTF8=1` and read with
`encoding="utf-8", errors="replace"`.

🪤 **`serve()` blocks on the calling thread until the stop.** A test that calls it on the main
thread hands it a stop already asked for, or raises the signal from a timer; a test that needs the
server's port captures the server through `build_server` and runs `serve()` on a second thread.

🪤 **Do not write a URL that carries a user name and a password to stand for a secret, in a test
or in a document.** The secrets scan reads that shape as a credential. The planner's first full run
failed on its own test, and the remote scan then failed on this page, where the shape was quoted
as the example ([DL-298](../design-log.md)). Use a marker word in the error's text and assert the
line does not hold it.

🪤 **The two existing fakes have exact signatures.** `fake_serve_loop` in E1 names its keyword
arguments, so the two new ones must be added to it; the execution and forecaster entrypoint tests
have the same shape for `work_loop`, and they must **not** need a change, because no graph-pull
call changes.

🪤 **`test-plan.md` ends with a sentence after its table.** A row appended at the end of the file
is outside the table and the law step reports its clause as missing.

🪤 **Do not add a `# pragma: no cover` to reach 100 %.** `serve_loop` loses the one it had.
`main()` in the master's entrypoint keeps the one it has.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
  `kernel/stop.py` imports the standard library only.
- Every module under 200 lines (warn at 150). 📌 On the prototype: `kernel/work_loop.py` **186**,
  `agents/master/store.py` **194**, `agents/master/entrypoint.py` **173**,
  `kernel/bus_azure_receiver.py` **170**, `kernel/stop.py` **165**, `agents/master/http_server.py`
  **163**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: `stop_drain_seconds` is a `tunable` with bounds and a `PARAM` row. The two
  constants (the one-second slice, the half-second accept wait) are how often a loop looks, not
  values an operator tunes.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- Version bump: PATCH, `uv.lock` staged with it.
- Secrets never through the worktree. The worktree has **no `.env`**; nothing in this sprint needs
  one. **State which tree you ran in.**

---

## Sequencing after merge (the planner's)

1. Review against the checklist; re-measure: the scope command; the 17 blob ids against
   `prototype_blobs.txt`; the planner's own tests copied beside the builder's under other names;
   `break_s272.py` on the built tree; each cited test resolved by hand; the master's row in
   `docs/laws/INDEX.md` and `ledger.md`. Merge `main` in first.
2. `make ci` on the merged tree, branch pushed, **`make gate-ran` exits 0** from the worktree.
   CodeQL set-diff against the last merged branch.
3. Merge to `main` and push; tag the version.
4. **F1, at no cost, before any deploy.** On merged `main`: `wq116_stop_paths.py` prints what
   `after_prototype.txt` holds, case for case; `pid1_probe.sh` on Linux, on `main`'s
   `kernel/stop.py`, ends with exit 0 and no kill.
5. **Deploy: an image-only retag, on the operator's word.** 🪤 The first stop after the retag is
   of the *old* image and is still a kill. No decision path differs, so the fidelity count stands.
6. **F2, on the fleet, at no cost.** After the retag each app starts a replica of the new image
   and the scaler stops it some minutes later. Read for each of the 16 apps: its console log holds
   the signal line and a closing line ending `exit 0`; the platform's event log holds no exit code
   137 for a revision of the new tag; the master's newest `Session` that has ended holds
   `ended_at` and `shutdown_reason` `SIGTERM`. Then the same read after the first nightly window's
   end. Record what the platform logs for a clean exit: it is not known today.

---

## Handover — paste this to Codex

```text
You are building Sprint 272 in the worktree ../ta-s272, on the branch
sprint-272-a-container-ends-cleanly-on-the-stop-signal. Never touch main.

Read first, whole: docs/sprints/sprint-272-a-container-ends-cleanly-on-the-stop-signal.md.
It is the specification. Then, before any code: agents/master/laws/laws.md and test-plan.md,
the TRG section of the curator's, operator's, researcher's, supervisor's and deliberator's
laws.md, docs/laws/conventions.md and docs/laws/drift-register.md. Fill the spec's
"Law reading record" before your first change.

What the sprint makes true: a container told to stop (SIGTERM) ends by itself. It takes no new
work, finishes the item or request in hand, closes what it holds, writes one line and exits 0.

How:
1. Write tests A1 and A2 of the Test plan first and watch them fail on the unchanged tree.
   A real SIGTERM ends a process that has no handler, so run A2's red proof in a child process.
2. The production change is given whole, as a diff, in the spec's appendix. Save the fenced block
   to a file and apply it from the worktree root with: git apply --unidiff-zero <file>
   Build it as given. If you believe it is wrong, STOP and report; do not repair it quietly.
3. Edit exactly two existing tests, E1 and E2 of the Test plan, in the lines named there.
4. Write the rest of the tests from the Test plan. Each test file stays under 200 lines.
   Every test cites its clause ID in its docstring.
5. Law cycle: the master's laws.md is in the diff. You add the test-plan rows (inside the
   table, not after the file's last sentence), the master's row in docs/laws/ledger.md and
   docs/laws/INDEX.md (v1.10, the count the gate derives), and DRIFT-113 in
   docs/laws/drift-register.md, as the spec words it.
6. Break the built code to prove each guard can fail, restore, and state each break.
7. Version bump: PATCH (the next free one), uv.lock staged with it.
8. make ci > a file 2>&1, never through a pipe. All sixteen steps, exit 0, 100.00 % coverage.
9. Fill the handback sections of the spec, set Status: BUILT, change this sprint's row in
   docs/sprints/README.md to lead with BUILT, commit on the branch. Do not push, do not merge.

DO NOT:
- change any file under agents/scanner/, agents/analyst/, agents/portfolio_manager/,
  agents/provider/domain/, contracts/, or agents/execution/order_tolerance.py,
  orchestration/packs/trading_tunables.json, orchestration/packs/trading_issuer_map.json,
  orchestration/history_window.py. The scope command in the handback checklist must print
  nothing. Test A15 READS three of those entrypoints; it does not edit them.
- change any existing test other than E1 and E2.
- add a "# pragma: no cover" anywhere.
- edit infra/, a Dockerfile, a pack, docs/STATE.md, docs/work-queue.md or docs/design-log.md.
- let the master's child process in A1 inherit your environment: give it the stripped one the
  Test plan names and a temporary working directory.

Traps written in the spec, read them: a signal with no handler ends pytest; restore the previous
SIGTERM handler after every test that installs one; a fake clock does not time wait();
serve() blocks until the stop; test-plan.md ends with a sentence after its table.

If a law contradicts the spec, or the diff does not apply, or a step of make ci cannot be made
green without leaving the scope: STOP and report what you found. An incomplete handback is
returned, not repaired.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`, here and in this sprint's row of `docs/sprints/README.md`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

**Handback checklist** (paste each command's output into the Closeout):

```bash
git diff --name-only main -- agents/scanner agents/analyst agents/portfolio_manager \
  agents/provider/domain agents/execution/order_tolerance.py contracts \
  orchestration/packs/trading_tunables.json orchestration/packs/trading_issuer_map.json \
  orchestration/history_window.py          # the scope command: prints nothing
git diff --stat main                       # every file you changed
git hash-object kernel/stop.py kernel/work_loop.py kernel/serve_loop.py kernel/graph_guarded.py \
  kernel/bus_azure_receiver.py agents/curator/entrypoint.py agents/operator/entrypoint.py \
  agents/researcher/entrypoint.py agents/supervisor/entrypoint.py agents/deliberator/entrypoint.py \
  agents/master/draining_server.py agents/master/http_server.py agents/master/fleet_preflight_loop.py \
  agents/master/stopping.py agents/master/store.py agents/master/settings.py agents/master/entrypoint.py
git grep -n "pragma: no cover" -- kernel/stop.py kernel/serve_loop.py kernel/work_loop.py \
  agents/master/stopping.py agents/master/draining_server.py agents/master/http_server.py   # prints nothing
```

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| Kernel stop, graph-pull/serve loops and resource closure | `agents/master/laws/laws.md` and `test-plan.md`, whole | New `MST-TRG-03`, `MST-OBS-05`; `MST-OUT-03` | Yes: prove real SIGTERM in isolated children first; restore any handler installed in pytest; keep bounded-pass behavior unchanged. |
| Master HTTP drain, schedule, entrypoint and session end | Same master books, whole | `MST-ORD-03`, new `MST-ORD-04`, `MST-OUT-03/04`, `MST-STA-01`, `MST-TRG-02`, `MST-IDM-02`, `PARAM` | Yes: one deadline measured from the signal; session end remains attempted when work or a closing step fails; only the appendix changes production. |
| Curator, operator, researcher and supervisor serve entrypoints | Each named agent's `laws.md`, `TRG` section | `CUR-TRG-01..03`, `OPR-TRG-01..03`, `RES-TRG-01..03`, `SUP-TRG-01..06` | No new capability trigger: only pass the existing graph and identity to the serving loop. Their locked books remain unchanged. |
| Deliberator serve entrypoint and E1 | `agents/deliberator/laws/laws.md`, `TRG`, `IDM`, `DEP`, `PERF` sections | `DLIB-TRG-01..03`, `DLIB-IDM-04`, `DLIB-DEP-02`, `DLIB-PERF-02` | Preserve poll interval 0, graph fault sink and all existing assertions; add only the two keyword arguments and assertions specified by E1. |
| Law cycle and drift evidence | `docs/laws/INDEX.md`, `conventions.md` and `drift-register.md`, whole | Conventions sections 2-4, 7, 7a, 9-10; authorized DRIFT-113 | Keep stable clause IDs, put rows inside the table, cite tests by their final names, and derive rollups with the gate. |

Read and recorded on 2026-10-13 before any code change, in `C:/Users/yury_/Downloads/project/ta-s272`, branch `sprint-272-a-container-ends-cleanly-on-the-stop-signal`. Initial tree clean; `HEAD` and `origin/main` both `fcb52ba9a8125f5b6880b36d8149aac89375b420`; no `.env` in this worktree. The excluded decision paths, trackers, packs, images and infrastructure remain outside the build. No push or merge is authorized.

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** Yes, a new container shutdown guarantee; no contract change. The master amendment is explicitly authorized in the appendix. Test-plan, both rollups and DRIFT-113 are owed in this unit of work.

**Contradictions found between a law and this spec:** The existing master recovery claims (`MST-STA-01`, `MST-IDM-02`, `MST-TRG-02`) are the already-decided DRIFT-113 named by this spec and amended by its appendix. No additional contradiction found in the required reading.

**Laws found silent where a decision was needed:** v1.9 has no stop-signal, bounded master drain or closing-line guarantee. The spec settles those questions with new `MST-TRG-03`, `MST-ORD-04`, `MST-OBS-05` and the amended `MST-OUT-03`; no design decision is reopened.

**Clauses that were ⬜ and are now proven:** At closeout, `MST-OUT-03` and the new `MST-TRG-03`, `MST-ORD-04`, `MST-OBS-05` are proven; gate-derived master rollup 30 / 55. The three recovery-path clauses receive exactly the authorized wording; `MST-TRG-02` and `MST-IDM-02` stay ⬜.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a1_master_process_ends_cleanly_on_sigterm` | `agents/master/tests/test_stop_process.py` | PASS | MST-ORD-04, MST-OUT-03, MST-OBS-05 |
| A2 | `test_a2_graph_pull_process_listens_for_sigterm`; `test_a2_unbounded_loop_installs_in_the_main_process` | `tests/test_work_stop_signal.py` | PASS | MST-TRG-03 |
| A3 | `test_a3_idle_serve_loop_listens_for_sigterm` | `tests/test_serve_stop.py` | PASS | MST-TRG-03 |
| A4 | `test_a4_a_pass_starts_no_item_after_stop` | `tests/test_work_stop.py` | PASS | MST-TRG-03 |
| A5 | `test_a5_stopped_loop_flushes_closes_without_sleep` | `tests/test_work_stop.py` | PASS | MST-TRG-03, MST-OBS-05 |
| A6 | `test_a6_pass_limit_installs_nothing_and_closes_nothing` | `tests/test_work_stop.py` | PASS | MST-TRG-03 |
| A7 | `test_a7_graph_close_failure_exits_one_without_error_text` | `tests/test_work_stop.py` | PASS | MST-TRG-03, MST-OBS-05 |
| A8 | `test_a8_taken_request_is_answered_before_closure` | `tests/test_serve_stop.py` | PASS | MST-TRG-03 |
| A9 | `test_a9_idle_loop_polls_again_until_the_stop` | `tests/test_serve_stop.py` | PASS | MST-TRG-03 |
| A10 | `test_a10_first_stop_keeps_its_reason_and_time`; `test_a10_wait_uses_real_time_and_wakes_on_stop` | `tests/test_stop_signal.py` | PASS | MST-TRG-03, MST-ORD-04 |
| A11 | `test_a11_handler_sets_the_flag_and_writes_exactly`; `test_a11_default_writer_uses_descriptor_two`; `test_a11_second_thread_installs_nothing` | `tests/test_stop_signal.py` | PASS | MST-TRG-03, MST-OBS-05 |
| A12 | `test_a12_each_closing_step_runs_and_the_line_is_exact`; `test_a12_no_steps_and_end_loop_exit_codes`; `test_a12_steps_name_only_held_closable_resources` | `tests/test_stop_closing.py` | PASS | MST-TRG-03, MST-OBS-05 |
| A13 | `test_a13_guarded_graph_closes_its_wrapped_store` | `tests/test_stop_resources.py` | PASS | MST-TRG-03 |
| A14 | `test_a14_consumer_closes_receiver_then_client_and_can_poll_again` | `tests/test_stop_resources.py` | PASS | MST-TRG-03 |
| A15 | `test_a15_every_entrypoint_passes_graph_and_agent` | `tests/test_stop_entrypoints.py` | PASS | MST-TRG-03 |
| A16 | `test_a16_server_answers_health_then_stops` | `agents/master/tests/test_stop_server.py` | PASS | MST-ORD-04 |
| A17 | `test_a17_activation_in_hand_is_answered` | `agents/master/tests/test_stop_server.py` | PASS | MST-ORD-04 |
| A18 | `test_a18_activation_outlasting_the_drain_is_reported` | `agents/master/tests/test_stop_server.py` | PASS | MST-ORD-04 |
| A19 | `test_a19_server_installs_its_own_sigterm_handler` | `agents/master/tests/test_stop_server.py` | PASS | MST-TRG-03, MST-ORD-04 |
| A20 | `test_a20_failed_request_thread_is_counted_out` | `agents/master/tests/test_stop_server.py` | PASS | MST-ORD-04 |
| A21 | `test_a21_session_starts_with_start_time_alone` | `agents/master/tests/test_stop_session.py` | PASS | MST-OUT-03 |
| A22 | `test_a22_stopped_master_ends_session_then_closes_graph` | `agents/master/tests/test_stop_session.py` | PASS | MST-OUT-03, MST-ORD-04, MST-OBS-05 |
| A23 | `test_a23_work_left_is_named_and_session_still_ends` | `agents/master/tests/test_stop_session.py` | PASS | MST-ORD-04, MST-OUT-03 |
| A24 | `test_a24_failed_session_write_still_closes_graph` | `agents/master/tests/test_stop_session.py` | PASS | MST-ORD-04, MST-OBS-05 |
| A25 | `test_a25_master_without_start_ends_no_session` | `agents/master/tests/test_stop_session.py` | PASS | MST-OUT-03 |
| A26 | `test_a26_session_end_cannot_be_overwritten` | `agents/master/tests/test_stop_session.py` | PASS | MST-OUT-03 |
| A27 | `test_a27_schedule_runs_no_check_after_stop`; `test_a27_daemon_wakes_from_schedule_wait_on_stop` | `agents/master/tests/test_stop_preflight.py` | PASS | MST-ORD-04 |
| E1 | `test_served_peer_uses_receive_wait_without_extra_idle_sleep` | `tests/test_deliberator_cold_peer_timing.py` | PASS | DLIB-IDM-04, DLIB-DEP-02, DLIB-PERF-02 |
| E2 | `test_serve_builds_its_server_from_master_settings` | `agents/master/tests/test_ehlo_server_routes.py` | PASS | MST-ORD-03, MST-IDM-03 |

**Tests added beyond the plan:** The in-process companion to A2 exercises the same handler path inside coverage; A1/A2's original red proofs remain child-process tests. Two additional `MST-ORD-04` tests prove that the server drain and the fleet-check join receive only the signal budget's 13 remaining seconds: `agents/master/tests/test_stop_deadline.py::test_server_drain_budget_counts_from_the_signal`; `agents/master/tests/test_stop_deadline.py::test_fleet_check_uses_the_same_remaining_budget`.

---

## Closeout — evidence

**Status:** BUILT — local proof complete; prepared for branch commit, no push or merge.

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/Downloads/project/ta-s272`, branch `sprint-272-a-container-ends-cleanly-on-the-stop-signal`; no `.env`. A1/A2 children use stripped environments and temporary working directories; the master child has its own 60 s watchdog.

**Result:** The prescribed production diff is built unchanged: real SIGTERM ends the master and graph-pull processes with exit 0, taken work completes, shutdown evidence and resource closure are tested, and failures/unfinished work are exit 1. A1/A2 red first, 41 focused cases green, 74 planted breaks red/restored, full sixteen-step CI exit 0 at 100.00% coverage. Local container-loop proof only; remote, Linux PID-1 and fleet proof remain owed.

**Files changed:** 17 production files; master laws/test-plan and three umbrella law files; twelve new test files and exactly E1/E2 among existing tests; this spec and its README row; `pyproject.toml` and `uv.lock`. Exact files and counts are in the diff stat below.

**Proof — the red run first:** A1 and A2 ran in child processes on unchanged production. Each child exited 3 under Windows default SIGTERM; pytest survived and exited 1. Command: `uv run pytest --no-cov agents/master/tests/test_stop_process.py tests/test_work_stop_signal.py`.

```text
============================= test session starts =============================
collected 2 items

agents\master\tests\test_stop_process.py F                               [ 50%]
tests\test_work_stop_signal.py F                                         [100%]

================================== FAILURES ===================================
_______________ test_a1_master_process_ends_cleanly_on_sigterm ________________
agents\master\tests\test_stop_process.py:72: in test_a1_master_process_ends_cleanly_on_sigterm
    assert child.returncode == 0, (child.returncode, child.stdout, child.stderr)
E   AssertionError: (3, '', '[master] no MASTER_PRIVATE_KEY_PEM — generated dev keypair
E     [master] MASTER_PUBLIC_KEY_PEM=-----BEGIN PUBLIC ...graph store: memory
E     [master] graph reachable
E     [master] session=session:20261013T104649:09cb8449 — serving on :8000
E     ')
E   assert 3 == 0
E    +  where 3 = CompletedProcess(args=['C:\\Users\\yury_\\Downloads\\project\\ta-s272\\.venv\\Scripts\\python.exe', '-c', "\nimport js...graph store: memory\n[master] graph reachable\n[master] session=session:20261013T104649:09cb8449 — serving on :8000\n').returncode
_______________ test_a2_graph_pull_process_listens_for_sigterm ________________
tests\test_work_stop_signal.py:57: in test_a2_graph_pull_process_listens_for_sigterm
    assert child.returncode == 0, (child.returncode, child.stdout, child.stderr)
E   AssertionError: (3, '', '')
E   assert 3 == 0
E    +  where 3 = CompletedProcess(args=['C:\\Users\\yury_\\Downloads\\project\\ta-s272\\.venv\\Scripts\\python.exe', '-c', "\nimport os...aph=graph, poll_interval=60)\nprint('closes=' + str(graph.closes), flush=True)\n"], returncode=3, stdout='', stderr='').returncode
=========================== short test summary info ===========================
FAILED agents/master/tests/test_stop_process.py::test_a1_master_process_ends_cleanly_on_sigterm
FAILED tests/test_work_stop_signal.py::test_a2_graph_pull_process_listens_for_sigterm
============================== 2 failed in 5.41s ==============================
```

**Proof — the green run:** `uv run pytest --no-cov <the twelve new test files> tests/test_deliberator_cold_peer_timing.py agents/master/tests/test_ehlo_server_routes.py`, restored production:

```text
============================= test session starts =============================
collected 41 items

agents\master\tests\test_stop_process.py .                               [  2%]
agents\master\tests\test_stop_server.py .....                            [ 14%]
agents\master\tests\test_stop_session.py ......                          [ 29%]
agents\master\tests\test_stop_preflight.py ..                            [ 34%]
agents\master\tests\test_stop_deadline.py ..                             [ 39%]
tests\test_work_stop_signal.py ..                                        [ 43%]
tests\test_work_stop.py ....                                             [ 53%]
tests\test_stop_signal.py .....                                          [ 65%]
tests\test_stop_closing.py .....                                         [ 78%]
tests\test_stop_resources.py ..                                          [ 82%]
tests\test_stop_entrypoints.py .                                         [ 85%]
tests\test_serve_stop.py ...                                             [ 92%]
tests\test_deliberator_cold_peer_timing.py .                             [ 95%]
agents\master\tests\test_ehlo_server_routes.py ..                        [100%]

============================= 41 passed in 15.49s =============================
```

**Guards planted:** Each plant ran its named pytest target in a separate child, then restored the original bytes and invalidated only that module's bytecode. All 74 were red; no survivor. M29/M50 terminated the child pytest process via Windows default SIGTERM (exit 3); other plants were pytest failures (exit 1). M71's master self-watchdog ended it at 60 s; no orphan was left. Each break and target:

| Plant | Built file | Break | Test target | Result |
| --- | --- | --- | --- | --- |
| M01 | `kernel/stop.py` | overwrite first stop reason/time | `tests/test_stop_signal.py::test_a10_first_stop_keeps_its_reason_and_time` | RED, exit 1; restored |
| M02 | `kernel/stop.py` | lose signal timestamp | `tests/test_stop_signal.py::test_a10_first_stop_keeps_its_reason_and_time` | RED, exit 1; restored |
| M03 | `kernel/stop.py` | lose requested flag | `tests/test_stop_signal.py::test_a10_first_stop_keeps_its_reason_and_time` | RED, exit 1; restored |
| M04 | `kernel/stop.py` | count elapsed time before a request | `tests/test_stop_signal.py::test_a10_first_stop_keeps_its_reason_and_time` | RED, exit 1; restored |
| M05 | `kernel/stop.py` | allow negative remaining drain | `tests/test_stop_signal.py::test_a10_first_stop_keeps_its_reason_and_time` | RED, exit 1; restored |
| M06 | `kernel/stop.py` | return from every idle wait immediately | `tests/test_stop_signal.py::test_a10_wait_uses_real_time_and_wakes_on_stop` | RED, exit 1; restored |
| M07 | `kernel/stop.py` | remove one-second signal wake slices | `tests/test_stop_signal.py::test_a11_handler_sets_the_flag_and_writes_exactly` | RED, exit 1; restored |
| M08 | `kernel/stop.py` | try installing from a worker thread | `tests/test_stop_signal.py::test_a11_second_thread_installs_nothing` | RED, exit 1; restored |
| M09 | `kernel/stop.py` | handler keeps the wrong signal reason | `tests/test_stop_signal.py::test_a11_handler_sets_the_flag_and_writes_exactly` | RED, exit 1; restored |
| M10 | `kernel/stop.py` | signal line goes to stdout | `tests/test_stop_signal.py::test_a11_default_writer_uses_descriptor_two` | RED, exit 1; restored |
| M11 | `kernel/stop.py` | signal line loses the promised words | `tests/test_stop_signal.py::test_a11_handler_sets_the_flag_and_writes_exactly` | RED, exit 1; restored |
| M12 | `kernel/stop.py` | skip later cleanup after a failed step | `tests/test_stop_closing.py::test_a12_each_closing_step_runs_and_the_line_is_exact` | RED, exit 1; restored |
| M13 | `kernel/stop.py` | leak error text in closing line | `tests/test_stop_closing.py::test_a12_each_closing_step_runs_and_the_line_is_exact` | RED, exit 1; restored |
| M14 | `kernel/stop.py` | ignore unfinished work in exit status | `tests/test_stop_closing.py::test_a12_each_closing_step_runs_and_the_line_is_exact` | RED, exit 1; restored |
| M15 | `kernel/stop.py` | ignore failed cleanup in exit status | `tests/test_stop_closing.py::test_a12_each_closing_step_runs_and_the_line_is_exact` | RED, exit 1; restored |
| M16 | `kernel/stop.py` | omit fault flushing from closing steps | `tests/test_stop_closing.py::test_a12_steps_name_only_held_closable_resources` | RED, exit 1; restored |
| M17 | `kernel/stop.py` | omit graph from closing steps | `tests/test_stop_closing.py::test_a12_steps_name_only_held_closable_resources` | RED, exit 1; restored |
| M18 | `kernel/stop.py` | reverse end_loop success/failure guard | `tests/test_stop_closing.py::test_a12_no_steps_and_end_loop_exit_codes` | RED, exit 1; restored |
| M19 | `kernel/stop.py` | print exit 0 for failed cleanup | `tests/test_stop_closing.py::test_a12_each_closing_step_runs_and_the_line_is_exact` | RED, exit 1; restored |
| M20 | `kernel/work_loop.py` | start items after stop | `tests/test_work_stop.py::test_a4_a_pass_starts_no_item_after_stop` | RED, exit 1; restored |
| M21 | `kernel/work_loop.py` | report unattempted items as attempted | `tests/test_work_stop.py::test_a4_a_pass_starts_no_item_after_stop` | RED, exit 1; restored |
| M22 | `kernel/work_loop.py` | unbounded work loop installs no handler | `tests/test_work_stop_signal.py::test_a2_graph_pull_process_listens_for_sigterm` | RED, exit 1; restored |
| M23 | `kernel/work_loop.py` | bounded work loop changes the process handler | `tests/test_work_stop.py::test_a6_pass_limit_installs_nothing_and_closes_nothing` | RED, exit 1; restored |
| M24 | `kernel/work_loop.py` | work loop disregards stop between passes | `tests/test_work_stop.py::test_a5_stopped_loop_flushes_closes_without_sleep` | RED, exit 1; restored |
| M25 | `kernel/work_loop.py` | ignore injected work-loop sleep | `tests/test_work_loop.py::test_work_loop_sleeps_after_empty_pass` | RED, exit 1; restored |
| M26 | `kernel/work_loop.py` | stopped work loop skips closure | `tests/test_work_stop.py::test_a5_stopped_loop_flushes_closes_without_sleep` | RED, exit 1; restored |
| M27 | `kernel/work_loop.py` | stopped work loop omits faults | `tests/test_work_stop.py::test_a5_stopped_loop_flushes_closes_without_sleep` | RED, exit 1; restored |
| M28 | `kernel/work_loop.py` | bounded loop skips its existing final flush | `tests/test_work_stop.py::test_a6_pass_limit_installs_nothing_and_closes_nothing` | RED, exit 1; restored |
| M29 | `kernel/serve_loop.py` | serve loop installs no handler | `tests/test_serve_stop.py::test_a3_idle_serve_loop_listens_for_sigterm` | RED, exit 3; restored |
| M30 | `kernel/serve_loop.py` | reverse serve-loop stop guard | `tests/test_serve_stop.py::test_a8_taken_request_is_answered_before_closure` | RED, exit 1; restored |
| M31 | `kernel/serve_loop.py` | lose the count of a taken/answered request | `tests/test_serve_stop.py::test_a8_taken_request_is_answered_before_closure` | RED, exit 1; restored |
| M32 | `kernel/serve_loop.py` | discard served agent identity | `tests/test_serve_stop.py::test_a3_idle_serve_loop_listens_for_sigterm` | RED, exit 1; restored |
| M33 | `kernel/serve_loop.py` | serve loop omits fault flushing | `tests/test_serve_stop.py::test_a8_taken_request_is_answered_before_closure` | RED, exit 1; restored |
| M34 | `kernel/serve_loop.py` | serve loop omits consumer close | `tests/test_serve_stop.py::test_a8_taken_request_is_answered_before_closure` | RED, exit 1; restored |
| M35 | `kernel/serve_loop.py` | serve loop omits graph close | `tests/test_serve_stop.py::test_a8_taken_request_is_answered_before_closure` | RED, exit 1; restored |
| M36 | `kernel/graph_guarded.py` | guarded graph does not delegate close | `tests/test_stop_resources.py::test_a13_guarded_graph_closes_its_wrapped_store` | RED, exit 1; restored |
| M37 | `kernel/bus_azure_receiver.py` | consumer skips client close | `tests/test_stop_resources.py::test_a14_consumer_closes_receiver_then_client_and_can_poll_again` | RED, exit 1; restored |
| M38 | `kernel/bus_azure_receiver.py` | consumer retains closed receiver | `tests/test_stop_resources.py::test_a14_consumer_closes_receiver_then_client_and_can_poll_again` | RED, exit 1; restored |
| M39 | `kernel/bus_azure_receiver.py` | consumer retains closed client | `tests/test_stop_resources.py::test_a14_consumer_closes_receiver_then_client_and_can_poll_again` | RED, exit 1; restored |
| M40 | `agents/curator/entrypoint.py` | curator omits graph keyword | `tests/test_stop_entrypoints.py::test_a15_every_entrypoint_passes_graph_and_agent` | RED, exit 1; restored |
| M41 | `agents/curator/entrypoint.py` | curator omits agent keyword | `tests/test_stop_entrypoints.py::test_a15_every_entrypoint_passes_graph_and_agent` | RED, exit 1; restored |
| M42 | `agents/operator/entrypoint.py` | operator omits graph keyword | `tests/test_stop_entrypoints.py::test_a15_every_entrypoint_passes_graph_and_agent` | RED, exit 1; restored |
| M43 | `agents/operator/entrypoint.py` | operator omits agent keyword | `tests/test_stop_entrypoints.py::test_a15_every_entrypoint_passes_graph_and_agent` | RED, exit 1; restored |
| M44 | `agents/researcher/entrypoint.py` | researcher omits graph keyword | `tests/test_stop_entrypoints.py::test_a15_every_entrypoint_passes_graph_and_agent` | RED, exit 1; restored |
| M45 | `agents/researcher/entrypoint.py` | researcher omits agent keyword | `tests/test_stop_entrypoints.py::test_a15_every_entrypoint_passes_graph_and_agent` | RED, exit 1; restored |
| M46 | `agents/supervisor/entrypoint.py` | supervisor omits graph keyword | `tests/test_stop_entrypoints.py::test_a15_every_entrypoint_passes_graph_and_agent` | RED, exit 1; restored |
| M47 | `agents/supervisor/entrypoint.py` | supervisor omits agent keyword | `tests/test_stop_entrypoints.py::test_a15_every_entrypoint_passes_graph_and_agent` | RED, exit 1; restored |
| M48 | `agents/deliberator/entrypoint.py` | deliberator omits graph keyword | `tests/test_stop_entrypoints.py::test_a15_every_entrypoint_passes_graph_and_agent` | RED, exit 1; restored |
| M49 | `agents/deliberator/entrypoint.py` | deliberator omits agent keyword | `tests/test_stop_entrypoints.py::test_a15_every_entrypoint_passes_graph_and_agent` | RED, exit 1; restored |
| M50 | `agents/master/http_server.py` | master server installs no handler | `agents/master/tests/test_stop_server.py::test_a19_server_installs_its_own_sigterm_handler` | RED, exit 3; restored |
| M51 | `agents/master/http_server.py` | reverse master server stop guard | `agents/master/tests/test_stop_server.py::test_a16_server_answers_health_then_stops` | RED, exit 1; restored |
| M52 | `agents/master/http_server.py` | master does not close listening socket | `agents/master/tests/test_stop_server.py::test_a16_server_answers_health_then_stops` | RED, exit 1; restored |
| M53 | `agents/master/http_server.py` | server drain starts a fresh budget | `agents/master/tests/test_stop_deadline.py::test_server_drain_budget_counts_from_the_signal` | RED, exit 1; restored |
| M54 | `agents/master/draining_server.py` | do not count a request in before thread start | `agents/master/tests/test_stop_server.py::test_a18_activation_outlasting_the_drain_is_reported` | RED, exit 1; restored |
| M55 | `agents/master/draining_server.py` | failed request thread is never counted out | `agents/master/tests/test_stop_server.py::test_a20_failed_request_thread_is_counted_out` | RED, exit 1; restored |
| M56 | `agents/master/draining_server.py` | completed requests are never counted out | `agents/master/tests/test_stop_server.py::test_a16_server_answers_health_then_stops` | RED, exit 1; restored |
| M57 | `agents/master/store.py` | restore empty shutdown_reason at session start | `agents/master/tests/test_stop_session.py::test_a21_session_starts_with_start_time_alone` | RED, exit 1; restored |
| M58 | `agents/master/stopping.py` | session end omits shutdown reason | `agents/master/tests/test_stop_session.py::test_a22_stopped_master_ends_session_then_closes_graph` | RED, exit 1; restored |
| M59 | `agents/master/stopping.py` | session end keeps wrong reason | `agents/master/tests/test_stop_session.py::test_a22_stopped_master_ends_session_then_closes_graph` | RED, exit 1; restored |
| M60 | `agents/master/stopping.py` | unfinished activations are ignored | `agents/master/tests/test_stop_session.py::test_a23_work_left_is_named_and_session_still_ends` | RED, exit 1; restored |
| M61 | `agents/master/stopping.py` | fleet-check join starts a fresh budget | `agents/master/tests/test_stop_deadline.py::test_fleet_check_uses_the_same_remaining_budget` | RED, exit 1; restored |
| M62 | `agents/master/stopping.py` | unfinished fleet check is ignored | `agents/master/tests/test_stop_session.py::test_a23_work_left_is_named_and_session_still_ends` | RED, exit 1; restored |
| M63 | `agents/master/stopping.py` | skip ending an opened session | `agents/master/tests/test_stop_session.py::test_a22_stopped_master_ends_session_then_closes_graph` | RED, exit 1; restored |
| M64 | `agents/master/stopping.py` | master omits graph close | `agents/master/tests/test_stop_session.py::test_a22_stopped_master_ends_session_then_closes_graph` | RED, exit 1; restored |
| M65 | `agents/master/stopping.py` | master exits zero despite unfinished work | `agents/master/tests/test_stop_session.py::test_a23_work_left_is_named_and_session_still_ends` | RED, exit 1; restored |
| M66 | `agents/master/settings.py` | change master drain default | `agents/master/tests/test_stop_deadline.py::test_fleet_check_uses_the_same_remaining_budget` | RED, exit 1; restored |
| M67 | `agents/master/fleet_preflight_loop.py` | start a scheduled check after stop | `agents/master/tests/test_stop_preflight.py::test_a27_schedule_runs_no_check_after_stop` | RED, exit 1; restored |
| M68 | `agents/master/fleet_preflight_loop.py` | daemon idle wait uses a different stop flag | `agents/master/tests/test_stop_preflight.py::test_a27_daemon_wakes_from_schedule_wait_on_stop` | RED, exit 1; restored |
| M69 | `agents/master/fleet_preflight_loop.py` | daemon check guard never sees stop | `agents/master/tests/test_stop_preflight.py::test_a27_daemon_wakes_from_schedule_wait_on_stop` | RED, exit 1; restored |
| M70 | `agents/master/entrypoint.py` | main does not install the early handler | `agents/master/tests/test_stop_process.py::test_a1_master_process_ends_cleanly_on_sigterm` | RED, exit 1; restored |
| M71 | `agents/master/entrypoint.py` | main hands server a different stop flag | `agents/master/tests/test_stop_process.py::test_a1_master_process_ends_cleanly_on_sigterm` | RED, exit 1; restored |
| M72 | `agents/master/entrypoint.py` | main omits shared stop from fleet daemon | `agents/master/tests/test_stop_process.py::test_a1_master_process_ends_cleanly_on_sigterm` | RED, exit 1; restored |
| M73 | `agents/master/entrypoint.py` | main never invokes shutdown | `agents/master/tests/test_stop_process.py::test_a1_master_process_ends_cleanly_on_sigterm` | RED, exit 1; restored |
| M74 | `agents/master/stopping.py` | silently accept a second session end | `agents/master/tests/test_stop_session.py::test_a26_session_end_cannot_be_overwritten` | RED, exit 1; restored |

Actual scratch harness output (`C:/Users/yury_/AppData/Local/Temp/s272-guards.txt`):

```text
Appendix blob identities verified: 17 production files
M01 RED exit=1; restored; overwrite first stop reason/time
M02 RED exit=1; restored; lose signal timestamp
M03 RED exit=1; restored; lose requested flag
M04 RED exit=1; restored; count elapsed time before a request
M05 RED exit=1; restored; allow negative remaining drain
M06 RED exit=1; restored; return from every idle wait immediately
M07 RED exit=1; restored; remove one-second signal wake slices
M08 RED exit=1; restored; try installing from a worker thread
M09 RED exit=1; restored; handler keeps the wrong signal reason
M10 RED exit=1; restored; signal line goes to stdout
M11 RED exit=1; restored; signal line loses the promised words
M12 RED exit=1; restored; skip later cleanup after a failed step
M13 RED exit=1; restored; leak error text in closing line
M14 RED exit=1; restored; ignore unfinished work in exit status
M15 RED exit=1; restored; ignore failed cleanup in exit status
M16 RED exit=1; restored; omit fault flushing from closing steps
M17 RED exit=1; restored; omit graph from closing steps
M18 RED exit=1; restored; reverse end_loop success/failure guard
M19 RED exit=1; restored; print exit 0 for failed cleanup
M20 RED exit=1; restored; start items after stop
M21 RED exit=1; restored; report unattempted items as attempted
M22 RED exit=1; restored; unbounded work loop installs no handler
M23 RED exit=1; restored; bounded work loop changes the process handler
M24 RED exit=1; restored; work loop disregards stop between passes
M25 RED exit=1; restored; ignore injected work-loop sleep
M26 RED exit=1; restored; stopped work loop skips closure
M27 RED exit=1; restored; stopped work loop omits faults
M28 RED exit=1; restored; bounded loop skips its existing final flush
M29 RED exit=3; restored; serve loop installs no handler
M30 RED exit=1; restored; reverse serve-loop stop guard
M31 RED exit=1; restored; lose the count of a taken/answered request
M32 RED exit=1; restored; discard served agent identity
M33 RED exit=1; restored; serve loop omits fault flushing
M34 RED exit=1; restored; serve loop omits consumer close
M35 RED exit=1; restored; serve loop omits graph close
M36 RED exit=1; restored; guarded graph does not delegate close
M37 RED exit=1; restored; consumer skips client close
M38 RED exit=1; restored; consumer retains closed receiver
M39 RED exit=1; restored; consumer retains closed client
M40 RED exit=1; restored; curator omits graph keyword
M41 RED exit=1; restored; curator omits agent keyword
M42 RED exit=1; restored; operator omits graph keyword
M43 RED exit=1; restored; operator omits agent keyword
M44 RED exit=1; restored; researcher omits graph keyword
M45 RED exit=1; restored; researcher omits agent keyword
M46 RED exit=1; restored; supervisor omits graph keyword
M47 RED exit=1; restored; supervisor omits agent keyword
M48 RED exit=1; restored; deliberator omits graph keyword
M49 RED exit=1; restored; deliberator omits agent keyword
M50 RED exit=3; restored; master server installs no handler
M51 RED exit=1; restored; reverse master server stop guard
M52 RED exit=1; restored; master does not close listening socket
M53 RED exit=1; restored; server drain starts a fresh budget
M54 RED exit=1; restored; do not count a request in before thread start
M55 RED exit=1; restored; failed request thread is never counted out
M56 RED exit=1; restored; completed requests are never counted out
M57 RED exit=1; restored; restore empty shutdown_reason at session start
M58 RED exit=1; restored; session end omits shutdown reason
M59 RED exit=1; restored; session end keeps wrong reason
M60 RED exit=1; restored; unfinished activations are ignored
M61 RED exit=1; restored; fleet-check join starts a fresh budget
M62 RED exit=1; restored; unfinished fleet check is ignored
M63 RED exit=1; restored; skip ending an opened session
M64 RED exit=1; restored; master omits graph close
M65 RED exit=1; restored; master exits zero despite unfinished work
M66 RED exit=1; restored; change master drain default
M67 RED exit=1; restored; start a scheduled check after stop
M68 RED exit=1; restored; daemon idle wait uses a different stop flag
M69 RED exit=1; restored; daemon check guard never sees stop
M70 RED exit=1; restored; main does not install the early handler
M71 RED exit=1; restored; main hands server a different stop flag
M72 RED exit=1; restored; main omits shared stop from fleet daemon
M73 RED exit=1; restored; main never invokes shutdown
73 planted breaks, 73 RED, all restored; 17 production blobs unchanged
Appendix blob identities verified: 17 production files
M74 RED exit=1; restored; silently accept a second session end
74 planted breaks, 74 RED, all restored; 17 production blobs unchanged
```

**The handback checklist's four outputs:** Each prescribed command ran in the worktree. Scope command exit 0 with no output; blob command exit 0. The pragma command exits 0 and prints two pre-existing protocol declarations, so the checklist's `prints nothing` comment is verified inaccurate. No coverage exemption was added; the loop exemption was removed by the supplied diff.

Scope:

```text
$ git diff --name-only main -- agents/scanner agents/analyst agents/portfolio_manager agents/provider/domain agents/execution/order_tolerance.py contracts orchestration/packs/trading_tunables.json orchestration/packs/trading_issuer_map.json orchestration/history_window.py
(no output)
exit 0
```

Diff stat:

```text
$ git diff --stat main
agents/curator/entrypoint.py                       |   2 +-
 agents/deliberator/entrypoint.py                   |   2 +
 agents/master/draining_server.py                   |  51 +++
 agents/master/entrypoint.py                        |  25 +-
 agents/master/fleet_preflight_loop.py              |  35 +-
 agents/master/http_server.py                       |  34 +-
 agents/master/laws/laws.md                         |  49 +-
 agents/master/laws/test-plan.md                    |  11 +-
 agents/master/settings.py                          |  13 +
 agents/master/stopping.py                          |  68 +++
 agents/master/store.py                             |   2 +-
 agents/master/tests/test_ehlo_server_routes.py     |  24 +-
 agents/master/tests/test_stop_deadline.py          |  87 ++++
 agents/master/tests/test_stop_preflight.py         |  68 +++
 agents/master/tests/test_stop_process.py           |  82 ++++
 agents/master/tests/test_stop_server.py            | 183 ++++++++
 agents/master/tests/test_stop_session.py           | 192 ++++++++
 agents/operator/entrypoint.py                      |   2 +-
 agents/researcher/entrypoint.py                    |   4 +-
 agents/supervisor/entrypoint.py                    |   4 +-
 docs/laws/INDEX.md                                 |   2 +-
 docs/laws/drift-register.md                        |   1 +
 docs/laws/ledger.md                                |   2 +-
 docs/sprints/README.md                             |   2 +-
 ...-a-container-ends-cleanly-on-the-stop-signal.md | 504 ++++++++++++++++++---
 kernel/bus_azure_receiver.py                       |  10 +
 kernel/graph_guarded.py                            |   6 +
 kernel/serve_loop.py                               |  43 +-
 kernel/stop.py                                     | 165 +++++++
 kernel/work_loop.py                                |  47 +-
 pyproject.toml                                     |   2 +-
 tests/test_deliberator_cold_peer_timing.py         |  12 +-
 tests/test_serve_stop.py                           | 121 +++++
 tests/test_stop_closing.py                         |  93 ++++
 tests/test_stop_entrypoints.py                     |  36 ++
 tests/test_stop_resources.py                       |  79 ++++
 tests/test_stop_signal.py                          | 118 +++++
 tests/test_work_stop.py                            | 118 +++++
 tests/test_work_stop_signal.py                     |  95 ++++
 uv.lock                                            |   2 +-
 40 files changed, 2273 insertions(+), 123 deletions(-)
```

17 blobs, in the exact order of the checklist's `git hash-object` command:

```text
$ git hash-object kernel/stop.py kernel/work_loop.py kernel/serve_loop.py kernel/graph_guarded.py kernel/bus_azure_receiver.py agents/curator/entrypoint.py agents/operator/entrypoint.py agents/researcher/entrypoint.py agents/supervisor/entrypoint.py agents/deliberator/entrypoint.py agents/master/draining_server.py agents/master/http_server.py agents/master/fleet_preflight_loop.py agents/master/stopping.py agents/master/store.py agents/master/settings.py agents/master/entrypoint.py
f9f17cb8bd9933d40867e54f3f2a3b40b6f0a866
441ee58984025b0ffee0abd2586827f53588decd
ad0734a71cb9928348c24f466a8f487e430dbe72
cc6661162f1c43f39bd194937a987eceb6a04aff
e3f229af194ec355ffa0e3fb0f6b61242ae36c50
d32821e88bc7122cb785ea7f50c4f7796fffb9ec
e9065e318ea8cd7bc24ef9aa0669b32d057456d5
dfccda1ada8e8aa0a98830d701ebd27c100a83b3
b2087b67475565bb06fd8707f679869e9a862f62
05d24d9f19aadbae3613496a8a05a4b0b28e914f
4b14c090ba19f0681a6abf3d722a6fb6d1f999e8
0d249a604c4edcbb462ba8ee80949dfd12457ecf
2234ab21c5fa1764f108e1927ed5ee73e791775e
29a2374dd8b26782e5df6d5ac007bd65eb956c3a
8ffe83da3a1884639023beee04e6c5b30a6ff35e
79a6d31937be8d0203d56f83409606d7482a1760
5bc320aa4d1ce3df81aa52d3b28363c10a896022
```

Pragma search:

```text
$ git grep -n "pragma: no cover" -- kernel/stop.py kernel/serve_loop.py kernel/work_loop.py agents/master/stopping.py agents/master/draining_server.py agents/master/http_server.py
kernel/serve_loop.py:35:        ...  # pragma: no cover - protocol declaration only.
kernel/serve_loop.py:39:        ...  # pragma: no cover - protocol declaration only.
```

**Module line counts:** Every touched Python module and new test file is under 200 lines:

```text
agents/curator/entrypoint.py: 44
agents/deliberator/entrypoint.py: 123
agents/master/draining_server.py: 51
agents/master/entrypoint.py: 173
agents/master/fleet_preflight_loop.py: 81
agents/master/http_server.py: 163
agents/master/settings.py: 157
agents/master/stopping.py: 68
agents/master/store.py: 194
agents/master/tests/test_ehlo_server_routes.py: 78
agents/master/tests/test_stop_deadline.py: 87
agents/master/tests/test_stop_preflight.py: 68
agents/master/tests/test_stop_process.py: 82
agents/master/tests/test_stop_server.py: 183
agents/master/tests/test_stop_session.py: 192
agents/operator/entrypoint.py: 54
agents/researcher/entrypoint.py: 46
agents/supervisor/entrypoint.py: 54
kernel/bus_azure_receiver.py: 170
kernel/graph_guarded.py: 87
kernel/serve_loop.py: 129
kernel/stop.py: 165
kernel/work_loop.py: 186
tests/test_deliberator_cold_peer_timing.py: 59
tests/test_serve_stop.py: 121
tests/test_stop_closing.py: 93
tests/test_stop_entrypoints.py: 36
tests/test_stop_resources.py: 79
tests/test_stop_signal.py: 118
tests/test_work_stop.py: 118
tests/test_work_stop_signal.py: 95
```

**`make ci`:** `make ci > C:/Users/yury_/AppData/Local/Temp/s272-ci.txt 2>&1`, exit **0**. Sixteen steps ran; none skipped. 4822 passed, 8 skipped, 2470 warnings in 397.73s (0:06:37). Coverage **100.00%**. The eight environment-dependent or optional test skips are pytest cases, not skipped CI steps; their exact reasons are pasted below. Dependency audit, detect-secrets and untracked-secret checks passed. Actual command lines and closing output:

```text
uv run ruff check . --output-format=github
uv run ruff format --check .
uv run mypy kernel contracts agents orchestration surfaces
uv run lint-imports
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run python scripts/check_law_coverage.py
uv run python scripts/check_param_law_sync.py
uv run python scripts/check_sprint_status.py
uv run python scripts/check_tracker_size.py
uv run python scripts/check_markdown_links.py
uv run python scripts/check_version_scheme.py
uv run pytest
uv run python scripts/check_dependency_audit.py
uv run pre-commit run detect-secrets --all-files
uv run python scripts/check_untracked_secrets.py

1693 files already formatted
Success: no issues found in 1205 source files
Contracts: 5 kept, 0 broken.
collected 4830 items
TOTAL                                                           20472      0   4358      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
SKIPPED [1] tests\test_bus_azure_config.py:21: Service Bus dotenv isolation proof requires local .env
SKIPPED [1] tests\test_bus_celery.py:181: CELERY_BROKER_URL is not set
SKIPPED [1] tests\test_deliberator_servicebus_peer.py:36: A1 proof requires .env present; CI has no local secrets file
SKIPPED [1] tests\test_graph_postgres.py:137: POSTGRES_TEST_DSN is not set
SKIPPED [1] tests\test_graph_postgres_keys.py:90: POSTGRES_TEST_DSN is not set
SKIPPED [1] agents\forecaster\tests\test_barrier_garch_oracle.py:179: could not import 'scipy.signal': No module named 'scipy'
SKIPPED [1] agents\provider\tests\test_sources.py:159: FINNHUB_TEST_NETWORK=1 is not set
SKIPPED [1] agents\provider\tests\test_stooq.py:66: STOOQ_TEST_NETWORK=1 is not set
========= 4822 passed, 8 skipped, 2470 warnings in 397.73s (0:06:37) ==========

uv run python scripts/check_dependency_audit.py
accepted: PYSEC-2026-2447 (diskcache 5.6.3) - reachable only via the 'optimizer' extra, installed by 1 of 15 Dockerfiles; each installing command excludes diskcache by name; the dev group carries it too, and every sync passes --no-dev or excludes it by name; no fix release exists; every deployed optimizer installation excludes diskcache by name (S254, DL-266, ADR-0032) [DL-184] - retire when diskcache publishes a fixed release, or the optimizer extra is dropped
No unaccepted vulnerabilities; 1 accepted advisory re-checked
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
detect-secrets (untracked): no untracked files to scan
CI_EXIT=0
```

**`make gate-ran`:** NOT RUN — the user explicitly forbids push and merge. Network was available for `uv lock` and the dependency audit; remote proof is owed by the planner after the branch is pushed, from this worktree's exact HEAD.

**Not met / verified failing:** No build/CI requirement left unmet. The pragma checklist's expected empty output is verified false: two existing protocol declarations print, exactly as pasted; no new pragma was added. Push, remote gates, merge, Linux PID-1 replay F1, deployment and fleet F2 are NOT DONE and remain with the planner/operator as specified.

---

## Return notes

- Built only in the requested worktree and branch; main and every excluded path untouched. PATCH `0.125.09`; `uv lock` changed only the project's normalized version, to `0.125.9`.
- All production blobs still match the appendix after 74 restored breaks; master v1.10 appears in all four required files, rollups 30 / 55, DRIFT-113 corrected.
- Twelve new test files stay below 200 lines; E1/E2 are the only existing tests edited, and their previous assertions remain. The three extra proofs are identified above.
- The checklist's pragma-comment discrepancy is recorded without changing the supplied code or adding a coverage exemption.
- Planner owes merged-tree local/remote gates, CodeQL comparison and F1 before any deployment; deployment requires the operator's word, then F2 for all 16 apps and the first nightly stop. Work longer than the platform grace and stop during import/activation remain outside this sprint.

---

## Planner's review at the merge — 2026-10-14

Re-measured by the planner in `../ta-s272`. Nothing here is taken from the handback.

- **The production change is the appendix's, but for three lines the planner changed.** On the
  builder's commit `c819f74e` all 17 production files and the master's `laws.md` had the
  prototype's blob ids, and the scope command printed nothing. Against the spec's commit the
  branch changes the files the spec names and no other. Two existing tests are edited, the two
  named, and every assertion they held is kept.
- **Two commits by the planner, for a fault in the planner's own prototype** (`b3852856`, then
  `497293b8`). CodeQL raised `py/uninitialized-local-variable` at error level on the branch for
  `clean` in the closing line (alert 290), a variable assigned on the line above its use. All
  three remote workflows were green with it: the gate reads `main`'s alerts, and it was the
  comparison with the last merged branch that showed it. The first rewrite took the expression out
  of the f-string, and the scanner raised the same error one line up (alert 292). It loses track
  of a local assigned from `not (a or b)` when an `if` has just tested both names. The second
  rewrite derives the exit code from a count of what was left or failed, and the error is gone.
  The line written and the value returned are the same; the builder's tests and the planner's pin
  both. `kernel/stop.py` therefore differs from the appendix in those lines: 165 lines, blob
  `1d0290b8`.
- **The builder's tests are its own**: twelve files, 38 tests, none of them the planner's text.
  The planner's own 38 were placed beside them and run with them: 76 passed. They are not
  committed.
- **Guards.** The planner's 51 breaks, one at a time against the builder's test files alone, each
  restored: **51 went red, none survived, none failed to apply**. The tree was clean afterwards
  and no process was left running. They ran on the builder's commit; the three that touch the
  rewritten lines were planted again on the final ones, and three went red.
- **Cited tests.** Each of the 38 citations in the rows of `MST-TRG-03`, `MST-ORD-04`,
  `MST-OBS-05` and `MST-OUT-03` was resolved by hand: the file, the test, and the clause named in
  its docstring. The master's row reads v1.10 and 30 / 55 in `docs/laws/INDEX.md` and
  `ledger.md`. DRIFT-113 is filed as corrected.
- **A fault in this spec, found by the builder.** The handback checklist says the search for
  `pragma: no cover` prints nothing. It prints two lines of `kernel/serve_loop.py`, the protocol
  declarations that were there before the sprint. No exemption was added.
- **`make ci`**, run by the planner on the final tree, because the last two commits are the
  planner's own: exit 0, sixteen steps, 4,822 passed, 8 skipped, 100.00 %. The second rewrite was
  pushed while that run was still going, to have the scanner's answer sooner; both were green
  before the merge.
- **Gate.** `GATE PROVEN` for `497293b8c546a6409bed876f9f1db7e2b150a8e7`, run from `../ta-s272`, whose `HEAD` it is: CI, CodeQL and
  Security Findings each `success`. `main` had not moved since the spec's last commit, so nothing
  was merged in and the proven commit is the merged one.
- **CodeQL.** 129 open alerts on the branch, 0 of them errors. Against the S271 branch one is
  added, a note (`py/unused-import` in the builder's `test_stop_deadline.py`, for a name used
  inside a `cast` under `TYPE_CHECKING`), and none is gone.
- **F1, at no cost, on the merged commit.** Run from the sprint's worktree, whose `HEAD` is the
  merged commit and which holds no `.env` (in the main checkout the master's child would read
  one). (a) `wq116_stop_paths.py`, five child processes, a real `SIGTERM` raised inside each: the
  lines printed are the prototype's, the session id and the seconds apart. An idle graph-pull
  agent and an idle served agent flush, close and exit 0; an agent with three one-second items
  finishes the one in hand, leaves the third pending and exits 0; an agent whose graph refuses to
  close exits 1 and its line names the error's type alone; the master ends its `Session` with
  `ended_at` and `shutdown_reason` `SIGTERM` and exits 0. (b) `pid1_probe.sh`, Linux 5.15, Python
  3.12 as process 1 of its own PID namespace: the control with no handler ignored `SIGTERM` for
  the 6.0 seconds it was watched and was killed; on the merged `kernel/stop.py` the process wrote
  its two lines and exited 0 in 0.2 seconds.
- **Owed.** The deploy: an image-only retag, on the operator's word. Then F2 on the fleet, at no
  cost: 16 closing lines in the console logs, no exit code 137 for a revision of the new tag, the
  master's newest ended `Session` holding `ended_at`; and the same read after the first nightly
  window's end. The first stop after the retag is of the old image and is still a kill. Not
  proven until then: that the platform stops a container with `SIGTERM` to process 1, and what it
  logs for an exit with code 0.

Evidence outside the repo: OneDrive `trading-agents-data/wq116-2026-10-13/`
(`planner_breaks_on_built.txt`, `break_s272_on_built.py`, `planner_tests/`, `s272-make-ci.txt`,
`planner_breaks_closing_on_final.txt`, `s272-gate-wait.txt`, `s272-gate-ran.txt`,
`codeql_s272_branch.tsv`, `f1_built_497293b8.txt`, `f1_pid1_built_497293b8.txt`,
`s272_merge_docs.py`).

---

## Appendix — the production change, measured on the planner's prototype

**On the prototype** *[measured 2026-10-13, Windows, the worktree's own environment, no `.env`]*:
`make ci` exit 0, sixteen steps (4,822 passed, 8 skipped, 100.00 %); 51 planted breaks, 51 red; the scope command prints nothing.

### 1. What the five process shapes print on the built code

From `wq116_stop_paths.py` (the planner's, outside the repository). The lines in square brackets
are the product's; the lines in round brackets are the measuring script's.

```text
== A. graph-pull agent, idle (no pending work, 60 s poll)
   exit code 0
   | (signal sent 1.5 s after the loop started)
   | [scanner] stop signal SIGTERM: taking no new work
   | (faults flushed)
   | (graph.close called)
   | [scanner] stopped on SIGTERM after 0.0 s: closed faults, graph; exit 0
   | (the process ended by itself 0.5 s after the signal)
== B. graph-pull agent, three items of 1 s each in hand when told
   exit code 0
   | (started one)
   | (finished one)
   | (started two)
   | (signal sent 1.5 s after the loop started)
   | [execution] stop signal SIGTERM: taking no new work
   | (finished two)
   | (graph.close called)
   | [execution] stopped on SIGTERM after 0.0 s: closed graph; exit 0
   | (left pending: ['three'])
   | (the process ended by itself 0.5 s after the signal)
== C. served agent, idle (empty inbox, 60 s poll)
   exit code 0
   | (signal sent 1.5 s after the loop started)
   | [curator] stop signal SIGTERM: taking no new work
   | (consumer.close called)
   | (graph.close called)
   | [curator] stopped on SIGTERM after 0.0 s: closed requests, graph; exit 0
   | (the process ended by itself 0.5 s after the signal)
== D. graph-pull agent whose graph refuses to close
   exit code 1
   | (signal sent 1.5 s after the loop started)
   | [monitor] stop signal SIGTERM: taking no new work
   | [monitor] stopped on SIGTERM after 0.0 s: NOT closed graph (ConnectionError); exit 1
   | (the process ended by itself 0.5 s after the signal)
== E. master: serving, in-memory graph, no pack
   exit code 0
   | [master] session=session:20261013T093056:543b756a — serving on :8000
   | (session props at start: ['started_at'])
   | (signal sent 1.5 s after the loop started)
   | [master] stop signal SIGTERM: taking no new work
   | [master] stopped on SIGTERM after 0.0 s: closed session; exit 0
   | (session props at exit: ['ended_at', 'shutdown_reason', 'started_at'])
   | (shutdown_reason: 'SIGTERM')
   | (the process ended by itself 0.0 s after the signal)
```

The seconds in a closing line count from the moment the handler ran, so an idle process reads
`0.0 s`; the half second before it is the sliced sleep ending. In E the in-memory graph has no
`close`, so the line names the session alone; on the fleet it reads `closed session, graph`.

### 2. The diff

Made with `git diff -U0` on the prototype, against `main` at `b048d251`. It holds no context
lines. Save the block to a file and apply it from the worktree root:

```bash
git apply --unidiff-zero <the file>
```

Seventeen production files and the master's `laws.md`. No test is in it.

```diff
diff --git a/agents/curator/entrypoint.py b/agents/curator/entrypoint.py
index b614c4ed..d32821e8 100644
--- a/agents/curator/entrypoint.py
+++ b/agents/curator/entrypoint.py
@@ -40 +40 @@ def main() -> None:  # pragma: no cover
-    serve_loop(consumer_from_env("curator", graph), bus)
+    serve_loop(consumer_from_env("curator", graph), bus, graph=graph, agent="curator")
diff --git a/agents/deliberator/entrypoint.py b/agents/deliberator/entrypoint.py
index 3b0cb88c..05d24d9f 100644
--- a/agents/deliberator/entrypoint.py
+++ b/agents/deliberator/entrypoint.py
@@ -73,0 +74,2 @@ def serve_peer(
+        graph=graph,
+        agent=settings.identity,
diff --git a/agents/master/draining_server.py b/agents/master/draining_server.py
new file mode 100644
index 00000000..4b14c090
--- /dev/null
+++ b/agents/master/draining_server.py
@@ -0,0 +1,51 @@
+"""Threading TCP server that knows how many requests it has in hand.
+
+Agent: master
+Role: count each request in before its thread starts and out when it ends, so a
+      stopping server can wait a bounded time for the requests in hand.
+External I/O: none of its own (the TCP socket belongs to the server it extends).
+"""
+
+from __future__ import annotations
+
+import socketserver
+import threading
+from typing import Any
+
+
+class DrainingTCPServer(socketserver.ThreadingTCPServer):
+    """A thread per request, counted, so ``drain`` can wait for those in hand."""
+
+    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
+        """Build the server with no request in hand."""
+        super().__init__(*args, **kwargs)
+        self._idle = threading.Condition()
+        self._in_hand = 0
+
+    def process_request(self, request: Any, client_address: Any) -> None:  # noqa: ANN401
+        """Count the request in before its thread starts."""
+        with self._idle:
+            self._in_hand += 1
+        try:
+            super().process_request(request, client_address)
+        except BaseException:
+            self._count_out()
+            raise
+
+    def process_request_thread(self, request: Any, client_address: Any) -> None:  # noqa: ANN401
+        """Serve the request on its thread, then count it out."""
+        try:
+            super().process_request_thread(request, client_address)
+        finally:
+            self._count_out()
+
+    def _count_out(self) -> None:
+        with self._idle:
+            self._in_hand -= 1
+            self._idle.notify_all()
+
+    def drain(self, seconds: float) -> int:
+        """Wait up to *seconds* for the requests in hand; return how many are left."""
+        with self._idle:
+            self._idle.wait_for(lambda: self._in_hand == 0, timeout=max(seconds, 0.0))
+            return self._in_hand
diff --git a/agents/master/entrypoint.py b/agents/master/entrypoint.py
index 7e0ce46b..5bc320aa 100644
--- a/agents/master/entrypoint.py
+++ b/agents/master/entrypoint.py
@@ -4 +4,2 @@ Agent: master
-Role: load RSA private key and secret store from env, start HTTP server on :8000.
+Role: load RSA private key and secret store from env, serve HTTP on :8000 until
+      the stop signal, then end the session and close the graph.
@@ -24,0 +26 @@ from agents.master.settings import MasterSettings
+from agents.master.stopping import shut_down
@@ -25,0 +28 @@ from kernel.crypto import generate_keypair
+from kernel.stop import StopSignal, install
@@ -90 +93 @@ def main() -> None:  # pragma: no cover
-    """Load config from env and start the master HTTP server."""
+    """Load config from env, serve until the stop signal, then shut down."""
@@ -92,0 +96 @@ def main() -> None:  # pragma: no cover
+    import sys
@@ -102,0 +107,2 @@ def main() -> None:  # pragma: no cover
+    stop = StopSignal()
+    install(stop, agent="master")
@@ -146 +152 @@ def main() -> None:  # pragma: no cover
-    start_fleet_preflight_daemon(
+    preflight = start_fleet_preflight_daemon(
@@ -149,0 +156 @@ def main() -> None:  # pragma: no cover
+        stop=stop,
@@ -152 +159,11 @@ def main() -> None:  # pragma: no cover
-    serve(8000, agent, key_pem, settings)
+    left = serve(8000, agent, key_pem, settings, stop=stop)
+    sys.exit(
+        shut_down(
+            agent,
+            graph,
+            stop,
+            activations_left=left,
+            preflight=preflight,
+            settings=settings,
+        )
+    )
diff --git a/agents/master/fleet_preflight_loop.py b/agents/master/fleet_preflight_loop.py
index ec971e28..2234ab21 100644
--- a/agents/master/fleet_preflight_loop.py
+++ b/agents/master/fleet_preflight_loop.py
@@ -4 +4 @@ Agent: master
-Role: repeat the fleet readiness check at a bounded interval.
+Role: repeat the fleet readiness check at a bounded interval, until told to stop.
@@ -11 +10,0 @@ from threading import Thread
-from time import sleep
@@ -14,0 +14 @@ from kernel.errors import fault_boundary
+from kernel.stop import StopSignal
@@ -22,0 +23,4 @@ if TYPE_CHECKING:
+def _never() -> bool:
+    return False
+
+
@@ -29,0 +34 @@ def run_fleet_preflight_loop(
+    should_stop: Callable[[], bool] = _never,
@@ -31 +36,4 @@ def run_fleet_preflight_loop(
-    """Run preflight repeatedly; one crashing iteration faults but does not stop it."""
+    """Run preflight repeatedly; one crashing iteration faults but does not stop it.
+
+    Once *should_stop* answers yes no further check starts.
+    """
@@ -33 +41 @@ def run_fleet_preflight_loop(
-    while iterations is None or completed < iterations:
+    while not should_stop() and (iterations is None or completed < iterations):
@@ -52,3 +60,9 @@ def start_fleet_preflight_daemon(
-) -> None:
-    """Start the master-owned preflight schedule without blocking HTTP serving."""
-    Thread(
+    stop: StopSignal | None = None,
+) -> Thread:
+    """Start the master-owned preflight schedule without blocking HTTP serving.
+
+    The schedule sleeps on *stop*, so a stop ends the wait between two checks at
+    once; the thread is returned so the stop can wait for a check in hand.
+    """
+    stopping = stop if stop is not None else StopSignal()
+    thread = Thread(
@@ -60 +74,2 @@ def start_fleet_preflight_daemon(
-            "sleep": sleep,
+            "sleep": stopping.wait,
+            "should_stop": lambda: stopping.requested,
@@ -64 +79,3 @@ def start_fleet_preflight_daemon(
-    ).start()
+    )
+    thread.start()
+    return thread
diff --git a/agents/master/http_server.py b/agents/master/http_server.py
index eced73eb..0d249a60 100644
--- a/agents/master/http_server.py
+++ b/agents/master/http_server.py
@@ -6 +6,2 @@ Role: expose /ehlo (ACTIVATE handshake, a resent boot id replayed) and /health o
-      run as the container's main blocking loop.
+      run as the container's main loop until the stop signal, then let the
+      activations in hand finish.
@@ -14 +14,0 @@ import json
-import socketserver
@@ -17,0 +18 @@ from agents.master.activation_replay import ActivationReplay, replay_lifetime_se
+from agents.master.draining_server import DrainingTCPServer
@@ -19,0 +21,3 @@ from kernel.handshake import EHLOMessage
+from kernel.stop import StopSignal, install
+
+_ACCEPT_WAIT_SECONDS = 0.5
@@ -61 +65 @@ def handle_ehlo(
-class EhloServer(socketserver.ThreadingTCPServer):
+class EhloServer(DrainingTCPServer):
@@ -136,2 +140,13 @@ def serve(
-) -> None:
-    """Serve EHLO on *host*:*port* until the process ends (the container's loop)."""
+    *,
+    stop: StopSignal | None = None,
+) -> int:
+    """Serve EHLO on *host*:*port* until told to stop (the container's loop).
+
+    Listens for the stop signal itself unless a *stop* is handed in. On a stop it
+    closes the listening socket, waits for the activations in hand until
+    ``stop_drain_seconds`` have passed since the signal, and returns how many it
+    left unfinished.
+    """
+    stopping = stop if stop is not None else StopSignal()
+    if stop is None:
+        install(stopping, agent="master")
@@ -142,2 +157,7 @@ def serve(
-    with server:
-        server.serve_forever()
+    server.timeout = _ACCEPT_WAIT_SECONDS
+    try:
+        while not stopping.requested:
+            server.handle_request()
+    finally:
+        server.server_close()
+    return server.drain(stopping.seconds_left(settings.stop_drain_seconds))
diff --git a/agents/master/laws/laws.md b/agents/master/laws/laws.md
index 6a6b1c74..99afca33 100644
--- a/agents/master/laws/laws.md
+++ b/agents/master/laws/laws.md
@@ -3 +3 @@
-**Prefix:** `MST` · **status:** LOCKED v1.9 · **Owner:** Yury Gurevich
+**Prefix:** `MST` · **status:** LOCKED v1.10 · **Owner:** Yury Gurevich
@@ -41,2 +41,10 @@ green only when a functional test cites its ID (conventions §3). Tests + status
-- **MST-TRG-02** — `drain` is triggered by the operator (via supervisor) or by master's own
-  crash-recovery logic on startup.
+- **MST-TRG-02** — `drain` is triggered by the operator (via supervisor). Nothing in master
+  triggers it at start: no recovery path exists.
+- **MST-TRG-03** — The platform's stop signal (`SIGTERM`) ends every container's main loop:
+  master's EHLO server, an agent's graph-pull loop and an agent's serve loop. From the signal a
+  graph-pull loop starts no further item and a serve loop takes no further request; the item or
+  request in hand is finished (a taken request was settled when taken, so it is answered); an idle
+  loop wakes within a second. The loop then flushes its faults and closes its request consumer and
+  its graph connection, each on its own, and the process exits `0` only if every one of them
+  closed; otherwise `1`. A loop listens from the moment it starts: a signal that arrives earlier,
+  while the container is still importing or activating, is not handled.
@@ -51,2 +59,4 @@ green only when a functional test cites its ID (conventions §3). Tests + status
-- **MST-OUT-03** — On `start()`, writes a `Session` node with `started_at`. Used for
-  crash-recovery detection (no `ended_at` → prior session crashed).
+- **MST-OUT-03** — On `start()`, writes a `Session` node with `started_at` and nothing else. On
+  the stop signal master adds `ended_at` and `shutdown_reason` (the signal's name) to it, once. A
+  `Session` with no `ended_at` belongs to a master that is still running or did not stop when
+  asked: it was killed or it crashed.
@@ -80,2 +90,3 @@ green only when a functional test cites its ID (conventions §3). Tests + status
-- **MST-STA-01** — `start()` writes one `Session` node with `started_at`. On next boot, if the
-  latest `Session` has no `ended_at`, master infers a crash and enters recovery mode.
+- **MST-STA-01** — `start()` writes one `Session` node with `started_at`. Nothing reads it at
+  the next boot; whether an earlier master stopped when asked is read from its `Session`
+  (`MST-OUT-03`).
@@ -95,2 +106,2 @@ green only when a functional test cites its ID (conventions §3). Tests + status
-- **MST-IDM-02** — If master restarts, it reads the existing `Session` nodes to determine recovery
-  context before writing a new `Session`.
+- **MST-IDM-02** — A restarted master opens a new `Session` and reads none of the earlier ones;
+  an earlier `Session` is never changed by a later master.
@@ -116,0 +128,5 @@ green only when a functional test cites its ID (conventions §3). Tests + status
+- **MST-ORD-04** — On the stop signal master stops in this order: it closes its listening socket;
+  it waits for the activations in hand and for a fleet check in hand, until `stop_drain_seconds`
+  have passed since the signal; it ends its session (`MST-OUT-03`); it closes its graph connection.
+  It exits `0` only if nothing was left unfinished and every step succeeded. An activation or a
+  fleet check left unfinished, or a failed step, is exit `1`, and the session end is still written.
@@ -198,0 +215,5 @@ guarantees.
+- **MST-OBS-05** — A stop leaves two lines on the container's stderr. When the signal arrives:
+  `[<agent>] stop signal <NAME>: taking no new work`, written unbuffered from the handler, so a
+  process killed later still shows that it was told to stop. When the process has closed what it
+  held: `[<agent>] stopped on <NAME> after <seconds> s: <left ...; closed ...; NOT closed ...>;
+  exit <code>`. A step that failed is named with its error's type alone, never the error's text.
@@ -235,0 +257 @@ guarantees.
+| `stop_drain_seconds` | `20.0` | `float ≥ 0.0 ≤ 600.0` | YES | Seconds after the stop signal that master waits for the activations in hand and a fleet check in hand before it ends its session (`MST-ORD-04`); keep it under the platform's stop grace, 30 seconds unless the app sets one |
@@ -253,0 +276,9 @@ guarantees.
+- v1.10 — S272 / DL-297 (2026-10-13): every container ends on the stop signal. New `MST-TRG-03`
+  (the kernel's graph-pull and serve loops and master's server end on `SIGTERM`, close what they
+  hold, exit `0` only when all of it closed), `MST-ORD-04` (master's order: listening socket,
+  activations and fleet check in hand within `stop_drain_seconds`, session end, graph) and
+  `MST-OBS-05` (the two lines a stop leaves). `MST-OUT-03` amended and proven: the `Session` gets
+  `ended_at` and `shutdown_reason` on a stop, and no empty `shutdown_reason` at start. `MST-STA-01`,
+  `MST-TRG-02` and `MST-IDM-02` reworded: they named a recovery path at boot that no code holds
+  (DRIFT-113). PARAM gains `stop_drain_seconds`.
+
diff --git a/agents/master/settings.py b/agents/master/settings.py
index de95b8fc..79a6d319 100644
--- a/agents/master/settings.py
+++ b/agents/master/settings.py
@@ -105,0 +106,13 @@ class MasterSettings(AgentSettings):
+    stop_drain_seconds: float = tunable(
+        20.0,
+        why=(
+            "Seconds after the stop signal that master waits for the activations "
+            "in hand and a running fleet check before it ends its session; keep it "
+            "under the platform's stop grace (30 s unless the app sets one) so the "
+            "session end is written before the kill."
+        ),
+        ge=0.0,
+        le=600.0,
+        unit="seconds",
+    )
+
diff --git a/agents/master/stopping.py b/agents/master/stopping.py
new file mode 100644
index 00000000..29a2374d
--- /dev/null
+++ b/agents/master/stopping.py
@@ -0,0 +1,68 @@
+"""Master's stop — end the session, close the graph, write the closing line.
+
+Agent: master
+Role: once the EHLO server has stopped, wait for a fleet check in hand, record
+      the end of the boot session, close the graph connection and return the
+      process exit code.
+External I/O: graph database via the injected GraphStore; writes to stderr.
+"""
+
+from __future__ import annotations
+
+from datetime import UTC, datetime
+from typing import TYPE_CHECKING
+
+from kernel.stop import closing_steps, finish
+
+if TYPE_CHECKING:
+    from collections.abc import Callable
+    from threading import Thread
+
+    from agents.master.agent import MasterAgent
+    from agents.master.settings import MasterSettings
+    from kernel import GraphStore
+    from kernel.graph import Node
+    from kernel.stop import Step, StopSignal
+
+
+def end_session(graph: GraphStore, session_id: str, *, reason: str) -> Node:
+    """Record on the boot session that master stopped when asked (MST-OUT-03)."""
+    return graph.merge_node(
+        "Session",
+        session_id,
+        {"ended_at": datetime.now(UTC).isoformat(), "shutdown_reason": reason},
+    )
+
+
+def shut_down(
+    agent: MasterAgent,
+    graph: GraphStore,
+    stop: StopSignal,
+    *,
+    activations_left: int,
+    preflight: Thread,
+    settings: MasterSettings,
+    write: Callable[[str], None] | None = None,
+) -> int:
+    """Finish a stopped master; return 0 only when nothing was left and nothing failed.
+
+    The session end is written even when an activation was left, because master
+    did stop when asked; the exit code and the closing line carry what was left.
+    """
+    unfinished: list[str] = []
+    if activations_left:
+        unfinished.append(f"{activations_left} activation(s)")
+    preflight.join(stop.seconds_left(settings.stop_drain_seconds))
+    if preflight.is_alive():
+        unfinished.append("the fleet check")
+    steps: list[Step] = []
+    session_id = agent.session_id
+    if session_id is not None:
+        steps.append(
+            ("session", lambda: end_session(graph, session_id, reason=stop.reason))
+        )
+    steps.extend(closing_steps(graph=graph))
+    clean = finish(
+        stop, agent="master", steps=steps, unfinished=unfinished, write=write
+    )
+    return 0 if clean else 1
diff --git a/agents/master/store.py b/agents/master/store.py
index 84de9335..8ffe83da 100644
--- a/agents/master/store.py
+++ b/agents/master/store.py
@@ -27 +27 @@ def write_session(graph: GraphStore, session_id: str) -> Node:
-        {"started_at": datetime.now(UTC).isoformat(), "shutdown_reason": ""},
+        {"started_at": datetime.now(UTC).isoformat()},
diff --git a/agents/operator/entrypoint.py b/agents/operator/entrypoint.py
index ef55260d..e9065e31 100644
--- a/agents/operator/entrypoint.py
+++ b/agents/operator/entrypoint.py
@@ -50 +50 @@ def main() -> None:  # pragma: no cover
-    serve_loop(consumer_from_env("operator", graph), bus)
+    serve_loop(consumer_from_env("operator", graph), bus, graph=graph, agent="operator")
diff --git a/agents/researcher/entrypoint.py b/agents/researcher/entrypoint.py
index 9ebc007b..dfccda1a 100644
--- a/agents/researcher/entrypoint.py
+++ b/agents/researcher/entrypoint.py
@@ -40 +40,3 @@ def main() -> None:  # pragma: no cover
-    serve_loop(consumer_from_env("researcher", graph), bus)
+    serve_loop(
+        consumer_from_env("researcher", graph), bus, graph=graph, agent="researcher"
+    )
diff --git a/agents/supervisor/entrypoint.py b/agents/supervisor/entrypoint.py
index d30e86bb..b2087b67 100644
--- a/agents/supervisor/entrypoint.py
+++ b/agents/supervisor/entrypoint.py
@@ -48 +48,3 @@ def main() -> None:  # pragma: no cover
-    serve_loop(consumer_from_env("supervisor", graph), bus)
+    serve_loop(
+        consumer_from_env("supervisor", graph), bus, graph=graph, agent="supervisor"
+    )
diff --git a/kernel/bus_azure_receiver.py b/kernel/bus_azure_receiver.py
index 043b1df8..e3f229af 100644
--- a/kernel/bus_azure_receiver.py
+++ b/kernel/bus_azure_receiver.py
@@ -92,0 +93,10 @@ class AzureServiceBusRequestConsumer:
+    def close(self) -> None:
+        """Close the receiver and the client behind it; a later poll opens anew."""
+        held = (self._receiver, self._client)
+        self._receiver = None
+        self._client = None
+        for item in held:
+            close = getattr(item, "close", None)
+            if callable(close):
+                close()
+
diff --git a/kernel/graph_guarded.py b/kernel/graph_guarded.py
index eb21d805..cc666116 100644
--- a/kernel/graph_guarded.py
+++ b/kernel/graph_guarded.py
@@ -35,0 +36,6 @@ class GuardedGraphStore:
+    def close(self) -> None:
+        """Close the wrapped store when it holds something to close."""
+        close = getattr(self._inner, "close", None)
+        if callable(close):
+            close()
+
diff --git a/kernel/serve_loop.py b/kernel/serve_loop.py
index eb241fcd..ad0734a7 100644
--- a/kernel/serve_loop.py
+++ b/kernel/serve_loop.py
@@ -8,2 +8,2 @@ Role: shared "receive a request -> dispatch to the bound handler -> reply" loop
-      share one code path and the loop can never die on a bad request. ``serve_once``
-      carries the coverage; ``serve_loop`` is the infinite wrapper (twin of
+      share one code path and the loop can never die on a bad request.
+      ``serve_loop`` wraps ``serve_once`` until the stop signal (twin of
@@ -16 +15,0 @@ from __future__ import annotations
-import time
@@ -19,0 +19 @@ from kernel.errors import CollectingFaultSink, fault_boundary
+from kernel.stop import UNNAMED, StopSignal, closing_steps, end_loop, install
@@ -24,0 +25 @@ if TYPE_CHECKING:
+    from kernel.graph import GraphStore
@@ -94 +95 @@ def serve_once(
-def serve_loop(  # pragma: no cover - blocks forever; serve_once carries the coverage
+def serve_loop(
@@ -100,5 +101,29 @@ def serve_loop(  # pragma: no cover - blocks forever; serve_once carries the cov
-) -> None:
-    """Serve forever: dispatch all pending requests, then sleep when idle."""
-    while True:
-        if serve_once(consumer, bus, sink=sink) == 0:
-            time.sleep(poll_interval)
+    graph: GraphStore | None = None,
+    agent: str | None = None,
+    stop: StopSignal | None = None,
+) -> int:
+    """Serve until told to stop: dispatch pending requests, sleep when idle.
+
+    A container's main loop: it listens for the stop signal itself unless a *stop*
+    is handed in. A request already taken is answered (it was settled when taken);
+    then the loop flushes the sink, closes the consumer and the graph and writes
+    the closing line (``kernel.stop``). Returns the number of requests served.
+    """
+    name = agent or UNNAMED
+    stopping = stop if stop is not None else StopSignal()
+    if stop is None:
+        install(stopping, agent=name)
+    served = 0
+    while not stopping.requested:
+        count = serve_once(consumer, bus, sink=sink)
+        served += count
+        if count == 0:
+            stopping.wait(poll_interval)
+    end_loop(
+        stopping,
+        agent=name,
+        steps=closing_steps(
+            faults=getattr(sink, "flush", None), requests=consumer, graph=graph
+        ),
+    )
+    return served
diff --git a/kernel/stop.py b/kernel/stop.py
new file mode 100644
index 00000000..f9f17cb8
--- /dev/null
+++ b/kernel/stop.py
@@ -0,0 +1,165 @@
+"""Stop signal for a container's main loop.
+
+Agent: kernel
+Role: turn the platform's stop signal (SIGTERM) into a flag a serving loop asks
+      and sleeps on, and write the two lines a stop leaves in the console log:
+      one when the signal arrives, one when what the loop held is closed.
+External I/O: installs a process signal handler; writes to stderr.
+"""
+
+from __future__ import annotations
+
+import os
+import signal
+import sys
+import threading
+import time
+from typing import TYPE_CHECKING
+
+if TYPE_CHECKING:
+    from collections.abc import Callable, Sequence
+
+    Step = tuple[str, Callable[[], object]]
+
+UNNAMED = "agent"
+_WAKE_SECONDS = 1.0
+
+
+class StopSignal:
+    """Set once when the process is told to stop; a loop asks it and sleeps on it."""
+
+    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
+        """Start unrequested; *clock* times the stop for the closing line."""
+        self._event = threading.Event()
+        self._clock = clock
+        self._requested_at = 0.0
+        self.reason = ""
+
+    def request(self, reason: str = "request") -> None:
+        """Ask the loop to stop; the first reason and its time are kept."""
+        if not self._event.is_set():
+            self.reason = reason
+            self._requested_at = self._clock()
+            self._event.set()
+
+    @property
+    def requested(self) -> bool:
+        """Whether a stop has been asked for."""
+        return self._event.is_set()
+
+    def wait(self, seconds: float) -> None:
+        """Sleep up to *seconds*; return within a second of a stop being asked for.
+
+        The sleep is taken in slices: the interpreter runs a signal handler only
+        when the main thread is back in Python code, and a signal the platform
+        hands to another thread does not end a single long wait.
+        """
+        deadline = time.monotonic() + max(seconds, 0.0)
+        while not self._event.is_set():
+            remaining = deadline - time.monotonic()
+            if remaining <= 0:
+                return
+            self._event.wait(min(remaining, _WAKE_SECONDS))
+
+    def seconds_since_request(self) -> float:
+        """Seconds since the stop was asked for (0.0 before one is)."""
+        return self._clock() - self._requested_at if self.requested else 0.0
+
+    def seconds_left(self, budget: float) -> float:
+        """Seconds of *budget* not yet spent since the stop was asked for."""
+        return max(budget - self.seconds_since_request(), 0.0)
+
+
+def _write_raw(line: str) -> None:
+    # A handler can interrupt the main thread inside a buffered write to stderr,
+    # and a second buffered write there raises; a raw write to the descriptor cannot.
+    os.write(2, line.encode())
+
+
+def _write_line(line: str) -> None:
+    sys.stderr.write(line)
+    sys.stderr.flush()
+
+
+def install(
+    stop: StopSignal, *, agent: str, write: Callable[[str], None] = _write_raw
+) -> bool:
+    """Route SIGTERM to *stop*; return False, installing nothing, off the main thread.
+
+    The interpreter runs a handler on the main thread only and refuses to install
+    one from another. The handler sets the flag and writes one line, so a process
+    killed later still shows in its log that it was told to stop and when.
+    """
+    if threading.current_thread() is not threading.main_thread():
+        return False
+
+    def handle(signum: int, _frame: object) -> None:
+        name = signal.Signals(signum).name
+        stop.request(name)
+        write(f"[{agent}] stop signal {name}: taking no new work\n")
+
+    signal.signal(signal.SIGTERM, handle)
+    return True
+
+
+def closing_steps(
+    *,
+    faults: Callable[[], object] | None = None,
+    requests: object = None,
+    graph: object = None,
+) -> tuple[Step, ...]:
+    """Name what a loop holds that can be closed, in the order it is closed."""
+    steps: list[Step] = []
+    if faults is not None:
+        steps.append(("faults", faults))
+    for name, held in (("requests", requests), ("graph", graph)):
+        close = getattr(held, "close", None)
+        if callable(close):
+            steps.append((name, close))
+    return tuple(steps)
+
+
+def finish(
+    stop: StopSignal,
+    *,
+    agent: str,
+    steps: Sequence[Step],
+    unfinished: Sequence[str] = (),
+    write: Callable[[str], None] | None = None,
+) -> bool:
+    """Run every closing step on its own, write the closing line, say whether clean.
+
+    A step that raises does not keep the next from running. The line names each
+    step and, for a failed one, the error's type alone (its text can hold a
+    connection string). *unfinished* names work the caller had to leave; a stop
+    is clean only when nothing was left and no step failed.
+    """
+    done: list[str] = []
+    failed: list[str] = []
+    for name, step in steps:
+        try:
+            step()
+        except Exception as exc:
+            failed.append(f"{name} ({type(exc).__name__})")
+        else:
+            done.append(name)
+    parts: list[str] = []
+    if unfinished:
+        parts.append("left " + ", ".join(unfinished))
+    if done:
+        parts.append("closed " + ", ".join(done))
+    if failed:
+        parts.append("NOT closed " + ", ".join(failed))
+    clean = not (unfinished or failed)
+    (write or _write_line)(
+        f"[{agent}] stopped on {stop.reason} after "
+        f"{stop.seconds_since_request():.1f} s: "
+        f"{'; '.join(parts) or 'nothing to close'}; exit {int(not clean)}\n"
+    )
+    return clean
+
+
+def end_loop(stop: StopSignal, *, agent: str, steps: Sequence[Step]) -> None:
+    """Close what a stopped loop held; a failed step ends the process with status 1."""
+    if not finish(stop, agent=agent, steps=steps):
+        raise SystemExit(1)
diff --git a/kernel/work_loop.py b/kernel/work_loop.py
index 82d97677..441ee589 100644
--- a/kernel/work_loop.py
+++ b/kernel/work_loop.py
@@ -14,0 +15 @@ from typing import TYPE_CHECKING
+from kernel.stop import UNNAMED, StopSignal, closing_steps, end_loop, install
@@ -28,0 +30,4 @@ if TYPE_CHECKING:
+def _never() -> bool:
+    return False
+
+
@@ -36,0 +42 @@ def run_once[T](
+    should_stop: Callable[[], bool] = _never,
@@ -38 +44,5 @@ def run_once[T](
-    """Process eligible pending items once and report progress, not activity."""
+    """Process eligible pending items once and report progress, not activity.
+
+    Once *should_stop* answers yes no further item is started: the item in hand
+    finishes and the rest stay pending for the next process.
+    """
@@ -43,0 +54 @@ def run_once[T](
+    attempted = 0
@@ -47,0 +59,3 @@ def run_once[T](
+        if should_stop():
+            break
+        attempted += 1
@@ -90 +104 @@ def run_once[T](
-        attempted=len(ready),
+        attempted=attempted,
@@ -109 +123 @@ def work_loop[T](
-    sleep: Callable[[float], None] = time.sleep,
+    sleep: Callable[[float], None] | None = None,
@@ -112,0 +127 @@ def work_loop[T](
+    stop: StopSignal | None = None,
@@ -114 +129,7 @@ def work_loop[T](
-    """Poll the graph forever: process all pending work, then sleep when idle."""
+    """Poll the graph until told to stop: process pending work, sleep when idle.
+
+    With no *max_iterations* this is a container's main loop, and it listens for
+    the stop signal itself unless a *stop* is handed in. On a stop it starts no
+    new item, ends the idle sleep at once, then flushes faults, closes the graph
+    and writes the closing line (``kernel.stop``).
+    """
@@ -116,0 +138,5 @@ def work_loop[T](
+    name = agent or UNNAMED
+    stopping = stop if stop is not None else StopSignal()
+    if stop is None and max_iterations is None:
+        install(stopping, agent=name)
+    pause = sleep if sleep is not None else stopping.wait
@@ -118 +144,3 @@ def work_loop[T](
-    while max_iterations is None or len(results) < max_iterations:
+    while not stopping.requested and (
+        max_iterations is None or len(results) < max_iterations
+    ):
@@ -124,0 +153 @@ def work_loop[T](
+            should_stop=lambda: stopping.requested,
@@ -130,2 +159,6 @@ def work_loop[T](
-            sleep(_sleep_duration(resolved.poll_interval_seconds, result))
-    if flush_faults is not None:
+            pause(_sleep_duration(resolved.poll_interval_seconds, result))
+    if stopping.requested:
+        end_loop(
+            stopping, agent=name, steps=closing_steps(faults=flush_faults, graph=graph)
+        )
+    elif flush_faults is not None:
```
