# Project State

**Last updated:** 2026-08-15 17:27 AEST · **Version:** 0.90.12 · **S177 local proof green: debate-packet numbers now name unit/scope, without changing PM sector-gate behaviour.**

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

- **Two deploys, and S169's guard proved itself by refusing (2026-08-15).** `s176a` = `0.90.10` via
  full `up` (env change), then `s176b` = `0.90.11` via image-only retag (pack unmoved). **Row Q
  closed:** the three `DELIBERATOR_*_MODEL=gpt-5.5` overrides are gone, so the models resolve from
  `DELIBERATOR_LLM_PROVIDER=openai` and S169's switch is the live path instead of a masked one.
  The first `up` **refused** and named all three keys — DL-100's defect is now closed by
  demonstration, not only by test. Verified both times: 16/16 on tag, 16/16 `Succeeded`, KEDA
  `min=0`/1 rule on every app, cron `30 22 * * 1-5`, other tunables intact. `DeployRecord`
  `…:s176b:439111b7`. 🪤 **`pwsh script.ps1 -DropEnv A,B,C` silently passes one literal string**
  (`-File` semantics); the call operator `& ./infra/deploy-agents.ps1` is what binds the array.

- **The audit-clause sweep, and one guard that had never been exercised (docs + test-only,
  2026-08-14 — [DL-111](design-log.md)).** The queue's *"17 audit-type rows"* measured **13**; **9**
  were green and in scope and **5 were demoted**, the cited test proving something adjacent to the
  clause each time. Ledger reconciled (analyst 24→23, execution 32→30, provider 17→16). Two are
  **false in code**, now drift rows: **DRIFT-039** `portfolio_state_snapshot` exists nowhere in the
  codebase; **DRIFT-040** nothing records which vendor served a fact. 🪤 Four of the
  five cite a test on the **pub/sub path production does not use** — the S174 shape in the ledger,
  and greppable, so the next sweep is cheap. The gate then caught the same disease in a test:
  `test_a_missing_sdk_raises_configuration_error` patched `builtins.__import__` while the adapter
  calls `importlib.import_module`, which **does not consult it** — so it passed only where the SDK was
  absent. Fixed, parametrised over both vendors, proven **with the SDKs installed** and planted out.
  **No bump** (test-only). New **row R**: three more guards are covered only by CI lacking the extras.

- **A deploy now keeps the switches it was given (fix, `0.90.10`, 2026-08-14 — closes
  [DL-100](design-log.md), [S169](sprints/sprint-169-one-switch-and-a-deploy-that-keeps-it.md)).**
  The three model tunables resolve from the **provider**, so `DELIBERATOR_LLM_PROVIDER` is the whole
  switch, and `role_models` records the resolved name — asserted on the written node. Operator
  tunables and the cron move into `orchestration/packs/trading_tunables.json`; `up` sweeps every
  agent **before its first create** and refuses, naming any live env key it would drop (`-DropEnv`
  to drop one deliberately). `make ci` **2299 passed / 100.00 %**, both planted failures watched.
  🪤 **Not deployed** — the live half (row Q) is owed at the next full `up`, which must also
  `-DropEnv` the three `DELIBERATOR_*_MODEL=gpt-5.5` overrides or the fleet keeps masking the new path.

Older sprints — **the deliberation-constraint measurement (`0.90.02`, DL-105) and the S166→S171
veto arc (`0.89.07`–`0.90.01`) → [STATE-08.md](state-archive/STATE-08.md)**;
`0.89` and below → [STATE-07.md](state-archive/STATE-07.md); earlier arcs (S36→S146) in
[STATE-01…06](state-archive/INDEX.md). Full chronological list: `docs/sprints/README.md`.

## Now

**PROVEN RESULT — S177 (`sprint-177-every-number-names-its-unit`, local).** Debate-packet values
now render with unit/scope labels or an explicit source-owned unknown-units boundary; `SectorBook`
approval behaviour stayed unchanged. Proof: three planted label-boundary defects failed and were
restored; final redirected `make ci` exited `0` with **2304 passed / 4 skipped / 100.00 %**,
pip-audit clean, detect-secrets clean; graph vocabulary pack unchanged (`13c0e3a0ef38...`). **Not
fixed by design:** whether `max_sector_pct` should include held portfolio sector dollars; filed in
DL-113 rather than folded into this label sweep.

**Read this first if you are picking the project up.** The fleet is on **`s176b` = `0.90.11`**
(`439111b7`, 2026-08-15) — **16/16 apps + the dispatcher job, nothing merged-but-undeployed**.
S175, S176, S169 and DL-112 are all live. The next scheduled fire is **Monday 22:30 UTC**
(`sched-2026-08-17`); 08-15 is a Saturday and the cron is `30 22 * * 1-5`.

**The 60 s timeout mitigation is PROVEN, not predicted.** `sched-2026-08-14`, measured on the spine:

| run | n | median | p90 | max | > timeout |
| --- | --- | --- | --- | --- | --- |
| `sched-2026-08-10` (pre-`effort`, 30 s) | 90 | 11.4 | 16.4 | 23.0 | 0 |
| `sched-2026-08-13` (`effort=high`, 30 s) | 32 | 15.1 | 30.1 | 39.1 | **4** |
| `sched-2026-08-14` (`effort=high`, **60 s**) | 45 | 12.8 | 34.6 | **46.2** | **0** |

`failed_open_count 0`, `debate_coverage 1.0` (9 verdicts / 9 approvals), zero `llm unavailable`.
The prediction held. 🪤 **The margin is thin** — max 46.2 s against a 60 s ceiling, and 46.2 s would
have failed open under the old 30 s. `effort=high` moves the tail, so the tail is what to watch.

**`sched-2026-08-14` — 8/8 stages, ACCEPTANCE UNPROVEN, and the funnel closed at the veto.**
99 tickers × **203 bars** (S174 holding in production), 23 survived the scanner, 30 scored,
9 PM-approved, **1 order submitted**. Acceptance reads UNPROVEN rather than FAIL because the PFE
order (38 sh @ $26.79) is still `pending`, correctly queued for Monday's open. **The 8 vetoes are
the story, and 6 of them were false** — see the DL-112 entry above. Monday is the first run where
the veto-context fixes are actually under the fleet.

**The `sched-2026-08-14` divergence is RESOLVED — reconciliation worked** (`/reconcile-broker`,
2026-08-15). Graph active positions and broker holdings agree **exactly, 19/19**: AMD/DOW/VZ were
**adopted** from broker truth mid-run and each got a protective stop at 22:54; AMZN/AVGO are
correctly marked `broker_absent`. 19 stops cover 19 positions. **No broker action was needed.**

🚨 **`healthy` has been permanently false since 2026-07-08, and that is the real finding.**
`compute_health` is `open_incidents == 0 and critical_flags == 0`; there are **47 unresolved
`critical` Flags** — every run raises one at start and nothing ever resolves it (only `warn` flags
have ever been resolved, 7, all mid-July). `pending_human_flags=47`. The signal carries no
information: a genuinely new critical condition cannot move it. Reconciliation auto-adopts broker
truth but never closes the loop on the Flag it raised.

## Next

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
