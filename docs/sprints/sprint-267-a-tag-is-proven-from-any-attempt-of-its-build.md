<!-- Agent: planning | Role: sprint handover -->
# Sprint 267 — a tag is proven from any attempt of its build, so a build in which a failed job was re-run can be recorded

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-267-a-tag-is-proven-from-any-attempt-of-its-build`
**Status:** BUILT
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** [DL-288](../design-log.md) (this sprint's six decisions, made and measured) · [DL-278](../design-log.md) (where the defect was met) · [work-queue 115](../work-queue.md) · DRIFT-111

> **Why this bump kind.** No new capability: the deploy record already rests on a successful build
> of the commit having published the tag, and for a build with a re-run job the reader cannot see
> that it did. A fix, so PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `surfaces/laws/laws.md` | The surfaces' **locked constitution** | **LOCKED. Read-only during a build**, except the one clause this spec adds (`SRF-DEP-04`). A clause you believe is wrong is a `drift-register.md` row plus a report, never a quiet edit |
| `surfaces/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: surfaces **`DEP`**, **`SEC`**, **`FAIL`**, **`PERF`**.

### The rule

1. **Before writing code**, read every law file in the map below, whole.
2. Read `surfaces/laws/test-plan.md` alongside `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Read the law-cycle answer below.** It is already answered; build it as written.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**No file in `contracts/` changes, and none may. Yes: the surfaces' law has never said how a tag is
proven**, and this sprint changes how. One law cycle is owed in this unit of work: **one clause is
added, `SRF-DEP-04`.**

| Book | From | What the cycle owes |
| --- | --- | --- |
| `surfaces/laws/laws.md` | LOCKED v1.5 | **`SRF-DEP-04` added** after `SRF-DEP-03`, with the text under *The clause* below. Changelog line, version up. No other clause changes |
| `surfaces/laws/test-plan.md` | v1.5, 30 / 37 | A row for `SRF-DEP-04` citing T1 to T8, 🟩; the header's two versions follow the law's |
| `docs/laws/ledger.md` **and** `docs/laws/INDEX.md` | surfaces 30 / 37, v1.5 | The surfaces' line, in both, names this sprint, DL-288 and the new version, with the count the gate computes (one clause added, one proven) |
| `docs/laws/drift-register.md` | DRIFT-111 is OPEN | Its status cell becomes CORRECTED, naming this sprint and the tests |

🪤 **The rollup is derived, not declared.** Let `scripts/check_law_coverage.py` tell you the number.
🪤 **The law gate does not check each citation.** Measured 2026-10-10: a row that cites one live
test naming the clause passes with a dead citation beside it. List every test `SRF-DEP-04`'s row
cites, with its file, in the handback.

#### The clause

> - **SRF-DEP-04** — The GitHub reader counts a successful image-build run as evidence that a tag
>   was published only when one of the run's logs names the master image under that tag as a
>   complete tag (`trading-agents-master:<tag>`; a longer tag that begins with it proves nothing).
>   **Every attempt of the run is evidence**: the latest attempt's log archive is read first, then
>   each earlier attempt's, newest first, until one names the tag, because after a re-run the run's
>   own archive holds the re-run jobs alone. With a commit given, a run counts only when that
>   commit is on `main`'s history, and a run that does not count is not read. An archive, a
>   comparison or an attempt count that cannot be read is an error, never an absent tag; a row
>   that names no attempt count has had one attempt. *(DRIFT-111, S267, DL-288.)*

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `surfaces/dashboard/github_tag_builds.py` | `surfaces/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `SRF-DEP-01` (the optional GitHub reader), `SRF-SEC-02` (external read errors are sanitised), `SRF-FAIL-01`, `SRF-PERF-02` (each read is bounded by the declared timeout) |
| nothing in `orchestration/` | `orchestration/deploy_record.py` (read it) | `record_verified_deploy` records only when the reader returns a build of the claimed commit; it does not change |

⚠️ **The one invariant this sprint must not break: unreadable evidence never reads as absent
evidence, and absent evidence never reads as proof.** A tag is proven only by a complete tag in a
log of a successful run of a commit on `main`'s history. If your change would let a run count that
does not meet all of that, or let an archive that could not be read pass as "the tag is not
there", stop and report.

---

## Goal

At merge, the reader that proves a tag from a build's logs reads every attempt of a run, the latest
first, so a successful build in which a failed job was re-run is evidence for the tag its first
attempt published, and `scripts/record_deploy.py` records a deploy from it.

## Why (context)

On 2026-10-08 the `s259` build pushed fifteen images and failed one job (a vulnerability scan could
not download its database). The failed job was re-run, the run read `success`, the fleet was
retagged and verified, and then the deploy could not be recorded: *"GitHub build evidence is
required before recording a deploy"* ([DL-278](../design-log.md)). GitHub's log archive for a run
is its latest attempt's, and after a re-run of the failed jobs that is those jobs' logs alone. The
same commit had to be built again under a second tag and the fleet retagged twice.

The deploy skill has since said *never re-run a failed job, dispatch a fresh run*. That works, and
costs a whole build and a second tag each time one job flakes.

### Measured, 2026-10-11 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| The run that had a re-run job | `37767377219`: `run_attempt` 2, `conclusion` success, commit `49146e40` | *[measured, GitHub]* `GET /repos/…/actions/runs/37767377219` |
| Its latest archive, `/runs/{id}/logs` | 25,420 bytes zipped, 127,151 unpacked, the scanner job alone, **0** mentions of `trading-agents-master:s259` | *[measured, GitHub]* the archive downloaded and searched |
| Its first attempt's archive, `/runs/{id}/attempts/1/logs` | 434,794 bytes zipped, 2,205,361 unpacked, 30 entries, **5** mentions as a complete tag | *[measured, GitHub]* same. `/attempts/2/logs` is the latest archive byte for byte in size; `/attempts/3/logs` answers HTTP 404 |
| DL-278's figures for the same archives (953 KB, 56 KB, ten mentions) | not reproduced | *[measured]* GitHub serves the same run's archives differently three days on; the finding stands, the sizes do not |
| The run rows the reader lists carry the attempt count | `run_attempt` on **100 of 100** successful runs; 99 have had one attempt, 1 has had two | *[measured, GitHub]* `GET …/workflows/build-images.yml/runs?status=success&per_page=100` |
| The repo's reader on today's code | `s259` for the commit: **no run**; `s259a`: run `37770503860`; `s25`: none | *[measured, read-only on GitHub]* the planner's `wq115_reader_on_real_run.py`, the real `GitHubActionsReader` with a counting `_read_bytes` |
| The same on the prototype | `s259`: run `37767377219`, after reading `/logs` and then `/attempts/1/logs`; `s259a` and `s25` as before; `record_verified_deploy` on an in-memory graph records `s259`; 43 seconds | *[measured, read-only on GitHub]* same script, from `../ta-s267` |
| What refusing costs today | the record step did not finish in 280 seconds: when the commit's own runs do not name the tag, `record_verified_deploy` asks again without the commit and the reader downloads the archive of each of the last 100 successful `main` runs | *[measured]* same script on `main`, stopped by its time limit. **Named, not this sprint's** |
| Who calls the tag lookup | `orchestration/deploy_record.py`, twice; nothing else outside tests | *[measured, grep]* the dashboard's deploy currency uses `latest_main_image_build` and `runtime_changes` |
| What the law says of proving a tag | nothing: no clause, and the existing tag tests cite none | *[measured, grep]* `surfaces/laws/laws.md`, `surfaces/tests/test_github_build_tag_*.py` |
| Existing tests the prototype breaks | **none**: the 39 tests of the five related files pass unedited, and the full suite reads **4,661 passed, 8 skipped, 100.00 %** | *[measured, run]* `../ta-s267` with the prototype and its 15 new tests |
| The planned tests against the unchanged code | **12 of 15 fail on behaviour**; the three that pass state what does not change (a run of one attempt, twice, and a run off `main`) | *[measured, run]* `proto_tests_red_on_main_code.txt` |
| The planner's breaks against the planned tests | **15 red of 15**, none survived, none failed to apply | *[measured, run]* `planner_mutations.py` |

