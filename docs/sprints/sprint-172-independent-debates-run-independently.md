<!-- Agent: deliberator | Role: sprint spec — run independent order debates concurrently so the veto scales with the funnel -->
# S172 — independent debates run independently

**Closes:** the scaling half of [DL-103](../design-log.md) · **Opens from:**
[DL-105](../design-log.md) · **Type:** feat ·
**Target version:** next available **MINOR** at merge — **do not pin it in this file** ·
**Branch:** `sprint-172-independent-debates-run-independently`

> Handover to a delegated coding agent. Everything under **Measured** was read off the live spine or
> the deployed fleet on 2026-08-11. Everything marked **Assumed** has **not** been verified — check
> it before building on it.

## Why

**The debate is serial end to end, and no grace value fixes it.**

> 🚨 **AMENDED 2026-08-19 — re-measured on the deployed `s181` fleet, and the case is stronger than
> the 2026-08-10 numbers below.** Run `verify-2026-08-19-clean-2`, 9 orders, 45 `LLMCall` rows:
>
> | | 2026-08-10 (original) | **2026-08-19 (current)** |
> | --- | --- | --- |
> | Orders / calls | 18 / 90 | 9 / 45 |
> | Span, first → last | 1,136 s | **1,113 s** |
> | Sum of per-call latency | 1,022 s | **1,059 s** |
> | **Sum ÷ span** | **0.90** | **0.95 — worse** |
> | Mean call latency | 11.4 s | **23.5 s** |
> | Max call latency | 23.0 s | **68.4 s** |
> | Wall clock per order | ~63 s | **124 s** |
>
> **Why it got worse: `effort` was fixed.** It was inert on the wire until `0.90.02`; now live at
> `high`, it roughly **doubled the per-order wall clock**. The "two free latency levers" framing in
> older notes is dead — `effort` was spent, and it cost latency rather than saving it.
>
> **The build trigger is no longer a judgement call — it is measured.** Grace is now **1800 s**
> (DL-116, raised from 900 so the veto could bind at all). At 124 s/order:
>
> | Orders | Projected wall clock | vs grace 1800 s | vs cap 3600 s |
> | --- | --- | --- | --- |
> | 9 (measured) | 1,113 s | fits | fits |
> | **15** | **1,854 s** | 🚨 **BREACHES** | fits |
> | 20 | 2,473 s | breaches | fits |
> | 25 (candidate cap) | 3,091 s | breaches | **86 % of the hard cap** |
>
> **Fifteen orders breaks it.** The clean run had 9 and `sched-2026-08-18` had 7, so this is one
> ordinary busy night away, not a distant scaling limit. **Build it.**

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

## Law-reading record

Read before code on branch `sprint-172-independent-debates-run-independently`:
`agents/deliberator/laws/laws.md` locked v1. Relevant clauses are `DLIB-IDN-03`
(three bounded identities), `DLIB-OUT-02` and `DLIB-OBS-01` (recorded debate shape and
reconstructable transcript), `DLIB-NEV-05` (no cross-agent/orchestration imports),
`DLIB-ORD-01` (turn order inside one order remains sequential), `DLIB-FAIL-01` (per-order
fail-open), and `DLIB-PERF-02` (peer wait bounded by request timeout).

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

**When to run the measurement — 2026-09-01, not before ([DL-135](../design-log.md)).** It needs `s172`
images and peer `maxReplicas=4` on the fleet, which puts unmerged code there again; rollback is a retag
to **`s187`** (work-queue item 3 still says `s182`). `sched-2026-08-31` runs first on `s187` untouched —
it is the only instrument that proves the master/Key Vault credential path, and a K=4 run against an
unproven path returns `real_debate_count=0` for the third time.

## Success factors

Each is a postcondition to prove, not an intention to state.

