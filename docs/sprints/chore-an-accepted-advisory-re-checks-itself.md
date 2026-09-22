<!-- Agent: tooling | Role: chore spec + closeout for work-queue item 74 -->
# chore-an-accepted-advisory-re-checks-itself — the gate states what it tolerates, and re-measures why

**Status:** MERGED `750ac98`

**Closes:** [work-queue item 74](../work-queue.md) · **Opens:** [DL-199](../design-log.md) ·
**Type:** feat · **Version:** 0.107.00 · **Branch:** `chore-an-accepted-advisory-re-checks-itself` ·
**Deploys:** nothing (gate tooling only; the fleet stays on `b18014e`)

> **Why this bump kind.** MINOR: the gate gains a check it did not have. `make ci` step 13 is no
> longer `pip-audit` with a flag but a check that audits a different, larger set and can fail for
> three reasons the old step had no way to express.

## Why

[DL-184](../design-log.md) accepted `PYSEC-2026-2447` (`diskcache` 5.6.3, no fix release) by passing
`--ignore-vuln` in both the `Makefile` and `ci.yml`. Item 74's complaint was that the acceptance had
**no expiry and no re-check**: nothing would notice a fix shipping, and the reasoning lived in a
Makefile comment. Building the re-check turned up the larger fact underneath it.

### Measured 2026-09-22 — read these before judging the scope

| Claim | Value | How it was measured |
| --- | --- | --- |
| A clean worktree sees the advisory at all | **No** | *[measured]* fresh `uv sync` in a new worktree: `diskcache` and `dspy` both absent from the venv |
| A clean `pip-audit` there | **`No known vulnerabilities found`, exit 0** | *[measured]* `uv run pip-audit --progress-spinner off` in that worktree |
| So the `ci.yml` ignore suppressed | **nothing, ever** | *[measured]* CI runs `uv sync --frozen`, which installs no optional extra, so the advisory was never raised there |
| Extras CI audited before this chore | **none** — `runtime`, `azure`, `llm`, `forecaster` all unaudited | *[measured]* same: the fleet images install extras that `uv sync --frozen` does not |
| Vulnerable packages across the **whole lock** | **1** (`diskcache`) | *[measured]* `uv export --frozen --all-extras --all-groups` → 2,333 pins → `pip-audit --no-deps` |
| `optimizer` installed by any Dockerfile | **0 of 15** | *[measured]* the check itself, from `git ls-files *Dockerfile` |

🎯 **The ignore was never the load-bearing part.** The gate's *scope* was: it audited whichever
interpreter happened to be running, which locally carries a hand-installed `optimizer` extra and in
CI does not. Two commands that read identically were auditing different package sets.

## What shipped

1. **`scripts/check_dependency_audit.py` (128)** replaces the raw `pip-audit` step in both the
   `Makefile` and `ci.yml`. It exports the lock with **every extra and every group** and audits that,
   so local and CI answer the same question and the audited set is a superset of what any container
   installs.
2. **`scripts/dependency_audit_baseline.py` (50)** holds the accepted advisories — one entry today —
   each naming its package, aliases, deciding record, reason, retire trigger, and the sole optional
   extra that pulls it in. One source of truth instead of two command lines.
3. **`scripts/dependency_audit_rules.py` (143)** judges a report against those acceptances. It fails
   when **any** premise stops holding: a fix release appears, the advisory stops being reported, the
   advisory lands on a different package, or a Dockerfile starts installing the named extra.
4. **The acceptance is printed on every green run**, with its measured premises, so the gate output
   states what it tolerates and why. That is item 74's "only the Makefile comment knows", answered.
5. **Gate self-test** gains failure case `accepted-advisory-re-check` and invariants
   `dependency-audit-not-ignored-by-ci` / `dependency-audit-wired-in-ci`, the latter refusing an
   `--ignore-vuln` flag in either definition.
6. **Doc drift fixed in passing:** `CLAUDE.md` said the gate has 14 steps and listed 14 while the
   `ci:` target already ran 15 — it had missed S224's sprint-status step. The sprint template's
   "all 12 steps" is now "every step of the `ci:` target", so the number cannot rot again.

### The road not taken (LAW-06)

- **A calendar expiry on the acceptance.** Rejected: a date fires when nothing has changed, which
  re-creates the harm DL-184 refused — a permanently failing gate nobody reads — and is the shape of
  item 33's 57 unread warnings. The premises here are event-driven instead.
- **Keep `--ignore-vuln` and add a separate re-check.** Rejected: the list would then live in three
  places and the two command lines could still drift from the thing auditing them.
- **Keep auditing the installed environment.** Rejected: that set is whatever the developer last
  synced. It is the defect, not the baseline.
- **Audit runtime extras only.** Rejected: it would shrink today's coverage of the dev toolchain to
  buy nothing — the full lock is one audit either way.
- **Drop the `optimizer` extra.** Still rejected for DL-184's reason: DSPy was adopted by ADR-0010;
  removing it is a direction change, not a CVE response.

## Blast radius — measured 2026-09-22

| What | Detail |
| --- | --- |
| Files changed | 3 new scripts (128 / 143 / 50), 1 new test file (10 tests), `Makefile`, `ci.yml`, `gate_selftest_cases.py`, `pyproject.toml`, 5 docs |
| Agents affected | none — no package module touched |
| Contract change? | no |
| Graph vocabulary change? | no |
| New env keys / tunables | none |
| Deploy implication | **nothing to deploy** — gate tooling only |

**Law-cycle question — does this change `contracts/` or add a guarantee an agent makes?** **No.**
Nothing under `kernel`, `contracts`, `agents`, `orchestration` or `surfaces` is touched; the change
is entirely in `scripts/`, the gate definitions and docs. No clause is owed.

