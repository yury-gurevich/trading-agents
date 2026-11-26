<!-- Agent: planning | Role: sprint handover -->
# Sprint 292 — a return record names the model that scored, and one file names the LLM vendor

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-292-a-return-record-names-its-scorer-and-one-file-names-the-vendor`
**Status:** SPEC
**Version:** *next available PATCH at merge* (the prototype measured `0.131.09`)
**Effort:** S
**Decisions:** [DL-327](../design-log.md) (this sprint's five decisions, made and measured) · [DRIFT-117](../laws/drift-register.md) (the row this closes) · [DL-282](../design-log.md) decision 8 (the pack's provider lines, held back until the fidelity count allowed) · [work-queue 142 and 109](../work-queue.md)

> **Why this bump kind.** No new capability. `FORE-IDN-01` and `FORE-OUT-05` already promise that a
> prediction's `Model` record identifies the model, and the return leg writes a setting instead; the
> tunables pack declares a vendor the fleet has not run since 2026-10-09 and no deploy sends. Two
> false records corrected: a PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 4 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/forecaster/laws/laws.md` | The forecaster's **locked constitution** | **LOCKED.** This sprint applies one amendment the planner wrote (Appendix B): `FORE-IDN-01`'s return-leg wording, the version line and one Changelog entry. Nothing else in it changes |
| `agents/forecaster/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Two rows gain test names (Appendix B). No status changes |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | `drift-register.md` (DRIFT-117 to CORRECTED), `ledger.md` and `INDEX.md` (the forecaster row) change as Appendix B gives, nothing else |

Binding clauses: **`FORE-IDN-01`** (the four legs, each naming what scores it), **`FORE-OUT-05`** (a
`Model` node is upserted per `model_id`), **`FORE-TRG-01`** (the deployed loop fires the barrier leg
only), and the forecaster's **`PARAM`** rows `return_model_id`, `return_model_ref`.

### The rule

1. **Before writing code**, read `agents/forecaster/laws/laws.md` and its `test-plan.md`, whole.
2. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md) (DRIFT-116 and DRIFT-117 are the pair).
3. **Answer the law-cycle question below** in the Law reading record.
4. **Write the Law reading record** (bottom of this file) **before** your first change.
5. **If a law contradicts this spec, STOP and report.**
6. The two forecaster tests cite `FORE-IDN-01` (both) and `FORE-OUT-05` (the agent test) in their
   docstrings. The four pack tests cite DL-327: no clause governs a pack's value.

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**No new guarantee; one amendment.** No file in `contracts/` changes and no clause is added. The
return leg starts to keep a promise `FORE-OUT-05` already makes, and `FORE-IDN-01`'s wording of
that leg ("LightGBM") is corrected to what scores it, exactly as the forecaster image chore did for
the sentiment leg (laws v1.13, DRIFT-116). So the law cycle is: v1.14, one Changelog line, the two
test-plan rows, DRIFT-117 to CORRECTED, the ledger and INDEX rows. **The rollup stays 30 / 57.** All
of it is written in Appendix B; apply it, do not reword it.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/forecaster/return_model.py`, `lightgbm_model.py`, `agent.py` | `agents/forecaster/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `FORE-IDN-01`, `FORE-OUT-05`; `PARAM` `return_model_ref` |
| `orchestration/packs/trading_tunables.json` | none binds a pack value; read [DL-282](../design-log.md) decision 8 and DL-327 | The pack is the configuration a full `up` applies, and a fidelity decision path |
| the two forecaster test files, `tests/test_tunables_pack_names_no_vendor.py` (new) | `docs/laws/conventions.md` | Module header; clause citations |

⚠️ **Two invariants.** (1) After this sprint a full `up` sends the three deliberator apps exactly
what it sends today (Appendix A): the pack edit removes lines the deploy script already drops. If
your change would make the script send anything else, stop and report. (2) The barrier leg, the
deployed loop and every other forecaster record are untouched: only the return leg's `Model` ref
changes, and only in what it names.

---

## Goal

At merge, a `forecast_return` call writes its `Model` node with the `ref` of the model that scored:
`fixed-fake-return` when no return model is injected (which is every path that exists), the injected
model's own `ref` otherwise, and `lightgbm-gbdt` for the LightGBM adapter. And
`orchestration/packs/trading_tunables.json` names no LLM vendor: the three `DELIBERATOR_LLM_PROVIDER`
lines are gone, the vendor is declared by `orchestration/packs/trading_llm.json` alone, and the pack's
own note says so.

## Why (context)

Both are records that say something false, each found and parked with its fix named.

- **DRIFT-117** (filed 2026-11-12, work-queue 142). The forecaster image chore made the sentiment leg
  record the model that scored (DRIFT-116) and left the return leg on purpose: `agent.py:119` still
  writes `settings.return_model_ref`, so the fixed fake's readings are labelled `lightgbm-gbdt`. No
  fleet record is wrong today, because the deployed loop never fires the leg, but the next record
  anyone reads from the local pipeline or a test lane would name a model that did not run.
- **Work-queue 109's last step.** Since S262 (`0.125.00`, deployed 2026-10-09) the vendor is one
  declared value in the LLM pack. The tunables pack kept its three lines saying `anthropic`, because
  it is a fidelity decision path and an edit restarted the clean-session count. The count read PASS on
  2026-10-27 and EXP-014 and EXP-022 are scored, so nothing holds the edit back. Until it is made, the
  one file an operator reads for "what does the fleet run with" says the opposite of what it runs.

### Measured, 2026-11-26 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| What the return leg records on `main` with no model injected | `Model lgbm-return-v1 ref='lightgbm-gbdt' kind='return'`, from the fixed fake's reading | *[measured]* the planner's `f1_return_record.py` on `main` `d0def753`, no `.env`: a forecaster built as `agents/forecaster/entrypoint.py:33` and `orchestration/local_pipeline.py:85` build it, the leg fired over 30 bars |
| Which paths inject a return model | none | *[read]* both constructors above pass no `return_model`; a repository search finds `LightGBMModel(` only in its own test |
| Return records on the live graph | 0: one `Model` node (`finbert-sentiment`, ref `ProsusAI/finbert`), 0 `ShadowPrediction` | *[measured 2026-11-26]* `live_model_nodes.py`, read-only, from the main checkout |
| Return records the local demonstrator writes | 0 (no `Model`, no `ShadowPrediction`) | *[measured]* `scripts/run_local.py`'s in-memory path, wrapped by `demo_writes_no_model.py` |
| What a full `up` of `main` sends the three deliberators | `DELIBERATOR_LLM_PROVIDER=openai` on all three, whatever the tunables pack says | *[measured]* the deploy script's own `Up`, every `az` call and credential a stand-in (the S290 runner); 20 lines, Appendix A |
| What a full `up` of the prototype sends | the same 20 lines | *[measured]* the same runner on `proto-s292` |
| What the live apps hold | the same 20 lines | *[measured 2026-11-26 02:12 UTC]* `az containerapp show` on each app, read-only |
| Why the pack's lines never reach an app | `Get-AgentEnv` drops a tunables line for any key the LLM pack names, then appends the pack's value; the master hands the vendor again at activation | *[read, whole function]* `infra/deploy-agents.ps1::Get-AgentEnv`; `agents/master/tests/test_candidate_activation.py` |
| What reads the tunables pack besides the deploy script | `scripts/replay_settings.py`, for scanner, analyst, provider, PM and execution only | *[read]* its `_APPS`; no deliberator |
| Existing tests that read the three lines | none | *[measured]* the prototype removes them and the whole suite passes |
| Whether `DELIBERATOR_EFFORT` is also dead in the pack | the master hands it at activation too, but removing it would make the next full `up` refuse | *[read]* `Assert-EnvPreserved` compares live env names with planned names; out of scope (DL-327) |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first.** Six tests under the names of the Test plan, in the three files it
   names, plus one required edit: `_RaisingReturnModel` in
   `agents/forecaster/tests/test_forecaster_return_agent.py` gains a class attribute
   `ref = "raising-test-model"` (without it `mypy` refuses the test, since the port now declares
   `ref`). Seven test cases fail on the unchanged tree and six pass.
2. **The change.** Apply Appendix B exactly: three forecaster files, the pack, the law cycle's five
   files, and the two version lines.
3. **The handback** at the bottom of this file, and this sprint's row of
   [`README.md`](README.md).

### Out of scope (do NOT build this sprint)

- **The settings fields `return_model_ref` and `model_ref`.** Neither is read after this sprint, but
  removing a field moves a `PARAM` row, and the sentiment twin was kept on purpose. Leave both.
- **`DELIBERATOR_EFFORT` in the pack.** It stays on all three entries (DL-327, ruled out).
- **`infra/deploy-agents.ps1`.** Its filter stays; an existing test holds it.
- **`orchestration/packs/trading_llm.json`.** It already declares the vendor.
- **Any other forecaster leg**, any other pack entry or key, `contracts/`, `kernel/`.
- **Any existing test** other than the `_RaisingReturnModel` attribute and the two additions named.
- **No ADR reversal.** An ADR is reversed by a new ADR, never by a sprint.

### The road not taken (LAW-06)

- **The fake's `ref` taken from the settings.** Rejected: that is the defect.
- **`LightGBMModel` takes its `ref` as a constructor argument, as `FinBERTModel` does.** Rejected:
  FinBERT loads the model its argument names; the booster's file says nothing about its family, so a
  free argument would only let a caller write any name. A class attribute equal to the setting's
  default keeps today's name for a real booster, and a test pins the two together.
- **Remove both settings fields now.** Rejected: see Out of scope; a cleanup of both, later.
- **Take `DELIBERATOR_EFFORT` out of the pack too.** Rejected: the next full `up` would refuse until
  run with `-DropEnv`, a live step for a line that states the first candidate's effort truthfully.
- **Delete the deploy script's filter, now that the pack names no vendor.** Rejected: it guards
  against a vendor line coming back.
- **Two sprints.** Rejected: two reviews and two version bumps for about a dozen lines.

---

## The design decisions — made, and recorded in DL-327

**Nothing is left for the builder to decide.** Do not add a design-log entry.

1. **D1** — `ReturnModel` declares `ref`; `FakeReturnModel.ref = "fixed-fake-return"`,
   `LightGBMModel.ref = "lightgbm-gbdt"`; `agent.py` writes `self._return_model.ref`. Laws v1.14.
2. **D2** — the three `DELIBERATOR_LLM_PROVIDER` lines leave the tunables pack; every other key stays.
3. **D3** — the pack's `_measured` gains one amendment (where the vendor lives; it supersedes the
   sentence of 2026-08-20).
4. **D4** — PATCH; the version lines are carried in Appendix B; `uv lock` is not run.
5. **D5** — no deploy at merge. The pack is a fidelity decision path, so the first deploy carrying the
   commit restarts the clean-session count; nothing waits on that count now.

---

## Blast radius — measured 2026-11-26

| What | Detail |
| --- | --- |
| Files changed | production: `agents/forecaster/agent.py` (169 lines, one line changes), `return_model.py` (42 → 46), `lightgbm_model.py` (41 → 43), `orchestration/packs/trading_tunables.json` (three lines out, `_measured` amended); laws: `agents/forecaster/laws/laws.md`, `test-plan.md`, `docs/laws/drift-register.md`, `ledger.md`, `INDEX.md`; version: `pyproject.toml`, `uv.lock` (one line each); tests: `test_forecaster_return_agent.py` (98 → 124 on the prototype), `test_forecaster_lightgbm.py` (24 → 39), `tests/test_tunables_pack_names_no_vendor.py` (new, 50); this spec; `docs/sprints/README.md` |
| Agents affected | forecaster (the return leg's record only). No agent imports another |
| Contract change? | no |
| Graph vocabulary change? | no: `Model.ref` and `Model.kind` exist |
| New env keys / tunables | none; three pack lines leave, and the deploy script already drops them |
| Deploy implication | none at merge. If deployed: an image-only retag (the forecaster image carries the code; the deployed loop never fires the leg, so no live record changes). The pack is a fidelity decision path (`scripts/replay_fidelity_git.py`, `DECISION_PATHS`): the first deploy carrying this commit restarts the clean-session count |
| Rollback | revert the commit. Nothing live changes at merge. A rollback `up` from an older commit sends the deliberators exactly what this one does (the older pack's lines are dropped the same way, since `s262`) |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Plant the failing tests first** (Test plan) and run them on the unchanged tree:
   `uv run --no-sync pytest agents/forecaster/tests/test_forecaster_return_agent.py agents/forecaster/tests/test_forecaster_lightgbm.py tests/test_tunables_pack_names_no_vendor.py --no-cov -q -p no:cacheprovider`.
   Paste the output: **7 failed, 6 passed** on the planner's prototype.
3. **Apply Appendix B**, exactly, and check the eleven blob ids it gives.
4. **Run the same command again: 13 passed.** Then the neighbours:
   `uv run --no-sync pytest agents/forecaster tests/test_deploy_llm_pack.py tests/test_deploy_tunables_pack.py tests/test_pack_debate_lanes.py --no-cov -q -p no:cacheprovider`: no failure.
5. **Prove the guards can fail (DL-70):** the fifteen breaks of Appendix C, one at a time, each red on
   the test named for it, each restored before the next.
6. **`make ci` green**, every step of the `ci:` target (count them from the `Makefile`),
   **redirected to a file, never piped**.
7. **Fill the handback sections** at the bottom of this file.

---

## Test plan

Under **exactly these names** (the planner's break script judges by them).

| # | Test | File | On the unchanged tree | Must prove |
| --- | --- | --- | --- | --- |
| A1 | 🎯 `test_return_model_record_names_the_scorer`, parametrized `injected` in `[False, True]` | `agents/forecaster/tests/test_forecaster_return_agent.py` | both cases fail | With `ForecasterSettings(return_model_ref="setting-is-not-the-scorer")`, 30 bars from `make_bars`, and either no return model or `FakeReturnModel(raw=0.05)` whose `ref` is set to `"x"`: after one `forecast_return` request, the `Model` node keyed `settings.return_model_id` has `ref` `"x"` (injected) or `"fixed-fake-return"` (not), `ref` differs from `settings.return_model_ref`, `kind` is `"return"`; the prediction's value is `squash(0.05, scale=0.05)` or `squash(0.0, scale=0.05)`; the sink holds no fault. Docstring cites `FORE-IDN-01 / FORE-OUT-05` |
| A2 | 🎯 `test_lightgbm_ref_names_the_algorithm_it_loads` | `agents/forecaster/tests/test_forecaster_lightgbm.py` | fails | With `importlib.import_module` monkeypatched to return one namespace whose `Booster(*, model_file)` records `model_file`: `LightGBMModel(model_path="m.txt")` records `["m.txt"]`, its `ref` is `"lightgbm-gbdt"` and equals `ForecasterSettings().return_model_ref`. Docstring cites `FORE-IDN-01` |
| A3 | 🎯 `test_no_tunables_entry_carries_the_vendor_key_of_its_app` | `tests/test_tunables_pack_names_no_vendor.py` (new) | fails | The LLM pack's `apps` map has 5 entries, and for each app the tunables pack's entry for it (or none) does not carry the key that map names |
| A4 | 🪤 `test_no_tunables_key_names_a_vendor` | the same | fails | The tunables pack's apps carry keys, and none ends in `_LLM_PROVIDER` |
| A5 | 🪤 `test_the_deliberators_keep_every_other_tunable` | the same | fails | Sorted, `deliberator-manager`'s keys are `DELIBERATOR_DEBATE_CONCURRENCY`, `DELIBERATOR_EFFORT`, `DELIBERATOR_REQUEST_TIMEOUT_SECONDS`; each debater's are `DELIBERATOR_EFFORT`, `DELIBERATOR_REQUEST_TIMEOUT_SECONDS` |
| A6 | `test_the_packs_note_records_the_move` | the same | fails | `_measured` contains `the three DELIBERATOR_LLM_PROVIDER lines`, `The vendor is changed in trading_llm.json, never here` and `DL-327` |

The new file reads the two packs as JSON, as `tests/test_deploy_llm_pack.py` does, and runs no
PowerShell. Its docstring declares `Agent: tooling`, a `Role:` and `External I/O: committed JSON only.`

---

## Success factors

- [ ] The eleven files of Appendix B carry its blob ids.
- [ ] A return `Model` node names the scorer: A1 both cases, A2.
- [ ] The tunables pack names no vendor and keeps every other key: A3 to A6.
- [ ] The six tests exist under the names given and pass; all seven cases were seen failing first.
- [ ] No other existing test changed except the one attribute; none fails.
- [ ] The law-cycle answer and the reading record are filled before the first change.
- [ ] Each of the fifteen breaks was planted, seen red on its named test, and restored.
- [ ] Every touched module is under 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage; a step the sandbox cannot run is named "not done".

---

## Traps

🪤 **Do not run `uv lock` or `uv sync`, in any form.** *[measured 2026-11-17, uv 0.8.14]* the lock was
written by a newer `uv`: offline it also moves `virtualenv` back, online it rewrites 54 lines. The lock
changes in **one line**, given in Appendix B, and `uv lock --check` accepts it.

🪤 **`_measured` is one line of 4,801 characters, and the ledger's and the law INDEX's forecaster
rows are lines of several thousand.** Do not retype them. Apply Appendix B with `git apply` and compare
the blob ids; a single different character changes one.

🪤 **`mypy` reads the tests.** The port now declares `ref`, so every class passed as a return model
needs one: `_RaisingReturnModel` is the only one (Scope 1).

🪤 **A2 constructs a `LightGBMModel` with no `lightgbm` installed.** The two lines after the import are
`# pragma: no cover`; the monkeypatch makes them run. Return the same namespace for every module name.

🪤 **A green suite proves little here.** No existing test fails with the old code or the new: only the
new tests and the breaks show the change.

🪤 **`ruff format` runs as a pre-commit hook.** A call that fits in 88 characters must sit on one line
(the prototype's first commit was refused for exactly that). Run `uv run --no-sync ruff format` on the
three test files before committing. No `# noqa`.

🪤 **Paste step lines and verdicts into the Closeout, not the whole `make ci` log.**

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150), tests included. No `# noqa`.
  📌 Prototype sizes: `test_forecaster_return_agent.py` **124**, `test_forecaster_lightgbm.py` **39**,
  `tests/test_tunables_pack_names_no_vendor.py` **50**, `agent.py` **169**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers in code. The two `ref` strings are identities, not tunables.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it, both from Appendix B.
- Secrets never through the worktree. The worktree has **no `.env`** and this sprint needs none.
  **State which tree you ran in.**

---

## Sequencing after merge (the planner's)

1. The planner re-measures: the eleven blobs against Appendix B; the planner's own test files run in
   place of the builder's; the break script against the builder's tests alone (15 breaks); the
   planner's own `make ci` (the dependency audit needs a network); the branch pushed;
   **`make gate-ran` exits 0** from the proving worktree, its SHA checked against `git rev-parse HEAD`;
   the open CodeQL alerts set-diffed against the baseline of 138.
2. Merge to `main`, tag. **Post-merge CodeQL** checked on `main`.
3. **F1, at no cost and read-only:** (a) on merged `main` the deploy script's own `Up`, every call a
   stand-in, prints the 20 lines the live apps hold, read the same hour (Appendix A); (b) on merged
   `main` the return leg fired on a forecaster built as the fleet builds it writes
   `ref='fixed-fake-return'` (`f1_return_record.py`; on `main` before, `'lightgbm-gbdt'`).
4. **No deploy.** Work-queue 142 closes at F1 (no fleet path fires the leg, so there is no F2);
   work-queue 109 closes at F1 too (no live value moves). DRIFT-117 reads CORRECTED from the merge.
5. The commit rides the next deploy; that deploy restarts the fidelity count and is recorded as doing so.

---

## Handover — paste this to Codex

```text
You are building Sprint 292 in the worktree ../ta-s292, on the branch
sprint-292-a-return-record-names-its-scorer-and-one-file-names-the-vendor. Never work on main.

Read docs/sprints/sprint-292-a-return-record-names-its-scorer-and-one-file-names-the-vendor.md,
whole, before anything else. It is the spec, and its bottom sections are your handback. Every
decision is made: Appendix B is the whole change to eleven files, and you write six tests.

In order:
1. Read agents/forecaster/laws/laws.md and test-plan.md, docs/laws/conventions.md and
   docs/laws/drift-register.md. Fill the Law reading record in the spec BEFORE any change. The
   law-cycle answer: no new guarantee, one amendment, written in Appendix B; do not reword it.
2. Write the six tests of the Test plan under exactly the names given, in the three files it
   names (one new: tests/test_tunables_pack_names_no_vendor.py, with a module docstring that
   declares Agent, Role and External I/O), and add ref = "raising-test-model" to
   _RaisingReturnModel in agents/forecaster/tests/test_forecaster_return_agent.py. Run
     uv run --no-sync pytest agents/forecaster/tests/test_forecaster_return_agent.py agents/forecaster/tests/test_forecaster_lightgbm.py tests/test_tunables_pack_names_no_vendor.py --no-cov -q -p no:cacheprovider
   on the unchanged production files and paste the output into the Closeout. Expected: 7 failed,
   6 passed.
3. Apply Appendix B: save its diff block to a file outside the repository's tracked files and run
   git apply on it. Then git hash-object on the eleven files must print the eleven blob ids
   Appendix B gives. Do NOT run uv lock or uv sync in any form.
4. Run the same pytest command again: 13 passed. Then
     uv run --no-sync pytest agents/forecaster tests/test_deploy_llm_pack.py tests/test_deploy_tunables_pack.py tests/test_pack_debate_lanes.py --no-cov -q -p no:cacheprovider
   No test may fail.
5. Plant the fifteen breaks of Appendix C one at a time. Each must go red on the test named for
   it. Restore each with git checkout of that file before the next (commit your work first, or
   keep a copy, so the restore returns your built file).
6. Run uv run --no-sync ruff format on the three test files, then make ci redirected to a file,
   and read the file. If a step cannot run in your sandbox (the dependency audit needs a
   network), say "not done" for that step and paste its lines.
7. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in this
   sprint's row of docs/sprints/README.md (the row's status cell must lead with BUILT). Commit on
   the branch if your sandbox lets you write the repository's git directory; if not, leave the
   tree uncommitted and say so.

DO NOT: run uv lock or uv sync; run infra/deploy-agents.ps1 or any az command; change any file
Appendix B does not name except the three test files, this spec and docs/sprints/README.md;
retype _measured or the long ledger and INDEX rows; change any other entry or key of the pack;
change any existing test beyond the one attribute; add a design-log entry; edit docs/STATE.md,
docs/work-queue.md or docs/design-log.md; add entries to .secrets.baseline; use noqa; paste a
whole make ci log into the spec; measure make ci through a pipe.

Traps: the long JSON and markdown lines (apply the diff, compare the blob ids); mypy needs ref
on _RaisingReturnModel; A2 runs the LightGBM constructor with a monkeypatched importlib; no
existing test fails with the old code or the new, so a green suite alone proves nothing; ruff
format is a pre-commit hook and wants a call that fits in 88 characters on one line.

Two tiers of trouble. A wrong path, count or command in this spec whose intent is plain: correct
it, go on, and record it in the Return notes. A blob id that does not match after a clean git
apply, a law that contradicts the spec, an existing test that fails, or a break that stays
green: STOP and report. State anything not done as "not done" or "verified failing". Never write
a Result for work you have not done.

Handback checklist, each answered in the Closeout:
 1. Law reading record filled before the first change; the law-cycle answer with its reason.
 2. Red output of step 2 pasted (7 failed, 6 passed).
 3. The eleven blob ids after git apply, as printed.
 4. Green output of step 4 pasted (13 passed; the neighbours pass).
 5. git diff --stat against the base: exactly Appendix B's eleven files, the three test files,
    this spec and docs/sprints/README.md.
 6. The fifteen breaks, one line each: the test that went red, and restored.
 7. The line counts of the three test files.
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
| *to fill* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *to fill*

**Contradictions found between a law and this spec:** *to fill*

**Laws found silent where a decision was needed:** *to fill*

**Clauses that were ⬜ and are now proven:** *to fill*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | | | | |
| A2 | | | | |
| A3 | | | | |
| A4 | | | | |
| A5 | | | | |
| A6 | | | | |

**Tests added beyond the plan:** *to fill*

---

## Closeout — evidence

**Status:** *to fill*

**Tree the proofs ran in (and `.env` present?):** *to fill*

**Result:** *to fill*

**Files changed:** *to fill*

**Design decisions:** recorded as [`DL-327`](../design-log.md) by the planner; none left to the builder.

**Proof — the red run first:**

```text
to fill
```

**Proof — the green run:**

```text
to fill
```

**Guards planted:** *to fill*

**Module line counts:** *to fill*

**`make ci`:** *to fill*

**`make gate-ran`:** the planner's, after the push.

**Not met / verified failing:** *to fill*

---

## Return notes

- *to fill*

---

## Appendix A — what the three apps hold live, and what `Up` sends before and after

Read 2026-11-26 02:12 UTC from the live apps, and printed by the deploy script's own `Up`, every `az`
call a stand-in, on `main` (`d0def753`) and on the prototype. The three outputs are equal, line for line:

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

## Appendix B — the change, measured on the planner's prototype

Save the block below to a file and run `git apply <file>` from the worktree's root. It changes three
forecaster files, the tunables pack, the law cycle's five files, and one line each of
`pyproject.toml` and `uv.lock`. The test files are yours to write (Test plan).

```diff
diff --git a/agents/forecaster/agent.py b/agents/forecaster/agent.py
index 301c5c74..150ee807 100644
--- a/agents/forecaster/agent.py
+++ b/agents/forecaster/agent.py
@@ -118,3 +118,3 @@ class ForecasterAgent(AgentBase):
             model_id=self._settings.return_model_id,
-            model_ref=self._settings.return_model_ref,
+            model_ref=self._return_model.ref,
             subject_kind=forecast.subject_kind,
diff --git a/agents/forecaster/laws/laws.md b/agents/forecaster/laws/laws.md
index 17cbe782..3771995f 100644
--- a/agents/forecaster/laws/laws.md
+++ b/agents/forecaster/laws/laws.md
@@ -2,3 +2,3 @@

-**Prefix:** `FORE` · **status:** LOCKED v1.13 · **Owner:** Yury Gurevich
+**Prefix:** `FORE` · **status:** LOCKED v1.14 · **Owner:** Yury Gurevich

@@ -17,4 +17,6 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   scores with the neutral fake, and the deployed loop does not fire it, `FORE-TRG-01`;
-  FinBERT is an offline research scorer, EXP-024), the return model (`forecast_return`,
-  LightGBM), the approved-factor shadow (`forecast_factor`), and the barrier model
+  FinBERT is an offline research scorer, EXP-024), the injected return model
+  (`forecast_return`; no fleet path injects one, so the leg scores with the fixed fake, and
+  the deployed loop does not fire it, `FORE-TRG-01`; LightGBM is the adapter for a trained
+  booster, which no fleet path builds), the approved-factor shadow (`forecast_factor`), and the barrier model
   (`forecast_barrier`, EXP-018's GARCH barrier claim, `FORE-OUT-07`). Each leg returns a
@@ -490 +492,5 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   corrected; no contracts change, no new clause; whole-purpose partial proofs stay gray.
+- v1.14 — S292 / work-queue 142 / DL-327 (2026-11-26): FORE-IDN-01 names the injected
+  return model and its fixed-fake fallback; LightGBM is an adapter no fleet path builds. A
+  return `Model` node now names the model that scored, not `return_model_ref`. DRIFT-117
+  corrected; no contracts change, no new clause; 30 / 57 unchanged.
diff --git a/agents/forecaster/laws/test-plan.md b/agents/forecaster/laws/test-plan.md
index d336793c..7601d966 100644
--- a/agents/forecaster/laws/test-plan.md
+++ b/agents/forecaster/laws/test-plan.md
@@ -4,3 +4,3 @@
 | --- | --- | --- |
-| FORE-IDN-01 | ⬜ | four-leg purpose statement (injected sentiment or neutral fake, return, factor, barrier, each `shadow=True`); partial: `test_sentiment_model_record_names_the_scorer`, `tests/test_served_agent_images.py::test_barrier_extra_contains_arch_without_the_offline_models`; per-leg duties are proven by `FORE-OUT-01/02/07` and the factor test; no single boundary proof of the whole purpose; _tbd_ |
+| FORE-IDN-01 | ⬜ | four-leg purpose statement (injected sentiment or neutral fake, injected return or fixed fake, factor, barrier, each `shadow=True`); partial: `test_sentiment_model_record_names_the_scorer`, `test_return_model_record_names_the_scorer`, `test_lightgbm_ref_names_the_algorithm_it_loads`, `tests/test_served_agent_images.py::test_barrier_extra_contains_arch_without_the_offline_models`; per-leg duties are proven by `FORE-OUT-01/02/07` and the factor test; no single boundary proof of the whole purpose; _tbd_ |
 | FORE-IDN-02 | 🟩 | `test_a_successful_call_writes_one_complete_claim`, `test_the_claim_passes_the_packs_vocabulary_guard`, `test_a_settlement_records_every_field_the_ledger_needs`, `test_the_settlement_passes_the_packs_vocabulary_guard` |
@@ -19,3 +19,3 @@
 | FORE-OUT-04 | 🟩 | `test_scorecard_is_never_promotion_eligible`, `test_scorecard_reports_samples_and_never_promotes`, `test_generic_scorecard_covers_factor_predictions_and_never_promotes`, `test_the_scorecard_reports_the_ledger_as_exp018_scores_it`, `test_an_empty_ledger_reports_counts_and_no_scores` |
-| FORE-OUT-05 | 🟩 | `test_forecast_persists_and_returns_a_shadow_prediction`, `test_sentiment_model_record_names_the_scorer` |
+| FORE-OUT-05 | 🟩 | `test_forecast_persists_and_returns_a_shadow_prediction`, `test_sentiment_model_record_names_the_scorer`, `test_return_model_record_names_the_scorer` |
 | FORE-OUT-06 | 🟩 | `test_forecast_with_no_news_is_neutral_zero_confidence` |
diff --git a/agents/forecaster/lightgbm_model.py b/agents/forecaster/lightgbm_model.py
index 1616f8b3..6c77b7fc 100644
--- a/agents/forecaster/lightgbm_model.py
+++ b/agents/forecaster/lightgbm_model.py
@@ -26,2 +26,4 @@ class LightGBMModel:

+    ref: str = "lightgbm-gbdt"
+
     def __init__(self, *, model_path: str) -> None:
diff --git a/agents/forecaster/return_model.py b/agents/forecaster/return_model.py
index 8017f66e..73fea2ea 100644
--- a/agents/forecaster/return_model.py
+++ b/agents/forecaster/return_model.py
@@ -21,2 +21,4 @@ class ReturnModel(Protocol):

+    ref: str
+
     def predict(self, features: FeatureRow) -> float:
@@ -29,2 +31,4 @@ class FakeReturnModel:

+    ref: str = "fixed-fake-return"
+
     def __init__(
diff --git a/docs/laws/INDEX.md b/docs/laws/INDEX.md
index 23107d0d..1bcf5452 100644
--- a/docs/laws/INDEX.md
+++ b/docs/laws/INDEX.md
@@ -48,3 +48,3 @@ Each agent's law files live at `agents/<name>/laws/`:
 | reporter | ✅ LOCKED v1.5 (S253, DL-262, DL-263) | 26 / 43 | S253 rewrites `RPT-OUT-02` (book counts from the broker's fills in the run's window, outcomes since the inception; DRIFT-099), amends `RPT-IN-01` and `RPT-NEV-03` (DRIFT-101), and adds and proves `RPT-IDM-04`; S251 names the run's own benchmark lineage in `RPT-OUT-07` (DRIFT-087) and the graph-pull trigger in `RPT-TRG-02` (DRIFT-086); v1.3 (DL-224) latest-per-date snapshot; S226 adds benchmark-relative `performance_metrics`, as-of bounded graph reads, contained performance failure, and backward-compatible snapshots; S205 rewrites `RPT-TYP-01`; S156 removed orphan `RPT-OBS-03`; S204 gives every clause a row and makes rowless clauses a hard gate |
-| forecaster | ✅ LOCKED v1.13 (chore-forecaster-image-without-torch, work-queue 141 A) | 30 / 57 | The forecaster image chore (DRIFT-116) amends `FORE-IDN-01` and `FORE-PERF-01`: the sentiment leg scores with the injected model or the neutral fake, FinBERT is an offline research scorer, the image installs the `barrier` extra only, a sentiment `Model` node names the scorer; partial proofs, 30 / 57 unchanged. S288 / DL-312: each claim states, from the paths its probabilities were counted on, its expected return, the tenth close's 5th percentile and each barrier's median session, and its settlement the realised return (`FORE-OUT-11`); the scorecard's return scores (`FORE-OUT-12`); 28 / 55 → 30 / 57. Before: S286 / DL-310: a barrier claim on every held name, its live stop and declared target from the claim's close (`FORE-OUT-09`), held claims scored apart (`FORE-OUT-10`), one history read per run and open-claims-only settlement (`FORE-PERF-04`); 25 / 52 → 28 / 55. Before: S252 / DL-261: `FORE-TRG-01` bounds both current-run finders before props are read; local calls stay unbounded; 25 / 52 unchanged. S251 names the four legs (`FORE-IDN-01`), one node per prediction (`FORE-OBS-01`; DRIFT-081) and the shadow scorecards' subject (`FORE-IDM-03`; DRIFT-083); S243 amends and re-proves `FORE-FAIL-04` (a designed refusal is a `warning`, a missing input an `error`); S241 adds and proves `FORE-OUT-08`, `FORE-IDM-05`, `FORE-FAIL-05` (the settlement of each barrier claim and `barrier_scorecard`) and amends `FORE-IDN-02`/`TRG-01`/`OUT-03`; the S239 second follow-up (D10) re-words the barrier clauses for the provider-written history; the S239 follow-up amends `FORE-TRG-01`/`FORE-TRG-02` (graph-pull trigger; the deployed loop fires `forecast_barrier` only); S239 amends `FORE-IDN-02` and adds `FORE-IN-07`, `FORE-OUT-07`, `FORE-IDM-04`, `FORE-FAIL-04` (the barrier claim); DL-203 reconciled `PARAM`; S205 proved `FORE-TYP-01`; counters are clauses proven / clauses declared |
+| forecaster | ✅ LOCKED v1.14 (S292, work-queue 142) | 30 / 57 | S292 (DRIFT-117) amends `FORE-IDN-01`: the return leg scores with the injected model or the fixed fake, and a return `Model` node names the scorer; partial proof, 30 / 57 unchanged. The forecaster image chore (DRIFT-116) amends `FORE-IDN-01` and `FORE-PERF-01`: the sentiment leg scores with the injected model or the neutral fake, FinBERT is an offline research scorer, the image installs the `barrier` extra only, a sentiment `Model` node names the scorer; partial proofs, 30 / 57 unchanged. S288 / DL-312: each claim states, from the paths its probabilities were counted on, its expected return, the tenth close's 5th percentile and each barrier's median session, and its settlement the realised return (`FORE-OUT-11`); the scorecard's return scores (`FORE-OUT-12`); 28 / 55 → 30 / 57. Before: S286 / DL-310: a barrier claim on every held name, its live stop and declared target from the claim's close (`FORE-OUT-09`), held claims scored apart (`FORE-OUT-10`), one history read per run and open-claims-only settlement (`FORE-PERF-04`); 25 / 52 → 28 / 55. Before: S252 / DL-261: `FORE-TRG-01` bounds both current-run finders before props are read; local calls stay unbounded; 25 / 52 unchanged. S251 names the four legs (`FORE-IDN-01`), one node per prediction (`FORE-OBS-01`; DRIFT-081) and the shadow scorecards' subject (`FORE-IDM-03`; DRIFT-083); S243 amends and re-proves `FORE-FAIL-04` (a designed refusal is a `warning`, a missing input an `error`); S241 adds and proves `FORE-OUT-08`, `FORE-IDM-05`, `FORE-FAIL-05` (the settlement of each barrier claim and `barrier_scorecard`) and amends `FORE-IDN-02`/`TRG-01`/`OUT-03`; the S239 second follow-up (D10) re-words the barrier clauses for the provider-written history; the S239 follow-up amends `FORE-TRG-01`/`FORE-TRG-02` (graph-pull trigger; the deployed loop fires `forecast_barrier` only); S239 amends `FORE-IDN-02` and adds `FORE-IN-07`, `FORE-OUT-07`, `FORE-IDM-04`, `FORE-FAIL-04` (the barrier claim); DL-203 reconciled `PARAM`; S205 proved `FORE-TYP-01`; counters are clauses proven / clauses declared |
 | operator | ✅ LOCKED v1.10 (S269, DL-292) | 20 / 51 | S269 (DL-292) rewords and re-proves `OPR-FAIL-02`: only text, a number or a boolean is a value; `null`, lists and objects are omitted from required and optional parameters, so missing required values are refused with the existing sentence and audit, while scalar text and blank-text behavior are unchanged; DRIFT-112 corrected; no clause added; before that S268 (DL-290) rewords and re-proves `OPR-FAIL-02`: an intent of no known family, or lacking a parameter its family requires under any accepted name, is refused before its audit, which reads `refused`, and no `Intent` is written; the prompt states each family's parameter names; DRIFT-109 corrected; no clause added; before that S265 (DL-286) rewords and re-proves `OPR-FAIL-01`: failed requests are audited on both capabilities, one operator fault and one plain reason, no grammar or error text in graph; malformed JSON is a fault-free refusal; DRIFT-107/108 corrected; no clause added; before that S264 (DL-285) re-proves `OPR-STA-03` for vendor stop reasons and billed counts on both reply paths and adds/proves `OPR-FAIL-04` for audited, fault-free cut-offs with one sentence and explicit grammar preserved; DRIFT-106 corrected; before that S263 (DL-284) amends and re-proves `OPR-DEP-01` for provider effort resolution and pre-call model-family refusal; PARAM effort and CAP reconciled; before that S262 (DL-282) amends and re-proves `OPR-DEP-01` for the selected vendor, model resolution and no fallback; PARAM reconciled; before that S256 (DL-272) rewrites and proves `OPR-IDM-02`: duplicate commands share the audit and intent, but every model call has its own ledger row; DRIFT-104 corrected; S222 proves `OPR-SEC-01` key containment and `OPR-DEP-01` Anthropic-only dependency; S205 rewrites and proves `OPR-TYP-01`; counters are clauses proven / clauses declared |
diff --git a/docs/laws/drift-register.md b/docs/laws/drift-register.md
index 43db0327..8a24adf9 100644
--- a/docs/laws/drift-register.md
+++ b/docs/laws/drift-register.md
@@ -207,3 +207,3 @@ clause is **false in code**, not merely untested — the rest were demoted in ea
 | DRIFT-116 | `FORE-IDN-01` (the sentiment leg is "FinBERT-class"), `FORE-PERF-01` ("FinBERT model is injected") | The sentiment leg scores headlines with an injected FinBERT. | *[read 2026-10-26]* No caller injects a model: `agents/forecaster/entrypoint.py::build_served_bus` and `orchestration/local_pipeline.py:85` build `ForecasterAgent` without one, so the leg runs `FakeSentimentModel` (neutral 0.5 for every headline); `FinBERTModel` is built only in its own tests. The deployed loop never fires the leg (`FORE-TRG-01`); the local pipeline does, and its `Model` node records `ref` `ProsusAI/finbert` for the fake's readings. | stale-law | **CORRECTED — [chore-forecaster-image-without-torch](../sprints/chore-forecaster-image-without-torch.md), option A authorized 2026-10-26, built 2026-11-12 on its branch: laws v1.13, barrier-only image selection and sentiment records name the scorer. Merge and image closure proof are separate closeout gates.** Was: OPEN — [work-queue 141](../work-queue.md). |
-| DRIFT-117 | `FORE-IDN-01` (the return model, `forecast_return`, LightGBM) | The return leg's `Model` node names the model that produced its readings. | *[read 2026-11-12, Codex's return note on the forecaster image chore, confirmed from source]* `ForecasterAgent` falls back to `FakeReturnModel` when no return model is injected, and `agents/forecaster/agent.py:119` records `settings.return_model_ref` (default `lightgbm-gbdt`) whatever model scored, so the local pipeline labels the fake's return readings `lightgbm-gbdt`. The deployed loop never fires the leg (`FORE-TRG-01`). The sentiment leg's twin, DRIFT-116, was corrected by the chore; the spec left this one deliberately untouched. | stale-record | **OPEN** — the fix is the chore's pattern (the model declares its `ref`, the agent writes it); S, no decision path. Work-queue 142 since 2026-11-13. |
+| DRIFT-117 | `FORE-IDN-01` (the return model, `forecast_return`, LightGBM) | The return leg's `Model` node names the model that produced its readings. | *[read 2026-11-12, Codex's return note on the forecaster image chore, confirmed from source]* `ForecasterAgent` falls back to `FakeReturnModel` when no return model is injected, and `agents/forecaster/agent.py:119` records `settings.return_model_ref` (default `lightgbm-gbdt`) whatever model scored, so the local pipeline labels the fake's return readings `lightgbm-gbdt`. The deployed loop never fires the leg (`FORE-TRG-01`). The sentiment leg's twin, DRIFT-116, was corrected by the chore; the spec left this one deliberately untouched. | stale-record | **CORRECTED** by S292 (DL-327, laws v1.14): `ReturnModel` declares `ref` (`FakeReturnModel` `fixed-fake-return`, `LightGBMModel` `lightgbm-gbdt`) and `agent.py` writes the scorer's own; `test_return_model_record_names_the_scorer` reads the node with and without an injected model. |
 | DRIFT-118 | `DLIB-NEV-08` | Never renders a `PASSED` verdict for a comparison no agent enforces. | *[measured 2026-11-22]* Since the reward-to-risk floor went to 0 (ADR-0027 Correction 2, 2026-09-17) every packet printed `PM gate outcome: name=reward_risk … threshold_reward_risk_ratio=0 -> PASSED (… comparison=DISCLOSURE_ONLY)`. `test_no_rendered_verdict_lacks_an_enforcing_check` accepts any PM gate's name, so it stayed green. All 43 debates with a stored packet (2026-10-01 to 2026-11-20) were ruled `revise` with a rationale naming that figure ([DL-326](../design-log.md)). | code-drift | **CORRECTED** by S291: the ratio prints as a disclosed figure with no threshold and no verdict, and a test reads the exact line. |
