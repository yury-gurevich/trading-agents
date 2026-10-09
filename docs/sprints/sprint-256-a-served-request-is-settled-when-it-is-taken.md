<!-- Agent: planning | Role: sprint handover -->
# Sprint 256 — A served request is settled when it is taken, and every completion is its own ledger row

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-256-a-served-request-is-settled-when-it-is-taken`
**Status:** MERGED 2026-10-08 — `0.123.01`, fast-forwarded to `b3f1ee1f`, tag `v0.123.01`, GATE PROVEN `b3f1ee1f` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (4,322 passed, 8 skipped, 100.00 %, dependency audit clean); built by Codex in `../ta-s256`, complete against the twelve-item checklist; deliberator laws v1.15 (`DLIB-IDM-04`, `DLIB-OBS-08`; `DLIB-OBS-02` proven), operator v1.4 (`OPR-IDM-02` rewritten), DRIFT-104 corrected; the planner's own re-measure: the reproduction prints its *after* block and six pieces of the old behaviour each turn the tests red; open CodeQL alerts 127, the same as sprint 255's branch, none new; **F1 PASS** (the merged code on the live namespace, disposable topics with the default one-minute lock and a 70-second handler: served once, no error, one reply, nothing given to a second consumer, both topics deleted); **deployed `s257` 2026-10-08**; **F2 PASS 2026-10-09** on `sched-2026-10-08` (one debated buy: each debater replica started once and restarted 0 times, the three apps wrote no console line, no ledger key holds `:repeat-`, 0 `Fault`s; the slowest turn took 67.5 s, with the five-minute lock still set by hand).
**Version:** *next available PATCH at merge*
**Effort:** M
**Decisions:** [DL-272](../design-log.md) (decisions D1 to D6 this sprint builds) ·
[DL-271](../design-log.md) (the defect, measured) · work-queue **112** ·
[DL-264](../design-log.md) amendment 7 (this fix comes before work-queue 111 and before step 3)

> **Why this bump kind.** No new capability. A served peer already promises to answer a request once and
> to record what it paid for; the code cannot deliver either when a turn is slow.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build**, except the amendments this spec names. A clause you believe is wrong is a `drift-register.md` row plus a report, never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: deliberator **`DLIB-TRG`**, **`DLIB-IDM`**, **`DLIB-OBS`**, **`DLIB-NEV`**;
operator **`OPR-STA`**, **`OPR-IDM`**.

### The rule

1. **Before writing code**, read every law file in the map below, whole file, first time.
2. Read each agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides what this sprint owes.
5. **Write the Law reading record** (at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
   One contradiction is already known and is this sprint's to resolve: `OPR-IDM-02`, below.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row (next free: DRIFT-104).
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**The planner's answer: no file in `contracts/`, and Yes, three guarantees in two books.** Exactly this
is owed, in the same unit of work:

- **`DLIB-IDM-04`** (new) in `agents/deliberator/laws/laws.md`: *"A served debate-turn request is
  settled when the peer takes it, before the model is called, and a peer takes one request at a time.
  One delivery is therefore served at most once, however long the turn takes. A turn whose peer stops
  mid-call, or whose reply cannot be published, is not served again by the bus: its order fails open on
  the manager's wait (`DLIB-NEV-06`, `DLIB-OBS-03`), and a reply that could not be published is recorded
  as a `Fault`."*
- **`DLIB-OBS-08`** (new) in the same book: *"Every completion is its own `LLMCall` row. A completion
  under a request id that already has a row is recorded under that row's key with a `:repeat-N` suffix,
  N from 1. No row is overwritten, merged or left out."* The book goes to **v1.15**.
- **`OPR-IDM-02`** (rewritten) in `agents/operator/laws/laws.md`. It reads today: *"Duplicate
  `interpret` calls with the same text produce separate `CommandAudit` and `LLMCall` nodes. No
  deduplication."* The code has never done that: without a request id the two calls share one correlation
  id (`OPR-IDM-03`), so there is one `CommandAudit`, one `Intent`, and until this sprint one `LLMCall`.
  Rewrite it to what is true after this sprint: *"Duplicate `interpret` calls with the same text and no
  request id share one correlation id (`OPR-IDM-03`), and so one `CommandAudit` and one `Intent`. Each LLM
  call they make is its own `LLMCall` row: the first under the correlation id, each later one with a
  `:repeat-N` suffix. No LLM call is deduplicated."* Verify the `CommandAudit` and `Intent` half against
  the code before you write it; if it is not true, write the true clause and say so. The book goes to
  **v1.4**.
- Each book: a Changelog line naming S256 and DL-272, a `test-plan.md` row per clause, the clause ID in
  the docstrings of the tests that prove it.
- A `drift-register.md` row, **DRIFT-104**, for `OPR-IDM-02` against the code, corrected in this sprint.
- The rollups in **both** `docs/laws/ledger.md` and `docs/laws/INDEX.md`, for both books. Let
  `make ci` tell you the numbers.

Edit no other clause. If your reading finds that an existing clause already makes one of these
guarantees, name it in the Law reading record, cite it, and do not add a duplicate.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `kernel/bus_azure_receiver.py`, `kernel/bus_azure_config.py`, `kernel/serve_loop.py` | `agents/deliberator/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `DLIB-TRG-02` (the two peers are served request and reply instances), `DLIB-NEV-06` (a failed peer call is never hidden), `DLIB-OBS-03` (a fail-open is visible); the new `DLIB-IDM-04`. The kernel has no law book of its own: the deliberator's peers are the only served agents any fleet component calls |
| `agents/deliberator/entrypoint.py` | same | `DLIB-TRG-02`; the peer gains a fault sink |
| `kernel/llm_ledger.py` | deliberator and operator books, both whole | `DLIB-OBS-02` (spend is attributable), `DLIB-OBS-05` (a completion is counted *"because it was still generated and still billed"*), `DLIB-IDM-02`; `OPR-STA-02` (ledger nodes accumulate, none is overwritten), `OPR-STA-03`, `OPR-IDM-02`, `OPR-IDM-03`; the new `DLIB-OBS-08` |
| `scripts/deliberation_reproducibility.py` | deliberator book | `DLIB-OBS-07`: it compares a recorded prompt hash with a rebuilt one, and it keys the recorded hashes by correlation id |

⚠️ **A request that could not be decoded is still refused, never settled.** The abandon and the
dead-letter at the delivery limit stay exactly as they are. If your change would complete a message whose
ready event did not resolve into a request, stop and report.

---

## Goal

At merge, a served agent completes each request message as soon as it has resolved into a request, before
the handler runs, and takes one request per pass. A turn that lasts longer than the subscription's lock is
answered once and nothing fails. A reply that cannot be published leaves a `Fault` and the loop keeps
serving. And a completion under a ledger key that already has a row is written as its own row, so the
ledger's tokens are the tokens that were paid for.

## Why (context)

A debater's turn on `gpt-5.5` takes about a minute, and the two subscriptions the debaters serve from
were created with a one-minute lock. A served peer takes its request under that lock, runs the model call,
publishes the reply and only then completes the message. When the call outlasts the lock, the reply still
goes out, the completion raises, nothing catches it, and the peer's process ends. The request is then
delivered again, the model is called a second time, and the ledger keeps only the first call's row
([DL-271](../design-log.md)). Since 2026-10-08 both subscriptions hold a five-minute lock, set by hand on
the live namespace. That is a setting on two resources, at the vendor's maximum, which a re-created
subscription loses. Work-queue 111 will raise the output cap, which makes turns longer, so this comes
first.

### Measured, 2026-10-08 — read these before designing

No LLM call. Rows marked *live* were measured by the planner with the fleet's credentials and cannot be
re-run in a worktree. The Appendix script reproduces the rows marked *Appendix* with no `.env`.

