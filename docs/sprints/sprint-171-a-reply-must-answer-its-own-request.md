<!-- Agent: deliberator | Role: sprint spec — correlate peer replies so a verdict belongs to its own order -->
# S171 — a reply must answer its own request

**Closes:** [DL-102](../design-log.md) · **Type:** fix ·
**Target version:** next available PATCH (`0.90.01` if this ships before
[S169](sprint-169-one-switch-and-a-deploy-that-keeps-it.md)/[S170](sprint-170-one-llm-adapter-in-the-plumbing.md);
this sprint depends on neither and should go first) ·
**Branch:** `sprint-171-a-reply-must-answer-its-own-request`

> Handover to a delegated coding agent. Everything under **Measured** was observed on the live
> deployed fleet on 2026-08-08 (`:s169`, run `check-s169-openai-cutover`). Everything marked
> **Assumed** has *not* been verified — check it before building on it.

## Why

**The deliberation manager pairs a request with whatever reply is at the head of the queue.**

**Measured.** The OpenAI cutover was working — the proponent made **18 real `gpt-5.5` completions**
and `role_models` recorded `gpt-5.5` for all three roles — yet the `DeliberationRun` came out
`real_debate_count=0, failed_open_count=18`, its `failed_open_reason` an **Anthropic** usage-limit
error. The manager never read the proponent's answers. It drained 18 stale error replies left by an
earlier run 5.5 hours before.

The `deliberator-manager.reply` subscription held **84 active messages**: oldest enqueued
**05:51:33 UTC** (the earlier `check-s166` run, which failed every order on the Anthropic limit),
newest **11:20:11 UTC** — this run's own proponent replies, which went in and were never consumed.

