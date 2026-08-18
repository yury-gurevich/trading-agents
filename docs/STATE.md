# Project State

**Last updated:** 2026-08-18 16:55 AEST · **Version:** 0.90.14 · **Fleet: `s178`** (16 apps + job, verified) · **S179 branch/local + live sweep proven:** `healthy` can be true again; S179 code/pack is not deployed yet.

**How to read.** *Now* = active · *Next* = queued · *Recent* = last few shipped (older detail lives in
each `docs/sprints/sprint-NN-*.md` + [`state-archive/`](state-archive/INDEX.md) `STATE-01…07.md` + git). **LAW-02:** an item is "shipped" only when
its success factors are *proven* (tests, `make ci`, the named live check) — never restate intent as outcome.
**Size rules**, after this file reached 574 lines with a **112 KB header line**: keep it **under 200
lines**, and keep the header above to **three clauses — stamp, version, one headline**. Replace that
headline each session; never append a fourth. Oldest *Recent* entries split to the archive.

---

## Current focus

Since P14 the project runs as **etalon-first continuous improvement** (DL-19).
**The platform is self-driving in paper mode**: the DEPLOYED, STANDING fleet (16 Container Apps +
`dispatcher-cron` job, KEDA scale-to-zero windows, idle ≈ $0) places a calendar-gated `RunRequest`
at 22:30 UTC daily, runs graph-pull + served-over-Service-Bus on the Neon Postgres spine (ADR-0014),
reconciles holdings against the broker (DL-44), debates vetoes under compiled prompts (DL-42), and
proves `ACCEPTANCE PASS`. Pausing = disable the job + zero the scale windows (`docs/deployment.md`).
Completed arcs live in their sprint docs + archives: fleet (DL-35), credentials (DL-36), Postgres
migration (DL-43), deliberation quality (DL-41/42). Layer-3 acceptance 🟩 at the full S&P-500;
Layer-2 choreography 🟩 on a distributed run (S102).

## Recent (most recent first — detail in each sprint doc)

- **The gate was red for two days over one test line (fix, no bump, 2026-08-17 —
  [DL-110](design-log.md)).** Four straight `Security Findings` runs failed — three on docs-only
  commits — on CodeQL `py/mismatched-multiple-assignment` **#177**, the only error-level alert of 76
  open: a PM test unpacked `SectorBook.outcomes()` into two names, and that call returns `()` when
  the ticker has no sector. Length now asserted, then indexed. `make ci` **2302 passed / 100.00 %**;
  #177 reads `fixed`; `GATE PROVEN` for `21a5e81`. 🪤 **A branch cannot clear an alert raised on
  `main`** — `codeql.yml` runs only there, so the fix branch failed its own gate on the same alert;
  merge-then-verify was the only exit. 🪤 **The step prints nothing on failure** (report → summary).

- **The veto read word counts as article counts, and the fleet caught up (fix, `0.90.11`,
  2026-08-15 — [DL-112](design-log.md)).** `sched-2026-08-14` completed **8/8** and put 9 PM
  approvals to the deliberator; **8 came back vetoed and 1 order reached the broker**. Reading the
  verdicts: **5 of the 8 cite defects S175 had already fixed but which were not deployed** (the
  invented ATR fragment on AMZN/MDLZ; sector/batch absence read as zero exposure on AVGO/CSCO/GOOGL).
  A sixth was **new and false in code** — XOM vetoed for a *"sentiment feed internally
  inconsistent (10 articles but 11 positive and 3 negative)"*, when `sentiment_positive` counted
  lexicon **word occurrences** and `sentiment_articles` counted **headlines**: two units, one prefix,
  carried verbatim into the debate by `quant_metrics`. Renamed to `sentiment_positive_words` /
  `sentiment_negative_words`; no computed value changed. `make ci` **2301 passed / 100.00 %**, guard
  planted (old keys → `KeyError`) and restored. Only WMT (earnings-gap-aware stop) and GOOG
  (correlation penalty) were substantive objections. 🪤 **Third instance of DL-104's disease** —
  invented fragment, absence-as-zero, unit-in-a-name — all three cost real orders; the class is
  worth one sweep of every value rendered into the debate, not three more point fixes.

Older sprints — **the two S176 deploys (`0.90.10`/`0.90.11`), the deliberation-constraint
measurement (`0.90.02`, DL-105) and the S166→S171 veto arc (`0.89.07`–`0.90.01`) →
[STATE-08.md](state-archive/STATE-08.md)**;
`0.89` and below → [STATE-07.md](state-archive/STATE-07.md); earlier arcs (S36→S146) in
[STATE-01…06](state-archive/INDEX.md). Full chronological list: `docs/sprints/README.md`.

## Now

**PROVEN RESULT - S179 (`sprint-179-a-fault-must-be-able-to-stop-being-an-incident`, branch/local).**
`open_incidents` now means unresolved `error`/`critical` Faults in the latest graph-run day, with
explicit append-only `FaultResolution` retirement; warning Faults remain queryable but do not pin
`healthy=false`. Both supervisor and dashboard paths call `kernel.fault_incidents`. Live proof on
the spine: before `healthy=False`, `open_incidents=2`, `pending_human_flags=0`, `Fault=6119`,
`FaultResolution=0`; after the audited sweep `healthy=True`, `open_incidents=0`, `Fault=6119`,
`FaultResolution=2`, all Fault statuses still `pending`, and both resolutions linked to one Fault.
Guards were planted and restored; final redirected `make ci` exited `0` with **2317 passed / 6
skipped / 100.00 %**, pip-audit clean, detect-secrets clean. **Not deployed:** fleet remains `s178`;
S179 changes the graph vocabulary pack by adding `FaultResolution`, so a deploy must carry code and
pack together. **Deferred, not hidden:** recurring stop-identity mismatch Faults are real
warning-level drop-sweep evidence and need their own execution fix.

## Next

**Ranked queue of record: [work-queue.md](work-queue.md)** — this section is the narrative around it, not a second ranking (🪤 collapsing the two is item (ii)).

**Ahead of the numbered list — one measurement now unblocked, and three questions raised and not yet
answered.**

**The measurement that reorders everything below it.** `0.90.02` made the `effort` tunable reach the
wire, so the two free latency levers are measurable for the first time. Sweep **`effort` down from
`max` first** — it is the only lever that costs nothing. Then `max_rounds` 2 → 1 **only if that is
not enough**: 🚨 its own `why` says *"debate must show more than one round in live proof"*, so one
round is **cutting the artefact under test to buy wall clock**, a recorded decision rather than a
knob. Build [S172](sprints/sprint-172-independent-debates-run-independently.md) **only if both
together still miss** — full ordering and the arithmetic in [DL-105](design-log.md)'s amendment.
The sweep's first point is **done** — `effort` `max` → `high`, live since 2026-08-12 — and it
cost three fail-opens before `request_timeout_seconds` went 30 → 60, **now proven at 0 fail-opens**
(table under *Now*). The two levers are
**coupled**: raising effort lengthens the peer-call tail into a fixed timeout. Measure both
together or not at all.

**Undecided, recorded so they are not re-derived** — all raised 2026-08-11, none actioned:
**(i)** amend S172 — its stated reason for excluding `max_rounds` is unsound (the sum-of-latency ÷
span ratio is invariant to call count), and its build-trigger belongs in the spec;
**(ii)** collapse to one ranked queue — the operator's out-of-repo `debt.md` table is the best
"what next" artefact in the project and is a third live tracker; folding its *shape* into this
section would delete a tracker rather than add one; **(iii)** stop pinning version numbers in sprint
specs (*"next available PATCH/MINOR at merge"*) — after three renumberings in one day.

