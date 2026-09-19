<!-- Agent: planning | Role: sprint handover -->
# Sprint 215 — a build is deploy evidence when its commit is on `main`, and only for the tag it published

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-215-build-evidence-commit-and-tag`
**Status:** BUILT
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** closes work-queue item **72**, plus a tag-prefix defect found while packaging it (folded into the same row) · extends [S180](sprint-180-a-deploy-record-must-name-the-commit-that-was-built.md)'s guarantee · no ADR · no DRIFT row expected (no law governs this code)

> **Why this bump kind.** PATCH. No new capability. `record_deploy.py` already exists to record a verified
> deploy; it refuses a truthful one (a tag-dispatched build of a commit on `main`) and accepts a false one (a
> tag that is only a prefix of the tag actually built). Both are bugs in one reader.

**Builder:** GitHub Copilot, the first sprint handed to it. The handover block is written for any coding
agent. Nothing in it assumes Codex.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `docs/laws/conventions.md` | How tests cite clauses, how laws are written | Read it whole. It tells you why this sprint cites **no** clause (below) |
| `docs/laws/drift-register.md` | Where a law/code disagreement is recorded | The **one law-adjacent file you may append to**. Not expected to change |
| [`sprint-180-…md`](sprint-180-a-deploy-record-must-name-the-commit-that-was-built.md) | The guarantee this reader exists to keep | Not a law, but binding here: *a `DeployRecord` names the commit that was actually built* |

Binding here: **LAW-02** (success is proven, never assumed: a `DeployRecord` is a proof claim about the
fleet) and **S180's guarantee**. No agent law governs this code; the measurement is below.

### The rule

1. **Before writing code**, read the files above plus S180's spec, whole, first time.
2. There is no agent `test-plan.md` to read. Confirm that yourself with the search in the next section.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, record it and add a `drift-register.md` row.
8. Tests here cite no clause ID, because no clause governs this code. Say so in the record rather than inventing one.

### 🩹 The law-cycle question — answered **NO**, with the reason

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**No.** Every change is in operator tooling under `surfaces/dashboard/`, which no fleet image contains. No
file under `agents/` or `contracts/` changes, and the `DeployRecord` shape stays exactly as it is. A search
for `DeployRecord`, `record_deploy` or `github_builds` across every `laws.md` and `test-plan.md` finds
**none**; the only law-folder mention is `docs/laws/functionality-checks.md`, which is a log, not a law.

🪤 **The answer flips to YES if you add a property to `DeployRecord`** (the run id or the dispatch ref, say).
That is a graph-vocabulary change, and it turns the deploy from "none" into a full `up`. Out of scope.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `surfaces/dashboard/github_builds.py` (**193** lines) | S180 spec; LAW-02 | The reader that decides what counts as build evidence. 7 lines from the hard block, so split before adding |
| new sibling module for the tag lookup (suggested `surfaces/dashboard/github_tag_builds.py`) | same | New home for `image_builds_for_tag`'s logic and the two fixes |
| `surfaces/tests/test_github_builds.py` (**192** lines) | `docs/laws/conventions.md` | Two of its tests assert the URL this sprint changes (see Traps). New tests go in a **new** file |
| `orchestration/deploy_record.py` (**125** lines) | S180 spec | Read it. It should need **no** change: it trusts whatever the reader returns |

⚠️ **The one invariant: a build of a commit that is not contained in `main` is never deploy evidence.**
Run `29904029290` built and published `smoke-test` from `576ee57…` on `chore-container-smoke`, a commit
that was never merged. It must be refused before this sprint and after it. If your change would return that
build, **stop and report**.

---

## Goal

After this sprint, `GitHubActionsReader.image_builds_for_tag(tag, git_sha)` returns a successful image build
that published `tag` whenever GitHub reports the build's commit **contained in `main`**, whichever ref
dispatched it. So `record_deploy.py --tag s211 --git-sha 7d3ff519c06fd7df9ad38da38508e41b506dbb12` would have
been accepted on 2026-09-17. A build of a commit not contained in `main` is still refused. A tag matches only
as a **whole** tag: a log that published `s214` is no longer evidence for `s21` or `s2`. The dashboard's
deploy-currency read (`latest_main_image_build`) does not change.

## Why (context)

On 2026-09-17 `deploy-agents.ps1 up -Tag s211` put **17/17** targets on `:s211`. `record_deploy.py` then
refused with *"GitHub build evidence is required"*, because the reader only lists builds whose ref is `main`
and build `35217747046` was dispatched on the tag `v0.98.08`. That tag points at the gated merge commit
`7d3ff51`. The refusal was right under the old rule and the outcome is wrong: the fleet moved and the
graph's deploy ledger could not say so. Any check that asks *"what is deployed?"* of the graph answered one
tag stale.

The workaround used for `s214` (dispatch on `main` while `main` still equals the merge commit) works only if
someone remembers the order. Once a docs commit lands above the merge, dispatching on `main` builds an
**ungated** commit, which is the S186 hazard. The tag is the right thing to build from. The reader has to
accept it.

While measuring this, a second defect turned up in the same function. `_run_log_mentions_tag`
(`github_builds.py:166-177`) tests `b"trading-agents-master:" + tag in log`, a **substring** match. Measured
live: the `s214` build is returned as evidence for tags `s21` and `s2`. `record_deploy.py --tag s2 --git-sha
1a6f3429…` would write a `DeployRecord` claiming a tag no build ever published.

The next deploy is S213's, held until Monday 2026-09-21's fill check. That deploy should be the first one
dispatched on its tag and recorded without the workaround.

### Measured, 2026-09-19 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| S211's build ran on a tag ref | run `35217747046`: `event=workflow_dispatch`, `head_branch=v0.98.08`, `head_sha=7d3ff519c06fd7df9ad38da38508e41b506dbb12`, `success`; its log publishes `trading-agents-master:s211` | *[measured 2026-09-19]* `gh run view 35217747046 --json …` and `gh run view --log` |
| The reader refuses it today | `image_builds_for_tag("s211", "7d3ff519…")` → `()` | *[measured 2026-09-19]* live read-only call from the main checkout with `.env`, `main` @ `f0e38d9` |
| GitHub returns it once `branch=main` is dropped | `…/runs?status=success&head_sha=7d3ff519…` → **2** runs: `35217747046` (`workflow_dispatch`, `v0.98.08`) and `35217221320` (`push`, `main`) | *[measured 2026-09-19]* REST with the `.env` token |
| That commit is contained in `main` | `compare/main...7d3ff519…` → `status=behind`, `ahead_by=0`, `behind_by=24` | *[measured 2026-09-19]* REST with the `.env` token: **200**, so the token can read `compare` |
| A successful build of a commit **not** on `main` exists | run `29904029290`, branch `chore-container-smoke`, `576ee571451a3b454a180ea1eee4c12f8889d186`, published `smoke-test`; `compare/main...576ee571…` → `status=diverged`, `ahead_by=1` | *[measured 2026-09-19]* `gh run list --event workflow_dispatch`; `gh api …/compare`; `gh run view --log` |
| Most branch builds are contained too | of the **19** most recent successful non-`main` dispatch builds, **18** are `behind`/`ahead_by=0` (their branches merged later) and **1** is `diverged` (the smoke build) | *[measured 2026-09-19]* `gh api …/compare/main...<sha>` per SHA. This is why decision 1 matters |
| The tag match is a substring match | `image_builds_for_tag("s21", "1a6f3429a728b0348ed2059de52b535803cb3fa4")` and `("s2", …)` both return run `35336964246`, which published `s214` | *[measured 2026-09-19]* live read-only; code at `github_builds.py:172-175` |
| The workaround is what recorded `s214` | `DeployRecord deploy:2026-09-18T11:04:47…:s214:1a6f342…`, written after dispatching on `main` while `main` equalled the merge commit | *[measured 2026-09-18]* work-queue item 72 |
| The dashboard reads the same reader | `surfaces/dashboard/projections_currency.py:49` calls `latest_main_image_build()` ("is the fleet behind `main`?") | *[measured 2026-09-19]* grep |
| No law governs any of it | 0 hits for `DeployRecord`, `record_deploy`, `github_builds` in any `laws.md`/`test-plan.md` | *[measured 2026-09-19]* grep over `**/laws/**/*.md` |
| `compare` semantics | `compare/main...X` reports `ahead_by == 0` exactly when `X` is `main` or an ancestor of it | *[ASSUMED — GitHub's documented meaning]* consistent on every SHA measured above; not tested against a force-pushed `main` |
| `head_sha` needs a full SHA | GitHub's runs filter silently returns 0 runs for an abbreviated SHA | *[measured by CLAUDE.md for the same API]* `c145e5e` → 0, full SHA → 2; not re-measured on this workflow |

---

## Scope — and what is deliberately NOT here

1. **A build of a commit on `main` is evidence whichever ref dispatched it.** When `image_builds_for_tag`
   is given a `git_sha`, it lists successful runs for that SHA **without** `branch=main`, and keeps a run only
   if (a) its `head_branch` is `main`, or (b) GitHub's `GET /repos/{repo}/compare/main...{head_sha}` returns
   `ahead_by == 0`. It drops every other run. An unreadable or malformed compare answer raises
   `GitHubReadError` with a sanitized message, the same way every other read here fails. It never falls back
   to assuming the commit is contained. The log check for the tag still applies to every kept run.
2. **A tag matches only as a whole tag.** `trading-agents-master:{tag}` counts only when the byte after it is
   not a Docker tag character (`[A-Za-z0-9_.-]`), or when the tag ends the file. `s21` must not match a log
   that says `:s214`, and `s214` must not match `:s214-rc1`.
3. **Unchanged on purpose.** `latest_main_image_build()` and the no-SHA listing (`image_builds_for_tag(tag)`
   with `git_sha=None`) keep `branch=main`. `orchestration/deploy_record.py`, `scripts/record_deploy.py` and
   `surfaces/dashboard/projections_currency.py` should need no edit. If you find you must change one, name it
   and say why in Return notes.
4. **Split before you add.** `github_builds.py` is at 193 lines. Move the tag lookup
   (`image_builds_for_tag`, `_run_log_mentions_tag` and the new ancestry check) into a sibling module. Keep
   `GitHubActionsReader`'s public methods and the `GitHubReader` protocol unchanged, so the dashboard,
   `record_deploy.py` and every existing fake keep working.

### Out of scope (do NOT build this sprint)

- **The deploy-fleet skill's step 2** still says `--ref main`. The planner updates it after the live check,
  not the builder.
- **Backfilling the missing `s211` `DeployRecord`.** `record_deploy.py` stamps `deployed_at = now`, and `s211`
  is no longer deployed, so a backfill would record a false time. The gap stays and is named here.
- **Refusing abbreviated SHAs up front.** A short SHA already fails closed (GitHub returns 0 runs). S180 ruled
  shape checks insufficient on their own. Not this sprint.
- **Any new `DeployRecord` property** (run id, ref). That is a vocabulary change and a full `up`; see the law-cycle answer.
- **Line-ending normalisation** (work-queue item 69). Separate chore.
- **No `laws.md` edit, no ADR.**

### The road not taken (LAW-06)

- **Drop `branch=main` and nothing else.** Rejected: it admits run `29904029290`, the never-merged
  `smoke-test` build, which breaks S180's guarantee. Test A3 exists to tell this apart from the real fix.
- **Accept any ref that looks like a release tag (`v*`).** Rejected: a tag's name says nothing about which
  commit it points at, and a tag can point anywhere.
- **"A push-to-`main` build exists for this SHA."** Rejected: `build-images.yml` has a `paths` filter, so a
  head that only touched docs never gets a push build. And several commits pushed together produce a run for
  the tip only.
- **Keep dispatching on `main`** (the `s214` workaround). Rejected in the work-queue row: it is a procedure
  people forget, and once `main` moves past the merge commit it builds an ungated commit.
- **Run the ancestry check on every run, `main` ones included.** Rejected in decision 2.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **What "on `main`" means.** Chosen: *contained in `main` when the record is written*, via
   `compare/main...{sha}` → `ahead_by == 0`. Consequence to record, not hide: a build dispatched from a sprint
   branch **before** merge is accepted once that commit is in `main`'s history (18 of the 19 measured branch
   builds are in that class). That is correct. The record still names the commit actually built, and the
   commit is in `main`'s history, so the currency arithmetic stays true.
2. **Which runs get the ancestry call.** Chosen: only runs whose `head_branch` is not `main`. A `main`-ref
   run's head was `main`'s head when it ran. Calling `compare` for it adds a request per run and changes
   every existing fixture. Rejected: compare every run.
3. **The no-SHA listing stays `main`-only.** `record_verified_deploy` calls it only to phrase its refusal
   (`deploy_record.py:112`), and it downloads one log per listed run. Widening it would multiply log
   downloads for an error message. Rejected: widen it too.
4. **Where a tag ends.** Chosen: the Docker tag charset `[A-Za-z0-9_.-]`. Any other byte, or the end of the
   log file, closes the tag.

🪤 **Take the next free DL number, then re-check it at merge.** At spec time the newest entry is **DL-176**,
so expect **DL-177**. The log has historic duplicates, and entries are added at both ends. A branch cut
before another DL lands can still collide.

---

## Blast radius — measured 2026-09-19

| What | Detail |
| --- | --- |
| Files changed | `surfaces/dashboard/github_builds.py` (**193**, shrinks); one new sibling module; one or two new test files under `surfaces/tests/`; the two URL assertions in `surfaces/tests/test_github_builds.py` (**192**) and its `_runs_response` helper; `docs/design-log.md`; `pyproject.toml` + `uv.lock` (PATCH); this spec's handback sections |
| Agents affected | **None.** `surfaces/` is in no image: `build-images.yml` builds from `agents/`, `kernel/`, `contracts/`, `orchestration/` and two scripts. The reader runs on the operator's machine |
| Contract change? | No |
| Graph vocabulary change? | No. `DeployRecord` keeps its four properties (`tag`, `git_sha`, `deployed_at`, `actor`) |
| New env keys / tunables | None. `main` stays a module constant, as the `"branch": "main"` literal is today |
| Deploy implication | **None.** The fix takes effect in the operator's `main` checkout on pull. The PATCH bump touches `pyproject.toml`/`uv.lock`, so the push to `main` rebuilds images; the fleet does not move |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the four design decisions** in `docs/design-log.md`.
3. **Plant the failing tests first** (A1, A2, A6) and watch them fail on the unchanged code. Paste the red output.
4. **Split** `github_builds.py` with no behaviour change, and run the existing tests green.
5. **Implement** items 1 and 2.
6. **Prove the guards can fail (DL-70).** Break each one (drop the ancestry check, flip `ahead_by == 0`,
   restore the substring match) and watch A3, A5 and A6 go red. Restore.
7. **`make ci` green**: all 12 steps, **redirected to a file, never piped**.
8. **Push the branch and run `make gate-ran`** from the worktree whose `HEAD` is the commit you pushed.
9. **Fill the handback sections** at the bottom of this file, set **Status:** `BUILT`, commit, push, and
   re-run `make gate-ran` on that final commit.

---

## Test plan

All tests use a fake HTTPS opener. None reaches `api.github.com`, and every SHA in a fixture is a full
40-character SHA. Use the real ones measured above.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 A tag-dispatched build of a commit on `main` is returned | runs for `head_sha=7d3ff519…`: one run, `head_branch="v0.98.08"`, `event="workflow_dispatch"`, id `35217747046`; `compare/main...7d3ff519…` → `{"status": "behind", "ahead_by": 0}`; log says `trading-agents-master:s211` | `image_builds_for_tag("s211", "7d3ff519…")` returns exactly that build. **Red on `main` today** (returns `()`) |
| A2 | 🎯 End to end: the record S211 could not write | `GitHubActionsReader` over A1's opener, passed to `record_verified_deploy` on an in-memory graph | one `DeployRecord` with `tag="s211"`, `git_sha="7d3ff519…"`. **Red today** (`DeployRecordVerificationError: GitHub build evidence is required…`). `surfaces` already imports `orchestration` (`surfaces/dashboard/projections.py`), so put this test under `surfaces/tests/` |
| A3 | 🪤 A build of a commit not on `main` is still refused | runs for `head_sha=576ee571…`: `head_branch="chore-container-smoke"`, id `29904029290`; compare → `{"status": "diverged", "ahead_by": 1}`; log says `trading-agents-master:smoke-test` | `image_builds_for_tag("smoke-test", "576ee571…")` returns `()`, and `record_verified_deploy` refuses. Green before and after, so prove it with the DL-70 break (drop the ancestry check → A3 red) |
| A4 | 🪤 An unreadable ancestry answer refuses | compare → HTTP 404; then a transport error; then a body with no `ahead_by` | `GitHubReadError` each time, message sanitized (no token, no URL, no raw exception text); the recorder refuses |
| A5 | 🪤 The compare direction is pinned | compare → `{"status": "ahead", "ahead_by": 3}`; assert the request URL | returns `()`, and the URL is `…/compare/main...{sha}`. Reversing base and head flips the meaning |
| A6 | 🎯 A tag matches only whole | a `main`-ref run whose log says `trading-agents-master:s214` | `s214` returns the build; `s21` and `s2` return `()`. **Red today** for `s21` and `s2` |
| A7 | Tag boundary edges | logs ending the tag with `"`, `\n`, a space, end of file, and `-rc1` | `s214` matches the first four and does **not** match `:s214-rc1` |
| A8 | Unchanged: `main`-ref runs make no compare call | the existing `main`-run fixtures | no request contains `/compare/`; existing tests pass (after the deliberate edits named in Traps) |
| A9 | Unchanged: `latest_main_image_build` and the no-SHA listing keep `branch=main` | assert both URLs | `branch=main` is in both |

