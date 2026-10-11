<!-- Agent: planning | Role: sprint handover -->
# Sprint 269 — a parameter the model returns as null, a list or an object is no value

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-269-a-null-parameter-is-no-value`
**Status:** SPEC
**Version:** *next available PATCH at merge*
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

- [ ] Every row of the Test plan is a passing test that cites `OPR-FAIL-02`.
- [ ] `git hash-object agents/operator/domain/result.py` prints `f47d86083f8091aa5b27e8d0e4abc99e92ba7be9` on LF bytes, or the difference is explained.
- [ ] No existing test changed (`git diff --stat main -- '*test*'` shows the one new file).
- [ ] `tests/test_dspy_recipe.py` passes untouched and `tests/fixtures/` and `.secrets.baseline` are unchanged.
- [ ] Law cycle done, every item: clause text as given, v1.10, Changelog, test-plan row, the operator's row in `INDEX.md` and in `ledger.md`, DRIFT-112 corrected.
- [ ] Every guard planted, watched to fail, restored, stated per guard.
- [ ] Every touched module under 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

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
| <element> | <files> | <clause IDs> | <Yes/No + what changed> |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** <Yes/No + what it owed and what was done>

**Contradictions found between a law and this spec:** <none | what, and what you did>

**Laws found silent where a decision was needed:** <none | what, and the drift row filed>

**Clauses that were ⬜ and are now proven:** <IDs, and the rollup in ledger.md + INDEX.md>

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| B1 | <name> | <file> | PASS/FAIL | <clause IDs> |

**Tests added beyond the plan:** <none | what and why>

---

## Closeout — evidence

**Status:** <BUILT | MERGED>

**Tree the proofs ran in (and `.env` present?):** <path, branch, .env yes/no>

**Result:** <what is now true, in the artefact's own words — not the intent restated>

**Files changed:** <list>

**Design decisions:** recorded as [DL-292](../design-log.md); none added by the build.

**Proof — the red run first:**

```text
<the failing test output, before the implementation>
```

**Proof — the green run:**

```text
<the passing output>
```

**Guards planted:** <per guard: what was planted, that it failed, that it was restored>

**Module line counts:** <file **n**, file **n**>

**`make ci`:** redirected to `<path>`. Exit code <n>. `<N passed, M skipped>`, coverage `<100.00 %>`.
dependency audit `<result>`. detect-secrets `<result>`.

**`make gate-ran`:** not the builder's: the planner runs it for the exact commit that merges.

**Not met / verified failing:** <plainly, or "none">

---

## Return notes

- <Scope held / where it moved and why.>
- <What you disagreed with in the spec after reading the laws.>
- <What the next sprint should know that is not obvious from the diff.>

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