diff --git a/docs/laws/ledger.md b/docs/laws/ledger.md
index 3536d77c..8e1273bb 100644
--- a/docs/laws/ledger.md
+++ b/docs/laws/ledger.md
@@ -40,3 +40,3 @@ and torn down to zero. Historical Neo4j rows remain valid evidence for the pre-S
 | analyst | ✅ v1.12 (LOCKED) | 31 / 54 | 🟨 partial — **31 of 54 clauses proven** after S284 (DL-308) adds and proves `ANLZ-OUT-11`: the lexicon sentiment pillar scores only headlines that name the ticker's company, no pillar below two; before that S279 (DL-302) adds and proves `ANLZ-PERF-02`: the held-stop read shares one lazy Fill read across the book and retains each lineage width, no decision changes; before that S259 (DL-276) reconciles `PARAM` only (the bounds of `scaled_stop_atr_multiplier` follow the code; no clause moves) and S255 (DL-269) adds and proves `ANLZ-OUT-10`: each scored recommendation records its constants and actual mean order; before that S253 (DL-263) adds and proves `ANLZ-IN-05`: a candidate under `required_history_bars` is scored on the indicators its bars allow, each missing core indicator visible as `<metric>_missing_bars`, and only fewer than `min_history_bars` rejects (DRIFT-096); before that S251 (DL-260) adds and proves `ANLZ-OUT-09`: a held position's stop check reads the shared stop-width resolver, a close at or below the decided stop is a forced `stop` sell, a live broker stop owns the exit, an unreadable book is a fault (DRIFT-074); `ANLZ-TRG-02` names the graph-pull trigger (DRIFT-086); before that S211 adds and proves `ANLZ-OBS-06`: decision-time favourable-excursion target evidence is measured from prior settled windows, serialized, and missing evidence rejects instead of falling back to a constant target; S205 rewrites `ANLZ-TYP-01` into required fields without moving the count; S198 adds and proves `ANLZ-OBS-05`; S186 adds and proves `ANLZ-OBS-04`; S204 gives every clause a row and promotes missing rows to a hard gate · S152 declared 3 new clauses (43→46) · S169-sweep demoted `ANLZ-OBS-01` |