---

## Success factors

- [ ] A1 and A2 pass, and both were watched red on the unchanged code first.
- [ ] A build of a commit not contained in `main` is refused (A3), and an unreadable compare refuses (A4).
- [ ] `s21` and `s2` no longer match an `s214` log (A6); boundary edges hold (A7).
- [ ] `latest_main_image_build` and the no-SHA path unchanged (A8, A9). `deploy_record.py`, `record_deploy.py`
      and `projections_currency.py` unchanged, or the change is named and justified.
- [ ] Four design decisions recorded as a DL entry with the rejected alternatives.
- [ ] Law-cycle question answered No, with the reason.
- [ ] Each guard planted, watched to fail, restored, stated per guard.
- [ ] Every touched module under 200 lines; `github_builds.py` shorter than 193.
- [ ] `make ci` exit 0, 100.00 % coverage, redirected to a file.
- [ ] Branch pushed; `make gate-ran` exit 0 for the branch tip, with the printed SHA equal to `git rev-parse HEAD`.

---

## Traps

🪤 **Two existing tests assert the very URL this sprint changes.** `test_github_reader_finds_successful_builds_that_published_tag`
expects `f"{runs_url}&head_sha=s194-sha"` in its `seen` list, and `test_github_reader_returns_empty_for_missing_candidate_build`
expects `…runs?branch=main&status=success&per_page=100&head_sha=missing-sha`. **Those assertions pin the
defect.** Update them to the new SHA-path URL and name the edit in Return notes. Do not delete either test.