1. **Serialization is gone, measured the same way it was found:** on a live run with `K=4`,
   sum-of-latency ÷ span drops from the **0.95 measured on 2026-08-19** to **≈ 0.25** (≈ 1/K).
   Report the measured ratio. Use the 2026-08-19 figure as the baseline, not the older 0.90.
2. **At least 15 orders finish inside the current 1800 s grace with headroom**, and the run writes
   **no** `DeliberationGraceExpired` fault. 15 is the measured breaking point at K=1 (1,854 s), so it
   is the number that proves the fix rather than merely exercising it.
3. **Determinism:** the same `PMRun` replayed at `K=1` and `K=4` produces `DeliberationRun` records
   whose `verdicts`, `vetoed_tickers`, `debates` and `transcript` are in identical order.
4. **S171's guarantee holds under load:** `orphaned_reply_count == 0`, and both deliberator reply
   subscriptions read **0 active / 0 dead-letter** after a concurrent run.
5. **Fault isolation:** a planted single-order failure leaves the other 17 verdicts intact and
   records exactly one `failed_open` ticker.
6. `make ci` exit 0 unpiped to a file, 100.00 % coverage floor held.

## Traps

- 🪤 **~~`effort` is inert~~ — CORRECTED 2026-08-19. It was fixed in `0.90.02` and is live at
  `high`.** Do not try to tune latency by lowering it: that was measured as a fail-open source
  (3 on 2026-08-13) and reverting re-opens the DL-63 inert-knob question. Treat `effort=high` as
  part of the fixed baseline you are measuring against.
- 🪤 **`max_tokens` is hard-capped `le=4096`.** Raising it is a code change, not a tunable move.
- 🪤 **`max_rounds` 2 → 1 is out of scope — and the reason first given here was wrong.**
  The old reason ("it will contaminate the before/after measurement") does not hold: the metric is
  **sum-of-latency ÷ span**, a ratio, and it is **invariant to call count** — halving the rounds
  halves numerator and denominator alike. The real reason is that it **changes the artefact under
  test**: this agent's own `max_rounds` `why` requires the debate to *"show more than one round in
  live proof"*, so a 1-round debate is a different thing, not a faster same thing. Cutting it to buy
  wall clock is a recorded decision, not a knob turn. Leave it at 2.
- 🪤 **Do not collapse the peers into the manager to get concurrency.** It would erase the role
  attribution the laws declare (`role_models`, `calling_agent` on every `LLMCall`) and with it the
  provenance guarantee DL-102 exists to protect.
- 🪤 **`maxReplicas` is production state, so this takes the full cycle and a deploy.**
  **CORRECTED 2026-08-19: S169 landed** (`0.90.10`, deployed `s176a`) — a full `up` now *refuses*
  before dropping a live env key and names it, and `orchestration/packs/trading_tunables.json` is the
  source of truth for operator values. **Put any new tunable's operator value in that pack**, or the
  next full `up` reverts it. Still snapshot env before and after: the guard is proven, your change
  to it is not.
- 🪤 **Peers scale from `minReplicas=0` inside the 22:25–00:30 UTC KEDA window.** Cold-start latency
  is on the critical path for the first debate; S171's closeout measured the cold path — do not
  regress it.
- 🪤 **Vendor rate limits are the real ceiling on K.** K concurrent debates means up to K in-flight
  completions per role. Measure before raising the default.

## Handover — paste this to Codex

