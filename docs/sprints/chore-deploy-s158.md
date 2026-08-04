<!-- Agent: planning | Role: deploy runbook (operator sequencing) -->
# Chore — Retag the fleet to `:s158` so the deliberation gate can see its own facts

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** none — this is a deploy, not a repo change (see *Version* below)
**Status:** SPEC — packaged 2026-08-04, **awaiting operator approval to execute**
**Version:** **no bump.** A retag ships no package behaviour; the code was versioned at `0.86.01`
when S158 merged. Bumping for a deploy would make a real fix indistinguishable from a cosmetic one
(CLAUDE.md, *Version scheme*).
**Tag:** `s158` · **Built from:** `main` at **`4bb6a29`** — S158 (`8be1570`) plus two fixes that
landed while this was packaged: the `make ci` exit-code fix (`44ae1f2`, hardening row S) and
**cryptography 50.0.0 for CVE-2026-69247** (`244f1d9`, `v0.86.02`). The CVE fix is a reason to
prefer this SHA over `8be1570`, not a complication: the fleet picks up the patched dependency in
the same deploy.
**Effort:** S — one workflow run, one script invocation, and a verification pass that is most of it
**Decisions:** [DL-46](../design-log.md) merge-to-main does not redeploy ·
[DL-68](../design-log.md) the pack is deployable only as base64 ·
[DL-84](../design-log.md) a green CI proves mergeable, not shippable ·
[DL-88](../design-log.md) the deploy tool's own report is not trustworthy ·
[LAW-02](../../ops/laws/LAW-02-successful-execution.md) success is proven, never assumed

---

## Why this deploy, now

Three reasons, in descending order of how much they bind.

**1 · The acceptance gate FAILs on every run until this lands.** `sched-2026-08-03` scored:

```text
ACCEPTANCE  FAIL
  FAIL  deliberation.debate_coverage: MISSING
  FAIL  deliberation.failed_open_count: MISSING
```

This is a **deploy gap, not a defect**. The fleet runs `:s155`, which predates S158, so the
`DeliberationRun` written at 22:39:36 carries the pre-S158 property set — no `real_debate_count`,
no `failed_open_count`. The S158 view reads `None` and reports `MISSING`. Verified in the code
rather than assumed: `_coverage` returns `1.0` when `reviewed == 0`
(`orchestration/packs/trading_deliberation_view.py`), so a legitimate no-trade day **passes** once
the fleet is on S158. Until then the gate is red for a reason that has nothing to do with the run.

A gate that is permanently red teaches you to stop reading it. That is the actual cost.

**2 · S158's insurance is not in force.** The whole point of S158 is that the *next* transient
config failure is **loud and leaves the backlog unconsumed** rather than silently spending it — on
2026-08-02 a fail-open pass consumed all 23 `PMRun`s, permanently, on an append-only store. The
manager's peer-topic preflight and the `BusConfigError` that replaces the silent primary-fallback
only protect the fleet once the fleet is running them.

**3 · DL-80 is still open and this does not close it.** `sched-2026-08-03` was a clean pass for the
*transport* — the `PMRun` was consumed with no `EntityPath` fault — but the PM approved zero orders,
so there was nothing to debate. `LLMCall` remains frozen at 25 calls, all `claude-sonnet-4-6`,
newest 2026-07-15. **Zero new model calls, still.** This deploy does not produce a debate; it
ensures that when one is finally attempted, a failure is visible. Say that plainly rather than
letting the retag look like the fix for DL-80.

## Preconditions — check before starting

- [x] **Images exist and are green.** `build-images` succeeded on **`4bb6a29`**
      (run `30872940346`), alongside CI (`30872940342`) and Security Findings (`30872940348`) —
      6/6 workflows green on that SHA. **This is the DL-84 check** — four merges were once called
      green on CI + Security Findings while `build-images` was failing, so it is checked by name
      rather than inferred from a green CI.
