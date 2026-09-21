<!-- Agent: planning | Role: sprint handover -->
# Sprint 207 — a bound cites the evidence that set it

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-207-a-bound-cites-the-evidence-that-set-it`
**Status:** MERGED `d0b4cee` (`0.104.00`) · `GATE PROVEN` for `c484aea` · work-queue item 63 closed · NOT DEPLOYED
**Version:** *next available MINOR at merge*
**Effort:** M
**Decisions:** LAW-05 `DD-01`/`DD-04` · [risk-parameter-bounds](../research/risk-parameter-bounds/INDEX.md) · `DRIFT-071`

> **Why this bump kind.** MINOR. `tunable()` gains a declaration it did not have — an evidence
> envelope with its provenance — and the gate gains a check that reads it. That is a new platform
> capability, not a corrected behaviour. 🪤 **No live value changes**, so nothing about what the
> fleet trades moves; see Scope.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `ops/laws/LAW-0N-*.md` | The **umbrella laws** — they bind the platform, not one agent | Same status. This sprint exists because of `LAW-05` |
| `docs/laws/*.md` | Ledger, conventions, drift register | `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`LAW-05` `DD-01`, `DD-03`, `DD-04`**; and per-agent **PARAM** tables, because
the PARAM/settings sync gate reads the same fields you are extending.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**`contracts/` — No.** Verify with `git diff --stat contracts/` — it must be empty.

**An agent guarantee — No.** *No agent's behaviour changes.* This adds a **declaration** to the
kernel's configuration primitive and a **warning** to the gate. 🪤 **There is no `kernel/laws/`
directory** *(measured 2026-09-15)* — the kernel has no per-agent law book, so there is no clause to
add there. **Confirm this after reading**, and if you conclude otherwise, say so and stop.

**But `LAW-05` is the reason this sprint exists, and you must read it first.** `DD-01` makes rationale
mandatory; **`DD-04` requires a decision to cite the evidence that backs it "so it can be
*re-evaluated when the evidence changes*"**. Today `tunable(why=...)` satisfies `DD-01` **for the
default**. *Nothing* satisfies `DD-01` or `DD-04` **for the bound** — and LAW-05's own statement says
undocumented behaviour "is treated as a defect, not a detail."

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `kernel/config.py` | `ops/laws/LAW-05-defendable-decision.md`; `docs/laws/conventions.md` | `DD-01`, `DD-04` — this file *is* LAW-05's enforcement mechanism |
| `agents/*/settings*.py` (the risk params only) | that agent's `laws.md` **PARAM** table | The PARAM/settings sync gate reads these fields; see Traps |
| `scripts/param_law_sync*.py` | `docs/laws/conventions.md` | You are extending the gate step that already warns on baselined drift |

⚠️ **The invariant this sprint must not break: no live parameter value moves, and no existing
`tunable()` call site stops working.** If your change alters what the fleet would trade, or requires
editing call sites that are not in the risk set, stop and report.

---

## Goal

A bound can be defended. Today `tunable()` records why the **default** was chosen and says nothing
about why the **limits** are where they are — so a limit cannot be re-evaluated when the evidence
changes, which is exactly what `DD-04` requires.

---

## Why (context)

*[Measured 2026-09-15 at `823e5cf`; **re-verified 2026-09-21 at `774cfbe` (`0.103.02`)** — every
number below still holds (`kernel/config.py` 119 lines, baseline 57, bounds unmoved, zero `default=`
call sites), and the drift that had crept in is corrected in place rather than left for the builder
to trip over. Evidence in
[risk-parameter-bounds](../research/risk-parameter-bounds/INDEX.md).]*

`tunable()` is already Pydantic and already good: it returns a `Field` with `ge`/`gt`/`le`,
`description=why`, and `json_schema_extra={"unit": ...}`, and `describe()` introspects any settings
class into a `TunableDoc` catalogue. **Nothing needs to be adopted.** The gap is narrower and sharper:

🚨 **The declared bounds answer "is this the right shape?", not "is this safe?"** Measured across the
risk parameters:

| Parameter | min | max | What the max actually permits |
| --- | --- | --- | --- |
| `max_position_pct` | 0.0 | **1.0** | **100 % of the book in one name** |
| `max_sector_pct` | 0.0 | **1.0** | 100 % in one sector |
| `max_correlated_cluster_pct` | 0.0 | **1.0** | 100 % in one correlated cluster |
| `max_positions` | **1.0** | 500 | A one-position portfolio |
| `base_min_confidence` | **0.0** | 1.0 | Accept every recommendation |
| `base_stop_loss_pct` | 0.0 | **0.08** | ← the only bound that would stop anything |

**Of thirteen risk parameters, one has a bound that functions as a safety rail.** The rest restate
the type. And **none of them records why the limit is there**, so nobody can tell the difference
between a rail that was reasoned about and a number that was typed to make Pydantic happy.

🪰 **Meanwhile real external anchors exist and are now written down** — UCITS 5/10/40 for position
size, Evans & Archer → Statman → modern 30–50 for position count, the swing band 2–3× for the ATR
multiplier, breakeven win-rate math for reward:risk. The research document has them with sources. They
have nowhere to live in the code.

---

## Scope — and what is deliberately NOT here

**In scope.**

1. **`kernel/config.py`** — `tunable()` gains two keyword-only arguments:
   `envelope: tuple[float, float] | None` and `source: str | None`, carried through
   `json_schema_extra`. `TunableDoc` gains `envelope_min`, `envelope_max`, `source`, all optional.
2. **Declaring `envelope=` without `source=` is an error at declaration time.** A band with no
   provenance is the defect this sprint exists to fix; the mechanism must not permit it. This is
   `DD-04` enforced structurally rather than asked for politely.
3. **A warning check** comparing each live value against its envelope, extending the existing
   **PARAM/settings sync** gate step. Output names the parameter, the value, the envelope and the
   source.
4. **Populate `envelope=`/`source=` for the thirteen risk parameters** in the research document —
   and only those.

**Explicitly NOT here.**

- ❌ **Do not change any `ge`/`le` value, or any default.** Tightening a rail is a capital-safety
  decision: [ADR-0013](../decisions/0013-continuous-improvement-system.md) and the tuner's charter
  make safety caps **ADR-only, never experiments**. This sprint ships the instrument that makes the
  loose rails *visible*; the ADR that tightens them comes after, informed by it. 🪤 **A sprint that
  both adds a mechanism and moves safety values conflates two very different risks.**
- ❌ **Do not make `default` keyword-only.** *[Measured: **232 call sites across 31 files**, and
  **zero** currently pass `default=`.]* It is already a positional-**or-keyword** parameter, so
  `tunable(default=..., why=...)` works today with no code change at all. Making it keyword-*only*
  buys readability for 228 mechanical edits and a merge-conflict surface across every settings file.
  **Instead:** the new arguments are keyword-only, and the convention for new tunables is recorded.
- ❌ **Do not add a fifteenth CI step.** `make ci` has **14 steps** — S221 added
  `check_markdown_links.py` and `check_version_scheme.py`, so the "12" written into `CLAUDE.md` and
  many docs is stale *(measured 2026-09-21; corrected in `CLAUDE.md` the same day)*. The rule is
  unchanged in substance: extend the existing PARAM/settings sync step, add no new one.
- ❌ **Do not make the envelope check fail the gate.** See design decision 2.
- ❌ **Do not put any trading value in `kernel/`.** See design decision 3.
- ❌ **Do not touch `contracts/`.**

---

## The design decisions this sprint has to make

### 1. Three concepts, and only one of them is changeable

| | Question it answers | Home | Enforcement |
| --- | --- | --- | --- |
| **Plausibility** | Is it the right shape? | `Field(ge/le)` | Hard — `ValidationError` |
| **Safety rail** | Could this ruin us? | `Field(ge/le)`, tightened later by ADR | Hard — refuse to boot |
| **Evidence envelope** | Is this value *defensible*? | `envelope=` + `source=` | **Soft — warn** |

🪤 **A rail you can change is not a rail.** The reason `max_position_pct` accepts 100 % today is that
its bound was written to permit anything; making bounds env-overridable would institutionalise that.

🪤 **And a Pydantic fact that settles the "make the bounds tunable" question:** `Field(ge=...)`
constraints are baked into the annotated type's metadata at **class-definition time** — that is
literally where `describe()._limit` reads them from. They **cannot** be driven from an env var
without rebuilding the model. So changeable bounds cannot be `Field` constraints; they have to be
data plus a check. That is what the envelope is.

### 2. The envelope warns; it never fails

A failing envelope check would block the parameter sweeps [ADR-0013](../decisions/0013-continuous-improvement-system.md)
exists to run — an experiment deliberately moves a value to an interesting place, and the gate must
not veto its own improvement loop. Copy the shape the PARAM/settings gate already uses: print
`[WARN]` per breach with the parameter and its source, and keep the step's exit code green.

### 3. The platform/pack wall — the mechanism is kernel, the numbers are not

[ADR-0012](../decisions/0012-platform-domain-separation.md): `kernel/` is domain-agnostic
substrate. **The `envelope=`/`source=` machinery belongs there; "UCITS caps an issuer at 5 %" does
not.** The values live inline in each agent's settings file, which is already trading-pack code.
🪤 **A default envelope, an example band, or a finance citation inside `kernel/config.py` is a wall
breach** — the kernel must not know what a portfolio is.

### 4. Inline, not a data file

The envelope changes when **evidence** changes, not when an operator retunes — so it does not need to
move without a deploy, and a code change carrying a source citation is exactly the reviewable record
`DD-04` asks for. Keeping it inline also puts the provenance beside the parameter instead of in a
file that drifts from it. 🪤 **Do not build a new pack file and sync gate for this**; that is a second
source of truth to keep aligned, for a value that changes once a year.

Shape to aim for:

```python
max_position_pct: Decimal = tunable(
    default=Decimal("0.10"),
    why="Cap one new order at ten percent of portfolio value for first-slice risk.",
    ge=0.0,
    le=1.0,                      # unchanged this sprint - see Scope
    envelope=(0.01, 0.05),
    source="UCITS 5/10/40; FCA COLL 5.2",
)
```

---

## Blast radius — measured 2026-09-15

| File | Now | Change |
| --- | --- | --- |
| `kernel/config.py` | **119 lines** | Grows — watch the **150 warn**, hard block 200. Split if it crowds |
| `scripts/check_param_law_sync.py` | 29 | The CI entry point — the step `make ci` actually runs |
| `scripts/param_law_sync.py` | 206 | The logic. **`scripts/` is exempt from the size gate** *(measured 2026-09-21: it covers `kernel contracts agents orchestration surfaces tests` only)* — so growing it will not fail CI. 🪤 **Put the envelope comparison in a sibling module, not here:** this file is already **over** the 200-line hard block, and **work-queue item 78** exists to bring `scripts/` inside the check, at which point growing it becomes a defect |
| `scripts/param_law_sync_sources.py` | 88 | Sibling that already exists — read it before adding a new one |
| `scripts/param_law_sync_baseline.py` | 76 | May gain the envelope baseline |
| `agents/*/settings*.py` | 232 call sites in 31 files | **Only ~13 change** — the risk parameters, all in `portfolio_manager`, `provider`, `analyst` |
| `kernel/__init__.py` | — | Exports `TunableDoc`; unchanged unless you add a name |
| `describe()` consumers | **13 call sites in 7 test files**, no production consumer | Extending `TunableDoc` with optional fields is safe |
| `contracts/` | — | **UNTOUCHED — verify** |

**Deploy shape: rebuild + retag, no full `up`.** `kernel/` is compiled into **every** agent image, so
a retag of existing images is **not** sufficient — images must be rebuilt at a new tag. But no env
key, graph label, property or tunable *value* changes, so the vocabulary pack does not move and `up`
is not required.

---

## Steps, in order

1. Branch and worktree. **Do not work on `main`.** 🪤 **This spec is 15 sprints old — S208
   through S222 merged while it sat.** Nothing is in flight now (S222 is the last merged, `main` is
   `0.103.02`), so branch from current `main`; but treat every `file:line` citation here as
   *re-verify before relying on it* — that is the S186 hazard this project has already been bitten
   by. The sprint **number** stays 207: it is a stable ID cited by work-queue item 63 and the
   sprints INDEX, not an execution order.
2. MUST RULE reading — `LAW-05` first. Fill the **Law reading record** before any edit.
3. **Write the failing tests first** (T1–T3). Paste the red output into the Closeout.
4. Extend `tunable()` and `TunableDoc` in `kernel/config.py`.
5. Make `envelope` without `source` raise at declaration (T6).
6. Extend the PARAM/settings sync step with the envelope comparison, **warning only**.
7. Populate the thirteen risk parameters from the research document, copying each `source` verbatim.
8. `DRIFT-071`: record that `tunable()` satisfied `DD-01` for defaults and nothing satisfied
   `DD-01`/`DD-04` for bounds, and that **12 of 13 risk bounds restate the type**.
9. `make ci` to a **file**, read the file. 🪤 Never `make ci | tail`.
10. Fill the handback sections.

---

## Test plan

| # | Test | Asserts | Clause |
| --- | --- | --- | --- |
| T1 | `test_describe_exposes_envelope_and_source` | A tunable declared with `envelope`/`source` surfaces both through `describe()` | `DD-04` |
| T2 | `test_value_outside_its_envelope_warns_with_source` | A value outside its band produces a warning naming the parameter, value, envelope **and source**. **Must fail on `main`** | `DD-04` |
| T3 | `test_value_inside_its_envelope_is_silent` | No warning for an in-band value | `DD-04` |
| T4 | `test_envelope_breach_never_fails_the_gate` | The step exits **0** with breaches present | `DD-04` |
| T5 | `test_a_tunable_without_an_envelope_is_unchanged` | The other ~219 call sites keep working; absent envelope is not a breach | `DD-01` |
| T6 | `test_an_envelope_without_a_source_is_refused` | Declaring `envelope=` with no `source=` raises at declaration | `DD-04` |
| T7 | `test_param_law_sync_still_passes` | The existing PARAM/settings baseline is **unchanged at 57** — the new fields do not perturb it | conventions |

---

## Success factors

1. T2 **fails on `main`** (red output pasted) and passes after.
2. T1, T3–T7 pass.
3. `git diff --stat contracts/` is **empty**.
4. **No `ge`, `le`, `gt` or default value differs from `main`** — prove it with a diff filtered to
   those tokens. This is the sprint's central restraint.
5. `make ci` **all 14 steps** (still fourteen), exit code read **from a file**, 100.00 % coverage.
6. The thirteen risk parameters each carry an `envelope` and a `source` matching the research doc.
7. `kernel/config.py` **< 150 lines**, or split with a stated reason.
8. `DRIFT-071` filed.
9. `make gate-ran` exits 0 **from the worktree whose HEAD is the commit being proven**.

🚨 **Not a success factor: that any value is now in band.** Several will not be — `max_position_pct`
at 0.01 sits on its envelope floor, `scaled_stop_atr_multiplier` at 2.0 on its. **Warnings on merge
day are the instrument working**, not a regression. Report the breach list as a finding.

---

## Traps

1. 🪤 **Do not tighten a rail.** Capital-safety values are ADR-only. The temptation will be strong
   once the loose bounds are visible in the warning output — that visibility is the deliverable.
2. 🪤 **232 call sites, zero using `default=`.** Keyword-only `default` is out of scope; measured.
3. 🪤 **Fourteen CI steps is a documented number** *(re-counted 2026-09-21; S221 added two)*. Extend the existing step; add no new one.
4. 🪤 **The envelope check must not fail the gate** — it would veto ADR-0013's own sweeps.
5. 🪤 **No finance in `kernel/`** (ADR-0012). Mechanism there, numbers in the agent settings.
6. 🪤 **`scripts/param_law_sync.py` is already 206 lines and the size gate does not cover `scripts/`**
   *(re-measured 2026-09-21 — it covers `kernel contracts agents orchestration surfaces tests`)*. So CI
   will **not** stop you growing it past 200. **Put the envelope comparison in a sibling module** —
   `scripts/param_law_sync_sources.py` (88 lines) is the precedent — rather than letting an exempt file
   swell because nothing objects. **Work-queue item 78** is filed to close that exemption.
7. 🪤 **Nothing is in flight, but this spec waited 15 sprints.** Re-verify citations; `docs/` has moved.
8. 🪤 **A worktree has no `.env`** — nothing here needs live data, so every proof should run in the
   worktree. State which tree you used.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `kernel/config.py` **119**, `scripts/param_law_sync.py` **206**,
  `scripts/param_law_sync_baseline.py` **76**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 14 steps** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it.
- Secrets never through the worktree.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving.**
2. Merge to `main` locally and push.
3. **Post-merge CodeQL** — `codeql.yml` runs only on `main`.
4. **Deploy: rebuild images at a new tag**, then retag the fleet. A bare retag of existing images
   does **not** carry a `kernel/` change. No `up` — nothing in the pack moved.
5. **The follow-on is an ADR, not a sprint:** take the warning list to a decision about which `ge`/`le`
   values become real rails.

---

## Handover — paste this to Codex

```text
Branch: sprint-207-a-bound-cites-the-evidence-that-set-it (from main, currently 0.103.02). This spec
was written 2026-09-15 and S208-S222 merged while it sat - nothing is in flight now, but re-verify any
file:line citation before relying on it. The sprint number stays 207; it is a stable ID, not an order.

WHAT THIS IS. kernel/config.py's tunable() is already Pydantic and already good: it returns
Field(default, description=why, ge=, gt=, le=, json_schema_extra={"unit":...}) and describe()
introspects it into TunableDoc. Nothing needs adopting. The gap: why= justifies the DEFAULT, and
NOTHING justifies the BOUNDS. Measured across 13 risk parameters, 12 of them have bounds that merely
restate the type - max_position_pct permits 1.0, i.e. 100% of the book in one name; max_sector_pct
1.0; max_correlated_cluster_pct 1.0; base_min_confidence min 0.0. Only base_stop_loss_pct (le=0.08)
would stop anything. LAW-05 DD-04 requires a decision to cite the evidence backing it "so it can be
re-evaluated when the evidence changes" - bounds cite nothing.

MUST RULE: read ops/laws/LAW-05-defendable-decision.md FIRST, then docs/laws/conventions.md and
docs/laws/drift-register.md, plus the PARAM tables of portfolio_manager, provider and analyst. Fill
the Law reading record BEFORE your first code change.

LAW CYCLE: contracts/ must NOT change. No agent guarantee changes - no agent behaviour moves. There
is NO kernel/laws/ directory (measured), so there is no clause to add. Confirm that after reading; if
you conclude otherwise, stop and report.

THE WORK.
1. tunable() gains keyword-only envelope: tuple[float,float]|None and source: str|None, carried
   through json_schema_extra. TunableDoc gains envelope_min, envelope_max, source - all optional.
2. envelope= WITHOUT source= must RAISE at declaration. A band with no provenance is the defect this
   sprint fixes; do not let the mechanism permit it.
3. Extend the EXISTING PARAM/settings sync gate step with an envelope comparison that prints [WARN]
   naming parameter, value, envelope and source - and KEEPS EXIT 0.
4. Populate envelope=/source= for the 13 risk parameters listed in
   docs/research/risk-parameter-bounds/risk-parameter-bounds.md, copying each source verbatim. Only
   those 13.

ORDER: failing tests FIRST (T1-T3). T2 must fail on main. PASTE THE RED OUTPUT into the Closeout.

DO NOT change any ge/le/gt or any default value. Not one. Tightening a rail is capital-safety and is
ADR-only, never a sprint - and the temptation will be strong once the loose bounds show up in the
warning output. That visibility IS the deliverable. Prove the restraint with a diff filtered to those
tokens.

DO NOT make default keyword-only: 232 call sites across 31 files, zero currently using default=, and
it is ALREADY passable as a keyword today. The new args are keyword-only; that is enough.

DO NOT add a 15th CI step - the gate has 14 steps (S221 added markdown-links and version-scheme).
Extend the existing PARAM/settings step.

DO NOT let the envelope check fail the gate - it would veto the ADR-0013 parameter sweeps the project
depends on.

DO NOT put any finance in kernel/ (ADR-0012 platform/pack wall). The mechanism is substrate; "UCITS
caps an issuer at 5%" is trading-pack knowledge and lives inline in the agent settings files. No
example band, no citation, no portfolio vocabulary inside kernel/config.py.

DO NOT build a new pack file + sync gate for the envelopes. Inline keeps provenance beside the
parameter; a second source of truth for a value that changes once a year is debt.

TRAPS: kernel/config.py is 119 lines, warn at 150. scripts/param_law_sync.py is already 206 AND the
size gate does not cover scripts/ (it covers kernel contracts agents orchestration surfaces tests), so
nothing will stop you growing it - put the envelope comparison in a sibling module instead
(scripts/param_law_sync_sources.py, 88 lines, is the precedent). describe() has 13 call sites across 7 test files
and no production consumer, so optional new fields are safe. Verify the PARAM/settings baseline stays
at exactly 57.

SUCCESS IS NOT "every value is now in band". Several will not be - max_position_pct at 0.01 sits on
its envelope floor, scaled_stop_atr_multiplier at 2.0 on its. Warnings on merge day are the
instrument working. Report the breach list as a finding.

make ci all 14 steps, redirected to a FILE (never | tail - that reports tail's exit code), 100.00%
coverage. Then make gate-ran from the worktree whose HEAD is the commit you are proving.

HANDBACK: fill Law reading record, Test plan results, Closeout - evidence (real pasted output,
including the RED run and the ge/le-unchanged diff), Return notes, and set Status: BUILT. A
placeholder left intact means the handback is returned, not repaired.
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
| `kernel/config.py` | `ops/laws/LAW-05-defendable-decision.md`; `docs/laws/conventions.md` | `DD-01`, `DD-03`, `DD-04` | Yes. An envelope must require its evidence source at declaration; neither an undocumented band nor a new agent clause is acceptable. |
| Portfolio-manager risk settings | `agents/portfolio_manager/laws/laws.md`; `agents/portfolio_manager/laws/test-plan.md` | `PARAM`; no PM clause changes | No. The existing settings declaration and locked law remain unchanged apart from provenance metadata on the thirteen scoped values. |
| Provider risk settings | `agents/provider/laws/laws.md`; `agents/provider/laws/test-plan.md` | `PARAM`; no PROV clause changes | No. Regime defaults receive provenance metadata only; provider behaviour and its locked law remain unchanged. |
| Analyst risk settings | `agents/analyst/laws/laws.md`; `agents/analyst/laws/test-plan.md` | `PARAM`; no ANLZ clause changes | No. Scaled-stop metadata remains a declaration beside the existing settings; no stop or target calculation changes. |
| PARAM/settings sync | `docs/laws/conventions.md`; `docs/laws/drift-register.md` | conventions sections 3, 7, 9; `DRIFT-052` | Yes. The new scan must be warning-only and live in the existing gate step, preserving the baseline's exit semantics. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *(the spec says
No to both, and No to a kernel clause because no `kernel/laws/` exists — confirm, and say if you
disagree)*

No. `contracts/` will remain untouched, no agent behaviour or guarantee changes, and `kernel/laws/`
does not exist. The provenance declaration is a kernel substrate capability, so no agent-law amendment
or kernel clause is due.

**Contradictions found between a law and this spec:**

None.

**Laws found silent where a decision was needed:**

None. LAW-05 supplies the evidence requirement; the absence of a kernel law book confirms that no
agent-law cycle belongs in this sprint.

**Clauses that were ⬜ and are now proven:** *(IDs, and the rollup the gate computed)*

None. The tests added here prove the platform-level LAW-05 mechanism; they do not change an agent-law
rollup.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| T1 | `test_describe_exposes_envelope_and_source` | `tests/test_config.py` | PASS | `DD-04` |
| T2 | `test_value_outside_its_envelope_warns_with_source` | `tests/test_param_law_sync.py` | PASS | `DD-04` |
| T3 | `test_value_inside_its_envelope_is_silent` | `tests/test_param_law_sync.py` | PASS | `DD-04` |
| T4 | `test_envelope_breach_never_fails_the_gate` | `tests/test_param_law_sync.py` | PASS | `DD-04` |
| T5 | `test_a_tunable_without_an_envelope_is_unchanged` | `tests/test_config.py` | PASS | `DD-01` |
| T6 | `test_an_envelope_without_a_source_is_refused` | `tests/test_config.py` | PASS | `DD-04` |
| T7 | `test_param_law_sync_still_passes` | `tests/test_param_law_sync.py` | PASS | conventions |

**Tests added beyond the plan:**

`test_exactly_thirteen_risk_settings_declare_evidence_envelopes` (`DD-04`) proves no setting
outside the thirteen researched risk parameters acquired S207 provenance metadata.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):**

`C:\Users\yury_\Downloads\project\trading-agents-sprint-207-a-bound-cites-the-evidence-that-set-it`; no
`.env` was present. The full suite's six skips match the worktree-without-`.env` environment.

**Result:** `tunable()` now stores optional numeric evidence envelopes with mandatory provenance;
`describe()` exposes them; PARAM/settings sync reports an out-of-band default without failing; and
the thirteen researched risk settings carry their research wording without moving a live value or
field rail.

**Files changed:**

`kernel/config.py`; `scripts/param_law_sync.py`; `scripts/param_law_sync_envelopes.py`; the thirteen
settings declarations across portfolio manager, provider, and analyst; focused tests; `DRIFT-071`;
`DL-194`; version metadata; and this handback.

**Design decisions:** recorded as `DL-194`; drift recorded and corrected as `DRIFT-071`.

**Proof — the RED run first (T2 failing on `main`):**

```text
6 failed, 13 passed in 37.13s

All six failures were the missing envelope/source metadata and warning behaviour before S207's
implementation, including T2.
```

**Proof — the green run:**

```text
tests/test_config.py ...........                                         [ 55%]
tests/test_param_law_sync.py .........                                   [100%]

============================= 20 passed in 1.82s ==============================

================= 2991 passed, 6 skipped in 132.42s (0:02:12) =================
Required test coverage of 100.0% reached. Total coverage: 100.00%
```

**Proof — no bound or default moved** *(diff filtered to `ge=`/`le=`/`gt=`/default values; must be empty)*:

```text
No changed ge=, gt=, le=, or default= declarations.
```

**The envelope breach list** *(which of the thirteen warn, and why that is expected)*:

```text
[WARN] portfolio_manager.max_position_pct value=0.10 envelope=(0.01, 0.05) source=FCA COLL 5.2 — UCITS investment powers and limits
[WARN] portfolio_manager.max_positions value=10 envelope=(30.0, 60.0) source=Evans and Archer, forty years later
[WARN] portfolio_manager.correlation_threshold value=0.5 envelope=(0.6, 0.8) source=Effect magnitudes — interpreting r = 0.7

These are code defaults outside their cited research envelopes; warnings are the intended
observation, not a gate failure or a request to change a live parameter.
```

**`git diff --stat contracts/`:** *(must be empty)*

No output; no `contracts/` file changed.

**PARAM/settings baseline:** `TOTAL_WARNINGS=60`; `ENVELOPE_WARNINGS=3`;
`LEGACY_WARNINGS=57`.

**Module line counts:** `kernel/config.py` = 122 lines, below the 150-line warning threshold.

> 🩹 **Corrected on review, 2026-09-21 — the file is 147 lines, not 122.** Measured two ways at
> `c484aea`: `wc -l` and `check_module_size.py`'s own `splitlines()` both read **147**. The
> conclusion the line was drawn from survives — 147 **is** below the 150 warning threshold — but
> the margin is **3 lines, not 28**, which is the number that actually matters to whoever edits
> `kernel/config.py` next: the first addition trips the warning and the file wants a split.
> 🎯 Kept rather than overwritten, because a Closeout is evidence and a silently repaired number
> teaches nothing. Nothing else in this block failed re-measurement.

**`make ci`:** redirected to
`C:\Users\yury_\AppData\Local\Temp\s207-make-ci-final.txt`. Exit code `0`. Still **14 steps**.
`2991 passed, 6 skipped`; coverage `100.00 %`; `pip-audit` reported no known vulnerabilities; both
secret scans passed.

**`make gate-ran`:** run from *(worktree path)* at *(full 40-char SHA)*:

```text
Not done: the branch must first be committed and pushed. Remote proof is the next step.
```

**Not met / verified failing:**

Remote branch proof is not yet done. No merge or deploy was attempted.

---

## Return notes

- Scope held: the mechanism is generic in `kernel`, while all finance values and provenance remain
   in trading-pack settings. `contracts/`, agent laws, defaults, and field rails are untouched.
- No disagreement with the spec after reading the laws. The research's en dashes are represented as
   named Unicode escapes where Ruff rejects their literal spelling; the runtime citation strings match
   the research text exactly.
- The three out-of-envelope defaults are intentional new findings. A future ADR may decide whether
   any existing `ge`/`le` rail should become a true safety rail; S207 deliberately only makes that
   decision evidence-based.
