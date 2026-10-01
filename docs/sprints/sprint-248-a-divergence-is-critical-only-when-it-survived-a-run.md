<!-- Agent: planning | Role: sprint handover -->
# Sprint 248 — a broker divergence is flagged critical only when it survived a run, however often that ticker has diverged before

**Phase:** Etalon-first continuous improvement (DL-19) · work-queue 100 (live defect)
**Branch:** `sprint-248-a-divergence-is-critical-only-when-it-survived-a-run`
**Status:** MERGED 2026-10-01 — `0.120.02`, fast-forwarded to `09699ad0`, tag `v0.120.02`, GATE PROVEN `09699ad0` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (3,775 passed, 8 skipped, 100.00 %); built by a Claude cloud session on `claude/upbeat-fermi-wva7zm` (cut from `main` `f1192239`); **F1 PASS** (the 53 live subjects replayed in memory through the merged code: first sighting 53 `warn` and 0 `critical`, the next run 53 `critical`, all gone 0 open, a new episode 53 `warn`; 0 of 224 copied nodes rewritten); A10 met with a one-argument edit to the sweep test, accepted (DL-254 D6); DRIFT-094 opened and filed as work-queue 102; **not deployed — the fleet runs `s246`**; owed: the image-only retag, then F2
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** [DL-253](../design-log.md) (the defect, measured, and the direction) · the builder's
decisions go to the **next free DL** (`DL-254` at spec time) · opens **DRIFT-093**

> **Why this bump kind.** No new capability. S178 built "severity follows persistence, not first
> sight", and the code does that only the first time a ticker diverges. This makes it do it every time.

