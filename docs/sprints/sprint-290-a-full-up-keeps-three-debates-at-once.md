<!-- Agent: planning | Role: sprint handover -->
# Sprint 290 — a full `up` keeps three debates at once and the manager's 240-second wait

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-290-a-full-up-keeps-three-debates-at-once`
**Status:** BUILT
**Version:** *next available PATCH at merge* (the prototype measured `0.131.07`)
**Effort:** S
**Decisions:** [DL-325](../design-log.md) (this sprint's six decisions, made and measured) · [DL-277](../design-log.md) amendment 2 (the operator's three debates at once, live since 2026-10-09) · [DL-274](../design-log.md) D4 (the manager's wait of 240 seconds, live since 2026-10-08) · [work-queue 113](../work-queue.md)

> **Why this bump kind.** No new capability: the fleet already debates three orders at once and the
> manager already waits 240 seconds. The pack still says 1 and 120, so a full `up` would put both
> back. The pack is the configuration every deploy applies and a fidelity decision path, so the
> change is a fix with a version of its own: a PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 4 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/deliberator/laws/laws.md` | The deliberator's **locked constitution** | **LOCKED. Read-only.** This sprint changes no row and no clause of it |
| `agents/deliberator/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read only. No row changes |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Read only. No row changes |

Binding sections here: the deliberator's **`PARAM`** table (the rows `debate_concurrency` and
`request_timeout_seconds`) and **`DLIB-DEP-04`**.

### The rule

1. **Before writing code**, read `agents/deliberator/laws/laws.md` and its `test-plan.md`, whole.
2. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
3. **Answer the law-cycle question below** in the Law reading record.
4. **Write the Law reading record** (bottom of this file) **before** your first change.
5. **If a law contradicts this spec, STOP and report.**
6. A test for behaviour a clause governs cites the clause ID in its docstring. *[read 2026-11-17]*
   no clause governs the value an app's pack entry holds: the `PARAM` rows state each setting's
   code default and bounds, and both new values are inside them (3 in 1 to 25; 240 in 1 to 300).
   The new tests cite the decisions (DL-325, DL-277, DL-274). If your reading finds a clause that
   governs a pack value, cite it and say so in the Return notes.

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**No.** No file in `contracts/` changes, no agent's code changes, and no code default changes, so
no `PARAM` row moves and no law file is edited. The pack is trading-pack data that the deploy
applies. **No law cycle is owed.** If you find yourself editing a law file, stop and report.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `orchestration/packs/trading_tunables.json` (the `deliberator-manager` entry and `_measured`) | `agents/deliberator/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `PARAM`: `debate_concurrency` is an int from 1 to 25, `request_timeout_seconds` a float from 1 to 300; `DLIB-DEP-04` |
| `tests/test_pack_debate_lanes.py` (new) | `docs/laws/conventions.md` | Module header; a test of clause-governed behaviour cites its clause (none here) |

⚠️ **The invariant this sprint must not break: after it, a full `up` changes nothing on the three
deliberator apps.** The pack must state exactly what the fleet holds live today (Appendix A). If
your change would send any other value to any app, stop and report.

---

## Goal

At merge, `orchestration/packs/trading_tunables.json` declares on `deliberator-manager` three
debates at once and a wait of 240 seconds, so the deploy script's own `Up` sends the manager those
two values and gives each debater three replicas in the nightly window: the state the fleet has
run since 2026-10-09. A test fixes each number and the one condition more than one lane rests on.

## Why (context)

Three debates at once has been live on the fleet since 2026-10-09 on the operator's word, and the
manager's wait of 240 seconds since 2026-10-08. Both were set by hand on the live apps, because the
pack is a fidelity decision path and an edit would have restarted the clean-session count. The count
read PASS on 2026-10-27, so nothing holds the edit back any more. Until it is made, any full `up`
puts one debate at a time and the 120-second wait back under a green `[OK]`: on 2026-10-11 a
narrower change already cost the debaters their three replicas for six nights before it was seen
([DL-277](../design-log.md) amendment 3). One debate at a time does not fit a busy night into
execution's 1,800-second wait, and then no buy of that night is placed
([DL-274](../design-log.md)).

### Measured, 2026-11-17 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| What the three apps hold live | manager: `DELIBERATOR_DEBATE_CONCURRENCY=3`, `DELIBERATOR_REQUEST_TIMEOUT_SECONDS=240`, 1 replica; each debater: wait 120, max 3 replicas, 3 in the nightly window | *[measured 2026-11-17 06:34 UTC]* `az containerapp show` on each app, read-only; the planner's `live_lanes_2026-11-17.txt` (Appendix A) |
| What a full `up` of `main` (`68273b16`) sends | manager: 1 and 120; each debater: max 1 replica, 1 in the window | *[measured]* the deploy script's own `Up` run with every `az` call and credential a stand-in; 4 of 20 printed lines differ from the live read |
| What a full `up` of the prototype sends | the live state | *[measured]* the same runner on the prototype: 20 of 20 lines equal the live read |
| The env guard does not catch a changed value | it compares names only | *[read, whole function]* `Assert-EnvPreserved` in `infra/deploy-agents.ps1` compares the live env names with the planned names; a value is never read |
| Who reads the wait | the manager only | *[read]* `agents/deliberator/entrypoint.py::build_manager` passes `request_timeout_seconds` to the peer client; no debater path reads it |
| The debate record since three at once went live | 27 nightly records from 2026-10-09 to 2026-11-16: 0 orders failed open, 0 orphaned replies; 6 nights with more than one debated order; the largest 7 orders in 662 seconds (2026-10-26) | *[measured]* the live graph, read-only: every `DeliberationRun` since 2026-10-09 with its PM run (`wq113pack_nights.py`) |
| One debate on its own | 217 to 347 seconds from the PM run to the record, 12 nights | *[measured]* the same read; seven of them one after another is 1,519 to 2,429 seconds against execution's 1,800 |
| Replicas each debater ran, 2026-10-12 to 2026-10-16 | 1, not 3 | *[carried from DL-277 amendment 3, not re-measured]* those five records are inside the 27 |
| The largest night on record | 18 approved buys (2026-08-08 and 2026-08-10); 7 since 2026-10-09 | *[measured]* 118 PM runs on the live graph (`wq113_buys.py`) |
| Requests a replica takes a pass | 1, the kernel's default; no pack entry and no line of the deploy script sets it | *[measured]* `AzureServiceBusSettings.model_fields["receive_max_messages"].default`; a search of both files for `RECEIVE_MAX_MESSAGES` |
| How many orders three lanes fit into 1,800 seconds | about 18 | *[ASSUMED — not measured]* 1,800 divided by the 95 seconds an order of the one seven-order night; no night since 2026-10-09 has debated more than 7 |
| The vendor's rate limit above three calls in flight a debater | unknown | *[ASSUMED — not measured]* DL-277 amendment 1 met no limit at three; four was never run on the fleet |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first.** A new file `tests/test_pack_debate_lanes.py` with the six tests of
   the Test plan, under the names given. Four fail on the unchanged tree and two pass, by design.
