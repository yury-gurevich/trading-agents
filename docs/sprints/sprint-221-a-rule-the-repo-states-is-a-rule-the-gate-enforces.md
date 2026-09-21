<!-- Agent: planning | Role: sprint handover — the gate learns two rules the repo already states -->
# Sprint 221 — a rule the repo states is a rule the gate enforces

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-221-a-rule-the-repo-states-is-a-rule-the-gate-enforces`
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** work-queue items **76** and **77** · `DL-190` (take the next free number and re-check it at merge) · both rules already exist in `CLAUDE.md`; this sprint adds no policy

> **Why this bump kind.** PATCH. No new capability and no agent gains a dimension — two rules the
> repo already states in `CLAUDE.md` gain the check that makes them true. Tooling only.

---

## 🔴 MUST RULE — read before you write any code

This sprint touches **no agent**, so it owes **no law cycle**. Read these anyway, in this order,
because each one names a trap this sprint can walk into:

| Read | Why it binds here |
| --- | --- |
| `CLAUDE.md` — *Version scheme* and *CI gate* | The two rules being enforced. Part B's check must accept every version the repo has ever shipped, including `0.99.00` before `0.100.00` |
| `scripts/gate_selftest_cases.py` | Every gate step registers a planted failure here. A check with no `FailureCase` is a check nobody has seen fail |
| `scripts/check_param_law_sync.py` + `tests/test_param_law_sync.py` | The house pattern for a gate script and its tests — follow it rather than inventing one |
| `.markdownlint-cli2.jsonc` | Its `ignores` list says which trees are generated or dated evidence. Part A's scope follows the same reasoning |

### The law-cycle question

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**No.** Nothing under `agents/`, `contracts/` or `kernel/` is touched. Say so in the Law reading
record and continue. 🪤 If you find yourself editing an agent to make a check pass, stop and report —
the check is wrong, not the agent.

⚠️ **The one invariant this sprint must not break: `make ci` must stay runnable offline.** Neither
new check may make a network call, read `.env`, or require a git remote. They read tracked files.

---

## Goal

At merge, `make ci` fails on two things it currently passes: a relative link in a tracked `.md` file
that resolves to nothing, and a `pyproject.toml` version that does not match the repo's declared
scheme. Both checks appear in the `Makefile`, in `.github/workflows/ci.yml`, and in
`scripts/gate_selftest_cases.py` with a planted violation that proves each can fail.

## Why (context)

Both rules are written down. Neither is checked, and both were broken this week.

**Part A — links.** On 2026-09-21 an audit of every relative link in all **459** tracked `.md` files
found **123** that resolved to no file. **112** were in `docs/state-archive/`, where `STATE-0*.md`
moved down one directory and its `design-log.md` / `sprints/…` links were never re-prefixed; the rest
were wrong slugs (ADR-0012, ADR-0023, S186, S197, S146, `LAW-02-proof.md`) plus five bare `#`
fragments in the work queue. 🎯 **`make markdown` was exit 0 the entire time, with all 123 present** —
`MD051` only validates fragments *inside one document*, and no markdownlint rule looks at a link
*between* files. The repair shipped as `48f7d58`; this sprint is the check that stops it recurring.

**Part B — the version.** [S220](sprint-220-a-correlated-issuer-counts-in-proportion.md) was handed
back with `version = "0.103.0"` in `pyproject.toml`. The scheme is `MAJOR.MMM.PP` and the last group
is **two digits**, so the correct value is `0.103.00`. `CLAUDE.md` calls breaking it *a blocker — do
not merge*. 🎯 **`make ci` was exit 0 over it**, because nothing in the twelve steps reads the version
at all. It was caught by a human reading the diff, which is exactly the thing the gate exists to stop
being necessary.