*(Sprint 247 is reserved by S246's spec for the readings scorer, so this one is 248.)*

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/execution/laws/laws.md` | The execution agent's **locked constitution**, v1.9 | **LOCKED.** This sprint amends it by one clause, named below, and nothing else |
| `agents/execution/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`STA`**, **`OBS`**, **`TRG`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read `agents/execution/laws/test-plan.md` alongside `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Read the law-cycle answer below.** It is already decided: this sprint owes a clause.
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered here: **YES**

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

`contracts/` is untouched. But the guarantee this sprint repairs is **in no clause**. *[measured
2026-10-01]* The five tests in `agents/execution/tests/test_reconciliation_flags.py` cite
`EXEC-TRG-07`, and `EXEC-TRG-07` (`laws.md:63`) says only that run-start reconciliation writes exactly
one `BrokerPositionSnapshot`. It says nothing about flags or their severity. S178 shipped the
behaviour under a locked book without declaring it.

So this sprint owes a **law cycle in the same unit of work**:

- A new clause **`EXEC-OBS-07`** (the next free `OBS` id; IDs are append-only). It must say, in your
  wording: a broker-position divergence is flagged **per episode**; an episode opens with a `warn`
  Flag at the run-start reconciliation that first sees the divergence; it becomes `critical` only when
  the same divergence is still present at the next run-start reconciliation; it closes, by an appended
  `FlagResolution`, when the divergence is gone; a divergence seen again after its episode closed opens
  a **new** episode at `warn`, whatever that ticker's history; and a live divergence always has exactly
  one unresolved Flag.
- `laws.md` version **v1.9 → v1.10** with a Changelog line that names the *why* (DL-253).
- `test-plan.md` rows for the clause, the clause ID in each test docstring.
- The severity tests that cite `EXEC-TRG-07` today are re-cited to `EXEC-OBS-07`. The snapshot test
  (`test_run_start_reconciliation_records_an_agreeing_book_without_flags`) keeps `EXEC-TRG-07`.
- The rollup in **both** `docs/laws/ledger.md` **and** `docs/laws/INDEX.md` (37 / 63 today).
  🪤 The rollup is derived: `make ci` recomputes it. Let the gate tell you the number.
- **DRIFT-093** in `docs/laws/drift-register.md`: the law was silent and the code drifted from what
  S178 intended.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/execution/reconciliation_flags.py` | `agents/execution/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `EXEC-STA-03` every graph write is append-only; `EXEC-TRG-07` the snapshot is written first and nothing alongside it may prevent it; new `EXEC-OBS-07` |
| `agents/execution/tests/test_reconciliation_flags*.py` | same | clause IDs in docstrings (conventions §3) |
| `agents/execution/laws/laws.md`, `test-plan.md` | `docs/laws/conventions.md`, `docs/laws/_TEMPLATE.md` (read, do not edit) | IDs append-only; version and Changelog |

⚠️ **No existing `Flag` or `FlagResolution` node is ever rewritten or deleted (`EXEC-STA-03`).** If your
change would write to a key that already exists, stop: that is the trap this defect lives in (see
Traps).

---

## Goal

At merge, `record_divergences` treats each occurrence of a divergence as its own episode. The first
run-start reconciliation that sees it writes a `warn`. Only a divergence still present at the next
run-start reconciliation becomes `critical`. A ticker that diverged and was adopted last month starts
again at `warn` this month, and a divergence that really persists is flagged `critical` no matter how
many times that ticker has diverged before.

## Why (context)

On `sched-2026-09-30` the broker no longer held MDLZ and the graph still did. That is ordinary: a
position left the book between runs, and reconciliation retires it in the same run. The run wrote a
`critical` Flag, "Divergence survived a full run without adoption", for a divergence it was seeing for
the first time, and resolved it seven minutes later. The same happened for BAC on `sched-2026-09-29`.

The cause is at `agents/execution/reconciliation_flags.py:48`. It asks whether a `warn` Flag **exists**
for the subject, not whether one is open. Flags are append-only and keyed
`flag:{subject_ref}:{severity}`, and the subject is `broker-position-divergence:{kind}:{ticker}` with no
episode in it, so each key can be used once per ticker, for ever.

The second half is worse than a false alarm. Once a ticker has used both its `warn` and its `critical`
key, lines 48–53 write nothing, and `_resolve` returns `False` because the resolution already exists.
A divergence on that ticker that really does persist raises **no flag at all**. The operator's bar
(2026-08-20) is that the evidence discipline catches its own defects unattended; this is a check that
cries wolf on some tickers and has gone blind on others.

### Measured, 2026-10-01 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| A second episode's first sighting is `critical` | yes | *[measured, no `.env`]* the reproduction below, on `InMemoryGraphStore` |
| A third episode writes no flag, even after surviving two runs | yes | *[measured, no `.env`]* same reproduction |
| Live subjects in the run-stable format | **53** | *[measured, Neon]* `Flag` nodes whose `subject_ref` starts `broker-position-divergence:` and not `…:broker-position-snapshot:` |
| Of those, with a spent `warn` only | **40** | *[measured, Neon]* their next divergence is `critical` on sight |
| Of those, with both keys spent | **12** | *[measured, Neon]* AMD, BAC, DOW, MDLZ, USB (extra); AMZN, CSCO, DOW, INTC, MDLZ, USB, XOM (missing): their next divergence writes nothing |
| Divergence Flags, and unresolved ones | **112**, **0** | *[measured, Neon]* every one has a `FlagResolution` |
| `critical` divergence Flags written since 09-01 | **10** | *[measured, Neon]* 3 checked (MDLZ extra 09-30, BAC extra 09-29, MDLZ missing 09-21): all 3 were first sightings with a `warn` spent weeks earlier. The other 7 were not checked |
| MDLZ on `sched-2026-09-30` | `critical` 22:32:22 UTC, resolved 22:39 | *[measured, Neon]* reason "divergence no longer present"; the `warn` key was spent on 09-08 |
| Books after that run | 34 / 34 positions, 34 / 34 stops, 0 failures | *[measured]* `scripts/audit_broker_graph.py` |
| Readers join a resolution to a flag on the props `(subject_ref, severity)` | 2 readers | *[measured, read]* `agents/supervisor/domain/health.py:46` and `:90`; `surfaces/queries/flags.py:39` and `:61` |
| ~~Writing to an existing key rewrites the node~~ **Wrong — corrected at merge.** It raises: the `ON CONFLICT … DO UPDATE` carries a `WHERE NOT EXISTS` that skips the update when an incoming prop differs, and `_raise_merge_conflict` then raises `property '…' cannot be overwritten` (`kernel/graph_postgres.py:99`); the in-memory store does the same. The planner read line 21 of the SQL and not the guard under it; measured by the builder (DL-254) | ~~yes~~ no | ~~*[measured, read]*~~ *[was a misreading]* `kernel/graph_postgres_queries.py:21`, `ON CONFLICT (label, key) DO UPDATE` |
| No reader parses the kind or ticker out of `subject_ref` | 0 | *[measured]* a search of `agents kernel contracts orchestration surfaces scripts` for the prefix and both kind names finds only `reconciliation_store.py`, `reconciliation_flags.py`, the sweep script and tests |
| The false `critical` set `healthy=false` for those seven minutes | unknown | *[ASSUMED — not measured]* `compute_health` counts unresolved `critical` Flags, so it would if a report was computed in that window. No report was located. Nothing in this sprint depends on it |

**The reproduction** (run from the repo root, no `.env`):

```python
from agents.execution.reconciliation_flags import record_divergences
from agents.execution.reconciliation_store import Divergence
from kernel import InMemoryGraphStore

MDLZ = Divergence("extra_graph_position", "MDLZ", "graph_qty=16")
g = InMemoryGraphStore()


def snap(key):
    return g.merge_node("BrokerPositionSnapshot", key, {"holding_count": 0})


def state(label):
    res = {(n.props["subject_ref"], n.props["severity"]) for n in g.list_nodes("FlagResolution")}
    flags = g.list_nodes("Flag")
    open_ = sorted(
        n.props["severity"] for n in flags if (n.props["subject_ref"], n.props["severity"]) not in res
    )
    print(f"{label:32s} flags={len(flags)} resolutions={len(res)} unresolved={open_}")


record_divergences(g, snapshot=snap("s1"), divergences=(MDLZ,)); state("episode 1, first sight")
record_divergences(g, snapshot=snap("s2"), divergences=()); state("episode 1, gone")
record_divergences(g, snapshot=snap("s3"), divergences=(MDLZ,)); state("episode 2, FIRST sight")
record_divergences(g, snapshot=snap("s4"), divergences=()); state("episode 2, gone")
record_divergences(g, snapshot=snap("s5"), divergences=(MDLZ,)); state("episode 3, first sight")
record_divergences(g, snapshot=snap("s6"), divergences=(MDLZ,)); state("episode 3, SURVIVED a run")
record_divergences(g, snapshot=snap("s7"), divergences=(MDLZ,)); state("episode 3, survived two")
```

Output on `main` @ `03c5ab60`:

```text
episode 1, first sight           flags=1 resolutions=0 unresolved=['warn']
episode 1, gone                  flags=1 resolutions=1 unresolved=[]
episode 2, FIRST sight           flags=2 resolutions=1 unresolved=['critical']
episode 2, gone                  flags=2 resolutions=2 unresolved=[]
episode 3, first sight           flags=2 resolutions=2 unresolved=[]
episode 3, SURVIVED a run        flags=2 resolutions=2 unresolved=[]
episode 3, survived two          flags=2 resolutions=2 unresolved=[]
```

The third line should read `['warn']`, the fifth `['warn']`, the sixth and seventh `['critical']`.

---

## Scope — and what is deliberately NOT here

1. **The failing tests first.** A1 and A2 from the test plan, red on `main`, pasted in the Closeout.
2. **An episode enters the subject.** A divergence's `subject_ref` identifies one episode: the kind,
   the ticker, and a token taken from the snapshot that first saw it. It still starts with
   `broker-position-divergence:` and never with `broker-position-divergence:broker-position-snapshot:`
   (the legacy prefix the sweep script owns).
3. **Severity comes from the open episode.** For each live divergence, find the unresolved Flag of the
   same kind and ticker. None: open a new episode at `warn`. An unresolved `warn`: write `critical` on
   that episode's subject and resolve the `warn` as "superseded by critical". An unresolved `critical`:
   write nothing.
4. **Retirement is unchanged in meaning.** An unresolved Flag whose divergence is no longer live gets
   one appended `FlagResolution`, "divergence no longer present".
5. **The upgrade path.** An unresolved Flag in today's suffix-less format is treated as the open
   episode: it escalates or retires exactly as it would today. All 112 live Flags are resolved, but a
   `warn` could be open if a deploy lands between two runs.
6. **The law cycle** named above: `EXEC-OBS-07`, v1.10, test-plan rows, both rollups, DRIFT-093.

### Out of scope (do NOT build this sprint)

- **The readers.** `agents/supervisor/domain/health.py`, `surfaces/queries/flags.py`, the dashboard,
  `scripts/_audit_broker_graph_impl.py`, the daily brief. They join on `(subject_ref, severity)` and
  keep working unchanged, which is the reason the episode goes into the subject.
- **The 112 existing Flags.** No migration, no rewrite, no deletion, no bulk resolution.
- **`scripts/sweep_divergence_flags.py` and the legacy snapshot-keyed Flags.** Untouched, and
  `agents/execution/tests/test_reconciliation_flag_sweep.py` passes unchanged.
- **`position_divergences` and adoption.** What counts as a divergence, and how it is adopted, do not
  change.
- **No `contracts/` change, no new label, property, env key or tunable.**
- **No ADR reversal.**

### The road not taken (LAW-06)

- **Change line 48 to "no unresolved `warn`".** Rejected: the key is spent. Writing the new `warn` to
  the old key rewrites that Flag (`ON CONFLICT … DO UPDATE`), which breaks `EXEC-STA-03`, and the old
  `FlagResolution` still matches `(subject_ref, severity)`, so every reader sees the new flag as
  already resolved. It would turn a false `critical` into an invisible `warn`.
- **Re-open an episode by deleting or superseding its `FlagResolution`.** Rejected: deletion breaks
  append-only and loses the history; a resolution-of-a-resolution needs every reader changed.
- **Put the episode in the resolution key and leave the subject stable.** Rejected: readers in the
  supervisor and in `surfaces/` join on `(subject_ref, severity)`, so an execution defect would need a
  change in two other components.
- **Drop `critical` and flag every divergence `warn`.** Rejected: it removes the one signal S178
  built, that adoption failed.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **The episode token.** Recommended: the first-sight snapshot's key (unique per run-start
   reconciliation, already in hand, and it ties the flag to the snapshot that raised it). Not the run
   id (a resumed or re-fired run repeats it), not a clock or a uuid (the tests could not pin it), not
   a counter (a read-modify-write).
2. **The subject's exact format and separator**, within the two prefix rules in Scope item 2.
3. **How the open episode is found.** Recommended: read `Flag` and `FlagResolution` once each per
   call and work in memory. 112 Flags today, about two more a night.
4. **The upgrade path** for an unresolved suffix-less Flag. Recommended: treat it as the open episode.
   Retire-and-reopen would downgrade a real `critical` to `warn` for a night.

🪤 **Take the next free DL number, then re-check it at merge.** `DL-254` at spec time.

---

## Blast radius — measured 2026-10-01

| What | Detail |
| --- | --- |
| Files changed | `agents/execution/reconciliation_flags.py` (**138**); a new test file beside `agents/execution/tests/test_reconciliation_flags.py` (**150**); `agents/execution/laws/laws.md`, `test-plan.md`; `docs/laws/ledger.md`, `docs/laws/INDEX.md`, `docs/laws/drift-register.md`; `docs/design-log.md`; this file and its README row |
| Agents affected | execution only. It imports no other agent, and none imports it |
| Contract change? | No |
| Graph vocabulary change? | No new label or property. The **value** of `Flag.subject_ref` for this family gains an episode token |
| New env keys / tunables | None |
| Deploy implication | Image-only retag |
| Rollback | Retag to the previous tag. A retag does not undo the Flags and resolutions already written in the new format. The old code resolves any open one at the next run start as "divergence no longer present" (its `_retire_absent` resolves every family subject outside its own live set) and re-raises under the old keys, which is today's behaviour. No broker order, schema or infra setting is involved |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md`.
3. **Plant A1 and A2 first** and watch them fail. Paste the red output.
4. **Implement.**
5. **Law cycle:** `EXEC-OBS-07`, v1.10, test-plan rows, docstring citations, both rollups, DRIFT-093.
6. **Prove the guards can fail (DL-70)** — the four plants in the handover, each red, pasted, restored.
7. **`make ci` green** — every step of the `ci:` target, **redirected to a file, never piped**.
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 A second episode's first sighting is `warn` | divergence seen, gone, seen again | one unresolved `warn`, zero unresolved `critical` |
| A2 | 🎯 A third episode is flagged, and escalates when it survives | seen, gone, seen, gone, seen, seen | after the fifth call one unresolved `warn`; after the sixth one unresolved `critical` whose reason says it survived a run |
| A3 | A live divergence always has exactly one unresolved Flag | five episodes of mixed length (one, two and four runs present) for two tickers | after every call: one unresolved Flag per live divergence, none for an absent one |
| A4 | Inside one episode the dedupe still holds | four runs with the divergence present | two Flags in total, one unresolved `critical` |
| A5 | 🪤 An unresolved suffix-less Flag is the open episode | an old-format `warn` with no resolution, divergence still live; and one whose divergence is gone | the first becomes `critical` with no second `warn`; the second is resolved "divergence no longer present" |
| A6 | Spent old-format keys do not touch a new episode | old-format `warn` and `critical` for the subject, both resolved (the live shape of the 12) | a first sighting writes one unresolved `warn` under a new subject |
| A7 | 🪤 Nothing already written is rewritten (`EXEC-STA-03`) | record every `Flag` and `FlagResolution` node's props before each call in A3 | every earlier node's props are identical after every later call |
| A8 | The subject is deterministic and well-formed | the same snapshot twice; two snapshots | same snapshot and divergence give the same subject; different first-sight snapshots give different subjects; every subject starts with the family prefix and none with the legacy prefix |
| A9 | Reads stay bounded | a counting store, 30 live divergences | at most one `list_nodes("Flag")` and one `list_nodes("FlagResolution")` per call |
| A10 | The legacy sweep is untouched | none | `test_reconciliation_flag_sweep.py` passes with no edit |

---

## Success factors

- [ ] The reproduction above prints `['warn']` on lines 3 and 5 and `['critical']` on lines 6 and 7.
- [ ] A1–A10 pass; A1 and A2 were red on `main` first, and the red output is pasted.
- [ ] No existing `Flag` or `FlagResolution` is rewritten or deleted (A7).
- [ ] The five readers named in Out of scope are unchanged in the diff.
- [ ] Design decisions recorded with rejected alternatives.
- [ ] Law cycle done: `EXEC-OBS-07`, v1.10, test-plan rows, both rollups, DRIFT-093.
- [ ] Each of the four guards planted, watched to fail, restored — stated per guard.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

**Owed to the planner, not the builder:** `uv lock` with the PATCH bump, Windows `make ci`,
`make gate-ran` from the proving worktree, merge, the image-only retag, and two live checks.
**F1** (before the deploy, read-only on Neon): the live divergence Flags and resolutions copied into
an in-memory store; for each of the 53 subjects a first sighting gives one unresolved `warn` and no
`critical`, a second run gives `critical`, an absent run retires it; the live rows are not written.
**F2** (after the deploy): the first scheduled run in which a position enters or leaves the book
writes only `warn` Flags, in the new subject format, each resolved in that run, and no `critical`.

---

## Traps

🪤 **The one-line fix looks right and is wrong.** See the first road not taken. If your diff is one
line in `record_divergences`, A7 and A1 will tell you; do not make them pass by weakening them.
🪤 **Every existing test passes today.** They each run one episode. A green suite before your change is
not evidence of anything here.
🪤 **`created_at` is a wall-clock read.** The Flag's `created_at` is written with `datetime.now`. The
episode token must not come from it, or two calls in one test differ by microseconds and A8 means
nothing. Take it from the snapshot.
🪤 **A subject that contains a snapshot key is not a legacy subject.** The legacy test is
`startswith("broker-position-divergence:broker-position-snapshot:")`. Keep the kind and ticker in
front and the sweep never sees the new format.
🪤 **The test file is at 150 lines.** New tests go in a new file.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `reconciliation_flags.py` **138**, `reconciliation.py` **116**,
  `test_reconciliation_flags.py` **150**, `test_reconciliation_flag_sweep.py` **75**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. This sprint needs none.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — `make ci | tail` reports *`tail`'s* exit code. Redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it (the planner's, see below).
