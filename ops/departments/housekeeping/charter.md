---
department: housekeeping
tier: x cross-cutting
owner: operator + AI housekeeping loop  (→ candidate "Librarian" agent)
status: draft
version: 0.3
implements_with: [.gitignore, ops/maintenance/ledger.md, "del-folder convention (../trading-agent-del/)"]
---

# Charter — Housekeeping & Navigability (keep the repo legible for humans)

> The operational law for keeping the repository **navigable and understandable by a human**.
> Where other charters keep systems *working*, this one keeps the codebase *legible*: every folder
> self-describes (INDEX.md), READMEs stay current, the root stays clean, nothing dead lingers, and
> git/GitHub stay lean. Subordinate to LAW-01…06. It changes no behaviour and ships no feature — it
> makes the system **findable**, for the human operator and the AI alike.

## OPS-IDN · Identity

Cross-cutting. Owns the *legibility* of the repo: the INDEX.md-per-folder rule, README currency,
folder-structure standards, root-folder cleanliness, the "del folder" delete convention, gitignore
discipline, and local/GitHub size hygiene. Exists because a one-person product nobody can navigate is
a liability — navigability is a first-class deliverable.

### What is IN / OUT

**IN:** INDEX.md / README structure, folder layout (folder-per-topic), root-folder cleanliness,
naming, dead-file removal, gitignore + regenerable-artifact hygiene, local & GitHub size audits, the
del-folder mechanism, fixing dead cross-links after moves.

**OUT:** code behaviour/logic (agents + CI own that), secrets (Security & IAM), infra/compute
(Platform/SRE), parameter tuning (Experimentation). **Housekeeping never changes what the code does.**

## OPS-OWN · Owns (single-writer)

- The `INDEX.md` in every `docs/` and tool folder (the "read me first" map per folder).
- The folder-structure conventions (every folder has an INDEX.md; a topic is a folder, not a loose file).
- Root-folder policy (what may live at repo root: config + `conftest.py` + `README`/`CLAUDE`; nothing else).
- `.gitignore` discipline for regenerable artifacts + the del-folder convention.
- The **size of the live trackers** (G-SIZE): what leaves a tracker, when, and where it goes. Not
  what a tracker says: its content stays with whoever writes it.
- This charter (the process). Does **not** own source code, agent laws, or ADRs.

## OPS-UP · Upstream (needs)

A tracked git repo, the ops ledger (`ops/maintenance/ledger.md`), and the external del folder
(`../trading-agent-del/` — the recoverable trash).

## OPS-DOWN · Downstream (blast radius)

Everyone who reads the repo — human or AI. Bad housekeeping → slower navigation, edits to the wrong
file, docs that lie about reality. **Blast radius is comprehension, not runtime.**

## OPS-GATE · Preflight gates (tidiness checks)

| Gate ID | Check | Pass criteria | On fail |
| --- | --- | --- | --- |
| G-IDX | every `docs/`/tool folder has an `INDEX.md` | present | add it |
| G-ROOT | no stray scripts/data/binaries at repo root | only config + `conftest.py` + `README`/`CLAUDE` | rehome or del |
| G-HIST | no large binary in git history; artifacts gitignored | `git count-objects` pack small | gitignore; history rewrite only via PNR-HK-01 |
| G-LINK | a move/rename left no dead inbound links | all links resolve | fix the references |
| G-DOC | README/INDEX reflect the current structure | current | refresh in the same change |
| G-SIZE | each live tracker is under its size limit, counted in bytes | the table under OPS-TRIM | run the tracker trim |

## OPS-ACT · Actions / Runbooks

| Action | Gates | Idempotent | Dry-run | Postcondition | Rollback | Blast radius |
| --- | --- | --- | --- | --- | --- | --- |
| root sweep | G-ROOT | yes | list-only | each root file is keep / rehomed / del'd | restore from del | none |
| folder-per-topic reorg | G-IDX/LINK | yes | n/a | every topic is a folder with an INDEX.md; links fixed | `git revert` | docs nav |
| INDEX/README refresh | G-DOC | yes | n/a | maps match reality | `git revert` | docs nav |
| dead-file removal | G-ROOT | yes | list-only | stray/regenerable files gone (del or `git rm`) | del folder / git history | none |
| size audit | G-HIST | yes | report-only | reclaimable artifacts deleted; pack measured | regenerate | none |
| tracker trim | G-SIZE/LINK/DOC | yes | report-only: sizes before, and what each rule would move | every tracker under its limit; everything removed is in the place its rule names; every link resolves | `git revert` | docs nav |

## OPS-TRIM · The tracker trim (v0.2, operator 2026-10-09)

The files edited most often are the trackers, and they only grow. Measured 2026-10-09 over the 593
commits of the 30 days before: `docs/STATE.md` was touched by 258 of them, `docs/work-queue.md` by
221, `docs/design-log.md` by 203, `docs/sprints/README.md` by 151 and `docs/sprints/INDEX.md` by 143.
`STATE.md` kept its limit of 200 lines at 76 KB, with one header line of 6 KB; the work queue was
242 KB in 272 lines, 71 % of it rows already closed. **A limit counted in lines does not hold a file
that grows sideways, so these limits are in bytes.**

