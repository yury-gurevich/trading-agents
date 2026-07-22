<!-- Agent: planning | Role: research — retrospective defect-detection-rate analysis -->
# Defect detection rate — retrospective over the drift register

**Date:** 2026-07-22 · **Part of:** [R006](INDEX.md) · **Method:** analysis only, no tooling added

R006 recommended one action: measure, retrospectively, how many real defects our test suite
actually caught. This is that measurement. It uses `docs/laws/drift-register.md` (23 rows), which
conveniently **annotates its own detection mechanism** in the `Kind` column.

---

## 1 · Classifying all 23 rows

| Class | Rows | n |
| --- | --- | ---: |
| **Escaped code defects** | 006, 007, 009, 011, 012, 013, 014, 016, 017, 018, 019, 020, 021, 022 | **14** |
| Intent / doc / design drift (not defects) | 001 `PRD-fork`, 002 `stale-doc`, 003 `gap/scope`, 004–005 `gap(enrich)`, 008 design record, 010 `stale-doc`, 015 `stale-doc` | 8 |
| Infrastructure / plan limit | 023 `dep-health` (Neon free-tier ceiling) | 1 |

## 2 · What detected each escaped defect

The register states this outright. Verbatim `Kind` fragments:

| Detector | Rows | Evidence in the register |
| --- | --- | --- |
| **Live / real-environment run** | 009, 012, 013, 014, 020, 021 | "real-probe finding", "surfaced by live acceptance" (×3), "production-regime teardown exposed it", live-proven S128 |
| **Real backend / container** (not the double) | 011, 016, 017, 018, 019 | "Neo4j-only; **in-memory hid it**", "container-only; **unit gate hid it**" (×2), "container entrypoint; **hidden by local graph demos**", "Postgres-only evidence capture" |
| **Law-authoring audit** | 006, 007 | both `CORRECTED (S69)` during the provider law cycle |
| **Manual / UX use** | 022 | dashboard run-selector scoping |
| **Unit test suite** | — | **none** |

### Headline

> **Unit-suite detection rate over escaped defects: 0 / 14 = 0 %.**
> In **4** cases the register explicitly records that a **test double or the unit gate *concealed*
> the defect** ("in-memory hid it", "unit gate hid it" ×2, "hidden by local graph demos").

## 3 · The honest caveat — this is not "unit tests don't work"

The drift register records defects that **escaped**. Anything the unit suite catches during
development never becomes a `DRIFT` row, by construction. So this measures the *residual* after
unit testing, not the suite's total value.

The correct reading is therefore sharper and more useful:

> **The entire escaped-defect population consists of failure modes unit tests cannot observe by
> construction** — container startup and entrypoints, backend-specific behaviour, live API rate
> limits, broker state divergence, and infrastructure ceilings.

Which means: **more unit-test strength cannot move this population.** Not because the tests are
weak — at 100 % coverage and an 84.36 % scoped mutation kill-rate they are strong — but because
the residual risk lives on the other side of every test double we use.

## 4 · Consequences

1. **Confirms R006's park/skip.** Pseudo-tested detection and a higher mutmut cadence target a
   defect class with **zero recorded escapes**. S132+S134 (79.87 % → 84.36 %) remain worthwhile as
   *insurance against future logic regression* — especially S134's money-parser assertions, which
   guard real financial arithmetic — but they have no measurable defect-prevention return to date.
2. **LAW-02 is doing all of the work.** "Every sprint ends with a real-environment functionality
   check" is not ceremony; it is empirically **the only mechanism that has ever caught a defect
   here**. Protect it before optimising anything else.
3. **The highest-leverage gap is double-vs-reality fidelity** — the "hid it" class. The S116
   backend parity suite (InMemory / Neo4j / Postgres) was exactly this remedy and is the template.

### The one repeating pattern worth acting on

**DRIFT-016, 017 and 018 are the same defect shape three times**: an agent container that does not
start its real entrypoint, invisible to the unit gate and to local graph demos, caught only by a
live fleet run. That is a repeating, mechanically-detectable failure with three data points.

**Recommendation:** a standing **container smoke check** — build each agent image, start it, assert
it reaches its real entrypoint and EHLOs — promoted from a per-sprint manual act to an automated
step. It would have caught all three. This is a far better use of the next quality hour than any
additional unit-test metric.

## 5 · Bottom line

| Question | Answer |
| --- | --- |
| Did the test suite catch our real defects? | No — 0 of 14 escaped defects |
| Is the suite therefore bad? | No — the escapes are structurally invisible to unit tests |
| Should we add more unit-test-quality tooling? | **No** (confirms R006) |
| Where does the next quality hour go? | Container smoke parity, then live-check discipline |

**Revisit trigger:** a decision-engine logic defect reaches production (a `DRIFT` row unit tests
*should* have caught). That would invert this finding and reopen pseudo-tested detection.