- Secrets never through the worktree — a worktree has **no `.env`**, so any proof needing live data
  is vacuous there. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving** and check the printed SHA
   against `git rev-parse HEAD`.
2. Merge to `main` locally and push. 🪤 Check you are not on the branch already.
3. **Post-merge CodeQL** on `main`, and the branch's open alerts against the last merged branch's.
4. **F1**, then the image-only retag (rollback tag recorded with the `DeployRecord`), then **F2**.
5. 🪤 **Repair the main checkout's venv after the merge** if `uv.lock` moved a package: the read-only
   folders on the planner's machine leave an upgraded package half-removed.

---

## Handover — paste this to the Claude cloud session

```text
Sprint 248 — a broker divergence is flagged critical only when it survived a run, however often that
ticker has diverged before. Spec:
docs/sprints/sprint-248-a-divergence-is-critical-only-when-it-survived-a-run.md on main (read ALL of
it, then CLAUDE.md). Repo: yury-gurevich/trading-agents.

Branch: sprint-248-a-divergence-is-critical-only-when-it-survived-a-run, cut from main. Never main. If
your session forces another branch name, use it and name it in the handback.
You have NO .env, NO gh, NO Azure and no route to download.pytorch.org. Every proof is a unit test on
InMemoryGraphStore. You cannot run `make gate-ran`: it is owed to the planner. Leave pyproject.toml's
version and uv.lock untouched and say so. Take the next free DL (DL-254 at spec time; re-check on main).

This handover is complete: nobody will send you follow-up messages. If something in the spec is wrong
or blocked, record it in the handback (Return notes, "not done") and stop; do not wait.

What and why: agents/execution/reconciliation_flags.py record_divergences (line 48) asks whether a
warn Flag EXISTS for a divergence's subject, not whether one is open. Flags are append-only and keyed
flag:{subject_ref}:{severity}; the subject is broker-position-divergence:{kind}:{ticker}, with no
episode. So each key is spent once per ticker. The second time a ticker diverges, its first sighting is
written `critical: survived a full run`. The third time, nothing is written at all, even if the
divergence really persists. Measured live 2026-10-01: 40 tickers have a spent warn, 12 have both keys
spent; MDLZ (09-30) and BAC (09-29) were flagged critical on first sight. The spec carries a
no-credentials reproduction script and its output: run it first.

MUST RULE before any code: read, whole, agents/execution/laws/laws.md + test-plan.md,
docs/laws/conventions.md, docs/laws/drift-register.md. Fill the Law reading record first.

Law-cycle answer: YES. The behaviour is in no clause (the tests cite EXEC-TRG-07, which is only about
the snapshot). Add EXEC-OBS-07 (per-episode flagging: warn on first sight, critical only if still
present at the next run-start reconciliation, closed by an appended FlagResolution, a new episode
starts at warn whatever the ticker's history, exactly one unresolved Flag per live divergence).
laws.md v1.9 -> v1.10 with a Changelog line; test-plan rows; clause ID in every test docstring; re-cite
the existing severity tests to EXEC-OBS-07 (the snapshot test keeps EXEC-TRG-07); rollups in
docs/laws/ledger.md AND docs/laws/INDEX.md (let make ci give the number); DRIFT-093.

Build:
1. The subject identifies one episode: kind, ticker, and a token from the snapshot that first saw the
   divergence (recommended: that snapshot's key). It starts with broker-position-divergence: and never
   with broker-position-divergence:broker-position-snapshot: (the legacy prefix).
2. Per live divergence, find the unresolved Flag of the same kind and ticker. None -> new episode,
   warn. Unresolved warn -> critical on that episode's subject, and resolve the warn "superseded by
   critical". Unresolved critical -> nothing.
3. An unresolved Flag whose divergence is gone gets one appended FlagResolution.
4. An unresolved Flag in today's suffix-less format is the open episode: it escalates or retires as it
   would today.
5. Read Flag and FlagResolution at most once each per call.
6. Law cycle.

Order: next free DL (decisions 1-4 with rejected alternatives) -> red A1 and A2 (paste) -> implement ->
law cycle -> DL-70 plants (restore the line-48 existence check: A1 red; drop the episode token from the
subject: A2 red; retire an open suffix-less flag unconditionally: A5 red; write a new flag to a spent
key: A7 red; each red, paste, restore) -> make ci redirected to a file, exit 0, 100.00 %.

DO NOT:
- change line 48 alone: the key is spent, merge_node rewrites the old Flag (ON CONFLICT DO UPDATE) and
  the old resolution makes the new flag read as resolved.
- rewrite, delete or bulk-resolve any existing Flag or FlagResolution; write a migration.
- touch agents/supervisor, surfaces/, scripts/sweep_divergence_flags.py,
  scripts/_audit_broker_graph_impl.py, contracts/, or what counts as a divergence.
- derive the episode token from a clock, a uuid, a counter or the run id.
- add a label, a property, an env key or a tunable.
- grow any module past 200 (test_reconciliation_flags.py is at 150: new tests go in a new file);
  # noqa to bypass a rule.
- claim a live proof or GATE PROVEN: F1, F2 and the gate are the planner's.
- pin a version: PATCH, next available at merge.

Handback — the planner returns it if ANY of these is missing:
[ ] Law reading record filled, including the law-cycle answer and contradictions/silences found.
[ ] Test plan results: A1-A10, each with final test name, file, PASS, clause IDs cited.
[ ] Closeout: the red run of A1 and A2 pasted before the fix; the green run after.
[ ] The reproduction script's output after the fix (lines 3 and 5 warn, 6 and 7 critical).
[ ] Each of the four DL-70 plants: what was planted, its red output, restored.
[ ] The DL number used, with decisions 1-4 and their rejected alternatives.
[ ] Module line counts for every file touched (all < 200).
[ ] make ci: the file, exit code, passed/skipped, coverage 100.00 %, dependency audit, detect-secrets.
[ ] Exactly how pyproject.toml and uv.lock were touched (untouched and owed, or what changed).
[ ] Owed items named: uv lock + PATCH bump, make gate-ran, Windows make ci, F1, retag, F2.
[ ] Status: BUILT in this file and in its docs/sprints/README.md row, in the same commit.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`, here and in the README row.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

