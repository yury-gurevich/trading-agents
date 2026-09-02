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

---

## The two S176 deploys (moved from *Recent* 2026-08-17)

- **Two deploys, and S169's guard proved itself by refusing (2026-08-15).** `s176a` = `0.90.10` via
  full `up` (env change), then `s176b` = `0.90.11` via image-only retag (pack unmoved). **Row Q
  closed:** the three `DELIBERATOR_*_MODEL=gpt-5.5` overrides are gone, so the models resolve from
  `DELIBERATOR_LLM_PROVIDER=openai` and S169's switch is the live path instead of a masked one.
  The first `up` **refused** and named all three keys — DL-100's defect is now closed by
  demonstration, not only by test. Verified both times: 16/16 on tag, 16/16 `Succeeded`, KEDA
  `min=0`/1 rule on every app, cron `30 22 * * 1-5`, other tunables intact. `DeployRecord`
  `…:s176b:439111b7`. 🪤 **`pwsh script.ps1 -DropEnv A,B,C` silently passes one literal string**
  (`-File` semantics); the call operator `& ./infra/deploy-agents.ps1` is what binds the array.

- **The veto read word counts as article counts, and the fleet caught up (fix, `0.90.11`,
  2026-08-15 — [DL-112](design-log.md)).** `sched-2026-08-14` completed **8/8** and put 9 PM
  approvals to the deliberator; **8 came back vetoed and 1 order reached the broker**. Reading the
  verdicts: **5 of the 8 cite defects S175 had already fixed but which were not deployed** (the
  invented ATR fragment on AMZN/MDLZ; sector/batch absence read as zero exposure on AVGO/CSCO/GOOGL).
  A sixth was **new and false in code** — XOM vetoed for a *"sentiment feed internally
  inconsistent (10 articles but 11 positive and 3 negative)"*, when `sentiment_positive` counted
  lexicon **word occurrences** and `sentiment_articles` counted **headlines**: two units, one prefix,
  carried verbatim into the debate by `quant_metrics`. Renamed to `sentiment_positive_words` /
  `sentiment_negative_words`; no computed value changed. `make ci` **2301 passed / 100.00 %**, guard
  planted (old keys → `KeyError`) and restored. Only WMT (earnings-gap-aware stop) and GOOG
  (correlation penalty) were substantive objections. 🪤 **Third instance of DL-104's disease** —
  invented fragment, absence-as-zero, unit-in-a-name — all three cost real orders; the class is
  worth one sweep of every value rendered into the debate, not three more point fixes.

Older sprints — **the two S176 deploys (`0.90.10`/`0.90.11`), the deliberation-constraint
measurement (`0.90.02`, DL-105) and the S166→S171 veto arc (`0.89.07`–`0.90.01`) →
[STATE-08.md](state-archive/STATE-08.md)**;
`0.89` and below → [STATE-07.md](state-archive/STATE-07.md); earlier arcs (S36→S146) in
[STATE-01…06](state-archive/INDEX.md). Full chronological list: `docs/sprints/README.md`.

---

## The gate was red for two days over one test line (fix, no bump, 2026-08-17)

*Moved out of `STATE.md` on 2026-08-24 so Recent stayed under the 200-line rule.*

**The gate was red for two days over one test line (fix, no bump, 2026-08-17 —
  [DL-110](../design-log.md)).** Four straight `Security Findings` failures — three on docs-only commits
  — on CodeQL #177, the only error-level alert of 76: a PM test unpacked `SectorBook.outcomes()` into
  two names, and that call returns `()` with no sector. `GATE PROVEN` for `21a5e81`. 🪤 **A branch
  cannot clear an alert raised on `main`** (`codeql.yml` runs only there), and 🪤 **the step prints
  nothing on failure** — read the report, not the log.

---

## Three diagnoses, one pattern (docs only, 2026-08-24)

*Moved out of `STATE.md` on 2026-08-31 so Recent stayed under the 200-line rule. The durable records are [DL-129](../design-log.md), [DL-130](../design-log.md), [DL-131](../design-log.md) and work-queue items 12/20/32.*

**Three diagnoses, one pattern, no code changed (docs only, 2026-08-24).** All three were execution's graph
  facts denormalising lifecycle differently, with only `Position` having a predicate to hide it: item 12's
  "202-fill backlog" is **27** ([DL-129](../design-log.md)); item 20's 228 faults are **13 objects** the broker
  agrees are cancelled ([DL-130](../design-log.md)); a stop that *fires* is never reconciled
  ([DL-131](../design-log.md), item 32). 🟩 Item 27's symptom is gone — 24 positions / 24 stops, 1:1, zero
  unprotected — but its live proof is still owed. 🪤 Measured 08-24; seven runs have happened since.

---

**Third entry appended 2026-09-01.** Three `Now` blocks moved down from [`../STATE.md`](../STATE.md) so the 200-line rule held when the 2026-09-01 closures landed: the `s187` deploy (superseded by `s190`), the end of the [DL-125](../design-log.md) provider outage, and S186 + S187 as shipped. All three are settled history whose detail lives in their sprint docs.

🟩 **SUPERSEDED BY `s190`** — `s187` deployed 2026-08-30, 16/16 verified; its runtime half landed on `sched-2026-08-31`.

🟩 **PROVEN — BOTH PROVIDERS RETURN HTTP 200, 2026-08-30**; the [DL-125](design-log.md) outage is **over** (the
Anthropic half was an **operator-set** spend limit, not credit). 🟩 **And now from inside the fleet too**, via S188.

🟩 **SHIPPED AND DEPLOYED IN `s187`, both 2026-08-30** — detail in their sprint docs.
**[S187](sprints/sprint-187-a-parameter-is-declared-once.md)** `7d36771` (`0.92.02`): `make ci` gained a **12th step**,
PARAM/settings sync. 🚨 Its audit found **20× its scope** — 60 divergences across nine agents, 3 fixed and **57
baselined warning-only** ([DL-133](design-log.md) decision 3, DRIFT-052, work-queue item 33).
**[S186](sprints/sprint-186-a-headline-about-twenty-companies-is-not-news-about-one.md)** `81b82ee` (`0.92.01`):
batch-scoped duplicate-headline weighting, analyst laws **v1.2**, ledger + INDEX **24 / 47** ([DL-132](design-log.md)).
🪤 Its gate proof named `4b0daaf` and I re-ran it on the tip — the docs-commit-on-top trap, which S188 nearly repeated.

---

**Fourth entry appended 2026-09-02.** The 2026-09-01 *three owed items closed* block moved down from [`../STATE.md`](../STATE.md) under the under-200-line rule, once its results were settled and recorded in [DL-142](../design-log.md), [DL-143](../design-log.md), [DL-144](../design-log.md) and the functionality-check register. It covers the day work-queue items **36**, **39** and **40** were closed or filed, with no code change and no version bump.

🟩 **PROVEN RESULT — THREE OWED ITEMS CLOSED, 2026-09-01. No code changed, no version moved.** 🟩 **Item 39** by prevention
([DL-142](design-log.md)): `required_status_checks.strict` and `allow_update_branch` both **`false` → `true`**, so the gated head *is* the merged tree; exactly one field changed and both open PRs flipped to `BEHIND`.
🟩 **Item 36's refusal half** with a control arm ([DL-144](design-log.md)): a wrong Alpaca key gave `ActivationRefused` with `AgentInstance` **unmoved**; the real key **activated**.
🟩 **S191 needed no cascade** — no deployed agent runs the acceptance view — so it was proven over **all 55 runs on the spine**, which is what surfaced item 40.