🪤 **Existing fixture runs carry no `head_branch`.** `_runs_response` in `test_github_builds.py` builds rows
with only `head_sha`, `id` and `html_url`. GitHub always sends `head_branch`. **Never read a missing
`head_branch` as `main`**, because that fails open. Either treat it as incomplete (as `_build_from_run` does
for a missing `id`) or send it to the ancestry check. Then add `head_branch: "main"` to the helper and say so.

🪤 **Dropping `branch=main` alone turns A1 and A2 green.** It also admits the never-merged `smoke-test` build.
A3 is the only test that tells the two fixes apart, so break-check it.

🪤 **Direction.** `compare/main...{sha}` gives `behind` or `identical` (`ahead_by == 0`) when `main` contains
the commit. `compare/{sha}...main` reports the same fact as `ahead`. Measured: `main...7d3ff51` →
`behind`/`0`; `main...576ee57` → `diverged`/`1`.

🪤 **The existing fakes answer every unknown URL with a log zip.** Add a compare request to the `main`-ref
path and it gets zip bytes, fails JSON parsing and turns old tests red for the wrong reason. Decision 2
avoids this. If you choose otherwise, change the fakes on purpose and say so.

🪤 **A short SHA proves nothing against a fake.** GitHub returns 0 runs for an abbreviated `head_sha`, but a
fake will happily match `7d3ff51`. Use full SHAs in every fixture.

