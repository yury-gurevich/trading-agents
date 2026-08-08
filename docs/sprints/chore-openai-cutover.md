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

- [ ] A `DeliberationRun` with **`real_debate_count > 0`** and `failed_open_count = 0`.
- [ ] Its `role_models` name the OpenAI model, not `claude-*`.
- [ ] New `LLMCall` nodes with the OpenAI model and `calling_agent` covering all three roles.
- [ ] `ExecutionRun.deliberation_status = applied` (the S166 gate still holds).
- [ ] Zero `Fault`s — **query `occurred_at`, not `created_at`** (DL-99; `created_at` is `NULL` on
      every Fault node and returns a false zero).
- [ ] Fleet returned to `minReplicas=0`, verified 16/16; any test orders cancelled and verified by
      **re-reading** them, not by trusting the DELETE's 204.

## Traps

- **Do not tear down the run's lineage** if it placed orders: `Fill` is a protected label since
  DL-94, so `pg_teardown --run-id` would delete the `OrderIntent`s and strand the `Fill`s.
- The market is shut at these hours; `tif=day` buys queue to the next open. Cancel them if the book
  should stay flat.
- `status.ps1 -Replicas` reads **POWER** from the KEDA cron window, so it prints `asleep` whenever
  the clock is outside 22:30–00:30 UTC even with pods running. **`PODS` is the honest column.**

## Closeout — evidence

_To be filled before handback; a handback with placeholders unfilled is not accepted._

**Deploy.** _Pack hash both sides, per-target tag/state verification, `DeployRecord`._

**Run.** _Stage counts, the `DeliberationRun` numbers, `role_models`, fault count by `occurred_at`._

**Teardown.** _Scale state, order cancellations verified by re-read._

**Not proven.** _State plainly what this does NOT establish._
