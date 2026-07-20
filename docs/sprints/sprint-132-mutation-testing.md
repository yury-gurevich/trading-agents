<!-- Agent: planning | Role: sprint handover -->
# Sprint 132 — Mutation testing (backlog row G): prove the suite asserts, not just runs

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-132-mutation-testing`
**Status:** ready for handover (packaged 2026-07-20)
**Effort:** M (mutation runs are slow; scope is bounded to compensate)

---

## Why this sprint

Backlog **row G**, trigger fired: "run after a stable sprint" — four clean sprints shipped
back-to-back (S128–S131). 100 % line coverage proves every line *executes* under test; it
does **not** prove a test would *fail* if the line were wrong. Mutmut plants small logic
defects (`>`→`>=`, `+`→`-`, drop a statement, flip a boolean) and reruns the suite per
mutant: a **surviving** mutant is a line whose logic no test actually pins. This sprint
finds and kills survivors in the code where a silent logic bug is most costly — the
deterministic decision engines that gate real (paper) capital.

This is a **test-quality** sprint: it strengthens assertions and, where a survivor exposes a
genuine latent bug, fixes the code. It is NOT a coverage sprint (already 100 %) and adds no
capability.

## What already exists (read before estimating)

- **The suite**: `uv run pytest`, 1608 passing, 100 % line + branch coverage floor
  (`make ci` step 7). 366 non-test modules — **full-repo mutation is impractical** as a
  bounded sprint (hours of runtime), hence the scoped target list below.
- **mutmut is NOT a dependency yet** — add to the `dev` dependency-group in
  `pyproject.toml` (`[dependency-groups] dev`), `uv lock`. It is a dev-only tool: it must
  NOT enter the runtime extra or any agent image.
- **The diskcache/pip-audit precedent**: an offline-only dev tool's transitive CVE goes to
  the hardening backlog, not the runtime — apply the same rule if mutmut drags one in.
- **No `make ci` step runs mutmut** — it is too slow for the per-PR gate (row G says so).
  This sprint runs it **manually**, records the report, and lands only the resulting
  test/code changes. Do not wire mutmut into `make ci`.

## Decisions taken at packaging (LAW-06)

1. **Scope to the deterministic decision engines**, where a weak assertion risks real
   money: analyst scoring + confidence gate (`agents/analyst/domain/`), PM risk/sizing/
   sector gates (`agents/portfolio_manager/`), scanner filters (`agents/scanner/`),
   execution idempotency/broker boundary (`agents/execution/`), the acceptance gate
   (`scripts/accept.py` + its lib), and the deliberation veto context
   (`orchestration/veto*.py`). *Ruled out:* whole-repo mutation (impractical per-sprint —
   revisit incrementally), and mutating surfaces/dashboard/kernel-plumbing first (lower
   money-risk; queue as a follow-up if this sprint proves the tooling).
2. **Every surviving mutant gets one of three honest dispositions**, recorded in the report:
   (a) **killed** by a new/strengthened assertion; (b) **genuine bug** → fixed with a
   regression test citing the mutant; (c) **equivalent mutant** (semantically identical, un-
   killable) → documented with the reason. No survivor is left unexplained. *Ruled out:*
   silencing survivors by excluding files.
3. **A survivor-that-is-a-bug may exceed "test-only"** — if mutation exposes a real logic
   defect in a gate, fixing it is in scope (with a drift-register row if it is a behavioral
   correction). *Ruled out:* deferring a found bug to "later" — a known gate bug is not
   shippable.

## Kickoff (paste this)

> Execute **Sprint 132 — mutation testing** exactly as specified in this file
> (`docs/sprints/sprint-132-mutation-testing.md`). Read first: backlog row G in
> `docs/hardening-backlog.md`; the target modules listed in decision 1; `pyproject.toml`
> dev dependency-group; design-log **DL-48** (the process contract this kickoff enforces).
>
> **Contract (DL-48 — enforced):**
>
> - **Start:** `git pull` on `main` — `pyproject.toml` must read **0.71.04** (stop and
>   report if not). Branch `sprint-132-mutation-testing`. Bump **PATCH → 0.71.05** +
>   `uv lock`.
> - **Drift rule:** before handback, `git fetch`; if `origin/main` moved, merge it in,
>   re-run the full gate, record what moved in the Return notes.
> - **Secrets rule** (CLAUDE.md): unchanged; mutmut is offline.
> - **Handback rule:** Closeout + Return notes last; incomplete handbacks are bounced.
> - Hard gate: `make ci` green (exit code captured), 100 % coverage held, ≤200-line
>   modules, headers. **Do not wire mutmut into `make ci`.**
>
> **Work items:**
>
> - **A (tooling):** add `mutmut` to the `dev` dependency-group; `uv lock`; a documented
>   `mutmut` config (`setup.cfg`/`pyproject`) scoped to the decision-1 target paths with
>   the test command it should run. Confirm it does NOT enter the runtime extra.
> - **B (run + triage):** run mutmut over the scoped targets; produce a survivor report
>   (module, line, mutant, disposition per decision 2). Commit the report under
>   `docs/reports/sprint-132-mutation-testing/`.
> - **C (kill survivors):** strengthen assertions / add regression tests until every
>   survivor is killed, fixed-as-bug, or documented-equivalent. Each new test cites the
>   mutant it kills in its docstring (law-test convention style). If a bug is found, fix it
>   + drift-register row.
> - **D (docs):** backlog row G → Done with the report link + kill-rate metric; if any
>   behavioral fix landed, a drift row; note in the report that mutmut stays a **manual**
>   periodic exercise (not a CI gate) and name the re-run trigger.
> - **Functionality check (LAW-02):** this sprint's "real environment" IS the mutation run
>   — record the before/after survivor counts (the kill-rate improvement) on the scoped
>   targets as the proof; plus `make ci` green. No live infra/graph/broker touch; no
>   teardown needed (offline). State that explicitly.
> - **Wrap up:** README/INDEX rows; Closeout + Return notes; push, hand back.
>   **Do not merge.**

## Guardrails

- mutmut is **dev-only** — never in the runtime extra or any agent image; verify the
  forecaster/provider image builds are unaffected (they should not see it).
- Do not wire mutmut into `make ci` (row G: too slow for per-PR).
- Do not drop coverage or exclude files to make survivors disappear (decision 2).
- Scope stays the decision-1 target list; if time allows more, record it as a follow-up,
  do not silently widen (bounded sprint).
- A found behavioral bug is fixed with a cited regression test + drift row, never deferred.

## Definition of done

1. mutmut runs over the scoped decision-engine targets with a committed survivor report.
2. Every survivor is killed, fixed-as-bug (with regression test + drift row), or documented
   as an equivalent mutant — none left unexplained; kill-rate recorded before/after.
3. Backlog row G → Done; mutmut recorded as a manual periodic exercise with its trigger.
4. `make ci` green at 100 % (exit code captured); mutmut absent from runtime; closeout +
   return notes filled.

## Closeout (coding agent fills; planning agent verifies before merge)

```text
CLOSEOUT — Sprint 132
Branch / merge commit:   <branch> / <merge sha or "not merged by instruction">
make ci:                 MAKE_CI_EXIT_CODE=<n>; <passed/skipped>; coverage <pct>
Functionality check:     <scoped mutation kill-rate before/after; survivor dispositions>
Version:                 0.71.04 → 0.71.05 (PATCH); uv.lock refreshed
Backlog row G:           <status + report link>; behavioral bugs found: <n + drift rows>
Drift rule:              <origin/main moved? merged? re-gated?>
Deviations from spec:    <none, or the honest list>
```

## Return notes (coding agent appends at handback — mandatory)

<!-- return notes go below this line -->
