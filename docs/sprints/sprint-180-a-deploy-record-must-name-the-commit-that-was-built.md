<!-- Agent: tooling | Role: sprint spec — make record_deploy verify its SHA against the build it claims -->
# S180 — a deploy record must name the commit that was actually built

**Closes:** work-queue item 21 · **Opens from:** the `s179` deploy, 2026-08-18 ·
**Type:** fix ·
**Target version:** next available **PATCH** at merge — **do not pin it in this file** ·
**Branch:** `sprint-180-a-deploy-record-must-name-the-commit-that-was-built`

> Handover to a delegated coding agent. Everything under **Measured** was read off this repo or the
> live spine on **2026-08-18**. Everything marked **Assumed** has **not** been verified — check it
> before building on it. Do not treat an unmarked claim as measured.

## Why

**It already produced a wrong answer once, today.** The `s179` deploy was recorded with
`--git-sha $(git rev-parse HEAD)`. `HEAD` had moved **one docs-only commit** past `4c8eeb0`, which
is the commit the images were actually built from, so the record named `8fbf3a41` — a commit that
was never built into any image.

That is not cosmetic. `surfaces/dashboard/projections_currency.py:61`:

```python
evidence["main_matches_record"] = sha == build.git_sha
```

`sha` is the record's `git_sha`; `build.git_sha` is the head SHA of the newest successful
`build-images.yml` run on `main`. They must be equal for the fleet to read `current`. With the wrong
SHA recorded, the dashboard would have reported the fleet **"behind" while it was current** — the
exact DL-46 currency error the `DeployRecord` exists to prevent.

**Measured — what `record_deploy` validates today.** `orchestration/deploy_record.py:27-31` checks
only that tag, sha and actor are **non-empty strings**:

```python
clean_sha = git_sha.strip().lower()
if not clean_tag or not clean_sha or not clean_actor:
    raise ValueError("tag, git sha, and actor are required")
```

There is **no shape check** (an abbreviated SHA, or `"banana"`, records fine) and **no cross-check**
against the build the tag came from. The script trusts whatever it is handed, and the value it is
handed is produced by a shell command that is *usually* right and silently wrong the moment `HEAD`
moves after the build — which is normal, because docs commits land between building and recording.

**How it was caught, and why that is the problem.** Only because the printed SHA was read by eye.
This is the same failure shape as the `make gate-ran` worktree trap (hardening row M): a command
that resolves a SHA from ambient state, prints a confident success, and is about a different commit
than you think. That trap was fixed by making the target resolve and *verify* the SHA itself instead
of trusting the caller. **Do the same here.**

**Measured — the correction that is already on the spine.** A second record was appended at
`07:56:29` with the true SHA. `_latest_record` takes `max` by `deployed_at`, so the corrected record
wins and currency now reads correctly. **Both records remain** — the log is append-only and the bad
one is superseded, not erased. **Do not delete it**, and do not build a delete path.

## The design decisions this sprint has to make

**1 · Verify, or resolve?** 🚨 **Recommended: verify, and refuse on mismatch.** Keep `--git-sha`
required, then compare it against the newest successful `build-images.yml` run and exit non-zero
naming both SHAs if they differ. Refusing teaches the operator what went wrong; silently resolving
hides that the command they typed was wrong.

- *Rejected:* **resolve it silently** (drop the argument, read the build's SHA). It would have
  produced the right record today, but it also makes `record_deploy` unable to record a deploy whose
  build is not the newest — and a rollback to an older tag is exactly that case.
- *Rejected:* validating shape only (40-hex). It would **not** have caught today's error:
  `8fbf3a41339d0a31aa9a057952fe5e6401280ac1` is a perfectly well-formed SHA.

**2 · Where does the check live?** 🚨 **Recommended: `scripts/record_deploy.py`**, the tooling layer.
🪤 **Do not put it in `orchestration/deploy_record.py`** — the reusable GitHub client lives at
`surfaces/dashboard/github_builds.py`, and importing it from `orchestration/` makes orchestration
depend on surfaces. Check the import-linter contracts before choosing; "Agents may not reach into
surfaces or orchestration" exists, and **Assumed, not verified:** that no contract currently forbids
`orchestration → surfaces`. Verify rather than assume.

**3 · What happens when GitHub cannot be read?** Token missing, API down, rate-limited. **Decide
explicitly** and say so: refuse (safe, but blocks a legitimate deploy record during a GitHub
outage), or record with a `sha_verified=false` prop (honest, and the currency projection can then
distinguish "verified" from "asserted"). 🚨 A silent pass is not an option — that is the current
behaviour and it is what this sprint exists to remove.

**4 · Does the tag matter too?** Today only the SHA is compared. **Assumed, not measured:** that a
record whose `tag` does not match the images actually on the fleet is impossible. It is not —
nothing checks it. Consider whether the deployed image tags should be verified as well, or say why
that belongs to `/check-fleet` instead.

## Blast radius — measured

- `scripts/record_deploy.py` (**38** lines) — the entry point run by the deploy procedure.
- `orchestration/deploy_record.py` (**45** lines) — the append-only writer.
- Reader: `surfaces/dashboard/github_builds.py` (**112** lines), `GitHubActionsReader
  .latest_main_image_build()` — already exists, already used by currency. **Reuse it; do not write a
  second GitHub client.**
- Consumer: `surfaces/dashboard/projections_currency.py` — unchanged by this sprint.

🟢 **Nothing in the trading path reads `DeployRecord`.** This cannot fail a run or block a trade. It
is a reporting-integrity fix.

## Steps, in order

1. **Reproduce as a failing test:** recording a well-formed SHA that is *not* the newest build's
   head SHA must be refused. Assert on the refusal, not on a log line.
2. **Record the decision** (decisions 1–3) in `docs/design-log.md` with rejected alternatives,
   **before** applying it. LAW-06.
3. **Implement the verification** in the tooling layer, reusing the existing reader.
4. **Prove it against the real repo:** the true `s179` pair (`s179` / `4c8eeb0505bc65c081be3d1fe
   71049f7d88e0e43`) must be accepted, and the wrong pair (`s179` / `8fbf3a41339d0a31aa9a057952fe
   5e6401280ac1`) must be **refused**. Both are real values from today.
5. `make ci` green, **plant each new guard and watch it fail**, restore.

## Success factors

- [ ] A well-formed but wrong SHA is **refused**, naming both the given and the expected SHA.
- [ ] The real `s179` / `4c8eeb0` pair is still accepted — the guard does not block correct use.
- [ ] The GitHub-unreadable case behaves as decision 3 says, and a test proves it.
- [ ] No second GitHub client — `GitHubActionsReader` is reused.
- [ ] Import-linter passes; no new `orchestration → surfaces` dependency introduced.
- [ ] Existing `DeployRecord` rows are untouched; **no delete path is added**.
- [ ] Decision recorded in `docs/design-log.md` with rejected alternatives.
- [ ] Each new guard **planted, watched to fail, restored** — stated per guard.
- [ ] `make ci` exit 0, 100.00 % coverage.

## Traps

🪤 **Shape validation is not the fix.** The SHA that broke this was perfectly well-formed. A 40-hex
check would have passed it. The check has to be against the *build*.

🪤 **`scripts/` may be outside the coverage floor.** S178 added `scripts/sweep_divergence_flags.py`
and `make ci` still reported 100.00 %, so scripts appear to be excluded. **Assumed, not verified.**
If the logic lives only in `scripts/`, it may be untestable under the floor — which is a reason to
put the *testable* part in a module and keep `scripts/` a thin entry point. Check the coverage
config before deciding where the code goes.

🪤 **Do not "fix" the bad record on the spine.** It is superseded and the log is append-only.
Deleting it would be the same class of move DL-44 prohibits.

🪤 **A script run from a git worktree silently gets the in-memory store** — a worktree has no `.env`
(gitignored). S178 hit this and reported a confident `0`. Copy the refuse-on-in-memory guard from
`scripts/sweep_divergence_flags.py`. **Never copy `.env` into a worktree** — CLAUDE.md forbids
credentials as files in the repo tree.

🪤 **The deploy procedure will need its wording updated too.** `.claude/skills/deploy-fleet/` step 6
tells the operator to pass `<full-built-commit-sha>`; if the command now refuses on mismatch, say so
there, or the next operator will read a refusal as a broken tool.

## Handover — paste this to Codex

```text
Work item: S180 - a deploy record must name the commit that was actually built.
Repo: trading-agents. Read
docs/sprints/sprint-180-a-deploy-record-must-name-the-commit-that-was-built.md in full before
writing anything. Read CLAUDE.md. Read docs/INDEX.md before opening any docs folder.

WHAT IS WRONG
scripts/record_deploy.py trusts the --git-sha it is handed. orchestration/deploy_record.py:27-31
validates only that tag/sha/actor are non-empty strings - no shape check, no cross-check.

This produced a wrong record today, 2026-08-18. The s179 deploy was recorded with
--git-sha $(git rev-parse HEAD), but HEAD had moved ONE DOCS-ONLY COMMIT past 4c8eeb0, the commit
the images were built from. The record named 8fbf3a41, a commit never built into any image.

That matters because surfaces/dashboard/projections_currency.py:61 does
  evidence["main_matches_record"] = sha == build.git_sha
where sha is the record's git_sha and build.git_sha is the head SHA of the newest successful
build-images.yml run on main. With the wrong SHA recorded the dashboard reports the fleet "behind"
while it is current - the exact DL-46 currency error the record exists to prevent. It was caught
only because a human read the printed SHA.

WHAT TO DO
1. Failing test first: a well-formed SHA that is NOT the newest build's head SHA must be refused.
2. Record the design decision in docs/design-log.md WITH rejected alternatives, before applying.
3. Verify and refuse on mismatch - do NOT silently resolve the SHA (that breaks recording a
   rollback to an older tag). Do NOT settle for 40-hex shape validation: the SHA that broke this
   was perfectly well-formed and would have passed.
4. Reuse the EXISTING client: surfaces/dashboard/github_builds.py GitHubActionsReader
   .latest_main_image_build(). Do not write a second GitHub client.
5. Put the check in the TOOLING layer (scripts/record_deploy.py). Putting it in
   orchestration/deploy_record.py would make orchestration import surfaces - check the
   import-linter contracts before you choose.
6. Decide explicitly what happens when GitHub cannot be read (refuse, or record with
   sha_verified=false). A silent pass is NOT an option - that is the current behaviour.
7. Prove with the real values from today: (s179, 4c8eeb0505bc65c081be3d1fe71049f7d88e0e43) must be
   ACCEPTED; (s179, 8fbf3a41339d0a31aa9a057952fe5e6401280ac1) must be REFUSED.
8. make ci green. Plant EVERY new guard, watch it fail, restore. Report each plant in the closeout.

CONSTRAINTS
- Do NOT delete or edit the bad DeployRecord on the spine. It is superseded by a corrected record
  appended at 07:56:29 and the log is append-only. Do not add a delete path.
- scripts/ appears to be excluded from the 100% coverage floor (S178 added a script and CI still
  read 100.00%) - VERIFY that, and keep the testable logic in a module with scripts/ a thin entry
  point if so.
- A script run from a git worktree silently gets the in-memory store, because a worktree has no
  .env. Copy the refuse-on-in-memory guard from scripts/sweep_divergence_flags.py. NEVER copy .env
  into a worktree.
- .claude/skills/deploy-fleet/ step 6 tells the operator to pass the full built commit SHA. If the
  command now refuses on mismatch, update that wording too.
- Nothing in the trading path reads DeployRecord, so this cannot fail a run. Verify that is still
  true before relying on it.
- Branch sprint-180-a-deploy-record-must-name-the-commit-that-was-built. Version: next available
  PATCH at merge, do not pin it. Fill in the Closeout block before handing back.
```

## Closeout — evidence

<!-- FILL THIS IN BEFORE HANDING BACK. A handback with this placeholder intact is not accepted. -->

**Result:** *not yet implemented.*

**Files changed:** *...*

**Design decisions:** *verify-vs-resolve, placement, and the GitHub-unreadable case, as a DL entry.*

**Proof:** *the real `s179` pair accepted, the wrong pair refused — both quoted.*

**Guards planted:** *per guard: what was planted, that it failed, that it was restored.*

**`make ci`:** *exit code, passed/skipped counts, coverage %.*