### Measured, 2026-09-21 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Tracked `.md` files | **459** | `git ls-files "*.md"` |
| Broken relative links before the repair | **123** (119 missing file, 4 dead same-file fragment) | full-tree audit, 2026-09-21 |
| Of those, in `docs/state-archive/` | **112** | same audit, grouped by file |
| `make markdown` while all 123 were present | **exit 0** | `make markdown`, 2026-09-21 |
| Broken links after the repair (`48f7d58`) | **0** | same audit, re-run |
| Version shipped by the S220 handback | `0.103.0` | `pyproject.toml` on the branch before correction |
| `make ci` over that version | **exit 0** | full local run in the S220 worktree |
| Gate steps that read the version | **0** | `grep` over `Makefile` and `.github/workflows/ci.yml` |
| Versions the check must accept | `0.90.16`, `0.94.02`, `0.98.11`, `0.99.00`, `0.100.00`, `0.102.00`, `0.103.00` | `git tag --sort=-v:refname` |

---

## Scope — and what is deliberately NOT here

### Part A — `scripts/check_markdown_links.py` (work-queue item 76)

1. **Plant the failing test first.** A fixture `.md` with a link to a file that does not exist must
   make the check exit non-zero. Watch it fail *before* the script exists, paste the red output.
2. **What it checks**, over every file from `git ls-files "*.md"`:
   - a relative link target resolves to an existing path (`[text](../foo.md)`, `[text](foo.png)`);
   - a `#fragment` on a `.md` target resolves to a heading in that file, using GitHub slug rules
     (lowercase; drop anything that is not a letter, number, space or hyphen; spaces → hyphens;
     duplicate headings get `-1`, `-2`);
   - 🎯 **link text that looks like a path matches the target it points at.** This is not padding:
     the repair produced `[codeql/python-security/README.md](../../README.md)`, which **resolved and
     still lied** — the file in the text does not exist. A resolver alone cannot see this.
3. **What it must NOT flag** — each of these is a measured false positive, not a hypothetical:
   - anything inside a fenced block or an inline code span. `docs/sprints/sprint-108-vault-seeder.md:61`
     contains `` `probes[probe](env)` ``, which a naive regex reads as a link to `env`;
   - `http://`, `https://`, `mailto:` and angle-bracket autolinks;
   - image links (`![alt](…)`) are in scope for *file existence* but have no fragments;
   - the trees `.markdownlint-cli2.jsonc` already ignores, for the reason it gives there —
     `codeql/python-security/reports/` is generated, dated evidence.
4. **Output** names `file:line`, the href, and which of the three rules it broke. A check whose
   message does not say what to fix costs more than it saves.

### Part B — `scripts/check_version_scheme.py` (work-queue item 77)

1. **Plant the failing test first**: `0.103.0` must be rejected, `0.103.00` accepted.
2. **The rule**, read from `pyproject.toml` `[project] version` only:
   - `MAJOR.MMM.PP` — major ≥ 1 digit, middle **1 to 3** digits, patch **exactly 2** digits;
   - no leading `v`, no suffix, no pre-release tag.
3. 🪤 **Read `pyproject.toml`, never `uv.lock`.** `uv` normalises trailing zeros: with `0.102.00` in
   `pyproject.toml`, `uv.lock` records `0.102.0`. A check that reads the lock file **fails on a
   correct repo** — measured on `main` today.
4. **Out of scope: monotonicity.** Whether a bump went *up*, and whether it was the right *kind*, is
   a judgement about the diff, not a format. Pinning it needs git tags and history, and
   🪰 `v0.100.00` sorts **before** `v0.99.00` under a plain `sort`. Format only, this sprint.

### Both parts

5. **Wire into all three places.** A check in one place only is the defect this sprint is about:
   - `Makefile` `ci:` target — 🪤 note it currently has **12** steps while `.github/workflows/ci.yml`
     has a `Gate self-test` step the `Makefile` does not. Do not "fix" that drift here; just add both
     new steps to **both** files and report the discrepancy in your Return notes;
   - `.github/workflows/ci.yml`, as its own named step;
   - `scripts/gate_selftest_cases.py` — one `FailureCase` per check, with the planted file and the
     command that must reject it.
6. **Module header.** `scripts/` is covered by `check_module_header.py`, so both new files need the
   `Agent:` / `Role:` / `External I/O:` docstring. 🪰 `scripts/` is **not** in the coverage source
   list, so these files do not move the 100 % floor — write tests because they are how you know the
   check works, not to satisfy the gate.

### Out of scope (do NOT build this sprint)