🪤 **Never run `scripts/record_deploy.py`, and never work in the main checkout.** The main checkout has a
`.env` pointing at the **production** graph, and `record_deploy.py` appends a permanent `DeployRecord` there.
Work in a worktree, which has no `.env`. The live check is the planner's, after merge.

🪤 **Line endings.** Repo files are LF, and there is no `.gitattributes` (work-queue item 69). Before each
commit, run `git ls-files --eol` on the files you touched and confirm `i/lf`.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass size.
  📌 Current sizes: `github_builds.py` **193**, `test_github_builds.py` **192**, `test_github_builds_env.py` **48**,
  `deploy_record.py` **125**, `test_deploy_record_verification.py` **167**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`. Copy the shape from `github_builds.py`.
- No magic numbers that influence processing. A branch name and a tag charset are constants, not tunables.
- Faults, not silent failure. Every GitHub read failure is a `GitHubReadError`, never a quiet `()`.
- `make ci` **all 12 steps** green, **100.00 % coverage floor** (`surfaces` is in the coverage source).
  **Never measure the gate through a pipe**: `make ci | tail` reports `tail`'s exit code, not `make`'s.
- PATCH bump in `pyproject.toml`, with `uv.lock` staged alongside it.
- Secrets never through the worktree. The worktree has **no `.env`**, and that is correct for this sprint:
  every proof here is a unit test.

---

## Sequencing after merge

1. The builder: `make ci` green locally, branch pushed, **`make gate-ran` exits 0** on the final commit.
   🪤 Run it from the worktree whose `HEAD` is that commit, and check the printed SHA against `git rev-parse HEAD`.
2. The planner verifies the handback, merges `--no-ff` to `main` and pushes, then checks post-merge CodeQL.
3. **No deploy.**
4. **Live check (planner, main checkout with `.env`, read-only):** `image_builds_for_tag("s211",
   "7d3ff519…")` returns run `35217747046`; `("smoke-test", "576ee571…")` returns `()`; `("s21",
   "1a6f3429…")` returns `()`. Record it in `docs/laws/functionality-checks.md`.
5. Update the deploy-fleet skill so step 2 may dispatch on the release tag. S213's deploy is the first real
   use, and its `DeployRecord` is the closing proof for work-queue item 72.

---

## Handover — paste this to Copilot

```text
Sprint 215 - a build is deploy evidence when its commit is on main, and only for the tag it published.
Spec: docs/sprints/sprint-215-a-build-is-evidence-for-its-commit-and-its-tag.md. Read it whole first,
then AGENTS.md and CLAUDE.md. Where they disagree, CLAUDE.md wins.

