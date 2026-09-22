<!-- Agent: planning | Role: sprint handover -->
# Sprint 224 — a spec's built state is readable by a machine, and the machine refuses to guess

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-224-a-spec-says-whether-it-was-built`
**Status:** MERGED `c33985b` (`0.106.00`) · tagged `v0.106.00`, 2026-09-22
**Version:** `0.106.00`
**Effort:** S
**Decisions:** work-queue item **22** (partial — Part A only) · `docs/sprints/_TEMPLATE.md` already fixed the vocabulary

> **Why this bump kind.** A new `make ci` step is a new capability the gate did not have, so **MINOR**.
> It adds a check that did not exist rather than repairing one that under-delivered.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

### The rule

Read the law file for every element this sprint touches before writing code, and record what you
read in the **Law reading record** below. This sprint touches **no agent**: it adds a repo-level
checker under `scripts/` and reads `docs/sprints/*.md`. No agent law binds it.

### 🩹 The law-cycle question — answer before step 5

**No law cycle.** No agent gains, loses or changes a capability. `docs/laws/conventions.md` is the
only law-side document that mentions spec status, and this sprint does not change what it says — it
makes the existing `_TEMPLATE.md` rule mechanical. If you find yourself editing a `laws.md`, stop:
you have left this sprint's scope.

### Element → law map

| Element touched | Law/convention to read first | Why |
| --- | --- | --- |
| `scripts/check_sprint_status.py` (new) | `docs/laws/conventions.md` | Tooling; no agent law binds it, but its output is read as evidence |
| `docs/sprints/_TEMPLATE.md` | itself | It already declares the vocabulary; this sprint enforces it, never redefines it |

---

## Goal

**One line, one vocabulary, and a machine that reads it.** After this sprint, `make ci` can answer
"is this spec built?" for every sprint doc that carries a status token — and for every doc that does
**not**, it names the doc rather than inventing an answer.

---

## Why (context)

Nothing can answer "is this spec built?". It cost a wasted handover once: S171 was recommended after
it had already shipped. The row has been re-measured three times and got worse each time.

### Measured, 2026-09-22 — read these before designing

| Fact | Value | How measured |
| --- | --- | --- |
| Sprint/chore docs in `docs/sprints/` | **227** | `*.md` excluding `INDEX.md`, `README.md`, `_TEMPLATE.md` |
| Docs carrying **no** `**Status:**` line at all | **20** | regex `^\*\*Status:\*\*` over each file |
| Distinct **full** `**Status:**` lines | **158** | exact string match on the text after the marker |
| Most common leading tokens | `shipped` 61 · `planned` 31 · `ready` 21 · `SPEC` 20 · `MERGED` 19 · `BUILT` 19 · `SHIPPED` 8 · `queued` 6 | first word after the marker |
| The vocabulary is **already decided** | `SPEC \| BUILT \| MERGED` | `docs/sprints/_TEMPLATE.md` line 20, which cites item 22 as its reason |

🎯 **The template already settled the policy.** This sprint does not choose a vocabulary; it enforces
the one that exists. If you feel a fourth token is needed, that is a finding for Return notes, not a
decision to take.

🚨 **The risk that shapes this sprint:** most of those 158 lines *carry evidence* — e.g.
``MERGED `7d3ff51` (`0.98.08`) · DEPLOYED `s211` · LIVE CHECK DISCHARGED``. Collapsing such a line to
a bare token **destroys** it, and deriving a token from freeform prose risks writing a **false**
status — which is the exact harm item 22 exists to prevent. A wrong machine-readable status is worse
than no status, because the next reader will trust it.

---

## Scope — and what is deliberately NOT here

**This sprint edits ZERO sprint documents.** It builds the classifier, the checker and the report.

1. `scripts/check_sprint_status.py` — classifies each doc's existing `**Status:**` line into exactly
   one of `SPEC | BUILT | MERGED`, or into `UNMAPPED`. Prints a report. Exits **0** in report mode.
2. A `make ci` step that fails **only** on a doc whose status line leads with a token in the
   vocabulary but in the wrong shape, and on any **new** doc added without a status line. Existing
   unmapped docs are a known, counted baseline — the S207/S221 ratchet shape, not a hard fail.
3. The unmapped report, committed as `docs/sprints/status-unmapped.md`, listing every doc the
   classifier refused, with its verbatim line.

### Out of scope (do NOT build this sprint)

- **Editing any sprint doc's `**Status:**` line.** That is Part B, and it must not start until a
  human has read the refusal list this sprint produces. Building the migration and running it in one
  sprint is precisely how a silent corruption ships.
- **Inventing a status for the 20 docs that have none.** A doc that never declared its state does not
  acquire one by inference. They are listed, not filled.
- **A fourth vocabulary token.** Raise it in Return notes.
- **Touching `docs/sprints/INDEX.md` rows** beyond adding this sprint's own row.

### The road not taken (LAW-06)

- **One sprint that classifies and migrates.** Rejected: the failure mode is *silent corruption over
  227 files*, and the only cheap defence is a human reading the refusal list between the two halves.
- **Hard-fail CI on every unmapped doc.** Rejected: it would turn a small sprint into a 227-doc
  cleanup, which is the mistake item 33 records (57 baselined warnings) — except worse, because here
  the gate would be red from the first commit.
- **Deriving the token from git history** (was the doc's branch merged?). Rejected as a second source
  of truth that can disagree with the doc; and a merged branch does not prove the spec was built as
  written. Worth reconsidering in Part B as a *cross-check*, never as the writer.
- **Storing status in a sidecar JSON.** Rejected: the doc is what a human reads, so a status that
  lives elsewhere drifts from the prose the same way `_REASON_GATE` drifted from its gate map (item 80).

---

## The design decisions this sprint has to make

1. **What makes a line unambiguously classifiable.** Propose a rule and defend it. A defensible
   starting point: classify on the **leading token only**, case-insensitively, against an explicit
   synonym table (`shipped`/`SHIPPED`/`merged`/`MERGED` → `MERGED`; `planned`/`queued`/`ready`/`SPEC`
   → `SPEC`; `BUILT`/`implemented` → `BUILT`). Anything whose leading token is not in the table is
   `UNMAPPED`. 🪤 **A synonym table is a policy claim.** Put each mapping in the test table so the
   claim is visible and reviewable, and put anything you are unsure about in `UNMAPPED` instead.
2. **What the migration line will look like**, written down now but NOT applied:
   `**Status:** <TOKEN> — <the original line, verbatim>`. Record it in the design log so Part B has a
   fixed target it cannot reinterpret.
3. **How the baseline is expressed** so it can only shrink. Follow `scripts/param_law_sync_baseline.py`
   — a named count, asserted by a test, that fails if it **grows**.

---

## Blast radius — measured 2026-09-22

| Dimension | Value |
| --- | --- |
| Files changed | `scripts/check_sprint_status.py` (new), `Makefile`, `.github/workflows/ci.yml`, `docs/sprints/status-unmapped.md` (new), tests, this doc |
| Sprint docs modified | **0** — this is the property that makes the sprint safe |
| Agents affected | **none**. No agent imports `scripts/`; no runtime path changes |
| Production behaviour | **none**. No deploy is owed |
| Reversibility | Complete — delete the script and the CI step |

---

## Steps, in order

1. Read `docs/sprints/_TEMPLATE.md` lines 17–24 and `docs/laws/conventions.md`. Record both in the
   Law reading record.
2. Write the failing tests FIRST, from the test plan table below. Paste the red run into the closeout.
3. Build `scripts/check_sprint_status.py` with two modes: `--report` (prints every doc, its token or
   `UNMAPPED`, exits 0) and default (the gate).
4. Generate `docs/sprints/status-unmapped.md` from the report.
5. Add the step to `ci:` in the `Makefile` and to `.github/workflows/ci.yml`. 🪤 **Both** — the
   Makefile alone is a local check that CI never runs.
6. Bump the MINOR group, `uv lock`, `make ci`, push, `make gate-ran`.

---

## Test plan

Every row is a behaviour. Write the test before the code; a row with no test is not built.

| # | Behaviour | Fixture | Expected |
| --- | --- | --- | --- |
| T1 | A line whose leading token is in the synonym table classifies to its token | `**Status:** MERGED \`abc123\` · DEPLOYED \`s211\`` | `MERGED` |
| T2 | 🎯 Classification reads the **leading token only** and ignores the evidence after it | the same line as T1 | `MERGED`, and the evidence string is returned unchanged beside it |
| T3 | 🪤 A line with an unknown leading token is `UNMAPPED`, never guessed | `**Status:** mostly done, see notes` | `UNMAPPED` — **no** token assigned |
| T4 | 🪤 A doc with no `**Status:**` line is reported as missing, not as `SPEC` | a doc with no such line | reported `MISSING`; **not** classified |
| T5 | The negative control — every vocabulary token round-trips | `SPEC`, `BUILT`, `MERGED` | each classifies to itself |
| T6 | Case-insensitivity is deliberate and bounded | `shipped`, `SHIPPED`, `Shipped` | all → `MERGED` |
| T7 | 🎯 The checker **never writes to a doc** | run the checker over a temp corpus, hash every file before and after | every hash identical |
| T8 | The baseline cannot grow silently | a corpus with one more unmapped doc than the recorded baseline | non-zero exit naming the new doc |
| T9 | A baseline that **shrinks** is not a failure | a corpus with one fewer | exit 0 |
| T10 | 🎯 The real corpus classifies without crashing | the live `docs/sprints/` | exits 0 in report mode; counts printed; **227** docs seen |
| T11 | A new doc with no status line fails the gate | add a fixture doc with no line | non-zero exit naming it |

---

## Success factors

- [ ] `make ci` gains a step that answers "is this spec built?" for every classifiable doc.
- [ ] **Zero** sprint docs modified, proven by T7 and by the diff.
- [ ] Every refusal is named in `docs/sprints/status-unmapped.md` with its verbatim line.
- [ ] The synonym table is visible in the test table, so every policy claim is reviewable.
- [ ] `make ci` exit 0 with the 100.00 % coverage floor held.
- [ ] `make gate-ran` exits 0 for the exact SHA being merged.

---

## Traps

🪤 **A wrong status is worse than no status.** The next reader trusts a machine-readable token more
than prose. When in doubt, `UNMAPPED`. A sprint that maps 150 docs and gets 3 wrong is a failure; one
that maps 120 and refuses 107 is a success.

🪤 **Do not "fix" a doc you notice is mislabelled.** It is out of scope and it is how the zero-docs-
modified property dies.

🪤 **Report mode must exit 0.** If the report exits non-zero, nobody will run it, and the refusal list
is the deliverable.

🪤 **The count 227 will drift** as sprints are added — including this one. Read it from the corpus,
never hardcode it; T10 asserts the checker *ran over* the corpus, not that the number is 227 forever.

🪤 **`docs/sprints/` contains non-sprint files.** `INDEX.md`, `README.md` and `_TEMPLATE.md` are not
sprint docs. Excluding them is behaviour — pin it with a test.

---

## Guardrails (every sprint)

- Branch `sprint-224-a-spec-says-whether-it-was-built` off latest `main`, in a worktree. Never `main`.
- No secret in the tree, ever — not even an untracked scratch file.
- Module size: 200 lines hard block, 150 warning. Split before you hit it; never `# noqa`.
- Architecture: `kernel ← contracts ← agents ← orchestration/surfaces`. Agents never import agents.
- `make ci` must pass all 14 steps. **Never measure the gate through a pipe** — redirect to a file and
  read the file; `make ci | tail` reports `tail`'s exit code.
- Fill the Closeout block. A handback with a placeholder intact is returned, not repaired.

---

## Sequencing after merge

**Part B (the migration) is queued, not authorised by this sprint.** It starts only after a human has
read `docs/sprints/status-unmapped.md`. Part B applies
`**Status:** <TOKEN> — <original line verbatim>` to the classified docs only, and leaves every
`UNMAPPED` and `MISSING` doc untouched.

---

## Handover — paste this to the coding agent

```text
Read docs/sprints/sprint-224-a-spec-says-whether-it-was-built.md fully, then fill the
"Law reading record" section BEFORE your first line of code.

BUILD: a checker that answers "is this spec built?" from docs/sprints/*.md.

THE ONE PROPERTY THAT MATTERS: this sprint edits ZERO sprint documents. It classifies and
reports. It never writes a status. Test T7 proves it by hashing every file before and after.

THE SECOND PROPERTY: it refuses to guess. The vocabulary is already fixed by
docs/sprints/_TEMPLATE.md line 20 as exactly SPEC | BUILT | MERGED. Do not invent a fourth
token. A line whose leading token you do not recognise is UNMAPPED, and UNMAPPED is a correct
answer, not a failure. A wrong token is worse than no token, because the next reader trusts it.

Measured 2026-09-22, re-measure before you start: 227 sprint/chore docs, 20 with NO **Status:**
line, 158 distinct full status lines. Leading tokens: shipped 61, planned 31, ready 21, SPEC 20,
MERGED 19, BUILT 19, SHIPPED 8, queued 6.

Most status lines CARRY EVIDENCE, e.g.
  **Status:** MERGED `7d3ff51` (`0.98.08`) · DEPLOYED `s211` · LIVE CHECK DISCHARGED
Classify on the LEADING TOKEN ONLY and return the rest untouched. Never collapse a line.

Every behaviour in the "Test plan" table must have a test, written BEFORE the code, and the red
run pasted into the closeout. A row with no test is not built.

Add the step to BOTH the Makefile `ci:` target AND .github/workflows/ci.yml - the Makefile alone
is a local check CI never runs.

Version: next available MINOR at merge - do not pin a number. No deploy.

DO NOT: edit any sprint doc's status line, invent a status for the 20 docs that have none, add a
fourth token, or "fix" a doc you notice is mislabelled. All four are out of scope and the last
three are how a false status ships.

Finish by filling the Closeout block: red run first, then green, make ci exit code, the counts
your checker reported, and the path to the unmapped report.
```

---

## Handback contract — MANDATORY

<!-- The coding agent fills everything below. Leave no placeholder. -->

**Status at handback:** BUILT

## Law reading record — fill BEFORE writing code

| File read | What it required of this sprint |
| --- | --- |
| `docs/sprints/_TEMPLATE.md` | The status line is machine-checkable and its vocabulary is exactly `SPEC \| BUILT \| MERGED`; preserve the line's evidence and do not invent another token. |
| `docs/laws/conventions.md` | The checker is repo tooling, not an agent capability or contract change, so no agent law cycle or clause-cited functional test is owed. Its report must remain evidence-based rather than inferring a state from prose. |

**Law-cycle decision:** No. This sprint changes no `contracts/` file and adds no agent guarantee; it makes the template's existing status vocabulary mechanically observable.

## Test plan results — fill at handback

| # | Test name | File | Result |
| --- | --- | --- | --- |
| T1 | `test_t1_known_leading_token_classifies_to_canonical_status` | `tests/test_sprint_status.py` | PASS — all eight explicit aliases map to a canonical token |
| T2 | `test_t2_evidence_after_leading_token_is_preserved_unchanged` | `tests/test_sprint_status.py` | PASS |
| T3 | `test_t3_unknown_leading_token_is_unmapped_not_guessed` | `tests/test_sprint_status.py` | PASS |
| T4 | `test_t4_document_without_status_is_missing_not_spec` | `tests/test_sprint_status.py` | PASS |
| T5 | `test_t5_vocabulary_tokens_round_trip` | `tests/test_sprint_status.py` | PASS — `SPEC`, `BUILT`, `MERGED` |
| T6 | `test_t6_shipped_synonym_is_case_insensitive` | `tests/test_sprint_status.py` | PASS — `shipped`, `SHIPPED`, `Shipped` |
| T7 | `test_t7_checker_never_writes_a_sprint_document` | `tests/test_sprint_status.py` | PASS — SHA-256 hashes unchanged before and after report mode |
| T8 | `test_t8_unmapped_count_above_baseline_fails_and_names_document` | `tests/test_sprint_status.py` | PASS |
| T9 | `test_t9_unmapped_count_below_baseline_passes` | `tests/test_sprint_status.py` | PASS |
| T10 | `test_t10_real_corpus_reports_every_sprint_document` | `tests/test_sprint_status.py` | PASS — 228 discovered; index, template, README, and report excluded |
| T11 | `test_t11_new_document_without_status_fails_and_names_document` | `tests/test_sprint_status.py` | PASS |

## Closeout — evidence

**Result:** `make ci` exit 0. `3023 passed, 6 skipped`; coverage `100.00%`; `pip-audit` and both secret sweeps passed. The classifier reports `docs_seen=228 SPEC=79 BUILT=21 MERGED=88 UNMAPPED=20 MISSING=20`.

**Files changed:** `scripts/check_sprint_status.py`, `tests/test_sprint_status.py`, `scripts/gate_selftest_cases.py`, `Makefile`, `.github/workflows/ci.yml`, `docs/sprints/status-unmapped.md`, `docs/design-log.md`, `pyproject.toml`, `uv.lock`, and this required handback. No classified document's `**Status:**` line changed.

**Design decisions:** The canonical vocabulary remains exactly `SPEC | BUILT | MERGED`. The visible synonym table is `planned`/`queued`/`ready` -> `SPEC`, `implemented` -> `BUILT`, and `shipped` -> `MERGED`, case-insensitively; each is an existing simple state word in the corpus. Unknown, punctuated, emoji-prefixed, and compound leading forms are `UNMAPPED`. Part B's unexecuted migration form is `**Status:** <TOKEN> — <original line verbatim>`; DL-197 records this and the rejected inference routes.

**Proof — the red run first:**

```text
$ uv run pytest --no-cov tests/test_sprint_status.py
collected 15 items
tests/test_sprint_status.py FFFFFFFFFFFFFFF
FAILED ... sprint status checker is missing: cannot import name 'check_sprint_status' from 'scripts'
============================= 15 failed =============================
```

**Proof — the green run:**

```text
$ uv run pytest --no-cov tests/test_sprint_status.py
collected 22 items
tests/test_sprint_status.py ......................
============================= 22 passed in 1.37s ==============================

$ uv run python scripts/gate_selftest.py
gate self-test: 26/26 passed

$ make ci > $env:TEMP\sprint-224-make-ci-final-utf8.txt 2>&1; Write-Output $LASTEXITCODE
0
================= 3023 passed, 6 skipped in 95.96s (0:01:35) ==================
Required test coverage of 100.0% reached. Total coverage: 100.00%
No known vulnerabilities found
Detect secrets...........................................................Passed
```

**Corpus counts reported by the checker:** `docs_seen=228 SPEC=79 BUILT=21 MERGED=88 UNMAPPED=20 MISSING=20`. The committed refusal report is `docs/sprints/status-unmapped.md`.

**Not met / verified failing:** `make gate-ran` is not run: no commit has been created or pushed. No deploy is owed.

## Return notes

No case for a fourth vocabulary token. `CLOSED`, `BLOCKED`, `active`, emojis, and compound forms remain documented refusals for a human Part B decision; silently treating any as a fourth status would violate the template's fixed vocabulary.
