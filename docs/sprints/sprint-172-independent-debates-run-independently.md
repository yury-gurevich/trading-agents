<!-- Agent: deliberator | Role: sprint spec — run independent order debates concurrently so the veto scales with the funnel -->
# S172 — independent debates run independently

**Closes:** the scaling half of [DL-103](../design-log.md) · **Opens from:**
[DL-105](../design-log.md) · **Type:** feat ·
**Target version:** next available MINOR (`0.91.00` if this ships after
[S169](sprint-169-one-switch-and-a-deploy-that-keeps-it.md)/[S170](sprint-170-one-llm-adapter-in-the-plumbing.md);
renumber if it goes first) ·
**Branch:** `sprint-172-independent-debates-run-independently`

> Handover to a delegated coding agent. Everything under **Measured** was read off the live spine or
> the deployed fleet on 2026-08-11. Everything marked **Assumed** has **not** been verified — check
> it before building on it.

## Why

**The debate is serial end to end, and no grace value fixes it.**

**Measured** — the `LLMCall` ledger for `sched-2026-08-10`:

| | |
| --- | --- |
| Calls | **90** — 18 manager + 36 proponent + 36 opponent (5 per order × 18 orders) |
| Per-call latency | mean **11.4 s**, p90 **16.4 s**, max **23.0 s** |
| Span, first call → last | **1,136 s** (22:41:00 → 22:59:56 UTC) |
| Sum of per-call latency | **1,022 s** |

🚨 **Sum-of-latency ÷ span = 0.90.** For ninety per cent of the wall clock exactly one call is in
flight. The remaining ~114 s is bus round-trip and graph writes, not concurrency.

Three independent serializations, each confirmed rather than inferred:

1. [`agents/deliberator/poll.py:64`](../../agents/deliberator/poll.py#L64) — a plain synchronous
   `for intent in order_set.approved:`.
2. Rounds within one order are inherently sequential (proponent → opponent → … → judge). **This one
   stays sequential** — it is the debate.
3. All three deliberator apps run `minReplicas=0, maxReplicas=1` on the live fleet, so even a
   concurrent manager would queue behind a single peer replica.

**Why it is urgent rather than tidy.** `deliberation_grace_seconds` is bounded `le=3600`, and the
funnel is being widened (`MAX_POSITIONS=60`, `SCANNER_CANDIDATE_CAP=25`):

| Orders | Serial wall clock | Against the `le=3600` ceiling |
| --- | --- | --- |
| 18 (measured) | 943–1,136 s | fits |
| 25 (today's candidate cap) | ~1,185 s | fits, ~34 % headroom |
| 68 | ~3,200 s | at the ceiling |
| 100 | ~4,740 s | **blows it by 30 % — no grace value fixes it** |

**[S171](sprint-171-a-reply-must-answer-its-own-request.md) is what makes this sprint possible.**
While the manager took `messages[0]` with no correlation, concurrent debates would have consumed
each other's replies — a stale *success* reply accepted as a verdict about a different ticker, with
no fault and a green gate. Correlation is now enforced, so concurrent in-flight requests are safe.
**That guarantee is this sprint's first-class regression risk: prove it still holds under load.**

## Steps, in order

1. **Add `debate_concurrency` as a `tunable()`** on `DeliberatorSettings` — the number of orders
   debated at once. Conservative default (**4**), `ge=1, le=25`, with a `why` naming the vendor rate
   limit as the reason it is bounded. `ge=1` must reproduce today's serial behaviour exactly.
2. **Replace the serial loop** at `poll.py:64` with bounded concurrent execution over
   `order_set.approved`. Prefer a bounded thread pool: `LLMClient.complete()` and the Service Bus
   client are both synchronous, and the work is I/O-bound — an asyncio rewrite would change two
   layers to buy the same thing.
3. **Reassemble results in deterministic order.** `verdicts`, `debates`, `transcript` and
   `llm_call_keys` are accumulated in loop order today. Under concurrency they must be rebuilt in
   `order_set.approved` order before `write_deliberation_run`, or the `DeliberationRun` stops being
   reproducible run-to-run. 🚨 **This is the subtle one — a passing concurrency test with
   non-deterministic record ordering is a regression, not a win.**
4. **Keep per-order fail-open isolated.** One order raising must not abort the other N−1; each order
   already fails open individually through `review.failed_open`. Verify that survives the pool.
5. **Raise `maxReplicas` on `deliberator-proponent` and `deliberator-opponent`** in
   `infra/deploy-agents.ps1` so the fan-out has somewhere to land. The manager stays at 1 —
   it is the coordinator, and a second manager would double-consume the `PMRun`.

## Success factors

Each is a postcondition to prove, not an intention to state.

1. **Serialization is gone, measured the same way it was found:** on a live run with `K=4`,
   sum-of-latency ÷ span drops from **0.90** to **≈ 0.25** (i.e. ≈ 1/K). Report the measured ratio.
2. **18 orders finish inside the 900 s grace with headroom**, and the run writes **no**
   `DeliberationGraceExpired` fault.
3. **Determinism:** the same `PMRun` replayed at `K=1` and `K=4` produces `DeliberationRun` records
   whose `verdicts`, `vetoed_tickers`, `debates` and `transcript` are in identical order.
4. **S171's guarantee holds under load:** `orphaned_reply_count == 0`, and both deliberator reply
   subscriptions read **0 active / 0 dead-letter** after a concurrent run.
5. **Fault isolation:** a planted single-order failure leaves the other 17 verdicts intact and
   records exactly one `failed_open` ticker.
6. `make ci` exit 0 unpiped to a file, 100.00 % coverage floor held.

## Traps

- 🪤 **`effort` is inert on the deployed fleet.** [`llm_openai.py:43`](../../agents/deliberator/llm_openai.py#L43)
  assigns `self.effort` and `complete()` never sends it. Do not attempt to tune latency with it and
  do not "fix" it here — it is filed separately so this sprint's blast radius stays one concern.
- 🪤 **`max_tokens` is hard-capped `le=4096`.** Raising it is a code change, not a tunable move.
- 🪤 **`max_rounds` 2 → 1 is a tunable, not this sprint.** It is ~40 % of the wall clock for zero
  code and should be swept separately, or it will contaminate this sprint's before/after measurement.
- 🪤 **Do not collapse the peers into the manager to get concurrency.** It would erase the role
  attribution the laws declare (`role_models`, `calling_agent` on every `LLMCall`) and with it the
  provenance guarantee DL-102 exists to protect.
- 🪤 **`maxReplicas` is production state, so this takes the full cycle and a deploy** — and a full
  `up` still discards operator env vars until [S169](sprint-169-one-switch-and-a-deploy-that-keeps-it.md)
  lands ([DL-100](../design-log.md)). Snapshot every app's env before deploying and re-read it after.
- 🪤 **Peers scale from `minReplicas=0` inside the 22:25–00:30 UTC KEDA window.** Cold-start latency
  is on the critical path for the first debate; S171's closeout measured the cold path — do not
  regress it.
- 🪤 **Vendor rate limits are the real ceiling on K.** K concurrent debates means up to K in-flight
  completions per role. Measure before raising the default.

## Closeout — evidence

<!-- Coding agent: replace this comment with the proven result. Required: files changed, the
     measured sum-of-latency ÷ span ratio at K=1 and K=4, the grace-headroom figure, the determinism
     comparison, orphaned_reply_count, the planted single-order failure result, the exact `make ci`
     summary (unpiped, redirected to a file), and `make gate-ran` output for the final tip.
     Do not merge until every success factor above is answered with a measurement. -->