WHERE TO WORK: a new git worktree on branch sprint-215-build-evidence-commit-and-tag, cut from current
origin/main, e.g.
  git worktree add ../trading-agents-sprint-215 -b sprint-215-build-evidence-commit-and-tag origin/main
Never commit to main. Never work in the main checkout: it has a .env pointing at the production graph.
NEVER run scripts/record_deploy.py or anything else that writes to the live graph. Do not merge, do not deploy.
Take the next PATCH version in pyproject.toml at the end, and stage uv.lock with it.

MUST RULE: before any code, read docs/laws/conventions.md, docs/laws/drift-register.md and
docs/sprints/sprint-180-a-deploy-record-must-name-the-commit-that-was-built.md, then fill the Law reading
record at the bottom of the spec.
LAW-CYCLE ANSWER: NO. Operator tooling in surfaces/dashboard only. No agents/, no contracts/, no new
DeployRecord property. If you find yourself editing agents/ or contracts/, STOP and report.

WHAT TO BUILD (surfaces/dashboard/github_builds.py, 193 lines, so split it first with no behaviour change):
1. image_builds_for_tag(tag, git_sha) with a SHA: list successful runs for that SHA WITHOUT branch=main.
   Keep a run only if head_branch == "main", or GET /repos/{repo}/compare/main...{head_sha} returns
   ahead_by == 0. An unreadable or malformed compare raises GitHubReadError (sanitized). Never assume
   contained. The tag log check still applies to every kept run.
