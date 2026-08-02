<!-- Agent: planning | Role: chore handover -->
# Chore — The vocabulary pack no longer travels on the command line (and a failed deploy stops saying it worked)

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `chore-deploy-pack-off-the-command-line`
**Status:** SPEC — packaged 2026-08-02, **blocking the `:s155` deploy**
**Version:** fix → **0.85.04** (PATCH: last two digits)
**Effort:** S–M
**Decisions:** [DL-68](../design-log.md) `GRAPH_VOCABULARY_B64` exists because no image ships
`orchestration/packs` · [DL-46](../design-log.md) merge-to-main does not redeploy ·
[DL-57](../design-log.md) a gate that cannot fail proves nothing ·
[LAW-02](../../ops/laws/LAW-02-successful-execution.md) success is proven, never assumed

> **Why PATCH.** No new capability. `deploy-agents.ps1 up` already exists; this makes it *work* and
> makes its failure *visible*. `0.85.03` → **`0.85.04`**.

---

## Why this chore

**The `:s155` deploy failed on 2026-08-02 with every one of 15 agents reporting `[XX]`, and the
script printed `Fleet deployed…` and exited `0`.** The fleet was left untouched on `:s152` — the
failure was clean — but nothing about the output said so.

The real error was suppressed by `2>$null`. Recovered by re-running a copy with the redirect removed:

```text
The command line is too long.
│   [XX] scanner
The command line is too long.
│   [XX] analyst
…once per agent, 15 times
```

### The measurement

`az` on this machine is **`C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd`** — a cmd.exe
batch wrapper, so every invocation inherits cmd's command-line ceiling.

| Thing | Chars |
| --- | --- |
| `GRAPH_VOCABULARY_B64` value **alone** | **12,032** |
| same pack, JSON minified first | 8,128 |
| pack at the `:s152` deploy (2026-07-31) | 11,228 |

Plus, on the same line: every Container App secret (`POSTGRES_DSN`, the SAS connection string, the
SAS bundle JSON), the GHCR PAT, `MASTER_PUBLIC_KEY_PEM_B64`, and the cron scale args.

**Minifying is not the fix** — 8,128 chars leaves no room for the rest, and the pack has grown twice
in one week (S153, S154, S155) with 51 more labels pending a property-declaration decision
([DL-82](../design-log.md)). It will keep growing.

### Why `:s152` worked and this did not

`:s152` was an image **retag** plus a narrow `--set-env-vars` call — short commands. `up` uses
`az containerapp create` carrying the full env *and* secrets *and* registry credentials *and* the
12 KB pack in one invocation. The pack growth did not cause this on its own; the wider command did.

**The precedent for the fix is already in the same file.** `Set-AppPostgresDsn`
(`infra/deploy-agents.ps1`, ~line 474) does exactly the two-step: `az containerapp secret set`, then
`az containerapp update --set-env-vars`. The vocabulary injection never adopted that shape.

## What ships (spec)

> Fill in the `**Result:**` line under each item as you complete it, **in place**.

### 1 · 🎯 The pack leaves the `create` command line

`Get-VocabularyEnv` is currently spliced into the big `create` invocation (agents, ~line 448) and
into the dispatcher job (~line 258). Both must stop carrying it inline.

- Create/update each target **without** `GRAPH_VOCABULARY_B64`, then set it in a **separate, narrow**
  `az containerapp update --set-env-vars` call — one variable, nothing else on the line.
- Do the same for `dispatcher-cron` via `az containerapp job update`.
- Follow `Set-AppPostgresDsn`'s existing shape rather than inventing a new one.
- **The second call must be checked.** A target whose image updated but whose pack did not is the
  worst outcome available: new code, stale vocabulary, `VocabularyError` fail-closed on the first
  write (the S148 stall pattern). Treat "image set" and "pack set" as one unit that succeeds or
  fails together.

**Result:** _fill at handback_

### 2 · 🎯 A failed deploy must fail loudly

This cost a full diagnosis cycle and could have cost a production run.

- **Stop swallowing the error.** `az @agentArgs 2>$null` (~line 466) hid `The command line is too
  long.` fifteen times. Surface stderr on failure — the message was sitting right there.
- **Accumulate failures.** `Check` (line 52) only prints; nothing tracks the result. `up` must know
  whether every target succeeded.
- **Do not print the success banner when anything failed**, and **exit non-zero**. Today `up` prints
  `Fleet deployed with cron scale windows and dispatcher job.` and returns `0` after a total
  failure. Any automated caller would read that as success — this is the DL-57 shape in the deploy
  tool itself: an outcome that cannot report its own failure.
- Same treatment for `preflight`, which already accumulates `$ok` but should also exit non-zero.

**Result:** _fill at handback_

### 3 · Tie the invariant down so it cannot silently reopen