```text
Work item: S172 - independent debates run independently.
Repo: trading-agents. Read docs/sprints/sprint-172-independent-debates-run-independently.md in full
before writing anything - especially the AMENDED 2026-08-19 block at the top of "Why", which
supersedes the older numbers under it. Read CLAUDE.md. Read docs/INDEX.md before opening any docs
folder.

WHAT IS WRONG
The deliberator debates PM-approved orders strictly one at a time, so the veto's wall clock grows
linearly with the funnel and has already started breaking the run.

Measured on the deployed s181 fleet, run verify-2026-08-19-clean-2, 9 orders / 45 LLMCall rows:
  span first->last call   1113 s
  sum of per-call latency 1059 s
  SUM / SPAN              0.95   <- for 95% of the wall clock exactly one call is in flight
  mean call latency       23.5 s, max 68.4 s
  wall clock per order    124 s

Three independent serializations:
 1. agents/deliberator/poll.py:64 is a plain synchronous `for intent in order_set.approved:`.
 2. Rounds within one order are sequential. THIS ONE STAYS - it is the debate.
 3. deliberator-proponent and deliberator-opponent run maxReplicas=1, so even a concurrent manager
    would queue behind a single peer replica.

WHY NOW
Grace is 1800 s (raised from 900 on 2026-08-19 by DL-116, so the veto could bind at all; it is
capped le=3600). At 124 s/order:
   9 orders -> 1113 s  fits
  15 orders -> 1854 s  BREACHES the grace
  20 orders -> 2473 s  breaches
  25 orders -> 3091 s  breaches, 86% of the hard cap
The last two runs had 9 and 7 orders. Fifteen is one ordinary busy night away.

When the grace expires, execution submits every order UNVETOED. That is not theoretical - it
happened on sched-2026-08-19: 9 orders submitted as proceeded_unvetoed, and the debate then
returned 6 vetoes, 71 s too late. Orders reaching the broker unreviewed is the cost this sprint
removes.

WHAT TO DO
1. Add `debate_concurrency` as a tunable() on DeliberatorSettings. Default 4, ge=1 le=25, with a
   `why` naming the vendor rate limit as the bound. ge=1 must reproduce today's serial behaviour
   EXACTLY. Put the operator value in orchestration/packs/trading_tunables.json too, or the next
   full `up` reverts it.
2. Replace the serial loop at poll.py:64 with bounded concurrent execution. Prefer a bounded THREAD
   POOL: LLMClient.complete() and the Service Bus client are both synchronous and the work is
   I/O-bound. An asyncio rewrite changes two layers to buy the same thing.
3. Reassemble results in deterministic order. verdicts, debates, transcript and llm_call_keys are
   accumulated in loop order today; under concurrency they must be rebuilt in order_set.approved
   order before write_deliberation_run. A passing concurrency test with non-deterministic record
   ordering is a REGRESSION, not a win.
4. Keep per-order fail-open isolated: one order raising must not abort the other N-1.
5. Raise maxReplicas on deliberator-proponent and deliberator-opponent in infra/deploy-agents.ps1.
   The manager STAYS at 1 - a second manager would double-consume the PMRun.
6. make ci green, REDIRECTED TO A FILE not piped. Plant every new guard, watch it fail, restore.

PROVE IT (each is a measurement, not a statement)
- sum-of-latency / span at K=4 drops from 0.95 to ~0.25. Report the measured number. Use 0.95 as
  the baseline, NOT the older 0.90 in the pre-amendment text.
- At least 15 orders finish inside the 1800 s grace with headroom and no DeliberationGraceExpired
  fault. 15 is the measured breaking point at K=1, so it is the number that proves the fix.
- Determinism: the same PMRun replayed at K=1 and K=4 produces DeliberationRun records whose
  verdicts, vetoed_tickers, debates and transcript are in IDENTICAL order.
- S171's correlation guarantee holds under load: orphaned_reply_count == 0 and both deliberator
  reply subscriptions read 0 active / 0 dead-letter after a concurrent run. This is the sprint's
  first-class regression risk - before S171 the manager took messages[0] with no correlation, and
  concurrent debates would have consumed each other's replies.
- A planted single-order failure leaves the other verdicts intact and records exactly one
  failed_open ticker.

CONSTRAINTS
- Do NOT touch max_rounds. It stays at 2. The reason is not measurement contamination (the ratio is
  invariant to call count) - it is that this agent's own max_rounds `why` requires more than one
  round in live proof, so a 1-round debate is a different artefact, not a faster one.
- Do NOT lower `effort`. It was inert until 0.90.02 and is now live at `high`; lowering it was
  measured as a fail-open source and reverting re-opens DL-63. It is part of the fixed baseline.
- Do NOT collapse the peers into the manager to get concurrency. It erases the role attribution the
  laws declare (role_models, calling_agent on every LLMCall) and the provenance DL-102 protects.
- max_tokens is hard-capped le=4096 - raising it is a code change, not a tunable move. Out of scope.
- Vendor rate limits are the real ceiling on K: K concurrent debates means up to K in-flight
  completions per role. Measure before raising the default above 4.
- Peers scale from minReplicas=0 inside the 22:25-00:30 UTC KEDA window; cold start is on the
  critical path for the first debate. Do not regress the cold path S171 measured.
- LLM PROVIDER AND COST - REWRITTEN 2026-08-30; the note here before was stale in every clause. The
  deliberator runs **Anthropic `claude-opus-5`**, not OpenAI: all three apps read
  `DELIBERATOR_LLM_PROVIDER=anthropic` live, applied by `up -Tag s187` today (DL-135). Both providers
  returned HTTP 200 on 2026-08-30 and the vault key is byte-identical to the verified one, so the
  outage is over and "capped until 2026-09-01" was a misread calendar reset. The old **~$0.46 per
  9-order run** was priced on gpt-5.5 and does NOT carry to claude-opus-5 at effort=high - price the
  run from the LLMCall ledger afterwards, do not assume it. An exhausted or refused account still
  presents misleadingly as "no deliberator peer reply received".
- OpenAI is now the FALLBACK, and the fallback can fail silently (work-queue item 35): llm_openai.py
  never inspects finish_reason, so a reasoning-truncated call returns HTTP 200 with empty content and
  raises nothing. If Anthropic throttles mid-measurement the K=4 numbers can degrade in a way that
  looks like success - check role_models on the LLMCall rows before trusting the ratio.
- maxReplicas is production state: full cycle and a deploy. S169 landed, so a full `up` now refuses
  before dropping a live env key - but verify, do not assume.
- Branch sprint-172-independent-debates-run-independently. Version: next available MINOR at merge,
  do not pin it. Push the branch and get `make gate-ran` GATE PROVEN before merging - run it from
  the worktree whose HEAD is the commit, and check the printed SHA. Fill in the Closeout block
  before handing back.
```