2. **The pack.** Apply Appendix B to `orchestration/packs/trading_tunables.json`: two values on
   `deliberator-manager` and one amendment appended to `_measured`. Nothing else in the file.
3. **The version.** Appendix B's two one-line changes to `pyproject.toml` and `uv.lock`.

### Out of scope (do NOT build this sprint)

- **`infra/deploy-agents.ps1`.** It already derives each debater's replicas from the pack's lane
  count, and an existing test holds that. It does not change.
- **The three `DELIBERATOR_LLM_PROVIDER` lines of the pack** (work-queue 109). `Up` already sends
  `openai` from the LLM pack whatever these lines say (Appendix A). Taking them out is its own
  sprint.
- **The five-minute message lock on the two debater subscriptions.** It is a Service Bus setting
  the deploy script does not set at all; a separate change.
- **The two debaters' wait.** It stays 120: it bounds nothing, and it is what the apps hold.
- **Any code default, any law file, any existing test.**
- **No ADR reversal.** An ADR is reversed by a new ADR, never by a sprint.

### The road not taken (LAW-06)

- **The lanes alone, the wait in a later sprint.** Rejected: both are the same file, the same
  deploy and the same restart of the fidelity count; and a full `up` that kept three lanes but put
  120 seconds back would cut off the slow turns (about 190 seconds at the output cap,
  [DL-274](../design-log.md) D3).
- **No fixed number in a test, as `test_deploy_tunables_pack.py` argues.** Rejected for these two
  values: with the number free, a pack that says 1 again passes every test, and that is the defect.
  The older test stays as it is; the new file says why it fixes the number.
- **Bounds in place of the number** (at least 2 by the measured night, at most 3 by what the fleet
  has run). Rejected: 2 would pass.
