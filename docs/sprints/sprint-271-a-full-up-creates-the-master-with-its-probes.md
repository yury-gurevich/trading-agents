<!-- Agent: planning | Role: sprint handover -->
# Sprint 271 — a full `up` creates the master with its probe pack, so no revision of it refuses to start

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-271-a-full-up-creates-the-master-with-its-probes`
**Status:** MERGED 2026-10-13 — no version bump, fast-forwarded to `9eb1325f`, GATE PROVEN `9eb1325f` (CI, CodeQL, Security Findings); F1 passed at no cost; F2 owed at the next full `up`; no deploy
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

- [x] On the built tree A1 to A6 pass (eight cases); on the unchanged script A1 and A2 fail.
- [x] `infra/deploy-agents.ps1` is the Appendix's text: its blob id is `d9447b634e68f1ea4e7deeec3e97d0d2220e1cfb`.
- [x] Exactly one existing test is removed, the one named; no other existing test is edited.
- [x] No file under `agents/`, `kernel/`, `contracts/`, `orchestration/`, `surfaces/` or `scripts/` changes; no version bump; `uv.lock` untouched.
- [x] Law-cycle question answered No, with the reason, in the Law reading record.
- [x] Every break under Traps planted, watched to fail, restored, stated per break.
- [x] Every touched Python module under 200 lines.
- [x] `make ci` exit 0, 100.00 % coverage.

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
| `infra/deploy-agents.ps1` | `agents/master/laws/laws.md` and `test-plan.md`, whole, 2026-10-13 | `MST-NEV-07`; related declaration requirement `MST-DEP-04` | No. Supply the existing required probes at create; preserve the startup refusal and separate vocabulary update. |
| `tests/test_deploy_master_revision.py` | Same master files; `docs/laws/conventions.md`, whole, 2026-10-13 | `MST-NEV-07` in A5/A6; conventions §3 and §7 require functional citations | No. Deployment-pack smoke tests supplement the existing local master tests; no law row or count changes. |
| `tests/test_deploy_script_invariants.py` | No additional law governs the named removal; master files read above | None governs deploy-call order | No. Remove only the obsolete narrow-update test. |
| Sprint handback | `docs/laws/drift-register.md`, whole, 2026-10-13; conventions above | `DRIFT-053` and corrected `DRIFT-105` explain the declaration and vendor-selection requirements | No contradiction or new drift found within this sprint. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No. No contract or agent code changes; the deployment script supplies the probes the master's existing `MST-NEV-07` refusal already requires.

**Contradictions found between a law and this spec:** None found in the four required files.

**Laws found silent where a decision was needed:** No clause governs deploy-call order or command-line pack size. DL-296 already decides these; no new decision or design-log entry is needed.

**Clauses that were ⬜ and are now proven:** None. `MST-NEV-07` is already 🟩; A5/A6 add deployment-pack evidence without changing its test-plan row or either rollup.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a1_create_carries_probes_secret_map_and_provider` | `tests/test_deploy_master_revision.py` | PASS; red first | None: deploy-call order |
| A2 | `test_a2_no_later_call_delivers_the_probe_pack` | same | PASS; red first | None: deploy-call order |
| A3 | `test_a3_vocabulary_keeps_its_separate_update` | same | PASS; both guards red/restored | None: deploy-call order |
| A4 | `test_a4_committed_create_packs_fit_the_command_line` | same | PASS before/after patch; both guards red/restored | None: command-line size |
| A5 | `test_a5_master_starts_with_the_create_packs` | same | PASS × 2 (`anthropic`, `openai`); each vendor deletion red/restored | `MST-NEV-07` |
| A6 | `test_a6_missing_probes_refuse_vendor_grants` | same | PASS × 2 (`anthropic`, `openai`); refusal deletion red/restored | `MST-NEV-07` |

**Tests added beyond the plan:** None. Six test functions, eight cases from the current two vendors in `KEY_ENV`.

---

## Closeout — evidence

