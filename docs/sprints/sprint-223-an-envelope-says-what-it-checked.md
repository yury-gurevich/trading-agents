<!-- Agent: planning | Role: sprint handover -->
# Sprint 223 — an envelope says which value it checked, and cannot name a value its own rails reject

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-223-an-envelope-says-what-it-checked`
**Status:** MERGED — `b18014e7` on `main` (fix(s223): an envelope names the value it checked and cannot exceed it) (item 22 review, 2026-09-23); the line read: BUILT
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** DL-196 (this sprint's fork) · [DL-195](../design-log.md) (the three breaches, filed on the S207 merge) · work-queue item **79**

> **Why this bump kind.** No new capability. S207 already promised that a declared band carries its
> provenance and that a value outside it is reported; the check reports the wrong value and two bands
> name values Pydantic rejects. Fixing what an existing promise already covers is a **PATCH**.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/portfolio_manager/laws/laws.md` | The PM's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/portfolio_manager/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/conventions.md`, `docs/laws/drift-register.md` | Umbrella laws and conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`PM-OBS-03`** (what the correlation gate must disclose) and the PM's
**PARAMETERS** table, which already carries `correlation_threshold = 0.50` as the ramp floor.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the PM's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Planner's answer: No, and the spec is scoped to keep it No.** Nothing under `contracts/` is
touched. No agent gains a guarantee: the PM's PARAM row for `correlation_threshold` already reads
`0.50` and already calls it the ramp floor, so this sprint changes only the *evidence metadata*
beside that value — the `envelope` and `source` kwargs — and never the value itself. The new
declaration-time rule binds `kernel.tunable()`, which is tooling, not an agent guarantee.

**If your reading disagrees, stop and report** — do not open a law cycle on your own initiative,
and do not edit `laws.md` to make the spec fit.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/portfolio_manager/settings.py` (envelope/source metadata only) | `agents/portfolio_manager/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `PM-OBS-03` governs what the correlation gate discloses; the PARAMETERS table is the law-side mirror of these fields |
| `kernel/config.py` (`tunable()`) | `docs/laws/conventions.md` | Every agent's settings import this; a declaration-time raise here is a **process-start** failure everywhere |
| `scripts/param_law_sync_envelopes.py` | `docs/laws/conventions.md` | Tooling; no agent law binds it, but its output is read as evidence |

⚠️ **The one invariant this sprint must not break: no live value moves.** If your change alters any
`tunable()` *default*, or any value the fleet runs, you have left the sprint. Stop and report.

---

## Goal

At merge, the envelope check can no longer be read as a statement about production. Every warning
line names the **scope** of the value it read (the declared default), so nobody can mistake it for
the value the fleet trades on. `kernel.tunable()` refuses at declaration any `envelope` that extends
past its own `ge`/`le` rails, so a band can no longer name a value Pydantic would reject. And
`correlation_threshold`'s band cites the evidence for the parameter it *now* bounds — a ramp floor,
per [ADR-0030](../decisions/0030-the-correlation-gate-is-a-ramp-not-a-cliff.md) — instead of the
cutoff-era source it still carries, so the one **live** breach clears on its merits rather than by
being ignored.

## Why (context)

S207 shipped the envelope check on 2026-09-21 and it produced exactly three breaches on its first
run. **Two of the three are false alarms about values the fleet does not use**, because
`envelope_warnings` reads `info.get_default()`. The narrowing was disclosed in `STATE.md`, so it is
a stated deviation, not a silent one — and CI genuinely cannot read live values, because it has no
`.env`, which is the very property the gate is trusted for. What is left unowned is the other half:
**the two values the fleet actually trades on are checked by nothing**, and the warning line gives a
reader no way to tell which kind of number they are looking at.

The third breach is live, and this morning's run made it concrete. `sched-2026-09-21` was the first
scheduled run governed by the deployed ramp, and its gate detail carries
`correlation_ramp=0.5000..0.9000` with `correlated_issuers=XOM:0.6235:w0.3087` — a partial
contribution the old cliff scored as zero. So `0.50` is not a guess: it is the floor of a shape
ADR-0030 decided four days ago and production has now exercised. Its envelope still reads
`(0.6, 0.8)` with the source *"Effect magnitudes — interpreting r = 0.7"*, which was written when
that parameter was a **cutoff**. The number changed meaning and its evidence did not follow.

🚨 **Why now rather than later.** An unanswered breach becomes a permanent `[WARN]`. That is item
**33**'s 57-warning shape reproducing inside the instrument built to prevent it — three warnings
nobody acts on teach the reader to skip the section, and the next real breach arrives into a habit
of not looking.

### Measured, 2026-09-22 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| `check_param_law_sync.py` exit code, unpiped | **0** | *[measured 2026-09-22]* redirected to a file from the main checkout, exit code read from the redirect, not a pipe |
| Total `[WARN]` lines | **60** | *[measured 2026-09-22]* `grep -c` on that output |
| Of which envelope breaches | **3** | *[measured 2026-09-22]* `grep 'envelope='` — `max_position_pct` 0.10, `max_positions` 10, `correlation_threshold` 0.5 |
| Legacy PARAM/settings baseline | **57** | *[measured 2026-09-22]* 60 − 3; matches item 33's `LEGACY_BASELINE`, unchanged since 2026-09-15 |
| Live `PORTFOLIO_MANAGER_MAX_POSITION_PCT` | **0.01** | *[measured 2026-09-22]* `az containerapp show -g trading-agents -n portfolio-manager`, read-only |
| Live `PORTFOLIO_MANAGER_MAX_POSITIONS` | **60** | *[measured 2026-09-22]* same command |
| Live `PORTFOLIO_MANAGER_CORRELATION_THRESHOLD` | **0.50** | *[measured 2026-09-22]* same command |
| 🎯 Both "false alarm" live values are **inside** their own envelopes | 0.01 ∈ (0.01, 0.05); 60 ∈ (30, 60) | *[measured 2026-09-22]* live values above against the declared bands in `settings.py` |
| Envelopes declared repo-wide | **13** | *[corrected 2026-09-22]* `describe()` swept over every `*Settings` class in the analyst, PM and provider settings modules. The spec-time **16** was never produced by this sweep; **13** has been pinned since S207 by `test_exactly_thirteen_risk_settings_declare_evidence_envelopes` (`tests/test_config.py`) |
| Of which extend past their own rails | **2** | *[measured 2026-09-22]* same sweep: `correlation_lookback_days` `(60, 252)` vs `le=250`; `min_correlation_bars` `(13, 60)` vs `ge=20` — **both in the PM, both named by item 79** |
| `kernel/config.py` line count | **147** | *[measured 2026-09-22]* `wc -l` — **3 lines below the 150 warning**, which S207's review already corrected once |
| `agents/portfolio_manager/settings.py` line count | **165** | *[measured 2026-09-22]* `wc -l` — already past the 150 warning |
| ADR-0030's measured range for the floor | cutoffs **0.50, 0.60 and 0.70 all give 0 rejections** over 17 runs / 38 approvals | *[measured, EXP-008, quoted in ADR-0030's comparison table]* |

---

## Scope — and what is deliberately NOT here

1. **🎯 The warning line names what it read.** `envelope_warnings` emits the scope of the value, so a
   reader cannot take a default for a live setting. The current line is
   `[WARN] portfolio_manager.max_position_pct value=0.10 envelope=(0.01, 0.05) source=…`; after this
   sprint it distinguishes the declared default explicitly. The wording is yours — `default=0.10`
   plus a scope word, or an explicit "declared default" phrase — but **a test asserts it**, never an
   eyeball.
2. **🪤 A band cannot name a value its rails reject.** `kernel.tunable()` raises at declaration when
   `envelope[0]` is below `ge`/`gt` or `envelope[1]` is above `le`. The message names the field, the
   band and the rail it breaks.
3. **The two rails breaches are corrected** so every one of the 13 declared envelopes passes the new
   rule: `correlation_lookback_days` `(60, 252)` → a band inside `ge=20, le=250`;
   `min_correlation_bars` `(13, 60)` → a band inside `ge=20, le=250`. **Correct the band, never the
   rail** — the rails are the safety limits and are not this sprint's business.
4. **`correlation_threshold`'s band and source are re-derived for a ramp floor.** Planner's
   recommendation, which you may argue with in Return notes: envelope `(0.50, 0.70)` with a source
   citing ADR-0030 / EXP-008 — the range EXP-008 swept and measured indistinguishable (0 rejections
   at 0.50, 0.60 and 0.70 over 17 runs and 38 approvals). This clears the live breach **on
   evidence**, not by deleting the check.
5. **The envelope-breach count drops from 3 to 2 and the legacy baseline stays exactly 57.** Both
   numbers are asserted by a test, because "the warnings went away" is the failure mode here.

### Out of scope (do NOT build this sprint)

- **Making the check read live values.** CI has no `.env` — that is the property the gate is trusted
  for, not a defect to route around. Reading live values needs a different runner (deploy-time, or
  the master's fleet preflight), and that is its own sprint.
- **Aligning the two PM defaults to the live values** (`max_position_pct` 0.10 → 0.01,
  `max_positions` 10 → 60). This would make default equal live and both warnings would vanish
  honestly — **but changing a risk default changes what an unconfigured deployment risks, which is
  the operator's call, not a builder's.** Named here, recorded in the design log, left for them.
- **Any change to a `tunable()` default, or to any live value.** See the ⚠️ invariant.
- **Item 33's 57 legacy divergences.** Adjacent, separately ranked, and untouched here.
- **No `laws.md` edit** — the law-cycle question is answered No above.
- **No ADR.** ADR-0030 already decided the floor; this sprint makes an envelope catch up to it. An
  ADR is reversed by a new ADR, never by a sprint.

### The road not taken (LAW-06)

- **Drop `correlation_threshold`'s envelope entirely.** Rejected: S207's whole point is that a bound
  records why it is there. Deleting the band to silence the warning is the check failing in the
  direction it was built to prevent.
- **Widen the band to `(0.5, 0.8)` so it swallows the value.** Rejected: that is fitting the evidence
  to the number. The band must be derived from what EXP-008 actually measured for a *floor*.
- **Make the rails/envelope rule a `make ci` warning rather than a declaration-time raise.**
  Rejected: a band naming a value Pydantic rejects is incoherent at birth, not drift that
  accumulates — and a warning would join the 60 lines nobody reads. 🪤 But see the trap: a raise has
  a blast radius a warning does not.
- **Put the new rule inside `kernel/config.py`.** Rejected on a measured constraint: the file is
  **147** lines against a 150-line warning, so the rule needs its own small module (or a split), and
  S207's review already had to correct a wrong line count on this exact file.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` as `DL-196` with their rejected alternatives BEFORE
implementing (LAW-06).** 🪤 Take the next free DL number and **re-check it at merge** — the log has
historic duplicates and entries are prepended *and* appended, so a branch cut before another DL lands
collides even when the number was free at branch time.

1. **The wording that makes scope unmistakable.** `default=` alone is terse; "declared default" is
   explicit but long. Whatever you choose, a reader who has never seen this spec must not be able to
   read the line as a live value — and a test asserts the chosen wording.
2. **Where the rails rule lives**, given `kernel/config.py` is 147 against a 150 warning. A new
   `kernel/` module, or a split of `config.py`. Say which and why.
3. **The floor's band.** The planner recommends `(0.50, 0.70)` per ADR-0030 / EXP-008. If your
   reading of EXP-008 supports a different band, say so and name the table row you read it from.

---

## Blast radius — measured 2026-09-22

| What | Detail |
| --- | --- |
| Files changed | `kernel/config.py` (**147**), a new small `kernel/` module, `scripts/param_law_sync_envelopes.py` (**37**), `agents/portfolio_manager/settings.py` (**165**, metadata only), plus tests |
| Agents affected | portfolio_manager only, and only its envelope/source metadata. No agent imports another |
| Contract change? | **No** — nothing under `contracts/` |
| Graph vocabulary change? | **No** |
| New env keys / tunables | **None** — no `tunable()` is added, removed, or has its default moved |
| Deploy implication | **No deploy.** No runtime value changes. 🪤 `kernel/` compiles into every image, so *if* a deploy were ever wanted for this it is a **rebuild + retag**, never a retag — but nothing here changes what the fleet trades |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md` as `DL-196`.
3. **Plant the failing tests first** and watch them fail. Paste the red output.
4. **Implement.**
5. **Law cycle:** not owed — state the answer and why in the Law reading record.
6. **Prove the guards can fail (DL-70)** — break each new guard, watch it go red, restore, and say so
   per guard.
7. **`make ci` green** — all **14** steps, **redirected to a file, never piped**. 🪤 `make ci | tail`
   reports *`tail`'s* exit code; a real failure reads as green.
8. **Fill the handback sections** at the bottom of this file and set **Status:** to `BUILT`.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 A warning line names the scope of the value it read | A settings class with a default outside its envelope | The emitted line identifies the value as the **declared default**, asserted on the string |
| A2 | 🪤 An envelope extending below `ge` is refused at declaration | `tunable(50, why=…, ge=20, le=250, envelope=(13.0, 60.0), source=…)` | `ValueError` at declaration, message naming the band and the rail it breaks |
| A3 | 🪤 An envelope extending above `le` is refused at declaration | `tunable(120, why=…, ge=20, le=250, envelope=(60.0, 252.0), source=…)` | Same, for the upper rail |
| A4 | 🪤 The negative control — a valid band is still accepted | An envelope strictly inside its rails, **and** one exactly equal to them | No raise. **A rule that rejects valid bands is worse than the defect** |
| A5 | 🪤 A band with no rails at all is still accepted | `tunable(…, envelope=(1.0, 2.0), source=…)` with no `ge`/`le` | No raise — absent rails are not a violated rail |
| A6 | 🎯 Every real declared envelope passes the new rule | `describe()` swept over the analyst, PM and provider settings classes | **13** envelopes inspected, **0** rails breaches (was **2**) |
| A7 | 🎯 `correlation_threshold` is inside its re-derived band and cites the right evidence | The real PM settings class | `0.50` within the declared envelope, and the `source` references ADR-0030 / EXP-008 rather than the r = 0.7 effect-magnitude note |
| A8 | 🪤 The counts move exactly as intended, and no further | The real `check_param_law_sync` run | Envelope breaches **3 → 2**; legacy baseline **still exactly 57**; total `[WARN]` **60 → 59**; exit code still **0** |

---

## Success factors

- [ ] A reader of any `[WARN]` envelope line can tell it is a declared default, proven by A1 asserting the string.
- [ ] `kernel.tunable()` raises for an envelope outside its rails (A2, A3) and does **not** raise for a valid one (A4, A5).
- [ ] All **13** declared envelopes pass the new rule; the two PM bands are corrected, and **no rail was moved** (A6).
- [ ] `correlation_threshold` `0.50` sits inside a band sourced to ADR-0030 / EXP-008 (A7).
- [ ] Envelope breaches **3 → 2**, legacy baseline **still 57**, checker exit still **0** (A8).
- [ ] **No `tunable()` default changed and no live value moved** — state this explicitly, having checked.
- [ ] Design decisions recorded as `DL-196` with rejected alternatives.
- [ ] Law cycle answered **No**, with the reason, in the Law reading record.
- [ ] Every new guard planted, watched to fail, restored — stated per guard.
- [ ] Every touched module under 200 lines; `kernel/config.py` stated with its final count against the 150 warning.
- [ ] `make ci` exit 0 (redirected, not piped), 100.00 % coverage.

---

## Traps

🪤 **A declaration-time raise is a process-start failure, everywhere.** Every agent imports its
settings at import time, so a band this rule rejects does not fail a test — it fails the container.
This is safe **only because it was measured**: exactly **2** of **13** declared envelopes breach
today, both in the PM, and both are fixed in this sprint. **Before you merge, re-run the sweep** — if
a new envelope landed on `main` meanwhile, it must be fixed here or the rule waits.

🪤 **The warnings disappearing is not success.** Two of the three breaches must **still be there**
after this sprint: they are honest warnings about declared defaults that really are outside their
bands — the fix is that the line now says so, not that it goes quiet. If your run shows 0 envelope
breaches, you have changed a default and left the sprint. A8 exists to catch exactly this.

🪤 **`correlation_threshold` is live and production exercised it this morning.** Do not touch the
value. The only things moving are its `envelope` and `source` kwargs.

🪤 **Correct the band, never the rail.** `le=250` and `ge=20` are the safety limits an operator
override cannot cross. Widening a rail to make a band fit inverts the whole point.

🪤 **`kernel/config.py` is 147 lines against a 150 warning.** S207's closeout claimed 122 and both
`wc -l` and the gate read 147; the margin is 3 lines, not 28. Measure it yourself before you add a
line to that file.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module under 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `kernel/config.py` **147**, `agents/portfolio_manager/settings.py` **165**,
  `scripts/param_law_sync_envelopes.py` **37**, `scripts/check_param_law_sync.py` **29**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 14 steps** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — redirect to a file and read the file.
- Version bump of the kind named at the top (**PATCH**), `uv.lock` staged with it.
- Secrets never through the worktree — a worktree has **no `.env`**, so any proof needing live data
  is vacuous there. **State which tree you ran in.** Every check in this test plan is offline and
  runs fine in a worktree; the live Azure values in the Measured table were read planner-side and you
  are not expected to reproduce them.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving** — it resolves the SHA
   from the working directory and ignores a `SHA=` argument. **Check the printed SHA against
   `git rev-parse HEAD`.**
2. Merge to `main` locally and push. 🪤 Check you are not on the branch already — a `git merge` from
   the branch's own worktree says *"Already up to date"* and merges nothing.
3. **No deploy.** Nothing here changes what the fleet trades.
4. Close work-queue item **79** with the measured before/after counts, and note in the row that the
   live-value half moved to its own item rather than being silently dropped.

---

## Handover — paste this to the coding agent

```text
Branch `sprint-223-an-envelope-says-what-it-checked` off latest main, in a worktree. Never commit
to main.

READ FIRST, before any code: agents/portfolio_manager/laws/laws.md and laws/test-plan.md,
docs/laws/conventions.md, docs/laws/drift-register.md, and
docs/decisions/0030-the-correlation-gate-is-a-ramp-not-a-cliff.md. Then fill the "Law reading
record" section of docs/sprints/sprint-223-an-envelope-says-what-it-checked.md BEFORE your first
code change. laws.md is LOCKED: read-only. If a law contradicts the spec, STOP and report.

LAW CYCLE: not owed. You change nothing in contracts/ and no agent gains a guarantee. If you
believe otherwise, stop and report - do not edit laws.md.

THE JOB, three parts:
(1) scripts/param_law_sync_envelopes.py emits warning lines that must name the SCOPE of the value
    it read. It reads info.get_default(), and today the line says only "value=0.10" - which a
    reader takes for the value the fleet runs. The fleet actually runs 0.01. Make the line say it
    is the declared default. A test asserts the string.
(2) kernel.tunable() must RAISE at declaration when an envelope extends past its own ge/gt/le
    rails. kernel/config.py is 147 lines against a 150-line warning, so put the rule in its own
    small kernel module or split config.py - say which and why in the design log.
(3) Fix the two bands that breach today, in agents/portfolio_manager/settings.py:
      correlation_lookback_days  envelope=(60.0, 252.0)  against le=250
      min_correlation_bars       envelope=(13.0, 60.0)   against ge=20
    CORRECT THE BAND, NEVER THE RAIL. The rails are safety limits.
    Also re-derive correlation_threshold: it is 0.50, its envelope says (0.6, 0.8), and its source
    still cites "Effect magnitudes - interpreting r = 0.7" from when that parameter was a CUTOFF.
    ADR-0030 turned it into a ramp FLOOR four days ago. Recommended: envelope (0.50, 0.70), source
    citing ADR-0030 / EXP-008 (cutoffs 0.50, 0.60 and 0.70 all produced 0 rejections over 17 runs
    and 38 approvals). Argue in Return notes if you read EXP-008 differently.

DO NOT:
- Do not change any tunable() DEFAULT, or any live value. correlation_threshold=0.50 is live and a
  production run exercised it this morning. Only its envelope and source kwargs move.
- Do not widen a ge/le rail to make a band fit.
- Do not make the check read live values. CI has no .env and that is deliberate.
- Do not touch the 57 legacy PARAM/settings divergences (work-queue item 33).
- Do not change the two PM defaults to match the fleet (0.01 / 60). That is an operator decision
  and it is explicitly out of scope.

TRAPS, named so you do not hit them:
- A declaration-time raise fails CONTAINER STARTUP, not just a test. Exactly 2 of 13 declared
  envelopes breach today (both in the PM, both above). Re-run the sweep before merging in case a
  new envelope landed on main meanwhile.
- The warnings going to zero is FAILURE, not success. Two breaches (max_position_pct default 0.10,
  max_positions default 10) must STILL warn afterwards - they are honest warnings about declared
  defaults. Only correlation_threshold's should clear, and only because its evidence now matches
  its meaning. Expected after: envelope breaches 3 -> 2, total [WARN] 60 -> 59, legacy baseline
  still exactly 57, checker exit still 0.
- A rule that rejects VALID bands is worse than the defect. Test the negative control: a band
  inside its rails, a band exactly equal to its rails, and a band with no rails at all must all be
  accepted.
- Measuring the gate through a pipe reports the pipe's exit code. Redirect to a file and read the
  file. All 14 steps.

ORDER: plant the failing tests and paste the RED output before implementing. Then implement, then
break each new guard, watch it go red, restore it, and say so per guard.

Version: next available PATCH at merge - do not pin a number. No deploy.

Fill the handback sections at the bottom of the spec (Law reading record, Test plan results,
Closeout - evidence, Return notes) with real pasted output and set Status: BUILT. A handback with a
placeholder left intact is returned, not repaired.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| PM envelope/source metadata in `agents/portfolio_manager/settings.py` | `agents/portfolio_manager/laws/laws.md`; `agents/portfolio_manager/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md`; ADR-0030 | `PM-NEV-08` defines `correlation_threshold` as the ramp floor; `PM-OBS-03` requires disclosed ramp evidence; the PM PARAMETERS row already declares `0.50` as that floor. The cited PM-NEV-08 / PM-OBS-03 ramp proofs are 🟩. | Yes. It confirms that `(0.50, 0.70)` updates stale evidence for an existing ramp-floor meaning; it does not change an agent guarantee or require a law cycle. |
| `kernel.tunable()` envelope-rail validation | `docs/laws/conventions.md`; `docs/laws/drift-register.md` | No agent clause binds kernel declaration validation. Conventions §§4, 7, and 9 require locked laws to remain untouched and genuine law drift to be recorded. | No. The rule is declaration integrity tooling, not an agent behaviour guarantee; it must stay outside `contracts/` and `laws.md`. |
| Envelope warning scope in `scripts/param_law_sync_envelopes.py` | `docs/laws/conventions.md`; `docs/laws/drift-register.md` | No agent clause binds the offline checker; DRIFT-071 records S207's evidence-envelope purpose and its warning-only semantics. | Yes. The checker must explicitly name `FieldInfo.get_default()`'s declared-default scope, while remaining offline and warning-only. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No. It changes no file under `contracts/`; PM defaults and live values remain unchanged; the PM law already declares `correlation_threshold=0.50` as the ramp floor. The kernel rail check prevents incoherent declarations but adds no agent guarantee.

**Contradictions found between a law and this spec:** None. The specification's recommended threshold band follows ADR-0030's existing ramp-floor decision and the PM law's current wording.

**Laws found silent where a decision was needed:** None. The wording, validation-module placement, and evidence band are implementation decisions governed by the sprint and ADR-0030, not missing agent-law guarantees.

**Clauses that were ⬜ and are now proven:** None. This sprint changes no agent behaviour and does not claim a law proof transition.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_value_outside_its_envelope_names_its_declared_default` | `tests/test_param_law_sync.py` | PASS | DD-04; tooling, no agent-law clause |
| A2 | `test_envelope_below_inclusive_lower_rail_is_refused` | `tests/test_tunable_envelopes.py` | PASS | DD-04; tooling, no agent-law clause |
| A3 | `test_envelope_above_upper_rail_is_refused` | `tests/test_tunable_envelopes.py` | PASS | DD-04; tooling, no agent-law clause |
| A4 | `test_valid_and_unrailed_envelopes_are_accepted` | `tests/test_tunable_envelopes.py` | PASS | DD-04; tooling, no agent-law clause |
| A5 | `test_valid_and_unrailed_envelopes_are_accepted` | `tests/test_tunable_envelopes.py` | PASS | DD-04; tooling, no agent-law clause |
| A6 | `test_all_declared_envelopes_stay_inside_their_rails` | `tests/test_tunable_envelopes.py` | PASS for all 13 actual declarations; the plan's 16-count premise is verified false | DD-04; tooling, no agent-law clause |
| A7 | `test_correlation_threshold_envelope_cites_the_ramp_evidence` | `tests/test_tunable_envelopes.py` | PASS | DD-04; tooling, no agent-law clause |
| A8 | `test_param_law_sync_keeps_the_expected_warning_baseline` | `tests/test_param_law_sync.py` | PASS | Conventions §9 / DRIFT-071; tooling, no agent-law clause |

**Tests added beyond the plan:** `test_envelope_below_exclusive_lower_rail_is_refused` in
`tests/test_tunable_envelopes.py` proves the required `gt` boundary: an envelope that includes the
exclusive lower rail is refused at declaration.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):**
`C:\Users\yury_\Downloads\project\trading-agents-sprint-223-an-envelope-says-what-it-checked`; `.env` present: `False`.

**Result:** `make ci` exit `0`; 2,997 passed, 6 skipped, 100.00% coverage. The offline checker
exits `0` with 2 honest envelope warnings and the unchanged 57-warning legacy baseline. No default,
live value, or field rail changed.

**Files changed:** `kernel/tunable_envelope.py`, `kernel/config.py`,
`scripts/param_law_sync_envelopes.py`, `agents/portfolio_manager/settings.py`,
`tests/test_tunable_envelopes.py`, `tests/test_param_law_sync.py`,
`docs/design-log.md`, this sprint handback, `pyproject.toml`, and `uv.lock`.

**Design decisions:** recorded as `DL-196` — `declared_default=...` names the checked scope; a
dedicated kernel helper keeps `config.py` at 148 lines; `(0.50, 0.70)` cites ADR-0030 / EXP-008.

**Proof — the red run first:**

```text
uv run pytest tests/test_config.py tests/test_param_law_sync.py -q
FAILED tests/test_config.py::test_envelope_below_inclusive_lower_rail_is_refused
   Failed: DID NOT RAISE ValueError
FAILED tests/test_config.py::test_envelope_below_exclusive_lower_rail_is_refused
   Failed: DID NOT RAISE ValueError
FAILED tests/test_config.py::test_envelope_above_upper_rail_is_refused
   Failed: DID NOT RAISE ValueError
FAILED tests/test_config.py::test_all_declared_envelopes_stay_inside_their_rails
   AssertionError: assert 13 == 16
FAILED tests/test_config.py::test_correlation_threshold_envelope_cites_the_ramp_evidence
   assert (0.6, 0.8) == (0.5, 0.7)
FAILED tests/test_param_law_sync.py::test_value_outside_its_envelope_names_its_declared_default
   AssertionError: declared_default output expected, value output received
FAILED tests/test_param_law_sync.py::test_param_law_sync_keeps_the_expected_warning_baseline
   AssertionError: assert 3 == 2
7 failed, 19 passed in 35.30s
```

📌 **Path note, added at merge review.** The red run above cites
`tests/test_config.py` because the six new tests were written there first; they were moved
into `tests/test_tunable_envelopes.py` before the green run, and `tests/test_config.py` is
**unmodified** by this sprint. The paste is left verbatim rather than rewritten — the test
names and failures are the ones that ran.

**Proof — the green run:**

```text
uv run pytest --no-cov tests/test_config.py tests/test_tunable_envelopes.py tests/test_param_law_sync.py -q
26 passed in 1.82s

make ci > C:\Users\yury_\AppData\Local\Temp\s223-make-ci-green.txt 2>&1
ci_exit=0
2997 passed, 6 skipped in 117.52s
Required test coverage of 100.0% reached. Total coverage: 100.00%
No known vulnerabilities found
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 2 new file(s)
```

**The four counts, before and after:**

```text
before: envelope breaches=3, total [WARN]=60, legacy baseline=57, checker exit=0
after:  envelope breaches=2, total [WARN]=59, legacy baseline=57, checker exit=0
```

**Guards planted:** `ge`, `gt`, and `le` branches were disabled together: their three direct tests
failed `DID NOT RAISE`, then passed `3 passed` after restoration. The warning was changed back to
`value=`: A1 failed against `declared_default=`, then passed after restoration. The threshold source
was changed back to the old effect-magnitude text: A7 failed because `ADR-0030` was absent, then
passed after restoration. The threshold band was changed back to `(0.6, 0.8)`: A8 failed `3 == 2`,
then passed after restoration.

**Module line counts:** `kernel/config.py=148`, `kernel/tunable_envelope.py=33`,
`scripts/param_law_sync_envelopes.py=37`, `agents/portfolio_manager/settings.py=168`,
`tests/test_config.py=162`, `tests/test_tunable_envelopes.py=112`, and
`tests/test_param_law_sync.py=187`.

**`make ci`:** redirected to `C:\Users\yury_\AppData\Local\Temp\s223-make-ci-green.txt`. Exit
code `0`. `2997` passed, `6` skipped, coverage `100.00%`. pip-audit: no known vulnerabilities.
detect-secrets and untracked-secret scans: passed.

**`make gate-ran`:** not run. The branch is uncommitted and unpushed, so no remote SHA exists to
prove:

```text
not run — commit and push the sprint branch, then run from this worktree and compare its printed SHA to HEAD.
```

**Not met / verified failing:** The handover's stated 16-envelope count is verified false: the
settings sweep finds 13 (3 analyst, 8 PM, 2 provider), matching S207's existing declaration test.
All 13 pass the new rail rule; no three envelopes were invented merely to satisfy the stale premise.
`make gate-ran` is not done because this handback has not been committed or pushed.

---

## Return notes

- Scope held. No file under `contracts/` changed; no agent law changed; no default, live value, or
   `ge`/`gt`/`le` rail changed; no live settings were read; the 57 legacy PARAM/settings divergences
   remain untouched. Package version advanced one PATCH to `0.104.01`; no deploy is owed.
- The laws agree with the sprint's ramp-floor reading. EXP-008 supports `(0.50, 0.70)`: all three
   cutoffs in that range produced zero rejections over 17 runs and 38 approvals, and ADR-0030 makes
   `0.50` the floor. No different band is warranted.
- The only disagreement is factual, not architectural: there are 13 declared envelopes, not 16.
   The checked count is now pinned to the actual declarations; adding three new bands was rejected
   as scope expansion. Live-value validation remains a separate deployment-side concern, as CI must
   stay independent of `.env`.
