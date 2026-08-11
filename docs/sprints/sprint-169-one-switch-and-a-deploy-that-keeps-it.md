<!-- Agent: deliberator | Role: sprint spec — make the provider switch one act, and make it survive a deploy -->
# S169 — a provider switch is one switch, and a deploy cannot silently unset it

**Closes:** [DL-100](../design-log.md) · **Type:** fix ·
**Target version:** 0.90.02 (PATCH — two defect fixes, no new capability; retargeted 2026-08-11, S171 shipped as `0.90.01`) ·
**Branch:** `sprint-169-one-switch-and-a-deploy-that-keeps-it`

> Handover to a delegated coding agent. Everything under **Measured** was observed on the live
> system on 2026-08-08 during `chore-openai-cutover` and can be relied on. Everything marked
> **Assumed** has *not* been verified — check it before building on it.

## Why

Both halves are the same defect class: **configuration that silently does not do what the operator
believes it does.** Neither produces an error. Both were found by doing the cutover by hand.

### A — the switch is four switches, and three of them are easy to forget

**Measured.** `DELIBERATOR_LLM_PROVIDER=openai` on its own is not a working switch.
[`entrypoint.py:76`](../../agents/deliberator/entrypoint.py#L76) passes the model explicitly:

```python
llm = build_llm(
    settings.llm_provider,
    api_key=os.environ.get(key_env_var(settings.llm_provider)),
    model=settings.model_for_role(settings.peer_role or "judge"),
    ...
)
```

and `defender_model` / `challenger_model` / `judge_model` each default to **`claude-opus-5`**. So
flipping only the provider sends an *Anthropic model name to OpenAI*. The cutover needed **four**
env vars per container, on three containers — twelve settings to get a one-word change.

**Why this is worse than inconvenient.** `role_models` is written straight onto the
`DeliberationRun` from these same tunables
([`review_record.py:89`](../../agents/deliberator/review_record.py#L89)). Left unset, the audit
record would have said the order was reviewed by `claude-opus-5` while the call went to OpenAI —
the provenance claim DL-99 exists to protect, quietly false.

**The fix.** An unset model resolves its default **from the provider**. Then
`DELIBERATOR_LLM_PROVIDER=openai` is the entire switch, and an explicit
`DELIBERATOR_JUDGE_MODEL=…` still overrides as it does today.

🪤 **The trap in the fix itself:** `role_models` must record the **resolved** model, never the
sentinel. A `DeliberationRun` reading `role_models={"judge": ""}` is a worse audit record than the
wrong-but-populated one it replaces. Assert on the written node, not on the settings object.

**Assumed, unverified:** that no other agent reads `defender_model`/`judge_model` off
`DeliberatorSettings` outside the deliberator. Confirm before changing the field defaults.

### B — a full `up` silently discards operator-set configuration

**Measured, twice, in one deploy.** `deploy-agents.ps1 up` builds `$agentEnv` and passes it to
`containerapp create --env-vars`, which **replaces** the container's env set
([`deploy-agents.ps1:569-583`](../../infra/deploy-agents.ps1#L569)). Anything an operator set
directly is gone, with no warning and a green `[OK]`:

| Setting | Before `up -Tag s169` | After | Default if unset |
| --- | --- | --- | --- |
| `SCANNER_CANDIDATE_CAP` | 25 | *(wiped)* | 5 |
| `PORTFOLIO_MANAGER_MAX_POSITION_PCT` | 0.01 | *(wiped)* | 0.10 |
| `PORTFOLIO_MANAGER_MAX_POSITIONS` | 60 | *(wiped)* | 10 |
| dispatcher cron | `30 22 * * 1-5` | `30 22 * * *` | script default |

The cron is the same bug in a second place: `$DispatcherCron` defaults to `'30 22 * * *'`
([`deploy-agents.ps1:19`](../../infra/deploy-agents.ps1#L19)), so S166's weekday-only schedule was
reverted to daily — which would have fired an unintended weekend run that night.

**Why it is dangerous rather than annoying.** A run with the defaults restored still *succeeds*. It
scans 5 candidates instead of 25 and sizes at 10 % across 10 slots instead of 1 % across 60 — a
materially different trading system, reporting `ACCEPTANCE PASS`. The only thing that caught it this
time was snapshotting the env before deploying, by hand, because S161's closeout happened to mention
restoring a tunable.

## Steps, in order

1. **A — provider-aware defaults.** Give the three model tunables an empty-string sentinel default
   and resolve at build time from a per-provider default table (`anthropic → claude-opus-5`,
   `openai → gpt-5.5`) living next to `KEY_ENV` in `llm_factory.py`, which already owns
   provider-shaped facts. Resolution must happen **before** `role_models(...)` is computed.
2. **A — keep the override.** An explicitly set model still wins over the provider default, for
   every one of the three roles.
3. **B — carry the tunables in the pack.** Add the operator-set agent tunables to a pack file the
   deploy reads and applies (alongside `trading_secrets.json` / `trading_grants.json`), so the
   deployed value has one source of truth rather than existing only as live cluster state.
4. **B — make a silent drop impossible.** Before `up` rewrites an app's env, read the live env and
   **fail loudly** if it carries an agent-prefixed key the deploy will not set. Loud and refusing
   beats quiet and wrong (the S158 preflight precedent).
5. **B — the cron.** Same rule: take the live schedule as the default rather than the script
   literal, or refuse to change it without an explicit flag.

## Success factors

- [ ] With **only** `DELIBERATOR_LLM_PROVIDER=openai` set, a deliberation writes a
      `DeliberationRun` whose `role_models` name **`gpt-5.5`** for all three roles — asserted on
      the written node, not on settings.
- [ ] With **only** `DELIBERATOR_LLM_PROVIDER=anthropic`, the same test yields `claude-opus-5` —
      the fix must not quietly re-point the Anthropic path.
- [ ] An explicit `DELIBERATOR_JUDGE_MODEL=x` still wins under both providers.
- [ ] A planted `up` against an app carrying an unlisted `SCANNER_*` key **fails the deploy** with
      that key named in the message.
- [ ] The tunables in the table above survive a full `up` and are proven by **re-reading the app**,
      not by the deploy's own report (hardening row Q).
- [ ] `make ci` exit 0, unpiped to a file; every new behaviour watched rejecting a planted
      violation before restoration (DL-70).

## Traps

- **Do not deploy this with an image-only retag if the pack moves.** Adding a pack file or changing
  a property-enforced label means full `pwsh infra/deploy-agents.ps1 up -Tag <tag>`. Prove it by
  hashing the vocabulary pack at the deployed commit and at `HEAD`, both sides.
- Deploying this sprint is also when the three temporary `DELIBERATOR_*_MODEL=gpt-5.5` overrides set
  by `chore-openai-cutover` on 2026-08-08 should be **removed**, so the fleet proves the new default
  path rather than masking it. Removing them before this ships would break the veto.
- `status.ps1 -Replicas` reads POWER from the KEDA cron window, so it prints `asleep` outside
  22:30–00:30 UTC even with pods running. **`PODS` is the honest column.**

## Closeout — evidence

_To be filled before handback; a handback with placeholders unfilled is not accepted._

**A.** _The `role_models` written under each provider, with no model env var set._

**B.** _The planted-drop deploy failure, and the post-`up` re-read of every tunable in the table._

**Not proven.** _State plainly what this does NOT establish._