- **A capacity test** (lanes times execution's wait covers the largest night). Rejected: no honest
  constant exists. The largest night on record (18 buys) times the slowest single debate (347
  seconds) exceeds three lanes of 1,800 seconds, while the one measured seven-order night ran at
  95 seconds an order.
- **Four lanes, the code's default.** Rejected: the fleet has run three, and the vendor's limit
  above three calls in flight is not measured.
- **Passing the values to `up` as parameters.** Rejected: the script has none for them, and the
  first `up` that forgets a parameter moves the value (as in [DL-295](../design-log.md)).

---

## The design decisions — made, and recorded in DL-325

**Nothing is left for the builder to decide.** Do not add a design-log entry.

1. **D1 — the pack declares three lanes on the manager**, and so three replicas of each debater.
2. **D2 — the pack declares the manager's wait of 240 seconds in the same edit**; the debaters keep 120.
3. **D3 — a test fixes each number, and one test fixes the condition lanes above one rest on**
   (each replica takes one request a pass); the older test that leaves the number free is untouched.
4. **D4 — the pack's own note records both moves** and says which older sentence it supersedes.
5. **D5 — PATCH; the version lines are carried in this spec** and `uv lock` is not run (Traps).
6. **D6 — no deploy.** The fleet already holds the values. The fidelity count restarts at the first
   deploy that carries this commit. F2 is read at the next full `up`.

---

## Blast radius — measured 2026-11-17

| What | Detail |
| --- | --- |
| Files changed | `orchestration/packs/trading_tunables.json` (47 lines), `pyproject.toml`, `uv.lock` (one line each), `tests/test_pack_debate_lanes.py` (new, 99 lines on the prototype), this spec, `docs/sprints/README.md` |
| Agents affected | none in code. At the next full `up`: `deliberator-manager`, `deliberator-proponent`, `deliberator-opponent` receive what they already hold |
| Contract change? | no |
| Graph vocabulary change? | no |
| New env keys / tunables | none; two existing keys change value in the pack |
| Deploy implication | none at merge. The pack is a fidelity decision path (`scripts/replay_fidelity_git.py`, `DECISION_PATHS`): the first deploy that carries this commit restarts the clean-session count |
| Rollback | revert the commit. Nothing live changes at merge, so nothing live is undone. After a full `up` from this commit a rollback `up` from an older commit puts 1 lane and 120 seconds back: set both by hand again, as today |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Plant the failing tests first** (Test plan) and watch them on the unchanged tree. Paste the
   output: 4 failed, 2 passed on the planner's prototype.
3. **Apply Appendix B**, exactly, and check the three blob ids it gives.
4. **Prove the guards can fail (DL-70):** the fifteen breaks of Appendix C, one at a time, each red
   on the test named for it, each restored before the next.
5. **`make ci` green**, every step of the `ci:` target (count them from the `Makefile`),
   **redirected to a file, never piped**.
6. **Fill the handback sections** at the bottom of this file.

---

## Test plan

All six in the new file `tests/test_pack_debate_lanes.py`, **under exactly these names** (the
planner's break script judges by them). The file reads the pack and the deploy script as text and
JSON, as `tests/test_deploy_tunables_pack.py` does; it runs no PowerShell.

| # | Test | On the unchanged tree | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 `test_a_full_up_keeps_three_debates_at_once` | fails | the manager's `DELIBERATOR_DEBATE_CONCURRENCY` in the pack is the string `"3"` |
| A2 | 🪤 `test_only_the_manager_declares_the_lanes` | passes | the apps of the pack that carry that key are exactly `["deliberator-manager"]` |
| A3 | 🎯 `test_a_full_up_keeps_the_managers_wait_of_240_seconds` | fails | the manager's `DELIBERATOR_REQUEST_TIMEOUT_SECONDS` in the pack is the string `"240"` |
| A4 | 🪤 `test_the_debaters_keep_their_wait_of_120_seconds` | passes | each of the two debaters' `DELIBERATOR_REQUEST_TIMEOUT_SECONDS` is `"120"` |
| A5 | `test_more_than_one_lane_takes_one_request_a_pass` | fails (on its first assertion: one lane) | the pack's lanes are above 1; the default of `AzureServiceBusSettings.model_fields["receive_max_messages"]` is 1; no app of the pack has a key containing `RECEIVE_MAX_MESSAGES`; the deploy script's text does not contain `RECEIVE_MAX_MESSAGES` |
| A6 | `test_the_packs_note_records_both_moves` | fails | `_measured` contains `DELIBERATOR_DEBATE_CONCURRENCY 1->3`, `DELIBERATOR_REQUEST_TIMEOUT_SECONDS 120->240` and `DL-325` |

No existing test changes, and none fails on the prototype.

---

## Success factors

- [x] The pack's `deliberator-manager` entry holds `"3"` and `"240"`; the file's blob id is Appendix B's.
- [x] No other app's entry and no other key changed: `git diff` of the pack shows three changed lines.
- [x] The six tests exist under the names given and pass; A1, A3, A5 and A6 were seen failing first.
- [x] No existing test, no law file, no script and no code file changed.
- [x] The law-cycle question is answered No, with the reason, in the Law reading record.
- [x] Each of the fifteen breaks was planted, seen red on its named test, and restored.
- [x] Every touched module is under 200 lines.
- [x] `make ci` exit 0, 100.00 % coverage; a step the sandbox cannot run is named "not done".

---

## Traps

🪤 **Do not run `uv lock`, with or without `--offline`.** *[measured 2026-11-17, uv 0.8.14]*
Offline it also moves `virtualenv` from 21.14.13 back to 21.14.12; with a network it rewrites 54
lines, because the lock was last written by a newer `uv`. The lock changes in **one line**, given in
Appendix B, and `uv lock --check` accepts it.

🪤 **`_measured` is one line of about 3,900 characters.** Do not retype it. Apply Appendix B's
block with `git apply` and compare the blob id; a single different character changes it.

🪤 **Two of the six tests pass before the change, and that is right.** A2 and A4 are the guards
that the edit lands on the manager and nowhere else. Do not strengthen them until they fail.

🪤 **A5 fails on the unchanged tree for the lane count, not for the requests a pass.** Its other
three assertions already hold; break B8, B9 and B10 are what show they can fail.

🪤 **`tests/test_deploy_tunables_pack.py` says in a docstring that the number is left free on
purpose.** It is not this sprint's to edit. The new file's header says why these two numbers are
fixed.

🪤 **The values are strings.** The pack holds `"3"` and `"240"`, as container env values are.

🪤 **A green suite proves little here:** no existing test fails with the old values or the new.
Only the six new tests and the breaks show the change.

🪤 **The lint step reads test files too.** *[met on the prototype]* a line over 88 characters fails
it, and a module constant whose name contains `PASS` holding a text value is read as a hardcoded
password (`S105`): name the constant for the requests-a-pass key something else. No `# noqa`.

🪤 **Paste step lines and verdicts into the Closeout, not the whole `make ci` log.**

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150), tests included. No `# noqa`.
  📌 Prototype size: `tests/test_pack_debate_lanes.py` **99**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers in code. The two numbers of this sprint are pack values and their tests.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it, both from Appendix B.
- Secrets never through the worktree. The worktree has **no `.env`** and this sprint needs none.
  **State which tree you ran in.**

---

## Sequencing after merge (the planner's)

1. The planner's own `make ci` (the dependency audit needs a network), the branch pushed,
   **`make gate-ran` exits 0** from the proving worktree, its SHA checked against `git rev-parse HEAD`.
2. The planner re-measures: the three blobs against Appendix B; the planner's own test file run in
   place of the builder's; the break script against the builder's tests alone (15 breaks); the open
   CodeQL alerts set-diffed against `main`'s.
3. Merge to `main`, tag. **Post-merge CodeQL** checked on `main`.
4. **F1, at no cost and read-only:** on merged `main` the script's own `Up`, every call a stand-in,
   prints for the three deliberator apps what the live apps hold, read the same hour: 20 of 20
   lines (Appendix A is that read on the prototype).
5. **No deploy.** STATE's two standing lines (the wait, the lanes) and work-queue 113 are closed by
   the planner; the fidelity count's restart is recorded at the first deploy that carries the commit.
6. **F2, owed at the next full `up`:** the three apps read back equal to Appendix A, and the first
   night after it with more than one debated buy shows no order failed open and no orphaned reply.

---

## Handover — paste this to Codex

```text
You are building Sprint 290 in the worktree ../ta-s290, on the branch
sprint-290-a-full-up-keeps-three-debates-at-once. Never work on main.

Read docs/sprints/sprint-290-a-full-up-keeps-three-debates-at-once.md, whole, before anything
else. It is the spec, and its bottom sections are your handback. Every decision is made; the
change is three lines of one JSON file, two version lines, and one new test file.

In order:
1. Read agents/deliberator/laws/laws.md and test-plan.md, docs/laws/conventions.md and
   docs/laws/drift-register.md. Fill the Law reading record in the spec BEFORE any change. The
   law-cycle answer is No; if you find yourself editing a law file, stop.
2. Write the six tests of the Test plan in the new file tests/test_pack_debate_lanes.py, under
   exactly the names given, with a module docstring that declares Agent, Role and External I/O.
   Run
     uv run --no-sync pytest tests/test_pack_debate_lanes.py --no-cov -q -p no:cacheprovider
   on the unchanged tree and paste the output into the Closeout. Expected: 4 failed, 2 passed
   (A2 and A4 pass before the change, by design).
3. Apply Appendix B: save its diff block to a file outside the repository's tracked files and
   run git apply on it. Then git hash-object on the three files must print the three blob ids
   Appendix B gives. Do NOT run uv lock in any form.
4. Run the same pytest command again: 6 passed. Run
     uv run --no-sync pytest tests/test_deploy_tunables_pack.py tests/test_pack_files.py --no-cov -q -p no:cacheprovider
   as well: no existing test may fail.
5. Plant the fifteen breaks of Appendix C one at a time. Each must go red on the test named for
   it. Restore each with git checkout of that file before the next (commit your work first, or
   keep a copy, so the restore returns your built file).
6. Run make ci redirected to a file and read the file. If a step cannot run in your sandbox (the
   dependency audit needs a network), say "not done" for that step and paste its lines.
7. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in this
   sprint's row of docs/sprints/README.md (the row's status cell must lead with BUILT). Commit
   on the branch if your sandbox lets you write the repository's git directory; if not, leave
   the tree uncommitted and say so.

DO NOT: run uv lock or uv sync; run infra/deploy-agents.ps1 or any az command; change
infra/deploy-agents.ps1, any file under agents/, kernel/, contracts/, orchestration/ other than
the pack, or any law file (the breaks of step 5 are restored, never kept); change any other
entry or key of the pack, or retype its _measured line; change any existing test; add a
design-log entry; edit docs/STATE.md, docs/work-queue.md or docs/design-log.md; add entries to
.secrets.baseline; use noqa; paste a whole make ci log into the spec; measure make ci through a
pipe.

Traps: _measured is one line of about 3,900 characters, so apply the diff and compare the blob
id; the values are the strings "3" and "240"; A5 fails before the change only on its first
assertion; an existing test's docstring says the lane number is left free on purpose and it is
not yours to edit; no existing test fails with the old values or the new, so a green suite
alone proves nothing; ruff reads test files (88 characters a line, and a constant named with
PASS holding text is flagged S105).

Two tiers of trouble. A wrong path, count or command in this spec whose intent is plain:
correct it, go on, and record it in the Return notes. A blob id that does not match after a
clean git apply, a law that contradicts the spec, an existing test that fails, or a break that
stays green: STOP and report. State anything not done as "not done" or "verified failing".
Never write a Result for work you have not done.

Handback checklist, each answered in the Closeout:
 1. Law reading record filled before the first change; law-cycle answer No with its reason.
 2. Red output of step 2 pasted (4 failed, 2 passed).
 3. The three blob ids after git apply, as printed.
 4. Green output of step 4 pasted (6 passed; the two existing files pass).
 5. git diff --stat against the base: exactly the pack, pyproject.toml, uv.lock, the new test
    file, this spec and docs/sprints/README.md.
 6. The fifteen breaks, one line each: the test that went red, and restored.
 7. The line count of tests/test_pack_debate_lanes.py.
 8. make ci: the file's path, the exit code, each step's verdict line, the pytest totals and
    coverage; every step not run named "not done".
 9. The tree the proofs ran in, and that it holds no .env.
10. Status BUILT in the spec and in the README row; committed or not, and the SHA if committed.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first change.
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
| Pack manager values and note | agents/deliberator/laws/laws.md and test-plan.md (whole); docs/laws/conventions.md and drift-register.md (whole), read 2026-11-17 before this first edit | PARAM bounds; DLIB-DEP-04; DLIB-IDM-04 for the one-request premise | Values fit bounds; cite DLIB-IDM-04 in A5; no law edit |
| New pack tests | docs/laws/conventions.md | Section 7 citations; DLIB-IDM-04 for A5 | Fixed pack values cite DL-325 / DL-277 / DL-274; A5 also cites the existing request guarantee |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No. No contracts, agent code, code defaults or PARAM rows change; only existing bounded pack values and their evidence change. No new agent guarantee and no law cycle owed.

**Contradictions found between a law and this spec:** None. DLIB-IDM-04 already governs the one-request premise; the pack values remain decisions rather than new guarantees.

**Laws found silent where a decision was needed:** No new decision needed. Exact pack values are fixed by DL-325, DL-277 and DL-274; PARAM declares defaults and bounds, not app pack values. DRIFT-041 deliberator records the operator value as pack data.

**Clauses that were ⬜ and are now proven:** None; this sprint adds pack guards, not a full new clause proof.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a_full_up_keeps_three_debates_at_once` | `tests/test_pack_debate_lanes.py` | PASS; red first | DL-325 / DL-277 |
| A2 | `test_only_the_manager_declares_the_lanes` | `tests/test_pack_debate_lanes.py` | PASS before and after | DL-325 |
| A3 | `test_a_full_up_keeps_the_managers_wait_of_240_seconds` | `tests/test_pack_debate_lanes.py` | PASS; red first | DL-325 / DL-274 |
| A4 | `test_the_debaters_keep_their_wait_of_120_seconds` | `tests/test_pack_debate_lanes.py` | PASS before and after | DL-325 |
| A5 | `test_more_than_one_lane_takes_one_request_a_pass` | `tests/test_pack_debate_lanes.py` | PASS; red first | DLIB-IDM-04 (configuration premise only); DL-325 |
| A6 | `test_the_packs_note_records_both_moves` | `tests/test_pack_debate_lanes.py` | PASS; red first | DL-325 |

**Tests added beyond the plan:** None.

---

## Closeout — evidence

**Status:** BUILT — all 16 local CI steps pass (exit 0), 100.00% coverage; 15 breaks red/restored; not pushed or merged.

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/Downloads/project/ta-s290`, branch `sprint-290-a-full-up-keeps-three-debates-at-once`; `Test-Path .env` printed `False`. Base: `3ff3d0a61bb82306e88fcd7dbfb0e7e6419ce2cf`.

**Result:** Appendix B applied with all three exact blobs. Six new tests pass after the expected 4-failed/2-passed red run; both existing files pass (90 tests). All 15 named mutation tests went red and were restored. All 16 local CI steps pass, exit 0, 5,333 passed / 9 skipped, 100.00% coverage. Remote proof, merge, deploy, F1 and F2 not done.

**Files changed:** exactly the six scoped files. `git diff --stat 3ff3d0a61bb82306e88fcd7dbfb0e7e6419ce2cf` (base to built tree):

```text
 docs/sprints/README.md                             |   2 +-
 ...nt-290-a-full-up-keeps-three-debates-at-once.md | 176 +++++++++++++++++----
 orchestration/packs/trading_tunables.json          |   6 +-
 pyproject.toml                                     |   2 +-
 tests/test_pack_debate_lanes.py                    |  70 ++++++++
 uv.lock                                            |   2 +-
 6 files changed, 219 insertions(+), 39 deletions(-)
```

**Design decisions:** recorded by the planner as [`DL-325`](../design-log.md); the builder adds none.

**Proof — the red run first:**

Command: `uv run --no-sync pytest tests/test_pack_debate_lanes.py --no-cov -q -p no:cacheprovider` (exit 1; pack unchanged).

```text
F.F.FF                                                                   [100%]
================================== FAILURES ===================================
_________________ test_a_full_up_keeps_three_debates_at_once __________________
tests\test_pack_debate_lanes.py:32: in test_a_full_up_keeps_three_debates_at_once
    assert _APPS["deliberator-manager"][_LANES] == "3"
E   AssertionError: assert '1' == '3'
E
E     - 3
E     + 1
____________ test_a_full_up_keeps_the_managers_wait_of_240_seconds ____________
tests\test_pack_debate_lanes.py:44: in test_a_full_up_keeps_the_managers_wait_of_240_seconds
    assert _APPS["deliberator-manager"][_WAIT] == "240"
E   AssertionError: assert '120' == '240'
E
E     - 240
E     + 120
______________ test_more_than_one_lane_takes_one_request_a_pass _______________
tests\test_pack_debate_lanes.py:59: in test_more_than_one_lane_takes_one_request_a_pass
    assert int(_APPS["deliberator-manager"][_LANES]) > 1
E   AssertionError: assert 1 > 1
E    +  where 1 = int('1')
___________________ test_the_packs_note_records_both_moves ____________________
tests\test_pack_debate_lanes.py:68: in test_the_packs_note_records_both_moves
    assert "DELIBERATOR_DEBATE_CONCURRENCY 1->3" in note
E   assert 'DELIBERATOR_DEBATE_CONCURRENCY 1->3' in "Snapshot of the live fleet read on 2026-08-14 from Azure Container Apps RG trading-agents. STAGED 2026-08-20: DELIBER...hich is DL-76's refusal rate measured on our own book. Operator chose this over closing the item as decided-by-design."
=========================== short test summary info ===========================
FAILED tests/test_pack_debate_lanes.py::test_a_full_up_keeps_three_debates_at_once
FAILED tests/test_pack_debate_lanes.py::test_a_full_up_keeps_the_managers_wait_of_240_seconds
FAILED tests/test_pack_debate_lanes.py::test_more_than_one_lane_takes_one_request_a_pass
FAILED tests/test_pack_debate_lanes.py::test_the_packs_note_records_both_moves
4 failed, 2 passed in 1.81s
```

**Proof — the green run:**

`uv run --no-sync pytest tests/test_pack_debate_lanes.py --no-cov -q -p no:cacheprovider` (exit 0):

```text
......                                                                   [100%]
6 passed in 1.35s
```

`uv run --no-sync pytest tests/test_deploy_tunables_pack.py tests/test_pack_files.py --no-cov -q -p no:cacheprovider` (exit 0):

```text
........................................................................ [ 80%]
..................                                                       [100%]
90 passed in 3.35s
```

**Blob ids after `git apply`:** `git hash-object orchestration/packs/trading_tunables.json pyproject.toml uv.lock` printed, in that order:

```text
d276a8600359172313654f3c4a5af01a475f5d25
5192763ac41793a1b86de964c08df997cb54f4bb
a0eca83dcccf706d5c06947c2627f0c0d2a1d930
```

**Guards planted:** one at a time; built pack saved outside the worktree and staged before planting, so `git checkout -- <file>` restored its built index contents. Kernel/script restored to HEAD. Byte comparison after every restore. Each named test run with `uv run --no-sync pytest <file>::<test> --no-cov -q -p no:cacheprovider`. Logs: `C:/Users/yury_/Downloads/project/s290-break-B1.txt` through `s290-break-B15.txt`.

- B1: tests/test_pack_debate_lanes.py::test_a_full_up_keeps_three_debates_at_once — red (exit 1), restored
- B2: tests/test_pack_debate_lanes.py::test_a_full_up_keeps_three_debates_at_once — red (exit 1), restored
- B3: tests/test_pack_debate_lanes.py::test_a_full_up_keeps_three_debates_at_once — red (exit 1), restored
- B4: tests/test_pack_debate_lanes.py::test_only_the_manager_declares_the_lanes — red (exit 1), restored
- B5: tests/test_pack_debate_lanes.py::test_a_full_up_keeps_the_managers_wait_of_240_seconds — red (exit 1), restored
- B6: tests/test_pack_debate_lanes.py::test_a_full_up_keeps_the_managers_wait_of_240_seconds — red (exit 1), restored
- B7: tests/test_pack_debate_lanes.py::test_the_debaters_keep_their_wait_of_120_seconds — red (exit 1), restored
- B8: tests/test_pack_debate_lanes.py::test_more_than_one_lane_takes_one_request_a_pass — red (exit 1), restored
- B9: tests/test_pack_debate_lanes.py::test_more_than_one_lane_takes_one_request_a_pass — red (exit 1), restored
- B10: tests/test_pack_debate_lanes.py::test_more_than_one_lane_takes_one_request_a_pass — red (exit 1), restored
- B11: tests/test_pack_debate_lanes.py::test_the_packs_note_records_both_moves — red (exit 1), restored
- B12: tests/test_pack_debate_lanes.py::test_the_packs_note_records_both_moves — red (exit 1), restored
- B13: tests/test_pack_debate_lanes.py::test_the_packs_note_records_both_moves — red (exit 1), restored
- B14: tests/test_deploy_tunables_pack.py::test_peer_replica_count_follows_the_pack_and_not_a_literal — red (exit 1), restored
- B15: tests/test_deploy_tunables_pack.py::test_peer_replica_count_follows_the_pack_and_not_a_literal — red (exit 1), restored

**Module line counts:** `tests/test_pack_debate_lanes.py`: 70 lines (under 200); pack: 47 lines.

**`make ci`:** `make ci > C:/Users/yury_/Downloads/project/s290-make-ci.txt 2>&1`, exit **0** (stored in `s290-make-ci.exit`). Ran in the named tree with `UV_NO_SYNC=1`, `UV_FROZEN=1`; no pipe. Read the redirected file. Counted **16** commands from the Makefile and log. No CI step is not done. Silent steps have no printed verdict; reaching the next command and final exit 0 proves their exit 0.

| Step | Command as printed | Verdict / output |
| --- | --- | --- |
| 1 | `uv run ruff check . --output-format=github` | PASS; silent success, next step ran |
| 2 | `uv run ruff format --check .` | PASS; `1845 files already formatted` |
| 3 | `uv run mypy kernel contracts agents orchestration surfaces` | PASS; `Success: no issues found in 1300 source files` |
| 4 | `uv run lint-imports` | PASS; `Contracts: 5 kept, 0 broken.` |
| 5 | `uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts` | PASS; exit 0 (existing WARN/LEGACY lines remain) |
| 6 | `uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts` | PASS; silent success, next step ran |
| 7 | `uv run python scripts/check_law_coverage.py` | PASS; silent success, next step ran |
| 8 | `uv run python scripts/check_param_law_sync.py` | PASS; exit 0 (existing envelope warnings remain) |
| 9 | `uv run python scripts/check_sprint_status.py` | PASS; `docs_seen=296 SPEC=10 BUILT=1 MERGED=285 UNMAPPED=0 MISSING=0` |
| 10 | `uv run python scripts/check_tracker_size.py` | PASS; exit 0 (README size warning at 94%, below limit) |
| 11 | `uv run python scripts/check_markdown_links.py` | PASS; silent success, next step ran |
| 12 | `uv run python scripts/check_version_scheme.py` | PASS; silent success, next step ran |
| 13 | `uv run pytest` | PASS; `5333 passed, 9 skipped, 2470 warnings in 503.53s (0:08:23)`; 100.00% coverage |
| 14 | `uv run python scripts/check_dependency_audit.py` | PASS; `No unaccepted vulnerabilities; 1 accepted advisory re-checked` |
| 15 | `uv run pre-commit run detect-secrets --all-files` | PASS; `Detect secrets...........................................................Passed` |
| 16 | `uv run python scripts/check_untracked_secrets.py` | PASS; `detect-secrets (untracked): no untracked files to scan` |

Final pytest / coverage lines pasted from the file:

```text
TOTAL                                                           21956      0   4700      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
========= 5333 passed, 9 skipped, 2470 warnings in 503.53s (0:08:23) ==========
```

The nine skips are the environment-dependent cases printed by pytest (optional dependencies, local secrets, database/network opt-ins, and link privilege); no test failed. The accepted audit advisory is `PYSEC-2026-2447` for `diskcache 5.6.3`, re-checked by the gate. `.secrets.baseline` unchanged.

**`make gate-ran`:** the planner's, after the push.

**Not met / verified failing:** No local build criterion failing. Remote gate (`make gate-ran`), push, merge, deploy, F1 and F2: **not done**, planner-owned. Live settings in Appendix A are planner evidence, not re-measured here.

---

## Return notes

- No scope or Appendix corrections needed. The explicit one-request guarantee in DLIB-IDM-04 is additionally cited in A5, which proves only its configuration premise; no claim of a newly green clause.
- Law reading record was the first edit, before the new test or Appendix application. No laws, existing tests, design log or state trackers edited. No uv lock/sync, Azure command or deploy executed.
- Appendix B patch and all evidence logs live outside the worktree in `C:/Users/yury_/Downloads/project/`.
- All local CI steps completed; no sandbox exception needed. Planner retains remote gates, merge, F1 and F2.
- Commit pending immediately after this prepared closeout; its SHA will be recorded in the follow-up handback commit. No push or merge.
- The first commit attempt was rejected by markdownlint MD012 for an extra blank line introduced in the closeout edit; that blank line was removed before retry.

---

## Appendix A — what the three apps hold live, and what the prototype's `Up` sends

Read 2026-11-17 06:34 UTC from the live apps, and printed by the deploy script's own `Up` on the
prototype with every `az` call a stand-in. The two outputs are equal, line for line:

```text
deliberator-manager    max replicas 1 | replicas in the nightly window 1
    DELIBERATOR_DEBATE_CONCURRENCY=3
    DELIBERATOR_EFFORT=high
    DELIBERATOR_INSTANCE_NAME=deliberator-manager
    DELIBERATOR_LLM_PROVIDER=openai
    DELIBERATOR_REQUEST_TIMEOUT_SECONDS=240
    DELIBERATOR_ROLE=manager
deliberator-proponent  max replicas 3 | replicas in the nightly window 3
    DELIBERATOR_EFFORT=high
    DELIBERATOR_INSTANCE_NAME=deliberator-proponent
    DELIBERATOR_LLM_PROVIDER=openai
    DELIBERATOR_REQUEST_TIMEOUT_SECONDS=120
    DELIBERATOR_ROLE=proponent
deliberator-opponent   max replicas 3 | replicas in the nightly window 3
    DELIBERATOR_EFFORT=high
    DELIBERATOR_INSTANCE_NAME=deliberator-opponent
    DELIBERATOR_LLM_PROVIDER=openai
    DELIBERATOR_REQUEST_TIMEOUT_SECONDS=120
    DELIBERATOR_ROLE=opponent
deliberator apps given a nightly rule: 3 ; failures recorded: 0
```

On `main` (`68273b16`) the same runner prints `DELIBERATOR_DEBATE_CONCURRENCY=1`,
`DELIBERATOR_REQUEST_TIMEOUT_SECONDS=120` on the manager, and `max replicas 1 | replicas in the
nightly window 1` on each debater: the four lines a full `up` would move today.

## Appendix B — the change, measured on the planner's prototype

Save the block below to a file and run `git apply <file>` from the worktree's root. It changes
three lines of the pack (two values on `deliberator-manager`, and `_measured`, which gains one
amendment at its end), one line of `pyproject.toml` and one line of `uv.lock`.

```diff
diff --git a/orchestration/packs/trading_tunables.json b/orchestration/packs/trading_tunables.json
index 414801aa..d276a860 100644
--- a/orchestration/packs/trading_tunables.json
+++ b/orchestration/packs/trading_tunables.json
@@ -2,3 +2,3 @@
   "_comment": "Operator-set agent tunables the deploy must carry (DL-100 / S169). Mechanism lives in infra/deploy-agents.ps1; these names and values are trading-pack data (ADR-0012). A full `up` REPLACES each app's env set, so a tunable that lives only as live cluster state is silently reverted to its code default with a green [OK]. This file is that single source of truth. Values are strings because container env vars are strings. Secrets never appear here - they arrive as secretrefs from Key Vault via master (DL-07).",
-  "_measured": "Snapshot of the live fleet read on 2026-08-14 from Azure Container Apps RG trading-agents. STAGED 2026-08-20: DELIBERATOR_LLM_PROVIDER openai->anthropic on all three deliberators (DL-99 operator switch). The three *_MODEL vars are deliberately empty, so this resolves the Anthropic adapter default claude-opus-5. NOT YET APPLIED LIVE - the Anthropic key is blocked by an operator-set spend limit; live env still reads openai until that limit is raised. Both providers are currently non-functional, so the divergence degrades nothing. Amended 2026-08-19 (DL-116): grace 900->1800 and deliberator request timeout 60->120, measured off sched-2026-08-19 (debate span ~990s vs 900s grace; LLM tail 65.3/59.3/58.2s vs a 60s ceiling). Amended 2026-09-04 (S172 merge): DELIBERATOR_DEBATE_CONCURRENCY ships at 1, not the code default of 4. K=1 is the deployed status quo; K>1 measured 1.78x of a possible 4x and, on one of two runs, dead-lettered 6 peer replies with 2 of 15 orders failing open, so the fan-out merges as an available dial rather than as proven behaviour. Raising it is a deliberate edit here plus an `up`. Amended 2026-09-05 (S198, operator decision): ANALYST_STOP_TARGET_MODE flat->scaled, promoting the S150 challenger (ADR-0013 / DL-77). Measured first on the live graph over 269 recorded recommendations - scaled stops span 3.00/5.45/8.00 pct against a flat 5.00/5.00/5.00, and the reward-risk pass rate is 100 pct in BOTH modes, so DL-77's named trap (widen the stop, silently stop trading AMD/MRVL/HPE) does not bite on this book. The touch-rate half could not be measured at all - stop_target_observed_drawdown_pct had no producer - so S198 ships the recorder in the same change: the flip is auditable on our own trades from its first night, not only against DL-77's external 2026-04 backtest. Amended 2026-09-13 (operator decision, work-queue item 47 / [DL-76]): EXECUTION_ORDER_PRICE_TOLERANCE_MODE flat->scaled, promoting the S149 challenger. Promoted on DL-76's EXTERNAL measurement (60 sessions of real overnight gaps to 2026-05-01: a flat 50 bps refuses 35 pct of buys and 23 pct of sells blended, and the distribution is the finding - SCHW 25 pct against AMD 52 pct, so one number encodes two different policies), NOT on own-book evidence, because own-book evidence was structurally uncollectable while the narrower band was the applied one: compare_order_tolerances reported flat and scaled identical at 0.00 pct drop over 170 orders, correctly, because scaled is wider on 170 of 170 (75-250 bps against a fixed 50) so every order the flat band accepted the scaled band also accepts. The flip inverts that and is what makes the comparison informative for the first time - with the wider band applied, an order filling above the flat limit is an order flat would have refused, which is DL-76's refusal rate measured on our own book. Operator chose this over closing the item as decided-by-design.",
+  "_measured": "Snapshot of the live fleet read on 2026-08-14 from Azure Container Apps RG trading-agents. STAGED 2026-08-20: DELIBERATOR_LLM_PROVIDER openai->anthropic on all three deliberators (DL-99 operator switch). The three *_MODEL vars are deliberately empty, so this resolves the Anthropic adapter default claude-opus-5. NOT YET APPLIED LIVE - the Anthropic key is blocked by an operator-set spend limit; live env still reads openai until that limit is raised. Both providers are currently non-functional, so the divergence degrades nothing. Amended 2026-08-19 (DL-116): grace 900->1800 and deliberator request timeout 60->120, measured off sched-2026-08-19 (debate span ~990s vs 900s grace; LLM tail 65.3/59.3/58.2s vs a 60s ceiling). Amended 2026-09-04 (S172 merge): DELIBERATOR_DEBATE_CONCURRENCY ships at 1, not the code default of 4. K=1 is the deployed status quo; K>1 measured 1.78x of a possible 4x and, on one of two runs, dead-lettered 6 peer replies with 2 of 15 orders failing open, so the fan-out merges as an available dial rather than as proven behaviour. Raising it is a deliberate edit here plus an `up`. Amended 2026-09-05 (S198, operator decision): ANALYST_STOP_TARGET_MODE flat->scaled, promoting the S150 challenger (ADR-0013 / DL-77). Measured first on the live graph over 269 recorded recommendations - scaled stops span 3.00/5.45/8.00 pct against a flat 5.00/5.00/5.00, and the reward-risk pass rate is 100 pct in BOTH modes, so DL-77's named trap (widen the stop, silently stop trading AMD/MRVL/HPE) does not bite on this book. The touch-rate half could not be measured at all - stop_target_observed_drawdown_pct had no producer - so S198 ships the recorder in the same change: the flip is auditable on our own trades from its first night, not only against DL-77's external 2026-04 backtest. Amended 2026-09-13 (operator decision, work-queue item 47 / [DL-76]): EXECUTION_ORDER_PRICE_TOLERANCE_MODE flat->scaled, promoting the S149 challenger. Promoted on DL-76's EXTERNAL measurement (60 sessions of real overnight gaps to 2026-05-01: a flat 50 bps refuses 35 pct of buys and 23 pct of sells blended, and the distribution is the finding - SCHW 25 pct against AMD 52 pct, so one number encodes two different policies), NOT on own-book evidence, because own-book evidence was structurally uncollectable while the narrower band was the applied one: compare_order_tolerances reported flat and scaled identical at 0.00 pct drop over 170 orders, correctly, because scaled is wider on 170 of 170 (75-250 bps against a fixed 50) so every order the flat band accepted the scaled band also accepts. The flip inverts that and is what makes the comparison informative for the first time - with the wider band applied, an order filling above the flat limit is an order flat would have refused, which is DL-76's refusal rate measured on our own book. Operator chose this over closing the item as decided-by-design. Amended 2026-11-17 (work-queue 113, DL-325; the operator's decisions of 2026-10-08 and 2026-10-09, DL-274 D4 and DL-277 amendment 2): on deliberator-manager DELIBERATOR_DEBATE_CONCURRENCY 1->3 and DELIBERATOR_REQUEST_TIMEOUT_SECONDS 120->240. Both were live settings on the fleet from those dates, held out of this file only by the fidelity count (PASS 2026-10-27), so a full up would have put one lane and the 120 s wait back. The deploy script gives each debater as many replicas as the lane count, so the 3 is also each debater's replicas in the nightly window. Measured on the live graph 2026-11-17: 27 nightly debate records since 2026-10-09, 0 orders failed open, 0 orphaned replies; seven buys were debated in 662 s on 2026-10-26, where one debate alone took 217 to 347 s on its own nights against execution's 1800 s. The two debaters keep 120: only the manager makes a peer request. This supersedes the 2026-09-04 sentence above that says the dial ships at 1.",
   "apps": {
@@ -27,4 +27,4 @@
       "DELIBERATOR_EFFORT": "high",
-      "DELIBERATOR_REQUEST_TIMEOUT_SECONDS": "120",
-      "DELIBERATOR_DEBATE_CONCURRENCY": "1"
+      "DELIBERATOR_REQUEST_TIMEOUT_SECONDS": "240",
+      "DELIBERATOR_DEBATE_CONCURRENCY": "3"
     },
diff --git a/pyproject.toml b/pyproject.toml
index daf54b77..5192763a 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -2,3 +2,3 @@
 name = "trading-agents"
-version = "0.131.06"
+version = "0.131.07"
 description = "An operator-controlled, single-user, agent-based trading system. Domain logic lives only in agents; the kernel is plumbing; contracts are the shared boundary."
diff --git a/uv.lock b/uv.lock
index b02eb597..a0eca83d 100644
--- a/uv.lock
+++ b/uv.lock
@@ -3671,3 +3671,3 @@ wheels = [
 name = "trading-agents"
-version = "0.131.6"
+version = "0.131.7"
 source = { virtual = "." }
```

After it, `git hash-object` must print:

```text
d276a8600359172313654f3c4a5af01a475f5d25  orchestration/packs/trading_tunables.json
5192763ac41793a1b86de964c08df997cb54f4bb  pyproject.toml
a0eca83dcccf706d5c06947c2627f0c0d2a1d930  uv.lock
```

On the prototype: `uv lock --check` accepts the lock; `make ci` exit 0 in one run with the bump applied, sixteen steps: 5,333 passed, 9 skipped, 100.00 % coverage, the dependency audit clean but the one accepted advisory.

## Appendix C — the fifteen breaks, as exact replacements

Each break replaces the first occurrence of **Old** with **New** in the file named, unless the row
says the second. `PROPONENT-END` is these three lines of the pack, the end of the proponent's entry:

```text
      "DELIBERATOR_REQUEST_TIMEOUT_SECONDS": "120"
    },
    "deliberator-opponent"
```

| # | File | Old | New | Must go red |
| --- | --- | --- | --- | --- |
| B1 | the pack | `"DELIBERATOR_DEBATE_CONCURRENCY": "3"` | `"DELIBERATOR_DEBATE_CONCURRENCY": "1"` | A1 |
| B2 | the pack | the same | `"DELIBERATOR_DEBATE_CONCURRENCY": "2"` | A1 |
| B3 | the pack | the same | `"DELIBERATOR_DEBATE_CONCURRENCY": "4"` | A1 |
| B4 | the pack | `PROPONENT-END` | its first line ends with a comma and is followed by a new line `"DELIBERATOR_DEBATE_CONCURRENCY": "3"` at the same indent | A2 |
| B5 | the pack | `"DELIBERATOR_REQUEST_TIMEOUT_SECONDS": "240"` | `"DELIBERATOR_REQUEST_TIMEOUT_SECONDS": "120"` | A3 |
| B6 | the pack | the same | `"DELIBERATOR_REQUEST_TIMEOUT_SECONDS": "300"` | A3 |
| B7 | the pack | `PROPONENT-END` | its first line holds `"240"` | A4 |
| B8 | `kernel/bus_azure_config.py` | the line `1,` directly above `why="A taken request is already settled` | `10,` | A5 |
| B9 | the pack | `PROPONENT-END` | its first line ends with a comma and is followed by a new line `"AZURE_SERVICEBUS_RECEIVE_MAX_MESSAGES": "10"` at the same indent | A5 |
| B10 | `infra/deploy-agents.ps1` | `function Get-AppMaxReplicas($name) {` | a new line `$TakenAPass = "AZURE_SERVICEBUS_RECEIVE_MAX_MESSAGES=10"` above it | A5 |
| B11 | the pack | `DELIBERATOR_DEBATE_CONCURRENCY 1->3` | `DELIBERATOR_DEBATE_CONCURRENCY 1->4` | A6 |
| B12 | the pack | `DELIBERATOR_REQUEST_TIMEOUT_SECONDS 120->240` | `DELIBERATOR_REQUEST_TIMEOUT_SECONDS 120->300` | A6 |
| B13 | the pack | `(work-queue 113, DL-325; ` | `(work-queue 113; ` | A6 |
| B14 | `infra/deploy-agents.ps1` | `"deliberator-opponent")) { return (Resolve-DebateConcurrency) }` | `"deliberator-opponent")) { return 3 }` | the existing `test_peer_replica_count_follows_the_pack_and_not_a_literal` in `tests/test_deploy_tunables_pack.py` |
| B15 | `infra/deploy-agents.ps1` | the same, **second** occurrence | the same | the same existing test |

On the prototype: 15 planted, 15 red, each on the test named; B1 also turns A5 red and B9 also an
existing test (`test_every_key_is_a_tunable_that_agent_reads`), which is expected.