| Claim | Value | How it was measured |
| --- | --- | --- |
| When a request is settled | after the handler and after the reply: `serve_once` calls `consumer.poll()`, then `bus.request`, then `consumer.reply`, and `reply` publishes and then calls `complete_message` | *[measured, read]* `kernel/serve_loop.py`, `kernel/bus_azure_receiver.py`; *[Appendix]* line 2 prints `['handled', 'published', 'settled']` |
| What guards the completion | nothing: `_complete` and `_reject` are called bare, `serve_once` and `serve_loop` catch nothing | *[measured, read]*; *[Appendix]* line 3 |
| How many requests one pass takes | up to `receive_max_messages`, default **10**, all under locks that start at the receive; they are then handled one after another | *[measured, read]* `kernel/bus_azure_config.py`; *[Appendix]* line 1 prints 3 of 3 |
| A reply that cannot be published | the request is abandoned, so the broker delivers it again and the handler runs again; nothing is recorded | *[measured, read]*; *[Appendix]* line 4 |
| A second completion under one ledger key | `write_llm_call` returns the first row; the second call's tokens are recorded nowhere | *[measured, read]* `kernel/llm_ledger.py`; *[Appendix]* line 5 prints 1 row and 7,738 of 15,479 tokens |
| The same defect on the live service, `main`'s code | default lock `0:01:00`, a 70-second handler: the reply is published, `serve_once` raises `MessageLockLostError`, a second consumer is given the same request, the handler runs **twice** | *[measured, live, 2026-10-07]* disposable topics, deleted afterwards |
| The prototype of this spec on the live service | same topics' shape, same default lock, same 70-second handler: served **once**, no error, one reply; a second consumer is given nothing; 0 active and 0 dead-lettered messages left; both topics deleted | *[measured, live, 2026-10-08]* the prototype's `kernel/bus_azure_receiver.py`, printed as the code under test |
| The prototype against the whole suite | **5 existing tests fail and 4,298 pass** (8 skipped): one test in each of three files under `tests/` and two under `agents/operator/tests/`; they are named under Traps | *[measured]* `uv run pytest` in this worktree with the prototype applied, then reverted |
| Who sends to a served agent's request topic | only the deliberator's manager, to its two peers. `scripts/servicebus_request.py` is a hand tool. No fleet component sends to the supervisor's, the operator's, the researcher's or the forecaster's request topic | *[measured]* `git grep "request_topic("` and `"\.requests"` over `agents surfaces orchestration kernel scripts`, tests excluded |
| How many orders the manager debates at once | one: `DELIBERATOR_DEBATE_CONCURRENCY` is `1` in `orchestration/packs/trading_tunables.json` (code default 4) | *[measured, read]* |
| How long the manager waits for a turn | 120 seconds (`DELIBERATOR_REQUEST_TIMEOUT_SECONDS` in the same pack; the tunable's bound is `le=120`) | *[measured, read]* |
| Served turns over 60 seconds in the record | 4 of 1,130 debater `LLMCall` rows, all on 2026-08-19, all `gpt-5.5` (61.6 to 68.4 s). The record cannot show a repeat, for the reason in the fifth row | *[measured, live, 2026-10-08]* |
| Replies the manager found with nobody waiting | 0 over 90 `DeliberationRun`s; 5 runs failed an order open on *"no deliberator peer reply received"* | *[measured, live, 2026-10-08]* |
| The request message's time to live | none: the manager sets none and both subscriptions keep a message forever. A request nobody waits for any more is served whenever a peer next takes it | *[measured, read and live]* the 2026-10-07 subscription snapshot. **Not fixed here**: see Out of scope |
| Readers of `LLMCall` rows | `surfaces/dashboard/llm_costs.py`, `scripts/check_llm_outage.py` and `scripts/deliberation_reproducibility.py` list every row; only the last builds a lookup, by `correlation_id`, and so keeps whichever of two rows is listed last | *[measured, read]* |
| The operator's duplicate command | two `interpret` calls with the same text and no request id make two model calls and leave one `CommandAudit`, one `Intent` and one `LLMCall` | *[measured]* `agents/operator/tests/test_operator_agent.py::test_ledger_is_idempotent_for_same_command` passes on `main` |
| Module sizes | `kernel/bus_azure_receiver.py` **173**, `kernel/llm_ledger.py` **153**, `scripts/deliberation_reproducibility.py` **139**, `agents/deliberator/entrypoint.py` **120**, `kernel/bus_azure_config.py` **116**, `kernel/serve_loop.py` **88** | *[measured]* `wc -l` |
| Whether the broker frees a locked message when its receiver disconnects | *[ASSUMED, from the vendor's documentation]* no: it stays locked until the lock runs out. Nothing in this design depends on it | not measured |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first (A1, A2, A7).** Watch each fail on the untouched tree.
2. **Settle on take** (D1): `AzureServiceBusRequestConsumer.poll` completes each message as soon as its
   ready event has resolved into a request, before returning it. `reply` publishes and does nothing else.
   The `_pending` map goes.
3. **One request per pass** (D2): the default of `receive_max_messages` becomes `1`, and its `why` says
   why.
4. **A reply that cannot be published is a fault** (D3): `serve_once` and `serve_loop` take an optional
   fault sink, the reply runs inside a fault boundary that does not re-raise, and the deliberator's
   `serve_peer` passes a graph fault sink.
5. **Every completion is its own ledger row** (D4): `write_llm_call` writes a repeat under the first key
   plus `:repeat-N`. No new property.
6. **The one reader that keys by correlation id** keeps the first row of a turn:
   `scripts/deliberation_reproducibility.py`.
7. **The law cycle**, two books and one drift row.

### Out of scope (do NOT build this sprint)

- **`pyproject.toml` and `uv.lock`.** Do not touch either. The planner bumps the version at merge.
- **Anything on the subscriptions**: `scripts/servicebus_prepare_routes.py`, `infra/`, the lock
  duration, a renewal of the lock. After this sprint no lock is held while a handler runs (D5).
- **The manager's side**: `agents/deliberator/poll.py`, `servicebus_peer_client.py`, the reply inbox, the
  wait, the fail-open.
- **A time to live on the request.** A request whose caller has stopped waiting is still served when a
  peer next takes it. It is a real cost with no recorded instance; it goes with work-queue 111, which
  changes the wait.
- **The output cap and the wait's bound** (work-queue 111).
- **A fault sink for the supervisor, the operator, the researcher or the forecaster.** Nothing sends to
  them; their loops keep the default in-memory sink.
- **Flushing the fault sink from the serve loop.** The first fault of a kind is written at once; identical
  ones inside the collapse window are counted only at a flush, which the loop does not do.
- **The role prompts, the guided turn, the DSPy engine and program, the judge.**
- **The merge and the push.** Commit on the branch and hand back.

### The road not taken (LAW-06)

- **Renew the lock while the handler runs** (the vendor's `AutoLockRenewer`). Rejected: a second thread on
  a synchronous receiver's connection, provable only on the live service, and it keeps the redelivery
  that makes the second paid call.
- **Create the subscriptions with an explicit five-minute lock and stop there.** Rejected: five minutes is
  the vendor's maximum, an existing subscription is not changed by a create, and a batch still ages under
  it (the third request of a pass has waited two turns before it starts).
- **Catch the lost lock and carry on.** Rejected: the request is still delivered and served again.
- **Settle each request just before its own handler, keeping the batch.** Rejected: it needs a third
  method on the consumer protocol and its own lost-lock path, for a batch that buys nothing when requests
  are handled one after another.
- **Keep one ledger row and add a repeat count and summed tokens to it.** Rejected: it rewrites an audit
  row and loses the second call's hash, latency and stop reason.
- **Key the ledger by the bus message's id.** Rejected: it changes every existing key and every reader.
- **A new `repeat_of` property on the row.** Rejected: the key already names the first row, and a new
  property is graph vocabulary.

---

## The design decisions — made, and recorded in DL-272

The planner made these and measured each in the Appendix script, in the prototype or on the live service.
**Build them as written.** Record in `docs/design-log.md` (next free: **DL-273**) only a decision the spec
did not make, or a place where you had to depart from one of these, with the reason.

| # | Decision | Rejected |
| --- | --- | --- |
| D1 | A served request is settled when it is taken. In `poll`, a message whose ready event resolves into a request is completed and then returned; one that does not resolve is abandoned or dead-lettered as today. `reply` only publishes. If the completion itself fails, the request is not returned and the error leaves `poll`: nothing was paid, and the broker delivers it again | see the road not taken |
| D2 | A served agent takes one request per pass: `receive_max_messages` defaults to `1`. The bounds stay, so a deployment may still raise it and accept what D1 then loses if the process stops | deleting the tunable: more surface for no gain |
| D3 | `serve_once(consumer, bus, *, sink=None)` runs `consumer.reply` inside `fault_boundary(..., agent=request.recipient, module="kernel.serve_loop", capability=request.capability, reraise=False)`, on the given sink or a new `CollectingFaultSink`. `serve_loop` takes the same `sink` and passes it. `serve_peer` passes `GraphFaultSink(graph, CollectingFaultSink())` | letting the error end the process: the next request then waits for a restart; swallowing it as today: silent |
| D4 | `write_llm_call` writes the first completion under `llmcall:{agent}:{correlation_id}` as today, and a later one under that key plus `:repeat-1`, `:repeat-2`, taking the first free. Every property is the completion's own. The returned node is the row just written, so the reply's `llm_call_key` names it | see the road not taken |
| D5 | Nothing changes on any subscription. The five-minute lock set by hand on 2026-10-08 stays where it is: it costs nothing, and it protects the old code after a rollback | setting it back to one minute |
| D6 | The operator's book says what is true: `OPR-IDM-02` is rewritten as above, and the test that proved `OPR-IDM-03` by counting one `LLMCall` counts two rows with one correlation id | leaving a clause the code contradicts |

**What D1 gives up, said plainly.** The bus no longer serves a turn again after its peer stopped mid-call
or its reply could not be published. That order fails open when the manager's wait ends, as a timed-out
turn does today. With the five-minute lock now on the live subscriptions a redelivery already arrives
after the manager's 120-second wait, so the fleet as it stands gives up nothing.

---

## Blast radius — measured 2026-10-08

| What | Detail |
| --- | --- |
| Files changed | `kernel/bus_azure_receiver.py` **173**, `kernel/bus_azure_config.py` **116**, `kernel/serve_loop.py` **88**, `kernel/llm_ledger.py` **153**, `agents/deliberator/entrypoint.py` **120**, `scripts/deliberation_reproducibility.py` **139**; the tests; two law books, two test plans, both rollups, the drift register |
| Agents affected | every served agent runs the kernel's consumer and loop; only the deliberator's two peers receive requests. The operator's ledger rows change shape for a repeated correlation id. No agent imports another |
| Contract change? | no |
| Graph vocabulary change? | no. A repeat is an `LLMCall` node with the same properties under a longer key |
| New env keys / tunables | none. One default changes (`receive_max_messages` 10 to 1). Nothing sets it: `git grep RECEIVE_MAX_MESSAGES` finds only the setting's own docstring, and neither debater app carries the variable (measured live, 2026-10-08, the two apps' environment names) |
| Deploy implication | image-only retag |
| Rollback | retag the fleet to the tag it ran before. `LLMCall` rows written under a `:repeat-N` key stay, and older code lists them like any other row. The five-minute lock on the two debater subscriptions is live infrastructure, untouched by a retag: it stays, and it is what protects the older code |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Run the Appendix script** in your worktree, on the untouched tree, and paste its output into the
   Closeout. It must print the block the Appendix labels *before*. If it does not, stop and report: your
   tree differs from the one this spec was measured in.
3. **Plant the failing tests first** (A1, A2, A7) and watch them fail. Paste the red output.
4. **Implement** D1 to D4 and scope item 6.
5. **Law cycle:** two books, their test plans, both rollups, DRIFT-104.
6. **Run the Appendix script again.** It must print the block labelled *after*. Paste it.
7. **Prove the guards can fail (DL-70):** break each guarded property, watch the guard go red, restore.
8. **`make ci`**, every step of the `ci:` target, **redirected to a file, never piped**. Name any step
   your sandbox cannot run as NOT RUN.
9. **Fill the handback sections** at the bottom of this file and set Status to `BUILT`, here and in
   this sprint's `README.md` row.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 A request is settled before its handler runs | A receiver that records when a message is completed; a handler and a reply subscriber that record when they run | For one request the order is settled, handled, published (`DLIB-IDM-04`) |
| A2 | 🎯 A turn that outlives its lock is served once | A receiver whose `complete_message` raises once the handler has started, as an expired lock does | `serve_once` returns 1 and raises nothing; the handler ran once; one reply is published (`DLIB-IDM-04`) |
| A3 | A reply that cannot be published is a fault, and nothing is delivered again | A bus whose publish fails; two requests; a `GraphFaultSink` over an in-memory graph | Each handler ran once; 2 settled, 0 abandoned, 0 dead-lettered; `serve_once` did not raise and served the second request; one `Fault` with `source_module` `kernel.serve_loop`, the serving agent, the capability and severity `error` (`DLIB-IDM-04`, `DLIB-NEV-06`) |
| A4 | 🪤 A request that cannot be decoded is refused, never settled | The two existing cases: a ready event whose claim is missing, and a body that is not text at the delivery limit | Abandoned, and dead-lettered at the limit, as today; `completed` is empty. The two existing tests pass with no edit |
| A5 | A request whose settlement fails is not served | A receiver whose `complete_message` raises at once | The handler does not run, nothing is published, and the error leaves `serve_once` |
| A6 | One request is taken per pass | Three requests on the receiver, settings with nothing overridden | The first pass serves 1 and leaves 2; three passes serve all three in order; the default of `receive_max_messages` is 1 (`DLIB-IDM-04`) |
| A7 | 🎯 A second completion under one key is its own row | `write_llm_call` three times with one agent and one correlation id and three different token counts | Keys: the first, `…:repeat-1`, `…:repeat-2`; the first row's properties are what they were after the first write; the token sum is all three; each returned node is the row just written (`DLIB-OBS-08`) |
| A8 | A turn served twice shows in the peer's ledger | `DeliberatorAgent.debate_turn` called twice with one request, on a fake model | Two `LLMCall` rows with equal `calling_agent` and `correlation_id`; the second reply's `llm_call_key` is the repeat's key (`DLIB-OBS-08`, `DLIB-OBS-02`) |
| A9 | The cost readers count a repeat | A ledger with a turn and its repeat, given to the dashboard's cost reader and to the outage report | The totals include both rows' tokens, and neither reader raises on the longer key (`DLIB-OBS-08`) |
| A10 | The operator's duplicate command | Two `interpret` calls with the same text and no request id | One `CommandAudit`, one `Intent`, two `LLMCall` rows with one `correlation_id` (`OPR-IDM-02`, `OPR-IDM-03`) |
| B1 | 🪤 The reproducibility check reads the first row of a turn | A turn and its repeat with different prompt hashes, in both listing orders | The recorded hash it compares against is the first row's, in both orders (`DLIB-OBS-07`) |
| B2 | 🪤 The peer passes a graph fault sink, and still does not sleep | `serve_peer` with `serve_loop` replaced | `sink` is a `GraphFaultSink` over the peer's graph; `poll_interval` is still 0 |
| B3 | 🪤 The other served agents are unchanged | The supervisor's, the operator's, the researcher's and the forecaster's entrypoint tests | They pass with no edit |
| B4 | 🪤 `reply` does not touch the receiver | A taken request, then its reply | The receiver's completed, abandoned and dead-lettered lists are the same before and after `reply` |

No test may skip when a dependency is missing. A skipped proof is not a proof. No test calls an LLM or
the network.

---

## Success factors

- [x] A request is completed before its handler runs, and a completion that would have failed after a
      long handler no longer exists (A1, A2).
- [x] A reply that cannot be published leaves one `Fault`, abandons nothing, and the loop serves the next
      request (A3).
- [x] A request that cannot be decoded is still abandoned, or dead-lettered at the limit, and never
      completed (A4).
- [x] One request is taken per pass by default (A6).
- [x] A completion under an existing ledger key is its own row; no row is overwritten (A7, A8).
- [x] Every reader of `LLMCall` rows counts or reads a repeat correctly (A9, B1).
- [x] The Appendix script prints the *before* block on the untouched tree and the *after* block on the
      built one.
- [x] `pyproject.toml`, `uv.lock`, `infra/`, the packs, the manager's modules and the role prompts are
      untouched.
- [x] Law cycle done in two books, DRIFT-104 filed as corrected, or an existing clause named in a new
      one's place.
- [x] Every new guard planted, watched to fail, restored, stated per guard.
- [x] Every touched module < 200 lines.
- [x] `make ci` exit 0, 100.00 % coverage, or each step that could not run named as NOT RUN.

---

## Traps

🪤 **Five existing tests assert the behaviour this sprint removes.** Measured on the prototype; each needs
a deliberate edit, named in the handback with its reason. Any sixth is a finding: name it.

- `tests/test_bus_azure_receiver.py::test_reply_abandons_pending_message_when_publish_fails`: asserts the
  abandon. Under D1 nothing is abandoned.
- `tests/test_bus_azure_receiver_edges.py::test_reply_publish_failure_without_pending_source_does_not_raise`:
  `reply` now raises on a failed publish; it is `serve_once` that contains it.
- `agents/operator/tests/test_operator_agent.py::test_ledger_is_idempotent_for_same_command`: counts one
  `LLMCall` for two model calls (D6).
- `agents/operator/tests/test_operator_store.py::test_write_llm_call_records_operator_attribution`:
  asserts the second write returns the first row.
- `tests/test_deliberator_cold_peer_timing.py::test_served_peer_uses_receive_wait_without_extra_idle_sleep`:
  its stand-in for `serve_loop` does not accept `sink`.

🪤 **`tests/bus_azure_receiver_helpers.py` pins `receive_max_messages` at 10.** A test that uses its
`settings()` does not exercise the default. A6 must build the settings with nothing overridden.
🪤 **`serve_once` must not swallow a failed take.** Only the reply is inside the fault boundary. An error
from `poll` leaves the loop, as a failed receive does today.
🪤 **`GraphFaultSink` writes the first fault of a kind at once and counts identical ones until a flush.**
Two failed replies in one test leave one `Fault` node, not two.
🪤 **A correlation id contains colons** (`<run>:<ticker>:<role>:r<n>`). Never parse a ledger key by
splitting it. Compare whole keys.
🪤 **`kernel/llm_ledger.py` is at 153 lines and `kernel/bus_azure_receiver.py` at 173.** The receiver
shrinks. Do not compress code to fit anywhere.
🪤 **The kernel imports nothing above it.** `kernel/serve_loop.py` may import `kernel.errors`; the graph
sink is built in the agent's entrypoint, not in the loop.
🪤 **Do not remove `receive_max_messages` or its bounds**, and do not hard-code `1` in the consumer.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: `kernel.tunable(..., why=...)` with bounds. This sprint adds no tunable and changes
  one default.
- Faults, not silent failure: `kernel.fault_boundary`.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- Secrets never through the worktree. A worktree has **no `.env`**, and nothing here needs one.
  **State which tree you ran in.**

---

## Sequencing after merge

Owed by the planner, in this order:

1. Review against the checklist; the planner's own re-measure (the Appendix script on the built tree, and
   the five edited tests read one by one); the PATCH bump and `uv lock`; Windows `make ci`, all steps;
   push the branch; **`make gate-ran` exits 0** from the worktree whose `HEAD` is the commit being proven;
   the branch's open CodeQL alerts compared with `sprint-255-the-packet-states-the-score-arithmetic`'s
   127.
2. Merge, the tag.
3. **F1, before any retag, no cost.** The 2026-10-07 live check on the merged code: disposable topics on
   the live namespace with the default one-minute lock and a 70-second handler. Served once, no error,
   one reply, nothing given to a second consumer, both topics deleted.
4. **Deploy:** image-only retag, on the operator's word, with whatever else is owed then. The diff
   against the scanner's, the analyst's and the PM's decision paths is read first; it is expected to be
   empty, which leaves the fidelity count where it is. The rollback tag is recorded.
5. **F2, the first scheduled night with a debated buy after the retag.** Each debater app's restart count
   is 0 and its log has no `MessageLockLostError`; no `LLMCall` key ends in `:repeat-`; no `Fault` names
   `kernel.serve_loop`; each turn's latency is read against the 120-second wait.

---

## Handover — paste this to Codex

```text
Sprint 256 — a served request is settled when it is taken, and every completion is its own ledger row.
Spec: docs/sprints/sprint-256-a-served-request-is-settled-when-it-is-taken.md (read ALL of it, then
CLAUDE.md). Repo: yury-gurevich/trading-agents, local checkout.

Your worktree already exists: ../ta-s256, on branch
sprint-256-a-served-request-is-settled-when-it-is-taken, cut from main, with its venv synced to the
lock. Work only there, never in the main checkout and never on main. You have no .env and no network:
every proof is a unit test, and no test calls an LLM or the bus. `uv run` is safe. Do not touch
pyproject.toml or uv.lock, and say so: the planner bumps the version at merge. Do not push and do not
merge: commit on the branch and hand back. Do not edit docs/STATE.md: put intent and results in the
spec's Closeout. If a make ci step cannot run in your sandbox (the dependency audit needs the network),
do not bypass it silently: name the step as NOT RUN in the handback.

This handover is complete: nobody will send you follow-up messages. Two tiers:
- A wrong command, count, path or clause number whose intent is plain from the spec's Scope and Success
  factors is NOT a reason to stop: follow the intent, record the correction in Return notes, continue.
  An existing test beyond the five the spec names that fails because of this change is the same tier:
  edit it only if the behaviour it asserts is one this spec removes, and name it with the reason.
- STOP and report, without improvising, when: the Appendix script does not print the "before" block on
  your untouched tree; a message whose ready event did not decode would be completed; a law contradicts
  the spec other than OPR-IDM-02, which the spec resolves; or making the suite pass would need a change
  to the manager's side, to a subscription, or to anything under infra/ or orchestration/packs/.

What and why: a debater's model call takes about a minute, and the peer holds its request under a
one-minute message lock until after the reply. When the call outlasts the lock the reply still goes
out, the completion raises, nothing catches it and the process ends; the request is delivered again,
the model is called a second time, and the ledger keeps only the first call's row because it returns
the existing row for a repeated key. The planner measured each step, prototyped this spec's fix, and
ran it on the live service: with the default one-minute lock and a 70-second handler the request is
served once and nothing fails.

MUST RULE before any code: read, whole, the laws.md and test-plan.md of the deliberator and the
operator, docs/laws/conventions.md, docs/laws/drift-register.md, and DL-272 and DL-271 in
docs/design-log.md. Fill the Law reading record first. Law-cycle answer: no contracts/ file, and YES,
three guarantees. Owed: DLIB-IDM-04 and DLIB-OBS-08 (new, deliberator v1.15), OPR-IDM-02 rewritten
(operator v1.4), each with a Changelog line naming S256 and DL-272, a test-plan row, the clause ID in
the proving tests' docstrings, DRIFT-104 for OPR-IDM-02 against the code (corrected here), and both
rollups (docs/laws/ledger.md and docs/laws/INDEX.md). The wording of each clause is in the spec. Edit
no other clause.

Order (the spec's Steps): laws -> run the Appendix script on the untouched tree (must print the
"before" block) -> plant A1, A2 and A7, watch them fail, paste the red -> implement -> law cycle -> run
the Appendix script again (must print the "after" block) -> break and restore every guard -> make ci to
a file.

Build (decisions D1-D6 are made; build them as written, the Appendix's prototype diff is the reference
shape, not text to paste):
1. kernel/bus_azure_receiver.py: poll completes a message as soon as its ready event has resolved into
   a request, then returns the request. A message that does not resolve is abandoned or dead-lettered
   exactly as today and never completed. reply publishes and does nothing else. The _pending map goes.
2. kernel/bus_azure_config.py: receive_max_messages defaults to 1; its why says a taken request is
   already settled, so a pass takes one. Keep the bounds.
3. kernel/serve_loop.py: serve_once and serve_loop take an optional sink; the reply runs inside
   fault_boundary(..., agent=request.recipient, module="kernel.serve_loop",
   capability=request.capability, reraise=False). poll stays outside the boundary.
4. agents/deliberator/entrypoint.py: serve_peer passes GraphFaultSink(graph, CollectingFaultSink()).
5. kernel/llm_ledger.py: a completion under a key that exists is written under that key plus :repeat-1,
   :repeat-2, the first free. No new property. The returned node is the row just written.
6. scripts/deliberation_reproducibility.py: its lookup by correlation id keeps the first row of a turn.
7. Tests A1-A10 and B1-B4 from the spec's Test plan, each citing its clause.

DO NOT: complete a message that did not decode; put poll inside the fault boundary; hard-code 1 in the
consumer or remove the tunable; add a property to LLMCall; rewrite or merge a ledger row; parse a ledger
key by splitting it; touch a subscription, the route preparation script, infra/, a pack, the manager,
the reply inbox, the role prompts, the guided turn, the DSPy modules or the judge; give any other
served agent a graph sink; import one agent from another; pin a version number.

Handback checklist (the handback is returned against these, one by one):
 1. Law reading record filled before the first code change.
 2. The Appendix script's "before" output pasted, with the tree it ran in.
 3. The red output of A1, A2 and A7 pasted, from before the implementation.
 4. Test plan results: one row for each of A1-A10 and B1-B4, with file, status and clause.
 5. Every guard's break-and-restore stated, one line per guard.
 6. DLIB-IDM-04, DLIB-OBS-08 and v1.15; OPR-IDM-02 rewritten and v1.4; two Changelog lines; test-plan
    rows; DRIFT-104; both rollups; no other clause edited.
 7. This prints nothing, and you say so:
    git diff main -- pyproject.toml uv.lock infra orchestration/packs scripts/servicebus_prepare_routes.py agents/deliberator/poll.py agents/deliberator/servicebus_peer_client.py agents/deliberator/servicebus_reply_inbox.py kernel/deliberation_prompts.py
 8. The Appendix script's "after" output pasted.
 9. Every EXISTING test file you edited, named, with the reason for each edit. The spec expects five
    tests in five files.
10. Every reader of LLMCall rows you found (path and line), and what each does with a repeat row.
11. make ci output file named, exit code stated, every NOT RUN step named with its reason.
12. Module line counts for every touched module; Status BUILT here and in the README row.
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
| Receiver, settings and serve loop | Deliberator `laws.md` and `test-plan.md`, both whole; `docs/laws/conventions.md` and `drift-register.md`, both whole | `DLIB-TRG-02`, `DLIB-NEV-06`, `DLIB-OBS-03`; owed `DLIB-IDM-04` | D1-D3 as decided. `TRG-02` is gray; this build proves settlement without claiming a new trigger proof. A failed decode is still refused; a failed take propagates before handling. |
| Peer entrypoint | Deliberator book and test plan, whole; DL-272 and DL-271 | `DLIB-TRG-02`, `DLIB-NEV-06`, owed `DLIB-IDM-04` | Only the deliberator peers gain a graph fault sink; ordinary peer audit writes remain the shared `LLMCall` path. |
| Shared ledger | Deliberator and operator books and test plans, all whole; conventions and drift register | `DLIB-IDM-02`, `DLIB-OBS-02`, `DLIB-OBS-05`; `OPR-STA-02`, `OPR-STA-03`, `OPR-IDM-02`, `OPR-IDM-03`; owed `DLIB-OBS-08` | D4 and D6 as decided. `DLIB-OBS-02`, `OPR-STA-02` and the old `OPR-IDM-02` are gray. Operator source confirms `audit:{correlation_id}` and `intent:{correlation_id}` are reused, with a new model call on each invocation. |
| Reproducibility reader | Deliberator book and test plan, whole | `DLIB-OBS-07` | Keep the original turn's full key, independent of listing order; never split colon-bearing keys. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No `contracts/` file; yes, the three guarantees specified above: new `DLIB-IDM-04` and `DLIB-OBS-08` (v1.15), rewritten `OPR-IDM-02` (v1.4), their Changelog/test-plan entries, DRIFT-104 and both rollups. Reading completed and this record saved before any code or test change.

**Contradictions found between a law and this spec:** Only the pre-identified `OPR-IDM-02` duplicate-command claim. `agents/operator/agent.py::_interpret_command` always calls the model; `agents/operator/store.py::write_command_audit` and `::write_intent` reuse their correlation-keyed nodes. D6 resolves it here. No additional contradiction found.

**Laws found silent where a decision was needed:** Neither book specifies settle-on-take or repeat-row keys; D1-D4 already resolve those silences and this sprint adds the two named deliberator clauses. No additional undecided design question.

**Clauses that were ⬜ and are now proven:** `DLIB-OBS-02` and rewritten `OPR-IDM-02`; new `DLIB-IDM-04` and `DLIB-OBS-08` are proven. `DLIB-TRG-02` and `OPR-STA-02` remain gray; neither is promoted by inference. The gate derives deliberator 32 / 63 and operator 19 / 50 (the operator plan footer was stale at 16 / 50).

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_request_is_settled_before_handling_and_publication` | `tests/test_served_request_settlement.py` | PASS | DLIB-IDM-04 |
| A2 | `test_a_turn_that_outlives_its_lock_is_served_once` | `tests/test_served_request_settlement.py` | PASS | DLIB-IDM-04 |
| A3 | `test_failed_replies_leave_a_fault_and_serve_the_next_request` | `tests/test_served_request_faults.py` | PASS | DLIB-IDM-04, DLIB-NEV-06 |
| A4 | `test_an_unresolved_request_is_refused_and_never_completed [False/True]; both existing bad-ready tests unchanged` | `tests/test_served_request_faults.py; tests/test_bus_azure_receiver.py` | PASS | DLIB-IDM-04, DLIB-NEV-06 (new proof) |
| A5 | `test_failed_settlement_propagates_before_any_handler_or_reply` | `tests/test_served_request_faults.py` | PASS | DLIB-IDM-04 |
| A6 | `test_one_request_is_taken_per_default_pass` | `tests/test_served_request_settlement.py` | PASS | DLIB-IDM-04 |
| A7 | `test_each_completion_is_its_own_unchanged_row` | `tests/test_llm_ledger_repeats.py` | PASS | DLIB-OBS-08 |
| A8 | `test_a_repeated_peer_turn_returns_its_own_ledger_key` | `agents/deliberator/tests/test_peer_ledger_repeats.py` | PASS | DLIB-OBS-08, DLIB-OBS-02 |
| A9 | `test_cost_and_outage_readers_count_repeat_rows` | `tests/test_llm_repeat_readers.py` | PASS | DLIB-OBS-08 |
| A10 | `test_ledger_is_idempotent_for_same_command` | `agents/operator/tests/test_operator_agent.py` | PASS | OPR-IDM-02, OPR-IDM-03 |
| B1 | `test_reproducibility_uses_the_original_in_either_listing_order [False/True]` | `tests/test_llm_repeat_readers.py` | PASS | DLIB-OBS-07 |
| B2 | `test_served_peer_uses_receive_wait_without_extra_idle_sleep` | `tests/test_deliberator_cold_peer_timing.py` | PASS | DLIB-IDM-04, DLIB-DEP-02, DLIB-PERF-02 |
| B3 | `existing served supervisor flag / operator interpret / researcher propose / forecaster forecast entrypoint tests, all unchanged` | `agents/{supervisor,operator,researcher,forecaster}/tests/test_*_entrypoint.py` | PASS | RES-TRG-03, RES-NEV-01; FORE-TRG-02, FORE-OUT-02, FORE-NEV-02; older supervisor/operator tests have no clause docstring (retained unchanged) |
| B4 | `test_reply_never_touches_the_receiver` | `tests/test_served_request_settlement.py` | PASS | DLIB-IDM-04 |

**Tests added beyond the plan:** `test_receive_batch_bounds_are_preserved` (both bounds), `test_receive_batch_tunable_can_still_be_raised` (no hard-coded batch), `test_repeat_allocation_takes_the_first_free_key` (gap and colon-bearing id), `test_serve_loop_forwards_the_given_fault_sink` (real loop wiring), `test_reply_faults_are_contained_with_the_default_sink` (optional-sink compatibility). Every new test cites its governing clause; no new proof skips.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/Downloads/project/ta-s256`; `.env` absent (`ENV_FILE_PRESENT=False`). All commands use `UV_OFFLINE=1` and `UV_NO_SYNC=1` (focused proofs also pass `--no-sync`); no live bus or model call.

**INTENT (before code):** Build D1-D6 in `C:/Users/yury_/Downloads/project/ta-s256`, branch `sprint-256-a-served-request-is-settled-when-it-is-taken`, clean starting HEAD and local `origin/main` `5535eb3250cdd76d30f83650c1f913788fec123d`. Prove the untouched Appendix before output; red A1/A2/A7; all A1-A10/B1-B4; every guard red/restored; the Appendix after output; scope and module-size checks; all runnable local CI steps with 100.00 % coverage. No network or live dependencies; no push, merge, version/lock change, STATE edit, contracts change or excluded production path. The handover's Closeout is the tracker for this unit of work.

**Result:** BUILT locally. A1-A10 and B1-B4 pass; the untouched and changed Appendix outputs match their references; 24 source guards failed and were restored; all 17 touched/new Python modules are below 200 lines. The scoped law cycle is complete. Full pytest passed at 100.00 % coverage; the offline dependency audit is NOT RUN, so the full CI gate is not green. No network, push, merge, version/lock edit, STATE edit or contracts change.

**Files changed:**

```text
agents/deliberator/entrypoint.py
agents/deliberator/laws/laws.md
agents/deliberator/laws/test-plan.md
agents/deliberator/tests/test_peer_ledger_repeats.py
agents/operator/laws/laws.md
agents/operator/laws/test-plan.md
agents/operator/tests/test_operator_agent.py
agents/operator/tests/test_operator_store.py
docs/laws/INDEX.md
docs/laws/drift-register.md
docs/laws/ledger.md
docs/sprints/INDEX.md
docs/sprints/README.md
docs/sprints/sprint-256-a-served-request-is-settled-when-it-is-taken.md
kernel/bus_azure_config.py
kernel/bus_azure_receiver.py
kernel/llm_ledger.py
kernel/serve_loop.py
scripts/deliberation_reproducibility.py
tests/served_request_helpers.py
tests/test_bus_azure_receiver.py
tests/test_bus_azure_receiver_edges.py
tests/test_deliberator_cold_peer_timing.py
tests/test_llm_ledger_repeats.py
tests/test_llm_repeat_readers.py
tests/test_served_request_faults.py
tests/test_served_request_settlement.py
```

**Design decisions:** recorded as [`DL-272`](../design-log.md); D1-D6 built as decided, no additional design decision or departure requiring DL-273.

**The Appendix script, before:**

```text
Tree: C:/Users/yury_/Downloads/project/ta-s256
Untouched source HEAD: 5535eb3250cdd76d30f83650c1f913788fec123d
Command: PYTHONPATH=. UV_OFFLINE=1 uv run --no-sync python s256_appendix.py
1. requests taken in the first pass: 3
2. order of events for the first request: ['handled', 'published', 'settled']
3. a turn that outlives its lock: raised LockLostError after ['handled', 'published']
4. a reply that cannot be published: settled 0 abandoned for redelivery 1
5. two completions of one turn: ledger rows 1 output tokens recorded 7738
   the second completion's key: llmcall:deliberator-proponent:sched-x:GILD:defender:r2
Appendix exit: 0
ENV_FILE_PRESENT=False
```

**Proof — the red run first:**

```text
Command: UV_OFFLINE=1 uv run --no-sync pytest --no-cov -q tests/test_served_request_settlement.py tests/test_llm_ledger_repeats.py
FFF                                                                      [100%]
================================== FAILURES ===================================
___________ test_request_is_settled_before_handling_and_publication ___________
tests\test_served_request_settlement.py:21: in test_request_is_settled_before_handling_and_publication
    assert events == ["settled", "handled", "one", "published"]
E   AssertionError: assert ['handled', '...d', 'settled'] == ['settled', '..., 'published']
E
E     At index 0 diff: 'handled' != 'settled'
E     Use -v to get more diff
______________ test_a_turn_that_outlives_its_lock_is_served_once ______________
tests\test_served_request_settlement.py:31: in test_a_turn_that_outlives_its_lock_is_served_once
    assert serve_once(consumer, served) == 1
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
kernel\serve_loop.py:75: in serve_once
    consumer.reply(bus.request(request))
kernel\bus_azure_receiver.py:103: in reply
    self._complete(raw)
kernel\bus_azure_receiver.py:158: in _complete
    self._receiver.complete_message(raw)
tests\served_request_helpers.py:42: in complete_message
    raise LockLostError("message lock expired")
E   tests.served_request_helpers.LockLostError: message lock expired
________________ test_each_completion_is_its_own_unchanged_row ________________
tests\test_llm_ledger_repeats.py:41: in test_each_completion_is_its_own_unchanged_row
    assert [node.key for node in nodes] == [first, first + ":repeat-1", first + ":repeat-2"]
E   AssertionError: assert ['llmcall:del...:defender:r2'] == ['llmcall:del...:r2:repeat-2']
E
E     At index 1 diff: 'llmcall:deliberator-proponent:sched-x:GILD:defender:r2' != 'llmcall:deliberator-proponent:sched-x:GILD:defender:r2:repeat-1'
E     Use -v to get more diff
=========================== short test summary info ===========================
FAILED tests/test_served_request_settlement.py::test_request_is_settled_before_handling_and_publication
FAILED tests/test_served_request_settlement.py::test_a_turn_that_outlives_its_lock_is_served_once
FAILED tests/test_llm_ledger_repeats.py::test_each_completion_is_its_own_unchanged_row
3 failed in 1.61s
Red exit: 1
```

**The Appendix script, after:**

```text
Command: PYTHONPATH=. UV_OFFLINE=1 uv run --no-sync python s256_appendix.py
1. requests taken in the first pass: 1
2. order of events for the first request: ['settled', 'handled', 'published']
3. a turn that outlives its lock: served 1, no error
4. a reply that cannot be published: settled 1 abandoned for redelivery 0
5. two completions of one turn: ledger rows 2 output tokens recorded 15479
   the second completion's key: llmcall:deliberator-proponent:sched-x:GILD:defender:r2:repeat-1
After exit: 0
```

**Proof — the green run:**

```text
After all 24 source plants were restored:
UV_OFFLINE=1 uv run --no-sync pytest --no-cov -q [all S256 proofs, five edited files, existing reproducibility suite, four unchanged entrypoint suites]
...............................................                          [100%]
47 passed in 6.05s
Restored focused exit: 0
```

**Guards planted:** each source plant below failed its targeted proving test(s); all six production files were checked against their saved bytes after every restore. G09 also made A8, A9 and A10 red; G10 made A9 red. The G12 result was 1 failed / 1 passed (both listing orders ran). No plant completed an unresolved message. B3 uses unchanged existing tests, so it adds no new guard. G01-G08 prove A1-A6/B4; G09-G11 prove A7-A10 and first-free allocation; G12 proves B1; G13-G14 prove B2; G15-G18 prove loop wiring and the receive tunable/bounds; G19-G22 prove A3 containment and provenance; G23 proves the unchanged ledger schema; G24 proves default-sink containment. Raw pytest logs and guard-to-test node ids are in `C:/Users/yury_/AppData/Local/Temp/ta-s256-evidence/guards.json` and `G01.txt` through `G24.txt`.

```text
G01: RED exit 1 (1 failed in 1.39s); RESTORED byte-for-byte; remove settlement before handling
G02: RED exit 1 (1 failed in 1.21s); RESTORED byte-for-byte; move settlement after publication on decoded requests
G03: RED exit 1 (1 failed in 1.24s); RESTORED byte-for-byte; reraise failed reply instead of continuing
G04: RED exit 1 (1 failed in 1.24s); RESTORED byte-for-byte; omit abandon on unresolved claim
G05: RED exit 1 (1 failed in 1.19s); RESTORED byte-for-byte; omit dead-letter at delivery limit
G06: RED exit 1 (1 failed in 1.17s); RESTORED byte-for-byte; swallow failed take inside a boundary
G07: RED exit 1 (1 failed in 1.17s); RESTORED byte-for-byte; restore default batch of ten
G08: RED exit 1 (1 failed in 1.20s); RESTORED byte-for-byte; make reply abandon through the receiver
G09: RED exit 1 (4 failed in 5.10s); RESTORED byte-for-byte; deduplicate repeated completions
G10: RED exit 1 (2 failed in 4.51s); RESTORED byte-for-byte; lose each completion's output token count
G11: RED exit 1 (2 failed in 1.22s); RESTORED byte-for-byte; skip repeat-1 instead of first free suffix
G12: RED exit 1 (1 failed, 1 passed in 5.38s); RESTORED byte-for-byte; let a repeat replace the reproducibility hash
G13: RED exit 1 (1 failed in 4.00s); RESTORED byte-for-byte; give the peer only a collecting sink
G14: RED exit 1 (1 failed in 3.88s); RESTORED byte-for-byte; add peer idle sleep
G15: RED exit 1 (1 failed in 1.23s); RESTORED byte-for-byte; drop the supplied sink at the serve-loop call
G16: RED exit 1 (1 failed in 1.23s); RESTORED byte-for-byte; hard-code the batch instead of honoring the tunable
G17: RED exit 1 (1 failed in 1.26s); RESTORED byte-for-byte; weaken the batch lower bound
G18: RED exit 1 (1 failed in 1.21s); RESTORED byte-for-byte; weaken the batch upper bound
G19: RED exit 1 (1 failed in 1.21s); RESTORED byte-for-byte; silently swallow reply publication failure
G20: RED exit 1 (1 failed in 1.22s); RESTORED byte-for-byte; misattribute the failed reply to its caller
G21: RED exit 1 (1 failed in 1.22s); RESTORED byte-for-byte; lose the reply's source module
G22: RED exit 1 (1 failed in 1.22s); RESTORED byte-for-byte; lose the reply's capability
G23: RED exit 1 (1 failed in 1.14s); RESTORED byte-for-byte; remove an existing ledger property
G24: RED exit 1 (1 failed in 1.27s); RESTORED byte-for-byte; reraise a reply fault with the default sink
24 guards verified red and restored
```

**Existing tests edited:** exactly the five expected tests in five files:

- `tests/test_bus_azure_receiver.py::test_reply_abandons_pending_message_when_publish_fails` -> `test_reply_failure_does_not_abandon_a_settled_request`: publication now raises to the serve boundary, with one completed request and no abandon; the two decode-refusal tests were not edited.
- `tests/test_bus_azure_receiver_edges.py::test_reply_publish_failure_without_pending_source_does_not_raise` -> `test_reply_publish_failure_propagates_to_the_serve_boundary`: containment now belongs to `serve_once`, not `reply`.
- `agents/operator/tests/test_operator_agent.py::test_ledger_is_idempotent_for_same_command`: one audit/intent and one correlation now have two LLMCall rows; also proves both row keys and the shared audit/intent keys.
- `agents/operator/tests/test_operator_store.py::test_write_llm_call_records_operator_attribution`: the repeat returns its own appended row instead of the original object.
- `tests/test_deliberator_cold_peer_timing.py::test_served_peer_uses_receive_wait_without_extra_idle_sleep`: the stand-in accepts the new sink and proves it is a GraphFaultSink over this peer's graph, with a collecting inner sink and idle sleep still zero.

**Readers of `LLMCall` rows:** searched Python, PowerShell, shell and SQL under kernel/agents/orchestration/surfaces/scripts; the purpose-specific readers are:

- `surfaces/dashboard/llm_costs.py:67`: lists all rows, adding each row's token groups, call count and price to model/agent totals, regardless of key length; A9 proves both rows count.
- `surfaces/dashboard/llm_cost_tokens.py:51`: reads each row's properties, not its key; a repeat has the same schema and its own token groups.
- `scripts/check_llm_outage.py:43`: passes every listed row to the classifier; A9 runs the CLI on the injected graph, with dotenv disabled.
- `kernel/llm_outage.py:90` / `:101`: classifies and counts all supplied rows by response hash/stop reason, never by a parsed key; A9 proves two calls.
- `scripts/deliberation_reproducibility.py:111`: keeps the original hash and skips a key beginning with the full canonical key plus `:repeat-`; B1 proves both listing orders, including correlation IDs containing colons. Existing legacy-shaped test rows still work.
- `agents/deliberator/store.py:84` / `:85`: resolves the exact `llm_call_key` and links that row by `PRODUCED_BY`; a repeat key is passed whole and resolves like any original key. This reader was omitted from the planner's list; no implementation edit is needed.
- `agents/operator/store.py:46` / `:72`: consume the returned LLMCall node when linking the shared audit by `PRODUCED_BY`; each call adds its own row's link, while the audit/intent nodes remain shared.
- `kernel/llm_ledger.py:126`: the writer's existence lookup now allocates the first free full key; it never parses a correlation id or reads a repeat as an original completion.

Generic graph adapters and the graph-label vocabulary are schema readers, not special LLMCall consumers; this sprint adds no label or property.

**Module line counts:** all 17 touched/new Python modules are below 200 lines.

```text
agents/deliberator/entrypoint.py: 121
agents/deliberator/tests/test_peer_ledger_repeats.py: 43
agents/operator/tests/test_operator_agent.py: 182
agents/operator/tests/test_operator_store.py: 43
kernel/bus_azure_config.py: 116
kernel/bus_azure_receiver.py: 160
kernel/llm_ledger.py: 154
kernel/serve_loop.py: 104
scripts/deliberation_reproducibility.py: 142
tests/served_request_helpers.py: 80
tests/test_bus_azure_receiver.py: 191
tests/test_bus_azure_receiver_edges.py: 48
tests/test_deliberator_cold_peer_timing.py: 49
tests/test_llm_ledger_repeats.py: 105
tests/test_llm_repeat_readers.py: 99
tests/test_served_request_faults.py: 111
tests/test_served_request_settlement.py: 86
```

**Scope and law comparison:**

```text
Command: git diff main -- pyproject.toml uv.lock infra orchestration/packs scripts/servicebus_prepare_routes.py agents/deliberator/poll.py agents/deliberator/servicebus_peer_client.py agents/deliberator/servicebus_reply_inbox.py kernel/deliberation_prompts.py
Output: nothing
Exit: 0
Command: git diff 5535eb3250cdd76d30f83650c1f913788fec123d -- contracts docs/STATE.md pyproject.toml uv.lock
Output: nothing
Exit: 0
Clause text comparison against starting HEAD:
agents/deliberator/laws/laws.md: added=['DLIB-IDM-04', 'DLIB-OBS-08'], changed=[], removed=[]
61 existing clauses unchanged
agents/operator/laws/laws.md: added=[], changed=['OPR-IDM-02'], removed=[]
49 existing clauses unchanged
```

`pyproject.toml` and `uv.lock` were not touched. The handover's protected-file diff prints nothing. No `.env` exists; the temporary Appendix and mutation runners were deleted from the worktree before staging. The six production files match the byte hashes saved after guard restoration and used by the full CI run; G24 was restored to those same bytes and the final 47-test run passed.

**`make ci`:** full redirected output is `C:/Users/yury_/AppData/Local/Temp/ta-s256-evidence/make-ci.txt`. The actual target ran with `UV_OFFLINE=1`, `UV_NO_SYNC=1`, `PIP_NO_INDEX=1`, offline npm/git settings, and a Python socket guard rejecting external addresses before I/O (local unit-test servers are allowed). Exit **2**: steps 1-12 passed, step 13's dependency audit could not obtain advisory data. The two remaining target commands were run explicitly and passed.

| Step | Check | Result |
| --- | --- | --- |
| 1 | Ruff lint | PASS |
| 2 | Ruff format | PASS |
| 3 | mypy | PASS |
| 4 | Import boundaries | PASS, 5 contracts kept |
| 5 | Module size | PASS |
| 6 | Module headers | PASS |
| 7 | Law coverage | PASS |
| 8 | PARAM/settings sync | PASS (existing envelope warnings only) |
| 9 | Sprint status | PASS |
| 10 | Markdown links | PASS |
| 11 | Version scheme | PASS; no bump |
| 12 | Full pytest and coverage | PASS, 4322 passed / 8 skipped / 100.00 % |
| 13 | Dependency audit | **NOT RUN**: audit invocation failed before external advisory lookup, because this handover prohibits network access |
| 14 | detect-secrets | PASS, explicitly after the stopped target |
| 15 | Untracked secrets | PASS, explicitly after the stopped target |

Actual command/output excerpts from the redirected file:

```text
Command: make ci > C:/Users/yury_/AppData/Local/Temp/ta-s256-evidence/make-ci.txt 2>&1
1586 files already formatted
Success: no issues found in 1163 source files
Contracts: 5 kept, 0 broken.
TOTAL                                                           20065      0   4240      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
========= 4322 passed, 8 skipped, 2470 warnings in 330.58s (0:05:30) ==========
uv run python scripts/check_dependency_audit.py
OSError: S256 offline proof: external network is prohibited by the handover
make: *** [Makefile:59: ci] Error 1
MAKE_CI_EXIT=2
Continuing the remaining two ci target commands explicitly after the unavailable dependency audit.
Command: uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
DETECT_SECRETS_EXIT=0
Command: uv run python scripts/check_untracked_secrets.py
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 6 new file(s)
UNTRACKED_SECRETS_EXIT=0
```

The eight skips are existing suite skips, not new S256 proof skips. The dependency audit's error names `pypi.org/pypi/aiohappyeyeballs/2.7.1/json`; no clean advisory result is claimed. `.secrets.baseline` is unchanged.

**Final documentation and staged-file checks:**

```text
Command: UV_OFFLINE=1 UV_NO_SYNC=1 uv run pre-commit run --files [the 27 staged S256 paths]
FINAL_PRE_COMMIT_EXIT=0
Ruff lint................................................................Passed
Ruff format..............................................................Passed
mypy.....................................................................Passed
markdownlint-cli2........................................................Passed
Detect secrets...........................................................Passed
module size (warn 150 / hard block 200)..................................Passed
coding-agent module header (Agent:/Role:)................................Passed
law coverage ledger......................................................Passed
import-linter (agents are islands).......................................Passed
Command: UV_OFFLINE=1 UV_NO_SYNC=1 uv run python scripts/check_sprint_status.py
FINAL_SPRINT_STATUS_EXIT=0
docs_seen=261 SPEC=11 BUILT=1 MERGED=249 UNMAPPED=0 MISSING=0
Command: UV_OFFLINE=1 UV_NO_SYNC=1 uv run python scripts/check_markdown_links.py
FINAL_MARKDOWN_LINKS_EXIT=0
Command: git diff --cached --check
Output: nothing
Exit: 0
```

Full final hook output: `C:/Users/yury_/AppData/Local/Temp/ta-s256-evidence/final-pre-commit.txt`; status/link outputs: `final-sprint-status.txt` and `final-markdown-links.txt` in the same directory. YAML/TOML hooks had no changed files to check; neither was an S256 proof skip. No files were rewritten by hooks.

**`make gate-ran`:** owed by the planner at merge.

**Not met / verified failing:** Full `make ci` exit 0 is **not done** (verified exit 2 at unavailable dependency audit). Dependency audit is **NOT RUN**, not clean. Online audit, exact-SHA remote gate, version/lock bump, merge, F1, deployment and F2 are **not done**, owed by the planner; this handback proves local unit behavior only.

---

## Return notes

- The untouched source was HEAD `5535eb3250cdd76d30f83650c1f913788fec123d`, not the Appendix historical label `9ee2008d`; its six printed before lines matched exactly, so the stop condition did not apply.
- The `ci:` target has **15** steps; AGENTS.md's short form says 14. CLAUDE.md explicitly calls for recounting the target; no gate or rule file was changed.
- A9's outage report has no token-total field: `kernel.llm_outage.outage_report` counts calls and classifies failures. The proof checks both calls there and in the CLI, and both rows' token/cost totals in the dashboard. No new report field or production reader change was invented.
- B3 explicitly requires the four existing entrypoint suites to pass without edits. The old supervisor/operator entrypoint tests lack clause docstrings; they remain unchanged. The researcher and forecaster tests cite their own clauses. All newly written proofs cite clauses.
- The operator test-plan footer's old `16 / 50` was stale: before this sprint the rollups claimed 18 / 50, and after the scoped row promotion the coverage checker derives 19 / 50. Both rollups and the footer now agree.
- D1 intentionally prevents bus retry after a settled peer dies or loses its reply; fail-open remains on the existing manager wait. No manager, reply-inbox, subscription, pack, prompt, judge or DSPy code changed.
- While this sprint was built, the planner advanced local `main` to `a4c3dda05475d3c03bac0f11bf35f830bce6a4bc` with documentation for S257/work-queue 113. This branch keeps the required starting base; no rebase or merge was performed. Protected production diffs against the advanced `main` remain empty.
- Commit only on this sprint branch. The planner owes the PATCH bump and lock sync, online dependency audit, exact-SHA remote gate, merge, F1, deployment and F2.

---

## Planner's review and merge-time work — 2026-10-08 14:43 AEDT

**The handback against the checklist.** All twelve items are met. Item 11 names one step as NOT RUN, the
dependency audit, which needs the network; the planner runs the whole gate below.

**Re-measured by the planner, not read from the builder's logs.**

- The Appendix script on the built tree prints the *after* block, equal to the spec's.
- The planner's own failed-reply script (two requests, a bus whose publish fails, a graph fault sink): both
  handlers ran once, 2 settled, 0 abandoned, 0 dead-lettered, one `Fault` from `kernel.serve_loop`, no
  error raised. On `main` the same script abandons both requests and writes no fault.
- Six pieces of the old behaviour put back one at a time, each red, each restored: the request not settled
  at the take (11 tests fail), a pass taking ten (2), a failed reply ending the loop (3), a repeated key
  returning the first row (6), the reproducibility lookup keeping the row listed last (1), the peer
  passing no fault sink (1). The 36 tests of the sprint's files are green before and after.
- The five existing tests the builder edited are the five the spec named. Each edit was read: every one
  asserts the new behaviour in place of the one removed, and none is weakened.
- The code is the decided design: D1 to D4 and the reader, nothing more. The protected paths are untouched.

**Changed by the planner at merge.**

- `test_ledger_is_idempotent_for_same_command` is renamed
  `test_same_command_shares_audit_and_intent_and_records_each_call`, in the test, the operator's test plan
  (two rows) and DRIFT-104. It now asserts two ledger rows, so the old name said the opposite. The
  builder's tables above keep the name it had at handback.
- The version is `0.123.01`. `uv lock` changed the version line only; 180 packages before and after.
- `main` was merged in. The two sprint tables conflicted on adjacent rows: this sprint's row is the
  branch's, sprint 257's row is `main`'s. `docs/STATE.md`, the design log and the work queue are `main`'s.

**Accepted as built.**

- The builder promoted `DLIB-OBS-02` (spend is attributable per calling agent) on test A8. The spec did not
  ask for it; the test asserts what the clause says, on both rows of a repeated turn.
- The operator's test-plan footer read 16 of 50 where both rollups read 18; it now reads the derived 19.
- A correlation id that itself ended in `:repeat-N` would share a key with another id's repeat. No caller
  writes one: a debate's id is `<run>:<ticker>:<role>:r<n>` and the operator's is a hash.

**Owed, in the order of "Sequencing after merge":** the gate on Windows and on the remote for the merged
SHA, the merge, F1 on the live namespace, the deploy on the operator's word, F2. Their results are recorded
in `docs/STATE.md` and in this file's Status line.

---

## Appendix — the reproduction, and the reference shape

### The script

Save as `s256_appendix.py` in the worktree's root, run it, delete it before you commit.

```python
"""Sprint 256 reproduction. No network, no .env, no LLM call.

Run from the root of a checkout:
    PYTHONPATH=. uv run --no-sync python s256_appendix.py
"""

from __future__ import annotations

from tests.bus_azure_receiver_helpers import (
    FailingPublishBus,
    FakeReceiver,
    RawMessage,
    raw_ready,
    request,
)

from kernel import (
    AzureServiceBusBus,
    AzureServiceBusRequestConsumer,
    AzureServiceBusSettings,
    InMemoryGraphStore,
    InProcessBus,
)
from kernel.llm_ledger import write_llm_call
from kernel.serve_loop import serve_once

# The fleet's own settings: nothing is overridden but the absent connection string.
FLEET = AzureServiceBusSettings(_env_file=None, connection_string=None)


class LockLostError(Exception):
    """Stands in for azure.servicebus.exceptions.MessageLockLostError."""


class Receiver(FakeReceiver):
    """Records when a message is settled; its lock runs out once the handler starts."""

    def __init__(self, messages: list[RawMessage], events: list[str]) -> None:
        super().__init__(messages)
        self.events = events
        self.lock_runs_out = False

    def complete_message(self, message: RawMessage) -> None:
        if self.lock_runs_out and "handled" in self.events:
            raise LockLostError("The lock on the message lock has expired.")
        self.events.append("settled")
        super().complete_message(message)


def scene(refs: tuple[str, ...], *, publish_fails: bool = False):
    events: list[str] = []
    graph = InMemoryGraphStore()
    setup = AzureServiceBusBus(settings=FLEET)
    receiver = Receiver([raw_ready(graph, setup, request(ref)) for ref in refs], events)
    reply_bus = FailingPublishBus() if publish_fails else AzureServiceBusBus(settings=FLEET)
    if not publish_fails:
        reply_bus.subscribe("operator.reply", lambda event: events.append("published"))
    consumer = AzureServiceBusRequestConsumer(
        reply_bus,
        graph,
        topic="echo.requests",
        subscription_name="echo",
        settings=FLEET,
        receiver=receiver,
    )
    served = InProcessBus()

    def handler(payload: dict[str, object]) -> dict[str, object]:
        events.append("handled")
        return {"ref": payload["ref"], "ok": True}

    served.register("echo", "echo", handler)
    return consumer, served, receiver, events


consumer, served, receiver, events = scene(("one", "two", "three"))
print("1. requests taken in the first pass:", serve_once(consumer, served))
print("2. order of events for the first request:", events[:3])

consumer, served, receiver, events = scene(("slow",))
receiver.lock_runs_out = True
try:
    outcome = f"served {serve_once(consumer, served)}, no error"
except LockLostError as exc:
    outcome = f"raised LockLostError after {events}"
print("3. a turn that outlives its lock:", outcome)

consumer, served, receiver, events = scene(("lost",), publish_fails=True)
serve_once(consumer, served)
print(
    "4. a reply that cannot be published: settled",
    len(receiver.completed),
    "abandoned for redelivery",
    len(receiver.abandoned),
)

ledger = InMemoryGraphStore()
for tokens_out in (7738, 7741):
    node = write_llm_call(
        ledger,
        calling_agent="deliberator-proponent",
        correlation_id="sched-x:GILD:defender:r2",
        model="gpt-5.5",
        prompt_hash="p",
        response_hash="r",
        tokens_in=100,
        tokens_out=tokens_out,
        latency_ms=70000,
    )
rows = ledger.list_nodes("LLMCall")
print(
    "5. two completions of one turn: ledger rows",
    len(rows),
    "output tokens recorded",
    sum(int(row.props["tokens_out"]) for row in rows),
)
print("   the second completion's key:", node.key)
```

### Before — `main` at `9ee2008d`, measured 2026-10-08

```text
1. requests taken in the first pass: 3
2. order of events for the first request: ['handled', 'published', 'settled']
3. a turn that outlives its lock: raised LockLostError after ['handled', 'published']
4. a reply that cannot be published: settled 0 abandoned for redelivery 1
5. two completions of one turn: ledger rows 1 output tokens recorded 7738
   the second completion's key: llmcall:deliberator-proponent:sched-x:GILD:defender:r2
```

### After — the prototype, measured 2026-10-08

```text
1. requests taken in the first pass: 1
2. order of events for the first request: ['settled', 'handled', 'published']
3. a turn that outlives its lock: served 1, no error
4. a reply that cannot be published: settled 1 abandoned for redelivery 0
5. two completions of one turn: ledger rows 2 output tokens recorded 15479
   the second completion's key: llmcall:deliberator-proponent:sched-x:GILD:defender:r2:repeat-1
```

### The live check behind the two *live* rows

The planner's script, kept outside the repo, is the repo's own `scripts/servicebus_receiver_live_check.py`
with a handler that sleeps 70 seconds. `main`'s code on 2026-10-07, then the prototype on 2026-10-08:

```text
main, 2026-10-07                         the prototype, 2026-10-08
lock_duration            0:01:00         0:01:00
first serve              raised MessageLockLostError    1, no error
replies after it         1               1
handler calls            1               1
second consumer served   1               0
handler calls in total   2               1
replies after it         1               0
left on the subscription 0 active, 0 dead               0 active, 0 dead
```

### The reference shape

The prototype the *after* block and the live check ran on. It is a shape, not text to paste: it has no
tests, it leaves an unused import behind, and it does not touch the reproducibility script.

```diff
--- a/kernel/bus_azure_receiver.py
+++ b/kernel/bus_azure_receiver.py
@@ def poll(self) -> list[AgentMessage]:
             except (RuntimeError, TypeError, ValueError, ValidationError):
                 self._reject(raw)
                 continue
-            self._pending[request.id] = raw
+            self._complete(raw)
             requests.append(request)
         return requests

     def reply(self, response: AgentMessage) -> None:
-        """Publish a claim-checked response and ack/abandon the source message."""
-        correlation_id = response.correlation_id
-        raw = self._pending.get(correlation_id) if correlation_id is not None else None
-        try:
-            self._publish_response(response)
-        except Exception:
-            if raw is not None and correlation_id is not None:
-                self._reject(raw)
-                self._pending.pop(correlation_id, None)
-            return
-        if raw is not None and correlation_id is not None:
-            self._complete(raw)
-            self._pending.pop(correlation_id, None)
+        """Publish a claim-checked response; the request was settled when taken."""
+        self._publish_response(response)
--- a/kernel/bus_azure_config.py
+++ b/kernel/bus_azure_config.py
     receive_max_messages: int = tunable(
-        10,
+        1,
--- a/kernel/serve_loop.py
+++ b/kernel/serve_loop.py
-def serve_once(consumer: RequestConsumer, bus: MessageBus) -> int:
+def serve_once(
+    consumer: RequestConsumer, bus: MessageBus, *, sink: FaultSink | None = None
+) -> int:
+    resolved = sink if sink is not None else CollectingFaultSink()
     requests = consumer.poll()
     for request in requests:
-        consumer.reply(bus.request(request))
+        response = bus.request(request)
+        with fault_boundary(
+            resolved,
+            agent=request.recipient,
+            module="kernel.serve_loop",
+            capability=request.capability,
+            reraise=False,
+        ):
+            consumer.reply(response)
     return len(requests)
--- a/agents/deliberator/entrypoint.py
+++ b/agents/deliberator/entrypoint.py
         poll_interval=PEER_SERVE_IDLE_SLEEP_SECONDS,
+        sink=GraphFaultSink(graph, CollectingFaultSink()),
     )
--- a/kernel/llm_ledger.py
+++ b/kernel/llm_ledger.py
-    key = f"llmcall:{calling_agent}:{correlation_id}"
-    current = graph.get_node("LLMCall", key)
-    if current is not None:
-        return current
+    first = f"llmcall:{calling_agent}:{correlation_id}"
+    key, repeat = first, 0
+    while graph.get_node("LLMCall", key) is not None:
+        repeat += 1
+        key = f"{first}:repeat-{repeat}"
     return graph.merge_node(
```
