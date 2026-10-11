<!-- Agent: planning | Role: sprint handover -->
# Sprint 269 — a parameter the model returns as null, a list or an object is no value

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-269-a-null-parameter-is-no-value`
**Status:** MERGED 2026-10-11 — `0.125.07`, fast-forwarded to `4b536d7e`, tag `v0.125.07`, GATE PROVEN `4b536d7e` (CI, CodeQL, Security Findings); no deploy; F1 passed at no cost
**Version:** `0.125.07` (PATCH)
**Effort:** S
**Decisions:** [DL-292](../design-log.md) (this sprint's seven decisions, made and measured) · [DL-290](../design-log.md) amendment 2 (where the defect was met) · [work-queue 128](../work-queue.md) · DRIFT-112

> **Why this bump kind.** No new capability: `OPR-FAIL-02` already says a required parameter must
> hold a value, and the code counts a `null` as one. The clause gains one sentence that says what
> a value is; no clause is added.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/operator/laws/laws.md` | The operator's **locked constitution** (v1.9) | **LOCKED.** This sprint rewords one clause, `OPR-FAIL-02`, with the text given below, and touches no other |
| `agents/operator/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | The `OPR-FAIL-02` row takes the new clause text and gains the new tests |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | `drift-register.md`: DRIFT-112 is marked corrected. `INDEX.md` and `ledger.md`: the operator's row reads v1.10 |

Binding sections here: **`OPR-FAIL`**, **`OPR-OUT`**, **`OPR-NEV`**.

### The rule

1. **Before writing code**, read `agents/operator/laws/laws.md` and its `test-plan.md`, whole.
2. Read [`docs/laws/conventions.md`](../laws/conventions.md) and the DRIFT-112 row of
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
3. **Write the Law reading record** (bottom of this file) **before** your first code change.
4. **If a law contradicts this spec, STOP and report.**
5. Every test for behaviour a clause governs **cites the clause ID in its docstring**.

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**No file in `contracts/` changes. One clause is reworded, none is added.** The cycle owed, every
item of it:

- `OPR-FAIL-02` in `agents/operator/laws/laws.md` is replaced by this text, the version goes to
  v1.10 and the Changelog gains one line
  (`v1.10 — S269 / DL-292 (2026-10-11): rewords OPR-FAIL-02`):

  > - **OPR-FAIL-02** — A reply whose outcome is `intent` is checked before anything is written
  >   for it. It is refused when its family is absent, is not a string or is not one of the
  >   grammar's families, and when it lacks a parameter the grammar marks required for its family.
  >   A required parameter is given when any of its accepted names holds a value that is not blank.
  >   A value is text, a number or a boolean: a parameter that holds `null`, a list or an object
  >   holds no value and is left out of the intent, whether its family requires it or not.
  >   When a reply is refused, `interpret` returns `CommandResult(outcome="refused", ...)` with a
  >   message that says so (for a missing parameter it names the family and each missing parameter
  >   by its first accepted name), the `CommandAudit` reads `refused` and no `Intent` is written.
  >   The check runs after the explicit command grammar, so a typed approve is not refused for the
  >   model's omission. A reply whose outcome is not `intent` is not checked. The system prompt
  >   states each family's parameter names. The sentences are pinned by tests, not quoted here.

- The `OPR-FAIL-02` row of `test-plan.md` carries the new clause text and cites every test of the
  Test plan below **as well as** the eight it cites today.
- `docs/laws/INDEX.md` and `docs/laws/ledger.md`: the operator's row reads v1.10 and says what this
  sprint did, in the form the row already uses for S268. 🪤 **The law gate does not check this
  label**: it compares the counts only, so a stale `v1.9` passes `make ci`. Change both rows by hand.
- DRIFT-112 is marked corrected, with the sprint and the DL.
- The counts stay 20 / 51: the clause was already 🟩. Let the gate say.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/operator/domain/result.py` | operator `laws.md` + `test-plan.md` | `OPR-FAIL-02`; `OPR-OUT-03` (what a `TypedIntent` carries); `OPR-OUT-05`, `OPR-OUT-06` (the refusal and its audit) |

⚠️ **Nothing else in the operator moves.** `grammar.py`, `prompts.py` and `agent.py` are not
touched. If your change alters any existing test, stop and report: the prototype breaks none.

---

## Goal

A parameter the model returns as `null`, a list or an object is left out of the intent, so an
intent that needs it is refused with the sentence S268 added, and one that does not need it is
passed on without it. Text, a number and a boolean are values, as they are today.

## Why (context)

S268 made the operator refuse an intent that lacks a parameter its family cannot do without. Its
paid check returned `modify`'s value as the JSON number `8`, which was accepted, and reading why
showed the check turns every value into text first: a `null` becomes the text `None`, which is
not blank. So `approve` with a `null` target is still passed on, and after the operator confirms
it the supervisor is asked to resolve a flag called `None`.

### Measured, 2026-10-11 — read these before designing

Every row was measured on `main` at `3fb617ce` unless it says otherwise. The reach rows are one
typed message through the dashboard's chat handler on a fresh in-memory context with a canned
model reply, unconfirmed and then confirmed (`wq128_null_reach.py`); no vendor call.

