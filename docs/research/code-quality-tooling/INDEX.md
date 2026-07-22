<!-- Agent: planning | Role: research index — code-quality & test-effectiveness tooling -->
# R006 — Code-quality & test-effectiveness tooling: PyExamine and the unused test-effectiveness methods

**Date:** 2026-07-22 · **Status:** 🗄️ Archived — **nothing adopted** · **Tags:** `code-smells`
`test-effectiveness` `mutation-testing` `pyexamine` `tooling` `signal-to-noise`

**Answers:** Should we add PyExamine (multi-level Python smell detection)? Of the standard
test-effectiveness methods (code coverage, mutation testing, defect detection rate,
pseudo-tested detection, flakiness/maintainability), which do we not use — and do we need them?

**Outcome:** No new tool adopted. One **non-tool** recommendation carried forward: run a
retrospective **defect-detection-rate** analysis over the existing drift register, because it
exposes a strategic mismatch between where defects actually occur and where test effort goes.

---

## 1 · PyExamine — evaluated, not adopted

**What it is.** An academic tool ([arXiv 2501.18327](https://arxiv.org/abs/2501.18327),
[IEEE 11025624](https://ieeexplore.ieee.org/document/11025624/)) detecting Python code smells
across three layers — architectural, structural, code-level — 49 smell types, validated on 183+
projects. Reported recall: 91.4 % code-level, 89.3 % structural, 80.6 % architectural. The paper
names its own limitations: **false positives, especially architectural**, and **complex initial
configuration**.

**Why not adopted:**

1. **Near-total overlap with an already-*enforcing* gate.** Architectural → `import-linter`
   (kernel ← contracts ← agents ← orchestration/surfaces; agents-are-islands; fails CI).
   Structural → 200-line hard block / 150-line warning + module-header check + ruff complexity.
   Code-level → ruff (pyflakes/pycodestyle/pylint/McCabe subsets) + strict mypy. Ours **block**;
   PyExamine only **reports** — trading a blocking gate for a report is a downgrade.
2. **Its confident complaints would be architecturally wrong here.** This codebase
   **deliberately duplicates logic across agents** because the island rule forbids cross-agent
   imports (S115 ships duplicated catalogue math with a parity test). A generic detector flags
   that as a major structural smell. "Un-opinionated" is the problem, not the selling point: it
   cannot know ADR-0012's platform/pack wall or the island rule.
3. **Wrong shape for our actual failures** — see §2; our defects are integration-shaped, not
   smell-shaped. The 200-line cap already makes god modules impossible.
4. **Signal-to-noise (DL-52).** Adding an advisory tool with acknowledged architectural false
   positives, right after a persistent ignored red marker cost ~2.5 weeks of blindness, is the
   wrong direction. The DL-52 fix was *fewer, real, enforcing* signals.
5. **Research-artifact maintenance risk** — a 2025 conference tool, not a maintained linter with
   an ecosystem; we would own the config complexity and FP triage.

**Revisit triggers.** (a) A cohesion/coupling blind spot becomes a demonstrated problem —
`import-linter` enforces *declared* contracts but measures neither cohesion nor emergent coupling,
and the 200-line cap is a crude proxy. (b) PyExamine becomes a maintained, packaged tool with a
configurable rule set that can be made *enforcing* rather than advisory.

## 2 · Test-effectiveness methods — which we use, which we don't

| Method | Cost | Status here |
| --- | --- | --- |
| Code coverage | Low | **In use** — 100 % floor, enforced in `make ci` |
| Mutation testing | High | **In use** — `mutmut`, manual/periodic (WSL-only), 84.36 % scoped kill-rate after S132+S134 |
| Defect detection rate | Medium | **Not used** — *recommended, see below* |
| Pseudo-tested detection | Medium | **Not used** — parked |
| Flakiness & maintainability | Low-Med | **Not used** — no need |

### The finding that drives all three verdicts

Classifying the 23 drift-register rows: DRIFT-015 docs, 016 integration, 017 deployment,
018 config, 019 tooling, 020 state reconciliation (CSCO double-buy), 021 external-API resilience,
022 UI scoping, 023 infrastructure limits. **Not one recorded production defect was a logic defect
in the analyst/PM decision engines** — which is precisely what coverage and mutation testing
target. S132+S134 moved the scoped kill-rate 79.87 % → 84.36 % on engines with *zero* recorded
escaped defects.

That is not wasted work — assertion strength is real insurance against future logic regressions,
and S134's money-parser bucket guards real financial arithmetic. But it means the **next marginal
hour belongs to the integration surface** (feeds, broker reconciliation, deploy/config wiring,
infra limits), not to another unit-test-quality metric.

### Verdicts

- **Defect detection rate — DO IT (analysis, not tooling).** Computable today from
  `docs/laws/drift-register.md` + `docs/laws/functionality-checks.md` + the standing
  "real bug → fix + regression test + drift row" rule. Ask, per drift row: would the suite have
  caught it pre-production, and was a regression test added? Value is the strategic redirect
  above, not the number. Cost: an afternoon, no new dependency.
- **Pseudo-tested detection — PARK.** It is the cheap proxy for what `mutmut` already did
  expensively; its remaining value is catching *newly added* assertion-weak code between manual
  mutmut runs. Given the finding above, that is fighting the last war. **Unverified caveat:** a
  mature Python equivalent of Java's Descartes was *not* confirmed — verify before any adoption.
- **Flakiness & maintainability — SKIP.** The suite is deterministic (offline; the 6 skips are
  env-gated), fast (1692 tests in ~2–3 min), and maintainability is covered by the 200-line cap
  plus module discipline. S134's wording exclusions show over-specification is already reasoned
  about. No observed problem to solve.

**Revisit trigger for the whole section:** a logic defect in a decision engine reaches production
(i.e. a DRIFT row that unit tests *should* have caught). That would invert the finding above and
justify re-opening pseudo-tested detection and a higher mutmut cadence.