## Test plan results

| # | Test | Status | Proves |
| --- | --- | --- | --- |
| A1 | `test_a_shipped_fix_retires_the_acceptance` | PASS | a `fix_versions` entry fails the gate and names the baseline file |
| A2 | `test_an_advisory_that_stopped_being_reported_is_a_stale_acceptance` | PASS | an acceptance nothing reports any more fails as stale |
| A3 | `test_installing_the_extra_voids_the_unreachability_premise` | PASS | a Dockerfile installing `optimizer` fails and names the file |
| A4 | `test_an_unaccepted_vulnerability_fails_the_gate` | PASS | the original job still works — anything unaccepted is red |
| A5 | `test_an_accepted_advisory_passes_and_states_its_premises` | PASS | the green path prints ID, package, reach, decision and retire trigger |
| A6 | `test_an_acceptance_matches_its_advisory_by_alias` | PASS | a GHSA-keyed report still matches a PYSEC-keyed acceptance |
| A7 | `test_an_acceptance_answers_for_its_package_only` | PASS | 🪤 an acceptance cannot silently cover a different package |
| A8 | `test_pip_audit_reporting_one_advisory_twice_yields_one_finding` | PASS | 🪤 the duplicate record pip-audit really emits is one finding, not two |
| A9 | `test_every_shipped_acceptance_names_a_decision_and_a_retire_trigger` | PASS | no acceptance can ship without a decision record and a retire trigger |
| A10 | `test_the_cli_reads_a_recorded_report_and_reports_the_acceptance` | PASS | the CLI path, end to end, offline |

## Success factors

- [x] The gate audits the lock with every extra and group, not the running interpreter.
- [x] Every accepted advisory's premises are re-measured on each run, and a shipped fix fails it.
- [x] The accepted list has exactly one home, and an `--ignore-vuln` flag in either definition fails
      the gate self-test.
- [x] The acceptance and its reasoning appear in gate output, not only in a comment.
- [x] Every new module under 200 lines (128 / 143 / 50).
- [x] `make ci` exit 0, 100.00 % coverage.
- [x] Design decisions recorded with rejected alternatives — [DL-199](../design-log.md).
- [x] Law-cycle question answered **No**, with the reason above.

## Closeout — evidence

**Tree the proofs ran in:** `C:/Users/yury_/Downloads/project/ta-chore-74`, branch
`chore-an-accepted-advisory-re-checks-itself`, **no `.env`** — which is the point: the new check
needs none, and it still sees the advisory a bare `pip-audit` there cannot.

**Result:** the dependency gate now audits 2,333 locked packages across every extra and group, holds
its one accepted advisory in a file that states the premises behind it, re-measures those premises on
every run, and prints them. A fix release for `diskcache`, the advisory disappearing, or any
Dockerfile installing the `optimizer` extra each turn the gate red with the instruction attached.

**Guard planted, watched to fail, restored:** gate self-test case `accepted-advisory-re-check` plants
a report where `PYSEC-2026-2447` carries fix release `5.6.4` and requires a non-zero exit containing
`a fix has shipped`. It is not a one-off — it runs on every push.

**Proof — the guard failing on the planted violation:**

```text
PASS  can-fail: accepted-advisory-re-check - rejected (exit 1)

gate self-test: 28/28 passed
```

**Proof — the green run:**

```text
accepted: PYSEC-2026-2447 (diskcache 5.6.3) - reachable only via the 'optimizer' extra,
installed by 0 of 15 Dockerfiles; no fix release exists, nothing imports dspy, and the attack
needs write access to the cache directory - which is code execution already [DL-184] -
retire when diskcache publishes a fixed release, or the optimizer extra is dropped
No unaccepted vulnerabilities; 1 accepted advisory re-checked
```

**Module line counts:** `check_dependency_audit.py` **128**, `dependency_audit_rules.py` **143**,
`dependency_audit_baseline.py` **50**.

**`make ci`:** redirected to a file, not piped. Exit code **0**. `3048 passed, 6 skipped`, coverage
`100.00 %`. Dependency audit: `No unaccepted vulnerabilities; 1 accepted advisory re-checked`.
Both secret scans read `Passed`. 🪤 **The first run of this gate on this very file failed**, because
`detect-secrets` reads the phrase *"detect-secrets: Passed"* as a keyword assignment — the
[docs-push hazard](../work-queue.md) again, caught locally this time by the untracked-file sweep.

**`make gate-ran`:** run from `C:/Users/yury_/Downloads/project/ta-chore-74`, whose `HEAD` is
the commit being proven - the printed SHA was checked against `git rev-parse HEAD`:

```text
GATE PROVEN for cc314df0a2dd6f9f0af072131e0a696d3aa963ef:
  CI: success (attempt 1)
  CodeQL: success (attempt 1)
  Security Findings: success (attempt 1)
```

**Merged** `750ac98`, tagged `v0.107.00`, 2026-09-22 22:34 AEST. Nothing deployed: gate tooling
only, so the fleet stays on `b18014e`.

**Not met / verified failing:** none.

## Return notes

- **Scope grew once, deliberately.** Item 74 asked for a re-check. The re-check could not work in CI
  until the audit's scope changed, because CI could not see the advisory at all. Widening the scope
  was measured first and cost nothing: one vulnerable package across the entire lock.
- **The finding worth carrying:** a security step can read identically in two places and audit
  different things. The `Makefile`/`ci.yml` pairing was kept textually in sync by DL-184 and was
  still not the same check. Compare *what a step examines*, not what it says.
- **What this does not do:** it audits the lock, not the built images. A container that installs a
  package outside `uv sync` is still outside this gate.