| Claim | Value | How it was measured |
| --- | --- | --- |
| A `null` under a required name is passed on | all six families | *[measured]* `approve`, `reject`, `modify` (name, and value), `mode`, `stage`, `resume`: each comes back as an intent whose parameter is the text `None`, audited `intent`, one `Intent` written |
| A confirmed `approve` of `None` is routed | `Command routed to supervisor.resolve_flag.` | *[measured]* the same case with `confirmed: true` |
| What `resolve_flag` then does with a subject no flag has | not known | *[ASSUMED — not measured]* not read past the dispatch |
| The supervisor reads the first name that is not empty | `subject or target`; `stage or target` | *[read]* `agents/supervisor/domain/gate.py:65` and `:152`. So a `null` under the first name hides a real value under the second: `{"target": null, "subject": "flag:case-1"}` reaches it as `target: None` and the subject both *[measured]* |
| A `null` subject replaces the typed question in `explain` | the text `None` | *[read]* `surfaces/operator_tools.py:65`, `intent.parameters.get("subject") or text`; the stored `Intent` holds `{"subject": "None"}` *[measured]* |
| A list or an object is passed on as Python's rendering of it | `['flag:case-1']`, `[]`, `{}` | *[measured]* each as `approve`'s target: routed to `supervisor.resolve_flag` after confirmation |
| A number and a boolean are carried as text, and that does not change | `8` → `8`, `0` → `0`, `false` → `False` | *[measured]* before and after, on `modify`'s value |
| Both readers of a reply's parameters call one function | `_params`, 2 callers | *[measured]* `grep` over `agents/operator`: `result.py:59` (the check) and `result.py:106` (the intent that is built); `store.py:88` writes what the intent holds |
| A real model has returned a `null` | 0 of 8 calls | *[measured, paid]* S268's check on gpt-5.5; Anthropic *[ASSUMED — not measured]* |
| The prototype's new tests on the unchanged code | 19 failed, 7 passed | *[measured]* in the sprint worktree; the seven are the guards that numbers, booleans and blank text do not move |
| The prototype's new tests on the prototype | 26 passed | *[measured]* |
| The prototype breaks no existing test | no existing test breaks (4,735 passed, 8 skipped, the 26 new cases among them) | *[measured]* full suite in the sprint worktree, `--no-cov`. Two import-wall tests look `lint-imports` up on the path and fail when the suite is started with the environment's interpreter directly, on the unchanged code as well; under `uv run` they pass |
| The prototype's guards can fail | 12 planted breaks, 12 red | *[measured]* one break at a time on the operator's tests, the file restored and green after |
| `result.py` after the change | 154 lines (149 before); blob `f47d8608` | *[measured]* on the prototype's bytes, LF line endings |
| The operator's recipe hash | unchanged | *[measured]* `tests/test_dspy_recipe.py` passes on the prototype; the recipe does not read `result.py` (S268 changed that file and the hash stood) |
| The same reach measurement on the prototype | every `null`, list and object under a required name is refused with the sentence; the others are left out | *[measured]* `after_prototype.txt` |

---

## Scope — and what is deliberately NOT here

1. **`_params` keeps a parameter only when its value is text, a number or a boolean.** One
   function, in `agents/operator/domain/result.py`. Replace it with exactly the text in the
   Appendix. Both the check and the intent that is built read it, so nothing else changes.
2. **Tests**, per the Test plan, in one new file.
3. **The law cycle** as answered above.

### Out of scope (do NOT build this sprint)

- **`grammar.py`, `prompts.py`, `agent.py` and `INTENT_TOOL_SCHEMA` do not change.** The prompt
  recipe hash must stay as it is; if `tests/test_dspy_recipe.py` goes red, stop and report.
- **The supervisor, `surfaces/` and `contracts/` do not change.**
- **No new sentence.** A parameter that holds no value is reported by the sentence S268 added.
- **A number's or a boolean's text is not changed.** `false` is still carried as `False`.
- **A `run` with no `stage` is still passed on**, as DL-290 named.
- **No new clause, no ADR, no version of any other agent's law.**

### The road not taken (LAW-06)

- **Mend the check alone.** Rejected: the text `None` would still be written into the `Intent`,
  still replace the typed question in `explain`, and still hide a real value under the second
  accepted name, because the supervisor reads the first name that is not empty.
- **Drop a `null` only, and keep a list or an object as text.** Rejected: `["flag:case-1"]` is
  passed on as the target `['flag:case-1']` and routed after confirmation; no reader takes a
  structure.
- **Take the one item of a one-item list.** Rejected: that is a guess at what the model meant.
- **Rename the supervisor's reads to one name each.** Rejected, as in DL-290: a second agent's
  law cycle, and it leaves the other readers as they are.

---

## The design decisions — made, and recorded in DL-292

They are recorded with their rejected alternatives. **Do not add a design-log entry.**

1. A value is text, a number or a boolean. A `null`, a list and an object are not values.
2. The mend is in `_params`, the one function both readers call.
3. A parameter that holds no value is left out of the intent, whether it is required or not.
4. A structure is dropped whole, never flattened.
5. No new sentence and no fault: a required parameter that holds no value is a missing one.
6. Blank text does not move: missing where required, carried as it is where not.
7. A number and a boolean are carried as the text Python gives them, as today.

---

## Blast radius — measured 2026-10-11

| What | Detail |
| --- | --- |
| Files changed | `agents/operator/domain/result.py` (149 → 154); one new test file; operator `laws.md`, `test-plan.md`; `docs/laws/INDEX.md`, `ledger.md`, `drift-register.md` |
| Agents affected | operator only; it imports no other agent |
| Contract change? | No |
| Graph vocabulary change? | No. An `Intent` node's `parameters` no longer holds a key whose value was not text, a number or a boolean |
| New env keys / tunables | None |
| Deploy implication | None needed: the chat runs in the dashboard and the fleet's operator container binds the fake client. The code reaches the image with the next retag |
| Rollback | Nothing beyond the retag |

---

## Steps, in order