2. _run_log_mentions_tag: match "trading-agents-master:{tag}" only when the next byte is not in
   [A-Za-z0-9_.-] or the tag ends the file. "s21" must not match ":s214"; "s214" must not match ":s214-rc1".
3. Unchanged: latest_main_image_build() and the no-SHA listing keep branch=main. deploy_record.py,
   record_deploy.py and projections_currency.py should need no edit.

ORDER: record the 4 design decisions in docs/design-log.md (next free DL, expect DL-177) -> write tests
A1, A2 and A6 and watch them FAIL on unchanged code (paste the red output) -> split the module, existing
tests green -> implement -> write A3-A5 and A7-A9 -> break each guard (drop the ancestry check,
flip ahead_by == 0, restore substring matching), watch A3/A5/A6 go red, restore ->
make ci > <file> 2>&1; echo $?   (never pipe) -> push the branch -> make gate-ran from the worktree,
and check the printed SHA equals git rev-parse HEAD -> fill Closeout + Return notes, set Status: BUILT,
commit, push, and run make gate-ran again on that final commit.

TRAPS:
- Two existing tests in surfaces/tests/test_github_builds.py assert the SHA-path URL contains branch=main
  (test_github_reader_finds_successful_builds_that_published_tag,
  test_github_reader_returns_empty_for_missing_candidate_build). Those assertions pin the defect: update
  them to the new URL and say so. Do not delete the tests.