## Closeout — evidence

**Result:** built, deployed, and branch-gated; **not mergeable yet** because the required live K=4
measurement could not be produced while the OpenAI account is out of credits. This is the exact
blocker warned in the handover, not a code failure or a valid reason to switch provider.

**Files changed:** `agents/deliberator/settings.py`, `agents/deliberator/review_batch.py`,
`agents/deliberator/poll.py`, `agents/deliberator/servicebus_peer_client.py`,
`agents/deliberator/servicebus_reply_inbox.py`, `kernel/bus_azure_ready.py`,
`infra/deploy-agents.ps1`, `orchestration/packs/trading_tunables.json`, deliberator/deploy tests,
law-plan/ledger/drift docs, `docs/STATE.md`, and the version bump to `0.91.00` with `uv.lock`.

**Implemented proof points:**
- `debate_concurrency` is a tunable defaulting to `4`, bounded `ge=1/le=25`, with the vendor-rate-limit
  rationale. `orchestration/packs/trading_tunables.json` carries `DELIBERATOR_DEBATE_CONCURRENCY=4`.
- Manager review now uses a bounded thread pool over independent approved orders. `K=1` takes the
  serial path; `K=4` reassembles `verdicts`, `vetoed_tickers`, `debates`, `transcript`, and
  `llm_call_keys` in `order_set.approved` order before the graph write.
