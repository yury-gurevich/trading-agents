<!-- Agent: planning | Role: sprint handover -->
# Sprint 268 — an intent that lacks what its family needs is refused, and the model is told what each family needs

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-268-an-intent-that-lacks-what-its-family-needs-is-refused`
**Status:** MERGED 2026-10-11 — `0.125.06`, fast-forwarded to `e9f4f4a8`, tag `v0.125.06`, GATE PROVEN `e9f4f4a8` (CI, CodeQL, Security Findings); no deploy; F1a passed at no cost; F1b passed on OpenAI ($0.04), not run on Anthropic
**Version:** `0.125.06` (PATCH)
**Effort:** S
**Decisions:** [DL-290](../design-log.md) (this sprint's seven decisions, made and measured) · [DL-286](../design-log.md) (where the defect was met) · [work-queue 126](../work-queue.md) · DRIFT-109

> **Why this bump kind.** No new capability: `OPR-FAIL-02` already says an intent with missing
> required fields is refused, and the code passes it on. The clause is reworded to say exactly what
> is checked; no clause is added.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/operator/laws/laws.md` | The operator's **locked constitution** (v1.8) | **LOCKED.** This sprint rewords one clause, `OPR-FAIL-02`, with the text given below, and touches no other |
| `agents/operator/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | The `OPR-FAIL-02` row gains the new tests |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | `drift-register.md`: DRIFT-109 is marked corrected |

Binding sections here: **`OPR-FAIL`**, **`OPR-OUT`**, **`OPR-NEV`**, **`OPR-IN`**.

### The rule

1. **Before writing code**, read `agents/operator/laws/laws.md` and its `test-plan.md`, whole.
2. Read [`docs/laws/conventions.md`](../laws/conventions.md) and the DRIFT-109 row of
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
3. **Write the Law reading record** (bottom of this file) **before** your first code change.
4. **If a law contradicts this spec, STOP and report.**
5. Every test for behaviour a clause governs **cites the clause ID in its docstring**.

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**No file in `contracts/` changes. One clause is reworded, none is added.** The cycle owed:

- `OPR-FAIL-02` in `agents/operator/laws/laws.md` is replaced by this text, the version goes to
  v1.9 and the Changelog gains one line (`v1.9 — S268 / DL-290 (2026-10-11): rewords OPR-FAIL-02`):

  > - **OPR-FAIL-02** — A reply whose outcome is `intent` is checked before anything is written
  >   for it. It is refused when its family is absent, is not a string or is not one of the
  >   grammar's families, and when it lacks a parameter the grammar marks required for its family.
  >   A required parameter is given when any of its accepted names holds a value that is not blank.
  >   `interpret` then returns `CommandResult(outcome="refused", ...)` with a message that says so
  >   (for a missing parameter it names the family and each missing parameter by its first accepted
  >   name), the `CommandAudit` reads `refused` and no `Intent` is written. The check runs after
  >   the explicit command grammar, so a typed approve is not refused for the model's omission. A
  >   reply whose outcome is not `intent` is not checked. The system prompt states each family's
  >   parameter names. The sentences are pinned by tests, not quoted here.

- The `OPR-FAIL-02` row of `test-plan.md` cites every test of the Test plan below.
- DRIFT-109 is marked corrected, with the sprint and the DL.
- The rollups in `docs/laws/ledger.md` and `docs/laws/INDEX.md` are recomputed by `make ci`; the
  clause was already 🟩, so expect no change in the counts. Let the gate say.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/operator/domain/grammar.py` | operator `laws.md` + `test-plan.md` | `OPR-FAIL-02`; the confirmation policy of `OPR-OUT-07` must not move |
| `agents/operator/domain/result.py`, `agents/operator/agent.py` | same | `OPR-FAIL-02`, `OPR-OUT-05`, `OPR-OUT-06`, `OPR-FAIL-01`, `OPR-FAIL-04` |
| `agents/operator/domain/prompts.py` | same | `OPR-IN-01`; the prompt recipe hash of `OPR-STA-03` changes with the source |

⚠️ **The failed-request path (S265) and the cut-off path (S264) must not move.** A request that
fails is still read by `failed_request` and is not checked; a cut-off reply still goes through
the explicit grammar. If your change alters any test in `test_failed_request_*.py` or
`test_cutoff_*.py`, stop and report.

---

## Goal

When the model answers `interpret` with an intent, the operator agent passes it on only if its
family is one of the grammar's and every parameter that family cannot do without is given under a
name its readers take. Otherwise the result is a refusal that says what is missing, the audit reads
`refused` and no `Intent` is written. The system prompt tells the model each family's parameter
names and to ask for clarification when the command does not give one.

## Why (context)

`OPR-FAIL-02` says an intent with missing required fields is refused. Measured on 2026-10-10
(DL-286, DRIFT-109): `approve` with no target, `modify` with no name or value and a reply with no
family at all are each passed on as an intent, the last as `status`. An `approve` that names
nothing then reaches the supervisor asking for confirmation of nothing. It is not on the fleet's
path (the operator container binds the fake client); it is on the dashboard chat's.

### Measured, 2026-10-11 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| The grammar's `params` are read by no code | 0 readers | *[measured]* `grep` for `.params` and `INTENT_FAMILIES` over the tree: `prompts.py` reads the family names and descriptions only |
| The model is told no parameter name | none | *[read]* `build_interpret_system` joins `name: description`; `INTENT_TOOL_SCHEMA["parameters"]` is a bare object |
| The readers take other names than the grammar lists | 3 families | *[read]* `agents/supervisor/domain/gate.py`: `approve` reads `subject` or `target`; `stage` reads `stage` or `target`; `resume` reads `from_stage` or `stage` |
| `explain` works with no `subject` | falls back | *[read]* `surfaces/operator_tools.py`: `intent.parameters.get("subject") or text` |
| `resume`'s `run_id` is supplied after the operator answers | by the surface | *[read]* `surfaces/operator_tools.py` adds the selected run's id to a `resume` intent |
| No reader takes `run`'s `stage`, except the hard-NO for `live` | 1 reader | *[read]* `agents/supervisor/domain/hard_no.py` |
| An unknown family is refused today, and its audit reads `intent` | as stated | *[read]* `_interpret_command` writes the audit before `intent_from_data` returns `None` |
| The prototype breaks three existing tests and no other | 3 of 4,675 | *[measured]* full suite in the sprint worktree, `--no-cov`: `test_interpret_maps_all_ten_families_with_confirmation_policy`, `test_result_helpers_normalize_invalid_or_refused_output`, `test_dspy_version_changes_only_the_deliberator_recipe` |
| With the three edited and the new tests added | 4,710 passed, 7 skipped | *[measured]* the same run after the edits |
| The prototype's guards can fail | 19 breaks, 19 red | *[measured]* one break at a time on the operator's tests, tree restored and green after |
| The operator recipe hash after the change | `43df2c61922b478cb4dc0c505fb9f104f6b3d07d2a65093fd8dd5af72b621392` | *[measured]* on the prototype's bytes, LF line endings; before: `3fcfed8f…` |
| Which names each real model returns per family today | not known | *[ASSUMED — not measured]* it needs paid calls on both vendors; it is this sprint's F1b, on the operator's word |
| What the unattended scorecard counts for a refusal of this kind | not known | *[ASSUMED — not measured]* DL-286 read that an audit with no intent and an outcome other than `explain` counts as a human action; not re-read here |

---

## Scope — and what is deliberately NOT here

1. **The grammar says what each family cannot do without.** `FamilySpec` gains `required`: one
   tuple of accepted names for each required parameter, the first being the name told to the model.
   `missing_parameters(family, parameters)` returns the first accepted name of each required
   parameter that no accepted name gives with a value that is not blank.
2. **The reply is checked before the audit is written.** `checked_intent` in `result.py` turns an
   intent of no known family, or lacking a required parameter, into a refusal with a fixed
   sentence. `_interpret_command` applies it to the output of the explicit grammar.
   `intent_from_data` then always builds an intent and returns no `None`.
3. **The system prompt states each family's parameter names** and tells the model to ask for
   clarification when the command does not give one the intent cannot do without.
4. **Tests**, per the Test plan, and the three existing tests edited as named there.
5. **The law cycle** as answered above.

The production change is the diff in the Appendix. Apply it as it stands.

### Out of scope (do NOT build this sprint)

- **`INTENT_TOOL_SCHEMA` does not change.** Whether either vendor accepts a schema with per-family
  parameter properties is not measured.
- **The supervisor's gate, the hard-NO list and `surfaces/` do not change.** That a `run` with no
  stage passes the hard-NO for `live` is as it was; it is named in DL-290, not mended here.
- **The explain path, the failed-request path and the cut-off path do not change.**
- **No value is validated.** A `stage` of `banana` is still the supervisor's to refuse.
- **No new clause, no ADR reversal, no file in `contracts/`.**

### The road not taken (LAW-06)

- **Reword the clause to what the code does.** Rejected: an `approve` that names nothing asks the
  operator to confirm nothing.
- **Refuse on the grammar's `params` as they stand.** Rejected: it would refuse an `explain` with
  no `subject`, a `resume` whose `run_id` the surface supplies, and an `approve` given as `subject`.
- **Rename the parameters in the supervisor to one name each.** Rejected here: a second agent's
  law cycle for no gain; the grammar accepts the names the readers take.
- **Describe the parameters in the tool schema.** Rejected for now: not measured on either vendor.

---

## The design decisions — made, and recorded in DL-290

They are recorded with their rejected alternatives. **Do not add a design-log entry.**

1. Required: `approve` and `reject` a `target` (or `subject`); `modify` a `name` and a `value`;
   `mode` a `mode`; `stage` a `stage` (or `target`); `resume` a `stage` (or `from_stage`).
2. Not required: `explain`'s `subject`, `run`'s `stage`, `resume`'s `run_id`; `status` and `pause`
   take none.
3. A blank value is a missing one. A `parameters` that is not an object is no parameters.
4. An intent with no family, a family that is not a string, or an unknown one is refused with one
   fixed sentence; the model's own `reason` is not shown for it.
5. The check runs after the explicit grammar and only on an `intent`.
6. The audit of a refused intent reads `refused` (for an unknown family it read `intent`).
7. The prompt names the parameters; the tool schema is left alone.

---

## Blast radius — measured 2026-10-11

| What | Detail |
| --- | --- |
| Files changed | `agents/operator/agent.py` (174 → 175), `domain/grammar.py` (84 → 109), `domain/result.py` (123 → 149), `domain/prompts.py` (68 → 73); tests: `test_operator_agent.py` (186 → 197 on the prototype), `test_operator_grammar.py`, one new test file; `tests/fixtures/guided_turn_main_records.json` (one hash); operator `laws.md`, `test-plan.md`; `drift-register.md` |
| Agents affected | operator only; it imports no other agent |
| Contract change? | No |
| Graph vocabulary change? | No |
| New env keys / tunables | None |
| Deploy implication | None needed: the chat runs in the dashboard and the fleet's operator container binds the fake client. The code reaches the image with the next retag |
| Rollback | Nothing beyond the retag |

---

## Steps, in order

1. **Read the laws** and write the Law reading record.
2. **Plant the failing tests first** (Test plan) and watch them fail on the unchanged code. Paste the red output.
3. **Apply the Appendix diff.**
4. **Edit the three existing tests** as the Test plan says.
5. **Law cycle** as answered above.
6. **Prove the guards can fail (DL-70):** at least the breaks listed under Traps, one at a time, each red, each restored.
7. **`make ci` green**, every step of the `ci:` target, **redirected to a file, never piped**.
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

New file `agents/operator/tests/test_required_parameters.py`. Each test drives the real
`OperatorAgent` on an in-memory graph with a canned reply, except A6 and A7.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 an intent lacking a required parameter is refused | parametrised: `approve` `{}`; `reject` `{}`; `modify` `{}`, name only, value only; `mode` `{}`; `stage` `{}`; `resume` with `run_id` only; `approve` with a blank `target`; `approve` with `parameters` a string; `stage` given as `Stage` | outcome `refused`, no intent, the message equals `missing_parameters_reply(family, missing)`, the one `CommandAudit` reads `refused`, 0 `Intent`, 1 `LLMCall` |
| A2 | an intent with what its family needs is passed on | parametrised: `status`, `pause`, `explain` and `run` with `{}`; `run` with `parameters` a string; `approve` by `target` and by `subject`; `reject` by `subject`; `modify` with both; `mode`; `stage` by `stage` and by `target`; `resume` by `stage` and by `from_stage` | outcome `intent`, the family, the parameters unchanged, the audit reads `intent`, 1 `Intent` |
| A3 | 🪤 an intent of no known family is refused | parametrised: no `family`; `bogus` with a `reason`; a list; `None` with a target; `Status` | outcome `refused`, the message equals `UNKNOWN_FAMILY_REPLY`, the audit reads `refused`, 0 `Intent` |
| A4 | a reply that is not an intent is not checked | `refused` and `needs_clarification`, each with family `approve`, no parameters and a `reason` | the outcome and the reason are the model's; the audit reads the same outcome |
| A5 | the explicit approve grammar supplies the target before the check | text `approve flag:case-1`, reply `approve` with no parameters | outcome `intent`, family `approve`, parameters `{"target": "flag:case-1"}` |
| A6 | `missing_parameters` names the first accepted name, in order | direct calls | `modify` `{}` gives `("name", "value")`; `resume` with a blank `from_stage` gives `("stage",)`; with `from_stage` given and `stage` empty gives `()`; and the two sentences, letter for letter |
| A7 | the grammar and the prompt state what is required | `INTENT_FAMILIES`, `build_interpret_system()` | exactly six families have a requirement; each required parameter's first name is in that family's `params`; the prompt holds `family: description (parameters: a, b)` for each family with parameters and no bracket for the others; the prompt holds `under exactly the name listed` and `ask for clarification; never guess it.` |

Existing tests to edit, and no other:

- `test_operator_agent.py::test_interpret_maps_all_ten_families_with_confirmation_policy`: its
  canned replies give `reject`, `modify`, `mode`, `stage` and `resume` the parameters they need.
  🪤 The file must stay under 200 lines (197 on the prototype).
- `test_operator_grammar.py::test_result_helpers_normalize_invalid_or_refused_output`: the line
  asserting `intent_from_data({"family": "not-real"}, "corr") is None` becomes an assertion that
  `checked_intent` reads that intent as a refusal carrying `UNKNOWN_FAMILY_REPLY`.
- `tests/fixtures/guided_turn_main_records.json`: `operator_prompt_recipe_hash` takes the hash
  your tree computes. It is expected to be the value in the Measured table.

---

## Success factors

- [x] Every row of the Test plan is a passing test that cites `OPR-FAIL-02`.
- [x] The production diff equals the Appendix (`git diff main -- agents/operator/agent.py agents/operator/domain`).
      *(As handed back. The planner then changed one word of the refusal sentence: see the review.)*
- [x] No test in `test_failed_request_*.py` or `test_cutoff_*.py` changed.
- [x] Exactly the three existing tests named above changed.
- [x] The operator recipe hash equals the Measured table's, or the difference is explained.
- [x] Law cycle done: clause text as given, v1.9, Changelog, test-plan row, DRIFT-109 corrected.
- [x] Every guard planted, watched to fail, restored, stated per guard.
- [x] Every touched module under 200 lines.
- [x] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **The recipe hash is computed from source bytes.** A working file with CRLF line endings gives
another hash than CI computes. Check `git ls-files --eol agents/operator/domain` before you read
the hash, and take the fixture's value from a tree whose files are LF.
🪤 **`test_dspy_recipe.py` goes red on any change to `grammar.py` or `prompts.py`.** It is not a
guard for this sprint's behaviour: run the breaks on `agents/operator` alone.
🪤 **A canned reply is matched by a substring of the prompt.** A test text that begins with
`approve ` is rewritten by the explicit grammar. Use a neutral text and a key that occurs nowhere else.
🪤 **`graph.list_nodes` returns a tuple.** Compare with `()`, not `[]`; `mypy` refuses the other.
🪤 **Putting the check before the explicit grammar changes nothing observable**, because the
grammar always produces a complete `approve`. It is not a guard; do not count it as one.

Breaks to plant, at the least: the check not applied; a reply that is not an intent checked too;
the unknown-family sentence replaced by the model's reason; a missing parameter not refused; the
last accepted name reported; a blank value counted as given; only the first accepted name read;
`resume` requiring nothing; `run` requiring a stage; `explain` requiring a subject; the prompt
without the parameter list; the prompt without the clarification sentence.

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
2. The planner re-measures: the diff against the Appendix, the planner's own test file and break
   script run on the built tree, the open CodeQL alerts set-diffed against `main`'s.
3. **F1a**, at no cost, on the merged `main`: the cases of A1 to A5 through the chat handler.
4. **F1b**, paid, on the operator's word and priced first: on each vendor, one typed command for
   each of the six families with a requirement, reading which names come back and whether a
   command that omits one is answered with a question.
5. No deploy.

---

## Handover — paste this to Codex

```text
You are building Sprint 268 in the worktree ../ta-s268, on the branch
sprint-268-an-intent-that-lacks-what-its-family-needs-is-refused. Never work on main.

Read docs/sprints/sprint-268-an-intent-that-lacks-what-its-family-needs-is-refused.md, whole,
before anything else. It is the spec, and its bottom sections are your handback.

In order:
1. Read agents/operator/laws/laws.md and test-plan.md, docs/laws/conventions.md and the DRIFT-109
   row of docs/laws/drift-register.md. Fill the Law reading record in the spec BEFORE any code.
2. Write the tests of the Test plan in agents/operator/tests/test_required_parameters.py. Run
   them on the unchanged code and paste the red output into the Closeout.
3. Apply the diff in the spec's Appendix to the four production files exactly as it stands.
4. Edit the three existing tests the Test plan names, and no other test.
5. Do the law cycle the spec answers: replace OPR-FAIL-02 with the given text, laws.md to v1.9
   with a Changelog line, the test-plan row, DRIFT-109 marked corrected.
6. Plant the breaks listed under Traps one at a time on agents/operator; each must go red; restore.
7. Bump the version (PATCH) and stage uv.lock. Run make ci redirected to a file and read the file.
8. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in the sprint's
   row of docs/sprints/README.md.

DO NOT: change INTENT_TOOL_SCHEMA, the supervisor, surfaces/, contracts/, or any test in
test_failed_request_*.py or test_cutoff_*.py; add a design-log entry; add a law clause; use
noqa; let any module reach 200 lines; measure make ci through a pipe.

Traps: the recipe hash is computed from source bytes, so read it from LF files
(git ls-files --eol); graph.list_nodes returns a tuple; a canned reply is matched by a substring
of the prompt and a text beginning with "approve " is rewritten by the explicit grammar.

If a law contradicts the spec, or the Appendix diff does not apply cleanly, STOP and report.
State anything not done as "not done" or "verified failing". Never write a Result for work you
have not done.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** before your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02).

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| `domain/grammar.py` | `agents/operator/laws/laws.md` v1.8 and `test-plan.md`, whole | `OPR-FAIL-02`, `OPR-OUT-07`, `OPR-NEV-01`, `OPR-NEV-02` | No redesign: apply the Appendix; accepted names follow DL-290 and confirmation policy stays grammar-owned. |
| `domain/result.py`, `agent.py` | Same operator laws and test-plan, whole | `OPR-FAIL-02`, `OPR-OUT-05`, `OPR-OUT-06`, `OPR-FAIL-01`, `OPR-FAIL-04` | Check only an intent, after explicit grammar and before audit; failed-request and cut-off guarantees remain binding. |
| `domain/prompts.py` | Same operator laws and test-plan, whole | `OPR-IN-01`, `OPR-STA-03`, `OPR-NEV-05` | State parameter names in the prompt; keep `INTENT_TOOL_SCHEMA` unchanged; compute the recipe from LF bytes. |
| New tests and the three named existing tests | Same operator laws and test-plan, whole; `docs/laws/conventions.md`, whole; `docs/laws/drift-register.md` DRIFT-109 | `OPR-FAIL-02`; conventions sections 2, 3, 4, 7, 7a | Every planned test cites the clause; red proof precedes implementation; guards are planted one at a time. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No. No contract file changes and no clause is added. The authorized amendment rewords `OPR-FAIL-02`, bumps the operator law to v1.9 with the given Changelog line, expands its existing green test-plan row and marks DRIFT-109 corrected (S268 / DL-290). Rollup counts are left to `make ci`.

**Contradictions found between a law and this spec:** None beyond the stale `OPR-FAIL-02` parsing description explicitly identified by DRIFT-109 and authorized for correction here. Its intended refusal agrees with this spec. Repository workflow discrepancy: AGENTS.md requires merge permission while CLAUDE.md retires it; this build follows the user's stricter instruction to stay in this worktree and never work on main.

**Laws found silent where a decision was needed:** The required families, aliases and blank-value rule were not enumerated by v1.8. DL-290 and the Appendix already decide them; no new decision or design-log entry is needed.

**Clauses that were ⬜ and are now proven:** None. `OPR-FAIL-02` was already green; its amended guarantee is re-proven by all 35 planned cases. The law-coverage gate accepted the unchanged operator rollup of 20 / 51 in both ledger and INDEX.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a1_missing_required_parameter_is_refused` | `agents/operator/tests/test_required_parameters.py` | PASS (11 cases) | `OPR-FAIL-02` |
| A2 | `test_a2_complete_family_parameters_are_passed_on` | `agents/operator/tests/test_required_parameters.py` | PASS (14 cases) | `OPR-FAIL-02` |
| A3 | `test_a3_unknown_family_is_refused` | `agents/operator/tests/test_required_parameters.py` | PASS (5 cases) | `OPR-FAIL-02` |
| A4 | `test_a4_non_intent_reply_is_not_checked` | `agents/operator/tests/test_required_parameters.py` | PASS (2 cases) | `OPR-FAIL-02` |
| A5 | `test_a5_explicit_approve_supplies_target_before_check` | `agents/operator/tests/test_required_parameters.py` | PASS (1 case) | `OPR-FAIL-02` |
| A6 | `test_a6_missing_names_and_refusal_sentences_are_pinned` | `agents/operator/tests/test_required_parameters.py` | PASS (1 case) | `OPR-FAIL-02` |
| A7 | `test_a7_grammar_requirements_and_prompt_parameters_are_declared` | `agents/operator/tests/test_required_parameters.py` | PASS (1 case) | `OPR-FAIL-02` |

**Tests added beyond the plan:** None. Seven test functions, 35 parametrized cases, exactly A1–A7.

---

## Closeout — evidence

**Status:** MERGED

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/Downloads/project/ta-s268`, branch `sprint-268-an-intent-that-lacks-what-its-family-needs-is-refused`, base HEAD `b8f112af6437eb87f725fc9019371b03f3d19292`. `.env` present: False. All proofs used this worktree; no main worktree edit. Changes remain uncommitted; version and lock are staged.

**Result:** A model intent without a known family or a required nonblank parameter is refused before its command audit and intent write; the audit reads `refused` and no `Intent` is written. Accepted aliases, optional fields, non-intents and explicit approve behave as specified. Proven: all 35 planned cases, 143 operator tests, twelve red/restored breaks, and full `make ci` exit 0 (4709 passed, 8 skipped, 2470 warnings in 661.53s (0:11:01), 100.00 % coverage). Production bytes equal the Appendix; recipe `43df2c61922b478cb4dc0c505fb9f104f6b3d07d2a65093fd8dd5af72b621392` matches the measured LF tree.

**Files changed:**

- `agents/operator/agent.py`
- `agents/operator/domain/grammar.py`
- `agents/operator/domain/prompts.py`
- `agents/operator/domain/result.py`
- `agents/operator/tests/test_required_parameters.py`
- `agents/operator/tests/test_operator_agent.py`
- `agents/operator/tests/test_operator_grammar.py`
- `tests/fixtures/guided_turn_main_records.json`
- `agents/operator/laws/laws.md`
- `agents/operator/laws/test-plan.md`
- `.secrets.baseline`
- `docs/laws/drift-register.md`
- `docs/sprints/sprint-268-an-intent-that-lacks-what-its-family-needs-is-refused.md`
- `docs/sprints/README.md`
- `docs/STATE.md`
- `pyproject.toml`
- `uv.lock`

`docs/STATE.md` records the intent and proven result required by CLAUDE.md; no design-log entry was added. Independent scope/Appendix measurement output:

```text
Appendix applies to main snapshot: exit 0
Appendix byte equality: agents/operator/agent.py
Appendix byte equality: agents/operator/domain/grammar.py
Appendix byte equality: agents/operator/domain/prompts.py
Appendix byte equality: agents/operator/domain/result.py
INTENT_TOOL_SCHEMA AST unchanged
Exactly three named existing test/fixture files changed
Every other existing test function AST unchanged
Fixture changed only operator_prompt_recipe_hash
Supervisor, surfaces, contracts, design-log, failed-request and cut-off test files unchanged
.env present: False
Module lines: agents/operator/agent.py = 175
Module lines: agents/operator/domain/grammar.py = 109
Module lines: agents/operator/domain/prompts.py = 73
Module lines: agents/operator/domain/result.py = 149
Module lines: agents/operator/tests/test_operator_agent.py = 197
Module lines: agents/operator/tests/test_operator_grammar.py = 141
Module lines: agents/operator/tests/test_required_parameters.py = 193
New test file contains no noqa
```

**Proof — the red run first:** `git diff --exit-code -- agents/operator/agent.py agents/operator/domain/grammar.py agents/operator/domain/result.py agents/operator/domain/prompts.py` exit 0 before the run (unchanged production). `uv run --frozen pytest agents/operator/tests/test_required_parameters.py --no-cov`, exit 1. Output pasted in full:

```text
============================= test session starts =============================
collected 35 items

agents\operator\tests\test_required_parameters.py FFFFFFFFFFF........... [ 62%]
...FFFFF...FF                                                            [100%]

================================== FAILURES ===================================
_ test_a1_missing_required_parameter_is_refused[approve-parameters0-missing0] _
agents\operator\tests\test_required_parameters.py:49: in test_a1_missing_required_parameter_is_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
_ test_a1_missing_required_parameter_is_refused[reject-parameters1-missing1] __
agents\operator\tests\test_required_parameters.py:49: in test_a1_missing_required_parameter_is_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
_ test_a1_missing_required_parameter_is_refused[modify-parameters2-missing2] __
agents\operator\tests\test_required_parameters.py:49: in test_a1_missing_required_parameter_is_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
_ test_a1_missing_required_parameter_is_refused[modify-parameters3-missing3] __
agents\operator\tests\test_required_parameters.py:49: in test_a1_missing_required_parameter_is_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
_ test_a1_missing_required_parameter_is_refused[modify-parameters4-missing4] __
agents\operator\tests\test_required_parameters.py:49: in test_a1_missing_required_parameter_is_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
__ test_a1_missing_required_parameter_is_refused[mode-parameters5-missing5] ___
agents\operator\tests\test_required_parameters.py:49: in test_a1_missing_required_parameter_is_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
__ test_a1_missing_required_parameter_is_refused[stage-parameters6-missing6] __
agents\operator\tests\test_required_parameters.py:49: in test_a1_missing_required_parameter_is_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
_ test_a1_missing_required_parameter_is_refused[resume-parameters7-missing7] __
agents\operator\tests\test_required_parameters.py:49: in test_a1_missing_required_parameter_is_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
_ test_a1_missing_required_parameter_is_refused[approve-parameters8-missing8] _
agents\operator\tests\test_required_parameters.py:49: in test_a1_missing_required_parameter_is_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
_ test_a1_missing_required_parameter_is_refused[approve-not an object-missing9] _
agents\operator\tests\test_required_parameters.py:49: in test_a1_missing_required_parameter_is_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
_ test_a1_missing_required_parameter_is_refused[stage-parameters10-missing10] _
agents\operator\tests\test_required_parameters.py:49: in test_a1_missing_required_parameter_is_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
__________________ test_a3_unknown_family_is_refused[data0] ___________________
agents\operator\tests\test_required_parameters.py:105: in test_a3_unknown_family_is_refused
    assert result.outcome == "refused"
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
__________________ test_a3_unknown_family_is_refused[data1] ___________________
agents\operator\tests\test_required_parameters.py:107: in test_a3_unknown_family_is_refused
    _audit(graph, "refused")
agents\operator\tests\test_required_parameters.py:191: in _audit
    assert audit.props["outcome"] == outcome
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
__________________ test_a3_unknown_family_is_refused[data2] ___________________
agents\operator\tests\test_required_parameters.py:107: in test_a3_unknown_family_is_refused
    _audit(graph, "refused")
agents\operator\tests\test_required_parameters.py:191: in _audit
    assert audit.props["outcome"] == outcome
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
__________________ test_a3_unknown_family_is_refused[data3] ___________________
agents\operator\tests\test_required_parameters.py:107: in test_a3_unknown_family_is_refused
    _audit(graph, "refused")
agents\operator\tests\test_required_parameters.py:191: in _audit
    assert audit.props["outcome"] == outcome
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
__________________ test_a3_unknown_family_is_refused[data4] ___________________
agents\operator\tests\test_required_parameters.py:107: in test_a3_unknown_family_is_refused
    _audit(graph, "refused")
agents\operator\tests\test_required_parameters.py:191: in _audit
    assert audit.props["outcome"] == outcome
E   AssertionError: assert 'intent' == 'refused'
E
E     - refused
E     + intent
___________ test_a6_missing_names_and_refusal_sentences_are_pinned ____________
agents\operator\tests\test_required_parameters.py:141: in test_a6_missing_names_and_refusal_sentences_are_pinned
    assert grammar.missing_parameters("modify", {}) == ("name", "value")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: module 'agents.operator.domain.grammar' has no attribute 'missing_parameters'
_______ test_a7_grammar_requirements_and_prompt_parameters_are_declared _______
agents\operator\tests\test_required_parameters.py:159: in test_a7_grammar_requirements_and_prompt_parameters_are_declared
    name for name, spec in grammar.INTENT_FAMILIES.items() if spec.required
                                                              ^^^^^^^^^^^^^
E   AttributeError: 'FamilySpec' object has no attribute 'required'
=========================== short test summary info ===========================
FAILED agents/operator/tests/test_required_parameters.py::test_a1_missing_required_parameter_is_refused[approve-parameters0-missing0]
FAILED agents/operator/tests/test_required_parameters.py::test_a1_missing_required_parameter_is_refused[reject-parameters1-missing1]
FAILED agents/operator/tests/test_required_parameters.py::test_a1_missing_required_parameter_is_refused[modify-parameters2-missing2]
FAILED agents/operator/tests/test_required_parameters.py::test_a1_missing_required_parameter_is_refused[modify-parameters3-missing3]
FAILED agents/operator/tests/test_required_parameters.py::test_a1_missing_required_parameter_is_refused[modify-parameters4-missing4]
FAILED agents/operator/tests/test_required_parameters.py::test_a1_missing_required_parameter_is_refused[mode-parameters5-missing5]
FAILED agents/operator/tests/test_required_parameters.py::test_a1_missing_required_parameter_is_refused[stage-parameters6-missing6]
FAILED agents/operator/tests/test_required_parameters.py::test_a1_missing_required_parameter_is_refused[resume-parameters7-missing7]
FAILED agents/operator/tests/test_required_parameters.py::test_a1_missing_required_parameter_is_refused[approve-parameters8-missing8]
FAILED agents/operator/tests/test_required_parameters.py::test_a1_missing_required_parameter_is_refused[approve-not an object-missing9]
FAILED agents/operator/tests/test_required_parameters.py::test_a1_missing_required_parameter_is_refused[stage-parameters10-missing10]
FAILED agents/operator/tests/test_required_parameters.py::test_a3_unknown_family_is_refused[data0]
FAILED agents/operator/tests/test_required_parameters.py::test_a3_unknown_family_is_refused[data1]
FAILED agents/operator/tests/test_required_parameters.py::test_a3_unknown_family_is_refused[data2]
FAILED agents/operator/tests/test_required_parameters.py::test_a3_unknown_family_is_refused[data3]
FAILED agents/operator/tests/test_required_parameters.py::test_a3_unknown_family_is_refused[data4]
FAILED agents/operator/tests/test_required_parameters.py::test_a6_missing_names_and_refusal_sentences_are_pinned
FAILED agents/operator/tests/test_required_parameters.py::test_a7_grammar_requirements_and_prompt_parameters_are_declared
======================== 18 failed, 17 passed in 3.18s ========================
```

**Proof — the green run:** `uv run --frozen pytest agents/operator --no-cov` before the guards: exit 0, `143 passed in 1.61s`. The guard script's final identical command after restoring all source bytes: exit 0; full output follows.

```text
============================= test session starts =============================
collected 143 items

agents\operator\tests\test_cutoff_adapter.py .........                   [  6%]
agents\operator\tests\test_cutoff_agent.py ..........                    [ 13%]
agents\operator\tests\test_cutoff_ledger.py .....                        [ 16%]
agents\operator\tests\test_failed_request_agent.py ...                   [ 18%]
agents\operator\tests\test_failed_request_faults.py .......              [ 23%]
agents\operator\tests\test_failed_request_ledger.py .....                [ 27%]
agents\operator\tests\test_failed_request_result.py .................... [ 41%]
..                                                                       [ 42%]
agents\operator\tests\test_operator_agent.py ......                      [ 46%]
agents\operator\tests\test_operator_approve_routing.py ......            [ 51%]
agents\operator\tests\test_operator_boundary.py ..                       [ 52%]
agents\operator\tests\test_operator_entrypoint.py .                      [ 53%]
agents\operator\tests\test_operator_evidence_flags.py ..                 [ 54%]
agents\operator\tests\test_operator_grammar.py .......                   [ 59%]
agents\operator\tests\test_operator_llm.py ........                      [ 65%]
agents\operator\tests\test_operator_llm_usage.py ....                    [ 67%]
agents\operator\tests\test_operator_settings.py ........                 [ 73%]
agents\operator\tests\test_operator_store.py .                           [ 74%]
agents\operator\tests\test_provider_model.py ..                          [ 75%]
agents\operator\tests\test_required_parameters.py ...................... [ 90%]
.............                                                            [100%]

============================= 143 passed in 1.82s =============================
```

**Guards planted:** All twelve listed under Traps, one at a time, running `python -m pytest agents/operator --no-cov` for each. Every process exited 1 and failed a planned test; each source restoration was asserted equal to its saved bytes before the next break. No full-suite recipe test counted as a guard. Pasted failure lines and final pytest lines per guard:

```text
G01 — check not applied — exit 1; restored exact bytes
FAILED agents/operator/tests/test_required_parameters.py::test_a1_missing_required_parameter_is_refused[approve-parameters0-missing0]
======================= 16 failed, 127 passed in 2.05s ========================
G02 — non-intent replies checked too — exit 1; restored exact bytes
FAILED agents/operator/tests/test_required_parameters.py::test_a4_non_intent_reply_is_not_checked[refused]
======================== 4 failed, 139 passed in 1.69s ========================
G03 — unknown family uses model reason — exit 1; restored exact bytes
FAILED agents/operator/tests/test_required_parameters.py::test_a3_unknown_family_is_refused[data1]
======================== 1 failed, 142 passed in 2.35s ========================
G04 — missing parameter not refused — exit 1; restored exact bytes
FAILED agents/operator/tests/test_required_parameters.py::test_a1_missing_required_parameter_is_refused[approve-parameters0-missing0]
======================= 11 failed, 132 passed in 1.99s ========================
G05 — last accepted name reported — exit 1; restored exact bytes
FAILED agents/operator/tests/test_required_parameters.py::test_a1_missing_required_parameter_is_refused[approve-parameters0-missing0]
======================== 8 failed, 135 passed in 1.82s ========================
G06 — blank value counted as given — exit 1; restored exact bytes
FAILED agents/operator/tests/test_required_parameters.py::test_a1_missing_required_parameter_is_refused[approve-parameters8-missing8]
======================== 2 failed, 141 passed in 1.67s ========================
G07 — only first accepted name read — exit 1; restored exact bytes
FAILED agents/operator/tests/test_required_parameters.py::test_a2_complete_family_parameters_are_passed_on[approve-parameters6]
======================== 6 failed, 137 passed in 1.95s ========================
G08 — resume requires nothing — exit 1; restored exact bytes
FAILED agents/operator/tests/test_required_parameters.py::test_a1_missing_required_parameter_is_refused[resume-parameters7-missing7]
======================== 3 failed, 140 passed in 1.65s ========================
G09 — run requires a stage — exit 1; restored exact bytes
FAILED agents/operator/tests/test_required_parameters.py::test_a2_complete_family_parameters_are_passed_on[run-parameters3]
======================== 5 failed, 138 passed in 1.69s ========================
G10 — explain requires a subject — exit 1; restored exact bytes
FAILED agents/operator/tests/test_required_parameters.py::test_a2_complete_family_parameters_are_passed_on[explain-parameters2]
======================== 3 failed, 140 passed in 1.63s ========================
G11 — prompt omits parameter lists — exit 1; restored exact bytes
FAILED agents/operator/tests/test_required_parameters.py::test_a7_grammar_requirements_and_prompt_parameters_are_declared
======================== 1 failed, 142 passed in 1.60s ========================
G12 — prompt omits clarification sentence — exit 1; restored exact bytes
FAILED agents/operator/tests/test_required_parameters.py::test_a7_grammar_requirements_and_prompt_parameters_are_declared
======================== 1 failed, 142 passed in 1.66s ========================
```

**Module line counts:** Every touched Python module is below 200; the gate also passed the repository size check.

```text
agents/operator/agent.py = 175
agents/operator/domain/grammar.py = 109
agents/operator/domain/prompts.py = 73
agents/operator/domain/result.py = 149
agents/operator/tests/test_operator_agent.py = 197
agents/operator/tests/test_operator_grammar.py = 141
agents/operator/tests/test_required_parameters.py = 193
```

**`make ci`:** `make ci > $ciLog 2>&1`, where `$ciLog` is `C:/Users/yury_/AppData/Local/Temp/ta-s268-evidence/make-ci.txt`; the captured `$LASTEXITCODE` was **0**. The whole file was read; all 15 commands ran, including dependency audit, detect-secrets and untracked-secrets. Verbatim output from every command is pasted below; only unchanged repository module warnings, old sprint rows, test progress, warning details and individual coverage rows are omitted. The complete redirected file was read. The first attempt was verified failing on new-test import ordering (`I001`), corrected by `ruff check agents/operator/tests/test_required_parameters.py --fix`. The second complete attempt was verified failing at detect-secrets on the changed public recipe digest in the fixture. Only that existing baseline entry's fingerprint was updated and staged after verifying the source-derived value; the targeted fixture secret check then passed. This final complete rerun passed. `uv lock` succeeded (`Resolved 180 packages`, `Updated trading-agents v0.125.5 -> v0.125.6`); only the root package version changed, and `pyproject.toml` / `uv.lock` are staged.

```text
uv run ruff check . --output-format=github
uv run ruff format --check .
1670 files already formatted
uv run mypy kernel contracts agents orchestration surfaces
pyproject.toml: note: unused section(s): module = ['azure.core', 'azure.identity.*', 'azure.keyvault', 'celery.*', 'redis', 'redis.*']
Success: no issues found in 1195 source files
uv run lint-imports

╔══╗─────────▶╔╗ ╔╗      ╔╗◀───┐
╚╣╠╝◀─────┐  ╔╝╚╗║║────▶╔╝╚╗   │
 ║║   ╔══╦══╦╩╗╔╝║║  ╔╦═╩╗╔╝╔═╦══╗
 ║║╔══╣╔╗║╔╗║╔╣║ ║║ ╔╬╣╔╗║║ ║│║╔═╝
╔╣╠╣║║║╚╝║╚╝║║║╚╗║╚═╝║║║║║╚╗║═╣║
╚══╩╩╩╣╔═╩══╩╝╚═╝╚═══╩╩╝╚╩═╩╩═╩╝
  └──▶║║                    ▲
      ╚╝────────────────────┘


---------
Contracts
---------

Analyzed 649 files, 2223 dependencies.
--------------------------------------

Agents may not import one another (talk only via messages) KEPT
Substrate imports no pack module KEPT
Agents may not reach into surfaces or orchestration KEPT
Kernel is pure plumbing — no domain, no contracts, no agents KEPT
Contracts declare schemas only — never import agents or runtime layers KEPT

Contracts: 5 kept, 0 broken.
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts
[WARN] agents/operator/agent.py: 175 lines (warn 150, hard block 200)
[WARN] agents/operator/tests/test_cutoff_agent.py: 157 lines (warn 150, hard block 200)
[WARN] agents/operator/tests/test_operator_agent.py: 197 lines (warn 150, hard block 200)
[WARN] agents/operator/tests/test_required_parameters.py: 193 lines (warn 150, hard block 200)
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run python scripts/check_law_coverage.py
uv run python scripts/check_param_law_sync.py
[WARN] portfolio_manager.max_position_pct declared_default=0.10 envelope=(0.01, 0.05) source=FCA COLL 5.2 — UCITS investment powers and limits
[WARN] portfolio_manager.max_positions declared_default=10 envelope=(30.0, 60.0) source=Evans and Archer, forty years later
uv run python scripts/check_sprint_status.py
docs/sprints/sprint-268-an-intent-that-lacks-what-its-family-needs-is-refused.md: SPEC | **Status:** SPEC
docs_seen=272 SPEC=11 BUILT=0 MERGED=261 UNMAPPED=0 MISSING=0
uv run python scripts/check_markdown_links.py
uv run python scripts/check_version_scheme.py
uv run pytest
collected 4717 items
TOTAL                                                           20264      0   4296      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
=========================== short test summary info ===========================
SKIPPED [1] tests\test_bus_azure_config.py:21: Service Bus dotenv isolation proof requires local .env
SKIPPED [1] tests\test_bus_celery.py:181: CELERY_BROKER_URL is not set
SKIPPED [1] tests\test_deliberator_servicebus_peer.py:36: A1 proof requires .env present; CI has no local secrets file
SKIPPED [1] tests\test_graph_postgres.py:137: POSTGRES_TEST_DSN is not set
SKIPPED [1] tests\test_graph_postgres_keys.py:90: POSTGRES_TEST_DSN is not set
SKIPPED [1] agents\forecaster\tests\test_barrier_garch_oracle.py:179: could not import 'scipy.signal': No module named 'scipy'
SKIPPED [1] agents\provider\tests\test_sources.py:159: FINNHUB_TEST_NETWORK=1 is not set
SKIPPED [1] agents\provider\tests\test_stooq.py:66: STOOQ_TEST_NETWORK=1 is not set
========= 4709 passed, 8 skipped, 2470 warnings in 661.53s (0:11:01) ==========
uv run python scripts/check_dependency_audit.py
accepted: PYSEC-2026-2447 (diskcache 5.6.3) - reachable only via the 'optimizer' extra, installed by 1 of 15 Dockerfiles; each installing command excludes diskcache by name; the dev group carries it too, and every sync passes --no-dev or excludes it by name; no fix release exists; every deployed optimizer installation excludes diskcache by name (S254, DL-266, ADR-0032) [DL-184] - retire when diskcache publishes a fixed release, or the optimizer extra is dropped
No unaccepted vulnerabilities; 1 accepted advisory re-checked
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 1 new file(s)
```

The second CI attempt's verified failure, and the scoped false-positive correction (the production Appendix and fixture value were kept exact):

```text
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Failed
- hook id: detect-secrets
- exit code: 1

ERROR: Potential secrets about to be committed to git repo!

Secret Type: Hex High Entropy String
Location:    tests\fixtures\guided_turn_main_records.json:5

Possible mitigations:
  - For information about putting your secrets in a safer place, please ask in
    #security
  - Mark false positives with an inline `pragma: allowlist secret` comment

If a secret has already been committed, visit
https://help.github.com/articles/removing-sensitive-data-from-a-repository

make: *** [Makefile:60: ci] Error 1
```

```text
Reviewed source recipe digest (not a credential): 43df2c61922b478cb4dc0c505fb9f104f6b3d07d2a65093fd8dd5af72b621392
Existing fixture line-5 baseline fingerprint only: 4cb73d92b065f4985b287281bc1229d94aa53420 -> 80eaf1c833db840d12230d6a84d32e5a1c238208
All plugin settings, review flags and other baseline entries unchanged.
```

**`make gate-ran`:** not done for Sprint 268. The build is uncommitted and unpushed; running it against the base HEAD would prove the base, not these changes. The planner owes exact-commit remote proof before merge, as in the sequencing section.

**Not met / verified failing:** No sprint build success factor remains unmet. Commit/push, remote gates, planner re-measure and CodeQL set-diff, merge, F1a chat-handler proof and paid F1b vendor proof: not done. Deploy: not done and none is required by this sprint. The initial CI import-order failure and the recipe-digest false positive were corrected; the final full rerun passed. Model names returned by real vendors and the unattended scorecard's treatment remain not measured; the build makes no claim about either.

---

## Return notes

Built as specified on the named branch, PATCH `0.125.06`; version and lock staged. The Appendix applied cleanly and the separate main-snapshot application produced identical bytes for all four production files.

Only the three named existing test/fixture files changed; all other existing test function bodies are unchanged. Failed-request and cut-off files, `INTENT_TOOL_SCHEMA`, supervisor, surfaces, contracts and design-log are unchanged. No new law clause or `noqa`. The largest touched module is 197 lines. One extra gate artifact changed: `.secrets.baseline` replaces only the fixture recipe digest's existing reviewed false-positive fingerprint. The plugin settings, review flags and every other entry were preserved; the staged baseline passed the targeted fixture check before the final full gate.

The authorized v1.9 clause text, Changelog, seven test-plan citations and DRIFT-109 correction are complete. Both rollup counts remain 20 / 51, accepted by `make ci`. `docs/STATE.md` records the required session evidence.

No real model, broker or deployed fleet was called for the behavior proofs; dependency resolution and audit ran as the gate requires. F1a/F1b and the other planner steps are not done. The next handoff is the planner's independent re-measure and proof of the exact eventual commit; no main work or deployment was performed. The actual skipped tests and their reasons are pasted above; the prototype count is historical, and the measured Windows count in this handback is the build result.

Final handback checks, after the BUILT status changes, all passed:

```text
docs/sprints/sprint-268-an-intent-that-lacks-what-its-family-needs-is-refused.md: BUILT | **Status:** BUILT
docs_seen=272 SPEC=10 BUILT=1 MERGED=261 UNMAPPED=0 MISSING=0
Post-handback sprint status exit: 0
Post-handback law coverage exit: 0
Post-handback Markdown links exit: 0
Detect secrets...........................................................Passed
Post-handback detect-secrets exit: 0
```

During the build, `main` and `origin/main` advanced from the base `b8f112af6437eb87f725fc9019371b03f3d19292` to `28d77906cc347cee0f8970cc4dbb67c2190c92d3` with documentation-only changes. The four production files, version files and baseline are unchanged between those commits. Owned changes are checked against this worktree's unchanged base HEAD; no main checkout, rebase or merge was performed. The planner must preserve the newer documentation when integrating. Pasted logs trim trailing whitespace only; the production Appendix bytes are unchanged.

---

## Planner's review at the merge — 2026-10-11

Re-measured by the planner in `../ta-s268` on the builder's tree, which was handed back uncommitted
on `b8f112af`; the planner committed it as `e54759bd`. Nothing here is taken from the handback.

- **Scope.** Sixteen files: the four production modules, one test file added and two edited, the
  fixture, the operator's two law files, the drift register, `.secrets.baseline`, the two version
  files, this file and its README row. No file in `agents/supervisor`, `surfaces/` or `contracts/`,
  no design-log entry, no test in `test_failed_request_*.py` or `test_cutoff_*.py`. Every one is LF.
- **As handed back, the code was the measured prototype byte for byte.** The four production
  files and the fixture had the prototype's blob ids (`f53f78f9`, `6a1c1227`, `fe9b066c`,
  `d4a9a83e`, `69d77d5a`), read by applying the prototype's patch to `b8f112af` in a scratch
  index. One word of one of them was then changed by the planner (below).
- **Guards.** The planner's 19 breaks, one at a time against the builder's tests alone, each
  restored: **19 went red, none survived, none failed to apply**; the restored tree is green.
- **The planner's own tests** (35 cases, written for the prototype) were placed beside the
  builder's and run on the built code: 35 passed. They are not committed.
- **The tests, read.** Seven functions, 35 cases, each citing `OPR-FAIL-02`. A1 to A5 drive the
  real `OperatorAgent` on an in-memory graph with a canned reply and assert the outcome, the
  message, the one `CommandAudit`'s outcome, one `LLMCall` and the count of `Intent`. A6 pins both
  sentences letter for letter.
- **The three existing tests.** `test_operator_agent.py` gives the five families their parameters
  through its `_raw` helper where the prototype added a second helper (197 lines either way);
  `test_operator_grammar.py` is the prototype's plus a docstring that cites the clause.
- **The law cycle.** Operator law v1.8 to v1.9; `OPR-FAIL-02` is the spec's text word for word
  (compared by script, 892 characters); Changelog; DRIFT-109 CORRECTED; 20 / 51 unchanged. **Each
  of the eight tests the row cites was resolved by hand:** every one is collected and its
  docstring names the clause.
- **A miss in the spec, mended by the builder.** The fixture's recipe hash is fingerprinted in
  `.secrets.baseline`, and the spec named the fixture and not the baseline, so the builder's
  second `make ci` stopped at detect-secrets. One fingerprint changed and nothing else: it is the
  SHA-1 of the new hash (`80eaf1c8…`), as the old one was of the old hash (`4cb73d92…`).
- **One change made by the planner in the code, a fault in the planner's own prototype.** Run
  through the chat handler, the refusal for an approve read *"A approve command needs its
  target"*. The sentence now begins *"The {family} command"* (`result.py`, one word), A6 pins the
  new letters and the approve sentence's opening, and with the old word put back A6 goes red. So
  `result.py` differs from the Appendix below in that word and the test file is 196 lines. The
  recipe hash does not read `result.py` and is unchanged. The 19 breaks were run again on the
  final code: 19 red.
- **Four changes made by the planner in docs.**
  1. `docs/laws/INDEX.md` and `docs/laws/ledger.md` still read operator v1.8. A gap in the spec,
     which said the gate would recompute the rollups: the gate checks the counts, not the version
     label. Both rows now read v1.9 and say what this sprint did.
  2. The DRIFT-109 row said "The Appendix checks", which means nothing outside this file. It now
     says "The operator checks".
  3. One blank line removed from this file: the markdown hook stopped the first commit on it.
  4. The builder's block in `docs/STATE.md` is not carried. STATE is written at the merge.
- **Seen and accepted.** The builder's first `make ci` failed on import order in the new test
  file and its second on detect-secrets; the third passed. The builder planted the twelve breaks
  the spec lists.
- **`main` moved during the build:** two docs commits, the tracker trim (`20597d82`) and the S261
  spec (`28d77906`). They were merged into this branch (`b3618d8f`); the two met in one file,
  `docs/sprints/README.md`, on neighbouring rows, resolved row by row (every row but this
  sprint's is `main`'s, byte for byte).
- **Version.** PATCH, `0.125.05` to `0.125.06`; `uv lock` changed the version line alone.

**The gate and the merge.** Windows `make ci` exit 0 on the branch at `e9f4f4a8`: all 15 steps, 4,709
passed, 8 skipped, 100.00 % coverage. `GATE PROVEN` for `e9f4f4a8`, run from `../ta-s268`, the
printed SHA equal to its `HEAD`: CI, CodeQL and Security Findings each `success`. Open CodeQL
alerts on the branch: 127, the same alert numbers as on the last merged branch, none at error
level. `main` fast-forwarded to that commit and tagged `v0.125.06`.

**After the merge, 2026-10-11 ([functionality checks](../laws/functionality-checks.md)).**
*F1a passed*, 180 of 180 checks over 33 cases, on the merged `main`, from the main checkout, at no
cost: each case of A1 to A5 as one typed message through the dashboard's chat handler, a fresh
in-memory context and one canned model reply a case. The eleven incomplete intents and the five of
no known family are each answered with the fixed sentence, audited `refused`, with no `Intent`
written and one model call; the fourteen complete ones are passed on with their parameters as
given (a `resume` gains the selected run from the surface); the two replies that are not intents
keep the model's outcome and reason; a typed `approve flag:case-1` is passed on although the
model's reply names no target. The same script on `main` before the merge (`28d77906`) failed 68
of 180: every incomplete intent came back *"confirmation required - resubmit with
confirmed=true"*. *F1b passed on OpenAI*, 8 of 8, paid (the operator: *"go for it"*, to OpenAI alone),
**$0.0422**: eight typed commands through the chat handler on `main` at `9237ec24` with the
real adapter (`gpt-5.5`, effort `xhigh`, cap 4,096). Each of the six complete commands came
back under the first accepted name the prompt lists and no alias did; each of the two that
omit a parameter was answered `needs_clarification`. *Not run on Anthropic.* *Met on the
way:* a required parameter returned as `null` counts as given (DRIFT-112, work-queue 128).

**Written at the merge, before the gate — what was still owed then:** the planner's Windows
`make ci`, the remote gate and the CodeQL set-diff for the commit that holds this block; then F1a
(the cases of A1 to A5 through the chat handler, at no cost); then F1b, paid, on the operator's word.

---

## Appendix — the production diff, measured on the planner's prototype

```diff
diff --git a/agents/operator/agent.py b/agents/operator/agent.py
index 00074a70..f53f78f9 100644
--- a/agents/operator/agent.py
+++ b/agents/operator/agent.py
@@ -20,6 +20,7 @@ from agents.operator.domain.prompts import (
 )
 from agents.operator.domain.result import (
     CUT_OFF_REPLY,
+    checked_intent,
     failed_request,
     failed_request_reply,
     intent_from_data,
@@ -148,7 +149,9 @@ class OperatorAgent(AgentBase):
         if fault is not None:
             data = failed_request(fault)
         else:
-            data = normalize_explicit_intent(command.text, parse_json(raw))
+            data = checked_intent(
+                normalize_explicit_intent(command.text, parse_json(raw))
+            )
         parsed_outcome = outcome(data)
         audit = write_command_audit(
             self._graph,
@@ -162,8 +165,6 @@ class OperatorAgent(AgentBase):
         if parsed_outcome != "intent":
             return CommandResult(outcome=parsed_outcome, message=message(data))
         intent = intent_from_data(data, corr)
-        if intent is None:
-            return CommandResult(outcome="refused", message=message(data))
         node = write_intent(
             self._graph, correlation_id=corr, audit_node=audit, intent=intent
         )
diff --git a/agents/operator/domain/grammar.py b/agents/operator/domain/grammar.py
index 9e3791e6..6a1c1227 100644
--- a/agents/operator/domain/grammar.py
+++ b/agents/operator/domain/grammar.py
@@ -22,22 +22,36 @@ class FamilySpec:
     description: str
     params: tuple[str, ...]
     requires_confirmation: bool
+    #: Each parameter the family cannot do without, as the names its readers take.
+    required: tuple[tuple[str, ...], ...] = ()


 INTENT_FAMILIES: dict[IntentFamily, FamilySpec] = {
     "status": FamilySpec("read system status", (), False),
     "explain": FamilySpec("explain a decision or artifact", ("subject",), False),
-    "approve": FamilySpec("approve a pending item", ("target",), True),
-    "reject": FamilySpec("reject a pending item", ("target",), True),
-    "modify": FamilySpec("change a parameter", ("name", "value"), True),
+    "approve": FamilySpec(
+        "approve a pending item", ("target",), True, (("target", "subject"),)
+    ),
+    "reject": FamilySpec(
+        "reject a pending item", ("target",), True, (("target", "subject"),)
+    ),
+    "modify": FamilySpec(
+        "change a parameter", ("name", "value"), True, (("name",), ("value",))
+    ),
     "run": FamilySpec("start a trading run", ("stage",), True),
-    "mode": FamilySpec("switch operating mode", ("mode",), True),
-    "stage": FamilySpec("promote or demote execution stage", ("stage",), True),
+    "mode": FamilySpec("switch operating mode", ("mode",), True, (("mode",),)),
+    "stage": FamilySpec(
+        "promote or demote execution stage",
+        ("stage",),
+        True,
+        (("stage", "target"),),
+    ),
     "pause": FamilySpec("pause scheduling", (), False),
     "resume": FamilySpec(
         "resume a selected run from one pipeline stage",
         ("run_id", "stage"),
         True,
+        (("stage", "from_stage"),),
     ),
 }

@@ -68,6 +82,17 @@ def normalize_explicit_intent(
     }


+def missing_parameters(
+    family: IntentFamily, parameters: dict[str, str]
+) -> tuple[str, ...]:
+    """Name each required parameter that none of its accepted names gives."""
+    return tuple(
+        names[0]
+        for names in INTENT_FAMILIES[family].required
+        if not any(parameters.get(name, "").strip() for name in names)
+    )
+
+
 def apply_confirmation_policy(family: IntentFamily, intent: TypedIntent) -> TypedIntent:
     """Force confirmation policy from the grammar, ignoring model output."""
     return intent.model_copy(
diff --git a/agents/operator/domain/prompts.py b/agents/operator/domain/prompts.py
index d40c2d67..fe9b066c 100644
--- a/agents/operator/domain/prompts.py
+++ b/agents/operator/domain/prompts.py
@@ -34,7 +34,9 @@ INTENT_TOOL_SCHEMA: dict[str, object] = {
 def build_interpret_system() -> str:
     """Build the bounded command-interpretation system prompt."""
     families = ", ".join(
-        f"{name}: {spec.description}" for name, spec in INTENT_FAMILIES.items()
+        f"{name}: {spec.description}"
+        + (f" (parameters: {', '.join(spec.params)})" if spec.params else "")
+        for name, spec in INTENT_FAMILIES.items()
     )
     return (
         "Map the operator command to exactly one allowed trading-system intent, "
@@ -43,7 +45,10 @@ def build_interpret_system() -> str:
         "health. Commands that say approve <subject-ref> or ask to confirm "
         "approval for a subject are approve intents with that exact target; "
         "never classify them as status. "
-        f"Allowed families: {families}."
+        f"Allowed families: {families}. "
+        "Give each parameter in `parameters` under exactly the name listed. If the "
+        "command does not say one the intent cannot do without, ask for "
+        "clarification; never guess it."
     )


diff --git a/agents/operator/domain/result.py b/agents/operator/domain/result.py
index a8bf7151..d4a9a83e 100644
--- a/agents/operator/domain/result.py
+++ b/agents/operator/domain/result.py
@@ -11,7 +11,11 @@ import hashlib
 import json
 from typing import TYPE_CHECKING, Literal

-from agents.operator.domain.grammar import apply_confirmation_policy
+from agents.operator.domain.grammar import (
+    INTENT_FAMILIES,
+    apply_confirmation_policy,
+    missing_parameters,
+)
 from contracts.common import Explanation, Provenance
 from contracts.operator import CommandResult, TypedIntent
 from kernel.llm_error_text import vendor_status_error
@@ -32,6 +36,33 @@ FAILED_REQUEST_REPLY = (
 )


+UNKNOWN_FAMILY_REPLY = (
+    "The model's reply named no command this system has, so nothing was done."
+)
+
+
+def missing_parameters_reply(family: str, missing: tuple[str, ...]) -> str:
+    """Say which parameters a command of this family was given without."""
+    return (
+        f"A {family} command needs its {' and '.join(missing)}, and the model's "
+        "reply gave none, so nothing was done. Say it again and name it."
+    )
+
+
+def checked_intent(data: dict[str, object]) -> dict[str, object]:
+    """Read an intent of no known family, or lacking what it needs, as a refusal."""
+    if outcome(data) != "intent":
+        return data
+    family = data.get("family")
+    if not isinstance(family, str) or family not in INTENT_FAMILIES:
+        return {"outcome": "refused", "reason": UNKNOWN_FAMILY_REPLY}
+    missing = missing_parameters(family, _params(data.get("parameters", {})))
+    if missing:
+        reason = missing_parameters_reply(family, missing)
+        return {"outcome": "refused", "reason": reason}
+    return data
+
+
 def failed_request_reply(fault: AgentFault) -> str:
     """Say the model request failed, then the error's own reason in plain words."""
     status = vendor_status_error(fault.message)
@@ -68,20 +99,15 @@ def outcome(data: dict[str, object]) -> Outcome:
     return "refused"


-def intent_from_data(
-    data: dict[str, object], correlation_id: str
-) -> TypedIntent | None:
-    """Build a TypedIntent and apply grammar-owned confirmation policy."""
-    try:
-        intent = TypedIntent(
-            family=str(data.get("family", "status")),  # type: ignore[arg-type]
-            parameters=_params(data.get("parameters", {})),
-            requires_confirmation=False,
-            provenance=Provenance(run_id=correlation_id, source_agent="operator"),
-        )
-        return apply_confirmation_policy(intent.family, intent)
-    except ValueError:
-        return None
+def intent_from_data(data: dict[str, object], correlation_id: str) -> TypedIntent:
+    """Build a TypedIntent from checked data; the grammar owns the confirmation."""
+    intent = TypedIntent(
+        family=data["family"],  # type: ignore[arg-type]
+        parameters=_params(data.get("parameters", {})),
+        requires_confirmation=False,
+        provenance=Provenance(run_id=correlation_id, source_agent="operator"),
+    )
+    return apply_confirmation_policy(intent.family, intent)


 def message(data: dict[str, object]) -> Explanation:
```