The planner's scripts and outputs are outside the repo (OneDrive `trading-agents-data/wq115-2026-10-11/`).
You do not need them, and you have no network: the Test plan's fake stands in for GitHub.

---

## Scope — and what is deliberately NOT here

1. **The failing tests first.** T1 and T3 of the Test plan, red on the unchanged code on behaviour,
   pasted in the Closeout.
2. **Every attempt is read.** In `surfaces/dashboard/github_tag_builds.py`,
   `run_log_mentions_tag` takes the run's attempt count and reads the latest archive at the path it
   reads today, then `/attempts/{n}/logs` for each earlier attempt, newest first, stopping at the
   first that names the tag. The call in `image_builds_for_tag` passes the count read from the
   run's row.
3. **The attempt count is read strictly.** A row with no `run_attempt` has had one attempt; a
   `run_attempt` that is not a positive integer is an incomplete response, refused before any
   archive is read.
4. **The rest of the Test plan**, in a new test file with its fake in a helper module.
5. **The law cycle** named above: `SRF-DEP-04`, v1.6, the test-plan row, both rollup lines,
   DRIFT-111 CORRECTED.

### Out of scope (do NOT build this sprint)

- **The slow refusal.** When no run of the commit names the tag, the fallback reads up to 100
  archives. It is the path that refuses, it is correct, and it is not this sprint's.
- **`orchestration/deploy_record.py`, `scripts/record_deploy.py`, `surfaces/dashboard/github_builds.py`.**
  None changes: the reader's port, its HTTP helpers and the record's rule stay as they are.
- **The deploy skill's rule** (*never re-run a failed job*). The planner changes it after the merge
  and the check; it is not a file you touch.
- **A limit on how many attempts are read.** None is added.
- **Proving a tag from the registry.** See *The road not taken*.
- **No contract, graph label or property, env key or tunable changes. No ADR reversal.**

### The road not taken (LAW-06)

- **Prove the tag from the registry.** Rejected: a second credential scope and a second source for
  which commit a tag was built from; the workflow run of the commit is the evidence the record
  already rests on.
- **Read the first attempt first, or every attempt always.** Rejected: 99 of 100 runs have had one
  attempt, and their one read and its path would change under every existing test.
- **Ask for the latest attempt by its number too.** Rejected: the same, for no gain.
- **Read each job's log through the jobs API.** Rejected: more calls for the same text.
- **Take an earlier archive that cannot be read for "the tag is not there".** Rejected: unreadable
  evidence and absent evidence must not look alike, which is the reader's rule today.
- **Cap the attempts read.** Rejected: no number to justify, each read is bounded by the timeout,
  and a build is re-run a handful of times at most.
- **Keep the skill's rule and close the row.** Rejected: the rule costs a second build and a second
  tag each time a scan cannot download its database.

---

## The design decisions — made, and recorded in DL-288

**They are made. Build them as written; if one cannot be built, stop and report.**

1. **D1 — every attempt of a successful run is evidence.** The reader lists only runs whose latest
   attempt concluded `success`. A job that was not re-run succeeded in the attempt whose log names
   it, and a re-run builds the same commit with the same inputs.
2. **D2 — the latest archive first, at today's path** (`/actions/runs/{id}/logs`), **then each
   earlier attempt** (`/actions/runs/{id}/attempts/{n}/logs`), **newest first, stopping at the first
   that names the tag.** A run of one attempt costs the one read it costs today.
3. **D3 — the attempt count is the run row's `run_attempt`.** Absent: one attempt. Present and not
   an integer of one or more (a boolean, a string, a float, `null`, zero, a negative): the reader's
   *"GitHub build response was incomplete"* error, before any archive is read.
4. **D4 — an earlier archive that cannot be read is an error**, the same sanitised errors the latest
   archive raises today (an HTTP failure; a body that is not a zip).
5. **D5 — one new clause, `SRF-DEP-04`**, states the whole rule for proving a tag; DRIFT-111 records
   that the law was silent.
6. **D6 — the change stays in `github_tag_builds.py`.** `run_log_mentions_tag` gains a fourth
   parameter, `attempts`, defaulting to 1; the archive search moves into a private helper.

**Named consequences, told to the operator:**

- After the merge and its check, a failed job of a build may be re-run before the fleet is retagged,
  and the deploy can be recorded. The other rule stands: a tag the fleet has pulled is never pushed
  again.
- A run of the same commit that has had more than one attempt and does not name the tag costs one
  more download for each earlier attempt.

🪤 **`DL-288` is taken by this sprint's entry on `main`.** If the build forces a decision, add an
amendment under DL-288; do not take a new number.

---

## Blast radius — measured 2026-10-11

| What | Detail |
| --- | --- |
| Files changed | `surfaces/dashboard/github_tag_builds.py` (94 lines, 115 in the prototype); two new files under `surfaces/tests/`; `surfaces/laws/laws.md`, `test-plan.md`; `docs/laws/ledger.md`, `INDEX.md`, `drift-register.md`; this file and its README row |
| Agents affected | none; the surfaces alone |
| Contract change? | no |
| Graph vocabulary change? | no |
| New env keys / tunables | none |
| Decision path? | none; no agent file changes |
| Deploy implication | **no deploy.** The reader runs from the main checkout when `scripts/record_deploy.py` records a deploy |
| Rollback | revert the commit. Nothing else: no schema, no pack, no setting, and a `DeployRecord` written meanwhile is a true record |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Read DL-288 and DL-278** in `docs/design-log.md`, and `orchestration/deploy_record.py`.
3. **Plant the failing tests first** (T1 and T3) and watch them fail on behaviour. Paste the red output.
4. **Implement** Scope 2 and 3. The Appendix holds the measured prototype.
5. **Write the rest of the plan.** No existing test changes.
6. **The law cycle**: the clause, the test-plan row, the docstring citations, both rollup lines,
   DRIFT-111.
7. **Prove the guards can fail (DL-70)**: break the implementation, watch each guard go red, restore.
8. **`make ci` green**, every step of the `ci:` target, **redirected to a file, never piped**.
9. **Fill the handback sections** at the bottom of this file.

---

## Test plan

New tests go in `surfaces/tests/test_github_build_tag_attempts.py`, their fake GitHub in a helper
module beside it. Every test cites `SRF-DEP-04`.