- Fixture rows from _runs_response have no head_branch. Never treat a missing head_branch as "main"
  (that fails open). Add head_branch to the helper.
- Dropping branch=main alone makes A1/A2 green AND admits the never-merged smoke-test build (A3).
- compare/main...{sha}: contained <=> ahead_by == 0. Reversed direction reports "ahead".
- Full 40-char SHAs in every fixture. Tests use fake openers only; no network.
- Test files are near 200 lines: new tests go in a new file. Every module < 200, no # noqa, 100.00% coverage.
- Keep LF line endings: check git ls-files --eol on touched files before committing.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| GitHub build reader, deploy evidence tests, and append-only writer | `docs/laws/conventions.md`; `docs/laws/drift-register.md`; S180 | LAW-02 proof discipline; no agent clause | Yes. This is operator tooling outside every agent law/test plan, so tests cite no invented clause and the existing `DeployRecord` shape remains unchanged. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No. It changes only
the `surfaces/dashboard/` reader's evidence selection; it does not change `contracts/`, any agent, or a
`DeployRecord` property. The corrected reader enforces S180's existing proof guarantee.

**Contradictions found between a law and this spec:** None.

**Laws found silent where a decision was needed:** No agent law governs GitHub build evidence. The four
operator-tooling decisions are recorded in DL-177; this is not a law/code drift.

**Clauses that were ⬜ and are now proven:** None; no law clause governs this code.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_tag_dispatched_build_of_main_ancestor_is_evidence` | `surfaces/tests/test_github_build_tag_ancestry.py` | PASS | none (no clause governs this code) |
| A2 | `test_tag_dispatched_main_ancestor_records_a_deploy` | `surfaces/tests/test_github_build_tag_ancestry.py` | PASS | none (no clause governs this code) |
| A3 | `test_divergent_build_is_not_deploy_evidence` | `surfaces/tests/test_github_build_tag_guards.py` | PASS | none (no clause governs this code) |
| A4 | `test_unreadable_or_malformed_ancestry_refuses` | `surfaces/tests/test_github_build_tag_guards.py` | PASS | none (no clause governs this code) |
| A5 | `test_ancestry_uses_main_as_compare_base` | `surfaces/tests/test_github_build_tag_guards.py` | PASS | none (no clause governs this code) |
| A6 | `test_tag_lookup_rejects_prefixes_of_published_tag` | `surfaces/tests/test_github_build_tag_ancestry.py` | PASS | none (no clause governs this code) |
| A7 | `test_tag_boundary_matches_only_complete_docker_tags` | `surfaces/tests/test_github_build_tag_guards.py` | PASS | none (no clause governs this code) |
| A8 | `test_main_run_skips_compare_and_url_shapes_are_preserved` | `surfaces/tests/test_github_build_tag_guards.py` | PASS | none (no clause governs this code) |
| A9 | `test_main_run_skips_compare_and_url_shapes_are_preserved` | `surfaces/tests/test_github_build_tag_guards.py` | PASS | none (no clause governs this code) |

**Tests added beyond the plan:** `test_non_object_json_response_refuses` proves a non-object GitHub JSON
payload fails closed as `GitHubReadError`; it covers the new response-shape validation required for complete
coverage.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):**
`C:\Users\yury_\Downloads\project\trading-agents-sprint-215-build-evidence-commit-and-tag`; no `.env`
was present. No live graph, broker, or GitHub mutation was performed.

**Result:** For a supplied SHA, `GitHubActionsReader.image_builds_for_tag` accepts a successful build that
published the requested complete Docker tag only when its commit is contained in `main`. Tag-dispatched S211
build evidence is accepted after its commit reaches `main`; the divergent `smoke-test` build remains refused;
`s21` and `s2` no longer match an `s214` publication. The no-SHA path and dashboard main-currency read remain
main-only.

**Files changed:** the detector baseline; `docs/design-log.md`; this sprint handback; `pyproject.toml`;
`uv.lock`; `surfaces/dashboard/github_builds.py`; new
`surfaces/dashboard/github_tag_builds.py`; `surfaces/tests/test_github_builds.py`; new
`surfaces/tests/test_github_build_tag_ancestry.py`; new `surfaces/tests/test_github_build_tag_guards.py`.

**Design decisions:** DL-177 in `docs/design-log.md`; rejected routes are recorded under its `Rejected routes`
heading. No ADR and no law-cycle change: this remains operator tooling only.

**Proof — the red run first:**

```text
FAILED surfaces/tests/test_github_build_tag_ancestry.py::test_tag_dispatched_build_of_main_ancestor_is_evidence - AssertionError: assert () == (MainImageBuild(...),)
FAILED surfaces/tests/test_github_build_tag_ancestry.py::test_tag_dispatched_main_ancestor_records_a_deploy - orchestration.deploy_record.DeployRecordVerificationError: GitHub build evidence is required...
FAILED surfaces/tests/test_github_build_tag_ancestry.py::test_tag_lookup_rejects_prefixes_of_published_tag - AssertionError: assert (MainImageBuild(...),) == ()
3 failed in 32.98s
```

**Proof — the green run:**

```text
$ uv run pytest surfaces/tests/test_github_builds.py surfaces/tests/test_github_build_tag_ancestry.py surfaces/tests/test_github_build_tag_guards.py orchestration/tests/test_deploy_record_verification.py --no-cov -q
.....................................                                    [100%]
37 passed in 1.72s
```

**Proof — lowercase boundary red run:**

```text
$ uv run pytest surfaces/tests/test_github_build_tag_guards.py::test_tag_boundary_matches_only_complete_docker_tags --no-cov -q
.....F...                                                                [100%]
FAILED surfaces/tests/test_github_build_tag_guards.py::test_tag_boundary_matches_only_complete_docker_tags[a-False]
1 failed, 8 passed in 1.90s
```

**Guards planted:** A3: replaced the non-main ancestry predicate with `True`; the divergent smoke build became
deploy evidence and `test_divergent_build_is_not_deploy_evidence` failed; restored the predicate. A5: inverted
`ahead_by == 0`; `test_ancestry_uses_main_as_compare_base` failed for `ahead_by=3`; restored the predicate.
A6: restored raw substring matching; `test_tag_lookup_rejects_prefixes_of_published_tag` failed because `s21`
and `s2` matched `s214`; restored complete Docker-tag matching. Lowercase follow-up: removed lowercase
letters from `_DOCKER_TAG_CHARACTERS`; `test_tag_boundary_matches_only_complete_docker_tags[a-False]` failed
with `1 failed, 8 passed`; restored `ascii_letters`.

**Module line counts:** `github_builds.py` 170; `github_tag_builds.py` 94; `test_github_builds.py` 195;
`test_github_build_tag_ancestry.py` 127; `test_github_build_tag_guards.py` 198. All are below the 200-line
hard limit.

**`make ci`:** `C:\Users\yury_\AppData\Local\Temp\sprint-215-followup-ci.txt`; exit 0. `2858 passed,
6 skipped`; coverage `100.00%`; `pip-audit`: `No known vulnerabilities found`; tracked and untracked
detect-secrets checks passed (the latter had no untracked files to scan).

**`make gate-ran`:** From
`C:\Users\yury_\Downloads\project\trading-agents-sprint-215-build-evidence-commit-and-tag`, implementation
commit `b6e3f6167740ec77e8adec733cbf3921844eeba7`.

```text
GATE PROVEN for b6e3f6167740ec77e8adec733cbf3921844eeba7:
   CI: success (attempt 1)
   Security Findings: success (attempt 1)
```

**Not met / verified failing:** None. The final handback commit must still be pushed and proven separately.

---

## Return notes

- Scope held. `orchestration/deploy_record.py`, `scripts/record_deploy.py`, and dashboard currency
   projections are unchanged; no deployment or live `DeployRecord` was created.
- The existing reader fixture lacked `head_branch`; it now supplies `main` explicitly rather than allowing
   a missing value to pass as main. The two existing candidate-SHA URL assertions were updated to the
   intentionally branchless route.
- The detector-baseline hash `a8c16c0156aa3aee9c4b2a3ed05554f069c9c732` is the public S214 merge SHA
   `1a6f3429a728b0348ed2059de52b535803cb3fa4`, not the S211 SHA. The direct Markdown pragma was not reliable
   through the Make-path hook. The next sprint should run its live read-only check only after merge, as
   specified; this sprint did not dispatch, record, or deploy anything.