- **Repairing any link.** The 123 are already repaired in `48f7d58`; if the check finds new ones, list them in the handback and fix only what your own changes introduced.
- **Work-queue item 22** (one `**Status:**` vocabulary across sprint docs). Same family, separate sprint, and it needs a data migration across ~70 documents.
- **Anything under `agents/`, `contracts/`, `kernel/`.**
- **Changing the markdownlint rules.** Item 73 settled those. This check is orthogonal to markdownlint and must not duplicate a rule it already enforces.

### The road not taken (LAW-06)

- **Use an off-the-shelf link checker** (`lychee`, `markdown-link-check`). Rejected: both want network access for external URLs and a pinned binary or npm package per platform; the gate must run offline, and the repo already pays a pinned-tool cost for `markdownlint-cli2`. The internal-only rule is ~80 lines.
- **Add link checking as a markdownlint custom rule.** Rejected: it would run under `make markdown`, which is **not** in `make ci` — the finding would stay outside the gate, which is the whole complaint.
- **Check version monotonicity as well as format.** Rejected for this sprint: see Part B item 4.
- **Fail only on new breakage, with a baseline of the existing ones.** Rejected: there are zero left, so a baseline would start empty and only ever serve to let the next one through — item 33's 57 baselined warnings are the cautionary case.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **How code spans are excluded** — fenced blocks *and* inline spans, with the measured
   `probes[probe](env)` case as the test.
2. **How the "text looks like a path" rule is bounded** — it must catch the `codeql/README.md` case
   without firing on ordinary prose link text. Name the boundary you chose and what it lets through.
3. **Which trees are out of scope, and why** — inherit `.markdownlint-cli2.jsonc`'s reasoning or
   state where you diverge.

---

## Blast radius — measured 2026-09-21

| What | Detail |
| --- | --- |
| Files changed | `scripts/check_markdown_links.py` *(new)*, `scripts/check_version_scheme.py` *(new)*, `scripts/gate_selftest_cases.py` **375**, `Makefile`, `.github/workflows/ci.yml`, two new test files |
| Agents affected | **none** |
| Contract change? | No |
| Graph vocabulary change? | No |
| New env keys / tunables | none |
| Deploy implication | 🟩 **None — no image contains `scripts/`.** No deploy, no retag. |

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 A link to a missing file fails the check | fixture `.md` with `[x](nope.md)` | non-zero exit, message names `file:line` and the href |
| A2 | A link to an existing file passes | fixture pair | exit 0 |
| A3 | A `#fragment` matching no heading fails | fixture with `[x](other.md#nope)` | non-zero exit |
| A4 | 🪤 A duplicate heading's `-1` anchor resolves | two identical headings | exit 0 — the slugger must match GitHub, not guess |
| A5 | 🪤 A link-shaped string inside a code span is not a link | the measured `` `probes[probe](env)` `` line | exit 0 |
| A6 | 🪤 A fenced block containing `[x](nope.md)` is not a link | fenced fixture | exit 0 |
| A7 | 🎯 Link text naming a path that differs from the target fails | `[a/b.md](../c.md)` | non-zero exit — the `codeql/README.md` shape |
| A8 | External and mail links are ignored | `https://`, `mailto:` | exit 0 with no network call |
| A9 | 🎯 `0.103.0` is rejected, `0.103.00` accepted | two fixture `pyproject.toml` bodies | the exact S220 defect fails |
| A10 | Every version this repo has shipped is accepted | the tag list in Measured | `0.99.00` and `0.100.00` both pass |
| A11 | 🪤 A `uv.lock`-style normalised version does not fail the repo | real `pyproject.toml` + real `uv.lock` on disk | exit 0 — the check reads the right file |
| A12 | 🎯 Both gates are registered in the self-test | `scripts/gate_selftest.py` run | each planted violation is rejected by its named command |

---

## Success factors

- [ ] `make ci` exits non-zero on a planted dead link, and on a planted `0.103.0`.
- [ ] Both checks appear in `Makefile`, `.github/workflows/ci.yml` **and** `gate_selftest_cases.py`.
- [ ] `uv run python scripts/gate_selftest.py` passes with both new cases.
- [ ] The full-tree run over `main` today reports **0** — no pre-existing breakage is left unexplained.
- [ ] No network access, no `.env`, no git remote required by either check.
- [ ] Each measured false positive (A5, A6, A8, A11) is a test, not a comment.
- [ ] Design decisions recorded with rejected alternatives.
- [ ] Law-cycle question answered **No**, with the reason.
- [ ] Every new guard planted, watched to fail, restored — stated per guard.
- [ ] Every touched module < 200 lines; `gate_selftest_cases.py` is **375** and already over — 🪤 it is **not** in `check_module_size.py`'s path list, so adding to it is allowed; do not "fix" it here.
- [ ] `make ci` exit 0, 100.00 % coverage, redirected to a file.

---

## Traps

🪤 **A checker that reports a link that is not a link is worse than no checker.** The `env` false
positive is in the repo right now; if your implementation reports it, the first thing anyone does is
add an ignore, and the ignore list becomes the next item 33.

🪤 **A link can resolve and still lie.** A7 exists because a mechanical `../` repair produced exactly
that this morning. Resolution is necessary and not sufficient.

🪤 **`uv.lock` disagrees with `pyproject.toml` by design.** If Part B reads the lock file it will
fail on a correct repo, and the obvious "fix" is to loosen the rule — which would have let `0.103.0`
through.

🪤 **The version check runs on every branch, including yours.** Pick your own bump correctly or the
gate you just added will stop your own merge. That is the check working.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
- Module docstring declares `Agent:` / `Role:` / `External I/O:` — enforced for `scripts/`.
- No magic numbers — `kernel.tunable(..., why=...)` does not apply to `scripts/`; constants there are module-level with a comment saying where the rule is written down.
- Faults, not silent failure.
- `make ci` **all steps** green, **100.00 % coverage floor**. **Never measure the gate through a pipe** — redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it. 🪤 Your own bump must satisfy Part B.
- Secrets never through the worktree — a worktree has **no `.env`**. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving** — it resolves the SHA from the working directory and ignores a `SHA=` argument. **Check the printed SHA against `git rev-parse HEAD`.**
2. Merge to `main` locally and push.
3. **Post-merge CodeQL** — `codeql.yml` runs only on `main`.
4. **No deploy.** Nothing in any image changes.

---

## Handover — paste this to the builder

```text
Sprint 221 - a rule the repo states is a rule the gate enforces.
Repo: trading-agents. Branch: sprint-221-a-rule-the-repo-states-is-a-rule-the-gate-enforces
(create it BEFORE any code; never work on main). Full spec:
docs/sprints/sprint-221-a-rule-the-repo-states-is-a-rule-the-gate-enforces.md - read it whole first.

WHAT IS WRONG TODAY
Two rules this repo writes down are enforced by nobody.
1. LINKS. On 2026-09-21, 123 of the relative links in the 459 tracked .md files resolved to no
   file - 112 of them in docs/state-archive/, where the files moved down a directory and their
   links were never re-prefixed. `make markdown` was exit 0 the whole time: markdownlint's MD051
   only validates fragments INSIDE one document, and no rule looks at links BETWEEN files. The 123
   are already repaired (48f7d58). This sprint is the check that stops it coming back.
2. VERSION. S220 was handed back with version = "0.103.0". The scheme is MAJOR.MMM.PP and the last
   group is TWO digits, so it must be "0.103.00". CLAUDE.md calls breaking it a blocker. make ci
   was exit 0 over it, because no gate step reads the version at all.

BUILD TWO CHECKS
A. scripts/check_markdown_links.py - over `git ls-files "*.md"`:
   - every relative link target exists;
   - every #fragment on a .md target matches a heading, GitHub slug rules, duplicates get -1/-2;
   - link TEXT that looks like a path matches the target it points at. (A mechanical repair this
     morning produced [codeql/python-security/README.md](../../README.md): it RESOLVES and still
     lies, because the file named in the text does not exist. A resolver alone cannot see this.)
   It must NOT flag: anything in a fenced block or inline code span; http/https/mailto/autolinks;
   the trees .markdownlint-cli2.jsonc already ignores.
B. scripts/check_version_scheme.py - read pyproject.toml [project] version ONLY:
   MAJOR.MMM.PP, middle 1-3 digits, patch EXACTLY 2 digits, no v prefix, no suffix.

WIRE EACH INTO ALL THREE PLACES - a check in one place only is the defect this sprint is about:
   1. the Makefile `ci:` target,
   2. .github/workflows/ci.yml as its own named step,
   3. scripts/gate_selftest_cases.py - one FailureCase per check, with the planted file and the
      command that must reject it. Read that file first; follow its existing entries exactly.

ORDER OF WORK
1. Read CLAUDE.md (Version scheme + CI gate), scripts/gate_selftest_cases.py,
   scripts/check_param_law_sync.py + tests/test_param_law_sync.py (the house pattern),
   .markdownlint-cli2.jsonc. Fill the Law reading record. LAW-CYCLE ANSWER IS "No" - no agent,
   no contracts/ file is touched. Confirm it, do not re-decide it.
2. Record the design decisions in docs/design-log.md (next free DL number, re-check at merge).
3. PLANT THE FAILING TESTS FIRST: a dead link must fail; "0.103.0" must fail. Watch both fail
   before the scripts exist. Paste the red output into the spec.
4. Implement. 5. Break each new guard, watch it go red, restore it, say so per guard.
6. make ci, ALL steps, redirected to a FILE (make ci > /tmp/ci.txt 2>&1 ; echo $?) then read the
   file. NEVER pipe it - a pipe reports the pipe's exit code and a real failure reads as green.
7. Fill the handback sections, set Status: BUILT.

MEASURED FALSE POSITIVES - each one is a required test, not a comment
- docs/sprints/sprint-108-vault-seeder.md:61 contains `probes[probe](env)` inside a code span. A
  naive regex reads it as a link to "env". If your checker reports it, someone adds an ignore, and
  the ignore list becomes the next pile of accepted debt.
- uv.lock NORMALISES trailing zeros: with 0.102.00 in pyproject.toml, uv.lock records 0.102.0. A
  version check that reads uv.lock FAILS ON A CORRECT REPO. Read pyproject.toml.
- Versions the check must accept, from real tags: 0.90.16, 0.94.02, 0.98.11, 0.99.00, 0.100.00,
  0.102.00, 0.103.00. Note 0.99.00 comes BEFORE 0.100.00 in this repo's history.

DO NOT
- Do not touch anything under agents/, contracts/ or kernel/. If a check makes you want to edit an
  agent, the check is wrong - stop and report.
- Do not repair links. They are already repaired. If the check finds new ones, list them.
- Do not add monotonicity or bump-kind checking. Format only.
- Do not build work-queue item 22 (the Status vocabulary). Separate sprint.
- Do not add a baseline / allowlist of existing failures. There are zero left; a baseline would
  only ever serve to let the next one through.
- Do not make either check touch the network, .env, or a git remote. make ci runs offline.
- Do not "fix" the fact that gate_selftest_cases.py is 375 lines - it is not in the module-size
  path list. Add to it. Do not fix the Makefile/ci.yml step-count drift either; REPORT it in your
  Return notes.

YOUR OWN BUMP
This is a PATCH (tooling, no new capability): the last two digits move, the rest stay. Your own
version must satisfy the check you are adding - if it does not, the gate stops your merge, and
that is the check working.

HANDBACK CONTRACT
Fill the Law reading record BEFORE your first code change. Fill the Test plan results table - a
test you chose not to write needs a reason, not a blank. Fill Closeout - evidence with real pasted
output (the RED run first, then the green). Fill Return notes. Set Status: BUILT. Anything not met
is stated plainly as "verified failing" or "not done". An incomplete handback is returned.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02).

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | File(s) read | What binds it | Did reading change your approach? |
| --- | --- | --- | --- |
| Existing CI and version rules | `CLAUDE.md` | `make ci` is offline and must be proven by redirected output; versions use `MAJOR.MMM.PP` with a two-digit patch group. | Yes — the version checker reads only `pyproject.toml`, and final CI evidence will be redirected to a file. |
| Gate failure proof | `scripts/gate_selftest_cases.py`, `scripts/gate_selftest.py` | Every gate owns a planted `FailureCase`; self-test probe files are untracked and removed after each command. | Yes — the Markdown checker will keep tracked-file discovery as its default and accept an explicit probe path for the self-test. |
| Checker and unit-test pattern | `scripts/check_param_law_sync.py`, `tests/test_param_law_sync.py` | Gate scripts expose `main(argv) -> int`; tests assert both exit code and actionable output. | Yes — both new checks will follow the same command-line and direct-unit-test shape. |
| Markdown scope | `.markdownlint-cli2.jsonc` | Generated CodeQL reports are excluded; `node_modules`, `.venv`, and mutation scratch output are outside the Markdown lint scope. | Yes — the link checker will inherit these exclusions rather than add a baseline. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** **No.** The change is offline repository tooling enforcing existing `CLAUDE.md` rules; it changes nothing under `agents/`, `contracts/`, or `kernel/` and adds no agent guarantee.

**Contradictions found between a rule and this spec:** none.

**Rules found silent where a decision was needed:** none; the bounded path-label rule and Markdown exclusion implementation are recorded in `DL-190`.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status |
| --- | --- | --- | --- |
| A1 | `test_missing_relative_link_fails_with_location_and_href` | `tests/test_check_markdown_links.py` | PASS — names source line, href, and missing-target rule |
| A2 | `test_existing_relative_link_passes` | `tests/test_check_markdown_links.py` | PASS |
| A3 | `test_missing_markdown_fragment_fails` | `tests/test_check_markdown_links.py` | PASS |
| A4 | `test_duplicate_heading_fragment_uses_github_suffix` | `tests/test_check_markdown_links.py` | PASS |
| A5 | `test_inline_code_link_shape_is_ignored` | `tests/test_check_markdown_links.py` | PASS |
| A6 | `test_fenced_link_shape_is_ignored` | `tests/test_check_markdown_links.py` | PASS |
| A7 | `test_path_like_link_text_must_match_target` | `tests/test_check_markdown_links.py` | PASS |
| A8 | `test_external_mail_and_autolinks_are_ignored` | `tests/test_check_markdown_links.py` | PASS |
| A9 | `test_rejects_single_digit_patch_group` | `tests/test_check_version_scheme.py` | PASS — `0.103.0` rejected |
| A10 | `test_accepts_versions_from_real_tags` | `tests/test_check_version_scheme.py` | PASS — all seven listed tag formats accepted |
| A11 | `test_real_pyproject_passes_despite_normalized_lockfile` | `tests/test_check_version_scheme.py` | PASS — `pyproject.toml` and normalized `uv.lock` differ by design |
| A12 | `FailureCase(name="markdown-links")` and `FailureCase(name="version-scheme")` | `scripts/gate_selftest_cases.py` | PASS — `gate_selftest.py` 23/23 |

**Tests added beyond the plan:** `test_heading_fragment_keeps_inline_code_content`, `test_path_like_text_accepts_repository_relative_target`, `test_missing_image_target_fails`, `test_generated_report_tree_is_ignored`, and malformed-version parameter cases.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\Downloads\project\trading-agents-sprint-221-a-rule-the-repo-states-is-a-rule-the-gate-enforces` on `sprint-221-a-rule-the-repo-states-is-a-rule-the-gate-enforces`; `.env` absent (verified `False`).

**Result:** `make ci` now calls both offline checks: a tracked relative link target, Markdown fragment, or filename-like label that does not resolve truthfully exits non-zero; a `[project] version` outside `MAJOR.MMM.PP` exits non-zero. The self-test proves each failure path.

**Files changed:** `scripts/check_markdown_links.py`, `scripts/check_version_scheme.py`, `tests/test_check_markdown_links.py`, `tests/test_check_version_scheme.py`, `scripts/gate_selftest_cases.py`, `Makefile`, `.github/workflows/ci.yml`, `pyproject.toml`, `uv.lock`, `docs/design-log.md`, `docs/STATE.md`, and this handback.

**Design decisions:** recorded as `DL-190` — code spans are syntax rather than an allowlist; path-label comparisons accept the four established local forms; Markdownlint exclusions are inherited; GitHub heading slugs retain inline-code text.

**Proof — the red run first:**

```text
FAILED tests/test_check_markdown_links.py::test_missing_relative_link_fails_with_location_and_href
Failed: markdown link checker is missing: No module named 'scripts.check_markdown_links'
FAILED tests/test_check_version_scheme.py::test_rejects_single_digit_patch_group
Failed: version scheme checker is missing: No module named 'scripts.check_version_scheme'
============================= 2 failed in 31.60s ==============================
```

