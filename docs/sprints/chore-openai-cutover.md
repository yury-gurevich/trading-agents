<!-- Agent: deliberator | Role: chore spec — make the S168 provider switch reachable on the fleet -->
# chore-openai-cutover — give the deliberator the key it needs

**Depends on:** S168 (`v0.90.00`, merge `c36b7d3`) — the code is shipped and proven; this chore only
makes it *reachable* on the fleet · **Type:** chore · **Version:** no package bump for the grant
change alone (config + pack); bump only if Python changes

## Why

Measured 2026-08-08:

| | Anthropic | OpenAI |
| --- | --- | --- |
| Local `.env` | present | present |
| Live API probe | **HTTP 400** — usage limit, access returns **2026-09-01 00:00 UTC** | **HTTP 200**, `gpt-5.5` |
| Granted to the deliberator containers | ✅ | ❌ **zero occurrences** |

S168 added `OpenAILLMClient` and the `llm_provider` tunable. But the three deliberator containers
never read `.env` — they start braindead and master hands them exactly what
`orchestration/packs/trading_secrets.json` lists, which is Anthropic only:

```json
"deliberator-manager":   [["anthropic-api-key", "ANTHROPIC_API_KEY"]],
"deliberator-proponent": [["anthropic-api-key", "ANTHROPIC_API_KEY"]],
"deliberator-opponent":  [["anthropic-api-key", "ANTHROPIC_API_KEY"]]
```

**So setting `DELIBERATOR_LLM_PROVIDER=openai` today fails closed**: `build_llm` reads
`os.environ.get("OPENAI_API_KEY")`, gets `None`, and raises `ConfigurationError` at startup. It
works on a laptop and dies on the fleet — the exact gap this chore closes.

## Steps, in order

1. **Grant the key.** Add `["openai-api-key", "OPENAI_API_KEY"]` to all three deliberator entries in
   `orchestration/packs/trading_secrets.json`. Check `trading_vault_probes.py` and
   `trading_vault_seed.json` for whatever else names `anthropic-api-key` and mirror it.
2. **Seed Key Vault** with `openai-api-key`. The value is already in `.env` — 🪤 **never** copy it
   into a tree file; pass it straight to the seeding script (CLAUDE.md: credentials never exist as
   files in the worktree).
3. **Set the provider — and the models with it.** `DELIBERATOR_LLM_PROVIDER=openai` on
   `deliberator-manager`, `-proponent`, `-opponent`. ✅ **Measured 2026-08-08:** the env prefix
   *is* `DELIBERATOR_` (`agents/deliberator/settings.py:101`).
   🪤 **The provider alone is not the switch.** `entrypoint.py:76` passes
   `model=settings.model_for_role(...)` explicitly, and `defender_model` / `challenger_model` /
   `judge_model` each default to **`claude-opus-5`** — so flipping only the provider sends an
   Anthropic model name to OpenAI. Set all three as well:
   `DELIBERATOR_DEFENDER_MODEL` / `_CHALLENGER_MODEL` / `_JUDGE_MODEL` = `gpt-5.5`. This is also
   what makes success factor 2 true rather than accidentally false, since `role_models` is written
   straight from these tunables. Fixing the coupling so one env var suffices is
   [S169](sprint-169-one-switch-and-a-deploy-that-keeps-it.md); **remove these three overrides
   when it ships.**
4. **Deploy `pwsh infra/deploy-agents.ps1 up -Tag s169`** — 🪤 **full `up`, not an image-only
   retag.** S167 added `failed_open_reason` to `DeliberationRun`, a **property-enforced** label, so
   the vocabulary pack has moved since `:s166`. A stale pack raises `VocabularyError` fail-closed on
   the first write and stalls the run mid-cascade (S148 / DL-79). Verify the pack hash on both sides
   before choosing the path, and read it back off a deployed app afterwards.
5. **Test.** Scale the 16 apps to `minReplicas=1`, place a manual `RunRequest` with a **`check-*`
   run id** via `place_run_request` (never a `sched-*` id — day-keyed ids merge-dedupe and would
   consume a real run), as_of the most recent trading session.

## Success factors

- [x] ⚠️ **PARTLY** — a `DeliberationRun` with **`real_debate_count = 16`** ✅ but
      `failed_open_count = 2` ✖ (USB, WFC — the cold-peer timeout, [S171](sprint-171-a-reply-must-answer-its-own-request.md)).
