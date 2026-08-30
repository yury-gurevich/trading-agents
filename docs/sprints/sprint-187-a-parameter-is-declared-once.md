<!-- Agent: planning | Role: sprint handover -->
# Sprint 187 — A parameter is declared once

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-187-a-parameter-is-declared-once`
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** S (plus one law cycle)
**Decisions:** [DL-120](../design-log.md) the sweep whose headline was wrong and whose remainder this
closes · work-queue item 29 · ADR-0013 the mode-selector category

> **Why this bump kind.** **fix → PATCH.** Nothing new is offered. Three parameters are declared in
> one place and not the other, in both directions; this makes the two agree and adds the check that
> stops them diverging again.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/scanner/laws/laws.md` | **LOCKED v1.1** (amended S183) | Read-only for this sprint — the scanner's law row is **correct**; the code is wrong |
| `agents/provider/laws/laws.md` | **LOCKED v1 since S69** | 🚨 This sprint **amends it**. That is a law cycle, done deliberately, not a quiet edit |
| `agents/execution/laws/laws.md` | **LOCKED** | 🚨 This sprint **amends its PARAM table** too |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: every agent's **`PARAM`** table, and `docs/laws/conventions.md` on what the
`Tunable` column means.

### The rule

1. **Before writing code**, read the PARAM section of **all three** law files named above — whole
   sections, first time — plus `docs/laws/conventions.md`.