**Proof — the green run:**

```text
MAKE_CI_EXIT=0
uv run python scripts/check_markdown_links.py
uv run python scripts/check_version_scheme.py
Required test coverage of 100.0% reached. Total coverage: 100.00%
================= 2975 passed, 6 skipped in 124.44s (0:02:04) =================
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 4 new file(s)
```

**Full-tree run over `main`:** branch checker ran against `git -C C:\Users\yury_\Downloads\project\trading-agents ls-files "*.md"` and the `main` worktree contents: **0 findings**, exit 0. The real `pyproject.toml` version check also exited 0.

**Gate self-test:** `uv run python scripts/gate_selftest.py` — `PASS can-fail: markdown-links — rejected (exit 1)`; `PASS can-fail: version-scheme — rejected (exit 1)`; `gate self-test: 23/23 passed`.

**Guards planted:** Markdown links: `docs/_gate_selftest_probe_dead_link.md` with `[missing](nope.md)` was rejected, then removed by the self-test. Version scheme: `scripts/_gate_selftest_probe_pyproject.toml` with `0.103.0` was rejected, then removed by the self-test.

**Module line counts:** `check_markdown_links.py` 186; `check_version_scheme.py` 33; `test_check_markdown_links.py` 101; `test_check_version_scheme.py` 48. `gate_selftest_cases.py` is 390 and remains outside the module-size path list, as the spec allows.

**`make ci`:** redirected to `C:\Users\yury_\AppData\Local\Temp\sprint-221-ci-retry.txt`; exit 0; 2975 passed, 6 skipped, 100.00 % coverage; pip-audit clean; tracked and untracked detect-secrets passed.

**`make gate-ran`:** not done — this branch has not been committed or pushed, so no remote SHA exists to prove.

```text
not run: branch is local and unpushed
```

**Not met / verified failing, as handed back:** remote `make gate-ran`, merge and post-merge CodeQL
were not done; no deploy is required. 🟩 **Discharged by the planner the same day** — see below.

🔴 **One defect the handback did not catch, found by probing the checker rather than reading it.**
`_slug()` dropped underscores, so a heading like `## reward_risk gate` produced the anchor
`rewardrisk-gate` while GitHub produces `reward_risk-gate`. **GitHub keeps hyphens *and*
underscores.** Measured on a fixture before the fix:

```text
under.md:5: missing fragment 'reward_risk-gate' in href '#reward_risk-gate'
exit=1
```

🎯 **This is the exact failure mode the spec named as disqualifying** — a checker reporting a
*valid* link as broken. It passed every test and the full corpus only because no document links
to an underscored anchor **yet**; this repo's headings are full of `reward_risk`,
`max_position_pct` and `vix_status`, so the first one to do so would have met a red gate on a
correct link — and the obvious response would have been an ignore entry, which is how item 33's
57 baselined warnings began.

**Fixed** in `_slug()` (`char in " -_"`), with `test_heading_fragment_keeps_underscores` added as
the regression. **Guard planted and watched:** reverting the one character turns that test red
(`1 failed`, output `missing fragment 'reward_risk-gate'`), restoring it turns it green (`1 passed`).

🪰 **Filed rather than fixed here:** `scripts/check_markdown_links.py` is **220** lines, past the
200 hard block — but `check_module_size.py` runs on `$(PKGS) tests` and **`scripts/` is not in
that list**. **15** files under `scripts/` already exceed 200 (largest **411**), so this file is
not an outlier and the sprint is not where that gets fixed. Recorded as work-queue item **78**,
which is the same shape as the two rules this sprint just closed.

---

## Return notes

- Scope held: no file under `agents/`, `contracts/`, or `kernel/` changed; no law cycle or deploy is owed.
- The `Makefile` vs `ci.yml` drift remains: the workflow quality job runs `gate_selftest.py`, while `make ci` does not; workflow tests/security are separate jobs. Both new checks are in both the local target and CI quality job, as required.
- The path-label comparison intentionally accepts source-relative, repository-relative, `docs/`-relative, and basename forms already used by tracked documents. It still rejects a label such as `codeql/python-security/README.md` when its href resolves elsewhere.