- [x] Its `role_models` name the OpenAI model, not `claude-*` — `{judge, defender, challenger} = gpt-5.5`.
- [x] New `LLMCall` nodes with the OpenAI model and `calling_agent` covering all three roles —
      **88 `gpt-5.5` calls**: proponent 40, opponent 32, judge 16.
- [x] `ExecutionRun.deliberation_status = applied` (the S166 gate still holds) — `submitted=8`,
      18 approved minus **10 vetoed**.
- [ ] ✖ **NOT MET** — **1** `Fault` by `occurred_at` in the run-3 window (the cold-peer timeout),
      plus pre-existing execution drop-sweep residue. Queried on `occurred_at`, not `created_at`
      (DL-99; `created_at` is `NULL` on every Fault node and returns a false zero).
- [x] Fleet returned to `minReplicas=0`, verified 16/16; all test orders cancelled and verified by
      **re-reading** them (0 open orders, 0 positions), not by trusting the DELETE's 204.

## Traps

- **Do not tear down the run's lineage** if it placed orders: `Fill` is a protected label since
  DL-94, so `pg_teardown --run-id` would delete the `OrderIntent`s and strand the `Fill`s.
- The market is shut at these hours; `tif=day` buys queue to the next open. Cancel them if the book
  should stay flat.
- `status.ps1 -Replicas` reads **POWER** from the KEDA cron window, so it prints `asleep` whenever
  the clock is outside 22:30–00:30 UTC even with pods running. **`PODS` is the honest column.**

## Closeout — evidence

**SHIPPED 2026-08-08.** Merge `8b30624` (grant + guard test, **no version bump** — the secret map is
injected from the repo at deploy time and ships no package behaviour). `make ci` exit 0, unpiped to
a file: **2216 passed / 6 skipped / 100.00 %**, contracts 4 kept 0 broken, pip-audit clean.
`make gate-ran` **GATE PROVEN** for `eded4bec1fb1…` (CI + Security Findings both `success`).

**Grant.** `openai-api-key → OPENAI_API_KEY` added to all three deliberator entries; Anthropic
**kept alongside**, so reverting the vendor is one env var with no redeploy. New
`tests/test_deliberator_provider_grant.py` binds the pack to `llm_factory.KEY_ENV` — every provider
the factory can select must have a granted key, for all three roles. **Planted-failure proof:**
reverting the pack fails exactly the 3 `openai` cases and leaves the 3 `anthropic` cases green.

**Key.** 🚨 The vault and `.env` held **different** OpenAI keys — vault `sk-proj-OPwS…` (single
version, created 2026-07-03, never rotated) vs `.env` `sk-proj-Qqt4…`. Both authenticated *and* both
completed real `gpt-5.5` calls, so nothing was broken — but the fleet would have billed a five-week-old
key nobody tracked. Synchronised via the probe-gated `.env` → Key Vault seeder (the only tooled
direction); verified by **re-reading** the vault: both `sha12 5aacfe5c37db`, and the vault value
completes a live call. Prior value retained as an older Key Vault version, so it is reversible.

**Deploy.** Full `up -Tag s169` — **proven necessary, not assumed**, for *two independent* reasons:
the vocabulary pack moved `b8d1a30f…` → `13c0e3a0…` (S167 declared `failed_open_reason` on
`DeliberationRun`, which **is** property-enforced), **and** `deploy-agents.ps1:525` injects the
secret map as `MASTER_SECRET_MAP_B64` from the repo file — an image-only retag would have shipped
the code and silently not the grant. Images `15/15 success` from `8b30624`. Verified per target:
**16/16 on `:s169`, 16/16 `Succeeded`, 16/16 `minReplicas=0` with exactly 1 KEDA rule**, job on
`:s169`. Pack read back off master and decoded: **byte-identical to `HEAD`**. Deployed secret map
decoded and read: all three deliberators carry `openai-api-key`. `DeployRecord
deploy:2026-08-08T10:59:20…:s169:8b30624…` written **after** verification. Master fetched
`openai-api-key` from Key Vault at **11:04:41, HTTP 200** — the grant proven live, not inferred.