- [ ] **No run in flight.** The cron fires 22:30 UTC. Do not deploy inside the 22:25–00:30 UTC
      scale window; a mid-run image swap is not a tested path.
- [ ] `az` reachable, `.env` and `infra/*.local.json` present.

## Procedure

### 1 · Build the 15 images at the tag

```bash
gh workflow run build-images.yml --ref main -f image_tag=s158
gh run watch <run-id> --exit-status
```

All **15** images must push (13 agents + `master` + `deliberator`, plus `dispatcher` — the
`deliberator` image serves all three deliberator apps). `fail-fast: false`, so a partial failure
still reports per-image; **do not proceed on a partial build.**

### 2 · Deploy with `up`, NOT the image-only retag

> 🚨 **This is the part it would be easy to get wrong.** The usual `/deploy-fleet` skill does an
> **image-only** update, which is correct for an ordinary retag and **wrong here**.

`DeliberationRun` is one of the four property-enforced labels, and **S158 added three properties to
it**. A target on S158 code with the `:s155` vocabulary pack raises `VocabularyError` **fail-closed**
on its first `DeliberationRun` write — inside the caller's fault boundary, which is the S148 stall
pattern. Image and pack must move as one unit.

```bash
pwsh infra/deploy-agents.ps1 up -Tag s158
```

`up` runs preflight first, then sets each target's image and calls `Set-AppVocabulary` /
`Set-JobVocabulary` as a **separate narrow** `--set-env-vars` call — the two-step from
`chore-deploy-pack-off-the-command-line`, without which the 12 KB pack blows cmd's 8,191-char
ceiling. It accumulates failures and exits non-zero.

**No re-provisioning is expected:** the deliberator's Postgres roles, SAS identities, rules, topics
and subscriptions were all created 2026-08-02 and verified idempotent; `alembic upgrade head` should
be a no-op. If preflight reports anything new to create, **stop and report it** — that is a
different change than this runbook covers.

### 3 · Distrust the deploy report (DL-88 / hardening row Q)

**Expect the script to under-report.** On the `:s155` deploy it printed `[XX]` for all 15 agents and
the job while **every target had in fact deployed correctly**: `az` exits 0, so no stderr surfaces,
and the state parsed out of a merged stdout/stderr stream is not the literal string `Succeeded`.

It fails **safe** — it under-reports rather than over-reports, which is why it is tolerated — but a
`[XX]` is now **uninformative in both directions**. Do not re-run `up` on the strength of it, and do
not trust an `[OK]` either. Step 4 is the actual verdict.

### 4 · Verify — this is the deliverable, not step 2

Per target, not sampled. All four must hold:

```bash
# a) 16 apps + the job on :s158
az containerapp list -g trading-agents \
  --query "[].{n:name,i:properties.template.containers[0].image}" -o tsv
az containerapp job show -n dispatcher-cron -g trading-agents \
  --query "properties.template.containers[0].image" -o tsv

# b) provisioning state per app
az containerapp list -g trading-agents --query "[].{n:name,s:properties.provisioningState}" -o tsv

# c) config intact — minReplicas=0, one KEDA rule, secretRefs, cron 30 22 * * *
az containerapp show -n scanner -g trading-agents \
  --query "{min:properties.template.scale.minReplicas, rules:properties.template.scale.rules[].name}"
```

**d) The pack, read back off a deployed app and decoded byte-identical to the repo pack.** This is
the step that actually de-risks the deploy — do it **per app**, as was done for `:s155`, not on one
sample:

```bash
# expected sha256 of the repo pack
sha256sum orchestration/packs/trading_graph_vocabulary.json
# then per app: pull GRAPH_VOCABULARY_B64, base64 -d, sha256sum, compare
```

An app whose **image moved but whose pack did not** is the single worst outcome available here: new
code, stale vocabulary, fail-closed on first write. It is also the exact failure the `:s155` deploy
produced in the window between its two runs, when all 16 apps sat on new images with
`GRAPH_VOCABULARY_B64` **absent** — the store unguarded, S144's protection simply off.

