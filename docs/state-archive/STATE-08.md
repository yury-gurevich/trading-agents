<!-- Agent: planning | Role: archive — STATE history split out 2026-08-12 -->
# State archive 08 — the veto arc: production, first reading, demotion to advisory

**Split out of [`../STATE.md`](../STATE.md) on 2026-08-12.** Nothing here is live. Chains from
[STATE-07.md](STATE-07.md).

**Second entry appended 2026-08-14**, covering the measurement that priced the veto's scaling
problem (`0.90.02`, [DL-105](../design-log.md)) — moved so *Recent* stayed under the 200-line rule
when S169 landed.

One *Recent* entry moved, covering **S166–S171 + `chore-openai-cutover`, versions `0.89.07`–`0.90.01`,
2026-08-08→10**. It is the whole arc in which the LLM veto stopped being a component and became a
posture: the race it had always lost (S166), the audit that reported *"Faults today = 0"* while 18
were being written (S167), its second vendor after the Anthropic key hit its limit (S168), the
uncorrelated peer client (S171), and then the reading of the verdicts themselves — **56 % self-
agreement, roughly 2 of 15 grounds surviving a check against the code** — which is what demoted the
veto to *a good auditor and a bad gate* (DL-104).

Why it was split at 192 rather than 200 lines: the session that closed [DL-106](../design-log.md)
added three paragraphs to *Now* and would have pushed the next one over. Splitting the oldest entry
while its successor arc is still live keeps *Recent* to what a session can actually scan.

**Read next:** [ADR-0022](../decisions/0022-the-veto-gates-buys-never-exits.md) for the posture
itself, [DL-98…DL-104](../design-log.md) for the reasoning, and
[sprint-166](../sprints/sprint-166-the-veto-gates-buys.md),
[sprint-167](../sprints/sprint-167-a-fault-count-cannot-lie.md),
[sprint-171](../sprints/sprint-171-a-reply-must-answer-its-own-request.md) and
[chore-openai-cutover](../sprints/chore-openai-cutover.md) for per-sprint detail. 🪤 **S168 has no
sprint doc of its own** — the second-vendor work is recorded in `chore-openai-cutover.md` and DL-99.

- **A deploy now keeps the switches it was given (fix, `0.90.10`, 2026-08-14 — closes
  [DL-100](design-log.md), [S169](sprints/sprint-169-one-switch-and-a-deploy-that-keeps-it.md)).**
  The three model tunables resolve from the **provider**, so `DELIBERATOR_LLM_PROVIDER` is the whole
  switch, and `role_models` records the resolved name — asserted on the written node. Operator
  tunables and the cron move into `orchestration/packs/trading_tunables.json`; `up` sweeps every
  agent **before its first create** and refuses, naming any live env key it would drop (`-DropEnv`
  to drop one deliberately). `make ci` **2299 passed / 100.00 %**, both planted failures watched.
  🪤 **Not deployed** — the live half (row Q) is owed at the next full `up`, which must also
  `-DropEnv` the three `DELIBERATOR_*_MODEL=gpt-5.5` overrides or the fleet keeps masking the new path.

- **The audit-clause sweep, and one guard that had never been exercised (docs + test-only,
  2026-08-14 — [DL-111](design-log.md)).** The queue's *"17 audit-type rows"* measured **13**; **9**
  were green and in scope and **5 were demoted**, the cited test proving something adjacent to the
  clause each time. Ledger reconciled (analyst 24→23, execution 32→30, provider 17→16). Two are
  **false in code**, now drift rows: **DRIFT-039** `portfolio_state_snapshot` exists nowhere in the
  codebase; **DRIFT-040** nothing records which vendor served a fact. 🪤 Four of the
  five cite a test on the **pub/sub path production does not use** — the S174 shape in the ledger,
  and greppable, so the next sweep is cheap. The gate then caught the same disease in a test:
  `test_a_missing_sdk_raises_configuration_error` patched `builtins.__import__` while the adapter
  calls `importlib.import_module`, which **does not consult it** — so it passed only where the SDK was
  absent. Fixed, parametrised over both vendors, proven **with the SDKs installed** and planted out.
  **No bump** (test-only). New **row R**: three more guards are covered only by CI lacking the extras.

## Recent (verbatim, as it stood in STATE.md)

- **The veto reached production, was read for the first time, and was demoted to advisory (feat + fix,
  0.89.07–0.90.01, 2026-08-08→10 — ADR-0022, DL-98/99/101/102/103/104).** **S166** closed the race the
  veto had always lost: execution reached the broker at 05:36:22 while the `DeliberationRun` saying
  *revise* landed at 05:47:32, and `_drop_vetoed` read an absent veto as *execute everything* — so *not
  finished yet* and *not deployed* were indistinguishable. A buy-carrying `PMRun` is now held for a
  bounded grace (`deliberation_grace_seconds`, default 900); **exits never wait** (ADR-0017). **S167**
  fixed an audit reporting *"Faults today = 0"* while 18 were being written — `Fault` stamps
  `occurred_at`, the query read `created_at`, which is `NULL` on every Fault node (measured both ways at
  the same moment: **18** vs **0**) — and made `failed_open_reason` record the captured cause instead of
  asserting one. **S168** (`0.90.00`) gave the veto a second vendor after the Anthropic key hit its limit
  to 2026-09-01: an `OpenAILLMClient` behind the same port plus an `llm_provider` **tunable, deliberately
  not an automatic fallback chain**, because a silent switch makes *which model reviewed this order*
  unanswerable after the fact. **chore-openai-cutover** granted the key and found the vault and `.env`
  holding **different** OpenAI keys — both authenticated, so nothing was broken, but the fleet would have
  billed a five-week-old key nobody tracked. **S171** (`0.90.01`) fixed a peer client taking `messages[0]`
  with no correlation; cold peers now measure `real_debate_count=18`, `failed_open_count=0`, reply
  subscription **0 active / 0 dead-letter**. 🚨 **Each fix exposed the next.** Correlation revealed the
  debate's true cost — **943 s** against a 900 s grace (DL-103) — so the grace went 900 → 1800; then
  DL-104 read the verdicts and returned it to **900 deliberately**: **45 `revise` of 58** real debates,
  **56 %** self-agreement on the same model and prompt 3.5 h apart, and roughly **2 of 15** grounds
  surviving a check against the code. The veto is a good auditor and a bad gate.

---

## Moved 2026-08-14 — the deliberation constraint, measured (`0.90.02`)

- **The deliberation constraint was measured, and one of its two free levers did not exist (fix,
  0.90.02, 2026-08-11 — DL-105).** Asked whether two Anthropic APIs fix the deliberator's scaling
  problem, the constraint was established first: 90 calls on `sched-2026-08-10`, span first→last
  **1,136 s**, sum of per-call latency **1,022 s** — **ratio 0.90**, so ninety per cent of the wall
  clock has exactly one call in flight. Serial end to end, proven rather than inferred. Cost is
  **$0.83 per run**, so the Batch API's 50 % is worth $0.41 — **wall clock is the scarce resource,
  not money.** That splits the answer rather than settling it: batching is the right substrate for an
  auditor (it *deletes* the grace window rather than optimising it) and useless for a gate, and the
  multi-agent session API is an ADR that reopens three locked decisions, not a sprint. 🚨 **Three
  adapter findings surfaced while checking, none of them looked for.** `effort` was assigned and
  never sent, so the tunable read as live and did nothing on the deployed `gpt-5.5` fleet —
  **fixed** (`0.90.02`: `reasoning_effort`, planted-failure proven at `KeyError`, `make ci` **2228
  passed / 4 skipped / 100.00 %**, gate proven on the full SHA). `effort="max"` with
  `max_tokens=4096` is a documented misconfiguration on Claude Opus 5 and a *candidate* contributor
  to the 56 % self-agreement — **still open**. Neither adapter uses prompt caching or structured
  outputs. 🪤 **The `effort` defect survived at 100 % coverage because the test asserted the stored
  attribute rather than what reached the wire** — the DL-97 shape again, and the reason the new test
  pins the request, not the object. Packaged
  [S172](sprints/sprint-172-independent-debates-run-independently.md) (concurrency) and
  [S173](sprints/sprint-173-a-verdict-must-be-reproducible.md) (verdict reproducibility on Batches).