**The fake the plan needs (the prototype's, described):** an opener, as the existing tests inject,
built from a map of attempt number to that attempt's log text, an exception to raise, or raw bytes.
It serves one run row for the workflow-runs list (with the `run_attempt` the test gives, or none),
`{"ahead_by": n}` for the comparison, the highest attempt's archive at `/runs/{id}/logs` and each
attempt's at `/runs/{id}/attempts/{n}/logs`, and **keeps the order in which archives were asked
for**. Most assertions are on that order.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| T1 | 🎯 A tag named only in an earlier attempt is proven | Two attempts: the first names `…/trading-agents-master:s259`, the latest holds another image's log alone | The build is returned; the archives read are `logs` then `attempts/1/logs`; `record_verified_deploy` on an in-memory graph writes one `DeployRecord` with that tag and commit |
| T2 | The latest attempt is read first and no further than needed | Three attempts, the tag in the latest; then three with the tag in the second | First case: only `logs` is read. Second: `logs`, then `attempts/2/logs`, and never the first |
| T3 | A run no attempt of which names the tag is not evidence | Three attempts, none naming the tag | No build; the archives read are `logs`, `attempts/2/logs`, `attempts/1/logs`, in that order |
| T4 | A run of one attempt reads one archive | Two cases: `run_attempt` 1; a row with no `run_attempt` | No build (the log does not name the tag) and exactly one read, `logs` |
| T5 | An earlier attempt must name the complete tag | The first attempt names `…:s259a`, the latest nothing | Asked for `s259`: no build. Asked for `s259a`: the build |
| T6 | 🪤 An earlier archive that cannot be read is an error | Two cases for the first attempt's archive: an HTTP 404; bytes that are not a zip | `GitHubReadError`, and the URL's host is not in the message (`SRF-SEC-02`) |
| T7 | 🪤 An attempt count that is not a positive integer refuses | `run_attempt` of 0, −1, `"2"`, `true`, `null`, 2.0 | `GitHubReadError` matching *response was incomplete*, and no archive was read |
| T8 | A run off `main` is not evidence whatever an attempt names | Two attempts, the first naming the tag; the run's branch is not `main` and the comparison says one commit ahead | No build, and no archive was read |

**No existing test may change.** The prototype passed all 39 tests of
`test_github_builds.py`, `test_github_build_tag_ancestry.py`, `test_github_build_tag_guards.py`,
`test_github_builds_env.py` and `orchestration/tests/test_deploy_record_verification.py` unedited.

---

## Success factors

- [x] A successful run whose latest archive does not name the tag and whose earlier attempt does is
      returned as a build, and a deploy is recorded from it (T1).
- [x] The latest archive is read first, at today's path; an earlier attempt is read only when the
      later ones did not name the tag, newest first (T2, T3).
- [x] A run of one attempt costs one read (T4).
- [x] The complete-tag rule and the `main`-history rule hold for every attempt (T5, T8).
- [x] An earlier archive or an attempt count that cannot be read is an error (T6, T7).
- [x] No production file other than `surfaces/dashboard/github_tag_builds.py` changes; no existing
      test changes.
- [x] The law cycle done: `SRF-DEP-04` as written, v1.6, changelog, the test-plan row, both rollup
      lines with the gate's count, DRIFT-111 CORRECTED.
- [x] Every new guard planted, watched to fail, restored, stated per guard.
- [x] Every touched module under 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage; any step the sandbox cannot run named NOT RUN.

---

## Traps

🪤 **`any()` over a list reads every archive before it searches one.** The stop at the first
attempt that names the tag needs a generator; T2 fails on a list.
🪤 **`True` is an integer in Python.** `isinstance(True, int)` holds; D3 refuses a boolean by name.
🪤 **`surfaces/tests/test_github_build_tag_guards.py` is at 198 lines.** Add nothing to it.
🪤 **The prototype's test file was 207 lines with its fake inside it.** Keep the fake in a helper
module (the prototype's two files were 127 and 96 lines).
🪤 **A fake that serves the same archive at every path proves nothing.** The latest archive and
each attempt's must differ, and the test must assert which were asked for.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` beyond the two the
  existing test helpers already use for a fake token.
  📌 Current sizes: `surfaces/dashboard/github_tag_builds.py` **94**,
  `surfaces/dashboard/github_builds.py` **180**, `surfaces/tests/test_github_build_tag_guards.py`
  **198**, `surfaces/tests/test_github_builds.py` **195**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers. This sprint adds none.
- Faults, not silent failure: the reader's sanitised `GitHubReadError`.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- **Do not touch `pyproject.toml` or `uv.lock`.** The planner bumps the version at merge.
- Secrets never through the worktree — a worktree has **no `.env`** and you need no token: no test
  calls GitHub. **State which tree you ran in.**

---

## Sequencing after merge (the planner's)

1. Review the diff against the checklist; re-measure (the scope command; the production file
   against the prototype's blob id; the planner's 15 breaks against the builder's tests; each test
   `SRF-DEP-04`'s row cites, resolved by hand); merge `main` in; PATCH bump, `uv lock`; Windows
   `make ci`; push; **`make gate-ran` from `../ta-s267`**, the printed SHA checked against
   `git rev-parse HEAD`; CodeQL set-diff against the open alerts of the last merged branch;
   fast-forward `main`; tag.
2. **F1, at no cost, from the main checkout on the merged code, read-only on GitHub:**
   `wq115_reader_on_real_run.py` finds run `37767377219` for `s259` after reading its latest
   archive and then its first attempt's, finds `s259a` and `s25` as today, and records `s259` on an
   in-memory graph. Nothing is written to the live graph.
3. **Then the deploy skill:** *never re-run a failed job* becomes *a failed job may be re-run before
   the retag*; the rule about a tag the fleet has pulled stays.
4. No deploy. **Not proven by any of these:** a real deploy recorded on the live graph from a build
   with a re-run job; that waits for the next job that fails.

---

## Handover — paste this to Codex

```text
Sprint 267 — a tag is proven from any attempt of its build, so a build in which a failed job was
re-run can be recorded.
Spec: docs/sprints/sprint-267-a-tag-is-proven-from-any-attempt-of-its-build.md (read ALL of it,
then CLAUDE.md). Repo: yury-gurevich/trading-agents, local checkout.

Your worktree already exists: ../ta-s267, on branch
sprint-267-a-tag-is-proven-from-any-attempt-of-its-build, cut from main, with its venv synced to
the lock. Work only in that worktree, never in the main checkout and never on main. Another builder
is working in ../ta-s266 on a different sprint: do not open it. You have no .env, no network and
no GitHub token, and you need none: every proof is a unit test with a fake opener, as the existing
tests in surfaces/tests/test_github_build_tag_guards.py inject one. `uv run` is safe; never run a
bare `uv sync`. Do not touch pyproject.toml or uv.lock, and say so: the planner bumps the version
at merge. Do not push and do not merge: commit on the branch and hand back. Do not edit
docs/STATE.md, docs/work-queue.md or docs/design-log.md (one exception: an amendment under DL-288
if the build forces a decision), and nothing under .claude/. If a make ci step cannot run in your
sandbox (the dependency audit needs the network), do not bypass it silently: name the step as NOT
RUN in the handback.

This handover is complete: nobody will send you follow-up messages. Two tiers:
- A wrong line number, count, path, test name or clause number whose intent is plain from the
  spec's Scope and Success factors is NOT a reason to stop: follow the intent, record the
  correction in Return notes, continue. The same holds if a gate wants a rollup line or a test-plan
  row worded differently from the spec: do what the gate accepts and say so.
- STOP and report, without improvising, when: the build needs a change to any production file
  other than surfaces/dashboard/github_tag_builds.py (surfaces/dashboard/github_builds.py,
  orchestration/deploy_record.py and scripts/record_deploy.py included); to anything under
  contracts/, kernel/, agents/ or infra/; an EXISTING test has to be edited (the planner's
  prototype broke none of 4,646); a law you read contradicts the spec; or a decision D1-D6 cannot
  be built as written.

What and why: before a fleet deploy is recorded, the reader in
surfaces/dashboard/github_tag_builds.py proves that a successful image build of the commit
published the tag, by finding `trading-agents-master:<tag>` in the build's log archive. GitHub's
archive for a run is its LATEST attempt's, and after a re-run of the failed jobs that is those
jobs' logs alone. So a build whose one failed job was re-run reads `success` and cannot be proven:
the deploy was refused its record on 2026-10-08, and the same commit had to be built again under a
second tag. You make the reader read every attempt: the latest archive first, at the path it reads
today, then /attempts/{n}/logs for each earlier attempt, newest first, stopping at the first that
names the tag. You unit-test it. You call nothing over the network.

MUST RULE before any code: read, whole, surfaces/laws/laws.md with its test-plan.md,
docs/laws/conventions.md, docs/laws/drift-register.md, surfaces/dashboard/github_tag_builds.py,
surfaces/dashboard/github_builds.py, orchestration/deploy_record.py, the three test files
surfaces/tests/test_github_build*.py, and DL-288 and DL-278 in docs/design-log.md. Fill the Law
reading record first.
Law-cycle answer: YES for surfaces: ONE new clause, SRF-DEP-04, with the text the spec gives under
"The clause", placed after SRF-DEP-03; changelog; version v1.5 -> v1.6 in laws.md and in the
test-plan's header; a test-plan row citing T1-T8; both rollup lines with the count the gate
computes; DRIFT-111 CORRECTED. NO contracts/ file changes.

Order (the spec's Steps): laws -> plant T1 and T3, watch them fail on behaviour, paste the red ->
implement (the Appendix holds the measured prototype) -> the remaining tests -> the law cycle and
DRIFT-111 -> break and restore every guard -> make ci to a file.

Build (decisions D1-D6 are made; build them as written):
1. run_log_mentions_tag(reader, run_id, tag, attempts=1): the urls are
   .../actions/runs/{run_id}/logs first, then .../actions/runs/{run_id}/attempts/{n}/logs for n
   from attempts-1 down to 1; return whether any names the tag, reading lazily (a generator, so
   nothing is read after the first hit).
2. A private helper holds what the function does to one archive today (open the zip, search every
   file for the complete tag, raise the existing "GitHub build log response was incomplete" on a
   bad zip).
3. A private helper reads the attempt count from the run row: row.get("run_attempt", 1); a boolean,
   a non-integer or a value below 1 raises GitHubReadError("GitHub build response was incomplete").
4. image_builds_for_tag passes that count. The order of its two conditions stays: the main-history
   check first, the logs second.
5. The tests (T1-T8) with their fake in a helper module, the law cycle.

DO NOT: read an attempt's archive before the later ones; read the latest by its attempt number;
read anything after the first archive that names the tag; treat an archive that cannot be read, or
is not a zip, as "the tag is not there"; accept a boolean, a string, a float, null, zero or a
negative as an attempt count; refuse a row that has no run_attempt; cap the attempts; change the
complete-tag rule, the main-history rule, the order of the two checks, the error texts, the
reader's port, record_verified_deploy or the script; prove a tag from the registry or the jobs
API; add a tunable; add to test_github_build_tag_guards.py (it is at 198 lines); edit an existing
test; let a test call the network; pin a version number.

Handback checklist (the handback is returned against these, one by one):
 1. Law reading record filled before the first code change.
 2. The red output of T1 and T3 pasted, from before the implementation, each failing on behaviour.
 3. Test plan results: one row for each of T1-T8, with file and status.
 4. Every guard's break-and-restore stated, one line per guard. At least these, each of which the
    planner broke on the prototype and saw red: the attempt count never passed to the log read;
    the latest attempt read twice (once more by its number); the first attempt never read; earlier
    attempts read oldest first; every archive read before any is searched; the latest archive
    skipped; only the last archive read deciding; an attempt count below one accepted; a boolean
    accepted; an attempt count of any type accepted; a row with no run_attempt refused; the count
    read from the wrong field; an archive that is not a zip taken for an absent tag; a tag matched
    by its beginning; the attempt's archive asked for at the wrong path.
 5. This prints nothing, and you say so (run it against the commit the branch was cut from if main
    has moved; name which you used):
    git diff main --stat -- agents contracts kernel orchestration scripts infra .claude surfaces/dashboard/github_builds.py surfaces/dashboard/github_tree_diff.py surfaces/context.py surfaces/queries surfaces/tests/test_github_builds.py surfaces/tests/test_github_build_tag_guards.py surfaces/tests/test_github_build_tag_ancestry.py surfaces/tests/test_github_builds_env.py pyproject.toml uv.lock docs/STATE.md docs/work-queue.md docs/design-log.md
 6. `git diff main -- surfaces/dashboard/github_tag_builds.py` pasted whole, and one line saying no
    other production file changed.
 7. One line saying no existing test changed, with `git diff main --stat -- surfaces/tests
    orchestration/tests` pasted.
 8. The surfaces law book's old and new version, SRF-DEP-04 quoted as written, its test-plan row
    quoted, DRIFT-111's status cell quoted, and both rollup lines.
 9. The law gate's output (scripts/check_law_coverage.py), exit code stated, AND every test
    SRF-DEP-04's row cites listed with its file: the gate does not check each citation.
10. make ci output file named, exit code stated, every NOT RUN step named with its reason.
11. Module line counts for every touched or new Python module; Status BUILT here and in the README
    row (the status cell leads with BUILT).
12. One line saying no test calls the network, and anything in the build you are unsure of.
State anything not met as "not done" or "verified failing". Never write a Result for work not done.
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
| Tag-build reader and new attempt tests | Whole `surfaces/laws/laws.md` and `surfaces/laws/test-plan.md`; whole `docs/laws/conventions.md` and `docs/laws/drift-register.md` | `SRF-DEP-01`, `SRF-SEC-02`, `SRF-FAIL-01`, `SRF-PERF-02`; new `SRF-DEP-04` | No change to D1-D6. `SRF-DEP-01`, `SRF-SEC-02` and `SRF-PERF-02` are currently unproven; T6 will prove the GitHub error limb only, not turn those whole clauses green. Unreadable evidence remains an error. |
| Preserved reader and deploy-record boundaries | Whole `surfaces/dashboard/github_tag_builds.py`, `surfaces/dashboard/github_builds.py`, `orchestration/deploy_record.py`; whole `surfaces/tests/test_github_builds.py`, `test_github_build_tag_guards.py`, `test_github_build_tag_ancestry.py`, `test_github_builds_env.py`; DL-288 and DL-278 in `docs/design-log.md`; this whole spec, then `CLAUDE.md` | `SRF-DEP-04` as specified, `SRF-SEC-02` | No. Preserve main-history filtering before log reads, complete-tag matching and existing sanitised errors; change only `github_tag_builds.py` in production. |

Reading completed on 2026-10-11 before any Python edit. Worktree:
`C:\Users\yury_\Downloads\project\ta-s267`; branch
`sprint-267-a-tag-is-proven-from-any-attempt-of-its-build`; clean starting HEAD,
`main` and `origin/main`: `c8926756841cfc991d98a6e638c89e18953423a7`. No `.env`.
`docs/STATE.md` is the active tracker in `CLAUDE.md`; the explicit handover excludes
editing it, `docs/work-queue.md`, `.claude/`, `pyproject.toml` and `uv.lock`.

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?**
No contract change; yes, one new surfaces guarantee. Owed: `SRF-DEP-04` verbatim,
v1.5 to v1.6 and changelog, T1-T8 citation row, both derived rollups, DRIFT-111
CORRECTED. This record precedes the tests and implementation; completion is
reported below only after proof. D1-D6 and the ruled-out options are already
recorded in DL-288; no new decision or amendment is needed.

**Contradictions found between a law and this spec:** none.

**Laws found silent where a decision was needed:** tag-proof semantics are silent
in v1.5; the existing OPEN DRIFT-111 records this gap, and DL-288 D1-D6 settle it.

**Clauses that were ⬜ and are now proven:** new `SRF-DEP-04` is proven by all
eight named tests (16 cases). No existing gray clause is promoted. The gate
derived surfaces **31 / 38**; both `ledger.md` and `INDEX.md` now carry that count
and v1.6.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| T1 | `test_t1_earlier_attempt_proves_tag_and_records_deploy` | `surfaces/tests/test_github_build_tag_attempts.py` | PASS | `SRF-DEP-04` |
| T2 | `test_t2_stops_at_first_matching_attempt` (2 cases) | `surfaces/tests/test_github_build_tag_attempts.py` | PASS | `SRF-DEP-04` |
| T3 | `test_t3_no_attempt_names_tag_reads_all_newest_first` | `surfaces/tests/test_github_build_tag_attempts.py` | PASS | `SRF-DEP-04` |
| T4 | `test_t4_one_or_omitted_attempt_count_reads_latest_once` (2 cases) | `surfaces/tests/test_github_build_tag_attempts.py` | PASS | `SRF-DEP-04` |
| T5 | `test_t5_earlier_attempt_requires_the_complete_tag` | `surfaces/tests/test_github_build_tag_attempts.py` | PASS | `SRF-DEP-04` |
| T6 | `test_t6_unreadable_earlier_archive_is_a_sanitised_error` (2 cases) | `surfaces/tests/test_github_build_tag_attempts.py` | PASS | `SRF-DEP-04`, `SRF-SEC-02` |
| T7 | `test_t7_invalid_attempt_count_refuses_before_log_reads` (6 cases) | `surfaces/tests/test_github_build_tag_attempts.py` | PASS | `SRF-DEP-04` |
| T8 | `test_t8_off_main_run_is_rejected_before_any_archive_read` | `surfaces/tests/test_github_build_tag_attempts.py` | PASS | `SRF-DEP-04` |

**Tests added beyond the plan:** no additional test function; T2's two cases are
parametrised separately (16 cases total), and T4 also exercises the unchanged
three-argument `run_log_mentions_tag` call. The fake places master evidence in
the archive's second file, after another image, to retain the all-files rule.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):**
`C:\Users\yury_\Downloads\project\ta-s267`, branch
`sprint-267-a-tag-is-proven-from-any-attempt-of-its-build`; `.env` absent.

**Result:** T1 returns the build whose first attempt published the complete tag
and writes exactly one in-memory `DeployRecord` for that tag and commit. T2-T8
pass for early stopping, newest-first absence, one/omitted attempt counts,
complete tags, unreadable earlier evidence, invalid counts and off-main refusal.
The related suite passes **55 tests**, including every unedited existing test.

**Files changed:** `surfaces/dashboard/github_tag_builds.py`;
new `surfaces/tests/github_build_attempts_helpers.py` and
`surfaces/tests/test_github_build_tag_attempts.py`; `surfaces/laws/laws.md` and
`test-plan.md`; `docs/laws/ledger.md`, `INDEX.md`, `drift-register.md`;
this sprint file and `docs/sprints/README.md`.

**Design decisions:** recorded as [`DL-288`](../design-log.md) — built as written;
no amendment. No file in `contracts/` changes.

**Proof — the red run first:**

```text
Command (before changing `github_tag_builds.py`):
uv run pytest surfaces/tests/test_github_build_tag_attempts.py --no-cov
Log: C:\Users\yury_\AppData\Local\Temp\s267-20261011-c892675\red.txt
Exit code: 1

============================= test session starts =============================
collected 2 items

surfaces\tests\test_github_build_tag_attempts.py FF                      [100%]

================================== FAILURES ===================================
____________ test_t1_earlier_attempt_proves_tag_and_records_deploy ____________
surfaces\tests\test_github_build_tag_attempts.py:26: in test_t1_earlier_attempt_proves_tag_and_records_deploy
    assert github.reader.image_builds_for_tag("s259", SHA) == (BUILD,)
E   AssertionError: assert () == (MainImageBui...mple/run/7'),)
E
E     Right contains one more item: MainImageBuild(git_sha='s267-commit', run_id=7, url='https://example/run/7')
E     Use -v to get more diff
_____________ test_t3_no_attempt_names_tag_reads_all_newest_first _____________
surfaces\tests\test_github_build_tag_attempts.py:49: in test_t3_no_attempt_names_tag_reads_all_newest_first
    assert github.archives == ["logs", "attempts/2/logs", "attempts/1/logs"]
E   AssertionError: assert ['logs'] == ['logs', 'att...empts/1/logs']
E
E     Right contains 2 more items, first extra item: 'attempts/2/logs'
E     Use -v to get more diff
=========================== short test summary info ===========================
FAILED surfaces/tests/test_github_build_tag_attempts.py::test_t1_earlier_attempt_proves_tag_and_records_deploy
FAILED surfaces/tests/test_github_build_tag_attempts.py::test_t3_no_attempt_names_tag_reads_all_newest_first
============================== 2 failed in 2.21s ==============================
```

**Proof — the green run:**

```text
Command: uv run pytest surfaces/tests/test_github_build_tag_attempts.py surfaces/tests/test_github_builds.py surfaces/tests/test_github_build_tag_ancestry.py surfaces/tests/test_github_build_tag_guards.py surfaces/tests/test_github_builds_env.py orchestration/tests/test_deploy_record_verification.py --no-cov
Exit code: 0

============================= test session starts =============================
collected 55 items

surfaces\tests\test_github_build_tag_attempts.py ................        [ 29%]
surfaces\tests\test_github_builds.py ...........                         [ 49%]
surfaces\tests\test_github_build_tag_ancestry.py ...                     [ 54%]
surfaces\tests\test_github_build_tag_guards.py ................          [ 83%]
surfaces\tests\test_github_builds_env.py ..                              [ 87%]
orchestration\tests\test_deploy_record_verification.py .......           [100%]

============================= 55 passed in 1.93s ==============================
```

**Guards planted:** each mutation compiled, failed on test behaviour (no
collection error), and restored the exact original bytes in a `finally` block.
Runner exit code 0; individual failure outputs and `mutations.json` are in
`C:\Users\yury_\AppData\Local\Temp\s267-20261011-c892675`. G01-G15 cover the required plants; G19 also checks literal
all-archives-before-any-search preloading. G16-G18 additionally guard
the main-history check order, default argument and all-files archive search.
G19 was added after the full suite; the restored bytes match that CI run,
and `uv run pytest surfaces/tests/test_github_build_tag_attempts.py --no-cov`
then passed all 16 cases (`restored.txt`, exit 0).

```text
G01: attempt count not passed; exit 1; 12 behavioral failures; restored=True
G02: latest attempt read twice by number; exit 1; 8 behavioral failures; restored=True
G03: first attempt skipped; exit 1; 5 behavioral failures; restored=True
G04: earlier attempts oldest first; exit 1; 2 behavioral failures; restored=True
G05: eager archive reads; exit 1; 2 behavioral failures; restored=True
G06: latest archive skipped; exit 1; 9 behavioral failures; restored=True
G07: only last archive decides; exit 1; 2 behavioral failures; restored=True
G08: below-one attempt count accepted; exit 1; 2 behavioral failures; restored=True
G09: boolean attempt count accepted; exit 1; 1 behavioral failures; restored=True
G10: any attempt-count type accepted; exit 1; 6 behavioral failures; restored=True
G11: missing attempt count refused; exit 1; 1 behavioral failures; restored=True
G12: count read from wrong field; exit 1; 12 behavioral failures; restored=True
G13: bad zip treated as absent tag; exit 1; 1 behavioral failures; restored=True
G14: tag prefix accepted as proof; exit 1; 1 behavioral failures; restored=True
G15: wrong attempt archive path; exit 1; 6 behavioral failures; restored=True
G16: logs searched before main-history check; exit 1; 1 behavioral failures; restored=True
G17: legacy default increased to two; exit 1; 2 behavioral failures; restored=True
G18: search only first file of archive; exit 1; 4 behavioral failures; restored=True
G19: every archive read before any search; exit 1; 2 behavioral failures; restored=True
19/19 guards red and restored; production SHA256 222328211e49f480a4ebc0ec1e229fd6477aab7855fecfe3a1cec78c304c6355
```

**Module line counts:** `surfaces/dashboard/github_tag_builds.py` **114**;
`surfaces/tests/github_build_attempts_helpers.py` **91**;
`surfaces/tests/test_github_build_tag_attempts.py` **135**. All are under 200.

**`make ci`:** redirected to `C:\Users\yury_\AppData\Local\Temp\s267-20261011-c892675\ci.txt`. Exit code **2**,
so the overall gate is **verified failing**, not green. All first 12 steps
passed; `4662 passed, 8 skipped, 2470 warnings in 497.46s (0:08:17)`, coverage **100.00 %**.
**Dependency audit: NOT RUN**, because the handover forbids network. An
external `offline/sitecustomize.py` stops that command at Python start-up
with the explicit NOT RUN message and exit 1; the Makefile and audit script
are unchanged. `UV_OFFLINE=1`, `UV_NO_SYNC=1` and localhost-only proxy
settings prevent dependency fetching. Both following secret steps were
run separately, without bypassing the failing `make ci` status:

```text
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
Exit code: 0
uv run python scripts/check_untracked_secrets.py
detect-secrets (untracked): no untracked files to scan
Exit code: 0
```

Selected real output from `ci.txt` (the full output remains in that file):

```text
Success: no issues found in 1190 source files
Contracts: 5 kept, 0 broken.
Required test coverage of 100.0% reached. Total coverage: 100.00%
SKIPPED [1] tests\test_bus_azure_config.py:21: Service Bus dotenv isolation proof requires local .env
SKIPPED [1] tests\test_bus_celery.py:181: CELERY_BROKER_URL is not set
SKIPPED [1] tests\test_deliberator_servicebus_peer.py:36: A1 proof requires .env present; CI has no local secrets file
SKIPPED [1] tests\test_graph_postgres.py:137: POSTGRES_TEST_DSN is not set
SKIPPED [1] tests\test_graph_postgres_keys.py:90: POSTGRES_TEST_DSN is not set
SKIPPED [1] agents\forecaster\tests\test_barrier_garch_oracle.py:179: could not import 'scipy.signal': No module named 'scipy'
SKIPPED [1] agents\provider\tests\test_sources.py:159: FINNHUB_TEST_NETWORK=1 is not set
SKIPPED [1] agents\provider\tests\test_stooq.py:66: STOOQ_TEST_NETWORK=1 is not set
========= 4662 passed, 8 skipped, 2470 warnings in 497.46s (0:08:17) ==========
NOT RUN: dependency audit requires network; S267 forbids network.
make: *** [Makefile:59: ci] Error 1
```

**`make gate-ran`:** not done. This handover forbids pushing and merging and
authorises fixture-only proof without network or a GitHub token. Exact-SHA
remote gates, merge, F1 and any live proof remain the planner's work.

**Not met / verified failing:** full `make ci` exit 0 is not met (dependency
audit NOT RUN, network forbidden). Push, remote gates, version bump, merge,
F1 on GitHub, deploy and live deploy-record proof are **not done**, as assigned
to the planner. No unresolved implementation uncertainty found.

**No test added by this sprint calls the network:** every GitHub read uses
`AttemptGitHub.open`; deploy verification uses `InMemoryGraphStore`.

**Scope proof:** the protected-path command below printed nothing (exit 0).
Comparison ref: `main`, branch-cut commit `c8926756841cfc991d98a6e638c89e18953423a7`.

```text
git diff main --stat -- agents contracts kernel orchestration scripts infra .claude surfaces/dashboard/github_builds.py surfaces/dashboard/github_tree_diff.py surfaces/context.py surfaces/queries surfaces/tests/test_github_builds.py surfaces/tests/test_github_build_tag_guards.py surfaces/tests/test_github_build_tag_ancestry.py surfaces/tests/test_github_builds_env.py pyproject.toml uv.lock docs/STATE.md docs/work-queue.md docs/design-log.md
(stdout empty)
Exit code: 0
```

No other production file changed. The whole production diff is pasted here:

```diff
diff --git a/surfaces/dashboard/github_tag_builds.py b/surfaces/dashboard/github_tag_builds.py
index 4bf113f6..0167945f 100644
--- a/surfaces/dashboard/github_tag_builds.py
+++ b/surfaces/dashboard/github_tag_builds.py
@@ -1,7 +1,7 @@
 """Select GitHub image builds whose logs published a requested tag.

 Agent: surfaces
-Role: filter successful image workflow evidence by published Docker tag.
+Role: filter successful image workflow evidence by Docker tag across every attempt.
 External I/O: none directly; uses the injected reader's GitHub helpers.
 """

@@ -40,7 +40,7 @@ def image_builds_for_tag(
         for row in runs
         for build in (reader._build_from_run(row),)
         if clean_sha is None or _run_commit_is_on_main(reader, row, build.git_sha)
-        if run_log_mentions_tag(reader, build.run_id, clean_tag)
+        if run_log_mentions_tag(reader, build.run_id, clean_tag, _attempts(row))
     )
     if not matches and clean_sha is not None:
         return ()
@@ -51,13 +51,25 @@ def image_builds_for_tag(
     return matches


-def run_log_mentions_tag(reader: GitHubActionsReader, run_id: int, tag: str) -> bool:
-    """Return whether any workflow log names the requested image tag."""
-    url = (
-        f"https://api.github.com/repos/{reader._repository}/actions/runs/{run_id}/logs"
-    )
-    raw = reader._read_bytes(url)
+def run_log_mentions_tag(
+    reader: GitHubActionsReader, run_id: int, tag: str, attempts: int = 1
+) -> bool:
+    """Return whether any attempt's workflow log names the requested image tag.
+
+    GitHub's log archive for a run is its latest attempt's, and after a re-run of
+    the failed jobs that is those jobs' logs alone (DL-278). The latest is read
+    first, then each earlier attempt, newest first, until one names the tag.
+    """
+    base = f"https://api.github.com/repos/{reader._repository}/actions/runs/{run_id}"
     marker = f"trading-agents-master:{tag}".encode()
+    urls = (
+        f"{base}/logs",
+        *(f"{base}/attempts/{number}/logs" for number in range(attempts - 1, 0, -1)),
+    )
+    return any(_archive_names_tag(reader._read_bytes(url), marker) for url in urls)
+
+
+def _archive_names_tag(raw: bytes, marker: bytes) -> bool:
     try:
         with ZipFile(BytesIO(raw)) as archive:
             return any(
@@ -68,6 +80,14 @@ def run_log_mentions_tag(reader: GitHubActionsReader, run_id: int, tag: str) ->
         raise GitHubReadError("GitHub build log response was incomplete") from None


+def _attempts(row: dict[str, object]) -> int:
+    """How many attempts the run has had; a row that does not say has had one."""
+    attempts = row.get("run_attempt", 1)
+    if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 1:
+        raise GitHubReadError("GitHub build response was incomplete")
+    return attempts
+
+
 def _run_commit_is_on_main(
     reader: GitHubActionsReader, row: dict[str, object], git_sha: str
 ) -> bool:
```

No existing test changed. Only these two new files appear:

```text
git diff main --stat -- surfaces/tests orchestration/tests
surfaces/tests/github_build_attempts_helpers.py  |  91 +++++++++++++++
 surfaces/tests/test_github_build_tag_attempts.py | 135 +++++++++++++++++++++++
 2 files changed, 226 insertions(+)
git diff main --name-status -- surfaces/tests orchestration/tests
A	surfaces/tests/github_build_attempts_helpers.py
A	surfaces/tests/test_github_build_tag_attempts.py
```

**Law cycle:** old **LOCKED v1.5**, new **LOCKED v1.6**, both test-plan
header versions v1.6; one new clause after `SRF-DEP-03`, one changelog entry.
`SRF-DEP-04`, quoted as written:

```text
- **SRF-DEP-04** — The GitHub reader counts a successful image-build run as evidence that a tag
  was published only when one of the run's logs names the master image under that tag as a
  complete tag (`trading-agents-master:<tag>`; a longer tag that begins with it proves nothing).
  **Every attempt of the run is evidence**: the latest attempt's log archive is read first, then
  each earlier attempt's, newest first, until one names the tag, because after a re-run the run's
  own archive holds the re-run jobs alone. With a commit given, a run counts only when that
  commit is on `main`'s history, and a run that does not count is not read. An archive, a
  comparison or an attempt count that cannot be read is an error, never an absent tag; a row
  that names no attempt count has had one attempt. *(DRIFT-111, S267, DL-288.)*
```

Its test-plan row, quoted:

```text
| SRF-DEP-04 | A successful image-build run proves a published master-image tag only from a complete-tag match in a log; a longer tag that begins with the requested tag proves nothing. Read the latest archive first, then earlier attempts newest first until a match; rerun archives hold only rerun jobs. With a commit given, require main history before log reads. Unreadable archives, comparisons or attempt counts are errors, never absent tags; an omitted count means one attempt. | `surfaces/tests/test_github_build_tag_attempts.py::test_t1_earlier_attempt_proves_tag_and_records_deploy`; `surfaces/tests/test_github_build_tag_attempts.py::test_t2_stops_at_first_matching_attempt`; `surfaces/tests/test_github_build_tag_attempts.py::test_t3_no_attempt_names_tag_reads_all_newest_first`; `surfaces/tests/test_github_build_tag_attempts.py::test_t4_one_or_omitted_attempt_count_reads_latest_once`; `surfaces/tests/test_github_build_tag_attempts.py::test_t5_earlier_attempt_requires_the_complete_tag`; `surfaces/tests/test_github_build_tag_attempts.py::test_t6_unreadable_earlier_archive_is_a_sanitised_error`; `surfaces/tests/test_github_build_tag_attempts.py::test_t7_invalid_attempt_count_refuses_before_log_reads`; `surfaces/tests/test_github_build_tag_attempts.py::test_t8_off_main_run_is_rejected_before_any_archive_read` | 🟩 |
```

DRIFT-111's status cell, quoted:

```text
**CORRECTED (S267 / DL-288, surfaces laws v1.6, 2026-10-11).** New `SRF-DEP-04` states complete-tag proof from every attempt of a successful run, latest first and earlier attempts newest first until a match; main history and sanitised errors remain required, and absent attempt counts default to one. Proven by T1-T8 in `surfaces/tests/test_github_build_tag_attempts.py` (16 cases), including an in-memory verified deploy from the earlier attempt. No live or remote proof claimed.
```

Both rollup lines, quoted:

```text
docs/laws/ledger.md
| surfaces | ✅ v1.6 (LOCKED) | 31 / 38 | 🟨 partial — **31 of 38 clauses proven**; S267 (DL-288) adds and proves `SRF-DEP-04`: complete-tag evidence from every attempt of a successful image-build run, latest first and earlier attempts newest first, with main-history and unreadable-evidence guards; DRIFT-111 corrected; before that S263 (DL-284) amends and re-proves `SRF-DEP-03` for model-family disconnection and its start-up reason; before that S262 (DL-282) adds and proves `SRF-DEP-03`: dashboard chat binds only through its selected provider and disconnects for absent keys, unknown providers and either vendor configuration error; DRIFT-105 corrected; before that S251 narrows `SRF-OUT-03` to model-composed answers and names the quick asks as graph reads that write no audit fact (DRIFT-078), count unchanged; after S236 adds and proves `SRF-OUT-08` (the unattended vital and the `scorecard` answer: G1, G3 and two clocks from the acceptance gate's verdict and the records human actions leave) and lists `scorecard` in `SRF-TRG-02`; DRIFT-078 is filed for `SRF-OUT-03`'s silence on the quick asks. S228 added and proved `SRF-OUT-07` (28 of 35); S229 authored the book (27 of 34). Covers dashboard, CLI, MCP, chat and operator-intent write boundaries; selected-run scoping cites DRIFT-022 as already corrected. |

docs/laws/INDEX.md
| surfaces | ✅ LOCKED v1.6 (S267, S263, S262, S251, S236, S229, S228) | 31 / 38 | S267 (DL-288) adds and proves `SRF-DEP-04`: complete-tag evidence from every attempt of a successful image-build run, latest first and earlier attempts newest first, with main-history and unreadable-evidence guards; DRIFT-111 corrected; before that S263 (DL-284) amends and re-proves `SRF-DEP-03` for model-family disconnection and its start-up reason; before that S262 (DL-282) adds and proves `SRF-DEP-03`: dashboard chat binds only through its selected provider and disconnects for absent keys, unknown providers and either vendor configuration error; DRIFT-105 corrected; before that S251 narrows `SRF-OUT-03` (quick asks write no audit fact; DRIFT-078); Component book under `surfaces/laws/`; dashboard, CLI, MCP, chat and operator-intent write boundaries; S236 adds and proves `SRF-OUT-08` (the unattended scorecard) and the `scorecard` tool, and files DRIFT-078; selected-run scoping cites corrected DRIFT-022 |
```

**Law gate:** `uv run python scripts/check_law_coverage.py`, exit **0**,
stdout empty (`law-green.txt`). Its initial derivation output, before
updating the rollups, establishes the count:

```text
[FAIL] docs/laws/ledger.md:53: surfaces claims 30 / 37; derived 31 / 38
[FAIL] docs/laws/INDEX.md:55: surfaces claims 30 / 37; derived 31 / 38
Exit code: 1 (rollup mismatch, subsequently corrected)
```

Every test cited by that row was independently resolved from its file and
docstring, beyond the gate's at-least-one-citation rule:

```text
surfaces/tests/test_github_build_tag_attempts.py::test_t1_earlier_attempt_proves_tag_and_records_deploy: resolved; docstring cites SRF-DEP-04
surfaces/tests/test_github_build_tag_attempts.py::test_t2_stops_at_first_matching_attempt: resolved; docstring cites SRF-DEP-04
surfaces/tests/test_github_build_tag_attempts.py::test_t3_no_attempt_names_tag_reads_all_newest_first: resolved; docstring cites SRF-DEP-04
surfaces/tests/test_github_build_tag_attempts.py::test_t4_one_or_omitted_attempt_count_reads_latest_once: resolved; docstring cites SRF-DEP-04
surfaces/tests/test_github_build_tag_attempts.py::test_t5_earlier_attempt_requires_the_complete_tag: resolved; docstring cites SRF-DEP-04
surfaces/tests/test_github_build_tag_attempts.py::test_t6_unreadable_earlier_archive_is_a_sanitised_error: resolved; docstring cites SRF-DEP-04
surfaces/tests/test_github_build_tag_attempts.py::test_t7_invalid_attempt_count_refuses_before_log_reads: resolved; docstring cites SRF-DEP-04
surfaces/tests/test_github_build_tag_attempts.py::test_t8_off_main_run_is_rejected_before_any_archive_read: resolved; docstring cites SRF-DEP-04
8/8 row citations resolved independently; no dead or ambiguous citation
Exit code: 0
```

---

## Return notes

- Scope held: only the named production reader changed; no existing test,
  contract, kernel, agent, orchestration, infrastructure or `.claude/` file
  changed. `docs/STATE.md`, `docs/work-queue.md`, `docs/design-log.md`,
  `pyproject.toml` and `uv.lock` are untouched. The planner bumps at merge.
- No disagreement with the laws or D1-D6. The added clause precedes Python
  edits, as conventions section 7 requires; its remaining law bookkeeping
  follows the passing tests. No DL-288 amendment.
- Counts clarified: T2 is parametrised, so the plan produces 16 cases rather
  than the prototype's 15. The production module measures 114 lines rather
  than the Appendix's 115; the final formatted file is the quoted diff.
- A complete local CI gate is still owed: network-enabled dependency audit,
  then the planner's version bump and exact-HEAD remote gates before merge.
  The temporary audit guard is outside git and must not be used to claim a
  green gate. All other 14 local steps passed; the last two ran separately.
- The slow refusal fallback remains unchanged. F1 is a read-only GitHub
  check assigned to the planner after merge; no live graph record is proven.

- CI output includes historical test counts from the sprint-status step;
  the actual pytest summary is the banner reporting 4,662 passed and
  8 skipped. The closeout extractor was corrected before commit.
- Blank context lines in the quoted diff have trailing spaces trimmed
  for the whitespace hook; the exact raw diff is `production-diff.txt`
  beside the CI log. No content line of the diff was removed.

---

## Planner's review at the merge — 2026-10-11

Re-measured by the planner in `../ta-s267` at the builder's commit `3f4dde1c`, not taken from the
handback.

- **Scope.** The checklist's scope command against the commit the branch was cut from
  (`c8926756`, which was `main` when the review began) prints nothing: no agent, contract, kernel
  or orchestration file, no other reader module, no existing test, no tracker, no version file.
  Ten files changed: one production module edited, two test files added, the two surfaces law
  files, the three shared law files, this file and its README row. Every one is LF.
- **The code is the measured prototype in every line of code.** The file's blob id is not the
  prototype's (`0167945f` against `6768b878`): the two differ in the module docstring's `Role:`
  line alone, one line where the prototype had two, so the module is 114 lines and not 115.
- **Guards.** The planner's 15 breaks, one at a time against the builder's tests, each restored
  and the file's hash checked after the last: **15 went red, none survived, none failed to
  apply.**
- **The tests, read.** Eight functions, 16 cases, each citing `SRF-DEP-04`. The fake serves a
  different archive at each path and keeps the order they were asked for, and every test asserts
  that order. T1 records the deploy on an in-memory graph. T2 plants an assertion error in the
  attempt that must not be read.
- **No existing test changed:** between `c8926756` and `3f4dde1c` the two test folders show two
  added files and nothing else.
- **The law cycle.** Surfaces law book v1.5 to v1.6; `SRF-DEP-04` is the spec's clause word for
  word (compared by script); changelog; 31 / 38 on both rollup lines, which is what the gate
  derives; DRIFT-111 CORRECTED. **Each of the eight tests the row cited was resolved by hand:**
  every one is a live function whose docstring names the clause.
- **One change made by the planner on the branch, a gap in the planner's own test plan.** The
  clause says *an archive, a comparison or an attempt count that cannot be read is an error*, and
  T1 to T8 plant the archive and the count, never the comparison. That behaviour was covered
  only by an older test that cites no clause, and the builder's fake had a branch for it that no
  test reached. **T9**, `test_t9_unreadable_comparison_is_an_error_and_no_archive_is_read`
  (three cases: a comparison GitHub refuses, one with no `ahead_by`, one whose `ahead_by` is a
  boolean), raises the reader's error with no host in its message and reads no archive, while an
  earlier attempt names the tag. Five breaks of the comparison were planted against T9 alone and
  **five went red**. The row now cites nine tests; the test file is 152 lines.
- **Seen and accepted.** The handback's `make ci` stopped at the dependency audit, which needs the
  network the builder does not have; the planner's Windows run is the proof. The plan's 15 cases
  are 16 because T2's two cases are parametrised apart. The builder planted four breaks beyond
  the fifteen asked for.
- **`main` moved during the review:** sprint 266 was merged (`b1580076`, `0.125.04`). It was
  merged into this branch; the two sprints met in one file, `docs/sprints/README.md`, on
  neighbouring rows, resolved row by row (sprint 266's row is `main`'s, byte for byte). The law
  gate reads exit 0 on the merged tree.
- **Version.** PATCH, `0.125.04` to `0.125.05`; `uv lock` changed the version line alone (180
  packages).

**Written at the merge, before the gate — what was still owed then:** the planner's Windows
`make ci`, the remote gate and the CodeQL set-diff for the commit that holds this block; then F1
(the reader on the real run of 2026-10-08, read-only on GitHub, at no cost); then the deploy
skill's line on re-running a failed job.

---

## Appendix — the planner's prototype

Measured in `../ta-s267` at `b991d39e` on 2026-10-11 and then removed, so the worktree is clean.
`ruff`, `mypy` and the header step passed on it, and the module is 115 lines.

**`surfaces/dashboard/github_tag_builds.py`, the whole change.** The call in `image_builds_for_tag`
becomes `if run_log_mentions_tag(reader, build.run_id, clean_tag, _attempts(row))`, the module
docstring's `Role:` says every attempt is read, and `run_log_mentions_tag` is replaced by:

```python
def run_log_mentions_tag(
    reader: GitHubActionsReader, run_id: int, tag: str, attempts: int = 1
) -> bool:
    """Return whether any attempt's workflow log names the requested image tag.

    GitHub's log archive for a run is its latest attempt's, and after a re-run of
    the failed jobs that is those jobs' logs alone (DL-278). The latest is read
    first, then each earlier attempt, newest first, until one names the tag.
    """
    base = f"https://api.github.com/repos/{reader._repository}/actions/runs/{run_id}"
    marker = f"trading-agents-master:{tag}".encode()
    urls = (
        f"{base}/logs",
        *(f"{base}/attempts/{number}/logs" for number in range(attempts - 1, 0, -1)),
    )
    return any(_archive_names_tag(reader._read_bytes(url), marker) for url in urls)


def _archive_names_tag(raw: bytes, marker: bytes) -> bool:
    try:
        with ZipFile(BytesIO(raw)) as archive:
            return any(
                _contains_complete_tag(archive.read(name), marker)
                for name in archive.namelist()
            )
    except BadZipFile:
        raise GitHubReadError("GitHub build log response was incomplete") from None


def _attempts(row: dict[str, object]) -> int:
    """How many attempts the run has had; a row that does not say has had one."""
    attempts = row.get("run_attempt", 1)
    if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 1:
        raise GitHubReadError("GitHub build response was incomplete")
    return attempts
```