| Tracker | Limit | What leaves at a trim | Where it goes |
| --- | --- | --- | --- |
| `docs/STATE.md` | 40 KB | a *Now* entry on which nothing is owed; narrative older than the current leg; anything in the header beyond stamp, version and one headline | `docs/state-archive/`, the next numbered file |
| `docs/work-queue.md` | 64 KB | a row that is closed or folded; the dated recount paragraphs above the table | `docs/work-queue-archive/` |
| `docs/sprints/README.md` | 96 KB | for a MERGED sprint outside the newest twelve rows: its status cell beyond the first clause and its goal cell beyond the lead sentence | nowhere: the sprint's own document holds both, and git holds the row as it was |
| `docs/sprints/INDEX.md` | 48 KB | a row of the queued table whose sprint is MERGED and has a README row | nowhere: the README row is the record |
| `docs/design-log.md` | 512 KB | every entry but the newest forty and any older entry that the work queue or STATE links | `docs/design-log-archive/`, by number range, verbatim, in the order the log held them |
| `docs/laws/functionality-checks.md` | 160 KB | every sprint row but the newest sixty; the production-operations table and the harness lesson stay | `docs/laws/functionality-checks-archive/`, one file a month by the row's date |
| `docs/laws/drift-register.md` | 160 KB | nothing yet; its rule is decided when it nears the limit | |

**A KB here is 1,000 bytes**, counted on the file as git stores it (line ends as LF): 40 KB is 40,000.

**The trim moves text; it does not rewrite it.** A moved row or entry is byte for byte what it was,
except that a relative link is re-based for its new folder. The two sprint tables are the exception
the table names: they are shortened, because the sprint's own document already holds what is cut.
Each archive folder has an `INDEX.md` (G-IDX), and the live file says in one line where its older
material went. **Never** trimmed: a law book, a sprint's own document, an ADR, an experiment record,
anything under a fidelity decision path (`scripts/replay_fidelity_git.py` lists them), and any row or
entry on which something is still owed.

**Who and when.** The Librarian, at the first session of each week, and whenever a tracker passes its
limit. `STATE.md` is trimmed by whoever is writing it that session, because deciding what is still
owed there is not housekeeping. Until `make ci` checks the limits the trim measures them by hand;
the gate step is a chore of its own, and once it exists a tracker over its limit fails the gate.

## OPS-PNR · Points of no return

| PNR ID | Irreversible step | Why | Guard |
| --- | --- | --- | --- |
| PNR-HK-01 | git history rewrite to shrink GitHub (filter-repo / BFG) | rewrites SHAs, breaks clones, needs force-push | explicit operator confirm **and** the size must justify it |
| PNR-HK-02 | `git rm` a tracked file with no regenerator, not copied to del | only git history recovers it | move to del first, or confirm |

## OPS-REC · Recovery

- The **del folder** (`../trading-agent-del/<date>-<reason>/`) is the recoverable trash for anything
  pulled from the working tree. Tracked deletions are also recoverable from git history.
- RPO = the del copy / last commit; RTO = a `mv` back or `git checkout`.

## OPS-NEV · Never

- Never touch operator-declared **untouchables** (e.g. `desktop.ini`, `folderico-favorites.ico`).
- Never delete **non-regenerable** data without moving it to del first.
- Never **rewrite git history** without explicit confirmation (PNR-HK-01).
- Never leave a moved file with **dead inbound links** (G-LINK).
- Never **commit a regenerable artifact or a binary** — gitignore it instead.

## OPS-OBS · Observability (how to tell it's tidy)

Root file count small and all-belong; every folder has an `INDEX.md`; `git count-objects -vH` pack
stays small; no large gitignored junk lingering; no dead links. Each housekeeping pass writes a row to
`ops/maintenance/ledger.md`.

## OPS-TUNE · Tuning

- **Assess:** root-stray count, folders-missing-INDEX, dead-link count, `.git` pack size, GB of
  reclaimable local junk.
- **Improve:** tighten `.gitignore` where junk recurs; ship an INDEX/README template; automate the
  size audit. Operator approves each change.

## OPS-PARAM · Parameters

| Param | Default | Range / options | Effect |
| --- | --- | --- | --- |
| size-audit cadence | per-chore / monthly | on-demand … monthly | when to sweep local + pack size |
| del retention | keep dated folders | days | how long del subfolders live before purge |
| tracker trim cadence | weekly, the first session of the week | weekly … on a G-SIZE failure | when the trackers are cut back to their limits |

## OPS-MNT · Maintenance trigger

When you **add a folder** → add its `INDEX.md`. When you **move/rename files** → update every inbound
link + the parent `INDEX.md` in the same change. When you **add a file at repo root** → justify it or
rehome it. When **local artifacts balloon** → run the size audit. When **a week starts, or a tracker passes its limit** → run the tracker trim (OPS-TRIM). Each pass writes a ledger row.

## Graduation to an agent — yes, an agent is being born

Today the owner is "operator + AI housekeeping loop." It already has the exact shape of a platform
agent: a bounded remit, an artifact it solely owns (the INDEX.md map), gates, runbooks, and a
measurable goal (navigability). Per **LAW-01 CI-05** (automation is *earned*), once this loop shows a
clean ledger track record it graduates into a **Librarian agent** — keeper of repo structure and
navigability — running these gates and the maintenance loop autonomously. **This charter is that
agent's `laws.md` in waiting.** (Same trajectory `ops/maintenance/loop.md` foresees: "an owner can
become a specific agent.")

## Changelog

| Version | Date | Change |
| --- | --- | --- |
| 0.1 | 2026-06-24 | initial draft — registers the root / INDEX / README / git-size housekeeping process; names the future Librarian agent |
| 0.3 | 2026-10-11 | first trim of the design log and the functionality-check register, and what it taught the two rules: an older design-log entry that the work queue or STATE links stays live; the register's operations table and harness lesson stay; a KB is 1,000 bytes on the file as git stores it |
| 0.2 | 2026-10-09 | the tracker trim (OPS-TRIM) and gate G-SIZE: size limits in bytes for the seven most-edited trackers, what leaves each and where it goes, weekly cadence (operator: *"yes, please"* to a maintenance schedule for frequently edited files) |
