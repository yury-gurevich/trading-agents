<!-- Agent: planning | Role: sprint handover -->
# Sprint 260 — Four debates at once lose no reply at one request a pass, and the repo can show it at no cost

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-260-debates-at-once-lose-no-reply-and-the-repo-can-show-it`
**Status:** BUILT — local memory proof; dependency audit and live transport NOT RUN
**Version:** *next available MINOR at merge*
**Effort:** M
**Decisions:** [DL-279](../design-log.md) (decisions D1 to D9 this sprint builds) ·
[DL-277](../design-log.md) (the measurement that traced September's lost replies, and the plan) ·
work-queue **113**

> **Why this bump kind.** The repository gains a tool it did not have: a command that runs the
> production debate manager and debaters at several debates at once and says whether a reply was lost.
> One argument is added to one shipped class and changes nothing when it is not passed.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report, never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here, all in the deliberator's book: **`DLIB-IDM-04`** (a request is settled when a
peer takes it, and a peer takes one at a time), **`DLIB-OBS-04`** (each `DeliberationRun` records its
orphaned peer replies), **`DLIB-NEV-06`** and **`DLIB-FAIL-01`** (a failed peer call fails its order
open and is never hidden), **`DLIB-DEP-02`** (the bus carries manager-to-peer requests and replies).

### The rule

1. **Before writing code**, read every law file in the map below, whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides what this sprint owes.
5. **Write the Law reading record** (at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row (take the next free number).
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**The planner's answer: No.** No file in `contracts/` changes. The deliberator promises nothing new:
its peer client gains one optional constructor argument, and with the argument absent every call
behaves as it does today. The harness is tooling; no agent's book governs it. Edit no law book.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/deliberator/servicebus_peer_client.py` (the one shipped file) | `agents/deliberator/laws/laws.md` and `test-plan.md`, whole; `docs/laws/conventions.md` | `DLIB-DEP-02`, `DLIB-OBS-04`, `DLIB-NEV-06`. The new argument must leave each of them as it is: the orphan count, the fault it writes and the fail-open on a missed reply do not move |
| `scripts/debate_lanes*.py` and their tests | `docs/laws/conventions.md`; the deliberator's book for what the harness reads | No book governs tooling. The harness reports what `DLIB-IDM-04`, `DLIB-OBS-04` and `DLIB-FAIL-01` promise, so a test that asserts one of those behaviours cites the clause beside DL-279 |

🚨 **Nothing under these paths may change, not a law book, not a test, not a comment:**
`agents/scanner/`, `agents/analyst/`, `agents/portfolio_manager/`, `agents/provider/domain/`,
`agents/execution/order_tolerance.py`, `contracts/`, `orchestration/packs/`,
`orchestration/history_window.py`. They are the fidelity check's decision paths: a changed file under
any of them restarts a count that takes weeks to accumulate. If the suite cannot pass without touching
one, stop and report.

⚠️ **The harness observes; it never changes what the manager or a debater sends.** Everything between
the transport and the canned model is the repository's own code, called as the fleet calls it. If a
number can only be produced by changing `kernel/` or `agents/deliberator/` beyond the one argument of
D2, stop and report.

---

## Goal

At merge, `uv run python scripts/debate_lanes.py` runs the production manager
(`review_pm_node` with `ServiceBusPeerClient` and its reply inbox) and the production debaters
(`DeliberatorAgent` served by `serve_once` over `AzureServiceBusRequestConsumer`) at a chosen number
of debates at once, with a canned model and a stand-in bus, in a worktree with no `.env` and no
network. It prints one report for each configuration and exits 0 only when every order was really
debated and no reply was lost. Four tests hold the result: four debates at once are clean at the
setting the fleet runs, and the same run with the September setting fails open. The same command can
run over three disposable topics on a real Service Bus namespace.

## Why (context)

A night with more debated buys than fit in execution's 30-minute wait places none of them
(work-queue 113): about 7 on `gpt-5.5` today, and five nights on record approved 9 or more. Debates
side by side were built in September (S172) and left switched off after one fleet run at four at once
lost six replies and failed two of fifteen orders open; a second run was clean and the cause was not
found. On 2026-10-08 the planner traced it at no cost ([DL-277](../design-log.md)): a debater that
found requests waiting took up to ten and served them one after another while the other replicas
idled, so a request at the back outlasted the manager's wait. S256 changed that number to one, for
another reason, and it has been on the fleet since `s257`.

What is missing is proof on the production manager and debaters together, kept in the repository.
The apparatus for the September runs was lost twice ([DL-145](../design-log.md)), and yesterday's
scripts measured the request side alone. This sprint does not switch anything on: the pack keeps the
dial at 1, and the fleet proof that follows is paid and is the operator's call.

### Measured, 2026-10-09 — read these before designing

Measured in the main checkout at `main` `4e49f45c`. The prototype is on no branch; it is the Appendix.
"Memory" is an in-process stand-in for the bus; "live" is three disposable topics on the fleet's
namespace, read with the main checkout's `.env`, before that morning's scheduled run began.