1. **Read the laws** and write the Law reading record.
2. **Plant the failing tests first** (Test plan) and watch them fail on the unchanged code. Paste the red output.
3. **Replace `_params`** with the Appendix's text.
4. **Law cycle** as answered above, every item.
5. **Prove the guards can fail (DL-70):** at least the breaks listed under Traps, one at a time, each red, each restored.
6. **`make ci` green**, every step of the `ci:` target, **redirected to a file, never piped**.
7. **Fill the handback sections** at the bottom of this file.

---

## Test plan

New file `agents/operator/tests/test_parameter_values.py`. Each test drives the real
`OperatorAgent` on an in-memory graph with one canned reply whose outcome is `intent`.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| B1 | 🎯 a required parameter that holds no value is refused | parametrised: `approve` with `target` a `null`, `[]`, `{}`, `["flag:case-1"]`, `{"id": "flag:case-1"}`; `reject` with `target` and `subject` both `null`; `modify` with `value` `null`, and with `name` `null`; `mode` with `mode` `null`; `stage` with `stage` `null` and `target` `[]`; `resume` with `stage` `null` and a `run_id` | outcome `refused`, no intent, the message equals `missing_parameters_reply(family, missing)`, the one `CommandAudit` reads `refused`, 0 `Intent` |
| B2 | 🪤 a parameter that holds no value is left out of the intent | parametrised: `approve` with `target` `null` and a real `subject`; `approve` with `subject` `[]` and a real `target`; `stage` with `stage` `null` and a real `target`; `resume` with `stage` `{}` and a real `from_stage`; `explain` with `subject` `null`; `run` with `stage` `null`; `run` with `stage` `["live"]`; `status` with two keys the grammar does not know, a `null` and an object | outcome `intent`; the intent's `parameters` equal exactly the kept ones; the stored `Intent` node's `parameters`, read back as JSON, equal the same |
| B3 | text, a number and a boolean are values | parametrised on `modify`'s `value`: `"8"`, `8`, `0`, `0.5`, `false`, `true` | outcome `intent`; `parameters` equal `{"name": ..., "value": <the text Python gives it>}`, so `0` and `false` are not dropped |
| B4 | blank text does not move | `approve` with a blank `target`; `run` with `stage` the empty text | the first is refused; the second is passed on with `{"stage": ""}` |

Existing tests to edit: **none.** If one fails, stop and report.

---

## Success factors

- [x] Every row of the Test plan is a passing test that cites `OPR-FAIL-02`.
- [x] `git hash-object agents/operator/domain/result.py` prints `f47d86083f8091aa5b27e8d0e4abc99e92ba7be9` on LF bytes, or the difference is explained.
- [x] No existing test changed (`git diff --stat main -- '*test*'` shows the one new file).
- [x] `tests/test_dspy_recipe.py` passes untouched and `tests/fixtures/` and `.secrets.baseline` are unchanged.
- [x] Law cycle done, every item: clause text as given, v1.10, Changelog, test-plan row, the operator's row in `INDEX.md` and in `ledger.md`, DRIFT-112 corrected.
- [x] Every guard planted, watched to fail, restored, stated per guard.
- [x] Every touched module under 200 lines.
- [x] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **`0` and `false` are values.** A filter that keeps what is truthy drops them. B3 plants both.
🪤 **A boolean is an `int` in Python.** A filter that excludes `bool` drops `true` and `false`.
🪤 **The law gate passes a stale version label** in `docs/laws/INDEX.md` and `ledger.md`.
🪤 **A canned reply is matched by a substring of the prompt**, and a text that begins with
`approve ` is rewritten by the explicit grammar. Use a neutral text.
🪤 **`graph.list_nodes` returns a tuple.** Compare with `()`, not `[]`.
🪤 **The `Intent` node stores its parameters as JSON text**, sorted by key: read it back with
`json.loads` before comparing.

Breaks to plant, at the least: every value kept, as before the sprint; a `null` kept; a list
kept; an object kept; only a `null` dropped; a number dropped; a boolean dropped; a float
dropped; blank text dropped too; a falsy value dropped; the check reading the raw parameters;
the intent built from the raw parameters.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module under 200 lines. Split, don't grow. No `# noqa`.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- Faults, not silent failure.
- `make ci` every step green, 100.00 % coverage floor, **never measured through a pipe**.
- PATCH bump, `uv.lock` staged with it. If `uv lock` cannot resolve in your sandbox, say so and
  say exactly how `uv.lock` was touched.
- Secrets never through the worktree. The worktree has no `.env`; nothing here needs one.

---

## Sequencing after merge (the planner's)

1. `make gate-ran` from the proving worktree, the printed SHA checked against `git rev-parse HEAD`.
2. The planner re-measures: the function against the Appendix, the planner's own test file and
   break script run on the built tree, the open CodeQL alerts set-diffed against the last merged
   branch's.
3. **F1**, at no cost, on the merged `main`: `wq128_null_reach.py`, sixteen cases through the chat
   handler, each unconfirmed and confirmed; its output must equal the prototype's.
4. **No paid check.** The prompt and the request do not change, so no model's reply does.
5. No deploy.

---

## Handover — paste this to Codex

