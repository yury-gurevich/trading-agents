<!-- Agent: deliberator | Role: sprint spec — correlate peer replies so a verdict belongs to its own order -->
# S171 — a reply must answer its own request

**Closes:** [DL-102](../design-log.md) · **Type:** fix ·
**Target version:** next available **PATCH** at merge — **do not pin it in this file** ·
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

- [x] **The core proof:** a stale reply is placed in the subscription *ahead* of the genuine one;
      `debate_turn` returns the **genuine** reply, and the stale one is dead-lettered. Assert on the
      returned turn's content, not merely that no exception was raised.
      **Result:** `tests/test_deliberator_correlated_peer.py::test_debate_turn_skips_stale_ahead_of_genuine_reply_and_faults`
      returns `pm-new:AAPL:defender:r1` / `"fresh AAPL reply"`, dead-letters the stale MSFT reply
      with reason `S171OrphanedReply`, and writes an `OrphanedPeerReply` fault. Planted violation
      (`run_id` ignored) failed red: the result became `pm-old:MSFT:defender:r1`.
- [x] A stale **success** reply for a different ticker is **not** accepted as this order's turn —
      the specific silent-corruption case, tested separately from the error case.
      **Result:** `tests/test_deliberator_correlated_peer.py::test_stale_success_for_different_ticker_is_not_accepted`
      raises `RuntimeError("no deliberator peer reply received")`, completes no stale message, and
      dead-letters the stale success. Planted violation (`run_id` ignored) failed red: no exception
      was raised.
- [x] With an empty queue and a prompt peer, behaviour is unchanged: one request, one reply, no
      dead-letters, no extra receives.
      **Result:** `tests/test_deliberator_correlated_peer.py::test_prompt_peer_reply_is_one_receive_no_dead_letter`
      proves one receive, one completed genuine reply, zero dead-letters, zero orphan count, and no
      fault. Planted violation (reject every ready event) failed red with `no deliberator peer reply
      received`.
- [x] No matching reply within the deadline still raises and fails open — fail-open policy is
      **unchanged** (S147 item 2: an LLM outage must never block exits).
      **Result:** `tests/test_bus_azure_correlated_ready.py::test_correlated_ready_event_timeout_reports_skipped_orphans`
      and `tests/test_deliberator_correlated_peer.py::test_no_matching_reply_still_raises_for_manager_fail_open`
      prove timeout/no-match stays loud; `agents/deliberator/tests/test_fail_open_reason.py` proves
      a peer exception still records `failed_open_count=1`. Planted false-ready-event violation
      failed red: the helper did not raise, and the client raised a wrong claim-check error.
- [x] Orphan count is queryable after a run in which orphans were skipped, and a fault is written.
      **Result:** `ServiceBusPeerClient.orphaned_reply_count` is asserted at `1`; `GraphFaultSink`
      writes a `Fault` with `error_type="OrphanedPeerReply"` and the in-process sink keeps
      `context["orphan_count"] == 1`. Planted no-op orphan recording failed red at
      `orphaned_reply_count == 0`.
- [x] `make ci` exit 0, **unpiped, redirected to a file**; each new behaviour watched failing a
      planted violation before restoration (DL-70).
      **Result:** `make ci *> $env:TEMP\s171-ci-final.txt; $LASTEXITCODE` returned `0`;
      pytest reported `2225 passed, 6 skipped`, and coverage reported `100.00%`. Planted violations
      were observed red for stale correlation, orphan surfacing, prompt-peer over-filtering,
      no-match timeout handling, and the cold-peer idle-sleep bound before restoration.

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

**Correlation.**

`uv run pytest tests/test_bus_azure_correlated_ready.py tests/test_deliberator_correlated_peer.py
tests/test_deliberator_servicebus_peer.py tests/test_bus_azure_receiver.py tests/test_deliberator_runtime.py
tests/test_deliberator_cold_peer_timing.py agents/deliberator/tests/test_fail_open_reason.py
agents/deliberator/tests/test_manager_preflight.py --no-cov` -> **30 passed, 1 skipped**. The
stale-ahead test returned the genuine AAPL reply and dead-lettered the stale MSFT reply with
`S171OrphanedReply`; the `ServiceBusPeerClient` exposed `orphaned_reply_count == 1`; the fault sink
wrote `OrphanedPeerReply`.

**Unchanged.**

No matching reply still raises `RuntimeError("no deliberator peer reply received")`, and the existing
manager fail-open path remains covered by `agents/deliberator/tests/test_fail_open_reason.py`:
`failed_open_count=1`, `failed_open_tickers=("AAPL",)`, and the captured exception text is recorded
as `failed_open_reason`. The normal prompt-peer Service Bus path remains one receive, one completed
reply, no dead-letters, no fault.

**Cold peer timing.** The second half of the spec was handled without raising
`request_timeout_seconds`: served deliberator peers now call `serve_loop(..., poll_interval=0)`, so
the default Service Bus receive wait is the pickup bound. `tests/test_deliberator_cold_peer_timing.py`
asserts the measured numbers are now `receive_timeout_seconds=5.0`, extra idle sleep `0`, manager
`request_timeout_seconds=30.0`; planted old sleep `60` failed red.

**Gate.** `make ci` was run unpiped and redirected to
`$env:TEMP\s171-ci-final.txt`; exit `0`; pytest `2225 passed, 6 skipped`; coverage `100.00%`;
`pip-audit` reported no known vulnerabilities; detect-secrets passed.

**PROVEN IN PRODUCTION 2026-08-08** (`:s171`, `check-s171-cold-start`, peers scaled from `minReplicas=0`). Deployed **image-only** — vocabulary pack byte-identical `13c0e3a0…` both sides, `orphaned_reply_count` is in-memory, no property-enforced label moved. Verified per target: 16/16 on `:s171`, `Succeeded`, `minReplicas=0`, one KEDA rule; tunables and OpenAI provider config survived the retag, read back not assumed; `DeployRecord` written after verification.

The cold-peer success factor, which could not be proven at handback, **now holds**: `real_debate_count=**18**`, `failed_open_count=**0**`, `failed_open_reason` empty, `role_models` all `gpt-5.5`, **zero deliberator faults**, **zero orphans dead-lettered**, and the reply subscription ended **0 active / 0 dead-letter** — the backlog no longer regenerates. The same cold case on `:s169` gave 16 real debates and 2 fail-opens.

🚨 **Fixing this exposed the next defect, [DL-103](../design-log.md).** With correlation correct, the debate takes its true duration: **943 s** for 18 orders (90 `LLMCall`s, 5 per order, ~10.6 s each) against a **900 s** `deliberation_grace_seconds`. It overran, `DeliberationGraceExpired` fired, and `ExecutionRun.deliberation_status = **proceeded_unvetoed**` submitted all 18 — including the 15 the veto had decided to veto. Mitigated by raising the grace **900 → 1800** (`le=3600`, no code change), read back and verified. **Not fixed:** at `MAX_POSITIONS=60` the cost is ~3180 s against a 3600 s ceiling.

**Not proven.**

No fleet deployment was performed. No live Azure dead-letter queue was inspected after this branch.
No scaled-from-zero production debate has yet proven `failed_open_count=0`; the cold-peer fix is
unit-proven by the served-peer timing bound, not by a live scheduled run. Remote branch gate proof
is reported in the handback after push; merge/deploy remain operator decisions.
