<!-- Agent: planning | Role: sprint handover -->
# Sprint 272 — a container told to stop ends by itself: it finishes the work in hand, closes what it holds, says so and exits 0

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-272-a-container-ends-cleanly-on-the-stop-signal`
**Status:** SPEC
**Version:** *next available PATCH at merge*
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

- [ ] The appendix's diff is applied as given: `git hash-object` of each of the 17 production
      files equals the planner's (the planner compares at review; you paste yours).
- [ ] A1 and A2 failed on the unchanged tree and pass on the built one.
- [ ] Exactly two existing tests are edited, E1 and E2, in the lines named.
- [ ] **No decision path changes**: the scope command prints nothing.
- [ ] Law cycle done: master v1.10 in four files, DRIFT-113 filed as corrected, every cited test
      exists under the name the row gives.
- [ ] Every new guard planted, watched to fail, restored, stated per guard.
- [ ] Every touched module under 200 lines; every new test file under 200 lines.
- [ ] `make ci` exit 0, sixteen steps, 100.00 % coverage, with no `# pragma: no cover` added
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
| *to be filled by the builder* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *to be filled by the builder*

**Contradictions found between a law and this spec:** *to be filled by the builder*

**Laws found silent where a decision was needed:** *to be filled by the builder*

**Clauses that were ⬜ and are now proven:** *to be filled by the builder*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | *to be filled by the builder* | | | |
| A2 | | | | |
| A3 | | | | |
| A4 | | | | |
| A5 | | | | |
| A6 | | | | |
| A7 | | | | |
| A8 | | | | |
| A9 | | | | |
| A10 | | | | |
| A11 | | | | |
| A12 | | | | |
| A13 | | | | |
| A14 | | | | |
| A15 | | | | |
| A16 | | | | |
| A17 | | | | |
| A18 | | | | |
| A19 | | | | |
| A20 | | | | |
| A21 | | | | |
| A22 | | | | |
| A23 | | | | |
| A24 | | | | |
| A25 | | | | |
| A26 | | | | |
| A27 | | | | |
| E1 | | | | |
| E2 | | | | |

**Tests added beyond the plan:** *to be filled by the builder*

---

## Closeout — evidence

**Status:** *to be filled by the builder*

**Tree the proofs ran in (and `.env` present?):** *to be filled by the builder*

**Result:** *to be filled by the builder*

**Files changed:** *to be filled by the builder*

**Proof — the red run first:** *to be filled by the builder*

**Proof — the green run:** *to be filled by the builder*

**Guards planted:** *to be filled by the builder, one line a break*

**The handback checklist's four outputs:** *to be filled by the builder: the scope command, the diff stat, the 17 blob ids, the pragma search*

**Module line counts:** *to be filled by the builder*

**`make ci`:** *to be filled by the builder: the file it was redirected to, the exit code, passed and skipped, coverage, dependency audit, detect-secrets*

**`make gate-ran`:** owed by the planner if the sandbox has no network; say so.

**Not met / verified failing:** *to be filled by the builder*

---

## Return notes

- *to be filled by the builder*

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