```text
You are building Sprint 269 in the worktree ../ta-s269, on the branch
sprint-269-a-null-parameter-is-no-value. Never work on main.

Read docs/sprints/sprint-269-a-null-parameter-is-no-value.md, whole, before anything else. It is
the spec, and its bottom sections are your handback.

In order:
1. Read agents/operator/laws/laws.md and test-plan.md, docs/laws/conventions.md and the DRIFT-112
   row of docs/laws/drift-register.md. Fill the Law reading record in the spec BEFORE any code.
2. Write the tests of the Test plan in agents/operator/tests/test_parameter_values.py. Run them
   on the unchanged code and paste the red output into the Closeout.
3. Replace the function _params in agents/operator/domain/result.py with the Appendix's text,
   exactly. Change nothing else in production code.
4. Do the law cycle the spec answers, every item: replace OPR-FAIL-02 with the given text,
   laws.md to v1.10 with a Changelog line, the test-plan row, the operator's row in
   docs/laws/INDEX.md and docs/laws/ledger.md (v1.10; the gate does not check it), DRIFT-112
   marked corrected.
5. Plant the breaks listed under Traps one at a time on agents/operator; each must go red; restore.
6. Bump the version (PATCH) and stage uv.lock. Run make ci redirected to a file and read the file.
7. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in the sprint's
   row of docs/sprints/README.md. Commit on the branch if your sandbox lets you write the
   repository's git directory; if not, leave the tree uncommitted and say so. Do not edit
   docs/STATE.md.

DO NOT: change grammar.py, prompts.py, agent.py, INTENT_TOOL_SCHEMA, the supervisor, surfaces/,
contracts/, tests/fixtures/, .secrets.baseline or any existing test; add a design-log entry; add
a law clause; use noqa; let any module reach 200 lines; measure make ci through a pipe.

Traps: 0 and false are values, so do not filter on truthiness; a boolean is an int in Python; the
Intent node stores its parameters as JSON text; graph.list_nodes returns a tuple; a canned reply
is matched by a substring of the prompt and a text beginning with "approve " is rewritten by the
explicit grammar.

If a law contradicts the spec, or any existing test fails, STOP and report. State anything not
done as "not done" or "verified failing". Never write a Result for work you have not done.
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
| `agents/operator/domain/result.py` | `agents/operator/laws/laws.md` v1.9 and `test-plan.md`, whole | `OPR-FAIL-02`, `OPR-OUT-03`, `OPR-OUT-05`, `OPR-OUT-06`, `OPR-OUT-07`, `OPR-NEV-01`, `OPR-NEV-05` | No: both parameter readers must use the Appendix's scalar filter; refusal, audit and intent storage stay on the existing paths. Read before any code change on 2026-10-11. |
| `agents/operator/tests/test_parameter_values.py` | Same operator law book and test plan, whole; `docs/laws/conventions.md` | `OPR-FAIL-02`; conventions §§3, 7, 7a, 10 | No: exercise the real operator with a synthetic model and in-memory graph, cite the clause in every test, and prove red before implementation. |
| Operator law amendment and rollup rows | `docs/laws/INDEX.md`, `docs/laws/conventions.md`, DRIFT-112 in `docs/laws/drift-register.md`; operator law book and test plan | `OPR-FAIL-02`; conventions §§2, 4, 7a, 9 | No: the spec authorizes one deliberate amendment to v1.10, retaining all eight current test citations and the 20 / 51 counts; both version labels must be edited by hand. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No. Owed: the given `OPR-FAIL-02` rewording, v1.10 and Changelog, test-plan text and new citations, both operator rollup rows, and DRIFT-112 corrected. The reading record preceded code. The given clause, v1.10 and Changelog, test-plan text with all eight existing citations plus B1-B4, both v1.10 rollup rows, and DRIFT-112 correction are done. The law gate exits 0; the counts remain 20 / 51.

**Contradictions found between a law and this spec:** none. Conventions §4 permits the deliberate amendment specified here; no other clause is changed.

**Laws found silent where a decision was needed:** none beyond the value definition already adjudicated in DL-292 and recorded as DRIFT-112; no new drift row is needed.

**Clauses that were ⬜ and are now proven:** none. `OPR-FAIL-02` is already 🟩; the operator rollup remains 20 / 51 after passing B1-B4 and the law gate (exit 0, no stdout).

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| B1 | `test_b1_required_parameter_without_value_is_refused` (11 cases) | `agents/operator/tests/test_parameter_values.py` | PASS | `OPR-FAIL-02` |
| B2 | `test_b2_parameter_without_value_is_omitted` (8 cases) | `agents/operator/tests/test_parameter_values.py` | PASS | `OPR-FAIL-02` |
| B3 | `test_b3_scalar_parameter_is_kept` (6 cases) | `agents/operator/tests/test_parameter_values.py` | PASS | `OPR-FAIL-02` |
| B4 | `test_b4_blank_text_keeps_existing_behavior` (required blank and optional empty text) | `agents/operator/tests/test_parameter_values.py` | PASS | `OPR-FAIL-02` |

**Tests added beyond the plan:** none. B4 proves both blank-text paths in one test, giving 26 collected cases as measured in the spec.

---

## Closeout — evidence

**Status:** MERGED

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/Downloads/project/ta-s269`, branch `sprint-269-a-null-parameter-is-no-value`, `.env`: no. Starting clean HEAD: `9e565885ad7654c9783026dfc520d1858cf1ba97`.

**Result:** B1-B4 prove required `null`, list and object parameters are refused with the existing missing-parameter sentence, one refused audit and no Intent; optional non-values are omitted from both the returned parameters and stored JSON. Text, numbers, booleans and blank text keep their prior behavior. All 26 new cases and the operator/recipe run pass; all 12 planted breaks fail and all 12 restored runs pass.

**Files changed:** `agents/operator/domain/result.py`, `agents/operator/tests/test_parameter_values.py`, `agents/operator/laws/laws.md`, `agents/operator/laws/test-plan.md`, `docs/laws/INDEX.md`, `docs/laws/ledger.md`, `docs/laws/drift-register.md`, `docs/sprints/sprint-269-a-null-parameter-is-no-value.md`, `docs/sprints/README.md`, `pyproject.toml`, `uv.lock`.

**Design decisions:** recorded as [DL-292](../design-log.md); none added by the build.

**Proof — the red run first:**