-| forecaster | ✅ v1.13 (LOCKED) | 30 / 57 | 🟨 partial — **30 of 57 clauses proven**; the forecaster image chore (work-queue 141 A, DRIFT-116) amends `FORE-IDN-01` and `FORE-PERF-01` to say the sentiment leg scores with the injected model or the neutral fake and FinBERT is an offline research scorer, with partial proofs on both (the image installs the `barrier` extra only; a sentiment `Model` node names the scorer); before that, after S288 (DL-312): each claim states its return and its settlement what happened (`FORE-OUT-11`), the scorecard's return scores (`FORE-OUT-12`), both new and green; before that, 28 / 55 after S286 (DL-310): a barrier claim on every held name (`FORE-OUT-09`, `FORE-OUT-10`, `FORE-PERF-04` new and green); before that, 25 / 52 after S252 (DL-261): `FORE-TRG-01` bounds both current-run finders before props are read; local calls stay unbounded; 25 / 52 unchanged; v1.9 (S251, DL-260) names the four legs in `FORE-IDN-01`, one recorded node per prediction in `FORE-OBS-01` (DRIFT-081) and the three shadow scorecards in `FORE-IDM-03` (DRIFT-083), all still gray, count unchanged; v1.8 (S243, DL-247) amends and re-proves `FORE-FAIL-04`: a designed "no claim" records a `warning`, a missing or broken input an `error` (DRIFT-089), count unchanged; after S241 (DL-243) adds and proves `FORE-OUT-08` (each claim settled once by EXP-018's rule from a provider-written `MarketData`; `barrier_scorecard` over EXP-018's fixed climatology), `FORE-IDM-05` (settled once, one pass per run) and `FORE-FAIL-05` (void with a named reason, never a false outcome), and amends and re-proves `FORE-IDN-02`/`TRG-01`/`OUT-03`; v1.6 (S239, DL-241 D10) re-words `FORE-IN-07`/`TRG-01`/`OUT-07`/`IDM-04`/`FAIL-04`/`NEV-04` for the provider-written history, count unchanged; before that the S239 follow-up amends and re-proves `FORE-TRG-01`/`FORE-TRG-02` (the deployed graph-pull loop fires `forecast_barrier` only; count unchanged); S239 amends `FORE-IDN-02` and adds `FORE-IN-07`, `FORE-OUT-07`, `FORE-IDM-04`, `FORE-FAIL-04` (the barrier claim), each proven; 27 have a gray row |
+| forecaster | ✅ v1.14 (LOCKED) | 30 / 57 | 🟨 partial — **30 of 57 clauses proven**; S292 (work-queue 142, DRIFT-117) amends `FORE-IDN-01` to say the return leg scores with the injected model or the fixed fake and a return `Model` node names the scorer, a partial proof, count unchanged; before that, the forecaster image chore (work-queue 141 A, DRIFT-116) amends `FORE-IDN-01` and `FORE-PERF-01` to say the sentiment leg scores with the injected model or the neutral fake and FinBERT is an offline research scorer, with partial proofs on both (the image installs the `barrier` extra only; a sentiment `Model` node names the scorer); before that, after S288 (DL-312): each claim states its return and its settlement what happened (`FORE-OUT-11`), the scorecard's return scores (`FORE-OUT-12`), both new and green; before that, 28 / 55 after S286 (DL-310): a barrier claim on every held name (`FORE-OUT-09`, `FORE-OUT-10`, `FORE-PERF-04` new and green); before that, 25 / 52 after S252 (DL-261): `FORE-TRG-01` bounds both current-run finders before props are read; local calls stay unbounded; 25 / 52 unchanged; v1.9 (S251, DL-260) names the four legs in `FORE-IDN-01`, one recorded node per prediction in `FORE-OBS-01` (DRIFT-081) and the three shadow scorecards in `FORE-IDM-03` (DRIFT-083), all still gray, count unchanged; v1.8 (S243, DL-247) amends and re-proves `FORE-FAIL-04`: a designed "no claim" records a `warning`, a missing or broken input an `error` (DRIFT-089), count unchanged; after S241 (DL-243) adds and proves `FORE-OUT-08` (each claim settled once by EXP-018's rule from a provider-written `MarketData`; `barrier_scorecard` over EXP-018's fixed climatology), `FORE-IDM-05` (settled once, one pass per run) and `FORE-FAIL-05` (void with a named reason, never a false outcome), and amends and re-proves `FORE-IDN-02`/`TRG-01`/`OUT-03`; v1.6 (S239, DL-241 D10) re-words `FORE-IN-07`/`TRG-01`/`OUT-07`/`IDM-04`/`FAIL-04`/`NEV-04` for the provider-written history, count unchanged; before that the S239 follow-up amends and re-proves `FORE-TRG-01`/`FORE-TRG-02` (the deployed graph-pull loop fires `forecast_barrier` only; count unchanged); S239 amends `FORE-IDN-02` and adds `FORE-IN-07`, `FORE-OUT-07`, `FORE-IDM-04`, `FORE-FAIL-04` (the barrier claim), each proven; 27 have a gray row |
 | portfolio_manager | ✅ v1 (LOCKED, amended **v1.12**) | 33 / 51 | 🟨 partial — **33 of 51 clauses proven** after S259 (DL-276) reconciles `PARAM` only (the bounds of six rows follow the code; no clause moves) and S251 (DL-260) narrows `PM-OBS-01`/`PM-OUT-06`/`PM-STA-04` to what `PMRun` and `OrderIntentResult` carry (the `portfolio_state_snapshot` promise withdrawn, DRIFT-039; `PM-STA-04` now green), makes `PM-OBS-04` per candidate (DRIFT-065), uses the emitted reason strings in `PM-OUT-03` (DRIFT-037), names the graph-pull trigger in `PM-TRG-02` (DRIFT-086) and narrows `PM-TYP-03`'s version sentence (DRIFT-060); DRIFT-098 filed for `PM-OUT-01`/`PM-TYP-03`; before that S240 adds and proves `PM-IN-05`: a run weighs each held ticker once at its own snapshot mark (adoption mark, then cost, as fallbacks) and a resumed run reads the snapshot of the run it resumes, closing DRIFT-079; `PM-IDN-01` stays gray (current-state conjunct proven, the whole-purpose boundary proof still owed); S220 amends and re-proves `PM-NEV-08` / `PM-OBS-03`: correlated issuers contribute on the ADR-0030 `0.50..0.90` ramp and gate detail renders the applied weights; S211 adds and proves `PM-OBS-05`: reward-risk now compares measured target evidence against stop risk, varies across measured profiles, and rejects measured upside below measured downside at the configured floor; S210 amends `PM-NEV-06`/`PM-NEV-08`/`PM-NEV-09` so concentration ratios use deployed capital and deployment-floor evidence is explicit without moving the count; S208 declares and proves `PM-OBS-04`; S197 declared and proved `PM-OBS-03`; S184 made PM-NEV-07/08/09 green and closed the v1.3 widened PM-NEV-06 and PM-TYP-03 rows |