*Filled 2026-10-01 before the first code change, in the cloud session's checkout of `main` @
`f1192239`. All four files read whole: `agents/execution/laws/laws.md` (v1.9, 459 lines),
`agents/execution/laws/test-plan.md` (123), `docs/laws/conventions.md` (160),
`docs/laws/drift-register.md` (196). Also read for the finding below: `agents/supervisor/laws/laws.md`
`SUP-IDN-02`, `contracts/execution.py` `owns_graph`, `contracts/supervisor.py` `owns_graph`.*

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| `agents/execution/reconciliation_flags.py` | execution `laws.md` + `test-plan.md`; `conventions.md`; `drift-register.md` | `EXEC-STA-03` 🟩 (all graph writes append-only; its cited test proves a `Fill` only, so for `Flag`/`FlagResolution` this sprint's A7 is the first proof); `EXEC-TRG-07` 🟩 (the snapshot, written before the flags; nothing here may prevent it, so the flag code still runs after `write_snapshot` and raises nothing new); new `EXEC-OBS-07` | Yes, twice. (1) `EXEC-STA-03` makes "never write to an existing `Flag` key" a guard in the writer, not only a property of the subject format (A7). (2) The single-writer finding below made me word `EXEC-OBS-07` in the passive ("is flagged") so the new clause claims no label ownership the supervisor book forbids |
| `agents/execution/tests/test_reconciliation_flag_episodes.py` (new), `test_reconciliation_flags.py` | same | conventions §3/§7: a clause ID in every docstring | Severity tests re-cited from `EXEC-TRG-07` to `EXEC-OBS-07`; the snapshot test keeps `EXEC-TRG-07` |
| `agents/execution/laws/laws.md`, `test-plan.md` | `conventions.md` §2 (IDs append-only: `OBS-07` is next free), §4 (version + Changelog with the *why*), §7a (the test-plan summary mirrors every conjunct) | — | The test-plan row restates all six conjuncts of `EXEC-OBS-07`, not a subset |
| `docs/laws/drift-register.md` | itself | conventions §9 | DRIFT-093 (the silence) and DRIFT-094 (the ownership contradiction) |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** `contracts/` is
untouched. It **declares** a guarantee S178 built and no clause held: **YES, law cycle owed and done
in this unit of work** — `EXEC-OBS-07`, v1.9 → v1.10, test-plan row, DRIFT-093, both rollups.

**Contradictions found between a law and this spec:** 🚨 **One, pre-existing, and I proceeded rather
than stopping — the planner should weigh that call.** `SUP-IDN-02` (supervisor `laws.md:18`):
*"The supervisor exclusively writes these graph labels (single-writer rule): `Message`, `Agent`,
`Flag`, `Fault`, `FlagResolution`."* Execution's CAP block says `"access": "write_own_labels_only"`
and lists neither label; `contracts/execution.py` `owns_graph` lists neither; `contracts/supervisor.py`
`owns_graph` lists both. Yet execution has written divergence `Flag`s since S120 (DRIFT-020) and
`FlagResolution`s since S178, and `reconciliation_flags.py:19` says so in a comment ("keys are
supervisor-owned; we never import that module"). No drift row recorded it. This spec tells execution
to keep writing both labels, so read literally it contradicts `SUP-IDN-02`. **Why I did not stop:**
the contradiction is in `main` today and this sprint neither adds a writer nor a label nor a new kind
of write; stopping would leave the measured defect (false `critical`s, 12 tickers blind) live while
an ownership question that is independent of it waits. **What I did instead:** DRIFT-094 (OPEN, forced
decision named), `EXEC-OBS-07` worded so it asserts what is flagged and when, not who owns the label,
and DL-254 D5 records the call and the rejected alternative (stop).

**Laws found silent where a decision was needed:** (1) The whole divergence-flag lifecycle: no clause
said when a divergence is `warn`, when `critical`, or how a flag closes; S178's tests cited
`EXEC-TRG-07`, which is about the snapshot. That silence is how the code drifted from S178's intent
(DRIFT-093, closed by `EXEC-OBS-07`). (2) No clause says what a second `record_divergences` call with
the **same** snapshot does. The spec's rule ("an unresolved `warn` → `critical`") would escalate on
it although no run has passed. I decided an episode is never escalated by the snapshot that opened it
(DL-254 D3) and wrote it into `EXEC-OBS-07` ("at the **next** run-start reconciliation").

**Clauses that were ⬜ and are now proven:** none were ⬜. `EXEC-OBS-07` is new and proven in this
sprint (⬜ → 🟩 at birth). `EXEC-STA-03` was already 🟩; A7 adds the first test of it on
`Flag`/`FlagResolution`.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a_second_episodes_first_sighting_is_warn` | `agents/execution/tests/test_reconciliation_flag_episodes.py` | PASS (red on `main` first) | `EXEC-OBS-07` |
| A2 | `test_a_third_episode_is_flagged_and_escalates_when_it_survives` | `agents/execution/tests/test_reconciliation_flag_episodes.py` | PASS (red on `main` first) | `EXEC-OBS-07` |
| A3 | `test_a_live_divergence_always_has_exactly_one_open_flag` (10 runs, MDLZ episodes of 1, 2, 4 runs and BAC of 4, 1; after every call the open set equals one Flag per live divergence, `warn` on its first run and `critical` after) | `agents/execution/tests/test_reconciliation_flag_episodes.py` | PASS | `EXEC-OBS-07` |
| A4 | `test_repeating_a_divergence_never_mints_a_second_unresolvable_flag` (the existing test is exactly A4: four runs present, two Flags, one open `critical`; re-cited, body unchanged) | `agents/execution/tests/test_reconciliation_flags.py` | PASS | `EXEC-OBS-07` (was `EXEC-TRG-07`) |
| A5 | `test_an_open_suffixless_flag_is_the_open_episode` (live MDLZ `warn` → `critical` on its own suffix-less subject, 3 Flags in total so no second `warn`; absent BAC `warn` resolved "divergence no longer present") | `agents/execution/tests/test_reconciliation_flag_upgrade.py` | PASS | `EXEC-OBS-07` |
| A6 | `test_spent_suffixless_keys_do_not_touch_a_new_episode` | `agents/execution/tests/test_reconciliation_flag_upgrade.py` | PASS | `EXEC-OBS-07` |
| A7 | `test_nothing_already_written_is_rewritten` (A3's schedule; props of every earlier `Flag` and `FlagResolution` identical after every later call) | `agents/execution/tests/test_reconciliation_flag_episodes.py` | PASS | `EXEC-STA-03` / `EXEC-OBS-07` |
| A8 | `test_the_subject_is_deterministic_and_well_formed` (a live-shaped snapshot key twice → same subject, a second key → different; family prefix, never the legacy prefix, parses to `(kind, ticker)`) | `agents/execution/tests/test_reconciliation_flag_upgrade.py` | PASS | `EXEC-OBS-07` |
| A9 | `test_each_call_reads_flag_and_resolution_once` (30 live divergences; first sight, escalation and retirement calls each read exactly `Flag` ×1 and `FlagResolution` ×1, and make **no** `get_node` call) | `agents/execution/tests/test_reconciliation_flag_upgrade.py` | PASS | `EXEC-OBS-07` |
| A10 | the three tests of `test_reconciliation_flag_sweep.py` | `agents/execution/tests/test_reconciliation_flag_sweep.py` | PASS **with a one-argument edit** — *not met as written* ("no edit"); see Return notes | unchanged (`EXEC-TRG-07`, `EXEC-STA-03` ×2) |

**Tests added beyond the plan:** (1) `test_a_repeated_call_for_one_snapshot_is_not_a_survived_run`
(DL-254 D3: the snapshot that opened an episode never escalates it), (2)
`test_an_open_critical_supersedes_a_stray_open_warn` (a live divergence keeps exactly one open Flag),
(3) `test_a_spent_critical_key_is_never_rewritten` (DL-254 D4's accepted limit; `EXEC-STA-03` /
`EXEC-OBS-07`) — all in `test_reconciliation_flag_upgrade.py`. **Re-cited, bodies changed only to pass
the episode:** `test_first_sight_of_a_divergence_is_warn_not_critical` and
`test_a_divergence_surviving_a_run_escalates_to_critical` (`EXEC-TRG-07` → `EXEC-OBS-07`),
`test_an_adopted_divergence_is_retired_on_the_next_run` (`EXEC-STA-03` → `EXEC-OBS-07 / EXEC-STA-03`).
`test_run_start_reconciliation_records_an_agreeing_book_without_flags` keeps `EXEC-TRG-07`. New shared
fixture module: `agents/execution/tests/flag_episode_helpers.py`.

---

## Closeout — evidence

**Tree the proofs ran in (and `.env` present?):** the claude.ai cloud session's checkout
`/home/user/trading-agents`, branch `claude/upbeat-fermi-wva7zm` cut from `main` `f1192239`.
**No `.env`.** Dependencies installed with `uv sync --frozen` (as CI does; the forecaster extra needs
`download.pytorch.org`, which this session cannot reach, and CI does not install it either). Every
proof is a unit test on `InMemoryGraphStore`; nothing ran against Neon, Alpaca or Azure.

**Result:** BUILT. Each occurrence of a divergence is its own episode; severity is read from the open
episode, never from a ticker's spent keys. Unit-proven only; F1 and F2 are the planner's.

**Files changed:**

- `agents/execution/reconciliation_flags.py` — the episode subject (`subject_ref_for(divergence,
  episode)`), the open-episode state machine, the spent-key guard; the legacy sweep path unchanged.
- `agents/execution/divergence_episodes.py` (**new**) — pure read side: `flag_join`, `identity`,
  `open_episodes` and the two prefixes. Split out because the flags module reached 208 lines.
- `agents/execution/tests/flag_episode_helpers.py` (**new**), `test_reconciliation_flag_episodes.py`
  (**new**), `test_reconciliation_flag_upgrade.py` (**new**).
- `agents/execution/tests/test_reconciliation_flags.py` — four docstrings re-cited, three calls pass
  the episode.
- `agents/execution/tests/test_reconciliation_flag_sweep.py` — **one argument** (Return notes).
- `agents/execution/laws/laws.md` (v1.10, `EXEC-OBS-07`, Changelog), `test-plan.md` (one row);
  `docs/laws/ledger.md`, `docs/laws/INDEX.md` (38 / 64); `docs/laws/drift-register.md` (DRIFT-093,
  DRIFT-094); `docs/design-log.md` (DL-254); this file and its `docs/sprints/README.md` row.
- **Not touched:** `agents/supervisor/`, `surfaces/`, `scripts/sweep_divergence_flags.py`,
  `scripts/_audit_broker_graph_impl.py`, `contracts/`, `reconciliation_store.py`
  (`position_divergences`), `reconciliation.py`, `pyproject.toml`, `uv.lock`.

**Design decisions:** [DL-254](../design-log.md). D1 token = the first-sight snapshot's key (rejected:
run id, clock/uuid, counter). D2 subject = `broker-position-divergence:{kind}:{ticker}:{snapshot key}`
(rejected: an `@` separator, token first — it would start with the legacy prefix — and a hash). D3 one
read of `Flag` and one of `FlagResolution`, open = no resolution on `(subject_ref, severity)`, grouped
by `(kind, ticker)`; the snapshot that opened an episode never escalates it; the writer refuses a key it
has read (rejected: a `get_node` per divergence, a prefix-query port, escalating on any open `warn`).
D4 an open suffix-less Flag is the open episode (rejected: retire-and-reopen). D5 proceed despite the
`SUP-IDN-02` contradiction (rejected: stop; route through the supervisor). D6 the sweep test changes by
one argument (rejected: a suffix-less subject for a ticker's first episode).

**Proof — the red run first** (A1, A2 written before any code change, on `f1192239`):

```text
FF                                                                       [100%]
agents/execution/tests/test_reconciliation_flag_episodes.py:24: in test_a_second_episodes_first_sighting_is_warn
E   AssertionError: assert ['critical'] == ['warn']
E     At index 0 diff: 'critical' != 'warn'
agents/execution/tests/test_reconciliation_flag_episodes.py:34: in test_a_third_episode_is_flagged_and_escalates_when_it_survives
E   AssertionError: assert [] == ['warn']
E     Right contains one more item: 'warn'
FAILED agents/execution/tests/test_reconciliation_flag_episodes.py::test_a_second_episodes_first_sighting_is_warn
FAILED agents/execution/tests/test_reconciliation_flag_episodes.py::test_a_third_episode_is_flagged_and_escalates_when_it_survives
2 failed in 0.57s
```

**Proof — the green run:**

```text
test_reconciliation_flag_episodes.py::test_a_second_episodes_first_sighting_is_warn PASSED
test_reconciliation_flag_episodes.py::test_a_third_episode_is_flagged_and_escalates_when_it_survives PASSED
test_reconciliation_flag_episodes.py::test_a_live_divergence_always_has_exactly_one_open_flag PASSED
test_reconciliation_flag_episodes.py::test_nothing_already_written_is_rewritten PASSED
test_reconciliation_flag_upgrade.py::test_an_open_suffixless_flag_is_the_open_episode PASSED
test_reconciliation_flag_upgrade.py::test_spent_suffixless_keys_do_not_touch_a_new_episode PASSED
test_reconciliation_flag_upgrade.py::test_the_subject_is_deterministic_and_well_formed PASSED
test_reconciliation_flag_upgrade.py::test_a_repeated_call_for_one_snapshot_is_not_a_survived_run PASSED
test_reconciliation_flag_upgrade.py::test_an_open_critical_supersedes_a_stray_open_warn PASSED
test_reconciliation_flag_upgrade.py::test_a_spent_critical_key_is_never_rewritten PASSED
test_reconciliation_flag_upgrade.py::test_each_call_reads_flag_and_resolution_once PASSED
test_reconciliation_flags.py::test_first_sight_of_a_divergence_is_warn_not_critical PASSED
test_reconciliation_flags.py::test_a_divergence_surviving_a_run_escalates_to_critical PASSED
test_reconciliation_flags.py::test_repeating_a_divergence_never_mints_a_second_unresolvable_flag PASSED
test_reconciliation_flags.py::test_an_adopted_divergence_is_retired_on_the_next_run PASSED
test_reconciliation_flags.py::test_run_start_reconciliation_records_an_agreeing_book_without_flags PASSED
test_reconciliation_flags.py::test_a_flag_whose_key_contradicts_its_severity_prop_is_not_resolved PASSED
test_reconciliation_flag_sweep.py::test_a_run_leaves_legacy_and_foreign_flags_alone PASSED
test_reconciliation_flag_sweep.py::test_the_sweep_retires_legacy_flags_once_and_only_legacy_ones PASSED
test_reconciliation_flag_sweep.py::test_legacy_flag_without_a_severity_prop_defaults_to_critical PASSED
20 passed in 0.45s
```

**The reproduction after the fix** (the spec's script, unchanged, `PYTHONPATH=.`, no `.env`):

```text
episode 1, first sight           flags=1 resolutions=0 unresolved=['warn']
episode 1, gone                  flags=1 resolutions=1 unresolved=[]
episode 2, FIRST sight           flags=2 resolutions=1 unresolved=['warn']
episode 2, gone                  flags=2 resolutions=2 unresolved=[]
episode 3, first sight           flags=3 resolutions=2 unresolved=['warn']
episode 3, SURVIVED a run        flags=4 resolutions=3 unresolved=['critical']
episode 3, survived two          flags=4 resolutions=3 unresolved=['critical']
```

Lines 3 and 5 `['warn']`, 6 and 7 `['critical']`. Before the fix, on `f1192239`, it printed the spec's
output byte for byte (`['critical']`, then `[]` ×3).

**Guards planted** (each applied to the working tree, run, then the saved file copied back and
`cmp`-verified identical; no plant was committed):

1. **Restore line 48's existence check — A1 red.** With no open episode, a first sighting went to
   `critical` whenever a `warn` key had ever been written for that kind and ticker (resolved or not):

   ```text
   E   AssertionError: assert ['critical'] == ['warn']
   FAILED …/test_reconciliation_flag_episodes.py::test_a_second_episodes_first_sighting_is_warn
   ```

   *(A first, cruder plant — counting resolved Flags as open in `open_episodes` — also went red, but by
   the store refusing to re-resolve: `ValueError: property 'resolved_at' cannot be overwritten`. The
   faithful plant above is the one that reproduces the live symptom.)*
2. **Drop the episode token from the subject — A2 red.** `subject_ref_for` returned
   `…:{kind}:{ticker}`; the third episode's keys are spent, the writer refuses them, nothing is flagged:

   ```text
   test_reconciliation_flag_episodes.py:40: in test_a_third_episode_is_flagged_and_escalates_when_it_survives
   E   AssertionError: assert [] == ['warn']
   1 failed in 0.43s
   ```

3. **Retire an open suffix-less Flag unconditionally — A5 red.** Every open subject with no token was
   closed "divergence no longer present" before the divergences were walked:

   ```text
   test_reconciliation_flag_upgrade.py:56: in test_an_open_suffixless_flag_is_the_open_episode
   E   AssertionError: assert ['broker-posi...tion:MDLZ:s9'] == ['broker-posi...osition:MDLZ']
   E     At index 0 diff: 'broker-position-divergence:extra_graph_position:MDLZ:s9' != 'broker-position-divergence:extra_graph_position:MDLZ'
   1 failed in 0.57s
   ```

4. **Write a new flag to a spent key — A7 red.** Token dropped **and** the spent-key guard removed (the
   one-line fix's shape). On `InMemoryGraphStore` the store itself refuses inside the call:
   `ValueError: property 'reason' cannot be overwritten` → A7 FAILED. To show A7's **own** comparison
   is not vacuous, the same plant was re-run with the store's `_append_props` monkeypatched to overwrite
   silently (a temporary `conftest.py`, removed):

   ```text
   E   AssertionError: ('s3', 'flag:broker-position-divergence:extra_graph_position:MDLZ:warn')
   E     Differing items:
   E     {'reason': 'Broker position divergence at run start (s3):\n- extra_graph_position MDLZ graph_qty=16'} != {'reason': 'Broker position divergence at run start (s1):\n- extra_graph_position MDLZ graph_qty=16'}
   E     {'created_at': '2026-10-01T02:46:58.548893+00:00'} != {'created_at': '2026-10-01T02:46:58.548712+00:00'}
   ```

**Module line counts:** `reconciliation_flags.py` **179** (was 138); `divergence_episodes.py` **56**
(new); `tests/flag_episode_helpers.py` **60** (new); `tests/test_reconciliation_flag_episodes.py`
**93** (new); `tests/test_reconciliation_flag_upgrade.py` **160** (new);
`tests/test_reconciliation_flags.py` **150** (unchanged count); `tests/test_reconciliation_flag_sweep.py`
**75** (unchanged count). All < 200; three sit in the 150 warn band and are printed as `[WARN]` by the
gate (179, 160, 150).

**`make ci`:** `make ci > scratchpad/ci.txt 2>&1 ; echo $?` → **exit 0**, run on the full working tree
before this handback was written, and re-run after it (see Return notes). All 15 steps: ruff, format
(1,511 files), mypy (1,130 files, no issues), import-linter (5 kept, 0 broken), module size (warnings
only), module header, law coverage, PARAM/settings sync (two pre-existing envelope warnings), sprint
status, markdown links, version scheme, pytest **3,775 passed, 8 skipped**, coverage **100.00 %**
(`divergence_episodes.py` and `reconciliation_flags.py` both 100.00 %), dependency audit "No unaccepted
vulnerabilities; 1 accepted advisory re-checked" (PYSEC-2026-2447, diskcache, DL-184), detect-secrets
**Passed**, untracked-secrets scan of the 4 new files **Passed**.

**`pyproject.toml` and `uv.lock`:** **untouched** — the version stays `0.120.01` and the lock is
byte-identical to `main`. `uv sync --frozen` read the lock and wrote nothing to it. The PATCH bump and
the `uv lock` that must follow it are owed to the planner (this session cannot re-resolve: no route to
`download.pytorch.org`).

**Owed to the planner:** `uv lock` with the PATCH bump (next available at merge); `make gate-ran` from
the proving worktree (no `gh` here); Windows `make ci`; **F1** (read-only replay of the 53 live
subjects on Neon in memory); the image-only retag; **F2** (the first run in which a position enters or
leaves the book). Nothing in this handback is `GATE PROVEN` or a live proof.

**Not met / verified failing:** **A10 as written** — "`test_reconciliation_flag_sweep.py` passes with
no edit" is not met; it passes with a one-argument edit (Return notes, item 1). Everything else in the
success factors is met.

---

## Return notes

1. **A10 could not be met as written, and I edited one argument rather than stop.** The sweep test's
   `test_the_sweep_retires_legacy_flags_once_and_only_legacy_ones` finds the run's own `warn` by
   `subject_ref_for(_PFE)` — the suffix-less subject — to show the sweep leaves it alone. The spec makes
   the subject name its episode (Scope 2), which cannot be computed from the divergence alone, so no
   one-argument form can name the Flag the run wrote. Measured, edit-free: `TypeError:
   subject_ref_for() missing 1 required positional argument: 'episode'`; and with a one-argument form
   kept, the suffix-less key is simply absent (`suffix-less key present: False`; the run wrote
   `flag:broker-position-divergence:missing_graph_position:PFE:s1:warn`). The edit is
   `subject_ref_for(_PFE)` → `subject_ref_for(_PFE, 's1')`; the assertion, the legacy fixtures, the
   other two tests and `scripts/sweep_divergence_flags.py` are untouched, and the sweep's behaviour is
   unchanged. DL-254 D6.
2. **The law contradicted the spec, and I did not stop (MUST RULE step 6) — please weigh it.**
   `SUP-IDN-02` makes the supervisor the single writer of `Flag` and `FlagResolution`; execution has
   written both since S120/S178, unrecorded. This sprint changes neither who writes nor which labels.
   DRIFT-094 (OPEN) carries the forced decision; DL-254 D5 the call. If the planner holds that step 6
   should have stopped the sprint, the branch can be returned as it stands — the contradiction is the
   same with or without it. Nothing enforces it at runtime: the vocabulary pack's `owners` map is
   empty on purpose.
3. **A correction to DL-253 and this spec's first road not taken.** `merge_node` to a spent key does not
   silently rewrite the old Flag on Postgres: the `ON CONFLICT … DO UPDATE` has a `WHERE NOT EXISTS`
   that skips a changed prop, and `_raise_merge_conflict` raises `ValueError … cannot be overwritten`
   (`kernel/graph_postgres.py:99`), exactly as `InMemoryGraphStore` does. So the one-line fix would have
   raised inside `reconcile_run_start` after the snapshot was written. Still rejected; recorded in
   DL-254, DL-253 itself left as the planner wrote it.
4. **One decision the spec did not ask for:** a second call with the **same** snapshot does not escalate
   (DL-254 D3; `test_a_repeated_call_for_one_snapshot_is_not_a_survived_run`), so `EXEC-OBS-07` reads
   "at the **next** run-start reconciliation". `reconcile_run_start` writes one snapshot per run today
   (`EXEC-TRG-07`), so nothing live depends on it.
5. **Accepted limit (DL-254 D4):** an open suffix-less `warn` whose `critical` key is already spent is
   not escalated (the writer refuses spent keys); it stays the one open `warn` and retires when the
   divergence goes. Only two crashes in a row between the old code's writes could produce it, and all
   112 live Flags are resolved.
6. **Rollback note, unchanged from the spec:** the old code's `_retire_absent` resolves any open
   new-format Flag as "divergence no longer present" and re-raises under the old keys.
7. `docs/STATE.md` was not edited: it is the planner's live tracker and the spec's handback list names
   only this file and its README row.
8. **Branch:** the session forced `claude/upbeat-fermi-wva7zm`; the spec's
   `sprint-248-a-divergence-is-critical-only-when-it-survived-a-run` was not created.

### Planner, at merge (2026-10-01)

- **Scope held.** The diff touches execution, its law book and docs only; no supervisor, `surfaces/`, `scripts/`, `contracts/` or `kernel/` file.
- **Proven.** Windows `make ci` exit 0 (3,775 passed, 8 skipped, 100.00 %); `GATE PROVEN` for `09699ad0` from the proving worktree, printed SHA equal to `HEAD`; fast-forwarded, so the merged SHA is the gated SHA; the branch's open CodeQL alerts equal the last merged branch's (0 added).
- **F1 PASS** ([functionality-checks](../laws/functionality-checks.md)). Live: 112 family Flags (65 run-stable, 47 legacy snapshot-keyed) and 112 resolutions; 53 subjects, 40 with a spent `warn`, 12 with both, and 1 old hash-keyed `critical`.
- **A10** as written was the spec's mistake: `subject_ref_for` had to gain the episode, so a test that names the flag by its subject had to pass it. Accepted.
- **DRIFT-094** is real and older than this sprint. Proceeding was right: stopping would have left a live defect to protect a rule nothing enforces. Filed as work-queue 102.
- **The spec's first road not taken was rejected for a wrong reason** (see the corrected Measured row). The one-line fix would have raised inside `reconcile_run_start`, not hidden a `warn`. Still rejected.
- **Accepted limit (DL-254 D4):** an open suffix-less `warn` whose `critical` key is already spent is not escalated. No live subject has that shape today: 0 Flags are open, and the one subject with a `critical` and no `warn` is the old hash-keyed one, which matches no ticker.
- **Owed:** the image-only retag (operator's call; rollback `s246`), then F2.