**Status:** MERGED — the build proof is the builder's, below; the remote gate and F1 are in the planner's review at the merge; F2 is owed at the next full `up`.

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/Downloads/project/ta-s271`, branch `sprint-271-a-full-up-creates-the-master-with-its-probes`; `.env` absent. Started clean at `60be51bb23dc06dcf9391f426b79306cffdb392d`, also the observed `origin/main`.

**Result:** The deploy script is the Appendix byte for byte, carries the probes on create, retains the separate vocabulary update, and has no later probe-delivery call. Eight planned cases pass; all 14 sequential guard runs fail as required and are restored; all 16 local CI steps pass. No deployment or remote gate is claimed.

**Files changed:** `infra/deploy-agents.ps1`; `tests/test_deploy_master_revision.py` (new); `tests/test_deploy_script_invariants.py` (only the named removal); this spec; this sprint's row in `docs/sprints/README.md`.

**Proof — the red run first:** Unchanged script, before the Appendix; exit 1. Only A1 and A2 failed; A3–A6 passed (six cases).

```text
uv run pytest tests/test_deploy_master_revision.py --no-cov -q
FF......                                                                 [100%]
================================== FAILURES ===================================
____________ test_a1_create_carries_probes_secret_map_and_provider ____________
tests\test_deploy_master_revision.py:64: in test_a1_create_carries_probes_secret_map_and_provider
    assert "(Get-MasterCredentialTestsEnv)" in env
E   assert '(Get-MasterCredentialTestsEnv)' in '\n    "MASTER_GRAPH=auto",\n    "MASTER_PRIVATE_KEY_PEM_B64=secretref:master-key-b64",\n    "MASTER_GRANT_POLICY_B64=$grantB64", "MASTER_SECRET_MAP_B64=$secretB64"\n  ) + (Get-AppLlmEnv "master")\n  '
________________ test_a2_no_later_call_delivers_the_probe_pack ________________
tests\test_deploy_master_revision.py:73: in test_a2_no_later_call_delivers_the_probe_pack
    assert "Set-MasterCredentialTests" not in text