diff --git a/orchestration/packs/trading_tunables.json b/orchestration/packs/trading_tunables.json
index d276a860..0f5fa1e8 100644
--- a/orchestration/packs/trading_tunables.json
+++ b/orchestration/packs/trading_tunables.json
@@ -2,3 +2,3 @@
   "_comment": "Operator-set agent tunables the deploy must carry (DL-100 / S169). Mechanism lives in infra/deploy-agents.ps1; these names and values are trading-pack data (ADR-0012). A full `up` REPLACES each app's env set, so a tunable that lives only as live cluster state is silently reverted to its code default with a green [OK]. This file is that single source of truth. Values are strings because container env vars are strings. Secrets never appear here - they arrive as secretrefs from Key Vault via master (DL-07).",
-  "_measured": "Snapshot of the live fleet read on 2026-08-14 from Azure Container Apps RG trading-agents. STAGED 2026-08-20: DELIBERATOR_LLM_PROVIDER openai->anthropic on all three deliberators (DL-99 operator switch). The three *_MODEL vars are deliberately empty, so this resolves the Anthropic adapter default claude-opus-5. NOT YET APPLIED LIVE - the Anthropic key is blocked by an operator-set spend limit; live env still reads openai until that limit is raised. Both providers are currently non-functional, so the divergence degrades nothing. Amended 2026-08-19 (DL-116): grace 900->1800 and deliberator request timeout 60->120, measured off sched-2026-08-19 (debate span ~990s vs 900s grace; LLM tail 65.3/59.3/58.2s vs a 60s ceiling). Amended 2026-09-04 (S172 merge): DELIBERATOR_DEBATE_CONCURRENCY ships at 1, not the code default of 4. K=1 is the deployed status quo; K>1 measured 1.78x of a possible 4x and, on one of two runs, dead-lettered 6 peer replies with 2 of 15 orders failing open, so the fan-out merges as an available dial rather than as proven behaviour. Raising it is a deliberate edit here plus an `up`. Amended 2026-09-05 (S198, operator decision): ANALYST_STOP_TARGET_MODE flat->scaled, promoting the S150 challenger (ADR-0013 / DL-77). Measured first on the live graph over 269 recorded recommendations - scaled stops span 3.00/5.45/8.00 pct against a flat 5.00/5.00/5.00, and the reward-risk pass rate is 100 pct in BOTH modes, so DL-77's named trap (widen the stop, silently stop trading AMD/MRVL/HPE) does not bite on this book. The touch-rate half could not be measured at all - stop_target_observed_drawdown_pct had no producer - so S198 ships the recorder in the same change: the flip is auditable on our own trades from its first night, not only against DL-77's external 2026-04 backtest. Amended 2026-09-13 (operator decision, work-queue item 47 / [DL-76]): EXECUTION_ORDER_PRICE_TOLERANCE_MODE flat->scaled, promoting the S149 challenger. Promoted on DL-76's EXTERNAL measurement (60 sessions of real overnight gaps to 2026-05-01: a flat 50 bps refuses 35 pct of buys and 23 pct of sells blended, and the distribution is the finding - SCHW 25 pct against AMD 52 pct, so one number encodes two different policies), NOT on own-book evidence, because own-book evidence was structurally uncollectable while the narrower band was the applied one: compare_order_tolerances reported flat and scaled identical at 0.00 pct drop over 170 orders, correctly, because scaled is wider on 170 of 170 (75-250 bps against a fixed 50) so every order the flat band accepted the scaled band also accepts. The flip inverts that and is what makes the comparison informative for the first time - with the wider band applied, an order filling above the flat limit is an order flat would have refused, which is DL-76's refusal rate measured on our own book. Operator chose this over closing the item as decided-by-design. Amended 2026-11-17 (work-queue 113, DL-325; the operator's decisions of 2026-10-08 and 2026-10-09, DL-274 D4 and DL-277 amendment 2): on deliberator-manager DELIBERATOR_DEBATE_CONCURRENCY 1->3 and DELIBERATOR_REQUEST_TIMEOUT_SECONDS 120->240. Both were live settings on the fleet from those dates, held out of this file only by the fidelity count (PASS 2026-10-27), so a full up would have put one lane and the 120 s wait back. The deploy script gives each debater as many replicas as the lane count, so the 3 is also each debater's replicas in the nightly window. Measured on the live graph 2026-11-17: 27 nightly debate records since 2026-10-09, 0 orders failed open, 0 orphaned replies; seven buys were debated in 662 s on 2026-10-26, where one debate alone took 217 to 347 s on its own nights against execution's 1800 s. The two debaters keep 120: only the manager makes a peer request. This supersedes the 2026-09-04 sentence above that says the dial ships at 1.",
+  "_measured": "Snapshot of the live fleet read on 2026-08-14 from Azure Container Apps RG trading-agents. STAGED 2026-08-20: DELIBERATOR_LLM_PROVIDER openai->anthropic on all three deliberators (DL-99 operator switch). The three *_MODEL vars are deliberately empty, so this resolves the Anthropic adapter default claude-opus-5. NOT YET APPLIED LIVE - the Anthropic key is blocked by an operator-set spend limit; live env still reads openai until that limit is raised. Both providers are currently non-functional, so the divergence degrades nothing. Amended 2026-08-19 (DL-116): grace 900->1800 and deliberator request timeout 60->120, measured off sched-2026-08-19 (debate span ~990s vs 900s grace; LLM tail 65.3/59.3/58.2s vs a 60s ceiling). Amended 2026-09-04 (S172 merge): DELIBERATOR_DEBATE_CONCURRENCY ships at 1, not the code default of 4. K=1 is the deployed status quo; K>1 measured 1.78x of a possible 4x and, on one of two runs, dead-lettered 6 peer replies with 2 of 15 orders failing open, so the fan-out merges as an available dial rather than as proven behaviour. Raising it is a deliberate edit here plus an `up`. Amended 2026-09-05 (S198, operator decision): ANALYST_STOP_TARGET_MODE flat->scaled, promoting the S150 challenger (ADR-0013 / DL-77). Measured first on the live graph over 269 recorded recommendations - scaled stops span 3.00/5.45/8.00 pct against a flat 5.00/5.00/5.00, and the reward-risk pass rate is 100 pct in BOTH modes, so DL-77's named trap (widen the stop, silently stop trading AMD/MRVL/HPE) does not bite on this book. The touch-rate half could not be measured at all - stop_target_observed_drawdown_pct had no producer - so S198 ships the recorder in the same change: the flip is auditable on our own trades from its first night, not only against DL-77's external 2026-04 backtest. Amended 2026-09-13 (operator decision, work-queue item 47 / [DL-76]): EXECUTION_ORDER_PRICE_TOLERANCE_MODE flat->scaled, promoting the S149 challenger. Promoted on DL-76's EXTERNAL measurement (60 sessions of real overnight gaps to 2026-05-01: a flat 50 bps refuses 35 pct of buys and 23 pct of sells blended, and the distribution is the finding - SCHW 25 pct against AMD 52 pct, so one number encodes two different policies), NOT on own-book evidence, because own-book evidence was structurally uncollectable while the narrower band was the applied one: compare_order_tolerances reported flat and scaled identical at 0.00 pct drop over 170 orders, correctly, because scaled is wider on 170 of 170 (75-250 bps against a fixed 50) so every order the flat band accepted the scaled band also accepts. The flip inverts that and is what makes the comparison informative for the first time - with the wider band applied, an order filling above the flat limit is an order flat would have refused, which is DL-76's refusal rate measured on our own book. Operator chose this over closing the item as decided-by-design. Amended 2026-11-17 (work-queue 113, DL-325; the operator's decisions of 2026-10-08 and 2026-10-09, DL-274 D4 and DL-277 amendment 2): on deliberator-manager DELIBERATOR_DEBATE_CONCURRENCY 1->3 and DELIBERATOR_REQUEST_TIMEOUT_SECONDS 120->240. Both were live settings on the fleet from those dates, held out of this file only by the fidelity count (PASS 2026-10-27), so a full up would have put one lane and the 120 s wait back. The deploy script gives each debater as many replicas as the lane count, so the 3 is also each debater's replicas in the nightly window. Measured on the live graph 2026-11-17: 27 nightly debate records since 2026-10-09, 0 orders failed open, 0 orphaned replies; seven buys were debated in 662 s on 2026-10-26, where one debate alone took 217 to 347 s on its own nights against execution's 1800 s. The two debaters keep 120: only the manager makes a peer request. This supersedes the 2026-09-04 sentence above that says the dial ships at 1. Amended 2026-11-26 (work-queue 109, DL-327; DL-282 decision 8): the three DELIBERATOR_LLM_PROVIDER lines (anthropic on deliberator-manager, deliberator-proponent and deliberator-opponent) leave this file. Since S262 (0.125.00) orchestration/packs/trading_llm.json declares the vendor: infra/deploy-agents.ps1 drops a line of this file for any key that pack names and appends the pack's value, and the master hands the vendor again at every activation (DL-289), so no full up since S262's deploy (2026-10-09) sent these lines, and they said the opposite of what the fleet runs. Measured 2026-11-26: the deploy script's own Up, every call a stand-in, sends the three apps the same DELIBERATOR_* values before and after this edit, equal to the live apps read the same hour. The vendor is changed in trading_llm.json, never here; this supersedes the STAGED 2026-08-20 sentence above. DELIBERATOR_EFFORT stays (DL-327).",
   "apps": {
@@ -25,3 +25,2 @@
     "deliberator-manager": {
-      "DELIBERATOR_LLM_PROVIDER": "anthropic",
       "DELIBERATOR_EFFORT": "high",
@@ -31,3 +30,2 @@
     "deliberator-proponent": {
-      "DELIBERATOR_LLM_PROVIDER": "anthropic",
       "DELIBERATOR_EFFORT": "high",
@@ -36,3 +34,2 @@
     "deliberator-opponent": {
-      "DELIBERATOR_LLM_PROVIDER": "anthropic",
       "DELIBERATOR_EFFORT": "high",
diff --git a/pyproject.toml b/pyproject.toml
index 6f12b92f..e37819f3 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -2,3 +2,3 @@
 name = "trading-agents"
-version = "0.131.08"
+version = "0.131.09"
 description = "An operator-controlled, single-user, agent-based trading system. Domain logic lives only in agents; the kernel is plumbing; contracts are the shared boundary."
diff --git a/uv.lock b/uv.lock
index ba64b9e8..98db7b5e 100644
--- a/uv.lock
+++ b/uv.lock
@@ -3671,3 +3671,3 @@ wheels = [
 name = "trading-agents"
-version = "0.131.8"
+version = "0.131.9"
 source = { virtual = "." }
```

After it, `git hash-object` must print:

```text
150ee807d6861d9b9abdadfee7cd99a487fdf2d7  agents/forecaster/agent.py
73fea2ea05b7dff925a4985401ff2142c4b7ecb3  agents/forecaster/return_model.py
6c77b7fc165468993721a6836b4a1fa6b4df51c3  agents/forecaster/lightgbm_model.py
0f5fa1e8289b681cfc38fcf56c47791039d1857f  orchestration/packs/trading_tunables.json
3771995f94e25ae2ce08f9da573a929adcd19982  agents/forecaster/laws/laws.md
7601d96643c1d0e7f12592ec46175e2592e07bf3  agents/forecaster/laws/test-plan.md
8a24adf94c1a8da9a255f4402a077e6a730af127  docs/laws/drift-register.md
8e1273bbf5ea0cc576bd519de49494850b0e331b  docs/laws/ledger.md
1bcf5452a7befd116a6af82b791f4dccab266ed4  docs/laws/INDEX.md
e37819f36a62ced49d9863f2bfe229dcfbf14598  pyproject.toml
98db7b5e9c2cbab427a4e5b4c89b17076cf7724e  uv.lock
```

On the prototype: `uv lock --check` accepts the lock; `make ci` exit 0 in one run with the bump applied, sixteen steps: 5,348 passed, 8 skipped, 100.00 % coverage; the dependency audit clean but the one accepted advisory (PYSEC-2026-2447, diskcache); the prototype's tests replace the three test files (`proto-s292` `d238b30d`, never pushed). Its first commit was refused by the `ruff format` hook on one wrapped call (Traps).

## Appendix C — the fifteen breaks, as exact replacements

Each break replaces the first occurrence of **Old** with **New** in the file named, unless the row
says otherwise. `EFFORT` is the pack line `      "DELIBERATOR_EFFORT": "high",` with its newline;
the manager's is the first, the proponent's the second, the opponent's the third.

| # | File | Old | New | Must go red |
| --- | --- | --- | --- | --- |
| B1 | `agents/forecaster/agent.py` | `model_ref=self._return_model.ref,` | `model_ref=self._settings.return_model_ref,` | A1 |
| B2 | the same | the same | `model_ref=self._model.ref,` | A1 |
| B3 | the same | the line `model_kind="return",` | removed | A1 |
| B4 | `agents/forecaster/return_model.py` | `ref: str = "fixed-fake-return"` | `ref: str = "lightgbm-gbdt"` | A1 |
| B5 | `agents/forecaster/lightgbm_model.py` | `ref: str = "lightgbm-gbdt"` | `ref: str = "lgbm"` | A2 |
| B6 | the same | `lightgbm.Booster(model_file=model_path)` | `lightgbm.Booster(model_file="other.txt")` | A2 |
| B7 | the pack | `EFFORT` (first) | a new line `"DELIBERATOR_LLM_PROVIDER": "anthropic",` above it, same indent | A3 |
| B8 | the pack | `EFFORT` (third) | a new line `"DELIBERATOR_LLM_PROVIDER": "openai",` above it, same indent | A3 |
| B9 | the pack | `"EXECUTION_ORDER_PRICE_TOLERANCE_MODE": "scaled"` | the same, then `,` and a new line `"EXECUTION_LLM_PROVIDER": "openai"` | A4 |
| B10 | the pack | `EFFORT` (first) | removed | A5 |
| B11 | the pack | `EFFORT` (second) | removed | A5 |
| B12 | the pack | `the three DELIBERATOR_LLM_PROVIDER lines` | `the DELIBERATOR_LLM_PROVIDER lines` | A6 |
| B13 | the pack | `The vendor is changed in trading_llm.json, never here` | `The vendor is changed in trading_llm.json` | A6 |
| B14 | the pack | `DL-327`, **every** occurrence | `DL-282` | A6 |
| B15 | `infra/deploy-agents.ps1` | `$llmKeys -notcontains ($_ -split '=', 2)[0]` | `$true` | the existing `test_c2_deploy_filters_tunables_before_appending_llm_pack` in `tests/test_deploy_llm_pack.py` |

On the prototype: 15 planted, 15 red, each on the test named, the tree clean after (`s292_breaks.py`, kit OneDrive `wq109-142-2026-11-26/`). B7 and B8 also turn A4 and A5 red, which is expected.
