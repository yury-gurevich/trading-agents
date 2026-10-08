<!-- Agent: planning | Role: sprint handover -->
# Sprint 256 — A served request is settled when it is taken, and every completion is its own ledger row

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-256-a-served-request-is-settled-when-it-is-taken`
**Status:** SPEC
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

- [ ] A request is completed before its handler runs, and a completion that would have failed after a
      long handler no longer exists (A1, A2).
- [ ] A reply that cannot be published leaves one `Fault`, abandons nothing, and the loop serves the next
      request (A3).
- [ ] A request that cannot be decoded is still abandoned, or dead-lettered at the limit, and never
      completed (A4).
- [ ] One request is taken per pass by default (A6).
- [ ] A completion under an existing ledger key is its own row; no row is overwritten (A7, A8).
- [ ] Every reader of `LLMCall` rows counts or reads a repeat correctly (A9, B1).
- [ ] The Appendix script prints the *before* block on the untouched tree and the *after* block on the
      built one.
- [ ] `pyproject.toml`, `uv.lock`, `infra/`, the packs, the manager's modules and the role prompts are
      untouched.
- [ ] Law cycle done in two books, DRIFT-104 filed as corrected, or an existing clause named in a new
      one's place.
- [ ] Every new guard planted, watched to fail, restored, stated per guard.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage, or each step that could not run named as NOT RUN.

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
| _to be filled by the builder_ | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** _to be filled_

**Contradictions found between a law and this spec:** _to be filled_

**Laws found silent where a decision was needed:** _to be filled_

**Clauses that were ⬜ and are now proven:** _to be filled_

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | _to be filled_ | | | |

**Tests added beyond the plan:** _to be filled_

---

## Closeout — evidence

**Status:** _to be filled: BUILT_

**Tree the proofs ran in (and `.env` present?):** _to be filled_

**Result:** _to be filled_

**Files changed:** _to be filled_

**Design decisions:** recorded as [`DL-272`](../design-log.md); _anything the builder added, to be filled_

**The Appendix script, before:**

```text
to be filled
```

**Proof — the red run first:**

```text
to be filled
```

**The Appendix script, after:**

```text
to be filled
```

**Proof — the green run:**

```text
to be filled
```

**Guards planted:** _to be filled, one line per guard_

**Existing tests edited:** _to be filled, one line per test with the reason_

**Readers of `LLMCall` rows:** _to be filled_

**Module line counts:** _to be filled_

**`make ci`:** _to be filled: the output file, the exit code, passed and skipped, coverage, each NOT RUN step_

**`make gate-ran`:** owed by the planner at merge.

**Not met / verified failing:** _to be filled_

---

## Return notes

- _to be filled by the builder_

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