```text
uv run pytest agents/operator/tests/test_parameter_values.py --no-cov -q
Exit code: 1
FFFFFFFFFFFFFFFFFFF.......                                               [100%]
================================== FAILURES ===================================
______ test_b1_required_parameter_without_value_is_refused[approve-null] ______
agents\operator\tests\test_parameter_values.py:59: in test_b1_required_parameter_without_value_is_refused
    _assert_refused(result, graph, family, missing)
agents\operator\tests\test_parameter_values.py:148: in _assert_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
___ test_b1_required_parameter_without_value_is_refused[approve-empty-list] ___
agents\operator\tests\test_parameter_values.py:59: in test_b1_required_parameter_without_value_is_refused
    _assert_refused(result, graph, family, missing)
agents\operator\tests\test_parameter_values.py:148: in _assert_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
__ test_b1_required_parameter_without_value_is_refused[approve-empty-object] __
agents\operator\tests\test_parameter_values.py:59: in test_b1_required_parameter_without_value_is_refused
    _assert_refused(result, graph, family, missing)
agents\operator\tests\test_parameter_values.py:148: in _assert_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
______ test_b1_required_parameter_without_value_is_refused[approve-list] ______
agents\operator\tests\test_parameter_values.py:59: in test_b1_required_parameter_without_value_is_refused
    _assert_refused(result, graph, family, missing)
agents\operator\tests\test_parameter_values.py:148: in _assert_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
_____ test_b1_required_parameter_without_value_is_refused[approve-object] _____
agents\operator\tests\test_parameter_values.py:59: in test_b1_required_parameter_without_value_is_refused
    _assert_refused(result, graph, family, missing)
agents\operator\tests\test_parameter_values.py:148: in _assert_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
__ test_b1_required_parameter_without_value_is_refused[reject-null-aliases] ___
agents\operator\tests\test_parameter_values.py:59: in test_b1_required_parameter_without_value_is_refused
    _assert_refused(result, graph, family, missing)
agents\operator\tests\test_parameter_values.py:148: in _assert_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
___ test_b1_required_parameter_without_value_is_refused[modify-null-value] ____
agents\operator\tests\test_parameter_values.py:59: in test_b1_required_parameter_without_value_is_refused
    _assert_refused(result, graph, family, missing)
agents\operator\tests\test_parameter_values.py:148: in _assert_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
____ test_b1_required_parameter_without_value_is_refused[modify-null-name] ____
agents\operator\tests\test_parameter_values.py:59: in test_b1_required_parameter_without_value_is_refused
    _assert_refused(result, graph, family, missing)
agents\operator\tests\test_parameter_values.py:148: in _assert_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
_______ test_b1_required_parameter_without_value_is_refused[mode-null] ________
agents\operator\tests\test_parameter_values.py:59: in test_b1_required_parameter_without_value_is_refused
    _assert_refused(result, graph, family, missing)
agents\operator\tests\test_parameter_values.py:148: in _assert_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
_ test_b1_required_parameter_without_value_is_refused[stage-nonvalue-aliases] _
agents\operator\tests\test_parameter_values.py:59: in test_b1_required_parameter_without_value_is_refused
    _assert_refused(result, graph, family, missing)
agents\operator\tests\test_parameter_values.py:148: in _assert_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
___ test_b1_required_parameter_without_value_is_refused[resume-null-stage] ____
agents\operator\tests\test_parameter_values.py:59: in test_b1_required_parameter_without_value_is_refused
    _assert_refused(result, graph, family, missing)
agents\operator\tests\test_parameter_values.py:148: in _assert_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
______ test_b2_parameter_without_value_is_omitted[approve-keeps-subject] ______
agents\operator\tests\test_parameter_values.py:98: in test_b2_parameter_without_value_is_omitted
    _assert_intent(result, graph, family, expected)
agents\operator\tests\test_parameter_values.py:164: in _assert_intent
    assert result.intent.parameters == expected
E   AssertionError: assert {'target': 'N...'flag:case-1'} == {'subject': 'flag:case-1'}
E
E     Omitting 1 identical items, use -vv to show
E     Left contains 1 more item:
E     {'target': 'None'}
E     Use -v to get more diff
______ test_b2_parameter_without_value_is_omitted[approve-keeps-target] _______
agents\operator\tests\test_parameter_values.py:98: in test_b2_parameter_without_value_is_omitted
    _assert_intent(result, graph, family, expected)
agents\operator\tests\test_parameter_values.py:164: in _assert_intent
    assert result.intent.parameters == expected
E   AssertionError: assert {'subject': '...'flag:case-1'} == {'target': 'flag:case-1'}
E
E     Omitting 1 identical items, use -vv to show
E     Left contains 1 more item:
E     {'subject': '[]'}
E     Use -v to get more diff
_______ test_b2_parameter_without_value_is_omitted[stage-keeps-target] ________
agents\operator\tests\test_parameter_values.py:98: in test_b2_parameter_without_value_is_omitted
    _assert_intent(result, graph, family, expected)
agents\operator\tests\test_parameter_values.py:164: in _assert_intent
    assert result.intent.parameters == expected
E   AssertionError: assert {'stage': 'No...get': 'paper'} == {'target': 'paper'}
E
E     Omitting 1 identical items, use -vv to show
E     Left contains 1 more item:
E     {'stage': 'None'}
E     Use -v to get more diff
_____ test_b2_parameter_without_value_is_omitted[resume-keeps-from-stage] _____
agents\operator\tests\test_parameter_values.py:98: in test_b2_parameter_without_value_is_omitted
    _assert_intent(result, graph, family, expected)
agents\operator\tests\test_parameter_values.py:164: in _assert_intent
    assert result.intent.parameters == expected
E   AssertionError: assert {'stage': '{}...e': 'analyst'} == {'from_stage': 'analyst'}
E
E     Omitting 1 identical items, use -vv to show
E     Left contains 1 more item:
E     {'stage': '{}'}
E     Use -v to get more diff
______ test_b2_parameter_without_value_is_omitted[explain-null-subject] _______
agents\operator\tests\test_parameter_values.py:98: in test_b2_parameter_without_value_is_omitted
    _assert_intent(result, graph, family, expected)
agents\operator\tests\test_parameter_values.py:164: in _assert_intent
    assert result.intent.parameters == expected
E   AssertionError: assert {'subject': 'None'} == {}
E
E     Left contains 1 more item:
E     {'subject': 'None'}
E     Use -v to get more diff
_________ test_b2_parameter_without_value_is_omitted[run-null-stage] __________
agents\operator\tests\test_parameter_values.py:98: in test_b2_parameter_without_value_is_omitted
    _assert_intent(result, graph, family, expected)
agents\operator\tests\test_parameter_values.py:164: in _assert_intent
    assert result.intent.parameters == expected
E   AssertionError: assert {'stage': 'None'} == {}
E
E     Left contains 1 more item:
E     {'stage': 'None'}
E     Use -v to get more diff
_________ test_b2_parameter_without_value_is_omitted[run-list-stage] __________
agents\operator\tests\test_parameter_values.py:98: in test_b2_parameter_without_value_is_omitted
    _assert_intent(result, graph, family, expected)
agents\operator\tests\test_parameter_values.py:164: in _assert_intent
    assert result.intent.parameters == expected
E   assert {'stage': "['live']"} == {}
E
E     Left contains 1 more item:
E     {'stage': "['live']"}
E     Use -v to get more diff
____ test_b2_parameter_without_value_is_omitted[status-unknown-nonvalues] _____
agents\operator\tests\test_parameter_values.py:98: in test_b2_parameter_without_value_is_omitted
    _assert_intent(result, graph, family, expected)
agents\operator\tests\test_parameter_values.py:164: in _assert_intent
    assert result.intent.parameters == expected
E   assert {'unknown_nul...': 'case-1'}"} == {}
E
E     Left contains 2 more items:
E     {'unknown_null': 'None', 'unknown_object': "{'id': 'case-1'}"}
E     Use -v to get more diff
=========================== short test summary info ===========================
FAILED agents/operator/tests/test_parameter_values.py::test_b1_required_parameter_without_value_is_refused[approve-null]
FAILED agents/operator/tests/test_parameter_values.py::test_b1_required_parameter_without_value_is_refused[approve-empty-list]
FAILED agents/operator/tests/test_parameter_values.py::test_b1_required_parameter_without_value_is_refused[approve-empty-object]
FAILED agents/operator/tests/test_parameter_values.py::test_b1_required_parameter_without_value_is_refused[approve-list]
FAILED agents/operator/tests/test_parameter_values.py::test_b1_required_parameter_without_value_is_refused[approve-object]
FAILED agents/operator/tests/test_parameter_values.py::test_b1_required_parameter_without_value_is_refused[reject-null-aliases]
FAILED agents/operator/tests/test_parameter_values.py::test_b1_required_parameter_without_value_is_refused[modify-null-value]
FAILED agents/operator/tests/test_parameter_values.py::test_b1_required_parameter_without_value_is_refused[modify-null-name]
FAILED agents/operator/tests/test_parameter_values.py::test_b1_required_parameter_without_value_is_refused[mode-null]
FAILED agents/operator/tests/test_parameter_values.py::test_b1_required_parameter_without_value_is_refused[stage-nonvalue-aliases]
FAILED agents/operator/tests/test_parameter_values.py::test_b1_required_parameter_without_value_is_refused[resume-null-stage]
FAILED agents/operator/tests/test_parameter_values.py::test_b2_parameter_without_value_is_omitted[approve-keeps-subject]
FAILED agents/operator/tests/test_parameter_values.py::test_b2_parameter_without_value_is_omitted[approve-keeps-target]
FAILED agents/operator/tests/test_parameter_values.py::test_b2_parameter_without_value_is_omitted[stage-keeps-target]
FAILED agents/operator/tests/test_parameter_values.py::test_b2_parameter_without_value_is_omitted[resume-keeps-from-stage]
FAILED agents/operator/tests/test_parameter_values.py::test_b2_parameter_without_value_is_omitted[explain-null-subject]
FAILED agents/operator/tests/test_parameter_values.py::test_b2_parameter_without_value_is_omitted[run-null-stage]
FAILED agents/operator/tests/test_parameter_values.py::test_b2_parameter_without_value_is_omitted[run-list-stage]
FAILED agents/operator/tests/test_parameter_values.py::test_b2_parameter_without_value_is_omitted[status-unknown-nonvalues]
19 failed, 7 passed in 1.60s
```

