<!-- Agent: planning | Role: sprint handover -->
# Sprint 271 — a full `up` creates the master with its probe pack, so no revision of it refuses to start

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-271-a-full-up-creates-the-master-with-its-probes`
**Status:** SPEC
**Version:** *no bump*
**Effort:** S
**Decisions:** [DL-296](../design-log.md) (this sprint's four decisions, made and measured) · [DL-282](../design-log.md) amendment 2 (where the hazard was first named) · [work-queue 122](../work-queue.md)

> **Why no bump.** The change is in `infra/deploy-agents.ps1` and in tests that read it. No file
> of the Python package changes, so the package's behaviour is the same and the version stays.
> The branch and the remote gate are still owed: the script changes production state.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 3 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/master/laws/laws.md` | The master's **locked constitution** | **LOCKED. Read only.** This sprint changes no line of it |
| `agents/master/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read only. `MST-NEV-07` is 🟩; two new tests cite it and its row does not change |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Read only. No rollup changes |

Binding sections here: **`MST-NEV`** (clause 07: the master refuses to start when an agent type is
granted the declared vendor's key and no probe is tagged for that vendor).

### The rule

1. **Before writing code**, read `agents/master/laws/laws.md` and its `test-plan.md`, whole.
2. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
3. **Write the Law reading record** (bottom of this file) **before** your first change.
4. **If a law contradicts this spec, STOP and report.**
5. A test for behaviour a clause governs cites the clause ID in its docstring: A5 and A6 cite
   `MST-NEV-07`. *[read 2026-10-13]* no clause of any law governs the order of the deploy script's
   calls; if your reading finds one, cite it and say so in the Return notes.

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**No.** No file under `contracts/` or `agents/` changes. The master's refusal is the law as it
stands; the sprint changes what the deploy script sends, so that the refusal is never met. No
clause, no test-plan row, no rollup and no drift row is owed. A5 and A6 are further tests of a
clause that is already green, so the law gate's counts stay as they are.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `infra/deploy-agents.ps1` | `agents/master/laws/laws.md` + `test-plan.md` | `MST-NEV-07`: what the master refuses to start on is what the create call must carry |
| `tests/test_deploy_master_revision.py` (new) | same; `docs/laws/conventions.md` §3 | A5 and A6 cite `MST-NEV-07` |
| `tests/test_deploy_script_invariants.py` | none | One test is removed: it pins the order this sprint ends |

⚠️ **The vocabulary pack must not join the master's create call.** With it the command line is
33,942 characters and the system refuses any line over 32,767. If your change would put
`Get-VocabularyEnv` or `GRAPH_VOCABULARY_B64` into that call, stop and report.

---

## Goal

After this sprint a full `up` makes two calls for the master, not three: the create call carries
the grant policy, the secret map, the declared LLM provider **and the probe pack**, and one update
adds the graph vocabulary. Every revision those calls create holds what the master needs to
start. A test goes red when the probe pack leaves the create call, when anything delivers it
later, or when the packs grow until the line no longer fits.

## Why (context)

The master refuses to start when it holds a secret map and no probes. `Up` creates the master
with the secret map, then sets the vocabulary, then sets the probe pack, each in its own call, and
each call makes a new revision. A create against an existing app replaces its whole env set, so
the first revision loses the probes the app held before, and the second still lacks them. Both
start, raise at start and are restarted by the platform until the third call lands.

The work-queue row said this *"did not bite"*. It was read for one deploy. The platform's log
says otherwise: it has happened at every full `up` in the 30 days the log keeps.

### Measured, 2026-10-13 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Master revisions that refused to start in the last 30 days | **22**, two at each of 11 full deploys on 10 days (2026-09-13 to 09-29), **63** refusals logged, each revision crashing 2 or 3 times in about 25 seconds | *[measured]* the master's console log in Log Analytics, the lines *"credential test declaration is required when a secret map is configured"*, grouped by revision (`master_refusals_30d.json`) |
| No refusal since 2026-09-29 | 0 rows | *[measured, same query]* every deploy since has been an image-only retag, which keeps the env set |
| What the master does with each state `up` leaves it in | secret map and no probes: refuses, under either vendor (*"operator granted openai key without its probe"*) and with no vendor (*"credential test declaration is required…"*); with the probes: starts, 9 probes kept under a vendor, 13 with none | *[measured]* `wq122_master_start.py`, `build_app` on the committed packs and an in-memory graph, no network |
| The calls `up` makes for the master today | 3: create (8 env names, no probes, line ≤ 8,412 characters), update with `GRAPH_VOCABULARY_B64` (≤ 16,863), update with `MASTER_CREDENTIAL_TESTS_B64` (≤ 9,070) | *[measured]* `up_call_sequence.ps1`: the script's own `Up`, every `az` call and every credential replaced by a stand-in of the real length |
| The same on the prototype | 2: create (9 env names, the probes among them, line ≤ **17,279**), update with the vocabulary (≤ 16,863) | *[measured, same harness]* |
| The line the system accepts | 17,300 and 32,000 characters pass, 33,950 is refused | *[measured]* one argument of that length given to the Azure CLI's own `python.exe` from PowerShell on this machine |
| With the vocabulary in the create call | 33,942 characters, over the limit | *[derived]* 17,279 + 16,663 |
| What is not pack content in the create line | 3,847 characters (key, registry, scale rule, env names, a 300-character DSN stand-in) | *[measured]* 17,279 less the three packs' 13,432 |
| A create replaces the env set of an app that exists | yes | *[carried from DL-100, measured 2026-08-08; consistent with the log above: each create's revision lacked the probes its predecessor held]* |
| Azure accepts the prototype's create call | not run | *[ASSUMED — not measured]* the call cannot be made without a deploy. The update that carries the vocabulary is 16,863 characters and has passed at every deploy since DL-85; the first full `up` after the merge settles it |
| Whether a crashing master revision ever harmed a deploy | not known | *[NOT measured]* the agents are created after the third call, and full deploys run outside the nightly window |

Evidence outside the repo: OneDrive `trading-agents-data/wq122-2026-10-13/`.

---

## Scope — and what is deliberately NOT here

1. **The tests first.** `tests/test_deploy_master_revision.py`, new, with the six tests of the
   Test plan. A1 and A2 fail on the unchanged script; A3 to A6 pass on it and guard what the
   change must keep.
2. **The script.** The four edits of the Appendix, exactly: the probe pack joins the master's env
   list, `Set-MasterCredentialTests` and its call are removed, and two comments say why.
3. **One existing test is removed**: `test_master_credential_tests_are_set_by_own_narrow_update`
   in `tests/test_deploy_script_invariants.py`. It asserts the function this sprint deletes. A2
   and A3 replace what it guarded.

### Out of scope (do NOT build this sprint)

- **The vocabulary call.** It stays a separate update, for the master and for every agent.
- **The master's start-up code.** The refusal is right and stays; no file under `agents/` changes.
- **The master's window start** (work-queue 131 f), the env-preservation check for the master, and
  anything else in the script.
- **`docs/deployment.md`.** Its warning about setting the three values in one update by hand
  stays true.
- **No `laws.md` edit**, no ADR reversal, no version bump, no `uv.lock` change.

### The road not taken (LAW-06)

- **Set the probe pack before the create.** Rejected: a create replaces the env set, so whatever
  an earlier update set is gone in the revision the create makes.
- **Create the master without the provider and the secret map, add them last.** Rejected: that
  first revision starts with no secret map at all, a master that can hand nothing over; the
  refusal is moved, not removed.
- **Everything in one call, the vocabulary too.** Rejected: 33,942 characters against 32,767.
- **A file of settings (`--yaml`) in place of the command line.** Rejected for this sprint: it
  would hold the master's private key and the registry token in a file on disk, and it is a new
  path for every app, not a fix for one.
- **Soften the master's refusal into a warning.** Rejected: a master with a secret map and no
  probes would hand over credentials nobody tested (DL-36).

---

## The design decisions — made, and recorded in DL-296

Do not add a design-log entry. They are recorded; this is their summary.

1. **The probe pack rides the master's create call**, beside the secret map and the provider.
2. **Nothing delivers it later**: `Set-MasterCredentialTests` is deleted, not kept unused.
3. **The vocabulary keeps its own call**, and a test says so for the master's create block.
4. **The line length is guarded by a test on the committed packs**: the three packs that ride,
   plus 5,000 characters for everything else (3,847 measured), must stay within 32,767.

---

## Blast radius — measured 2026-10-13

| What | Detail |
| --- | --- |
| Files changed | `infra/deploy-agents.ps1` (946 → 938 lines), `tests/test_deploy_script_invariants.py` (195 → 178), `tests/test_deploy_master_revision.py` (new, about 125), this file, this sprint's row in `README.md` |
| Agents affected | none; no file under `agents/`, `kernel/`, `contracts/`, `orchestration/` or `surfaces/` |
| Contract change? | no |
| Graph vocabulary change? | no |
| New env keys / tunables | none; the master's env set after a full `up` is the same ten names as today |
| Deploy implication | none by itself. The change acts at the next full `up`, whenever one is next needed |
| Rollback | revert the commit. A retag is not involved; nothing is written to the graph, the broker or Azure by this sprint |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Write the six tests** and run them on the unchanged script. A1 and A2 must fail. Paste the
   red output into the Closeout.
3. **Apply the Appendix** to `infra/deploy-agents.ps1`, exactly. Keep the file's line endings (LF).
4. **Remove the one existing test** named in Scope item 3. Change nothing else in that file.
5. **Prove the guards can fail (DL-70)**: plant each break listed under Traps, one at a time, see
   the named test go red, restore.
6. **`make ci` green**, every step of the `ci:` target, **redirected to a file, never piped**.
7. **Fill the handback sections**; set Status to `BUILT` here and in this sprint's `README.md` row.

---

## Test plan

All six in `tests/test_deploy_master_revision.py`. The *create block* is the script's text from
`Top "DEPLOY MASTER"` to `$masterState = Invoke-Az $mArgs`; the *env list* is the part of it from
`$envv = @(` to `$masterGraph`.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 the create carries the probes with the secret map and the provider | the script as it is | the env list holds `"MASTER_SECRET_MAP_B64=$secretB64"`, `(Get-MasterCredentialTestsEnv)` and `(Get-AppLlmEnv "master")`, and the block sends it: `$mArgs += @("--env-vars") + $envv` |
| A2 | 🎯 no later call delivers the probe pack | the script as it is | `Set-MasterCredentialTests` and `credentialTestsOk` appear nowhere; `Get-MasterCredentialTestsEnv` appears exactly twice (its definition and the env list); `MASTER_CREDENTIAL_TESTS_B64` exactly once |
| A3 | 🪤 the vocabulary pack stays out of the create call | the script as it is | neither `Get-VocabularyEnv` nor `GRAPH_VOCABULARY_B64` is in the create block, and `$vocabOk = Set-AppVocabulary "master"` follows it |
| A4 | 🪤 the create line fits with the packs as committed | the pack file names found in the create block and in the body of `Get-MasterCredentialTestsEnv` | they are exactly the grants, secrets and credential-tests packs, and the sum of their base64 lengths plus 5,000 is at most 32,767 |
| A5 | the master starts on what the create call carries, once for each vendor in `kernel.llm_factory.KEY_ENV` | `MasterSettings` built from the three committed packs and that vendor, an in-memory graph | `build_app` returns an agent with a session (`MST-NEV-07`) |
| A6 | 🪤 without the probes the same values refuse to start, once for each vendor | the same settings with an empty probe pack | `build_app` raises `ValueError` matching `granted <vendor> key without its probe` (`MST-NEV-07`) |

---

## Success factors

- [ ] On the built tree A1 to A6 pass (eight cases); on the unchanged script A1 and A2 fail.
- [ ] `infra/deploy-agents.ps1` is the Appendix's text: its blob id is `d9447b634e68f1ea4e7deeec3e97d0d2220e1cfb`.
- [ ] Exactly one existing test is removed, the one named; no other existing test is edited.
- [ ] No file under `agents/`, `kernel/`, `contracts/`, `orchestration/`, `surfaces/` or `scripts/` changes; no version bump; `uv.lock` untouched.
- [ ] Law-cycle question answered No, with the reason, in the Law reading record.
- [ ] Every break under Traps planted, watched to fail, restored, stated per break.
- [ ] Every touched Python module under 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **`tests/test_deploy_script_invariants.py` is at 195 lines and blocks at 200.** The new tests go
in the new file. That file only loses the one test.

🪤 **Do not run the script.** `infra/deploy-agents.ps1` and every `az` command are out of bounds;
your sandbox has no network and the script changes production. The tests read its text.

🪤 **The script's line endings are LF.** A tool that rewrites them to CRLF changes the blob id and
the handback is returned.

🪤 **A4 passes on the unchanged script, and that is right.** It guards the size, not the order.

🪤 **The breaks to plant, each alone, with the test that must go red:**

| Break | Red |
| --- | --- |
| remove `(Get-MasterCredentialTestsEnv)` from the env list | A1, A2 |
| put `Set-MasterCredentialTests` and its call back | A2 |
| add `(Get-MasterCredentialTestsEnv)` to `Set-AppVocabulary`'s update | A2 |
| remove `+ (Get-AppLlmEnv "master")` from the env list | A1 |
| remove `"MASTER_SECRET_MAP_B64=$secretB64"` from the env list | A1 |
| add `(Get-VocabularyEnv)` to the env list | A3 |
| replace `$vocabOk = Set-AppVocabulary "master"` with `$vocabOk = $true` | A3 |
| drop `@("--env-vars") + $envv` from the `$mArgs +=` line | A1 |
| pad a probe in `trading_credential_tests.json` until the file is 16,000 bytes longer | A4 |
| make `Get-MasterCredentialTestsEnv` read `trading_issuer_map.json` | A4 |
| delete every probe tagged `openai` from the pack (then the same for `anthropic`) | A5 |
| replace the `raise` at the end of `agents/master/credential_selection.py` with `pass` | A6 |

Restore each file before the next break. `git status` must show only your own work at the end.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `tests/test_deploy_script_invariants.py` **195**, `infra/deploy-agents.ps1`
  **946** (PowerShell, outside the size gate).
- Module docstring declares `Agent:` / `Role:` / `External I/O:` (the new test file: `tooling`).
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file. Count the steps from the `ci:` target.
- Run the suite with `uv run`, never with the venv's interpreter directly.
- **No version bump and no `uv.lock` change.**
- Secrets never through the worktree. The worktree has **no `.env`** and every test here runs
  without one. **State which tree you ran in.**

---

## Sequencing after merge (the planner's)

1. `make gate-ran` from the proving worktree, the printed SHA checked against `git rev-parse HEAD`.
2. The planner re-measures: the script's blob against the Appendix, the planner's own test file
   and `break_s271.py` (14 breaks) on the built tree, the open CodeQL alerts set-diffed against the
   last merged branch's.
3. **F1**, at no cost and with no network: on the merged `main`, `up_call_sequence.ps1` prints two
   master calls with the probes in the create, as `up_calls_prototype.txt` holds; the script parses
   with 0 errors; `wq122_master_start.py` prints what it printed before.
4. **F2, owed at the next full `up`** and not before: the master gets two new revisions, and the
   query of *Measured* returns no refusal for either. No full `up` is made for this sprint alone: a
   full `up` puts back the pack's values over the live-only settings (STATE, *Standing conditions*).
5. No deploy. `infra/` ships in no image.

---

## Handover — paste this to Codex

```text
You are building Sprint 271 in the worktree ../ta-s271, on the branch
sprint-271-a-full-up-creates-the-master-with-its-probes. Never work on main.

Read docs/sprints/sprint-271-a-full-up-creates-the-master-with-its-probes.md, whole, before
anything else. It is the spec, and its bottom sections are your handback.

In order:
1. Read agents/master/laws/laws.md and test-plan.md, docs/laws/conventions.md and
   docs/laws/drift-register.md. Fill the Law reading record in the spec BEFORE any change.
2. Write the six tests of the Test plan in a new file, tests/test_deploy_master_revision.py.
   Run them on the unchanged script: A1 and A2 must fail. Paste the red output into the Closeout.
3. Apply the Appendix to infra/deploy-agents.ps1, exactly, keeping LF line endings. Then
   git hash-object infra/deploy-agents.ps1 must print d9447b634e68f1ea4e7deeec3e97d0d2220e1cfb.
4. Remove test_master_credential_tests_are_set_by_own_narrow_update from
   tests/test_deploy_script_invariants.py. Change nothing else in that file.
5. Plant the breaks in the table under Traps one at a time; each must go red; restore each.
6. Run make ci redirected to a file and read the file. No version bump, no uv.lock change.
7. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in this
   sprint's row of docs/sprints/README.md. Commit on the branch if your sandbox lets you write
   the repository's git directory; if not, leave the tree uncommitted and say so.

DO NOT: run infra/deploy-agents.ps1 or any az command; change any file under agents/, kernel/,
contracts/, orchestration/, surfaces/ or scripts/; change anything else in the deploy script;
edit any existing test but the one removal named; add a design-log entry; edit docs/STATE.md,
docs/work-queue.md or docs/deployment.md; add or reword a law clause; bump the version; use
noqa; let any Python module reach 200 lines; measure make ci through a pipe.

Traps: tests/test_deploy_script_invariants.py is at 195 lines and blocks at 200, so the new
tests live in the new file; A4 passes on the unchanged script by design; the vocabulary pack
must never join the master's create call (the line would pass 32,767 characters); the break in
agents/master/credential_selection.py is a planted break, restore it.

STOP and report, writing nothing further, if: a law contradicts the spec; the blob id in step 3
does not match after an exact application; or a test other than A1 and A2 fails on the unchanged
script. For anything smaller, note it in the Return notes and continue.
State anything not done as "not done" or "verified failing". Never write a Result for work you
have not done.
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
| *to be filled by the builder* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *to be filled by the builder*

**Contradictions found between a law and this spec:** *to be filled by the builder*

**Laws found silent where a decision was needed:** *to be filled by the builder*

**Clauses that were ⬜ and are now proven:** *to be filled by the builder*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | *to be filled by the builder* | | | |
| A2 | | | | |
| A3 | | | | |
| A4 | | | | |
| A5 | | | | |
| A6 | | | | |

**Tests added beyond the plan:** *to be filled by the builder*

---

## Closeout — evidence

**Status:** *to be filled by the builder*

**Tree the proofs ran in (and `.env` present?):** *to be filled by the builder*

**Result:** *to be filled by the builder*

**Files changed:** *to be filled by the builder*

**Proof — the red run first:** *to be filled by the builder*

**Proof — the green run:** *to be filled by the builder*

**Guards planted:** *to be filled by the builder, one line a break*

**Blob id of `infra/deploy-agents.ps1`:** *to be filled by the builder*

**Module line counts:** *to be filled by the builder*

**`make ci`:** *to be filled by the builder: the file it was redirected to, the exit code, passed and skipped, coverage, dependency audit, detect-secrets*

**`make gate-ran`:** owed by the planner if the sandbox has no network; say so.

**Not met / verified failing:** *to be filled by the builder*

---

## Return notes

- *to be filled by the builder*

---

## Appendix — the script, measured on the planner's prototype

Four edits to `infra/deploy-agents.ps1`. Nothing else in the file changes.

### 1. The comment in `Get-MasterCredentialTestsEnv` — its first two comment lines become these three

```powershell
  # Rides the master's create call (DL-296): the master refuses to start with a
  # secret map and no probes, so a create without this pack left a revision that
  # crashed until a later update delivered it.
```

### 2. `Set-MasterCredentialTests` — the whole function is deleted

The nine lines from `function Set-MasterCredentialTests {` to its closing `}`, and the one blank
line after it, so that `function Up {` follows `Set-JobVocabulary`'s closing brace after one
blank line.

### 3. In `Up`, the comment line and the env list

The line `# Credential tests are set by their own narrow call below to stay under cmd.exe.`
becomes these two:

```powershell
  # The probe pack rides this call, so the revision it creates can start (DL-296).
  # The vocabulary pack cannot join it: together they pass CreateProcess's 32,767.
```

and the env list becomes:

```powershell
  $envv = @(
    "MASTER_GRAPH=auto",
    "MASTER_PRIVATE_KEY_PEM_B64=secretref:master-key-b64",
    "MASTER_GRANT_POLICY_B64=$grantB64", "MASTER_SECRET_MAP_B64=$secretB64",
    (Get-MasterCredentialTestsEnv)
  ) + (Get-AppLlmEnv "master")
```

### 4. In `Up`, after the create

The line `$credentialTestsOk = Set-MasterCredentialTests` is deleted, and the check becomes:

```powershell
  Check ($masterOk -and $vocabOk -and [bool]$fqdn) "master @ https://$fqdn"
```

The file is then 938 lines and its blob id is `d9447b634e68f1ea4e7deeec3e97d0d2220e1cfb`.