| Claim | Value | How it was measured |
| --- | --- | --- |
| What runs when the dial is above 1 | `review_approved_orders` gives each order a thread; every thread calls `ServiceBusPeerClient.debate_turn`; `ServiceBusReplyInbox` hands each reply to the wait that asked for it by correlation id; a debater replica is `serve_once` over `AzureServiceBusRequestConsumer`, taking `receive_max_messages` requests a pass (default 1 since S256) | *[measured, read whole]* `agents/deliberator/review_batch.py`, `servicebus_peer_client.py`, `servicebus_reply_inbox.py`, `kernel/bus_azure_receiver.py`, `kernel/serve_loop.py` |
| Where the dial stands | the code's default is 4, the pack sets 1, and the deploy script gives each debater as many replicas as the pack's value | *[measured, read]* `agents/deliberator/settings.py` `debate_concurrency`; `orchestration/packs/trading_tunables.json` `DELIBERATOR_DEBATE_CONCURRENCY`; `infra/deploy-agents.ps1` `Get-AppMaxReplicas`, `Get-AppDesiredReplicas` |
| Who may ask a debater for a turn | one caller, `deliberator-manager`, matched exactly | *[measured, read]* `contracts/deliberator.py` `_turn_capability`; `kernel/bus.py` `caller_authorized` |
| What follows for a harness | its manager must be `deliberator-manager`. The manager's reply topic is its identity followed by `reply_topic_suffix`, a setting, so the suffix is what makes that topic disposable; the debaters' identities are settings too | *[measured, read and run]* `ServiceBusPeerClient._read_live_ready_event`; `AzureServiceBusRequestConsumer._response_topic`; the live rows below |
| What can be supplied to the manager's client | its reply receiver (`reply_receiver=`), not its publisher: `__init__` builds `AzureServiceBusBus(settings=...)` itself. The debaters' consumer takes both | *[measured, read]* `servicebus_peer_client.py` lines 40 to 61; `bus_azure_receiver.py` lines 53 to 72 |
| Memory, four at once, four replicas up 0.3 s late, 1 request a pass | 10 runs of 10 the same: **4 of 4 debated, 0 failed open, 0 replies nobody took**, round 1's four defender turns served by **4** replicas | *[measured]* Appendix, `memory ci 10`, first configuration |
| The same with 10 requests a pass | 10 runs of 10 the same: **2 of 4 failed open** (`no deliberator peer reply received`), **2 replies nobody took** (1 dead-lettered as an orphan, 1 left unread), the four defender turns served by **1** replica, 1 turn started after its caller had given up | *[measured]* second configuration |
| Four at once and one replica, 1 a pass | 10 of 10: 2 of 4 failed open, 2 replies nobody took | *[measured]* third configuration |
| One at a time | 10 of 10: 4 of 4 debated, effective lanes 1.00, a reply picked up in under 0.001 s | *[measured]* fourth configuration |
| Memory, 8 orders, 2 rounds, turns of 0.5 s, replicas polling before the manager starts | at 1, 2, 3 and 4 at once: all clean; effective lanes **1.00, 1.39, 1.89, 2.30** | *[measured]* `memory warm` |
| Why lanes fall short of the count at short turns | a reply taken by a sibling's receive call is kept for its owner, who sees it when its own receive call returns: up to `REPLY_RECEIVE_SLICE_SECONDS`, 1.0 s. At four at once the pickup's median is 0.5 s and its largest 1.0 s; at one at once it is 0 | *[measured and read]* `reply_pickup_s` in the same runs; `servicebus_reply_inbox.py` |
| Memory, 16 orders, 2 rounds, turns of 0.02 s, four at once | 25 runs of 25 clean: 1,600 turns, no exception from the in-memory graph under 12 threads | *[measured]* `memory stress 25` |
| The first guided turn in a fresh process | 2.36 s, the import of DSPy; the next takes 0.02 s. Before the prototype warmed up, a first run failed every order on it | *[measured]* timed around `warm_up()` |
| Live, two at once, 2 orders, 1 round, turns of 3 s | clean; a request reached its replica in 0.7 to 0.8 s and a reply reached the manager in 1.6 s | *[measured]* `live live-smoke`, 35 s, three topics created and deleted |
| Live, four at once, replicas up 3 s late, turns of 8 s, a wait of 20 s, 1 a pass | clean, 4 replicas served the first four turns | *[measured]* `live live-late`, first configuration |
| The same live with 10 a pass | **2 of 4 failed open, 2 replies nobody took**, one replica served all four: the September failure, and the same counts as the memory run | *[measured]* second configuration |
| Live, 4 orders, 2 rounds, turns of 10 s | one at once: clean, 16 turns in 186.6 s, effective lanes 0.86. Four at once: clean, the same 16 turns in **48.8 s**, effective lanes **3.28**, each of the eight replicas serving two turns: **3.8 times faster**. A request reached its replica in 0.7 to 0.9 s; a reply reached the manager in 0.8 s at the median and 2.8 s at most | *[measured]* `live live-lanes` |
| The fleet's three debate subscriptions during the live runs | unchanged: read before and after each configuration | *[measured]* the `teardown` line of each live report |
| What the gates read under `scripts/` | module size and module header: yes. Coverage and `mypy`: no (`source` and `PKGS` list `kernel contracts agents orchestration surfaces`). `agents/deliberator/` is under the 100.00 % floor | *[measured, read]* `Makefile`, `pyproject.toml` |
| Module size | `agents/deliberator/servicebus_peer_client.py` **181** | *[measured]* `wc -l` |
| That the new argument breaks no existing test | *[ASSUMED]* it is a keyword argument with a default; the suite was not run with it | B1 settles it; any test that needs an edit is a finding |
| That the venv CI builds has no Azure SDK | *[ASSUMED from the lock's extras, not re-read today]* | A10 settles it either way: it asserts the import is lazy, not that the SDK is absent |

**Not measured here, and not claimed:** Postgres as the claim-check store, containers scaling out to
several replicas, and the vendor's rate limit with several calls in flight. Those are the fleet proof.

### What the command reports

One JSON object for each configuration. The prototype prints the same quantities under shorter keys.

| Field | Meaning |
| --- | --- |
| `transport`, `concurrency`, `replicas`, `orders`, `rounds`, `turn_seconds`, `wait_seconds`, `replica_start_delay_seconds`, `requests_a_pass` | the configuration as run; `requests_a_pass` is the number the debaters' settings held |
| `real_debate_count`, `failed_open_count`, `failed_open_reason`, `orphaned_reply_count` | read from the `DeliberationRun` the manager wrote |
| `replies_nobody_took` | `orphaned_reply_count` plus the replies still unread on the manager's reply subscription at the end |
| `mismatched_replies` | manager calls whose reply carried another request's id |
| `turns_asked`, `turns_served`, `turns_served_twice` | calls the manager made; requests a replica served; request ids served more than once |
| `turns_answered_for_nobody`, `turns_started_after_caller_gave_up` | served turns that ended after their caller had stopped waiting; of those, the ones that also started after |
| `first_wave_replicas` | how many different replicas served round 1's defender turn of the first `concurrency` orders |
| `by_replica` | served turns for each replica |
| `span_seconds`, `served_work_seconds`, `effective_lanes` | the manager's wall time for the batch; the sum of the replicas' serving time; the second divided by the first |
| `request_wait_seconds`, `reply_pickup_seconds` | median and largest, over answered turns: from the manager's call to the replica starting; from the replica finishing to the manager's call returning |
| `subscriptions` | messages left, and messages dead-lettered, on each of the three subscriptions |
| `errors`, `faults` | exceptions that ended a replica's loop; faults submitted, counted by type |
| `production_unchanged` | live only: the fleet's three debate subscriptions hold what they held before |
| `clean` | the rule of D3 |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first (A1, A2, A7).**
2. **The one argument** on `ServiceBusPeerClient` (D2).
3. **The harness**: the scene that builds the production manager and debaters, the two observers, the
   canned model, the report and its rule, and the memory transport (D1, D3 to D5, D7, D8).
4. **The live transport** (D6), ported from the Appendix. You cannot run it; say so.
5. **The command** (D9).

### Out of scope (do NOT build this sprint)

- **Turning the dial.** `orchestration/packs/` does not change, and no default changes.
- **Any file under a fidelity decision path** (the list under the MUST RULE).
- **`kernel/`.** Nothing there changes. The stand-in bus lives with the harness.
- **The reply pickup of up to one second, a time to live on a request, and a verdict applied per
  order.** The harness measures the first two; fixing any of the three is its own item.
- **`infra/`, the workflows, `docs/STATE.md`.**
- **`pyproject.toml` and `uv.lock`.** The planner bumps the version at merge.
- **The live run, the merge and the push.** Commit on the branch and hand back.

### The road not taken (LAW-06)

- **Keep the scripts outside the repository.** Rejected: the September apparatus was lost twice.
- **A harness that only runs live.** Rejected: the builder has no network, CI could not hold the
  result, and the September setting could be put back with nothing going red.
- **Stand-in manager or debaters**, as S172's `DelayedPeer` tests use. Rejected: they bypass the reply
  inbox and the request consumer, which is where the replies were lost.
- **Set the client's private publisher from outside.** Rejected: its receiver can already be supplied
  through the constructor; the publisher gets the same door.
- **A process for each replica.** Rejected for this sprint: processes need a shared graph, which means
  Postgres, which means writes to the production spine and a teardown. Threads over one in-memory
  graph cost nothing. What that leaves unmeasured is listed above.
- **Judge the lanes.** Rejected: at a canned turn of a second the one-second pickup dominates, so a
  floor would be a number about the harness. Lanes are reported.
- **A harness manager under its own name.** Rejected: the capability admits `deliberator-manager`
  alone, and that list is in `contracts/`, a fidelity decision path.

---

## The design decisions — made, and recorded in DL-279

**Build them as written.** Record in `docs/design-log.md` (take the next free number) only a decision
the spec did not make, or a place where you had to depart from one of these, with the reason.

| # | Decision | Rejected |
| --- | --- | --- |
| D1 | **The harness lives under `scripts/`**, entry point `scripts/debate_lanes.py`, with its parts in modules beside it (`debate_lanes_*.py`), each under 200 lines, each with the `Agent:` / `Role:` / `External I/O:` header (`Agent: tooling`). Its tests live under `tests/`. It ships in no image | under `agents/deliberator/`: it would ship in three images |
| D2 | **`ServiceBusPeerClient.__init__` takes `bus=None`.** When given, it is the bus the client publishes its request events on; when absent, the client builds `AzureServiceBusBus(settings=...)` as today. Nothing else in the class changes | see the road not taken |
| D3 | **`clean` is true when all of these hold:** `real_debate_count` equals `orders`; `failed_open_count` is 0; `replies_nobody_took` is 0; `mismatched_replies` is 0; `turns_served_twice` is 0; `errors` is empty; and, live, `production_unchanged` is true. The rule is one pure function over the report | judging lanes: see the road not taken |
| D4 | **The canned model** waits `turn_seconds` and then answers a debater's turn in the guided format with empty readings; asked for a verdict (the prompt starts with `DECISION UNDER TEST`) it answers `uphold` at once. It imports no vendor library and needs no key | recorded real completions: nothing here reads the text |
| D5 | **One configuration is built like this.** A fresh in-memory graph with one `PMRun` of `orders` approved buys. The manager is a `DeliberatorAgent` with role `manager` and the default identity, `max_rounds` = `rounds`, `debate_concurrency` = `concurrency`, and the two debater identities the transport names. Its peer client is a `ServiceBusPeerClient` with `timeout_seconds` = `wait_seconds`. Each replica is a thread: its own `InProcessBus`, its own bound `DeliberatorAgent` (role `proponent` or `opponent`, `instance_name` the transport's identity), its own request consumer from the transport, and a loop of `serve_once` that ends when told to stop. `replicas` of each role; the default is `concurrency`, the deploy script's rule. `review_pm_node` is called once. The memory transport's settings pass `connection_string=None` and `connection_strings_json=None` explicitly, so a connection string in the environment cannot send anything. `requests_a_pass` is passed to the settings only when the argument is given; left out, the settings' own default applies, so A1 also guards that default | a `PeerClient` of the harness's own |
| D6 | **The live transport** makes three topics, each with a subscription `agent`, from a fresh random run id: `<run>-proponent.requests`, `<run>-opponent.requests` and `deliberator-manager.<run>.reply`, the last by setting `reply_topic_suffix` to `.<run>.reply`. It refuses, before creating anything, when a name is one of the fleet's three topics or does not hold the run id. It reads the fleet's three subscriptions (`deliberator-manager.reply`, `deliberator-proponent.requests`, `deliberator-opponent.requests`, subscription `agent`) before and after and reports `production_unchanged`; one it cannot read is reported as unreadable and does not fail the run. It deletes its topics in a `finally` and reports each. The Azure SDK is imported inside its functions, never at module import. Each configuration gets its own three topics | reusing topics across configurations: a late reply of one would be an orphan of the next |
| D7 | **Observation is two wrappers and nothing else.** One stands in front of each replica's bus and records, for every request served, the request id, the replica, and when serving started and ended. One stands in front of the manager's peer client and records, for every call, the request id, when it was made and returned, and whether it was answered, answered with another request's id, or raised. Neither changes a message | reading timings out of the prompt or the transcript |
| D8 | **Timing.** One guided turn is run before anything is measured, so DSPy's import is outside the span. With no start delay, the manager starts only after every replica has finished one poll. With a start delay, the replicas start that many seconds after the manager. After the manager returns, the harness waits `min(2 x turn_seconds + 0.3, 12)` seconds before stopping the replicas, so a turn nobody waits for can finish and be counted | starting the clock at process start |
| D9 | **The command.** `--transport memory` (default) or `live`; `--concurrency` one or more integers, a configuration for each; `--replicas` (default: the concurrency); `--orders` (default 8); `--rounds` (default 2); `--turn-seconds` (default 0.5); `--wait-seconds` (default 5); `--replica-start-delay` (default 0); `--requests-a-pass` (default: not passed). It prints one JSON object a line for each configuration, then one line: `LANES CLEAN` or `LANES NOT CLEAN` with the concurrencies that were not. Exit 0 when every configuration is clean, 1 when one is not, 2 when it could not run: a bad argument, `live` with no connection string, or a refused topic name | a table for people: the JSON is what a later run is compared with |

---

## Blast radius — measured 2026-10-09

| What | Detail |
| --- | --- |
| Files changed | `agents/deliberator/servicebus_peer_client.py` **181** (one argument); new `scripts/debate_lanes.py` and `scripts/debate_lanes_*.py`; new tests under `tests/`, and the test of D2 under `agents/deliberator/tests/` or `tests/` |
| Agents affected | the deliberator's peer client gains an argument nothing in the fleet passes. No agent imports another |
| Contract change? | no |
| Graph vocabulary change? | no |
| New env keys / tunables | none |
| Deploy implication | none owed. The changed deliberator module rides the next retag; `agents/deliberator/` is not a fidelity decision path, and `scripts/` ships in no image |
| Rollback | revert the commit. Nothing is deployed, and the live transport deletes what it creates |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Run the Appendix prototype** as its first lines say. Its four `memory ci` reports must carry the
   counts of the Appendix's table. If they do not, stop and report.
3. **Plant the failing tests first** (A1, A2, A7) and watch them fail. Paste the red output.
4. **Implement** D1 to D9.
5. **Prove the guards can fail (DL-70):** break each guarded property, watch the guard go red, restore.
6. **Run the four timed tests twenty times in a row** and state the count that passed.
7. **`make ci`**, every step of the `ci:` target, **redirected to a file, never piped**. Name any step
   your sandbox cannot run as NOT RUN.
8. **Fill the handback sections** at the bottom of this file and set Status to `BUILT`, here and in
   this sprint's `README.md` row.

---

## Test plan

A1 to A4 run the built harness on the memory transport, with real threads and real waits: the timings
are chosen so that each asserted count has at least 0.8 s of margin. Assert the counts named here and
no timing beyond them.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 Four debates at once lose no reply | memory; concurrency 4, replicas 4, orders 4, rounds 1, turns of 1.0 s, a wait of 2.5 s, replicas started 0.3 s after the manager, `requests_a_pass` not passed | `clean` is true; 4 of 4 really debated; 0 failed open; 0 replies nobody took; 0 mismatched; no turn served twice; `first_wave_replicas` is 4; the report says the debaters took 1 request a pass |
| A2 | 🪤 The September setting loses them | the same with `requests_a_pass` 10 | `clean` is false; `first_wave_replicas` is 1; `failed_open_count` at least 2 and the reason names `no deliberator peer reply received`; `replies_nobody_took` at least 2; `turns_started_after_caller_gave_up` at least 1 |
| A3 | 🪤 Four lanes need four replicas | concurrency 4, replicas 1, no start delay, the rest as A1 | `clean` is false; `failed_open_count` at least 2; `first_wave_replicas` is 1 |
| A4 | One debate at a time | concurrency 1, replicas 1, no start delay, the rest as A1 | `clean` is true; `effective_lanes` between 0.8 and 1.1; the largest reply pickup under 0.5 s |
| A5 | 🪤 A reply that answers another request is counted | the manager-side observer around a stub client that returns a reply carrying another request's id | `mismatched_replies` is 1 and `clean` is false |
| A6 | 🪤 Each term of the rule alone makes a run not clean | the rule of D3 over a clean report, then with one term changed at a time: one order failed open; one order not really debated; one reply nobody took; one mismatched; one turn served twice; one error; `production_unchanged` false | true for the first, false for each of the seven |
| A7 | 🎯 The manager's publisher can be supplied | `ServiceBusPeerClient` built with `bus=` a recording bus and a reply receiver that answers | the request's ready event is published on the supplied bus, on the debater's request topic; built with no `bus`, the client holds its own `AzureServiceBusBus` |
| A8 | The command | `main` with memory arguments for one clean configuration, for A2's configuration, and with a bad argument | one JSON line a configuration holding every field of the report table, then the verdict line; return values 0, 1 and 2 |
| A9 | 🪤 The live transport cannot name a fleet topic | the pure function that names the three topics for a run id, and the guard | each name holds the run id; the guard raises for each of the fleet's three topics and for a name without the run id; `main` with `--transport live` and no connection string returns 2 and creates nothing |
| A10 | 🪤 The live module imports without the Azure SDK | import the live transport's module | the import succeeds and no module named `azure.servicebus` is in `sys.modules` because of it |
| B1 | 🪤 The existing tests | the whole suite | every existing test passes with no edit |

No test may skip when a dependency is missing. A skipped proof is not a proof.

---

## Success factors

- [x] On the memory transport four debates at once are clean with the settings' own default (A1), and
      the same run with ten requests a pass fails open and is reported not clean (A2).
- [x] Too few replicas (A3), a mismatched reply (A5) and each term of the rule alone (A6) are reported
      not clean.
- [x] `ServiceBusPeerClient` publishes on a supplied bus and is unchanged without one (A7); no
      existing test is edited (B1).
- [x] The command prints the report and returns 0, 1 or 2 as D9 says (A8).
- [x] The live transport refuses a fleet topic name and imports without the Azure SDK (A9, A10); the
      handback says plainly that it was not run.
- [x] The four timed tests pass twenty times of twenty.
- [x] Nothing under a fidelity decision path, `kernel/`, `orchestration/`, `infra/`, `pyproject.toml`
      or `uv.lock` is touched; in `agents/` only `agents/deliberator/servicebus_peer_client.py` and,
      if you put A7 there, one new test file.
- [x] Every new guard planted, watched to fail, restored, stated per guard.
- [x] Every touched module < 200 lines.
- [x] `make ci` exit 0, 100.00 % coverage, or each step that could not run named as NOT RUN.

---

## Traps

🪤 **The manager must be `deliberator-manager`.** A debater refuses any other caller. Do not widen the
capability: it is in `contracts/`. The reply topic is made disposable by the settings' suffix (D6).
🪤 **A fresh process pays 2.4 s on its first guided turn.** Without the warm-up of D8 the first order
fails open on the wait and every count is wrong.
🪤 **The timed tests wait for real.** They take about 30 s together. Do not shorten the turn to speed
them up: at turns of 0.5 s the margins fall under half a second and a busy runner will fail them. Do
not mock the clock either: the code under test reads `time.monotonic` and blocks in a receive call.
🪤 **A late reply is counted in one of two places.** It is dead-lettered as an orphan when another wait
is still receiving, and left unread on the subscription when none is. Read both, after the wait of
D8, or A2's count is one short on some runs.
🪤 **The stand-in bus must behave like the real one where it matters:** a message goes to exactly one
receiver; a receive call returns at once with what is queued, up to the count asked for, and
otherwise waits up to its timeout for the first message. The live run with ten a pass gave the same
counts as the prototype's stand-in.
🪤 **A connection string in the environment must not reach the memory transport** (D5). The planner
runs the command from a checkout that has one.
🪤 **Threads share one in-memory graph.** The prototype ran 1,600 turns that way with no exception.
If you see one, report it; do not add a lock to `kernel/`.
🪤 **`ruff` reads `scripts/` and `tests/`; `mypy` and coverage do not read `scripts/`.** The one
shipped line is under the 100.00 % floor: A7 must cover both of its branches.
🪤 **The Appendix sets a private attribute** (`client._bus`). That line is what D2 replaces; do not
carry it into the harness.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` beyond the import-order ones
  a script's entry point needs after it puts the repository root on `sys.path`.
  📌 Current size: `agents/deliberator/servicebus_peer_client.py` **181**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: `kernel.tunable(..., why=...)` with bounds. This sprint adds no tunable; the
  harness's numbers are its arguments.
- Faults, not silent failure.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- Secrets never through the worktree. A worktree has **no `.env`**, and nothing you run needs one.
  **State which tree you ran in.**

---

## Sequencing after merge

Owed by the planner, in this order:

1. **Before the handover:** the worktree `../ta-s260` cut from `main`, its venv synced, and the
   Appendix prototype run there.
2. Review against the checklist; the planner's own run of the four configurations and of the
   command; **the live run before the merge** (one to four at once on disposable topics); the MINOR
   bump and `uv lock`; Windows `make ci`, all steps; push the branch; **`make gate-ran` exits 0** from
   the worktree whose `HEAD` is the commit being proven; the branch's open CodeQL alerts compared with
   `main`'s.
3. Merge, the tag.
4. **F1, no cost.** On the merged `main`, live: one to four at once, 8 orders, 2 rounds, turns of
   20 s, the fleet's wait of 240 s; then four at once with ten a pass and late replicas, which must
   read not clean. Recorded in `docs/laws/functionality-checks.md`; the topics deleted.
5. **No deploy.**
6. **Then the operator's call:** one paid proof on the fleet at three at once
   ([DL-277](../design-log.md), step 2).

---

## Handover — paste this to Codex

```text
Sprint 260 — four debates at once lose no reply at one request a pass, and the repo can show it at no
cost. Spec: docs/sprints/sprint-260-debates-at-once-lose-no-reply-and-the-repo-can-show-it.md (read
ALL of it, then CLAUDE.md). Repo: yury-gurevich/trading-agents, local checkout.

Your worktree already exists: ../ta-s260, on branch
sprint-260-debates-at-once-lose-no-reply-and-the-repo-can-show-it, cut from main, with its venv synced
to the lock. Work only there, never in the main checkout and never on main. You have no .env and no
network: every proof is a unit test or a run of the command on its memory transport. `uv run` is safe;
never run a bare `uv sync`. Do not touch pyproject.toml or uv.lock, and say so: the planner bumps the
version at merge. Do not push and do not merge: commit on the branch and hand back. Do not edit
docs/STATE.md: put intent and results in the spec's Closeout. If a make ci step cannot run in your
sandbox (the dependency audit needs the network), do not bypass it silently: name the step as NOT RUN
in the handback.

This handover is complete: nobody will send you follow-up messages. Two tiers:
- A wrong command, count, path, test name or clause number whose intent is plain from the spec's Scope
  and Success factors is NOT a reason to stop: follow the intent, record the correction in Return
  notes, continue.
- STOP and report, without improvising, when: the Appendix prototype does not print the counts of its
  table in your worktree; a number can only be produced by changing kernel/ or agents/deliberator/
  beyond the one constructor argument of D2; an EXISTING test has to be edited; or the suite cannot
  pass without changing a file under agents/scanner/, agents/analyst/, agents/portfolio_manager/,
  agents/provider/domain/, contracts/, orchestration/packs/, orchestration/history_window.py or
  agents/execution/order_tolerance.py.

What and why: debates side by side were built in September (the manager's debate_concurrency) and left
switched off after one fleet run at four at once lost replies and failed orders open. The planner
traced that to a debater taking up to ten waiting requests and serving them in turn; sprint 256 made
it one. Nothing in the repository runs the production manager and debaters together at more than one
debate, so nothing would go red if the old setting came back. This sprint commits that harness. It
switches nothing on.

MUST RULE before any code: read, whole, agents/deliberator/laws/laws.md and its test-plan.md,
docs/laws/conventions.md, docs/laws/drift-register.md, and DL-279 and DL-277 in docs/design-log.md.
Fill the Law reading record first. Law-cycle answer: NO. No contracts/ file and no new guarantee.
Edit no law book.

Order (the spec's Steps): laws -> run the Appendix prototype (copy its block to
.tools/s260/prototype.py, then `uv run python .tools/s260/prototype.py memory ci` from the worktree
root) and compare its four reports with the Appendix table -> plant A1, A2 and A7, watch them fail,
paste the red -> implement -> break and restore every guard -> the four timed tests twenty times ->
make ci to a file.

Build (decisions D1-D9 are made; build them as written):
1. agents/deliberator/servicebus_peer_client.py: one optional constructor argument, bus=None (D2).
   Nothing else in agents/ or kernel/ changes.
2. scripts/debate_lanes.py and modules beside it: the scene (D5), the canned model (D4), the two
   observers (D7), the timing rules (D8), the report and its rule (D3, and the report table), the
   memory transport, the live transport (D6), the command (D9). Each module under 200 lines with the
   Agent / Role / External I/O header.
3. Tests A1-A10 and B1 from the spec's Test plan.
The Appendix is a working prototype of all of it in one file. Port it; do not carry over its
`client._bus = ...` line, which D2 replaces.

DO NOT: change orchestration/packs or any default; change contracts/ or widen who may call a debater;
add a lock or anything else to kernel/; shorten the timed tests' turns or mock the clock; judge the
lanes; import the Azure SDK at module import; run or claim the live transport; pin a version number.

Handback checklist (the handback is returned against these, one by one):
 1. Law reading record filled before the first code change.
 2. The Appendix prototype's four `memory ci` reports from your worktree, pasted, and a line saying
    their counts equal the Appendix table's.
 3. The red output of A1, A2 and A7 pasted, from before the implementation.
 4. Test plan results: one row for each of A1-A10 and B1, with file and status.
 5. Every guard's break-and-restore stated, one line per guard. At least: each term of the rule (A6);
    the reply-id comparison (A5); requests_a_pass not reaching the settings (A2); the start delay
    ignored (A2); the fleet-name guard (A9); the supplied bus ignored (A7).
 6. The four timed tests run twenty times in a row: the command and the count that passed.
 7. Pasted whole, with the exit code of each:
    uv run python scripts/debate_lanes.py --concurrency 1 2 3 4 --orders 8 --rounds 2 --turn-seconds 0.5 --wait-seconds 5
      (expected: four clean reports, exit 0)
    uv run python scripts/debate_lanes.py --concurrency 4 --orders 4 --rounds 1 --turn-seconds 1 --wait-seconds 2.5 --replica-start-delay 0.3 --requests-a-pass 10
      (expected: not clean, exit 1)
 8. This prints nothing, and you say so:
    git diff main --stat -- agents/scanner agents/analyst agents/portfolio_manager agents/provider/domain agents/execution/order_tolerance.py contracts orchestration infra kernel pyproject.toml uv.lock docs/STATE.md
    and this names agents/deliberator/servicebus_peer_client.py and at most one new test file:
    git diff main --stat -- agents
 9. Every EXISTING test you edited, named, with the reason. The expected answer is none.
10. make ci output file named, exit code stated, every NOT RUN step named with its reason.
11. Module line counts for every touched or new module; Status BUILT here and in the README row.
12. One line saying the live transport was NOT RUN, and anything in it you are unsure of.
State anything not met as "not done" or "verified failing". Never write a Result for work not done.
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
| `ServiceBusPeerClient.__init__` | `agents/deliberator/laws/laws.md` (whole, LOCKED v1.16), its `test-plan.md` (whole), `docs/laws/conventions.md` (whole) | `DLIB-DEP-02`, `DLIB-OBS-04`, `DLIB-NEV-06`, `DLIB-FAIL-01` | No: D2 supplies the publisher only; the existing inbox, faults, correlation and fail-open behavior stay in place. |
| Harness and new tests | the same deliberator book and test plan; `docs/laws/drift-register.md` (whole); DL-279 and DL-277 in `docs/design-log.md` | `DLIB-IDM-04`, `DLIB-OBS-04`, `DLIB-NEV-06`, `DLIB-FAIL-01`, `DLIB-DEP-02` | No: D1-D9 already decide the scene, observation, timing and reporting. The five binding clauses are green in the existing plan; `DLIB-TRG-02`, `DLIB-IN-02` and `DLIB-SEC-03` remain gray, so their entire clauses are not claimed proven here. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** NO. No `contracts/` file changes and no new agent guarantee; no law amendment or rollup change is owed.

**Contradictions found between a law and this spec:** None.

**Laws found silent where a decision was needed:** None needed for D1-D9. No new drift row.

**Clauses that were ⬜ and are now proven:** None. No clause status or law book changes.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | test_four_debates_lose_no_reply | tests/test_debate_lanes_timed.py | PASS | DLIB-IDM-04 / DLIB-OBS-04 |
| A2 | test_september_setting_loses_replies | tests/test_debate_lanes_timed.py | PASS | DLIB-FAIL-01 / DLIB-NEV-06 / DLIB-OBS-04 |
| A3 | test_four_lanes_need_four_replicas | tests/test_debate_lanes_timed.py | PASS | DLIB-FAIL-01 |
| A4 | test_one_debate_at_a_time | tests/test_debate_lanes_timed.py | PASS | DLIB-DEP-02 / DLIB-OBS-04 |
| A5 | test_another_requests_reply_is_counted | tests/test_debate_lanes_reporting.py | PASS | DLIB-NEV-06 |
| A6 | test_each_rule_term_alone_makes_the_report_not_clean (7 cases) | tests/test_debate_lanes_reporting.py | PASS | DLIB-FAIL-01 / DLIB-OBS-04 |
| A7 | test_manager_publisher_can_be_supplied (supplied and absent bus) | tests/test_debate_lanes_peer_bus.py | PASS | DLIB-DEP-02 |
| A8 | test_command_reports_and_returns_the_counted_result; test_bad_argument_returns_two_without_a_report | tests/test_debate_lanes_command.py | PASS | DLIB-FAIL-01 / DLIB-OBS-04; DL-279 |
| A9 | test_disposable_names_hold_the_run_id; test_fleet_or_unrelated_topic_is_refused; test_live_without_connection_string_returns_two_and_creates_nothing | tests/test_debate_lanes_transport.py | PASS | DL-279 (tooling) |
| A10 | test_live_module_imports_with_the_azure_sdk_refused | tests/test_debate_lanes_transport.py; tests/debate_lanes_import_probe.py | PASS | DL-279 (tooling) |
| B1 | whole existing suite without edits | Makefile ci target / pytest testpaths | PASS — 4436 passed, 8 skipped; 100.00% coverage; eight pre-existing skips listed below | existing test citations unchanged |

**Tests added beyond the plan:** D6 synthetic lifecycle/cleanup (`tests/test_debate_lanes_live_lifecycle.py`); D8 actual first-poll completion, manager identity and competing-receiver semantics (`tests/test_debate_lanes_startup.py`); D5 environment isolation and D3 memory without a production-count field; D9 literal command defaults. These hold the specified setup and teardown without adding a production guarantee.

---

## Closeout — evidence

**Intent recorded before the first code change, 2026-10-09:** Work only in `../ta-s260` on the specified sprint branch, initially clean at `main` `10770f91`. Read the complete spec and then this worktree's `CLAUDE.md`, the complete law files above, and DL-279 / DL-277. First reproduce the Appendix table, then record A1/A2/A7 red before D1-D9. Prove each guard by breaking and restoring it, run A1-A4 twenty times, run the two commands and redirected `make ci`, and commit a local handback. Success is the spec's counts and scope checks. Do not change the version/lock, STATE, fidelity paths, kernel, any existing test, or any production default. Live, push, merge and remote proof are not authorized.

**Status:** BUILT — local memory proof; not remotely gated, merged, deployed or live-proven

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/Downloads/project/ta-s260`, branch `sprint-260-debates-at-once-lose-no-reply-and-the-repo-can-show-it`; `.env` absent. Original base `10770f91bf531eda99cc105f8e80abdfe22fabb0`. The law-reading and intent record was committed as `2fe980679286ad34661f9e605560e56af7f4e0eb` before code. All runs used `UV_OFFLINE=1`; a gitignored proof guard allowed loopback IPC and refused external DNS/TCP/UDP. CI additionally stopped pip-audit immediately when it attempted external I/O, and prohibited HTTP/HTTPS git fetching. No saved advisory report substituted for the audit.

**Result:** The repository now runs the production manager and debaters together on a competing memory bus and reports the durable counts, timing, request/reply identity and loss. Four concurrent debates complete cleanly at the settings' own one-request default; the ten-request reproduction records two real debates, two fail-opens and two untaken replies. The two required commands returned 0 and 1 respectively. All 34 guard plants failed and passed after restoration; A1-A4 passed twenty consecutive times (80/80). The whole suite passed without any existing test edited, at 100.00% coverage. This is local BUILT proof; the dependency audit did not complete and the live transport was NOT RUN.

**Files changed:** `agents/deliberator/servicebus_peer_client.py` (only the optional constructor bus and its type import); `scripts/debate_lanes.py`, `debate_lanes_live.py`, `debate_lanes_memory.py`, `debate_lanes_model.py`, `debate_lanes_observers.py`, `debate_lanes_report.py`, `debate_lanes_scene.py`; `tests/test_debate_lanes_command.py`, `test_debate_lanes_live_lifecycle.py`, `test_debate_lanes_peer_bus.py`, `test_debate_lanes_reporting.py`, `test_debate_lanes_startup.py`, `test_debate_lanes_timed.py`, `test_debate_lanes_transport.py`, `debate_lanes_import_probe.py`; this spec, `docs/design-log.md`, `docs/sprints/README.md` and `docs/sprints/INDEX.md`.

**Design decisions:** [`DL-279`](../design-log.md) and D1-D9 remain the binding choices. [`DL-281`](../design-log.md) records the missing default concurrency list as `[1, 2, 3, 4]`, with requiring the flag or defaulting only to four rejected because the bare command is supposed to show one through four. Existing rejected alternatives stay in the spec and DL-279. No contract or new agent guarantee; law-cycle answer remains NO and no law book changed.

**Proof — Appendix before implementation:**

```text
$ uv run python .tools/s260/prototype.py memory ci
{"transport": "memory", "k": 4, "replicas": 4, "orders": 4, "rounds": 1, "turn_s": 1.0, "wait_s": 2.5, "start_delay_s": 0.3, "requests_a_pass": 1, "real_debate_count": 4, "failed_open_count": 0, "failed_open_reason": "", "orphaned_reply_count": 0, "replies_nobody_took": 0, "mismatched_replies": 0, "turns_asked": 8, "turns_served": 8, "turns_served_twice": 0, "turns_answered_for_nobody": 0, "turns_started_after_caller_gave_up": 0, "first_wave_replicas": 4, "by_replica": {"opponent-0": 1, "opponent-1": 1, "opponent-2": 1, "opponent-3": 1, "proponent-0": 1, "proponent-1": 1, "proponent-2": 1, "proponent-3": 1}, "span_s": 4.06, "served_work_s": 8.22, "effective_lanes": 2.02, "request_wait_s": [0.158, 0.343], "reply_pickup_s": [0.683, 1.003], "subscriptions": {"lanes-proponent.requests": {"active": 0, "dead": 0}, "lanes-opponent.requests": {"active": 0, "dead": 0}, "deliberator-manager.reply": {"active": 0, "dead": 0}}, "errors": [], "faults": {}, "clean": true, "teardown": []}
{"transport": "memory", "k": 4, "replicas": 4, "orders": 4, "rounds": 1, "turn_s": 1.0, "wait_s": 2.5, "start_delay_s": 0.3, "requests_a_pass": 10, "real_debate_count": 2, "failed_open_count": 2, "failed_open_reason": "RuntimeError: no deliberator peer reply received", "orphaned_reply_count": 1, "replies_nobody_took": 2, "mismatched_replies": 0, "turns_asked": 6, "turns_served": 6, "turns_served_twice": 0, "turns_answered_for_nobody": 2, "turns_started_after_caller_gave_up": 1, "first_wave_replicas": 1, "by_replica": {"opponent-0": 1, "opponent-3": 1, "proponent-0": 4}, "span_s": 3.52, "served_work_s": 6.07, "effective_lanes": 1.72, "request_wait_s": [0.152, 1.319], "reply_pickup_s": [0.091, 0.697], "subscriptions": {"lanes-proponent.requests": {"active": 0, "dead": 0}, "lanes-opponent.requests": {"active": 0, "dead": 0}, "deliberator-manager.reply": {"active": 1, "dead": 1}}, "errors": [], "faults": {"RuntimeError": 2, "OrphanedPeerReply": 1}, "clean": false, "teardown": []}
{"transport": "memory", "k": 4, "replicas": 1, "orders": 4, "rounds": 1, "turn_s": 1.0, "wait_s": 2.5, "start_delay_s": 0.0, "requests_a_pass": 1, "real_debate_count": 2, "failed_open_count": 2, "failed_open_reason": "RuntimeError: no deliberator peer reply received", "orphaned_reply_count": 1, "replies_nobody_took": 2, "mismatched_replies": 0, "turns_asked": 6, "turns_served": 6, "turns_served_twice": 0, "turns_answered_for_nobody": 2, "turns_started_after_caller_gave_up": 1, "first_wave_replicas": 1, "by_replica": {"opponent-0": 2, "proponent-0": 4}, "span_s": 4.09, "served_work_s": 6.14, "effective_lanes": 1.5, "request_wait_s": [0.256, 1.009], "reply_pickup_s": [0.259, 1.008], "subscriptions": {"lanes-proponent.requests": {"active": 0, "dead": 0}, "lanes-opponent.requests": {"active": 0, "dead": 0}, "deliberator-manager.reply": {"active": 1, "dead": 1}}, "errors": [], "faults": {"RuntimeError": 2, "OrphanedPeerReply": 1}, "clean": false, "teardown": []}
{"transport": "memory", "k": 1, "replicas": 1, "orders": 4, "rounds": 1, "turn_s": 1.0, "wait_s": 2.5, "start_delay_s": 0.0, "requests_a_pass": 1, "real_debate_count": 4, "failed_open_count": 0, "failed_open_reason": "", "orphaned_reply_count": 0, "replies_nobody_took": 0, "mismatched_replies": 0, "turns_asked": 8, "turns_served": 8, "turns_served_twice": 0, "turns_answered_for_nobody": 0, "turns_started_after_caller_gave_up": 0, "first_wave_replicas": 1, "by_replica": {"opponent-0": 4, "proponent-0": 4}, "span_s": 8.16, "served_work_s": 8.13, "effective_lanes": 1.0, "request_wait_s": [0.0, 0.019], "reply_pickup_s": [0.0, 0.002], "subscriptions": {"lanes-proponent.requests": {"active": 0, "dead": 0}, "lanes-opponent.requests": {"active": 0, "dead": 0}, "deliberator-manager.reply": {"active": 0, "dead": 0}}, "errors": [], "faults": {}, "clean": true, "teardown": []}
Exit code: 0
```

All four counted reports equal the Appendix table, including `orphaned_reply_count`; no errors, mismatches or duplicate turns. Times were not compared.

**Proof — the red run first:**

```text
$ uv run pytest --no-cov -q tests/test_debate_lanes_timed.py::test_four_debates_lose_no_reply tests/test_debate_lanes_timed.py::test_september_setting_loses_replies tests/test_debate_lanes_peer_bus.py::test_manager_publisher_can_be_supplied
FFF                                                                      [100%]
================================== FAILURES ===================================
_______________________ test_four_debates_lose_no_reply _______________________
tests\test_debate_lanes_timed.py:13: in test_four_debates_lose_no_reply
    from scripts.debate_lanes_scene import run
E   ModuleNotFoundError: No module named 'scripts.debate_lanes_scene'
____________________ test_september_setting_loses_replies _____________________
tests\test_debate_lanes_timed.py:39: in test_september_setting_loses_replies
    from scripts.debate_lanes_scene import run
E   ModuleNotFoundError: No module named 'scripts.debate_lanes_scene'
___________________ test_manager_publisher_can_be_supplied ____________________
tests\test_debate_lanes_peer_bus.py:37: in test_manager_publisher_can_be_supplied
    peer = ServiceBusPeerClient(
E   TypeError: ServiceBusPeerClient.__init__() got an unexpected keyword argument 'bus'
=========================== short test summary info ===========================
FAILED tests/test_debate_lanes_timed.py::test_four_debates_lose_no_reply - Mo...
FAILED tests/test_debate_lanes_timed.py::test_september_setting_loses_replies
FAILED tests/test_debate_lanes_peer_bus.py::test_manager_publisher_can_be_supplied
3 failed in 7.65s
Exit code: 1
```

**Proof — the green run:**

```text
$ $testPaths = @(Get-ChildItem -Path tests -Filter 'test_debate_lanes*.py' | ForEach-Object { $_.FullName }); uv run pytest --no-cov -q @testPaths
...........................................                              [100%]
43 passed in 48.28s
Exit code: 0

$ uv run pytest --no-cov -q tests/test_debate_lanes_command.py::test_bad_argument_returns_two_without_a_report tests/test_debate_lanes_startup.py tests/test_debate_lanes_transport.py::test_live_module_imports_with_the_azure_sdk_refused
14 passed in 14.44s
Exit code: 0

The additional manager-identity refusal test passed after its guard was restored (guard 32); the final whole-suite count is recorded below.
```

**Guards planted (34/34):**

- 1. `rule-real-debate` in `scripts/debate_lanes_report.py`: replaced `real_debate_count == orders` with `True`; `tests/test_debate_lanes_reporting.py::test_each_rule_term_alone_makes_the_report_not_clean` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-01-rule-real-debate-red.txt` and `.tools/s260/guard-01-rule-real-debate-restored.txt`; SHA-256 verified.
- 2. `rule-failed-open` in `scripts/debate_lanes_report.py`: replaced `failed_open_count == 0` with `True`; `tests/test_debate_lanes_reporting.py::test_each_rule_term_alone_makes_the_report_not_clean` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-02-rule-failed-open-red.txt` and `.tools/s260/guard-02-rule-failed-open-restored.txt`; SHA-256 verified.
- 3. `rule-untaken-reply` in `scripts/debate_lanes_report.py`: replaced `replies_nobody_took == 0` with `True`; `tests/test_debate_lanes_reporting.py::test_each_rule_term_alone_makes_the_report_not_clean` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-03-rule-untaken-reply-red.txt` and `.tools/s260/guard-03-rule-untaken-reply-restored.txt`; SHA-256 verified.
- 4. `rule-mismatched-reply` in `scripts/debate_lanes_report.py`: replaced `mismatched_replies == 0` with `True`; `tests/test_debate_lanes_reporting.py::test_each_rule_term_alone_makes_the_report_not_clean` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-04-rule-mismatched-reply-red.txt` and `.tools/s260/guard-04-rule-mismatched-reply-restored.txt`; SHA-256 verified.
- 5. `rule-duplicate-turn` in `scripts/debate_lanes_report.py`: replaced `turns_served_twice == 0` with `True`; `tests/test_debate_lanes_reporting.py::test_each_rule_term_alone_makes_the_report_not_clean` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-05-rule-duplicate-turn-red.txt` and `.tools/s260/guard-05-rule-duplicate-turn-restored.txt`; SHA-256 verified.
- 6. `rule-replica-error` in `scripts/debate_lanes_report.py`: replaced the empty replica-errors condition with `True`; `tests/test_debate_lanes_reporting.py::test_each_rule_term_alone_makes_the_report_not_clean` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-06-rule-replica-error-red.txt` and `.tools/s260/guard-06-rule-replica-error-restored.txt`; SHA-256 verified.
- 7. `rule-fleet-unchanged` in `scripts/debate_lanes_report.py`: replaced the live fleet-unchanged condition with `True`; `tests/test_debate_lanes_reporting.py::test_each_rule_term_alone_makes_the_report_not_clean` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-07-rule-fleet-unchanged-red.txt` and `.tools/s260/guard-07-rule-fleet-unchanged-restored.txt`; SHA-256 verified.
- 8. `reply-id-comparison` in `scripts/debate_lanes_observers.py`: replaced the returned-versus-requested reply-id comparison with `True`; `tests/test_debate_lanes_reporting.py::test_another_requests_reply_is_counted` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-08-reply-id-comparison-red.txt` and `.tools/s260/guard-08-reply-id-comparison-restored.txt`; SHA-256 verified.
- 9. `requests-a-pass-ignored` in `scripts/debate_lanes_memory.py`: discarded the supplied receive-batch override, leaving the settings default; `tests/test_debate_lanes_timed.py::test_september_setting_loses_replies` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-09-requests-a-pass-ignored-red.txt` and `.tools/s260/guard-09-requests-a-pass-ignored-restored.txt`; SHA-256 verified.
- 10. `start-delay-ignored` in `scripts/debate_lanes_scene.py`: forced the supplied replica start delay to zero; `tests/test_debate_lanes_timed.py::test_september_setting_loses_replies` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-10-start-delay-ignored-red.txt` and `.tools/s260/guard-10-start-delay-ignored-restored.txt`; SHA-256 verified.
- 11. `fleet-topic-guard` in `scripts/debate_lanes_live.py`: removed the fleet-topic membership refusal; `tests/test_debate_lanes_transport.py::test_fleet_or_unrelated_topic_is_refused` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-11-fleet-topic-guard-red.txt` and `.tools/s260/guard-11-fleet-topic-guard-restored.txt`; SHA-256 verified.
- 12. `run-id-guard` in `scripts/debate_lanes_live.py`: removed the topic run-id containment refusal; `tests/test_debate_lanes_transport.py::test_fleet_or_unrelated_topic_is_refused` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-12-run-id-guard-red.txt` and `.tools/s260/guard-12-run-id-guard-restored.txt`; SHA-256 verified.
- 13. `empty-run-id-guard` in `scripts/debate_lanes_live.py`: removed the empty-run-id refusal; `tests/test_debate_lanes_transport.py::test_fleet_or_unrelated_topic_is_refused` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-13-empty-run-id-guard-red.txt` and `.tools/s260/guard-13-empty-run-id-guard-restored.txt`; SHA-256 verified.
- 14. `supplied-bus-ignored` in `agents/deliberator/servicebus_peer_client.py`: always constructed the default Azure publisher, ignoring the supplied bus; `tests/test_debate_lanes_peer_bus.py::test_manager_publisher_can_be_supplied` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-14-supplied-bus-ignored-red.txt` and `.tools/s260/guard-14-supplied-bus-ignored-restored.txt`; SHA-256 verified.
- 15. `falsey-supplied-bus-ignored` in `agents/deliberator/servicebus_peer_client.py`: used bus truthiness instead of `is not None`, ignoring a falsey supplied bus; `tests/test_debate_lanes_peer_bus.py::test_manager_publisher_can_be_supplied` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-15-falsey-supplied-bus-ignored-red.txt` and `.tools/s260/guard-15-falsey-supplied-bus-ignored-restored.txt`; SHA-256 verified.
- 16. `absent-bus-no-default` in `agents/deliberator/servicebus_peer_client.py`: used `None` instead of the default publisher when no bus was supplied; `tests/test_debate_lanes_peer_bus.py::test_manager_publisher_can_be_supplied` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-16-absent-bus-no-default-red.txt` and `.tools/s260/guard-16-absent-bus-no-default-restored.txt`; SHA-256 verified.
- 17. `first-poll-wait-removed` in `scripts/debate_lanes_scene.py`: removed every replica first-poll wait before the manager starts; `tests/test_debate_lanes_startup.py::test_manager_starts_after_every_replica_finishes_one_poll` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-17-first-poll-wait-removed-red.txt` and `.tools/s260/guard-17-first-poll-wait-removed-restored.txt`; SHA-256 verified.
- 18. `memory-primary-isolation-removed` in `scripts/debate_lanes_memory.py`: removed explicit isolation from an environment connection string; `tests/test_debate_lanes_transport.py::test_memory_settings_ignore_connections_in_the_environment` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-18-memory-primary-isolation-removed-red.txt` and `.tools/s260/guard-18-memory-primary-isolation-removed-restored.txt`; SHA-256 verified.
- 19. `memory-bundle-isolation-removed` in `scripts/debate_lanes_memory.py`: removed explicit isolation from an environment connection-string bundle; `tests/test_debate_lanes_transport.py::test_memory_settings_ignore_connections_in_the_environment` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-19-memory-bundle-isolation-removed-red.txt` and `.tools/s260/guard-19-memory-bundle-isolation-removed-restored.txt`; SHA-256 verified.
- 20. `old-default-simulated` in `scripts/debate_lanes_memory.py`: simulated the old ten-request default solely in the harness, leaving kernel untouched; `tests/test_debate_lanes_timed.py::test_four_debates_lose_no_reply` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-20-old-default-simulated-red.txt` and `.tools/s260/guard-20-old-default-simulated-restored.txt`; SHA-256 verified.
- 21. `message-returned-without-taking` in `scripts/debate_lanes_memory.py`: returned the queue head without removing it; `tests/test_debate_lanes_startup.py::test_memory_delivery_competes_and_respects_the_requested_batch_size` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-21-message-returned-without-taking-red.txt` and `.tools/s260/guard-21-message-returned-without-taking-restored.txt`; SHA-256 verified.
- 22. `receive-batch-limit-removed` in `scripts/debate_lanes_memory.py`: returned every queued message instead of respecting the requested batch bound; `tests/test_debate_lanes_startup.py::test_memory_delivery_competes_and_respects_the_requested_batch_size` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-22-receive-batch-limit-removed-red.txt` and `.tools/s260/guard-22-receive-batch-limit-removed-restored.txt`; SHA-256 verified.
- 23. `positive-argument-guard` in `scripts/debate_lanes.py`: disabled the positive-integer argument refusal; `tests/test_debate_lanes_command.py::test_bad_argument_returns_two_without_a_report` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-23-positive-argument-guard-red.txt` and `.tools/s260/guard-23-positive-argument-guard-restored.txt`; SHA-256 verified.
- 24. `finite-nonnegative-argument-guard` in `scripts/debate_lanes.py`: disabled the finite, nonnegative float refusal; `tests/test_debate_lanes_command.py::test_bad_argument_returns_two_without_a_report` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-24-finite-nonnegative-argument-guard-red.txt` and `.tools/s260/guard-24-finite-nonnegative-argument-guard-restored.txt`; SHA-256 verified.
- 25. `positive-wait-guard` in `scripts/debate_lanes.py`: disabled the strictly-positive wait refusal; `tests/test_debate_lanes_command.py::test_bad_argument_returns_two_without_a_report` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-25-positive-wait-guard-red.txt` and `.tools/s260/guard-25-positive-wait-guard-restored.txt`; SHA-256 verified.
- 26. `scene-bounds-preflight-removed` in `scripts/debate_lanes.py`: clamped invalid round/concurrency inputs during preflight instead of refusing them; `tests/test_debate_lanes_command.py::test_bad_argument_returns_two_without_a_report` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-26-scene-bounds-preflight-removed-red.txt` and `.tools/s260/guard-26-scene-bounds-preflight-removed-restored.txt`; SHA-256 verified.
- 27. `batch-bounds-preflight-removed` in `scripts/debate_lanes.py`: skipped receive-batch bounds preflight; `tests/test_debate_lanes_command.py::test_bad_argument_returns_two_without_a_report` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-27-batch-bounds-preflight-removed-red.txt` and `.tools/s260/guard-27-batch-bounds-preflight-removed-restored.txt`; SHA-256 verified.
- 28. `missing-live-connection-guard` in `scripts/debate_lanes_live.py`: disabled the missing live connection-string refusal; `tests/test_debate_lanes_transport.py::test_live_without_connection_string_returns_two_and_creates_nothing` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-28-missing-live-connection-guard-red.txt` and `.tools/s260/guard-28-missing-live-connection-guard-restored.txt`; SHA-256 verified.
- 29. `partial-creation-cleanup-removed` in `scripts/debate_lanes_live.py`: removed deletion cleanup on partial live topic creation failure; `tests/test_debate_lanes_live_lifecycle.py::test_partial_creation_deletes_every_created_topic` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-29-partial-creation-cleanup-removed-red.txt` and `.tools/s260/guard-29-partial-creation-cleanup-removed-restored.txt`; SHA-256 verified.
- 30. `fleet-change-comparison-ignored` in `scripts/debate_lanes_live.py`: forced the before/after fleet comparison result to true; `tests/test_debate_lanes_live_lifecycle.py::test_changed_fleet_counts_and_failed_deletion_are_visible` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-30-fleet-change-comparison-ignored-red.txt` and `.tools/s260/guard-30-fleet-change-comparison-ignored-restored.txt`; SHA-256 verified.
- 31. `unreadable-fleet-count-hidden` in `scripts/debate_lanes_live.py`: hid unreadable fleet counts as zero active/dead counts; `tests/test_debate_lanes_live_lifecycle.py::test_cleanup_compares_readable_fleet_counts_and_reports_unreadable` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-31-unreadable-fleet-count-hidden-red.txt` and `.tools/s260/guard-31-unreadable-fleet-count-hidden-restored.txt`; SHA-256 verified.
- 32. `manager-identity-guard-removed` in `scripts/debate_lanes_scene.py`: disabled the fixed manager identity refusal; `tests/test_debate_lanes_startup.py::test_a_manager_identity_override_is_refused` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-32-manager-identity-guard-removed-red.txt` and `.tools/s260/guard-32-manager-identity-guard-removed-restored.txt`; SHA-256 verified.
- 33. `command-default-comparison-lost` in `scripts/debate_lanes.py`: changed the default concurrency list to only four; `tests/test_debate_lanes_command.py::test_command_defaults_are_the_recorded_scene` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-33-command-default-comparison-lost-red.txt` and `.tools/s260/guard-33-command-default-comparison-lost-restored.txt`; SHA-256 verified.
- 34. `unread-replies-not-counted` in `scripts/debate_lanes_report.py`: omitted unread active replies from the untaken-reply count; `tests/test_debate_lanes_timed.py::test_september_setting_loses_replies` failed, exit 1; original bytes restored and the same test passed, exit 0. Outputs: `.tools/s260/guard-34-unread-replies-not-counted-red.txt` and `.tools/s260/guard-34-unread-replies-not-counted-restored.txt`; SHA-256 verified.

`uv run python .tools/s260/mutate.py` first exited 1 after 33 verified plants because the last source matcher did not account for ruff's line break; it restored all original bytes. After correcting that matcher, `uv run python .tools/s260/mutate.py resume` exited 0, verified all prior hashes, and completed guard 34 red/restored. `.tools/s260/guards.json` records every result. No existing test was edited.

**Proof — twenty consecutive timed runs:**

```text
$ pwsh -NoProfile -ExecutionPolicy Bypass -File .tools/s260/repeat-timed.ps1 > .tools/s260/timed-twenty.txt 2>&1
Iteration 1/20: 4 passed; exit 0
Iteration 2/20: 4 passed; exit 0
Iteration 3/20: 4 passed; exit 0
Iteration 4/20: 4 passed; exit 0
Iteration 5/20: 4 passed; exit 0
Iteration 6/20: 4 passed; exit 0
Iteration 7/20: 4 passed; exit 0
Iteration 8/20: 4 passed; exit 0
Iteration 9/20: 4 passed; exit 0
Iteration 10/20: 4 passed; exit 0
Iteration 11/20: 4 passed; exit 0
Iteration 12/20: 4 passed; exit 0
Iteration 13/20: 4 passed; exit 0
Iteration 14/20: 4 passed; exit 0
Iteration 15/20: 4 passed; exit 0
Iteration 16/20: 4 passed; exit 0
Iteration 17/20: 4 passed; exit 0
Iteration 18/20: 4 passed; exit 0
Iteration 19/20: 4 passed; exit 0
Iteration 20/20: 4 passed; exit 0
20/20 consecutive timed runs; 80/80 tests passed
Exit code: 0
```

The script ran `uv run pytest --no-cov -q tests/test_debate_lanes_timed.py` on each iteration, with no concurrent heavy checks. Each of the twenty saved `timed-01.txt` through `timed-20.txt` outputs reports four passed; one-second turns and actual waits were preserved.

**Proof — both required commands, whole output:**

```text
$ uv run python scripts/debate_lanes.py --concurrency 1 2 3 4 --orders 8 --rounds 2 --turn-seconds 0.5 --wait-seconds 5
{"transport": "memory", "concurrency": 1, "replicas": 1, "orders": 8, "rounds": 2, "turn_seconds": 0.5, "wait_seconds": 5.0, "replica_start_delay_seconds": 0.0, "requests_a_pass": 1, "real_debate_count": 8, "failed_open_count": 0, "failed_open_reason": "", "orphaned_reply_count": 0, "replies_nobody_took": 0, "mismatched_replies": 0, "turns_asked": 32, "turns_served": 32, "turns_served_twice": 0, "turns_answered_for_nobody": 0, "turns_started_after_caller_gave_up": 0, "first_wave_replicas": 1, "by_replica": {"opponent-0": 16, "proponent-0": 16}, "span_seconds": 16.46, "served_work_seconds": 16.42, "effective_lanes": 1.0, "request_wait_seconds": [0.0, 0.001], "reply_pickup_seconds": [0.0, 0.012], "subscriptions": {"lanes-proponent.requests": {"active": 0, "dead": 0}, "lanes-opponent.requests": {"active": 0, "dead": 0}, "deliberator-manager.reply": {"active": 0, "dead": 0}}, "errors": [], "faults": {}, "teardown": [], "clean": true}
{"transport": "memory", "concurrency": 2, "replicas": 2, "orders": 8, "rounds": 2, "turn_seconds": 0.5, "wait_seconds": 5.0, "replica_start_delay_seconds": 0.0, "requests_a_pass": 1, "real_debate_count": 8, "failed_open_count": 0, "failed_open_reason": "", "orphaned_reply_count": 0, "replies_nobody_took": 0, "mismatched_replies": 0, "turns_asked": 32, "turns_served": 32, "turns_served_twice": 0, "turns_answered_for_nobody": 0, "turns_started_after_caller_gave_up": 0, "first_wave_replicas": 2, "by_replica": {"opponent-0": 9, "opponent-1": 7, "proponent-0": 7, "proponent-1": 9}, "span_seconds": 13.52, "served_work_seconds": 16.87, "effective_lanes": 1.25, "request_wait_seconds": [0.0, 0.002], "reply_pickup_seconds": [0.027, 0.966], "subscriptions": {"lanes-proponent.requests": {"active": 0, "dead": 0}, "lanes-opponent.requests": {"active": 0, "dead": 0}, "deliberator-manager.reply": {"active": 0, "dead": 0}}, "errors": [], "faults": {}, "teardown": [], "clean": true}
{"transport": "memory", "concurrency": 3, "replicas": 3, "orders": 8, "rounds": 2, "turn_seconds": 0.5, "wait_seconds": 5.0, "replica_start_delay_seconds": 0.0, "requests_a_pass": 1, "real_debate_count": 8, "failed_open_count": 0, "failed_open_reason": "", "orphaned_reply_count": 0, "replies_nobody_took": 0, "mismatched_replies": 0, "turns_asked": 32, "turns_served": 32, "turns_served_twice": 0, "turns_answered_for_nobody": 0, "turns_started_after_caller_gave_up": 0, "first_wave_replicas": 3, "by_replica": {"opponent-0": 5, "opponent-1": 6, "opponent-2": 5, "proponent-0": 5, "proponent-1": 6, "proponent-2": 5}, "span_seconds": 9.83, "served_work_seconds": 16.77, "effective_lanes": 1.71, "request_wait_seconds": [0.001, 0.001], "reply_pickup_seconds": [0.482, 1.013], "subscriptions": {"lanes-proponent.requests": {"active": 0, "dead": 0}, "lanes-opponent.requests": {"active": 0, "dead": 0}, "deliberator-manager.reply": {"active": 0, "dead": 0}}, "errors": [], "faults": {}, "teardown": [], "clean": true}
{"transport": "memory", "concurrency": 4, "replicas": 4, "orders": 8, "rounds": 2, "turn_seconds": 0.5, "wait_seconds": 5.0, "replica_start_delay_seconds": 0.0, "requests_a_pass": 1, "real_debate_count": 8, "failed_open_count": 0, "failed_open_reason": "", "orphaned_reply_count": 0, "replies_nobody_took": 0, "mismatched_replies": 0, "turns_asked": 32, "turns_served": 32, "turns_served_twice": 0, "turns_answered_for_nobody": 0, "turns_started_after_caller_gave_up": 0, "first_wave_replicas": 4, "by_replica": {"opponent-0": 4, "opponent-1": 6, "opponent-2": 4, "opponent-3": 2, "proponent-0": 7, "proponent-1": 4, "proponent-2": 3, "proponent-3": 2}, "span_seconds": 7.75, "served_work_seconds": 16.48, "effective_lanes": 2.13, "request_wait_seconds": [0.001, 0.016], "reply_pickup_seconds": [0.494, 0.974], "subscriptions": {"lanes-proponent.requests": {"active": 0, "dead": 0}, "lanes-opponent.requests": {"active": 0, "dead": 0}, "deliberator-manager.reply": {"active": 0, "dead": 0}}, "errors": [], "faults": {}, "teardown": [], "clean": true}
LANES CLEAN
Exit code: 0
```

```text
$ uv run python scripts/debate_lanes.py --concurrency 4 --orders 4 --rounds 1 --turn-seconds 1 --wait-seconds 2.5 --replica-start-delay 0.3 --requests-a-pass 10
{"transport": "memory", "concurrency": 4, "replicas": 4, "orders": 4, "rounds": 1, "turn_seconds": 1.0, "wait_seconds": 2.5, "replica_start_delay_seconds": 0.3, "requests_a_pass": 10, "real_debate_count": 2, "failed_open_count": 2, "failed_open_reason": "RuntimeError: no deliberator peer reply received", "orphaned_reply_count": 1, "replies_nobody_took": 2, "mismatched_replies": 0, "turns_asked": 6, "turns_served": 6, "turns_served_twice": 0, "turns_answered_for_nobody": 2, "turns_started_after_caller_gave_up": 1, "first_wave_replicas": 1, "by_replica": {"opponent-0": 2, "proponent-0": 4}, "span_seconds": 3.53, "served_work_seconds": 6.1, "effective_lanes": 1.73, "request_wait_seconds": [0.152, 1.348], "reply_pickup_seconds": [0.078, 1.006], "subscriptions": {"lanes-proponent.requests": {"active": 0, "dead": 0}, "lanes-opponent.requests": {"active": 0, "dead": 0}, "deliberator-manager.reply": {"active": 1, "dead": 1}}, "errors": [], "faults": {"RuntimeError": 2, "OrphanedPeerReply": 1}, "teardown": [], "clean": false}
LANES NOT CLEAN: 4
Exit code: 1
```

**Module line counts (physical lines, all < 200):**

| Module | Lines |
| --- | --- |
| `agents/deliberator/servicebus_peer_client.py` | 184 |
| `scripts/debate_lanes.py` | 111 |
| `scripts/debate_lanes_live.py` | 149 |
| `scripts/debate_lanes_memory.py` | 144 |
| `scripts/debate_lanes_model.py` | 89 (92 at handback; the planner removed a module global before the merge) |
| `scripts/debate_lanes_observers.py` | 85 |
| `scripts/debate_lanes_report.py` | 101 |
| `scripts/debate_lanes_scene.py` | 183 |
| `tests/test_debate_lanes_command.py` | 119 |
| `tests/test_debate_lanes_live_lifecycle.py` | 112 |
| `tests/test_debate_lanes_peer_bus.py` | 58 |
| `tests/test_debate_lanes_reporting.py` | 80 |
| `tests/test_debate_lanes_startup.py` | 63 |
| `tests/test_debate_lanes_timed.py` | 91 |
| `tests/test_debate_lanes_transport.py` | 85 |
| `tests/debate_lanes_import_probe.py` | 31 |

**`make ci`:** `make ci > .tools/s260/ci.txt 2>&1`, exit **2**. The full pytest command in that target reported `4436 passed, 8 skipped` and **100.00% coverage**. The target stopped at step 13, so steps 14 and 15 were run separately using the target's exact commands. The overall gate is not green.

| Step | Command/check | Actual result |
| --- | --- | --- |
| 1 | ruff | PASS |
| 2 | format | PASS |
| 3 | mypy, all five production packages | PASS |
| 4 | import-linter | PASS |
| 5 | module size | PASS, existing legacy/warning rows retained |
| 6 | module headers | PASS |
| 7 | law coverage | PASS |
| 8 | PARAM/settings sync | PASS, existing PM envelope warnings retained |
| 9 | sprint status | PASS; checked again after BUILT metadata |
| 10 | Markdown links | PASS; checked again after handback edits |
| 11 | version scheme | PASS, version/lock untouched |
| 12 | full pytest | PASS, 4436 passed, 8 skipped; 100.00% coverage |
| 13 | dependency audit | **NOT RUN to completion**: the actual attempt was refused external network access; no complete audit result was produced |
| 14 | detect-secrets | PASS separately, exit 0; `.tools/s260/secrets.txt` |
| 15 | untracked secrets | PASS separately, exit 0; `.tools/s260/untracked-secrets.txt` |

Actual pytest coverage total, summary and pre-existing skips from the redirected log:

```text
TOTAL                                                           20066      0   4240      0  100.00%
========= 4436 passed, 8 skipped, 2470 warnings in 522.06s (0:08:42) ==========
SKIPPED [1] tests\test_bus_azure_config.py:21: Service Bus dotenv isolation proof requires local .env
SKIPPED [1] tests\test_bus_celery.py:181: CELERY_BROKER_URL is not set
SKIPPED [1] tests\test_deliberator_servicebus_peer.py:36: A1 proof requires .env present; CI has no local secrets file
SKIPPED [1] tests\test_graph_postgres.py:137: POSTGRES_TEST_DSN is not set
SKIPPED [1] tests\test_graph_postgres_keys.py:90: POSTGRES_TEST_DSN is not set
SKIPPED [1] agents\forecaster\tests\test_barrier_garch_oracle.py:179: could not import 'scipy.signal': No module named 'scipy'
SKIPPED [1] agents\provider\tests\test_sources.py:159: FINNHUB_TEST_NETWORK=1 is not set
SKIPPED [1] agents\provider\tests\test_stooq.py:66: STOOQ_TEST_NETWORK=1 is not set
```

Actual dependency-audit tail:

```text
uv run python scripts/check_dependency_audit.py
dependency audit failed: WARNING:pip_audit._cli:--no-deps is supported, but users are encouraged to fully hash their pinned dependencies
WARNING:pip_audit._cli:Consider using a tool like `pip-compile`: https://pip-tools.readthedocs.io/en/latest/#using-hashes
S260 dependency audit NOT RUN: external network disabled: external DNS refused
make: *** [Makefile:59: ci] Error 1
make ci exit code: 2
```

```text
$ uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
Exit code: 0
```

```text
$ uv run python scripts/check_untracked_secrets.py
detect-secrets (untracked): no untracked files to scan
Exit code: 0
```

**Final document checks:** outputs saved in `.tools/s260/final-sprint-status.txt` and
`.tools/s260/final-markdown-links.txt`. The status report's final line is pasted below; the links
check and staged whitespace check printed nothing. Status tokens and link targets were unchanged
by subsequently recording this evidence.

```text
$ uv run python scripts/check_sprint_status.py
docs_seen=265 SPEC=10 BUILT=1 MERGED=254 UNMAPPED=0 MISSING=0
Exit code: 0
$ uv run python scripts/check_markdown_links.py
Exit code: 0
$ git diff --cached --check
Exit code: 0
```

**Scope proof:** all commands ran in `ta-s260`; `main` at this measurement was `99060be4a42f73a1325e03a044d5f2effe0f9240`. Existing tests edited: **none**. `pyproject.toml` and `uv.lock` were not touched; the planner owns the MINOR bump and lock update at merge. `docs/STATE.md`, locked laws and every protected production path were not changed by this branch.

The requested two-tip comparison against moving `main` did **not** print nothing: independent commits on `main` changed STATE after the worktree was cut. The actual output is pasted, followed by the original-base and merge-base checks that measure this sprint's changes:

```text
$ git diff main --stat -- agents/scanner agents/analyst agents/portfolio_manager agents/provider/domain agents/execution/order_tolerance.py contracts orchestration infra kernel pyproject.toml uv.lock docs/STATE.md
 docs/STATE.md | 209 ++++++++++++++++++++++++++++++++++++++++++----------------
 1 file changed, 152 insertions(+), 57 deletions(-)
$ git diff main --stat -- agents
 agents/deliberator/servicebus_peer_client.py | 7 +++++--
 1 file changed, 5 insertions(+), 2 deletions(-)
$ git diff 10770f91bf531eda99cc105f8e80abdfe22fabb0 --stat -- agents/scanner agents/analyst agents/portfolio_manager agents/provider/domain agents/execution/order_tolerance.py contracts orchestration infra kernel pyproject.toml uv.lock docs/STATE.md
$ git diff $(git merge-base main HEAD) --stat -- agents/scanner agents/analyst agents/portfolio_manager agents/provider/domain agents/execution/order_tolerance.py contracts orchestration infra kernel pyproject.toml uv.lock docs/STATE.md
$ git diff 10770f91bf531eda99cc105f8e80abdfe22fabb0 --name-only --diff-filter=MDR -- tests 'agents/*/tests/**'
```

The last three checks printed **nothing**, exit 0 each. The agents-only check names just the constructor file. The direct diff against `main` is a **verified failing literal empty-output check** caused by independent main history; no protected edits were made to satisfy it.

**`make gate-ran`:** **NOT RUN**. No push or remote access authorized; no remote gate proof, merge or deployment claimed.

**Live transport:** **NOT RUN against Azure**. Topic-name/lazy-import guards and synthetic administration cleanup are unit proof only. Actual SDK operation, namespace permissions, live delivery and eventual visibility of subscription counts remain unmeasured.

**Not met / verified failing:** dependency audit NOT RUN to completion; eight existing tests skipped for missing secrets/configuration, network opt-in flags or the optional SciPy oracle, as listed above; live Azure transport and remote gate NOT RUN; push/merge/deploy/version bump not done, as instructed. The requested literal empty `git diff main` check was verified failing because main moved; the original-base and merge-base scope checks were empty. No implementation stop condition was encountered.

---

## Return notes

- Scope held: only D2's constructor seam, harness, new tests and handback/design/index docs changed. No existing test edited. No kernel, fidelity path, pack, orchestration, contract, law, infra, STATE, version or lock edit. No production dial/default changed. Live, push and merge were not run.
- Law-cycle answer NO remains correct. The cited five deliberator clauses are green; no contradiction or new guarantee was introduced. D9 omitted the concurrency default, so DL-281 records one through four and the rejected alternatives. No new policy or lane threshold was added to the clean rule.
- The supplied AGENTS short form counts 14 CI steps; current CLAUDE.md and the actual Makefile target count 15, including sprint status. CLAUDE.md wins. All 15 checks were accounted for; the audit was attempted but could not complete offline.
- PowerShell passed `tests/test_debate_lanes*.py` literally to pytest (exit 4, no tests). The corrected command resolves explicit test file paths before invocation and passed. The guard runner's final matcher initially missed ruff's line break (runner exit 1 after 33 plants); the runner restored all bytes, the matcher was corrected, and resume completed guard 34 with red/restored evidence. Neither correction changed the requested test behavior.
- Main advanced independently after the branch was cut: housekeeping charter changes, then STATE trimming and tracker/archive/sprint status updates. The exact protected-path comparison against main therefore includes STATE. Keep the sprint isolated; assess scope against original base `10770f91` or the merge base. The exact nonempty requested output and the empty corrected checks are above. No rebase or unrelated change was made.
- The memory command warms one guided turn before measurement, waits for every actual first poll when delay is zero, and drains late replies before counting. SDK imports are denied in A10's child process, regardless of whether a local SDK happens to be installed. These are measured harness properties, not live transport proof.
- The planner still owes the version/lock bump at merge, remote gates for the final SHA, and any desired live run. The local gate remains incomplete until the dependency audit can run with its advisory service available.

---

## Appendix — the planner's prototype, and what it printed

One file, on no branch. Copy the block to `.tools/s260/prototype.py` (the folder is ignored by git) and
run it from the worktree root:

```text
uv run python .tools/s260/prototype.py memory ci
```

It prints four JSON reports. The counted fields of each, the same in ten runs of ten on 2026-10-09:

| Configuration | `real_debate_count` | `failed_open_count` | `orphaned_reply_count` | `replies_nobody_took` | `first_wave_replicas` | `turns_asked` | `clean` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1: four at once, 4 replicas 0.3 s late, 1 a pass | 4 | 0 | 0 | 0 | 4 | 8 | true |
| 2: the same, 10 a pass | 2 | 2 | 1 | 2 | 1 | 6 | false |
| 3: four at once, 1 replica, 1 a pass | 2 | 2 | 1 | 2 | 1 | 6 | false |
| 4: one at once, 1 replica | 4 | 0 | 0 | 0 | 1 | 8 | true |

`mismatched_replies` and `turns_served_twice` are 0 and `errors` is empty in all four. Times vary from
run to run: do not compare them. The prototype's keys are shorter than the report table's (`k`,
`turn_s`, `wait_s`, `start_delay_s`, `span_s`, `served_work_s`, `request_wait_s`, `reply_pickup_s`),
its live transport puts the fleet's counts in a `teardown` line instead of `production_unchanged`,
and it waits a fixed time for idle replicas where D8 asks for each replica's first poll.

```python
"""S260 prototype (planner): the production manager and debaters at K debates at once, canned model, $0.

  memory:  uv run python .tools/s260/prototype.py memory <scenario> [repeat]      (no .env, no network)
  live:    uv run --no-sync --env-file .env python <this file> live <scenario>    (the planner only)
Run from the repository root.

Between the transport and the canned model everything is the repo's own code: review_pm_node,
ServiceBusPeerClient, ServiceBusReplyInbox, AzureServiceBusRequestConsumer, serve_once, DeliberatorAgent.
memory = an in-process broker with competing receivers. live = three disposable topics on the real
namespace, created and deleted here. Observation is two wrappers that change nothing that is sent.
"""

from __future__ import annotations

import json
import os
import statistics
import sys
import threading
import time
import uuid
from collections import Counter, defaultdict, deque
from decimal import Decimal
from typing import Any

sys.path.insert(0, os.getcwd())  # run from the repository root; no PYTHONPATH needed

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.poll import review_pm_node
from agents.deliberator.servicebus_peer_client import ServiceBusPeerClient
from agents.deliberator.settings import DeliberatorSettings
from agents.deliberator.store import DELIBERATION_RUN_LABEL
from contracts.common import Explanation, Money, Provenance
from contracts.deliberator import DebateProposition, DebateTurnReply, DebateTurnRequest
from contracts.portfolio_manager import OrderIntent, OrderIntentSet
from kernel import (
    AgentMessage,
    AzureServiceBusBus,
    AzureServiceBusRequestConsumer,
    AzureServiceBusSettings,
    CollectingFaultSink,
    InMemoryGraphStore,
    InProcessBus,
)
from kernel.serve_loop import serve_once
from kernel.serve_transport import request_topic

GUIDED = (
    "[[ ## reasoning ## ]]\n"
    '{"readings": [], "gaps": []}\n\n'
    "[[ ## argument ## ]]\nA.\n\n"
    "[[ ## completed ## ]]"
)
UPHOLD = '{"ruling": "uphold", "rationale": "clears review"}'
MANAGER = "deliberator-manager"  # the debate_turn capability admits this caller and no other
PRODUCTION_TOPICS = frozenset(
    {"deliberator-manager.reply", "deliberator-proponent.requests", "deliberator-opponent.requests"}
)
SUBSCRIPTION = "agent"


class Raw:
    def __init__(self, body: str) -> None:
        self.body = body
        self.delivery_count = 1


class MemoryBroker:
    """Topics with one subscription each and competing receivers."""

    def __init__(self) -> None:
        self._cond = threading.Condition()
        self._queues: dict[str, deque[Raw]] = defaultdict(deque)
        self.dead: Counter[str] = Counter()

    def publish(self, topic: str, event: dict[str, Any]) -> None:
        with self._cond:
            self._queues[topic].append(Raw(json.dumps(event)))
            self._cond.notify_all()

    def take(self, topic: str, count: int, wait: float) -> list[Raw]:
        deadline = time.monotonic() + wait
        with self._cond:
            queue = self._queues[topic]
            while not queue:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return []
                self._cond.wait(remaining)
            return [queue.popleft() for _ in range(min(count, len(queue)))]

    def left(self, topic: str) -> int:
        with self._cond:
            return len(self._queues[topic])


class MemoryReceiver:
    def __init__(self, broker: MemoryBroker, topic: str) -> None:
        self._broker, self._topic = broker, topic

    def receive_messages(self, *, max_message_count: int, max_wait_time: float) -> list[Raw]:
        return self._broker.take(self._topic, max_message_count, max_wait_time)

    def complete_message(self, message: Raw) -> None:
        del message

    def abandon_message(self, message: Raw) -> None:
        self._broker.publish(self._topic, json.loads(message.body))

    def dead_letter_message(self, message: Raw, *, reason: str) -> None:
        del message, reason
        self._broker.dead[self._topic] += 1


class MemoryTransport:
    name = "memory"

    def __init__(self, a_pass: int) -> None:
        self.broker = MemoryBroker()
        self.proponent, self.opponent = "lanes-proponent", "lanes-opponent"
        self.sb = AzureServiceBusSettings(
            _env_file=None, connection_string=None, connection_strings_json=None,
            receive_max_messages=a_pass, receive_timeout_seconds=0.2,
        )
        self.reply_topic = f"{MANAGER}{self.sb.reply_topic_suffix}"

    def consumer(self, graph: InMemoryGraphStore, identity: str) -> Any:
        topic = request_topic(identity)
        return AzureServiceBusRequestConsumer(
            self.broker, graph, topic=topic, subscription_name=SUBSCRIPTION, settings=self.sb,
            receiver=MemoryReceiver(self.broker, topic),
        )

    def peer_client(self, graph: InMemoryGraphStore, wait: float, sink: Any) -> ServiceBusPeerClient:
        client = ServiceBusPeerClient(
            graph, sender=MANAGER, settings=self.sb, timeout_seconds=wait,
            reply_receiver=MemoryReceiver(self.broker, self.reply_topic), sink=sink,
        )
        client._bus = self.broker  # type: ignore[assignment]  # the seam S260 adds as `bus=`
        return client

    def counts(self) -> dict[str, dict[str, int]]:
        topics = (request_topic(self.proponent), request_topic(self.opponent), self.reply_topic)
        return {t: {"active": self.broker.left(t), "dead": self.broker.dead[t]} for t in topics}

    def close(self) -> list[str]:
        return []


class LiveTransport:
    name = "live"

    def __init__(self, a_pass: int) -> None:
        from azure.servicebus.management import ServiceBusAdministrationClient

        connection_string = AzureServiceBusSettings().connection_string
        assert connection_string, "SERVICEBUS_CONNECTION_STRING is required"
        run = f"lanes-{uuid.uuid4().hex[:10]}"
        self.proponent, self.opponent = f"{run}-proponent", f"{run}-opponent"
        suffix = f".{run}.reply"
        self.reply_topic = f"{MANAGER}{suffix}"
        self.topics = (request_topic(self.proponent), request_topic(self.opponent), self.reply_topic)
        assert not set(self.topics) & PRODUCTION_TOPICS, self.topics
        self.sb = AzureServiceBusSettings(
            connection_string=connection_string, connection_strings_json=None,
            receive_max_messages=a_pass, receive_timeout_seconds=2.0, reply_topic_suffix=suffix,
        )
        self._admin = ServiceBusAdministrationClient.from_connection_string(connection_string)
        self._created: list[str] = []
        self.production_before = self._production()
        for topic in self.topics:
            self._admin.create_topic(topic)
            self._created.append(topic)
            self._admin.create_subscription(topic, SUBSCRIPTION)

    def consumer(self, graph: InMemoryGraphStore, identity: str) -> Any:
        return AzureServiceBusBus(settings=self.sb).request_consumer(graph, topic=request_topic(identity))

    def peer_client(self, graph: InMemoryGraphStore, wait: float, sink: Any) -> ServiceBusPeerClient:
        return ServiceBusPeerClient(graph, sender=MANAGER, settings=self.sb, timeout_seconds=wait, sink=sink)

    def counts(self) -> dict[str, dict[str, int]]:
        out = {}
        for topic in self.topics:
            runtime = self._admin.get_subscription_runtime_properties(topic, SUBSCRIPTION)
            out[topic] = {"active": runtime.active_message_count, "dead": runtime.dead_letter_message_count}
        return out

    def _production(self) -> dict[str, list[int]]:
        out = {}
        for topic in sorted(PRODUCTION_TOPICS):
            runtime = self._admin.get_subscription_runtime_properties(topic, SUBSCRIPTION)
            out[topic] = [runtime.active_message_count, runtime.dead_letter_message_count]
        return out

    def close(self) -> list[str]:
        after = self._production()
        result = [f"production subscriptions [active, dead] before {self.production_before} after {after}"
                  f" unchanged={after == self.production_before}"]
        for topic in self._created:
            try:
                self._admin.delete_topic(topic)
                result.append(f"{topic}: deleted")
            except Exception as exc:  # noqa: BLE001
                result.append(f"{topic}: NOT deleted ({type(exc).__name__})")
        return result


class SleepingLLM:
    """A canned model: waits as a debater's turn would, then answers in the guided format."""

    def __init__(self, seconds: float) -> None:
        self._seconds = seconds

    def complete(self, *, system: str, user: str, tool_schema: dict[str, object]) -> str:
        del system, tool_schema
        if user.startswith("DECISION UNDER TEST"):
            return UPHOLD
        time.sleep(self._seconds)
        return GUIDED


class TimedBus:
    """Observe each served request: which replica, when it started and ended."""

    def __init__(self, inner: InProcessBus, replica: str, log: list[dict[str, Any]], lock: threading.Lock) -> None:
        self._inner, self._replica, self._log, self._lock = inner, replica, log, lock

    def request(self, message: AgentMessage) -> AgentMessage:
        started = time.monotonic()
        response = self._inner.request(message)
        with self._lock:
            self._log.append({
                "request_id": message.payload.get("request_id"), "replica": self._replica,
                "start": started, "end": time.monotonic(), "type": response.message_type,
            })
        return response


class CheckingPeerClient:
    """Observe each manager call: its timings, and whether the reply answers this request."""

    def __init__(self, inner: ServiceBusPeerClient, log: list[dict[str, Any]], lock: threading.Lock) -> None:
        self._inner, self._log, self._lock = inner, log, lock

    @property
    def orphaned_reply_count(self) -> int:
        return self._inner.orphaned_reply_count

    def preflight(self, recipients: tuple[str, ...]) -> None:
        self._inner.preflight(recipients)

    def debate_turn(self, recipient: str, request: DebateTurnRequest) -> DebateTurnReply:
        row: dict[str, Any] = {"request_id": request.request_id, "call": time.monotonic(), "outcome": "raised"}
        try:
            reply = self._inner.debate_turn(recipient, request)
            row["outcome"] = "answered" if reply.request_id == request.request_id else "mismatched"
            return reply
        finally:
            row["return"] = time.monotonic()
            with self._lock:
                self._log.append(row)


_WARM = False


def warm_up() -> None:
    """Pay DSPy's import once, outside the measured span (a fresh process spends seconds on it)."""
    global _WARM
    if _WARM:
        return
    agent = DeliberatorAgent(InProcessBus(), graph=InMemoryGraphStore(), llm=SleepingLLM(0.0),
                             settings=DeliberatorSettings(role="proponent"))
    agent.debate_turn(DebateTurnRequest(request_id="warm-up", role="defender", round_number=1,
                                        proposition=DebateProposition(decision="buy WARM", context="ctx")))
    _WARM = True


def pm_node(graph: InMemoryGraphStore, orders: int) -> Any:
    order_set = OrderIntentSet(
        run_id="pm-lanes",
        approved=tuple(
            OrderIntent(ticker=f"T{n:02d}", action="buy", quantity=1, est_price=Money(amount=Decimal("100.00")),
                        rationale=Explanation(summary=f"T{n:02d} approved"))
            for n in range(orders)
        ),
        rejected=(),
        explanation=Explanation(summary="sized"),
        provenance=Provenance(run_id="pm-lanes", source_agent="portfolio_manager"),
    )
    return graph.merge_node("PMRun", order_set.run_id, {"order_intent_set": order_set.model_dump(mode="json")})


def run(transport_name: str, *, k: int, replicas: int, orders: int, rounds: int, turn: float, wait: float,
        start_delay: float, a_pass: int) -> dict[str, Any]:
    warm_up()
    transport = MemoryTransport(a_pass) if transport_name == "memory" else LiveTransport(a_pass)
    graph = InMemoryGraphStore()
    served: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []
    lock, stop = threading.Lock(), threading.Event()
    errors: list[str] = []
    sink = CollectingFaultSink()
    out: dict[str, Any] = {
        "transport": transport.name, "k": k, "replicas": replicas, "orders": orders, "rounds": rounds,
        "turn_s": turn, "wait_s": wait, "start_delay_s": start_delay, "requests_a_pass": a_pass,
    }
    try:
        def replica(role: str, identity: str, index: int) -> None:
            settings = DeliberatorSettings(role=role, instance_name=identity, max_rounds=rounds)  # type: ignore[arg-type]
            bus = InProcessBus()
            DeliberatorAgent(bus, graph=graph, llm=SleepingLLM(turn), settings=settings).bind()
            timed = TimedBus(bus, f"{role}-{index}", served, lock)
            try:
                consumer = transport.consumer(graph, identity)
                while not stop.is_set():
                    serve_once(consumer, timed, sink=sink)  # type: ignore[arg-type]
            except Exception as exc:  # noqa: BLE001 - the measurement records what is raised
                errors.append(f"{role}-{index}: {type(exc).__name__}: {str(exc)[:160]}")

        threads = [
            threading.Thread(target=replica, args=(role, identity, i), daemon=True)
            for role, identity in (("proponent", transport.proponent), ("opponent", transport.opponent))
            for i in range(replicas)
        ]

        def start_replicas() -> None:
            time.sleep(start_delay)
            for thread in threads:
                thread.start()

        manager_settings = DeliberatorSettings(
            role="manager", max_rounds=rounds, debate_concurrency=k,
            proponent_identity=transport.proponent, opponent_identity=transport.opponent,
        )
        assert manager_settings.identity == MANAGER
        manager = DeliberatorAgent(InProcessBus(), graph=graph, llm=SleepingLLM(0.0), settings=manager_settings)
        client = CheckingPeerClient(transport.peer_client(graph, wait, sink), calls, lock)
        pm = pm_node(graph, orders)
        starter = threading.Thread(target=start_replicas, daemon=True)
        if start_delay == 0:
            start_replicas()
            time.sleep(0.2 if transport.name == "memory" else 6.0)  # every replica is polling, as idle ones are
        began = time.monotonic()
        if start_delay > 0:
            starter.start()
        review_pm_node(pm, graph=graph, manager=manager, peer_client=client,  # type: ignore[arg-type]
                       settings=manager_settings, sink=sink)
        span = time.monotonic() - began
        time.sleep(min(turn * 2 + 0.3, 12.0))  # let a turn that nobody waits for any more finish
        stop.set()
        for thread in threads:
            thread.join(timeout=turn + 8)
        (record,) = graph.list_nodes(DELIBERATION_RUN_LABEL)
        p = record.props
        counts = transport.counts()
        by_id = Counter(row["request_id"] for row in served)
        call_by_id = {row["request_id"]: row for row in calls}
        served_by_id = {row["request_id"]: row for row in served}
        unwaited = [row for row in served
                    if call_by_id.get(row["request_id"], {}).get("outcome") == "raised"
                    and row["end"] > call_by_id[row["request_id"]]["return"]]
        late = [row for row in unwaited if row["start"] > call_by_id[row["request_id"]]["return"]]
        answered = [row for row in calls if row["outcome"] == "answered" and row["request_id"] in served_by_id]
        waits = [served_by_id[r["request_id"]]["start"] - r["call"] for r in answered]
        pickups = [r["return"] - served_by_id[r["request_id"]]["end"] for r in answered]
        first_wave = {f"pm-lanes:T{n:02d}:defender:r1" for n in range(min(k, orders))}
        work = sum(row["end"] - row["start"] for row in served)
        reply_left = counts[transport.reply_topic]["active"]
        out.update({
            "real_debate_count": p["real_debate_count"], "failed_open_count": p["failed_open_count"],
            "failed_open_reason": p.get("failed_open_reason", ""),
            "orphaned_reply_count": p["orphaned_reply_count"],
            "replies_nobody_took": p["orphaned_reply_count"] + reply_left,
            "mismatched_replies": sum(1 for row in calls if row["outcome"] == "mismatched"),
            "turns_asked": len(calls), "turns_served": len(served),
            "turns_served_twice": sum(1 for n in by_id.values() if n > 1),
            "turns_answered_for_nobody": len(unwaited),
            "turns_started_after_caller_gave_up": len(late),
            "first_wave_replicas": len({row["replica"] for row in served if row["request_id"] in first_wave}),
            "by_replica": dict(sorted(Counter(row["replica"] for row in served).items())),
            "span_s": round(span, 2), "served_work_s": round(work, 2),
            "effective_lanes": round(work / span, 2) if span else None,
            "request_wait_s": [round(statistics.median(waits), 3), round(max(waits), 3)] if waits else None,
            "reply_pickup_s": [round(statistics.median(pickups), 3), round(max(pickups), 3)] if pickups else None,
            "subscriptions": counts, "errors": errors,
            "faults": dict(Counter(f.error_type for f in sink.faults)),
        })
        out["clean"] = (
            out["real_debate_count"] == orders and out["failed_open_count"] == 0
            and out["replies_nobody_took"] == 0 and out["mismatched_replies"] == 0
            and out["turns_served_twice"] == 0 and not errors
        )
    finally:
        stop.set()
        out["teardown"] = transport.close()
    return out


SCENARIOS: dict[str, list[dict[str, Any]]] = {
    # the four candidate tests: late replicas at one a pass; the same at ten; too few replicas; one lane
    "ci": [
        dict(k=4, replicas=4, orders=4, rounds=1, turn=1.0, wait=2.5, start_delay=0.3, a_pass=1),
        dict(k=4, replicas=4, orders=4, rounds=1, turn=1.0, wait=2.5, start_delay=0.3, a_pass=10),
        dict(k=4, replicas=1, orders=4, rounds=1, turn=1.0, wait=2.5, start_delay=0.0, a_pass=1),
        dict(k=1, replicas=1, orders=4, rounds=1, turn=1.0, wait=2.5, start_delay=0.0, a_pass=1),
    ],
    "warm": [dict(k=k, replicas=k, orders=8, rounds=2, turn=0.5, wait=5.0, start_delay=0.0, a_pass=1)
             for k in (1, 2, 3, 4)],
    "stress": [dict(k=4, replicas=4, orders=16, rounds=2, turn=0.02, wait=5.0, start_delay=0.0, a_pass=1)],
    # live: short turns prove the path; the paid proof on the fleet is a separate act
    "live-smoke": [dict(k=2, replicas=2, orders=2, rounds=1, turn=3.0, wait=60.0, start_delay=0.0, a_pass=1)],
    "live-lanes": [dict(k=k, replicas=k, orders=4, rounds=2, turn=10.0, wait=120.0, start_delay=0.0, a_pass=1)
                   for k in (1, 4)],
    "live-late": [dict(k=4, replicas=4, orders=4, rounds=1, turn=8.0, wait=20.0, start_delay=3.0, a_pass=a)
                  for a in (1, 10)],
}

if __name__ == "__main__":
    transport_name, scenario = sys.argv[1], sys.argv[2]
    repeat = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    for _ in range(repeat):
        for config in SCENARIOS[scenario]:
            print(json.dumps(run(transport_name, **config)), flush=True)
```