**Proof — the green run:**

```text
uv run pytest agents/operator/tests/test_parameter_values.py --no-cov -q
Exit code: 0
..........................                                               [100%]
26 passed in 1.36s

uv run pytest agents/operator/tests tests/test_dspy_recipe.py --no-cov -q
Exit code: 0
........................................................................ [ 41%]
........................................................................ [ 83%]
............................                                             [100%]
172 passed in 3.01s

uv run python scripts/check_law_coverage.py
Exit code: 0 (no stdout)

uv lock
Exit code: 0
Resolved 180 packages in 3.28s
Updated trading-agents v0.125.6 -> v0.125.7
```

**Guards planted:** each mutation was applied alone to `agents/operator/domain/result.py`; the new operator tests were run with `uv run pytest agents/operator/tests/test_parameter_values.py --no-cov -q`. Each red run exited 1 with assertion failures; the original file bytes were restored in `finally`, then the same tests exited 0. Actual per-guard output:

```text
G01 every value kept: red exit 1, 19 failed, 7 passed in 1.71s; restored exit 0, 26 passed in 1.02s
G02 null kept: red exit 1, 12 failed, 14 passed in 1.93s; restored exit 0, 26 passed in 1.14s
G03 list kept: red exit 1, 5 failed, 21 passed in 1.50s; restored exit 0, 26 passed in 1.07s
G04 object kept: red exit 1, 4 failed, 22 passed in 1.96s; restored exit 0, 26 passed in 1.26s
G05 only null dropped: red exit 1, 9 failed, 17 passed in 2.46s; restored exit 0, 26 passed in 1.56s
G06 number dropped: red exit 1, 4 failed, 22 passed in 1.42s; restored exit 0, 26 passed in 1.42s
G07 boolean dropped: red exit 1, 2 failed, 24 passed in 1.50s; restored exit 0, 26 passed in 1.69s
G08 float dropped: red exit 1, 1 failed, 25 passed in 1.93s; restored exit 0, 26 passed in 1.65s
G09 blank text dropped too: red exit 1, 1 failed, 25 passed in 1.49s; restored exit 0, 26 passed in 1.34s
G10 falsy value dropped: red exit 1, 3 failed, 23 passed in 1.91s; restored exit 0, 26 passed in 1.47s
G11 check reading raw parameters: red exit 1, 11 failed, 15 passed in 1.96s; restored exit 0, 26 passed in 1.62s
G12 intent built from raw parameters: red exit 1, 8 failed, 18 passed in 2.06s; restored exit 0, 26 passed in 1.31s
```