A static check that fails if the pack is ever spliced back into a `create`/`job create` argument
list. Crude string-level assertion over `infra/deploy-agents.ps1` is fine and is the same tie used
for the Dockerfile↔build-matrix gap this week — what matters is that `make ci` catches the
regression rather than a deploy attempt discovering it.

**Plant the violation and watch it fail** (DL-70) before you make it pass.

**Result:** _fill at handback_

### 4 · Record the drift you find (do not fix it here)

If anything else in the deploy path swallows errors or reports unearned success, add it to
`docs/hardening-backlog.md` with an unblock trigger rather than widening this chore.

**Result:** _fill at handback_

## Scope boundary — what you cannot verify, and must not fake

**You have no Azure credentials, and this is a deploy script.** `make ci` will not exercise it, and
you must not attempt to reach Azure, Key Vault, Service Bus or Postgres.

Your definition of done is: the script change, the static check from item 3, `make ci` green, the
four remote gates green, and the closeout filled.

**The live proof is operator sequencing** and consists of: `preflight -Tag s155` green → `up -Tag
s155` with every target `[OK]` → **the pack read back off a deployed app and decoded to match the
repo pack**, exactly as was done for `:s152` (that read-back is the whole point of item 1) → 16 apps
present, config intact → `DeployRecord` written only after all of that.

Say plainly in the closeout that items 1 and 2 are **unverified against Azure** by your handback.
That is the honest status, not a gap.

## Test plan

| # | What it proves |
| --- | --- |
| 1 | The `create` argument list contains no `GRAPH_VOCABULARY_B64` (item 3's static check) |
| 2 | Planted regression: splice it back in → the check fails |
| 3 | A simulated failed target makes `up` exit non-zero |
| 4 | A simulated failed target suppresses the success banner |
| 5 | An all-success path still prints the banner and exits `0` — the regression risk of items 2/3 |

Tests 3–5 need the failure/success paths reachable without Azure. If that means extracting the
result-accumulation into something testable, do that; if you conclude it is genuinely untestable in
this repo's harness, **say so and explain why** rather than leaving it silently uncovered.

## Explicit non-goals

- **Do not migrate the script to `az containerapp create --yaml`.** That removes the whole limit
  class and is the better long-term answer, but it is a rewrite of every create/update path and is
  not what unblocks Monday. If you believe it is genuinely smaller than the two-step, say so in the
  return notes rather than doing it.
- **Do not minify the pack.** 8,128 chars still leaves no headroom, and it would change the
  byte-identical read-back verification recipe for no durable gain.
- **Do not change what the pack contains**, or any vocabulary declaration.
- **Do not re-provision anything.** The deliberator's Postgres roles, SAS identities, rules, topics
  and subscriptions were all created on 2026-08-02 and verified idempotent (existing agents' SAS
  keys were **not** rotated — checked against the live rule key). Preflight is 17/17 and 16/16.
- **Do not deploy.** Operator sequencing.

### The road not taken (LAW-06)

- **`--yaml` config files** — the durable fix; removes the command-line limit entirely rather than
  staying under it. Deferred as too large for the blocking path, and recorded here so it is a
  decision rather than an oversight. Worth its own chore.
- **Minify the JSON before base64** — 12,032 → 8,128. Rejected: no headroom, and the pack keeps
  growing.
- **Put the pack in a Container App secret instead of an env var** — does not help. The script
  passes `--secrets name=value` inline too, so the blob would still be on the same command line.
- **Shorten the pack by dropping declarations** — never. The pack's completeness is what makes the
  guard trustworthy (S143/S144); trimming it to fit a shell limit would trade correctness for
  convenience.

## Guardrails

- `make ci` green, all 9 steps, 100.00 % coverage floor.
- No production Python behaviour changes — this is infra plus a static check.
- **Remote green is the gate.** Push, poll until `quality`, `test`, `security` and `gate` all read
  `success` on your branch tip; `in_progress` is not `success`. If it goes red, **you fix it**.
  Assert a run exists for your head SHA (hardening-backlog row **M**). **Do not merge.**

## Handback contract — MANDATORY

Append results **inside this file**, in the sections below. Not a separate report file. Spec at the
top, proof at the bottom. An incomplete handback is returned, not repaired (DL-48).

---

## Closeout — evidence

> **Fill this in at handback. Do not return the chore with this block unedited.**

- Files changed:
- Version bump (`pyproject.toml`, `uv.lock` restaged):
- `make ci` — pass count, skips, coverage:
- Planted-failure observation for item 3:
- How items 1 and 2 were exercised without Azure (or why they could not be):
- Remote gate run IDs **and job conclusions**, with a run asserted to exist for the head SHA:
- Not met / operator sequencing:

---

## Return notes

- Branch and base commit:
- Whether you considered `--yaml` smaller than the two-step, and why you did or did not:
- Every red remote run hit on the way (run ID + cause + fix):
- Anything found and deliberately not fixed:
