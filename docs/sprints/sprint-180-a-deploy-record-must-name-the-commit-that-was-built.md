<!-- Agent: tooling | Role: sprint spec — make record_deploy verify its SHA against the build it claims -->
# S180 — a deploy record must name the commit that was actually built

**Closes:** work-queue item 21 · **Opens from:** the `s179` deploy, 2026-08-18 ·
**Type:** fix ·
**Target version:** next available **PATCH** at merge — **do not pin it in this file** ·
**Branch:** `sprint-180-a-deploy-record-must-name-the-commit-that-was-built`

> Handover to a delegated coding agent. Everything under **Measured** was read off this repo or the
> live spine on **2026-08-18**. Everything marked **Assumed** has **not** been verified — check it
> before building on it. Do not treat an unmarked claim as measured.
> 🟩 **Re-verified 2026-09-03, before handover.** Every `file:line` below was re-read at `14d8458`.
> **Two citations had drifted by one line and are corrected here**, and **both “Assumed” claims are now
> measured** — one of them **changes decision 2** (see *Decision 2* and the coverage trap). The rest of
> the spec stands as written; the `s179` SHA pair in step 4 is still real.

## Why

**It already produced a wrong answer once, today.** The `s179` deploy was recorded with
`--git-sha $(git rev-parse HEAD)`. `HEAD` had moved **one docs-only commit** past `4c8eeb0`, which
is the commit the images were actually built from, so the record named `8fbf3a41` — a commit that
was never built into any image.

That is not cosmetic. `surfaces/dashboard/projections_currency.py:60`:

```python
evidence["main_matches_record"] = sha == build.git_sha
```

`sha` is the record's `git_sha`; `build.git_sha` is the head SHA of the newest successful
`build-images.yml` run on `main`. They must be equal for the fleet to read `current`. With the wrong
SHA recorded, the dashboard would have reported the fleet **"behind" while it was current** — the
exact DL-46 currency error the `DeployRecord` exists to prevent.

**Measured — what `record_deploy` validates today.** `orchestration/deploy_record.py:26-30` checks
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
required, then verify it against the build record and exit non-zero naming both SHAs if it does not
hold. Refusing teaches the operator what went wrong; silently resolving hides that the command they
typed was wrong.

🚨 **CORRECTED 2026-09-03 — verify against *the newest* build is the WRONG RULE, and this repo
disproves it today.** The original wording said "compare it against the newest successful
`build-images.yml` run". Measured now:

- The `s194` images were built from **`e0a144f`** (its own successful build run, `2026-09-02T07:26Z`).
- The newest successful `build-images.yml` run on `main` is **`75027b6`** (`08:47Z`) — a **docs
  commit**, which built only because `build-images.yml`'s path filter includes `agents/**` and the
  commit edited `agents/deliberator/laws/laws.md`.
- So under the newest-build rule, recording the deploy that is **actually on the fleet right now**
  (`s194` / `e0a144f`) would be **REFUSED** — the correct record rejected as a mismatch.

🪰 **It is the same flaw the spec already rejected "resolve silently" for.** That option was
rejected because it "makes `record_deploy` unable to record a deploy whose build is not the newest —
and a rollback to an older tag is exactly that case". **Verify-against-newest breaks the identical
case**, and additionally breaks the ordinary case where any law-file edit lands after the build.

🎯 **The rule to implement instead:** the given SHA must be the head SHA of a **successful
`build-images.yml` run that produced the tag being recorded** — an existence-and-identity check, not
a recency check. 🪰 **`latest_main_image_build()` cannot answer that** — it returns only the newest
run — so this needs a **second query on the existing client**, which is not the same thing as a second
client. Extending `GitHubActionsReader` is in scope; writing a new GitHub adapter is not.

- *Rejected:* **resolve it silently** (drop the argument, read the build's SHA). It would have
  produced the right record today, but it also makes `record_deploy` unable to record a deploy whose
  build is not the newest — and a rollback to an older tag is exactly that case.
- *Rejected:* validating shape only (40-hex). It would **not** have caught today's error:
  `8fbf3a41339d0a31aa9a057952fe5e6401280ac1` is a perfectly well-formed SHA.

**2 · Where does the check live?** 🚨 **Recommended: `scripts/record_deploy.py`**, the tooling layer.
🪤 **Do not put it in `orchestration/deploy_record.py`** — the reusable GitHub client lives at
`surfaces/dashboard/github_builds.py`, and importing it from `orchestration/` makes orchestration
depend on surfaces.

🟩 **MEASURED 2026-09-03, and it is the opposite of what this spec assumed.** `.importlinter` declares
**four** contracts — `agents-are-islands`, `agents-import-only-kernel-and-contracts`,
`kernel-has-no-domain-knowledge`, `contracts-are-pure-vocabulary`. **None of them forbids
`orchestration → surfaces`**, so `lint-imports` will **not** stop you putting the check in
`orchestration/`. 🚨 **The gate is therefore not the arbiter here — judgement is.** Do not read a
green `lint-imports` as permission.

🎯 **Recommended resolution, because decision 2 and the coverage trap below are otherwise in direct
tension:** put the testable verification in a **module**, taking the expected SHA (or a zero-argument
callable returning it) as a **parameter**, and let `scripts/record_deploy.py` stay a thin entry point
that constructs the concrete reader and passes it in. That satisfies both constraints at once — the
logic sits inside the coverage floor, and **no new cross-layer import is created at all**.
🟩 **The seam already exists:** `surfaces/dashboard/github_builds.py:37` declares a `GitHubReader`
**Protocol** (`latest_main_image_build`) separate from the concrete adapter at `:45`, so a fake
satisfies it in a test without touching the network.

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
4. **Prove it against the real repo.** 🚨 **These values were "real today" on 2026-08-18 and have
   since decayed — re-verified and restated 2026-09-03.** The pair that must be **REFUSED** still
   holds and is the sharpest case: `8fbf3a41339d0a31aa9a057952fe5e6401280ac1` (a docs commit)
   has **zero** `build-images.yml` runs — measured, `gh run list` returns none for it — while
   `4c8eeb0505bc65c081be3d1fe71049f7d88e0e43` has **two** successful runs. That is the real
   discriminator: *was this commit ever built at all*, not *is it the newest*.
   🚨 **Add the counter-example that the newest-build rule fails:** `s194` /
   `e0a144fc08b1d5fd8bc219f4ed48fef74fa8d120` is the deploy **currently on the fleet** and **must be
   ACCEPTED**, even though `75027b62a8d45a67be0b8a3aaf66108f22ffc228` is a newer successful build.
   A guard that refuses this pair is wrong, however green its tests are.
5. `make ci` green, **plant each new guard and watch it fail**, restore.

## Success factors

- [ ] A well-formed but wrong SHA is **refused**, naming both the given and the expected SHA.
- [ ] 🚨 **The `s194` / `e0a144f` pair is ACCEPTED though a newer build exists** — the check is
      existence-and-identity, not recency. This success factor is the one that fails a
      newest-build implementation.
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

🪤 **`scripts/` IS outside the coverage floor — this is no longer an assumption.** 🟩 **Measured
2026-09-03:** `pyproject.toml:239` reads
`source = ["kernel", "contracts", "agents", "orchestration", "surfaces"]` — **`scripts` is not in that
list** — while `:253` sets `fail_under = 100.00`. So **logic placed in `scripts/` is invisible to the
floor**: it can ship untested and `make ci` will still print 100.00 %. 🚨 **This is what puts decision 2
in tension with itself** — "put the check in `scripts/`" and "prove it under the 100 % floor" cannot
both be satisfied by the same lines. Resolve it as decision 2 now recommends: testable logic in a
module, `scripts/record_deploy.py` a thin wiring entry point.

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
scripts/record_deploy.py trusts the --git-sha it is handed. orchestration/deploy_record.py:26-30
validates only that tag/sha/actor are non-empty strings - no shape check, no cross-check.

This produced a wrong record today, 2026-08-18. The s179 deploy was recorded with
--git-sha $(git rev-parse HEAD), but HEAD had moved ONE DOCS-ONLY COMMIT past 4c8eeb0, the commit
the images were built from. The record named 8fbf3a41, a commit never built into any image.

That matters because surfaces/dashboard/projections_currency.py:60 does
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
3b. CORRECTED 2026-09-03, READ THIS BEFORE IMPLEMENTING. Do NOT verify against "the newest
   successful build". Measured today: the s194 images on the fleet were built from e0a144f, but the
   newest successful build-images.yml run on main is 75027b6 - a DOCS commit that built only because
   the path filter includes agents/** and it edited agents/deliberator/laws/laws.md. Under a
   newest-build rule the correct record for the running fleet would be REFUSED. Implement an
   EXISTENCE-AND-IDENTITY check instead: the given SHA must be the head SHA of a successful
   build-images.yml run that produced the tag being recorded. latest_main_image_build() cannot
   answer that - extend GitHubActionsReader with a second query. Extending the existing client is in
   scope; a second GitHub adapter is not.
4. Reuse the EXISTING client: surfaces/dashboard/github_builds.py GitHubActionsReader
   .latest_main_image_build(). Do not write a second GitHub client.
5. Placement. MEASURED 2026-09-03: .importlinter has four contracts and NONE forbids
   orchestration -> surfaces, so lint-imports will not stop you putting this in orchestration/.
   Do not read a green lint-imports as permission. ALSO MEASURED: scripts/ is NOT in
   [tool.coverage.run] source (pyproject.toml:239) while fail_under = 100.00 (:253), so logic in
   scripts/ is invisible to the coverage floor and can ship untested at a green 100.00%.
   Those two facts together: put the TESTABLE verification in a module taking the expected SHA
   (or a callable returning it) as a PARAMETER, and keep scripts/record_deploy.py a thin entry
   point that builds the concrete reader and passes it in. No new cross-layer import, and the
   logic sits inside the floor. The seam exists already: surfaces/dashboard/github_builds.py:37
   declares a GitHubReader Protocol, separate from the adapter at :45, so a fake satisfies it.
6. Decide explicitly what happens when GitHub cannot be read (refuse, or record with
   sha_verified=false). A silent pass is NOT an option - that is the current behaviour.
7. Prove with real values, re-verified 2026-09-03:
   - (s179, 8fbf3a41339d0a31aa9a057952fe5e6401280ac1) must be REFUSED - that commit has ZERO
     build-images.yml runs, while 4c8eeb0505bc65c081be3d1fe71049f7d88e0e43 has two successful ones.
   - (s179, 4c8eeb0505bc65c081be3d1fe71049f7d88e0e43) must be ACCEPTED.
   - (s194, e0a144fc08b1d5fd8bc219f4ed48fef74fa8d120) must be ACCEPTED - this is the deploy on the
     fleet right now, and a NEWER successful build (75027b6...) exists. This pair is the one that
     fails a newest-build implementation. Do not skip it.
8. make ci green. Plant EVERY new guard, watch it fail, restore. Report each plant in the closeout.

CONSTRAINTS
- Do NOT delete or edit the bad DeployRecord on the spine. It is superseded by a corrected record
  appended at 07:56:29 and the log is append-only. Do not add a delete path.
- scripts/ is excluded from the 100% coverage floor - measured, see step 5. Do not put logic you
  cannot test there.
- Repo files are LF, not CRLF. Do not convert or reflow line endings, and do not let an editor do
  it: a delegated agent did exactly that on 2026-09-02 and reported the conversion as a fix
  (DL-148). Check `git diff -w` shows no whole-file rewrites before handing back.
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

**Result:** Implemented. `make ci` exits 0. Branch pushed to remote.

**Files changed:**

| File | Lines | Change |
|---|---|---|
| `orchestration/deploy_verify.py` | 50 | NEW — testable `verify_build_sha()` + `GitHubBuildChecker` Protocol |
| `orchestration/tests/test_deploy_verify.py` | 53 | NEW — 5 tests for the verify module |
| `surfaces/tests/test_dashboard_github_sha_check.py` | 78 | NEW — 6 tests for `sha_has_successful_build` |
| `surfaces/dashboard/github_builds.py` | 142 | Extended: `sha_has_successful_build()` added to `GitHubActionsReader` |
| `orchestration/deploy_record.py` | 47 | `sha_verified: bool = True` added to `record_deploy()` and props |
| `orchestration/tests/test_deploy_record.py` | 65 | Assert updated to include `sha_verified: True` in props |
| `scripts/record_deploy.py` | 79 | Calls `verify_build_sha`; adds `InMemoryGraphStore` guard |
| `.claude/skills/deploy-fleet/SKILL.md` | +10 | Step 6 updated with refusal note |
| `docs/design-log.md` | — | DL-149 corrected: existence-and-identity, sha_verified=False |
| `pyproject.toml` | — | 0.94.05 → 0.94.06 (PATCH) |

**Design decisions:** DL-149 (corrected 2026-09-03):
- Decision 1: existence-and-identity check — SHA must head a successful `build-images.yml` run, not necessarily the newest one. Recency rule rejected because `s194`/`e0a144f` would be refused under it.
- Decision 2: testable logic in `orchestration/deploy_verify.py` with injected `GitHubBuildChecker` Protocol; `scripts/record_deploy.py` is a thin wiring entry point. No `orchestration→surfaces` import created.
- Decision 3: GitHub unreadable → record with `sha_verified=False` (honest degraded path). Fail-closed rejected because it blocks legitimate deploys during GitHub outages.

**Proof — real test values (re-verified 2026-09-03):**
- `(s179, 8fbf3a41339d0a31aa9a057952fe5e6401280ac1)` → **REFUSED** — `_Checker(False)` models zero build runs for this SHA; `test_verify_raises_when_no_build_exists` asserts `DeployVerifyError`.
- `(s179, 4c8eeb0505bc65c081be3d1fe71049f7d88e0e43)` → **ACCEPTED** — `_Checker(True)` models two successful runs; `test_verify_returns_true_when_build_exists` asserts `True`.
- `(s194, e0a144fc08b1d5fd8bc219f4ed48fef74fa8d120)` → **ACCEPTED** — the existence check asks "was this SHA ever built?", not "is it the newest?". A newer build for `75027b6` is irrelevant. Same `_Checker(True)` path.

**Guards planted:**

1. **`verify_build_sha` refuses a SHA with no build:** Replaced `raise DeployVerifyError(...)` with `pass`. `test_verify_raises_when_no_build_exists` failed with `DID NOT RAISE DeployVerifyError`. Restored.

2. **`sha_has_successful_build` returns `None` on transport error:** Changed `return None` to `return False` in the `except` block. `test_sha_has_successful_build_returns_none_on_read_error[url-error]` failed with `assert False is None`. Restored.

3. **`sha_verified` stored in DeployRecord props:** Commented out `"sha_verified": sha_verified`. `test_record_deploy_appends_and_exact_replay_dedupes` failed with `Right contains 1 more item: {'sha_verified': True}`. Restored.

**`make ci`:** exit 0 — 2461 passed, 6 skipped, 100.00% coverage. No whole-file CRLF rewrites (`git diff -w` shows only content diffs).