**Module line counts:** `agents/operator/domain/result.py` **154**, `agents/operator/tests/test_parameter_values.py` **173**. The production blob is exactly `f47d86083f8091aa5b27e8d0e4abc99e92ba7be9` on LF bytes.

**`make ci`:** redirected to `C:/Users/yury_/AppData/Local/Temp/ta-s269-codex-20261011/make-ci.txt`; the file was read. Exit code **0**; all **15** target steps completed. **4,735 passed, 8 skipped**, coverage **100.00 %**. Dependency audit: **No unaccepted vulnerabilities; 1 accepted advisory re-checked** (`PYSEC-2026-2447`, the existing diskcache acceptance). detect-secrets **Passed**; untracked-secrets check **no untracked files to scan**. `.secrets.baseline` unchanged. Actual commands and result lines, pasted from the redirected file:

```text
make ci > 'C:\Users\yury_\AppData\Local\Temp\ta-s269-codex-20261011\make-ci.txt' 2>&1
Exit code: 0
uv run ruff check . --output-format=github
uv run ruff format --check .
1671 files already formatted
uv run mypy kernel contracts agents orchestration surfaces
Success: no issues found in 1196 source files
uv run lint-imports
Contracts: 5 kept, 0 broken.
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts
[WARN] agents/operator/domain/result.py: 154 lines (warn 150, hard block 200)
[WARN] agents/operator/tests/test_parameter_values.py: 173 lines (warn 150, hard block 200)
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run python scripts/check_law_coverage.py
uv run python scripts/check_param_law_sync.py
uv run python scripts/check_sprint_status.py
docs_seen=274 SPEC=11 BUILT=1 MERGED=262 UNMAPPED=0 MISSING=0
uv run python scripts/check_markdown_links.py
uv run python scripts/check_version_scheme.py
uv run pytest
TOTAL                                                           20264      0   4296      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
SKIPPED [1] tests\test_bus_azure_config.py:21: Service Bus dotenv isolation proof requires local .env
SKIPPED [1] tests\test_bus_celery.py:181: CELERY_BROKER_URL is not set
SKIPPED [1] tests\test_deliberator_servicebus_peer.py:36: A1 proof requires .env present; CI has no local secrets file
SKIPPED [1] tests\test_graph_postgres.py:137: POSTGRES_TEST_DSN is not set
SKIPPED [1] tests\test_graph_postgres_keys.py:90: POSTGRES_TEST_DSN is not set
SKIPPED [1] agents\forecaster\tests\test_barrier_garch_oracle.py:179: could not import 'scipy.signal': No module named 'scipy'
SKIPPED [1] agents\provider\tests\test_sources.py:159: FINNHUB_TEST_NETWORK=1 is not set
SKIPPED [1] agents\provider\tests\test_stooq.py:66: STOOQ_TEST_NETWORK=1 is not set
========= 4735 passed, 8 skipped, 2470 warnings in 633.07s (0:10:33) ==========
uv run python scripts/check_dependency_audit.py
accepted: PYSEC-2026-2447 (diskcache 5.6.3) - reachable only via the 'optimizer' extra, installed by 1 of 15 Dockerfiles; each installing command excludes diskcache by name; the dev group carries it too, and every sync passes --no-dev or excludes it by name; no fix release exists; every deployed optimizer installation excludes diskcache by name (S254, DL-266, ADR-0032) [DL-184] - retire when diskcache publishes a fixed release, or the optimizer extra is dropped
No unaccepted vulnerabilities; 1 accepted advisory re-checked
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
detect-secrets (untracked): no untracked files to scan
```

**Scope and amendment verification — actual output:**

```text
Branch and scope: PASS; exactly 11 authorized files; no .env; all excluded files unchanged.
Appendix blob and module sizes: PASS; result.py 154; test_parameter_values.py 173; LF bytes.
Law amendment: PASS; exact given clause; only OPR-FAIL-02 changed; no clause added.
Test-plan: PASS; all eight existing citations retained; B1-B4 cite OPR-FAIL-02; 20 / 51 unchanged.
Both operator version labels: PASS v1.10; DRIFT-112 corrected for S269 / DL-292.
agents/operator/tests/test_parameter_values.py | 173 +++++++++++++++++++++++++
 1 file changed, 173 insertions(+)
The '*test*' glob also matches the mandated laws/test-plan.md amendment; the Python-only glob shows one new test file.
```

