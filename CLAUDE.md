# CLAUDE.md — project-level rules for Claude Code

These rules are in effect for every session in this repo. They override defaults.
Keep this file short: only hard behavioral rules, not documentation.

---

## Navigation — always use INDEX.md

Before exploring any folder in `docs/`, read its `INDEX.md` first.
Do not open random files to discover what's there — the index tells you.

| Entry point | Use when |
| --- | --- |
| `docs/INDEX.md` | Starting any docs task — maps every file and subfolder |
| `docs/decisions/INDEX.md` | Checking if an architecture question is already settled |
| `docs/laws/INDEX.md` | Understanding the law book structure or agent law status |
| `docs/research/INDEX.md` | Checking if a tool or library has already been evaluated |
| `docs/sprints/INDEX.md` | Finding which phase a sprint belongs to or what is queued |
| `docs/sprints/README.md` | Full chronological sprint list with goal summaries |

The same rule applies to agent folders: before digging into `agents/<name>/`,
check `agents/<name>/laws/laws.md` if a law question is involved.

---

## CI gate — always run all 9 steps

```bash
make ci
```

Never declare a change "green" without `make ci` passing locally **and** without
polling `gh run list` after pushing to confirm GitHub CI also passes.
The gate has 9 steps: ruff, format, mypy, import-linter, module size, module header,
pytest (100 % coverage floor), pip-audit, detect-secrets.

---

## Version scheme — HARD RULE

`MAJOR.MM.PP` in `pyproject.toml`.

- **feat** (new capability, new agent, new endpoint) → bump the **two middle digits** (MINOR).
- **fix** (bug, CVE patch, refactor) → bump the **last two digits** (PATCH).
- A higher bump zeroes all lower groups: `0.11.00` not `0.11.04`.

Breaking this rule is a blocker — do not merge.

---

## Module size — hard block

- **200 lines**: hard block (`make ci` fails).
- **150 lines**: warning (visible in CI output; must not grow past 200).

Split modules before they hit the hard block. Do not use `# noqa` to bypass.

---

## Architecture boundaries — enforced by import-linter

```text
kernel  ←  contracts  ←  agents  ←  orchestration / surfaces
```

Agents never import other agents. Agents talk only via typed messages on the bus.
`kernel` imports nothing from `contracts`, `agents`, or any layer above it.

Violations break `make ci`. Never add an import that crosses a boundary.

---

## Branch convention

Every sprint or chore on its own branch named `sprint-NN-<slug>` or `chore-<slug>`.
Merge to `main` is the deploy trigger. Never commit sprint work directly to `main`.

---

## Law conventions (when working on agent laws)

- Every functional test for a law clause **must** cite the clause ID in its docstring
  (e.g., `"""PROV-OUT-01 / PROV-NEV-01: ..."""`). Gray ⬜ → green 🟩 requires this.
- The provider `laws.md` is **LOCKED v1** (S69). Copy `docs/laws/_TEMPLATE.md`
  (not provider's `laws.md`) as the base for new agent laws.
- Do not edit `docs/laws/_TEMPLATE.md` without completing a new full law cycle.

---

## State file discipline (LAW-02)

When updating `docs/STATE.md`, stamp "Last updated" with Melbourne local time
`HH:MM AEST` (GMT+10) or `HH:MM AEDT` (GMT+11, Oct–Apr). Not just the date.

**Intent → perform → proven result (LAW-02: success is proven, never assumed).** Log each item
as **INTENT** — what, plus its **verifiable success factors** (the definition-of-done). After doing
it, report the **PROVEN RESULT**: the checks that actually passed (tests, `make ci`, the named
postcondition). **Never restate the intent as if it were the outcome** ("did X" without proof is
forbidden). An item moves to *Recent / shipped* **only when its success factors are verified** — and
if a success factor is *not* met, say so plainly (e.g. "verified failing"). This binds every session.

**Single live tracker — STATE.md only.** `docs/STATE.md` is the *one* live status/direction doc
(Now/Next, updated every session). `docs/build-plan.md` is the **phase record + standing principles**,
not a status board: reconcile its Status table *only* at a phase closeout, and never treat it as current
state. Live "does it work" proof lives in `docs/laws/ledger.md` + `docs/laws/drift-register.md`. Keeping
exactly one live tracker is what stops them drifting — the build-plan went stale once because two docs
both tried to track status.

---

## Capture decisions — the conversation is part of the work (LAW-06)

When a discussion produces a **decision, trade-off, discovered constraint, or ruled-out
option**, record it **in the same unit of work**, while fresh — chat logs are volatile.

- In-flight / not-yet-final reasoning → `docs/design-log.md` (options, **ruled-out + why**, status).
- A closed question (decided "forever" until reopened) → an ADR in `docs/decisions/` + INDEX row.
- Capture the **road not taken**, not just the choice. A decision discussed but unrecorded is
  treated as not-yet-made. Full law: `ops/laws/LAW-06-capture.md`.