The cause is [`agents/deliberator/peer_client.py:143-154`](../../agents/deliberator/peer_client.py#L143):

```python
messages = receiver.receive_messages(max_message_count=1, max_wait_time=...)
if not messages:
    raise RuntimeError("no deliberator peer reply received")
raw = messages[0]
receiver.complete_message(raw)
data = json.loads(_body_text(raw))
return data          # <- whatever was at the head. No correlation, no check.
```

🚨 **The error case is the benign one.** It raises and the order fails open — noisy, safe, and what
we saw. The **success** path is the dangerous one: `debate_turn` continues to
`DebateTurnReply.model_validate(reply.payload)` and accepts a stale success reply as a debate turn
**for a different ticker's order**. The `DeliberationRun` then records a verdict, a transcript and a
rationale that are about some other decision — with no fault, no error and a green acceptance gate.
That is exactly the provenance guarantee the veto exists to provide: *which model reviewed this
order, and about what*.

**The fix is small, because the correlation key is already on the wire.** Measured by reading the
code, not inferred:

| Step | Where | Fact |
| --- | --- | --- |
| Manager publishes the request | `peer_client.debate_turn` | `AgentMessage` with id `M`; ready event `ref=str(M)` |
| Peer replies | [`kernel/bus.py:136,158`](../../kernel/bus.py#L136) | `bus.request` sets `correlation_id = message.id` on **both** response and error |
| Envelope enforces it | [`kernel/envelope.py:54`](../../kernel/envelope.py#L54) | response/error **must** carry a `correlation_id` |
| Reply announced | [`kernel/bus_azure_receiver.py:135-146`](../../kernel/bus_azure_receiver.py#L135) | ready event `run_id = str(response.correlation_id)` |

So every reply already announces the id of the request it answers. `_read_ready_event` just never
looks at it.

**Assumed, unverified:** that `deliberator-manager` is the only caller of `_read_ready_event`, and
that no other agent performs Service Bus request/reply today. Grep before choosing where the fix
lives.

## The second half: what *manufactures* the backlog

🚨 **Correlation alone will not make the veto work.** Measured on the same fleet, run
`check-s169-debate-2`, with the reply queue **empty**:

| Side | Setting | Value |
| --- | --- | --- |
| Peer | `receive_timeout_seconds` ([`bus_azure_config.py:67`](../../kernel/bus_azure_config.py#L67)) | **5 s** blocking receive |
| Peer | `serve_loop` idle sleep ([`serve_loop.py:23`](../../kernel/serve_loop.py#L23)) | **60 s** |
| Manager | `request_timeout_seconds` (`DeliberatorSettings`) | **30 s** |

A peer that has gone idle is awake for ~5 s in every ~65 s. **The manager gives up after 30 s, so a
cold peer cannot answer inside the window.** Observed exactly: the first turn faulted at **11:50:07**
with `no deliberator peer reply received`; the peers then woke, and from **11:50:41** the debate ran
normally through all three roles including the judge (`deliberator-manager`, 11:51:20).

**This is the mechanism that produced the 84-message backlog.** Every timed-out turn leaves the
peer's late reply in the subscription as an orphan, which is then read as the answer to a *later*
request. The two defects feed each other: the timing mismatch manufactures orphans, and the missing
correlation converts them into wrong verdicts. Fixing only correlation yields a manager that
correctly dead-letters orphans and **still fails open on every cold start**.

**Additional steps required, therefore:**

- Make the manager's reply budget exceed the peer's worst-case pickup latency, or make an idle peer
  pick up promptly (a long-poll receive rather than a short receive plus a long sleep). State which
  you chose and why; do not simply enlarge `request_timeout_seconds` until it happens to pass —
  bound it against the measured peer wake-up, and record the numbers.
- The `le=` bound on `request_timeout_seconds` is **120 s**; if the chosen budget needs more, that
  bound is part of the change, not an obstacle to route around.

**Additional success factor:** a debate started against **cold** peers (both scaled from idle, no
recent traffic) completes with `failed_open_count = 0`. This is the case that fails today and the
one Monday's scheduled run actually hits, since the fleet sits at `minReplicas=0` until 22:25 UTC.

## Steps, in order

1. **Put the correlated receive in `kernel/`,** not in the deliberator. This is transport plumbing,
   the reply side of a primitive the kernel already owns (`AzureServiceBusRequestConsumer` publishes
   the correlated reply; only the *caller* half is missing). A helper such as
   `receive_correlated_ready_event(receiver, *, correlation_id, deadline)` keeps the next
   request/reply caller from reinventing the same bug.
2. **Match on `run_id`.** Accept a ready event only when its `run_id` equals `str(message.id)` for
   the request just published. Keep receiving until a match or the deadline expires.
3. **Dispose of an orphan loudly, not silently.** A non-matching reply is by definition orphaned —
   the manager is strictly sequential, one outstanding request at a time. **Dead-letter it with a
   reason** rather than completing it (which silently destroys evidence) or abandoning it (which
   re-delivers it and can spin). Dead-lettering removes it from the active path *and* keeps it
   inspectable.
4. **Count orphans and surface them.** Record how many orphaned replies were skipped while resolving
   a turn, and raise a fault when the number is non-zero. A backlog is a real condition — silence
   about it is what let this sit undetected across runs.
5. **Keep the timeout meaning what it says.** `request_timeout_seconds` is the budget for
   *resolving one turn*, not for a single `receive_messages` call. Draining orphans must not let a
   turn wait indefinitely.

## Success factors

- [ ] **The core proof:** a stale reply is placed in the subscription *ahead* of the genuine one;
      `debate_turn` returns the **genuine** reply, and the stale one is dead-lettered. Assert on the
      returned turn's content, not merely that no exception was raised.
- [ ] A stale **success** reply for a different ticker is **not** accepted as this order's turn —
      the specific silent-corruption case, tested separately from the error case.
- [ ] With an empty queue and a prompt peer, behaviour is unchanged: one request, one reply, no
      dead-letters, no extra receives.
- [ ] No matching reply within the deadline still raises and fails open — fail-open policy is
      **unchanged** (S147 item 2: an LLM outage must never block exits).
- [ ] Orphan count is queryable after a run in which orphans were skipped, and a fault is written.
- [ ] `make ci` exit 0, **unpiped, redirected to a file**; each new behaviour watched failing a
      planted violation before restoration (DL-70).

## Traps

- 🪤 **Do not "fix" this by draining the queue at startup.** That was the manual mitigation applied
  on 2026-08-08 (84 messages drained after inspection) and it is exactly the accident this sprint
  removes: with an empty queue a sequential manager pairs correctly *by luck*. The bug reopens on
  the first timeout, crash mid-debate, restart, or second manager.
- 🪤 **Do not raise `request_timeout_seconds`.** The manager was not timing out; it was reading
  promptly and reading the wrong thing.
- **Fail-open must survive.** It is deliberate (S147 / ADR-0017): blocking the run on an LLM outage
  would block *exits*. This sprint changes *which* reply is read, never whether the veto can block.
- The reply is a **claim-check ready event** — the envelope lives in the graph under
  `(label, ref)`. Correlate on the ready event's `run_id`; do not fetch the graph node first, or a
  stale ref does a pointless read.
- **Deploy:** if nothing is added to a property-enforced label, an image-only retag is permissible —
  but prove it by hashing `orchestration/packs/trading_graph_vocabulary.json` at the deployed commit
  and at `HEAD`. If a new fault or count becomes a declared property, it is a **full
  `pwsh infra/deploy-agents.ps1 up -Tag <tag>`** (S148 / DL-79).
- `status.ps1 -Replicas` reads POWER from the KEDA cron window and prints `asleep` outside
  22:30–00:30 UTC even with pods running. **`PODS` is the honest column.**

## Closeout — evidence

_To be filled before handback; a handback with placeholders unfilled is not accepted._

**Correlation.** _The stale-ahead-of-genuine test, and the dead-lettered orphan._

**Unchanged.** _Proof that fail-open still fails open when no reply arrives._

**Not proven.** _State plainly what this does NOT establish._