2. Read each agent's `test-plan.md` alongside its `laws.md`.
3. Read [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** For this sprint it is **Yes**.
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where a decision was needed, that silence is a finding → `drift-register.md`.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered: **YES**

This sprint adds PARAM rows to **two LOCKED law books** (provider and execution). Each amendment
needs its law version bumped, a Changelog line, and a drift row recording what was out of alignment
and why. 🪤 **PARAM rows are declarations, not clauses** — they do not add `test-plan.md` rows or move
the proven/declared rollup. Do not invent a clause just to have something to cite; if the rollup
moves, you have done something else as well and should say what.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/scanner/settings.py:53` `benchmark_ticker` | `agents/scanner/laws/laws.md` PARAM row (line ~228) | The law declares it **`YES`** (a tunable) and the code does not register it. **The law is right** — fix the code |
| `agents/provider/settings_feeds.py:64,93` | `agents/provider/laws/laws.md` PARAM table (**LOCKED v1**) | Two parameters exist in no law at all. Law cycle |
| `agents/execution/settings.py:123` `deliberation_grace_seconds` | `agents/execution/laws/laws.md` PARAM table | A registered `tunable()` with no PARAM row. Law cycle |
| the new `make ci` check | `docs/laws/conventions.md` | It encodes what the `Tunable` column means; it must not invent a stricter rule than the convention states |

⚠️ **The law is the authority, and it has already caught me out once here.** [DL-120](../design-log.md)'s
original headline claimed six bare settings were defects and that two agents had made *"the same
mistake"*. **That was backwards** — `stop_target_mode` and `order_price_tolerance_mode` are declared
`NO (mode selector)` in their locked laws, deliberately, citing ADR-0013. The audit had classified by
code shape and never opened `laws.md`. **Read the law row before calling anything a defect.**

---

## Goal

Every parameter is declared in exactly one authoritative place — its agent's PARAM table — and the
code agrees with that declaration. Where they disagree today, they stop disagreeing; and `make ci`
gains a check so the next divergence fails the gate instead of waiting for an audit.

## Why (context)

**The PARAM tables and the code have drifted apart in both directions, across three agents, with
nothing checking.** This is the surviving, verified remainder of DL-120's sweep after its headline
was retracted. It is not a style complaint: the PARAM table is what tells the operator which knobs
exist and which are deliberately not knobs, and a table that is wrong in either direction makes the
tuner's job guesswork.

🪤 **The most interesting instance is the one that proves it is systemic.** The scanner law and the
analyst law carry the *same* `benchmark_ticker` row, declared `YES` in both. The analyst honours it;
the scanner does not. One law row, two agents, one obeys.

### Measured, 2026-08-22 — read these before designing

| Instance | Direction | Status |
| --- | --- | --- |
| `scanner.benchmark_ticker` | law says `YES`, **code is a bare default** | *[measured]* `agents/scanner/laws/laws.md:228` declares `YES`; `agents/scanner/settings.py:53` reads `benchmark_ticker: str = "SPY"`. The analyst's identical row at `agents/analyst/laws/laws.md:254` **is** honoured — `agents/analyst/settings.py:93` calls `tunable(` |
| `provider.alpaca_data_feed` | **in no law at all** | *[measured]* `agents/provider/settings_feeds.py:93`, plain `Field(default="iex")`. Zero hits in `agents/provider/laws/laws.md` |
| `provider.ingest_ohlcv_only` | **in no law at all** | *[measured]* `agents/provider/settings_feeds.py:64`, plain `Field(default=False)`, cited to DL-29 in a code comment only |
| `execution.deliberation_grace_seconds` | **registered `tunable()`, no PARAM row** | *[measured]* `agents/execution/settings.py:123`. Surfaced while speccing [S185](sprint-185-the-veto-posture-is-declared-not-arithmetic.md) |
| `execution.stage` | — | 🚨 *[measured — **RETRACTED**]* work-queue item 29 carried this as *"unverified whether it belongs"*. **It is already there**, `agents/execution/laws/laws.md:326`, declared `NO (config)`. **Not a defect. Do not touch it.** |

🪤 **The provider law is LOCKED v1 since S69**, so its two missing rows were added post-lock. That
makes them a **law cycle**, not a code edit — the code is fine, the law never caught up.

---

## Scope — and what is deliberately NOT here

1. **`scanner.benchmark_ticker` becomes a real `tunable()`**, matching the law row that already
   declares it and the analyst that already honours it.
2. **The provider law gains PARAM rows** for `alpaca_data_feed` and `ingest_ohlcv_only`, with the
   right `Tunable` verdict for each — that verdict is a design decision, see below.
3. **The execution law gains a PARAM row** for `deliberation_grace_seconds`.
4. 🎯 **`make ci` gains a check** reconciling every PARAM row against its settings field, both ways.
   **This is the durable half of the sprint** — items 1–3 are today's instances, item 4 is why there
   is not a fifth.
5. **Drift rows** recording each divergence and its direction.
6. 🧹 **Optional rider, take it or decline it in the return notes.** `scripts/check_module_size.py:32`
   and `scripts/check_module_header.py:38` both skip paths containing `alembic/versions`. **That
   condition excludes nothing**: the migrations live at `infra/migrations/versions`, and neither
   checker scans `infra/` at all (`PKGS = kernel contracts agents orchestration surfaces`). It is
   left over from the Sprint-03 root-level `alembic/`, deleted 2026-08-22. It is harmless but it
   *reads* as "migrations are in scope and deliberately exempted", which is false. Deleting the two
   clauses is the honest fix — you are already in both files. **Do not instead point the checkers at
   `infra/migrations/versions`**: alembic-generated migrations do not carry `Agent:`/`Role:` headers
   by convention, so that would manufacture work rather than remove a lie.

### Out of scope (do NOT build this sprint)

- 🚨 **Do NOT touch `stop_target_mode`, `order_price_tolerance_mode`, or `curator.predictor_strategy`.**
  All three are declared `NO (mode selector)` / `NO (structural)` **on purpose**. DL-120's retracted
  headline called them defects; they are the convention working. **Registering any of them is a law
  violation.**
- **Do NOT touch `execution.stage`** — already declared, see the retraction above.
- **No value changes.** Every default stays exactly what it is today. This sprint changes *declarations
  and registration*, never a number.
- **No new parameters.**
- **No promotion of the check to cover clauses** — `check_law_coverage.py` already owns that.

### The road not taken (LAW-06)

- **Amend the scanner law to say `NO` instead of registering the tunable.** Rejected: the analyst
  honours the identical row, so the law is coherent and the scanner is the outlier. Changing the law
  to match the weaker implementation would be filing drift against a correct rule — exactly the
  mistake DL-120 made.
- **Ship items 1–3 and skip the check.** Rejected: this is the *second* audit to find this class
  (DL-120, then S185's spec work found a fourth instance unprompted). Without the check there will be
  a third audit.
- **Make the check a warning like assertion E.** Rejected as the *end state* — but see design
  decision 3, because it may have to start that way.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Is `provider.alpaca_data_feed` a tunable, a mode selector, or config?** It picks which vendor
   feed answers (`iex` vs others) — that smells like a **mode selector**, and ADR-0013's wording is
   the test: *a tunable is a value **within** a formula; a mode selector chooses **which formula
   runs***. Whatever you decide, the rationale column must say why.
2. **Is `provider.ingest_ohlcv_only` a tunable or config?** It switches enrichment off wholesale
   (DL-29 fast mode). Same test.
3. 🚨 **Does the new check start as a hard failure or a warning?** Run it across **all** agents before
   deciding — if it finds twenty more instances, a hard failure blocks the gate on work this sprint
   is not doing, and the honest move is warn-now with a named promotion trigger (the pattern assertion
   E already uses, work-queue item 10). **Measure first, then choose, and say which you chose and
   what the count was.**
4. **What exactly does the check compare?** Name presence in both directions is the floor. Whether it
   also compares the declared *type*, *bounds* or *default* against the code is a scope question —
   more value, more false positives. Decide and justify.

🪤 **Take the next free DL number, then re-check it at merge.** Highest as of 2026-08-30 is **DL-132** (S186 took it). 🚨 **Re-check every `file:line` in this spec before you start** — S186 merged on 2026-08-30 and its analyst law amendment shifted every analyst PARAM row by 3 (`laws.md:251` → **254**), which was corrected here but is exactly how these citations rot. 🚨 The log is **not** in numeric order — S185's DL-128 sits *above* DL-127 — and carries five historic duplicates, so scan every `^## DL-` heading and take max+1 rather than reading the end of the file.

---

## Blast radius — measured 2026-08-22

| What | Detail |
| --- | --- |
| Files changed | `agents/scanner/settings.py`, `agents/provider/laws/laws.md`, `agents/execution/laws/laws.md`, a new `scripts/check_*.py`, `Makefile`, `docs/laws/drift-register.md` |
| Agents affected | `scanner` (code), `provider` + `execution` (law only). 🪤 No agent imports another |
| Contract change? | **No** |
| Graph vocabulary change? | **No** |
| New env keys / tunables | `scanner.benchmark_ticker` becomes operator-settable — that is the point. 🪤 It gains an env key, which makes the deploy a **full `up`** rather than a retag |
| Deploy implication | **Full `up`.** Verify `ENV PRESERVATION` returns 16/16 |
| Behaviour change | **None intended.** Defaults are unchanged; only their declaration and settability change |
| 🚨 CI gate | The gate goes from 11 steps to **12**. Update every place that says "11 steps" — `CLAUDE.md`, `docs/`, and this template family |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Run the reconciliation across all agents first**, before writing any fix — the count decides
   design decision 3.
3. **Record the four design decisions** in `docs/design-log.md` with rejected alternatives.
4. **Plant the failing tests first** (A1–A5) and watch them fail. Paste the red output.
5. **Fix `scanner.benchmark_ticker`**; **amend the two law PARAM tables** (version bump + Changelog
   line each); **file the drift rows**.
6. **Add the check** and wire it into `make ci`.
7. **Prove the guards can fail (DL-70)** — revert the scanner registration, watch the check go red;
   delete a PARAM row, watch it go red the other way; restore both.
8. **`make ci` green** — now **12 steps**, **redirected to a file, never piped**.
9. **Fill the handback sections** and set **Status:** to `BUILT`.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 `scanner.benchmark_ticker` is a registered tunable with bounds and a `why` | — | it appears in the tunable registry exactly as the analyst's does |
| A2 | the check fails when a PARAM row has no settings field | a law row for a field that does not exist | red, and the message names the row |
| A3 | the check fails when a settings field has no PARAM row | a new bare field | red, and the message names the field |
| A4 | 🪤 the check does **not** fire on a declared mode selector | `stop_target_mode`, `order_price_tolerance_mode` | green. **These are correct and must stay correct** |
| A5 | the check does not fire on secrets or config-only rows | `alpaca_api_key`, `execution.stage` | green |

---

## Success factors

- [ ] `scanner.benchmark_ticker` is a `tunable()` with the same bounds/rationale shape as the analyst's.
- [ ] Provider law has PARAM rows for both fields; provider law version bumped + Changelog line.
- [ ] Execution law has a PARAM row for `deliberation_grace_seconds`; version bumped + Changelog line.
- [ ] `make ci` reconciles PARAM rows against settings fields, **both directions**.
- [ ] 🪤 The check is **green on all three declared mode selectors** (A4) — this is the one that
      proves it encodes the convention rather than a code-shape heuristic.
- [ ] **No default value changed anywhere.**
- [ ] `execution.stage` untouched.
- [ ] Drift rows filed for each divergence, naming its direction.
- [ ] Every reference to "11 steps" updated to 12.
- [ ] Design decisions recorded with rejected alternatives, before implementation.
- [ ] Every new guard planted, watched to fail, restored — stated per guard.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **Read the law row before calling anything a defect.** DL-120's headline was retracted for exactly
this. The audit classified by code shape and never opened `laws.md`.
🪤 **A mode selector is not a tunable.** `stop_target_mode`, `order_price_tolerance_mode` and
`curator.predictor_strategy` are deliberately not registered. Your check must know this, and A4 is
how you prove it does.
🪤 **`execution.stage` is already declared.** The queue said otherwise; the queue was stale.
🪤 **The provider law is LOCKED v1 since S69.** Amending it is a law cycle done on purpose, with a
version bump and a Changelog line — not a quiet edit.
🪤 **Measure the full reconciliation before choosing hard-fail.** A check that blocks the gate on
twenty pre-existing rows is a check that gets reverted.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` green, **100.00 % coverage floor**. **Never measure the gate through a pipe** — redirect
  to a file and read the file.
- Version bump of the kind named at the top (fix → PATCH), `uv.lock` staged with it.
- Secrets never through the worktree — a worktree has **no `.env`**. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving**, and **check the printed
   SHA against `git rev-parse HEAD`**.
2. Merge to `main` locally and push. 🪤 Check you are not on the branch already.
3. **Post-merge CodeQL** — runs only on `main` (work-queue item 31).
4. **Deploy is a full `up`** — `scanner.benchmark_ticker` gains an env key. `ENV PRESERVATION` 16/16.

---

## Handover — paste this to Codex

```text
Sprint 187 - a parameter is declared once.
Branch: sprint-187-a-parameter-is-declared-once (create it BEFORE any code, off main, never work on
main). Full spec: docs/sprints/sprint-187-a-parameter-is-declared-once.md - read it whole.

THE PROBLEM. Each agent's laws.md has a PARAM table declaring which settings exist and which are
tunable. The tables and the code have drifted apart in BOTH directions, across three agents, with
nothing checking. Verified 2026-08-22:
  (a) scanner.benchmark_ticker - the scanner law (laws.md:228) declares it YES (a tunable) and the
      code (settings.py:53) is a bare `benchmark_ticker: str = "SPY"`. The ANALYST carries the
      identical law row (analyst/laws.md:251) and DOES honour it (analyst/settings.py:93 calls
      tunable(). One law row, two agents, one obeys. The law is right - fix the scanner code.
  (b) provider.alpaca_data_feed and provider.ingest_ohlcv_only - plain Field(default=...) in
      agents/provider/settings_feeds.py:93 and :64, and they appear in NO law at all. The provider
      laws.md is LOCKED v1 since S69, so these were added post-lock. That is a LAW CYCLE, not a code
      edit - the code is fine, the law never caught up.
  (c) execution.deliberation_grace_seconds - a registered tunable() at settings.py:123 with NO PARAM
      row. Found while speccing S185.

ALREADY RETRACTED - DO NOT "FIX" THESE:
  - execution.stage is ALREADY in the execution PARAM table (laws.md:326, "NO (config)"). An older
    note called it unverified. It is verified and it is not a defect. Do not touch it.
  - stop_target_mode, order_price_tolerance_mode and curator.predictor_strategy are declared
    "NO (mode selector)" / "NO (structural)" ON PURPOSE, citing ADR-0013. DL-120's original headline
    called them defects and was RETRACTED - the audit had classified by code shape and never opened
    laws.md. Registering any of them is a LAW VIOLATION.

WHAT SHIPS.
  1. scanner.benchmark_ticker becomes a real tunable(), matching the law and the analyst.
  2. Provider law gains PARAM rows for both fields (law version bump + Changelog line).
  3. Execution law gains a PARAM row for deliberation_grace_seconds (same).
  4. THE DURABLE HALF: make ci gains a check reconciling every PARAM row against its settings field,
     BOTH DIRECTIONS. Items 1-3 are today's instances; item 4 is why there is not a fifth.
  5. Drift rows for each divergence, naming its direction.

READ THE LAWS FIRST - THIS IS A GATE, NOT ADVICE. Read the PARAM section of the scanner, provider
and execution laws.md whole, plus docs/laws/conventions.md (it defines what the Tunable column
means) and docs/laws/drift-register.md, BEFORE you open an editor. Fill the "Law reading record"
table at the bottom of the spec BEFORE your first code change. If a law contradicts the spec, STOP
and report - that has already happened once on this exact item.

THE LAW CYCLE IS IN SCOPE. You are amending TWO LOCKED law books (provider, execution). Each needs
its law version bumped and a Changelog line. NOTE: PARAM rows are DECLARATIONS, not clauses - they
do not add test-plan.md rows and must not move the proven/declared rollup. Do not invent a clause
just to have something to cite. If the rollup moves, you did something else - say what.

FOUR DESIGN DECISIONS - record in docs/design-log.md with rejected alternatives BEFORE coding:
  1. Is provider.alpaca_data_feed a tunable, a mode selector, or config? It picks which vendor feed
     answers. ADR-0013's test: a tunable is a value WITHIN a formula, a mode selector chooses WHICH
     formula runs.
  2. Is provider.ingest_ohlcv_only a tunable or config? It switches enrichment off wholesale (DL-29).
  3. Does the new check start as a HARD FAILURE or a WARNING? RUN THE FULL RECONCILIATION ACROSS ALL
     AGENTS FIRST. If it finds twenty more instances, hard-fail blocks the gate on work this sprint
     is not doing, and warn-now with a named promotion trigger is the honest move (the pattern
     assertion E already uses). Measure first, then choose, and report the count.
  4. What exactly does the check compare? Name presence both ways is the floor. Type, bounds and
     default comparison is more value and more false positives. Decide and justify.

TESTS - plant them first, watch them fail, paste the red output:
  A1 scanner.benchmark_ticker is a registered tunable with bounds and a why, like the analyst's.
  A2 the check fails when a PARAM row has no settings field (message names the row).
  A3 the check fails when a settings field has no PARAM row (message names the field).
  A4 THE IMPORTANT ONE: the check does NOT fire on stop_target_mode or order_price_tolerance_mode.
     This is how you prove it encodes the convention rather than a code-shape heuristic - which is
     precisely the mistake DL-120 made.
  A5 the check does not fire on secrets (alpaca_api_key) or config-only rows (execution.stage).

HARD LIMITS:
- NO DEFAULT VALUE CHANGES ANYWHERE. This sprint changes declarations and registration, never a
  number.
- No new parameters.
- Do not extend the check to law clauses - check_law_coverage.py already owns that.

ALSO: this takes make ci from 11 steps to 12. Update every place that says "11 steps" - CLAUDE.md
and docs/. And scanner.benchmark_ticker gaining an env key makes the deploy a full "up", not a
retag - note it in the closeout.

GATE: make ci, all 12 steps, exit 0, 100.00% coverage. Redirect to a FILE and read the file - never
pipe it, because make ci | tail reports tail's exit code, not make's. Then push and run make
gate-ran FROM THE WORKTREE whose HEAD is the commit you are proving; check the printed SHA against
git rev-parse HEAD. Do not merge - hand back.

HANDBACK: fill the Law reading record, the Test plan results table, Closeout - evidence (real pasted
output, red run first), and Return notes. Set Status: to BUILT. State anything not met plainly as
"verified failing" or "not done". An incomplete handback is returned, not repaired.
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

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *Pre-answered
YES. State the two law versions bumped, the Changelog lines, and the drift rows.*

**Full reconciliation count before choosing hard-fail vs warn:** *the number, per agent.*

**Contradictions found between a law and this spec:**

**Laws found silent where a decision was needed:**

**Clauses that were ⬜ and are now proven:** *Expected: none — PARAM rows are declarations, not clauses.*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | | | | |
| A2 | | | | |
| A3 | | | | |
| A4 | | | | |
| A5 | | | | |

**Tests added beyond the plan:**

---

## Closeout — evidence

<!-- FILL THIS IN BEFORE HANDING BACK. A handback with this placeholder intact is not accepted. -->

**Status:** *not yet implemented.*

**Tree the proofs ran in (and `.env` present?):**

**Result:** *not yet implemented.*

**Files changed:**

**Design decisions:** *the four above, as a DL entry with rejected alternatives.*

**Full reconciliation result:** *how many divergences across all agents, and hard-fail or warn.*

**Proof — the red run first:**

**Proof — the green run:**

**Guards planted:**

**Module line counts:**

**`make ci`:** *exit code (12 steps now), passed/skipped counts, coverage %.*

**`make gate-ran`:** *worktree path and full 40-char SHA.*

**Not met / verified failing:**

---

## Return notes

-
