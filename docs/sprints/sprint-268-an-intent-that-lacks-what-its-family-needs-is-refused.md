<!-- Agent: planning | Role: sprint handover -->
# Sprint 268 — an intent that lacks what its family needs is refused, and the model is told what each family needs

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-268-an-intent-that-lacks-what-its-family-needs-is-refused`
**Status:** SPEC
**Version:** *next available PATCH at merge*
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

- [ ] Every row of the Test plan is a passing test that cites `OPR-FAIL-02`.
- [ ] The production diff equals the Appendix (`git diff main -- agents/operator/agent.py agents/operator/domain`).
- [ ] No test in `test_failed_request_*.py` or `test_cutoff_*.py` changed.
- [ ] Exactly the three existing tests named above changed.
- [ ] The operator recipe hash equals the Measured table's, or the difference is explained.
- [ ] Law cycle done: clause text as given, v1.9, Changelog, test-plan row, DRIFT-109 corrected.
- [ ] Every guard planted, watched to fail, restored, stated per guard.
- [ ] Every touched module under 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

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
| *to be filled by the builder* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *to be filled by the builder*

**Contradictions found between a law and this spec:** *to be filled by the builder*

**Laws found silent where a decision was needed:** *to be filled by the builder*

**Clauses that were ⬜ and are now proven:** *to be filled by the builder*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| *to be filled by the builder* | | | | |

**Tests added beyond the plan:** *to be filled by the builder*

---

## Closeout — evidence

**Status:** *to be filled by the builder*

**Tree the proofs ran in (and `.env` present?):** *to be filled by the builder*

**Result:** *to be filled by the builder*

**Files changed:** *to be filled by the builder*

**Proof — the red run first:** *to be filled by the builder*

**Proof — the green run:** *to be filled by the builder*

**Guards planted:** *to be filled by the builder*

**Module line counts:** *to be filled by the builder*

**`make ci`:** *to be filled by the builder*

**`make gate-ran`:** owed by the planner if the sandbox has no network.

**Not met / verified failing:** *to be filled by the builder*

---

## Return notes

*to be filled by the builder*

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