E   assert 'Set-MasterCredentialTests' not in "# deploy-ag... Down }\n}\n"
E
E     'Set-MasterCredentialTests' is contained here:
E
E       function Set-MasterCredentialTests {
E         $state = Invoke-Az @(
E           "containerapp", "update", "--name", "master", "--resource-group", $RG,
E           "--subscription", $SUB, "--set-env-vars", (Get-MasterCredentialTestsEnv),...
E
E     ...Full output truncated (220 lines hidden), use '-vv' to show
=========================== short test summary info ===========================
FAILED tests/test_deploy_master_revision.py::test_a1_create_carries_probes_secret_map_and_provider
FAILED tests/test_deploy_master_revision.py::test_a2_no_later_call_delivers_the_probe_pack
2 failed, 6 passed in 1.48s
RED_EXIT=1
```

**Proof — the green run:** After every planted break was restored; eight new cases plus eleven retained deploy invariants.

```text
uv run pytest tests/test_deploy_master_revision.py tests/test_deploy_script_invariants.py --no-cov -q
...................                                                      [100%]
19 passed in 1.30s
RESTORED_GREEN_EXIT=0
```

**Guards planted:** Each alone, restored before the next. The create-probe removal was independently planted for A1 and A2; the final refusal break failed both vendor cases. Logs are in `C:/Users/yury_/AppData/Local/Temp/ta-s271-20261013-60be51bb`.

```text
01-remove-create-probes-A1: exit=1; 1 failed in 1.38s; restored byte-for-byte
02-remove-create-probes-A2: exit=1; 1 failed in 1.34s; restored byte-for-byte
03-restore-late-setter-and-call: exit=1; 1 failed in 1.36s; restored byte-for-byte
04-probes-in-vocabulary-update: exit=1; 1 failed in 1.35s; restored byte-for-byte
05-remove-declared-provider: exit=1; 1 failed in 1.34s; restored byte-for-byte
06-remove-secret-map: exit=1; 1 failed in 1.35s; restored byte-for-byte
07-vocabulary-in-create: exit=1; 1 failed in 1.37s; restored byte-for-byte
08-skip-master-vocabulary-update: exit=1; 1 failed in 1.36s; restored byte-for-byte
09-drop-create-env-arguments: exit=1; 1 failed in 1.36s; restored byte-for-byte
10-pad-probe-pack-16000-bytes: exit=1; 1 failed in 1.38s; restored byte-for-byte
11-getter-reads-issuer-pack: exit=1; 1 failed in 1.34s; restored byte-for-byte
12-delete-openai-probes: exit=1; 1 failed in 1.35s; restored byte-for-byte
13-delete-anthropic-probes: exit=1; 1 failed in 1.35s; restored byte-for-byte
14-remove-vendor-refusal: exit=1; 2 failed in 1.36s; restored byte-for-byte
GUARDS_PROVEN=14/14; ALL_MUTATED_FILES_RESTORED
```

**Blob id of `infra/deploy-agents.ps1`:**

```text
git hash-object infra/deploy-agents.ps1
d9447b634e68f1ea4e7deeec3e97d0d2220e1cfb
git ls-files --eol -- infra/deploy-agents.ps1
i/lf    w/lf    attr/text=auto eol=lf 	infra/deploy-agents.ps1
```

**Module line counts:**

```text
infra/deploy-agents.ps1: 938 lines; CRLF=0
tests/test_deploy_script_invariants.py: 178 lines; CRLF=0
tests/test_deploy_master_revision.py: 123 lines; CRLF=0
Existing test file: exactly the named test removed; no other byte changed.
Unchanged: agents/master/credential_selection.py
Unchanged: orchestration/packs/trading_credential_tests.json
Unchanged: pyproject.toml
Unchanged: uv.lock
CI_STEPS=16
PACK_BASE64_PLUS_RESERVE=18432
```

**`make ci`:** Redirected directly to `C:/Users/yury_/AppData/Local/Temp/ta-s271-20261013-60be51bb/ci.txt`, then read in full. Exit 0; 16 of 16 steps passed, no CI step skipped; pytest 4,784 passed / 8 skipped / 2,470 warnings; coverage 100.00 %. Dependency audit passed (one existing accepted advisory re-checked); detect-secrets passed; no untracked files to scan. The status step ran before the final SPEC → BUILT doc edits; their affected checks are re-run below.

Verbatim excerpts from the redirected file: all 16 command lines are retained; repetitive module-size warnings, sprint rows, pytest progress, warnings and per-module coverage rows are omitted.

```text
make ci > C:/Users/yury_/AppData/Local/Temp/ta-s271-20261013-60be51bb/ci.txt 2>&1
uv run ruff check . --output-format=github
uv run ruff format --check .
1678 files already formatted
uv run mypy kernel contracts agents orchestration surfaces
pyproject.toml: note: unused section(s): module = ['azure.core', 'azure.identity.*', 'azure.keyvault', 'celery.*', 'redis', 'redis.*']
Success: no issues found in 1197 source files
uv run lint-imports
Agents may not import one another (talk only via messages) KEPT
Substrate imports no pack module KEPT
Agents may not reach into surfaces or orchestration KEPT
Kernel is pure plumbing — no domain, no contracts, no agents KEPT
Contracts declare schemas only — never import agents or runtime layers KEPT
Contracts: 5 kept, 0 broken.
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts
[WARN] tests/test_deploy_script_invariants.py: 178 lines (warn 150, hard block 200)
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run python scripts/check_law_coverage.py
uv run python scripts/check_param_law_sync.py
[WARN] portfolio_manager.max_position_pct declared_default=0.10 envelope=(0.01, 0.05) source=FCA COLL 5.2 — UCITS investment powers and limits
[WARN] portfolio_manager.max_positions declared_default=10 envelope=(30.0, 60.0) source=Evans and Archer, forty years later
uv run python scripts/check_sprint_status.py
docs/sprints/sprint-271-a-full-up-creates-the-master-with-its-probes.md: SPEC | **Status:** SPEC
docs_seen=276 SPEC=11 BUILT=0 MERGED=265 UNMAPPED=0 MISSING=0
uv run python scripts/check_tracker_size.py
[OK] docs/STATE.md: 30,620 of 40,000 bytes (76 %)
[OK] docs/work-queue.md: 46,946 of 64,000 bytes (73 %)
[WARN] docs/sprints/README.md: 90,456 of 96,000 bytes (94 %)
[OK] docs/sprints/INDEX.md: 23,863 of 48,000 bytes (49 %)
[OK] docs/design-log.md: 357,959 of 512,000 bytes (69 %)
[OK] docs/laws/functionality-checks.md: 103,464 of 160,000 bytes (64 %)
[OK] docs/laws/drift-register.md: 131,646 of 160,000 bytes (82 %)
uv run python scripts/check_markdown_links.py
uv run python scripts/check_version_scheme.py
uv run pytest
TOTAL                                                           20288      0   4306      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
SKIPPED [1] tests\test_bus_azure_config.py:21: Service Bus dotenv isolation proof requires local .env
SKIPPED [1] tests\test_bus_celery.py:181: CELERY_BROKER_URL is not set
SKIPPED [1] tests\test_deliberator_servicebus_peer.py:36: A1 proof requires .env present; CI has no local secrets file
SKIPPED [1] tests\test_graph_postgres.py:137: POSTGRES_TEST_DSN is not set
SKIPPED [1] tests\test_graph_postgres_keys.py:90: POSTGRES_TEST_DSN is not set
SKIPPED [1] agents\forecaster\tests\test_barrier_garch_oracle.py:179: could not import 'scipy.signal': No module named 'scipy'
SKIPPED [1] agents\provider\tests\test_sources.py:159: FINNHUB_TEST_NETWORK=1 is not set
SKIPPED [1] agents\provider\tests\test_stooq.py:66: STOOQ_TEST_NETWORK=1 is not set
========= 4784 passed, 8 skipped, 2470 warnings in 378.13s (0:06:18) ==========
uv run python scripts/check_dependency_audit.py
accepted: PYSEC-2026-2447 (diskcache 5.6.3) - reachable only via the 'optimizer' extra, installed by 1 of 15 Dockerfiles; each installing command excludes diskcache by name; the dev group carries it too, and every sync passes --no-dev or excludes it by name; no fix release exists; every deployed optimizer installation excludes diskcache by name (S254, DL-266, ADR-0032) [DL-184] - retire when diskcache publishes a fixed release, or the optimizer extra is dropped
No unaccepted vulnerabilities; 1 accepted advisory re-checked
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
detect-secrets (untracked): no untracked files to scan
CI_EXIT=0
```

**Post-handback doc checks:** All six exited 0 after both statuses became BUILT; full log: `C:/Users/yury_/AppData/Local/Temp/ta-s271-20261013-60be51bb/final-doc-checks-green.txt`. Verbatim output below omits the other sprint rows.

```text
COMMAND: uv run python scripts/check_sprint_status.py
docs/sprints/sprint-271-a-full-up-creates-the-master-with-its-probes.md: BUILT | **Status:** BUILT
docs_seen=276 SPEC=10 BUILT=1 MERGED=265 UNMAPPED=0 MISSING=0
EXIT=0
COMMAND: uv run python scripts/check_tracker_size.py
[OK] docs/STATE.md: 30,620 of 40,000 bytes (76 %)
[OK] docs/work-queue.md: 46,946 of 64,000 bytes (73 %)
[WARN] docs/sprints/README.md: 90,610 of 96,000 bytes (94 %)
[OK] docs/sprints/INDEX.md: 23,863 of 48,000 bytes (49 %)
[OK] docs/design-log.md: 357,959 of 512,000 bytes (69 %)
[OK] docs/laws/functionality-checks.md: 103,464 of 160,000 bytes (64 %)
[OK] docs/laws/drift-register.md: 131,646 of 160,000 bytes (82 %)
EXIT=0
COMMAND: uv run python scripts/check_markdown_links.py
EXIT=0
COMMAND: uv run pre-commit run markdownlint-cli2 --files docs/sprints/sprint-271-a-full-up-creates-the-master-with-its-probes.md docs/sprints/README.md
markdownlint-cli2........................................................Passed
EXIT=0
COMMAND: uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
EXIT=0
COMMAND: uv run python scripts/check_untracked_secrets.py
detect-secrets (untracked): no untracked files to scan
EXIT=0
FINAL_DOC_CHECKS=6/6
```

**`make gate-ran`:** not done. The branch is not pushed; the planner owes remote proof for the final branch SHA before merge.

**Not met / verified failing:** No required local build check is verified failing. Push, remote gate, merge, deploy, post-merge F1 and next-full-`up` F2 are not done. Azure acceptance of the create call remains unproven, as the spec states.

---

## Return notes

- No clause governs deploy-call order; A1–A4 pin DL-296, while A5/A6 cite the existing `MST-NEV-07`. No law row, rollup, drift row or design-log entry changed.
- Only the five scoped files change. The planted `agents/master/credential_selection.py` break and all probe-pack mutations were restored byte for byte. All excluded source directories, `scripts/`, the version and `uv.lock` are unchanged. The probe budget is 18,432 of 32,767 characters; padding the pack by exactly 16,000 bytes made A4 fail at 39,764.
- Small tooling corrections: initial reads used two nonexistent paths, corrected to root `conftest.py` and `orchestration/packs/`; the temporary mutation runner stopped before guard 04 because its vocabulary pattern matched both app and job setters, then was scoped to `Set-AppVocabulary` and resumed; one log-excerpt reader hit Windows cp1252 and was re-run with UTF-8. These did not change the implementation or the CI result. Trailing spaces on otherwise blank red-output lines were trimmed for Markdown hygiene; the final Markdown check also caught two trailing spaces on evidence labels, now removed and re-checked.
- CI's eight existing skips are pasted above. Its existing module-size and parameter-envelope warnings remain; `docs/sprints/README.md` is close to its 96,000-byte limit and was not trimmed outside this row.
- No deploy script or `az` command was run. Push, `make gate-ran`, merge, deploy and the planner's F1/F2 are not done; keep those stages separate from BUILT.

---

## Planner's review at the merge — 2026-10-13

Re-measured by the planner in `../ta-s271` on the builder's commit `9eb1325f`. Nothing here is taken
from the handback.

- **The script is the measured prototype byte for byte.** `infra/deploy-agents.ps1` has the
  Appendix's blob id (`d9447b63`), LF line endings, and parses with 0 errors. Against the spec's
  commit the branch changes the five files the spec names and no other; one existing test is
  removed, the one named, and that removal equals the prototype's diff.
- **The builder's test file is not the planner's text.** It is reworded, with the same six
  functions and the same assertions. It builds the master with a fixed text for the key where the
  planner's generates one, and it shuts the settings off from any `.env`.
- **Guards.** The planner's 14 breaks, one at a time against the three deploy test files, each
  restored: **14 went red, none survived, none failed to apply**; the tree was clean afterwards.
- **The planner's own tests** (eight cases, written for the prototype) were placed beside the
  builder's and run with the builder's file and the two retained deploy files: 29 passed. They are
  not committed.
- **Not re-run by the planner:** the local `make ci`. The builder's sixteen-step pass is the
  builder's statement; the proof is the remote gate on the same commit.
- **Gate.** `GATE PROVEN` for `9eb1325ff0259096006697943618930c70a25e5b`, run from `../ta-s271`,
  whose `HEAD` it is: CI, CodeQL and Security Findings each `success` on the first attempt. `main`
  had not moved since the spec's commit, so nothing was merged in and the proven commit is the
  merged one.
- **CodeQL.** 128 open alerts on the branch, 0 of them errors, the same 128 numbers as on the S270
  branch: none new, none gone.
- **F1, at no cost, on merged `main`.** `up_call_sequence.ps1` runs the script's own `Up` with
  every `az` call and credential a stand-in. It printed what the prototype printed: two master
  calls where the unchanged script made three; the create carries `MASTER_CREDENTIAL_TESTS_B64`
  beside the secret map and the provider on a line of at most 17,279 characters; the update
  carries the vocabulary alone; 30 calls for the 15 agents, 0 failures.
- **Owed.** F2 at the next full `up`: no refusal line in the master's console log for the two new
  revisions. Not proven until then: that Azure accepts the longer create call. No deploy follows
  from this sprint.

Evidence outside the repo: OneDrive `trading-agents-data/wq122-2026-10-13/`
(`planner_tests_on_built.txt`, `planner_breaks_on_built.txt`, `s271-gate-wait.txt`,
`s271-gate-ran.txt`, `codeql_s271_branch.tsv`, `codeql_s270_live.tsv`,
`up_calls_built_9eb1325f.txt`, `f1_main_9eb1325f.txt`, `s271_merge_docs.py`).

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