- Peer replies use a shared in-process inbox so one manager thread can stash a sibling's correlated
  ready event instead of dead-lettering it. The planted regression for the receive-stash race failed
  with `CorrelatedReadyEventTimeoutError`; restored code passed
  `tests/test_deliberator_correlated_peer.py` and `tests/test_deliberator_reply_inbox.py` (`9 passed`).
- `test_single_order_failure_is_isolated_under_concurrency` plants one order failure and proves the
  other verdicts survive with exactly one failed-open ticker. Determinism is covered by
  `test_concurrent_reviews_preserve_durable_order`, comparing serial and concurrent record order.
- `infra/deploy-agents.ps1` keeps `deliberator-manager` at `maxReplicas=1` and sets
  `deliberator-proponent`/`deliberator-opponent` to `maxReplicas=4`, with cron `desiredReplicas=4`
  for the peers.

**Baseline K=1 measurement:** carried from the amended 2026-08-19 live run
`verify-2026-08-19-clean-2`: 9 orders, 45 `LLMCall` rows, first-to-last span `1113 s`, summed
per-call latency `1059 s`, `sum/span = 0.95`, projected 15-order serial wall clock `1854 s`.

**Live K=4 measurement attempt:** deployed tag `s172` from code/deploy proof commit
`a7e7ad12911ca2dd76be51c6ef5bba0f6344e350`. `preflight -Tag s172` exit `0`; `up -Tag s172` exit
`0`. Azure config after deploy: manager image `trading-agents-deliberator:s172`, `max=1`,
cron `desiredReplicas=1`; proponent/opponent image `trading-agents-deliberator:s172`, `max=4`,
cron `desiredReplicas=4`. For the live proof window, replicas were manually warmed to manager `1`,
proponent `4`, opponent `4`, all `Running`; after the blocked attempt they were restored to
`minReplicas=0`.

Synthetic PMRun `verify-2026-08-19-s172-k4-15-racefix-a7e7ad1` was inserted at
`2026-08-19T12:58:10.717138+00:00` with 15 approved orders. The resulting `DeliberationRun` was
created at `2026-08-19T12:59:19.553907+00:00`, but it was not a successful concurrency proof:
`real_debate_count=0`, `failed_open_count=15`, `transcript_count=0`, `LLMCall=0`, and
`failed_open_reason` was OpenAI `429 credit_balance_exhausted` / "You have no credits remaining".
Because no `LLMCall` rows were written, the required K=4 `sum-of-latency / span` ratio is **not
measurable**. The grace headroom figure for this failed-open artifact was `1731.163 s`, but that
does **not** satisfy the success factor because zero orders were actually debated.

**S171 under load:** Service Bus residue before the live attempt was 0 active / 0 dead-letter on
`deliberator-manager.reply/agent`, `deliberator-proponent.requests/agent`, and
`deliberator-opponent.requests/agent`; after the failed-open attempt the same three subscriptions
were still 0 active / 0 dead-letter. No `DeliberationGraceExpired` fault was written for the attempt,
but `orphaned_reply_count == 0` under a successful 15-order concurrent debate is still unproven
because the LLM calls never started.

**Local gate:** `make ci` was redirected to `..\s172-make-ci.log`, not piped:
`make_ci_exit=0`; tail summary `2336 passed, 6 skipped in 121.37s`; total coverage `100.00 %`;
`pip-audit` reported no known vulnerabilities; detect-secrets and untracked-secret checks passed.

**Remote gate at the code/deploy proof commit:**
```
make gate-ran SHA=a7e7ad12911ca2dd76be51c6ef5bba0f6344e350
GATE PROVEN for a7e7ad12911ca2dd76be51c6ef5bba0f6344e350:
  Build and push agent images: success
  Security Findings: success
  CI: success
```

**Return note:** do **not** merge yet. Restore OpenAI credits, rerun the same 15-order K=4 live proof,
and replace this blocked measurement with the real `sum/span`, grace-headroom, `real_debate_count=15`,
`failed_open_count=0`, 75 `LLMCall` rows, and post-run orphan/subscription counts.