### 5 · Record the deploy fact — only after step 4 passes

```bash
PYTHONPATH=. uv run python scripts/record_deploy.py \
  --tag s158 --git-sha <full sha of the built commit> --actor <operator>
```

Never backfill a tag or SHA from inference — the append-only `DeployRecord` is the dashboard's
currency evidence.

### 6 · Post-deploy proof, scoped honestly

- [ ] `/check-fleet` — 16 apps + job healthy, on tag, activated, spine and bus reachable.
- [ ] Row in [`docs/laws/functionality-checks.md`](../laws/functionality-checks.md).
- [ ] STATE.md updated with the **proven** result (LAW-02), not the intent.

**Two things this deploy will NOT do, and the closeout must say so:**

1. **`sched-2026-08-03` will still FAIL acceptance, permanently.** Its `DeliberationRun` was written
   by `:s155` code and the spine is append-only — the missing properties can never be added. The
   gate can only pass from the **next** run onward. Do not re-run `accept.py` on that run id and
   read the failure as a deploy problem.
2. **DL-80 stays open.** The debate needs a day on which the PM approves at least one order. Watch
   for a `DeliberationRun` with a **non-empty transcript** and a **`claude-opus-5` `LLMCall` dated
   after 2026-08-02**, against a ledger frozen at 25 calls / newest 2026-07-15.

## Rollback

One command each way: `pwsh infra/deploy-agents.ps1 up -Tag s155`, which restores both the images
and the `:s155` pack together. The `:s155` images are unaffected by this deploy and remain in GHCR.

**Do not roll back by image alone** — that would leave S158's pack on `:s155` code. Harmless in this
direction (extra declarations are a superset, not a violation), but it breaks the invariant that
image and pack move together, and the next person to reason about it should not have to work that
out.

## Explicit non-goals

- **Do not change what the pack contains**, or any vocabulary declaration.
- **Do not re-provision** Service Bus, Key Vault, Postgres roles or identities. All were done and
  verified idempotent on 2026-08-02.
- **Do not fix hardening row Q** (the `[XX]` misreport) inside this deploy. It is filed; it fails
  safe; step 3 works around it. Fixing the deploy tool during a deploy is how a small change becomes
  an outage.
- **Do not enable DL-46 auto-deploy.** Still deferred; DL-80 is the standing argument for keeping a
  human gate on what reaches the fleet.

### The road not taken (LAW-06)

- **Image-only retag via `/deploy-fleet`** — smaller and the usual path, and **rejected here**:
  it does not move `GRAPH_VOCABULARY_B64`, and S158 added three properties to a property-enforced
  label. It would deploy cleanly and fail closed on the first `DeliberationRun` write.
- **Wait for a PM-approved order so the deploy and the DL-80 proof land together** — rejected.
  It couples a deploy that is ready to a market condition nobody controls, and leaves the
  acceptance gate red in the meantime. The two are independent; ship the one that is ready.
- **Deploy only the three deliberator apps** — rejected. The fleet has been retagged as a unit since
  DL-46, and a split-tag fleet makes "are we running the code we think we are" unanswerable at a
  glance, which is the question `/check-fleet` exists to answer.

---

## Closeout — evidence

> **Fill this in at execution. Do not close this chore with the block unedited.**

- `build-images` run ID + all 15 images pushed at `s158`:
- Preflight result (`N/N`), and anything it wanted to create:
- `up -Tag s158` exit code, and what the per-target report claimed (expect untrustworthy `[XX]`):
- **Step 4a/b/c** — 16 apps + job on tag, provisioning state, config intact:
- **Step 4d** — pack sha256 read back **per app**, matched against the repo pack:
- `DeployRecord` tag + SHA written, and the timestamp it was written **after** verification:
- `/check-fleet` result:
- Functionality-check row:
- Not met / deliberately out of scope:
