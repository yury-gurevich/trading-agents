<!-- Agent: planning | Role: sprint handover — find out why K=4 lost two replies and two-thirds of its speedup -->
# Sprint 192 — a reply that arrives late is still an answer

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-192-a-reply-that-arrives-late-is-still-an-answer` — cut from **`sprint-172-k4-on-s190`**, not from `main`
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** M
**Decisions:** [DL-140](../design-log.md) the K=4 measurement · `DL-142` (take it, then re-check at merge) · work-queue item 3

> **Why this bump kind.** No new capability. S172 already promises that concurrent debates do not
> lose peer replies; the measurement shows it does not deliver that. **fix → PATCH.**

---

---

## 🚨 AMENDMENT, 2026-09-01 — read this before the rest of the spec

**The spec below was written against a single measurement. It has been re-measured, and the premise
moved.** Nothing below is deleted, because the reasoning is still worth reading — but where it
conflicts with this block, **this block wins**. Full detail in [DL-145](../design-log.md).

The reproduction ran in the operator's window: same image `s172b`, same K=4, same 15-order harness,
about five hours after DL-140's run.

| | DL-140 | re-measured |
| --- | --- | --- |
| `real_debate_count` | 13 / 15 | **15 / 15** |
| `failed_open_count` | 2 | **0** |
| span ÷ sum | 0.67 (1.49x) | **0.562 (1.78x)** |
| `orphaned_reply_count` | "6" | **UNKNOWN — see below** |

**1 · The correctness failure did not reproduce.** It is **intermittent**. Do not design a fix
around the assumption that it happens every run; a green run proves nothing, and so does a red one.

**2 · The speed miss did reproduce, so the two symptoms are separable.** DL-140 guessed they were
"very likely one defect, not two". This run has the miss **without** the losses at the same
concurrency, which **falsifies that guess**. Fixing correlation may leave 1.78x untouched. Latency
was median 17.2 s / p90 23.0 s / max 32.2 s with **zero calls over 120 s**, so the timeout ceiling is
not the cause and raising it is still the wrong first move.

**3 · 🎯 THE SPRINT'S FIRST JOB HAS CHANGED. Success factor 4 is currently unmeasurable.**
`orphaned_reply_count` lives only in `ServiceBusPeerClient` process memory
(`agents/deliberator/servicebus_peer_client.py:60-66`) and is emitted **only as a log warning**
(`:170`). It is **never written to the graph** — the `DeliberationRun` has no orphan field — and
`deliberator-manager` contributed **zero** rows to `ContainerAppConsoleLogs_CL` over three hours
while master, opponent and proponent all logged. DL-140's "6" **can never be re-derived**, and the
re-measured run's count is **UNKNOWN — not zero**.

> **So step 1 is no longer "reproduce". It is: put `orphaned_reply_count` on the `DeliberationRun`,
> beside `failed_open_count`, which is already there and is the same kind of number.** Until that
> exists, the acceptance criterion cannot be falsified, the intermittency in finding 1 cannot be
> counted across runs, and a fourth attempt will end exactly where the first three did.

🪤 **Then, and only then, reproduce.** With the count recorded, a handful of runs answers the
question that two expensive runs could not: how often, and correlated with what.

🪤 **Two traps for whoever runs the harness.** (a) **DL-140's harness was never committed** — this
run had to recover the recipe from the graph. Commit it this time. (b) **Peer replica counts are
still unmeasured across both runs**; the second attempt failed because it called `az` from Python
via `subprocess` without Windows `.cmd` resolution. Capture them from the shell.

⚠️ **Do not merge S172 on a green sample.** A good sample of an intermittent failure is not proof of
absence, and success factor 4 remains unmeasured.

---

## 🔴 MUST RULE — read the laws before any code

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/deliberator/laws/laws.md` | LOCKED, now **v1.2** (S172's `debate_concurrency` PARAM row) | Read-only during a build. A clause you think is wrong is a `drift-register.md` row plus a report |
| `agents/deliberator/laws/test-plan.md` | Proven vs unproven per clause | Read it before relying on anything |

Binding: **`DLIB-ORD`** (record order), **`DLIB-NEV-06`** (never hide a failed debate or peer call as a
clean veto), **`DLIB-OBS-03`** (queryable fail-open causes).

⚠️ **The invariant this sprint must not break:** a debate that genuinely could not complete must still
fail **open and visibly** (`DLIB-NEV-06`). Making the symptom quiet — fewer dead-letter warnings, no
fail-open rows — while replies are still being lost is the failure mode to avoid. **Silence is not a fix.**

**Law-cycle question:** my reading is **No** — no `contracts/` change, no new guarantee, this makes an
existing promise true. Confirm it yourself and record the answer.

---

## Goal

Under `debate_concurrency=4`, fifteen orders complete fifteen real debates with **zero** peer replies
dead-lettered and **zero** fail-opens, and the measured concurrency is materially closer to K than
the 1.5× observed. The sprint succeeds when the **cause is named and proven**, not when the warnings
stop appearing.

## Why (context)

[DL-140](../design-log.md), measured 2026-09-01 on `pm-run-s172k4-a` — the first trustworthy K=4 run
after three attempts that returned `real_debate_count=0`.

| Postcondition | Target | Measured |
| --- | --- | --- |
| span ÷ sum-of-latency | 0.25 (1/K) | **0.67** — about **1.5×**, not 4× |
| 15 real debates | 15 | **13** |
| `orphaned_reply_count == 0` | 0 | **6 dead-lettered** |
| Fail-opens | 0 | **2** (AAPL, BAC) — `RuntimeError: no deliberator peer reply received` |

The run itself was clean: all **69** `LLMCall` rows `claude-opus-5`, every `stop_reason=end_turn`. No
throttle, no fallback, no truncation. Mean call latency ≈ **16.4 s** (1132.5 s ÷ 69), which is far
below the 120 s `request_timeout_seconds` — so **no individual LLM call was near timing out.**

### Measured, 2026-09-01

| Claim | Value | How |
| --- | --- | --- |
| Dead-lettered orphan replies | **6**, across 5 warnings | Fault rows, `deliberator-manager/debate_turn` |
| The exact keys | `SCHW:defender:r2`, `INTC:challenger:r2`, `BAC:challenger:r1`, `NFLX:challenger:r1` ×2, `NFLX:challenger:r2` | fault messages |
| Fail-opens | 2 — AAPL, BAC | `failed_open_tickers` on the `DeliberationRun` |
| Mean LLM call latency | **16.4 s** | 1132.5 s ÷ 69 calls |
| Wall-clock span | **760.9 s**; end-to-end 815 s | first call start → last call end |
| Per-call latency distribution | **NOT MEASURED — and the rows were torn down** | 🪤 my miss: `pg_teardown` ran before the distribution was mined. Retain it this time |
| Whether peer replicas actually scaled to 4 | **NOT MEASURED** | apps were scaled back to 0; check Log Analytics, or instrument the re-run |

---

## The competing explanations — the sprint's real job is to choose between them

**Do not fix anything before you know which of these it is.** They imply different fixes, and the
observed symptoms are consistent with all three.

1. **Late replies after a wait exits.** `ServiceBusReplyInbox.expecting()`'s `finally` block runs
   `self._pending.discard(id)` *and* `self._stashed.pop(id)`. Once a wait ends — including by
   **timeout** — its id stops being pending, so a reply arriving afterwards fails `_is_pending` and is
   dead-lettered. Under this reading **the 6 dead-letters are a symptom of the 2 timeouts, not a
   cause**, and the real question is why two waits timed out when mean call latency was 16 s.
2. **Peer capacity, not manager logic.** Peers were set to `maxReplicas=4`, but KEDA scales on load:
   the first burst may have hit one replica, queueing replies behind cold starts. This would explain
   **both** the timeouts and 1.5× instead of 4× — the peers, not the manager, were the bottleneck.
   🪤 If this is the cause, no amount of manager-side fixing helps.
3. **Manager-side serialisation.** All concurrent waits share one Service Bus receiver and pull
   `max_message_count=1` per slice, so throughput may be capped by the receive loop regardless of K.

🪤 **The in-process routing is probably NOT simply broken.** `tests/test_deliberator_reply_inbox.py::test_reply_inbox_stashes_pending_sibling_without_dead_letter`
passes, so sibling stashing works when both ids are pending. Do not start by rewriting the inbox.

---

## Scope

1. **🎯 Reproduce with instrumentation retained.** Re-run the 15-order K=4 harness (DL-140 records
   how: seed a synthetic `PMRun` into a real analyst chain, execution held at `minReplicas=0`), and
   **keep** per-call latency, per-call start/end, peer replica counts over time, and reply
   inter-arrival times. **Do not tear down until the distribution is mined.**
2. **Name the cause with evidence**, discriminating between the three explanations above.
3. **Fix that cause**, and only that cause.
4. **Re-measure**: 15 debates, 0 dead-letters, 0 fail-opens, and report the ratio in the corrected
   orientation.

### Out of scope

- **Do not raise `debate_concurrency` above 4.** If replies are being lost, more concurrency loses more.
- **Do not lower `max_rounds`** — S172 ruled that out and the reason still stands.
- **Do not merge S172.** This sprint decides whether it *can* be.

### The road not taken (LAW-06)

- **Suppress the dead-letter warning.** Rejected: it is the only evidence the system currently emits
  about lost replies, and `DLIB-NEV-06` exists to stop exactly this kind of quieting.
- **Raise `request_timeout_seconds` past 120 s.** Rejected as a first move: mean latency was 16 s, so
  a timeout at 120 s points at queueing, not slow calls. Raising it would mask explanation 2.
- **Extend `expecting()` to keep ids pending after a timeout.** Rejected as a first move — it is a
  plausible fix for explanation 1, but applying it before the cause is known would make the warnings
  disappear while replies are still lost.

---

## Blast radius — to be re-measured by the builder

| What | Detail |
| --- | --- |
| Likely files | `agents/deliberator/servicebus_reply_inbox.py` (118), `servicebus_peer_client.py`, possibly `kernel/bus_azure_ready.py` |
| Agents affected | deliberator only |
| Contract change? | Expected **no** |
| Graph vocabulary change? | Expected **no** — keeps the deploy an image-only retag |
| Deploy implication | Image-only retag of the **three deliberator apps only**; the other 13 stay on `s190`, which DL-140 verified is safe |

---

## Test plan

| # | Test | Must prove |
| --- | --- | --- |
| A1 | 🎯 A reply arriving **after** its wait timed out | is not silently dead-lettered as an orphan — it is attributable |
| A2 | Sibling stashing under 4 concurrent waits | every reply reaches its own waiter; `orphaned_reply_count == 0` |
| A3 | 🪤 A genuinely absent reply | **still** fails open visibly (`DLIB-NEV-06`) — the invariant the fix must not break |
| A4 | Live re-run at K=4, 15 orders | 15 real debates, 0 dead-letters, 0 fail-opens |

## Success factors

- [ ] The cause is **named and evidenced**, and the two rejected explanations are recorded as ruled out.
- [ ] 15 orders → 15 real debates, `orphaned_reply_count == 0`, 0 fail-opens, measured live.
- [ ] Ratio reported as **span ÷ sum-of-latency** with the orientation stated (see the trap below).
- [ ] A genuinely absent reply still fails open visibly.
- [ ] Per-call latency distribution retained and reported.
- [ ] `make ci` exit 0, 100.00 % coverage, redirected to a file never piped.

## Traps

🪤 **S172's success factor 1 is written in the wrong direction — do not inherit it.** It asks the
ratio to *drop* 0.95 → 0.25, but if 0.95 is serial then `sum ÷ span` must *rise* under parallelism.
Only **span ÷ sum** makes both numbers coherent. State the orientation in your report.

🪤 **A quiet run is not a fixed run.** Fewer warnings with replies still lost is the failure mode.
Assert on `real_debate_count == 15`, not on the absence of faults.

🪤 **The 15-order load is synthetic and always will be.** Real nights produce 3–9 orders, so this
can never be proven by waiting for a busy night.

🪤 **Execution must be held at `minReplicas=0` for the whole run**, or the synthetic buys reach the
broker. DL-140's run was safe only because of this.

---

## Sequencing after merge

1. `make ci` green, branch pushed, `make gate-ran` exits 0 **run from the worktree at that commit** —
   check the printed SHA against `git rev-parse HEAD`.
2. This branch sits on top of `sprint-172-k4-on-s190`. Decide explicitly whether S172 + S192 merge to
   `main` together; they are one capability and probably should.
3. Deploy: image-only retag of the three deliberator apps. **Roll back to `s190` before 22:30 UTC**
   if the scheduled run is still armed.

---

## Handover — paste this to Codex

```text
Build sprint 192 in trading-agents. Branch sprint-192-a-reply-that-arrives-late-is-still-an-answer,
cut from sprint-172-k4-on-s190 (NOT from main). Read
docs/sprints/sprint-192-a-reply-that-arrives-late-is-still-an-answer.md whole first.

THE SITUATION. S172 adds concurrent debates. Measured live on 2026-09-01 at debate_concurrency=4
with 15 orders (DL-140): 13 of 15 debated, 2 failed open with "no deliberator peer reply received"
(AAPL, BAC), 6 peer replies were dead-lettered as orphans, and concurrency came out at ~1.5x
instead of 4x. The run itself was clean - all 69 LLMCall rows claude-opus-5, all stop_reason
end_turn, mean call latency 16.4s against a 120s timeout. So no LLM call was slow; something in
reply routing or peer capacity is wrong.

YOUR JOB IS DIAGNOSIS FIRST, NOT A FIX. There are three live explanations and they need different
fixes:
 1. Late replies. ServiceBusReplyInbox.expecting()'s finally block discards the id from _pending
    AND drops its stash. After a wait times out, its reply is no longer recognised as a sibling and
    gets dead-lettered. Under this reading the 6 dead-letters are a SYMPTOM of the 2 timeouts.
 2. Peer capacity. Peers were maxReplicas=4 but KEDA scales on load; the first burst may have hit
    one replica and queued everything. This would explain BOTH the timeouts and the poor ratio, and
    no manager-side fix would help.
 3. Manager-side serialisation - all waits share one receiver pulling max_message_count=1.

DO NOT start by rewriting the inbox. tests/test_deliberator_reply_inbox.py::
test_reply_inbox_stashes_pending_sibling_without_dead_letter passes, so in-process sibling stashing
works when both ids are pending.

STEP 1 is to reproduce at K=4 with 15 orders AND RETAIN the instrumentation: per-call latency and
start/end, peer replica count over time, reply inter-arrival times. The previous run's LLMCall rows
were torn down before the distribution was mined - that is the single most useful missing datum, do
not repeat it.

HOW TO RUN IT. Seed a synthetic 15-buy PMRun linked into a REAL analyst chain so the veto context is
faithful (DL-140 describes it). Hold execution and portfolio-manager at minReplicas=0 for the whole
run or the synthetic buys reach the live broker. Deploy branch images to the THREE DELIBERATOR APPS
ONLY - the other 13 stay on s190, which is safe because the one shared-image file S172 touches
(kernel/bus_azure_ready.py) changes type annotations only.

DO NOT:
- Do NOT suppress the dead-letter warning. It is the only evidence of lost replies, and DLIB-NEV-06
  forbids hiding a failed peer call as a clean veto.
- Do NOT raise request_timeout_seconds as a first move - mean latency was 16s against a 120s
  timeout, so this is queueing, not slow calls, and raising it would mask explanation 2.
- Do NOT raise debate_concurrency above 4.
- Do NOT touch max_rounds.
- Do NOT make the warnings go away while replies are still lost. Assert real_debate_count == 15.

TRAP: S172's own success factor 1 states the ratio backwards. It asks for a DROP from 0.95 to 0.25,
but if 0.95 is serial then sum/span must RISE under parallelism. Only span/sum is coherent. Report
span/sum and say so.

MUST RULE: read agents/deliberator/laws/laws.md (LOCKED v1.2) and test-plan.md before any code, and
fill the Law reading record first. Binding: DLIB-ORD, DLIB-NEV-06, DLIB-OBS-03. Record design
decisions in docs/design-log.md as DL-142 with rejected alternatives. Failing test first, paste the
red output. make ci redirected to a file, never piped. Fill every handback section; a handback with
a placeholder left intact is returned, not repaired.
```

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| | | | |

**Law-cycle question:**

**Contradictions found:**

**Laws silent where a decision was needed:**

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | | | | |
| A2 | | | | |
| A3 | | | | |
| A4 | | | | |

---

## Closeout — evidence

**Status:**

**Tree the proofs ran in (and `.env` present?):**

**The cause, named and evidenced:**

**Explanations ruled out, and on what evidence:**

**Result:**

**Live re-run:** 15 orders → real debates, dead-letters, fail-opens, span ÷ sum

**Per-call latency distribution:**

**`make ci`:** redirected to `<path>`. Exit code . coverage .

**`make gate-ran`:** from `<worktree>` at `<full SHA>`:

```text
```

**Not met / verified failing:**

---

## Return notes

-
-