🚨 **The full `up` silently discarded operator configuration** (→ [DL-100](../design-log.md), S169):
`SCANNER_CANDIDATE_CAP` 25, `PORTFOLIO_MANAGER_MAX_POSITION_PCT` 0.01, `MAX_POSITIONS` 60 were
wiped, and the dispatcher cron reverted `30 22 * * 1-5` → `30 22 * * *` (which would have fired an
unintended weekend run that night). All restored and **re-read**; cron verified back at
`30 22 * * 1-5`. Caught only because the env was snapshotted by hand before deploying.

**Run.** Three `check-*` runs; `sched-2026-08-10` never touched.

1. `check-s169-openai-cutover` — 8/8. Provider 99/99 no degraded feeds, scanner 99→22, PM
   **approved 18 / rejected 0**. `DeliberationRun`: **`real_debate_count=0, failed_open_count=18`**
   with an *Anthropic* usage-limit reason, despite the proponent making **18 real `gpt-5.5`
   completions**. Root cause **not the provider** → [DL-102](../design-log.md).
2. `check-s169-openai-debate` — 8/8 but `approved=0`, all 18 `account_unavailable`. Cause was **my
   own concurrent Alpaca calls** rate-limiting `position_sync` (`account_status=stale`,
   `broker positions read failed: HTTPError`). S161's gate correctly refused to size against an
   unknown account. Proof of the safety gate, not of the debate.
3. `check-s169-debate-2` — 8/8, `account_status=fresh` (equity `10246421` = the broker to the cent).
   PM **approved 18 / rejected 0**. **`DeliberationRun`: `real_debate_count=16`,
   `failed_open_count=2` (USB, WFC), `role_models = {judge, defender, challenger} = gpt-5.5`,
   `vetoed_tickers` = 10 of 18.** `LLMCall` **88, all `gpt-5.5`** — proponent 40, opponent 32,
   **judge 16**. `ExecutionRun.deliberation_status = **applied**`, `submitted=8 rejected=0` —
   18 approved minus 10 vetoed.

🟢 **The veto blocked real orders for the first time**, with reasoning, e.g. *“AMZN: revise — the
volatility gate cites ATR% 3.07 while the recommendation metrics show ATR_pct 3.603, so the stop
adequacy check uses an internally inconsistent input.”*

**Success factors:** 1 ⚠️ (`real_debate_count=16` ✅, `failed_open_count=2` ✖) · 2 ✅ · 3 ✅ (all
three roles, judge included) · 4 ✅ `applied` · 5 ✖ (**1** fault by `occurred_at` in the run window,
the cold-peer timeout; run 1's 18 were the stale-reply defect, plus pre-existing execution drop-sweep
residue) · 6 ✅.

**Teardown.** Run 1: 18 orders cancelled (`{204: 18}`), scoped to that PM id, **0 out of scope**.
Run 3: 8 orders cancelled (`{204: 8}`), **0 out of scope**. Both verified by **re-reading** the
broker: **0 open orders, 0 positions**, equity `$102,464.21` unchanged. Fleet returned to **16/16
`minReplicas=0`**, all `:s169`, one KEDA rule each; job `:s169`, cron `30 22 * * 1-5`. Lineage
**deliberately not torn down** (`Fill` protected since DL-94). Reply queue drained to **0**.

**Not proven.**

- **The veto is not reliable, only demonstrated.** 2 of 18 orders still failed open, and the two
  defects behind that are unfixed: [DL-102](../design-log.md) (no `request_id` correlation) and the
  timing mismatch that manufactures orphan replies. Both are packaged as
  [S171](sprint-171-a-reply-must-answer-its-own-request.md).
- **Draining the queue is a mitigation, not a fix.** Measured: the backlog regenerated **0 → 2**
  within a single run, one orphan per timed-out turn, and those two were *success* replies — the
  silent wrong-attribution case. Drained again before handover; it will return on the next timeout.
- **Monday's cold start is the untested case.** All three runs debated with peers already warm.
  `sched-2026-08-10` starts from `minReplicas=0`, which is exactly the condition that produced the
  two fail-opens.
- **The operator agent is still Anthropic-only** and that key is limited until 2026-09-01 — this
  chore fixed the deliberator only ([DL-101](../design-log.md), S170).
- The three `DELIBERATOR_*_MODEL=gpt-5.5` overrides are **temporary**; remove them when S169 ships
  provider-aware defaults.