1. 🚨 **Close the loop on `critical` Flags, so `healthy` can mean something again.** A **fix**.
   47 unresolved critical Flags since 2026-07-08 pin `healthy=false` and `pending_human_flags=47`
   forever. A divergence that reconciliation has already adopted should resolve its own Flag; the
   backlog needs a one-off sweep behind that. 🪤 **Retracted, 2026-08-15:** this item previously
   claimed the graph had the book wrong and ranked #1 for that reason. It did not — graph and broker
   matched 19/19. The AVGO `overturn` was a **false premise**, not a data defect (see item 2).
2. 🪤 **Sweep the debate context for the same class — now FOUR instances, packaged as [S177](sprints/sprint-177-every-number-names-its-unit.md)** (2026-08-15). The fourth
   is `max_sector_pct`'s `deployed`: `SectorBook.__init__` seeds `_names` from held positions but
   **never seeds `_deployed`**, so `deployed` counts only *this batch* (GOOGL's `deployed=687.05` is
   exactly GOOG's `order_cost` moments earlier). `deployed=0.00` beside `existing_sector_names=2`
   is correct and unreadable, and it cost the AVGO overturn. 🚨 **Same code is also a latent gate
   defect** — the dollar sector cap never sees held positions, so across days sector exposure can
   pass 30 % unnoticed; masked today only because `max_names_per_sector=3` binds first. Every value rendered into the packet should be
   checkable against what the reader will assume it means: right unit, right period, right scope.
   **Not yet a spec.** This is the highest-value item once the divergence is settled.
3. **~~DL-104 (a) — the invented ATR fragment~~ — DONE.** S175, `0.90.08`, **deployed `s176a`
   2026-08-15**. `_atr_pct`/`_atr_fragment` deleted. Cost, measured before the fix landed: the AMZN
   and MDLZ vetoes on `sched-2026-08-14`.
4. **~~DL-104 (b) — batch/portfolio absence~~ — DONE.** S175, same deploy. Cost, measured: the AVGO
   `overturn` plus the CSCO and GOOGL `revise`s on `sched-2026-08-14`.
5. **~~DL-112 — sentiment counts name their unit~~ — DONE.** `0.90.11`, **deployed `s176b`**.
   Cost, measured: the XOM veto and part of AMZN's.
6. **DL-104 (c) — the analyst's hardcoded SMA-200 rationale.** The summary string always names
   SMA-200 while `indicators.sma_distance` returns `None` below its period. 🪤 **The bars gap
   underneath it is CLOSED** — S174 ships 203 bars, so SMA-200 now computes; what survives is the
   rationale asserting an input without checking it exists. Same class as item 5.
7. **DL-104 (d) — a real advisory/binding switch**, so *advisory* is a declared posture rather than a
   grace that happens to expire. Every run writes a truthful but uninformative `error` fault, which
   trains the operator to read a real fault as noise.
8. **S170 — one LLM adapter in `kernel/`**
   ([sprint-170](sprints/sprint-170-one-llm-adapter-in-the-plumbing.md)). Capability, not repair, so
   it ranks below the fixes — but it gives the operator the same provider switch the deliberator has,
   while the Anthropic key is usage-limited to 2026-09-01.
9. **Remaining hardening rows: N, O, R.** **N** — delegated coding agents default to
   `danger-full-access` with no approval prompt; the protection is the operator remembering a CLI
   flag. **O** — S157's 101 missing law-clause test-plan rows, then flip assertion E in
   `scripts/check_law_coverage.py` to hard fail. **R** — three guards covered only by CI lacking the
   extras. 🪤 **Row P is closed** (S176, deployed); **row Q is closed** (the `s176a` full `up`
   returned `[OK]` on all 16 env-preservation checks after refusing once — see Recent).

## Pointers

Product `docs/PRD.md` · architecture `docs/architecture.md` · phases `docs/build-plan.md` · closed
decisions `docs/decisions/INDEX.md` · open threads `docs/design-log.md` · "does it work"
`docs/laws/{ledger,drift-register,functionality-checks}.md` · per-agent `agents/<name>/mission.md`.
