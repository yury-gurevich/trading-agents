# AGENTS.md — rules for any coding agent working in this repo

**[`CLAUDE.md`](CLAUDE.md) is the source of truth.** Read it before you start. This file exists so
agents that look for `AGENTS.md` (Codex and others) find the same rules; where the two ever
disagree, **CLAUDE.md wins** and the disagreement is a bug to report, not a choice to make.

Below is the short form. It is not a substitute for reading `CLAUDE.md` and the sprint handover you
were given.

---

## The non-negotiables

1. **Navigate via `INDEX.md`.** Before exploring any folder under `docs/`, read its `INDEX.md`
   first. Do not open random files to discover what is there. Same for agent laws:
   `agents/<name>/laws/laws.md`.

2. **`make ci` must pass — all 12 steps.** ruff, format, mypy, import-linter, module size, module
   header, law coverage, PARAM/settings sync, pytest at a **100.00 % coverage floor**, pip-audit,
   detect-secrets, untracked secrets. Never lower the floor. Never declare work green without running
   it, and confirm the remote gates after pushing.

3. **Version scheme `MAJOR.MM.PP` in `pyproject.toml` — a hard rule.** *feat* bumps the **two
   middle** digits; *fix* bumps the **last two**. A higher bump zeroes all lower groups
   (`0.11.00`, not `0.11.04`). Stage `uv.lock` with the bump.

4. **Module size is a hard block at 200 lines** (warning at 150). Split modules; never use `# noqa`
   to bypass the check.

5. **Architecture boundaries, enforced by import-linter:**
   `kernel ← contracts ← agents ← orchestration / surfaces`.
   **Agents never import other agents** — they talk only via typed messages on the bus. `kernel`
   imports nothing from any layer above it.

6. **Branch per sprint or chore** — `sprint-NN-<slug>` or `chore-<slug>`, created *before* coding.
   Never commit sprint work directly to `main`. Push the branch and see it green on the remote
   before anyone merges. Do not merge to `main` yourself unless told to — merge is the deploy
   trigger.

7. **Secrets never enter the worktree**, not even as untracked scratch files. Use the gitignored
   `.env` / `infra/*.local.json`, or receive them via chat. detect-secrets is the last line of
   defence, not the process.

8. **No magic numbers.** Any value that influences processing or a forecast is declared with
   `kernel.tunable(..., why=...)`, justified and bounded — never a bare literal.

9. **Faults, not silent failure.** Wrap fallible work in `kernel.fault_boundary`; errors are
   redirected with provenance, never swallowed. A failure that is invisible is worse than one that
   is loud.

10. **Every module docstring declares `Agent:` / `Role:` / `External I/O:`.** Enforced by
    `scripts/check_module_header.py`.

---

## Proof discipline (LAW-02) — this is the one people get wrong

**Success is proven, never assumed.** Report what actually passed — the tests, the `make ci`
output, the named postcondition — and never restate an intention as though it were an outcome.
"Did X" without evidence is forbidden.

If a success factor was **not** met, say so plainly ("verified failing", "not done"). **A proven
failure is a valid handback; a silent gap is not.** Do not quietly narrow scope to make a result
look clean.

## Capture the reasoning (LAW-06)

A decision, trade-off, discovered constraint, or ruled-out option is recorded **in the same unit of
work**, while it is fresh:

- in-flight reasoning → `docs/design-log.md` (options, **ruled-out + why**, status);
- a closed question → an ADR in `docs/decisions/` plus its `INDEX.md` row.

Capture the **road not taken**, not just the choice. A decision discussed but unrecorded is treated
as not-yet-made.

## Laws

Agent behaviour is governed by locked constitutions at `agents/<name>/laws/laws.md`, with clause IDs
like `EXEC-NEV-03` or `MON-STA-02`. Any test covering behaviour a clause governs **must cite that
clause ID in its docstring**. `laws.md` files are **LOCKED** — if one is wrong, add a row to
`docs/laws/drift-register.md` and report it; never edit the law to match the code.

Some sprint handovers require you to **read the relevant laws before writing code** and record what
you read. When they do, that is a gate, not a suggestion.

## The sprint handover is binding

Your task lives in `docs/sprints/sprint-NN-<slug>.md`. It is written to be executed end to end by a
cold-start agent. Fill every `**Result:**` line **in that file**, then its **Closeout — evidence**
and **Return notes** blocks, with real command output pasted in — not a summary, not a separate
report, not chat-only. Stay inside the sprint's scope; anything else you find gets flagged, not
fixed. An incomplete handback is returned, not repaired.