**`make gate-ran`:** not the builder's: the planner runs it for the exact commit that merges.

**Not met / verified failing:** none of the builder's success factors. The eight environment/dependency-gated tests are skipped as pasted above; those scenarios are not done. Branch push, remote gate, merge, the planner's independent prototype/CodeQL checks and post-merge F1 are not done by the builder. No paid check or deploy is called for; vendor/live proof is not done.

---

## Return notes

- Scope held: the Appendix is the only production change, one new test file, the named law-cycle files, PATCH metadata and the two sprint handback files. All excluded paths, existing tests, `tests/fixtures/`, `.secrets.baseline`, `docs/STATE.md` and `docs/design-log.md` are unchanged.
- No disagreement after reading the laws. The given deliberate amendment is permitted by conventions §4; no new clause or guarantee is added, and no new design entry is owed.
- The first run reproduced 19 failed / 7 passed; the Appendix reproduced its exact LF blob. B4 checks two fresh graph/client contexts in one test, so the planned file collects 26 cases. Every canned reply uses neutral text, storage assertions decode JSON and the empty Intent tuple is checked as `()`.
- The broad `*test*` diff glob also matches the required `agents/operator/laws/test-plan.md` amendment; the Python-only diff shows exactly one new test file and no existing test changes. Both v1.10 labels were checked explicitly, because the law gate does not check them.
- `uv lock` resolved 180 packages successfully; its only diff is the virtual package version `0.125.6` → `0.125.7`. The lock was generated by uv, not edited manually, and staged with `pyproject.toml` `0.125.07`. Full CI retains existing warnings and the eight skips shown above; none is claimed as live proof.
- The planner still owns exact-commit `make gate-ran`, the independent Appendix/tests/break-script and CodeQL set-diff checks, then F1 on merged `main` (sixteen chat-handler cases, unconfirmed and confirmed). Those are not done here. No paid check and no deploy are needed.

---

## Planner's review at the merge — 2026-10-11

Re-measured by the planner in `../ta-s269` on the builder's commit `85add8c5`. Nothing here is
taken from the handback.

- **The code is the measured prototype byte for byte.** `git hash-object
  agents/operator/domain/result.py` prints `f47d86083f8091aa5b27e8d0e4abc99e92ba7be9`, the
  Appendix's blob id. The commit changes the eleven files the spec names and no other; no existing
  test is changed, and no working file was left with CRLF line endings.
- **Guards.** The planner's 12 breaks of `result.py`, one at a time against the operator's tests,
  each restored: **12 went red, none survived, none failed to apply**, and the restored tree is
  green.
- **The planner's own tests** (written for the prototype) were placed beside the builder's and run
  on the built code together with the builder's file and `tests/test_dspy_recipe.py`: 55 passed.
  They are not committed.
- **The law cycle, read by hand where the gate does not look.** `OPR-FAIL-02` is the given text,
  the law reads v1.10 and the Changelog has its line; the test-plan row keeps its eight citations
  and gains B1 to B4; the operator's row reads v1.10 in `docs/laws/INDEX.md` and in
  `docs/laws/ledger.md`; DRIFT-112 is marked corrected; the counts stand at 20 / 51.
- **`main` moved during the build:** S261's merge and its records. They were merged into this
  branch (`a3a769c8`); the two met in one file, `docs/sprints/README.md`, resolved row by row
  (S261's row is `main`'s, this sprint's is the branch's).
- **The handback's fifteen steps were every step its tree had.** S261 added the sixteenth, the
  tracker-size step, while this sprint was being built. On the merged tree that step exits 0 and
  warns twice: `docs/work-queue.md` at 91 % and `docs/sprints/README.md` at 93 % of their limits.
- **PATCH bump to `0.125.07`**; the change to `uv.lock` is the one version line.

**Written at the merge, before the gate — what was still owed then:** the planner's Windows
`make ci`, all sixteen steps, the remote gate and the CodeQL set-diff for the commit that holds
this block; then F1 at no cost.

**The gate and the merge.** Windows `make ci` exit 0 on the branch at `4b536d7e`: all sixteen steps,
4,748 passed, 8 skipped, 100.00 % coverage. `GATE PROVEN` for `4b536d7e`, run from `../ta-s269`, the
printed SHA equal to its `HEAD`: CI, CodeQL and Security Findings each `success`. Open CodeQL
alerts on the branch: 128, the same 128 as on the last merged branch; none at error level. `main`
fast-forwarded to that commit, tag `v0.125.07`.

**After the merge, 2026-10-11 ([functionality checks](../laws/functionality-checks.md)).**
*F1 passed*, at no cost: on the merged `main`, sixteen cases through the dashboard's chat handler,
each typed once and then confirmed, print what the prototype printed, line for line. Every `null`,
list and object under a required name is refused with S268's sentence, audited `refused`, no
`Intent` written; under a name that is not required it is left out and the intent is passed on.
No paid check and no deploy, as sequenced.

---

## Appendix — the function, measured on the planner's prototype

Replace `_params` in `agents/operator/domain/result.py` with exactly this. It is the last
function in the file. The file is then 154 lines and its blob id is
`f47d86083f8091aa5b27e8d0e4abc99e92ba7be9`.

```python
def _params(value: object) -> dict[str, str]:
    """Keep the parameters that hold text, a number or a boolean; drop every other."""
    if not isinstance(value, dict):
        return {}
    return {
        str(key): str(item)
        for key, item in value.items()
        if isinstance(item, (str, int, float))  # a bool is an int
    }
```
