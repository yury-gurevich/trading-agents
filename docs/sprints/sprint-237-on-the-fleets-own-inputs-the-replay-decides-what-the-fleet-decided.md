<!-- Agent: planning | Role: sprint handover -->
# Sprint 237 — on the fleet's own inputs, the replay decides what the fleet decided, and every difference has a named cause

**Phase:** Etalon-first continuous improvement (DL-19) · next leg P17, item **E17.4** (fidelity)
**Branch:** `sprint-237-the-replay-decides-what-the-fleet-decided`
**Status:** BUILT · the return, 2026-09-27: R1–R10 addressed on synthetic fixtures; `make gate-ran` and the live export are owed to the planner (see *Closeout* and *Return notes*)
**Version:** *next available MINOR at merge*
**Effort:** M
**Decisions:** [DL-237](../design-log.md) (the fidelity bar, re-cut: **settled, do not reopen**) ·
[DL-232](../design-log.md) (the replay is price-only) · [DL-233](../design-log.md) (live reads IEX
volume; fixed elsewhere, **not** here) · [DL-234](../design-log.md) (the harness) · ADR-0029 (only
`overturn` blocks) · work-queue **82** · the builder records its decisions as **DL-238**

> **Why this bump kind.** The fleet gains nothing. The repository gains a capability it did not have:
> exporting what each live run saw and decided, and replaying it stage by stage against the harness.
> New capability → MINOR.

**Builder:** Codex. **Your worktree has no `.env` and no network.** Every proof is on synthetic
fixtures. The live export and the verdict are the planner's, after merge. **If a number you measure
differs from one written here, stop and report. Do not adjust and continue.**

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report, never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: the scanner's, analyst's and PM's **OUT** and **IDM** clauses (you call their
domain functions and must not re-implement them), the reporter's **`RPT-OUT-07`** (the one return
metric), and **`GRAPH`/`kernel` read paths** (the exporter only reads).

### The rule

1. **Before writing code**, read every law file in the map below: whole file, first time.
2. Read each agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, record it and add a `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring**.

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Expected answer: No.** Everything lives in `scripts/` and `tests/`. Scripts may import agents (the
`backtest_proposal.py` and S235 precedent); agents never import each other or scripts. If you find you
need an agent or contract change to make a stage replayable, **stop and report**: that is a finding,
not a fix to make here.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `scripts/fidelity_export*.py` (new) | `docs/laws/conventions.md`; `kernel` graph read API; ADR-0014 | Read-only against the spine: **no `merge_node`, no `add_edge`**. Vendor data (IEX bars) leaves the repo |
| `scripts/fidelity_*.py` (new): stage replays | `agents/scanner/laws/laws.md`, `agents/analyst/laws/laws.md`, `agents/portfolio_manager/laws/laws.md` + each `test-plan.md` | Each stage is the fleet's own domain function, called with the inputs the live agent was given. No local scoring, filtering or sizing logic |
| `scripts/replay_runner.py` (199 lines) + a split | same, plus `agents/reporter/laws/laws.md` | `RPT-OUT-07`: returns only through `calculate_performance`. The file is at the size edge: **split before you add a line** |
| `scripts/replay_day.py` | PM laws (concentration caps) | `position_values`: see Trap 1 |

⚠️ **The one invariant: the comparison never judges itself by a formula of its own.** The fleet's
functions produce both sides of every comparison. If you catch yourself writing a filter, a score, a
sizing rule or a return, stop.

---

## Goal

At merge, one command exports what each scheduled live run **saw** (its stored `MarketData` snapshot,
regime, book) and **decided** (candidates, recommendations, PM approvals and rejections, deliberator
vetoes, execution outcomes, fills). A second command replays every exported session **stage by stage on
those same inputs** through the harness and writes, per session and per stage, whether the replay
decided what the fleet decided, with a named cause for every difference. The same tool then swaps the
live inputs for the cache's one at a time (SIP volume, no fundamentals, no news, no earnings dates,
cache bars) and reports how much each swap moves the decisions. That is the account DL-232 and DL-233
owe. The verdict itself is the planner's, on the live export, after merge.

## Why (context)

E17.3 (S235) replays ten years and returns **+217.9 %** against exposure-matched SPY's **+232.2 %**.
Nothing yet shows that this number is the pipeline's and not the harness's. The plan's bar
(*≥ 90 % approved-order membership against live*) cannot be applied as written: the replay is
price-only by decision (DL-232), and live has run on IEX volume that drops 63 % of the universe
(DL-233). A replay-vs-live membership number would fail on those two known causes and say nothing
about the harness. [DL-237](../design-log.md) re-cuts the bar into three layers. **Without this the
backtest is fiction; if the harness layer fails, P17 stops here and the gap becomes the work.**

The S235 merge review also named residue this sprint must close. (a) `sessions.csv` lacks per-session
candidates, recommendations, approvals and rejections. (b) An 84-minute run prints nothing until it
ends.

### Measured, 2026-09-27 (planner, live spine, main checkout with `.env`) — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Scheduled runs with a stored `MarketData` snapshot | **56**, `sched-2026-07-07` → `sched-2026-09-25` (57 `RunRequest`s) | *[measured 2026-09-27]* `nodes` where `label='MarketData'` and key `market-data:sched-*` |
| What a snapshot holds | `bars` (OHLCV, **IEX volume**), `benchmark`, `fundamentals`, `news`, `sentiment`, `sectors`, `earnings`, `earnings_horizon_days`, `quality`, `provenance` | *[measured]* `sched-2026-09-25`: 19,894 bars, 203 SPY bars, 99 fundamentals, 99 news, 99 sectors, 50 earnings dates, `sentiment` empty |
| Snapshot completeness over the window | `07-07`…`07-15` (7 runs): feeds degraded, no fundamentals or news. `07-20`…`08-12`: ~40 bars per name. From `08-13`: ~203 bars per name. **`benchmark` empty before `09-04`** (16 runs have it) | *[measured]* per-run counts of each snapshot key |
| Lineage chain | `RunRequest` –`INGESTED_BY`→ `MarketData` –`SCANNED_BY`→ `ScanRun` –`ANALYZED_BY`→ `AnalystRun` –`EVALUATED_BY`→ `PMRun` –`DELIBERATED_BY`→ `DeliberationRun`, –`EXECUTED_BY`→ `ExecutionRun`; `RunRequest` –`REFRESHES`→ `BrokerPositionSnapshot`; `OrderIntent` –`EMITTED_BY`→ `PMRun`; `Rejection` –`REJECTED_IN`→ `PMRun` | *[measured]* `edges` grouped by `(parent_label, edge_type, child_label)` |
| Stored stage outputs | `ScanRun.candidate_set` (all 78), `filter_trace` (50 of 78); `AnalystRun.recommendation_set` (full, with `quant_metrics` including `technical_score`, `fundamental_score`, `sentiment_score`, `composite_score`, `confidence`); `OrderIntent` (ticker, action, quantity, stop/target pct, est. price); `Rejection` (reason, `gate_report` on 1,059 of 1,187) | *[measured]* property-key census per label |
| Book per run | `BrokerPositionSnapshot` for **all 57** scheduled runs: `holdings` (ticker, quantity, avg entry, market value), account cash/equity | *[measured]* |
| How live PM builds its book | `cash` = account **equity**; `position_values` = each holding's market value from the snapshot | *[measured]* `agents/portfolio_manager/graph_portfolio.py:34-56` |
| How the replay builds it | `cash` = equity; **`position_values={}`** | *[measured]* `scripts/replay_day.py` (the `PortfolioState(...)` call) |
| Recent PM volume | 0–4 approvals, 21–27 rejections per scheduled session (`09-14` → `09-25`) | *[measured]* `PMRun.approved_count` / `rejected_count` |
| Deliberator vetoes | `DeliberationRun.vetoed_tickers` present on all 81 PM runs; e.g. `09-16`: 4 approvals, 4 vetoed, 0 submitted | *[measured]* |
| Deploys during the window | **~35** image changes (`DeployRecord`, `s177` → `s232`) | *[measured]* |
| Decision-code distance from `main` per deploy | `git diff --stat <deploy sha> main` over `agents/{scanner,analyst,portfolio_manager}`, `agents/provider/domain`, `agents/execution/order_tolerance.py`, `contracts/`, `trading_tunables.json`, `orchestration/history_window.py`: s198 **63 files**, s214 32, s219a 28, s225 (`fe26574e`, deployed 2026-09-22 13:43 UTC) **11**, all of them `contracts/` or `laws.md`; s232 **0** | *[measured]* |
| Clean sessions (decision code equal to `main`) | `sched-2026-09-22` … `09-25` (**4**) plus every run from `sched-2026-09-28` on `s232` | ⚠️ *[ASSUMED]* that the 11 `contracts/` diffs since s225 (`stop_width.py`, `positions.py`, `common.py`, …: S227/S230/S232 moved stop placement and the substrate) do not change a scanner, analyst or PM decision. **The stage-isolated result settles it:** a difference on those four sessions caused by one of those files is named, not hidden |
| Harness tests today | `tests/test_replay_*.py`, fixtures in `tests/replay_fixtures.py`; `replay_runner.py` **199** lines, `replay_marks.py` 194, `replay_ledger.py` 186, `replay_day.py` 177 | *[measured]* `wc -l` |

---

## Scope — and what is deliberately NOT here

### Part A — the S235 residue

1. **`sessions.csv` carries the pipeline's counts.** Per session: `members`, `candidates`,
   `recommendations_buy`, `recommendations_hold`, `recommendations_sell`, `approved_buy`,
   `approved_sell`, one `rejected_<reason>` column per PM rejection reason seen in the run (header is the
   sorted union, `0` where absent), plus the existing expiry and gap columns. Counts come from the
   `ReplayDayResult` objects, not recomputed.
2. **A progress line.** To **stderr**, never into an output file: one line every `--progress-every`
   sessions (default 20) and at the end: session date, `i/n`, elapsed seconds, equity. Outputs stay
   byte-identical with and without it (A17 of S235 still holds).
3. **Split `replay_runner.py` first** (199 lines). Suggested: the per-session loop body into
   `replay_session.py`; the counters into `replay_counters.py`. Every module < 200 lines, no baseline
   entry.

### Part B — the live export (read-only)

4. **`scripts/fidelity_export.py export --start --end --out <dir>`.** For each `RunRequest` whose
   `run_id` is `sched-YYYY-MM-DD` in the range (not `manual-*`, not `*-resume-*`, not `resume-link:*`
   keys), follow the lineage chain above and write **one JSON per session** holding:
   - `run_id`, `session` (the date), the `DeployRecord` in force when the run's `ScanRun` was created
     (the latest `deployed_at` before `ScanRun.created_at`: tag and SHA);
   - the `MarketData.snapshot` as stored, and the run's `RegimeContext` (label, VIX, base parameters);
   - the `BrokerPositionSnapshot` the run refreshed (holdings with market values, account equity);
   - the held-stop inputs the analyst was given: the held tickers and any `BrokerStopOrder` refs the
     live analyst read. **Read `agents/analyst` to learn exactly what it read, and export that.** What
     cannot be reconstructed is listed in the session's `not_persisted` list, never guessed;
   - the live outputs: `ScanRun.candidate_set` and `filter_trace`, `AnalystRun.recommendation_set`,
     every `OrderIntent` and `Rejection` of the `PMRun`, `DeliberationRun.vetoed_tickers` and verdicts,
     `ExecutionRun` counts, and each approved buy's `Fill` status and price.

   Read through the kernel graph store (`kernel/graph_env.py`), never raw SQL, so the test runs on the
   in-memory store. **The output directory is refused if it is inside the worktree**
   (`refuse_worktree_out`): the bars are vendor data and the repo is public.
5. **A resumed session is exported as the fleet finished it.** When a stage node carries
   `linked_from_key`, follow the link. The session's JSON records `resumed: true`.

### Part C — the fidelity replay

6. **`scripts/replay_fidelity.py run --export <dir> [--cache <dir>] --out <dir>`**, three layers per
   session.

   **Layer 1: harness fidelity, stage-isolated, on live inputs.** Each stage gets the **live** inputs
   of that stage, never the replay's own upstream output, so a difference is located in one stage:
   - *scanner:* the snapshot's bars, benchmark, earnings and `earnings_horizon_days` → `apply_filters`
     → `rank_survivors` (cap from the settings) → compared with the live candidate list (ticker set
     **and** rank order) and, where stored, the live `filter_trace` verdict per ticker;
   - *analyst:* the **live** `CandidateSet` plus the snapshot as `MarketData` (fundamentals, news,
     sectors included), the live regime and the live held book → `scoring_universe` →
     `score_candidates` → `split_decisions` → compared per ticker: action, `exit_trigger`, `confidence`
     (absolute difference ≤ 1e-9), `technical_score`, `suggested_stop_pct`;
   - *PM:* the **live** `RecommendationSet` plus the live book, with `position_values` from the
     snapshot's market values (Trap 1) → `evaluate_recommendations` with the settings the harness builds
     → compared per ticker: approved or rejected, the rejection reason, quantity and stop pct.

   **Layer 2: input attribution, same code, chained.** Starting from the live inputs, run the three
   stages chained and swap **one input at a time, cumulatively, in this order**, recording candidates,
   recommendations and approvals at each step: (0) live snapshot; (1) volume → the cache's SIP volume for
   the same dates; (2) fundamentals removed; (3) news removed; (4) earnings dates removed; (5) bars → the
   cache's bars over `declared_lookback_days`. Step 5 is the S235 replay of that session, anchored on the
   live book. Report each step's Jaccard overlap with step 0 for candidates and approvals, and the
   tickers that entered and left. The order is fixed so the planner's report reads the same way each
   time. It is an attribution by sequence, not a decomposition claim.

   **Layer 3: from approval to fill, live only.** Per session, from the export: PM approvals → vetoed
   by the deliberator (`overturn`) → submitted → dropped or rejected by execution → filled or expired.
   Counts only; no replay.

7. **Outputs, outside the repo:** `layer1.csv` (session, stage, ticker, live, replay, match, cause),
   `layer2.csv` (session, step, candidates, approvals, Jaccard, entered, left), `layer3.csv`,
   `summary.json`, and a `fidelity.md` that states the verdict of the pre-registered bar in DL-237's
   words.
8. **Every Layer 1 difference carries exactly one cause**, from a closed list:
   `code_changed:<path>` (the session's deploy SHA differs from the replayed code in that decision
   file; take the file from `git diff --name-only <sha> HEAD` over the decision paths, so the tool
   needs git but no network), `not_persisted:<field>` (the input the live stage used is not in the
   export), `harness:<what>` (the replay built an input differently from live), or `unexplained`. A
   `harness:` cause found on the synthetic fixture is **fixed in this sprint, not carried**.
9. **The verdict is computed, not written.** `summary.json` holds, over **clean sessions only** (no
   `code_changed` cause possible: the deploy SHA's decision paths equal `HEAD`'s), the pooled
   per-stage agreement, its denominator, the counts per cause, and the bar's verdict (`PASS`, `FAIL` or
   `INSUFFICIENT`) exactly as DL-237 defines it. Non-clean sessions are reported beside it and never
   pooled into it.

### Out of scope (do NOT build this sprint)

- **Fixing item 89** (live IEX volume). Layer 2 measures it; the fix is the provider's, elsewhere.
- **Replaying the deliberator.** It is an LLM debate; Layer 3 counts what it did. `$0` LLM.
- **A free-running P&L comparison against the live account** as a bar. The planner runs the S235
  replay over the live 99 from 2026-08-10 and places its `calculate_performance` beside the reporter's
  live series in the closeout as **context only**: the two books diverge from the first different
  fill, so the number carries no bar.
- **Old code.** No checkout of past deploys, no replay under historical code. Non-clean sessions are
  attributed, not reproduced.
- **No `laws.md` edit, no `contracts/` change, no ADR reversal.**

### The road not taken (LAW-06)

- **The plan's bar as written (≥ 90 % replay-vs-live approval membership).** Rejected in DL-237: it
  would fail on two causes already known and decided (price-only, IEX volume) and could not tell a
  harness defect from either.
- **Chained end-to-end comparison only.** Rejected: an early difference (one candidate) cascades, and
  the report could not say which stage diverged. Stage isolation localises; Layer 2 chains on purpose.
- **Replay each session under the code deployed that night** (a worktree per deploy SHA). Rejected: ~35
  deploys, harness modules that did not exist then, and it answers a question about old code that P17
  does not ask.
- **Raw SQL in the exporter.** Rejected: untestable without Postgres, and it bypasses the store's
  node decoding.
- **Commit the export as a fixture.** Rejected: it holds IEX bars (vendor data) and the repo is public.
  The fixture is synthetic.

---

## The design decisions this sprint has to make

Record them in `docs/design-log.md` as **DL-238** with rejected alternatives BEFORE implementing.

1. **How each stage's live inputs are rebuilt as contract objects** from the export: which constructor,
   and what is defaulted. Every default is a named `not_persisted` entry or a documented equality.
2. **The analyst's held-stop and active-stop inputs**: what live read (read the analyst's serve path),
   and how the export carries it.
3. **Which settings each stage runs with.** Current code plus the pack (`build_effective_settings`), for
   every session. Non-clean sessions differ by construction and are attributed.
4. **The clean-session test**: which paths define "decision code", and how the tool computes it from
   git.
5. **Module boundaries**, each < 200 lines.

🪤 **DL-237 is taken by the planner's bar; take DL-238, then re-check at merge.**

---

## Blast radius — measured 2026-09-27

| What | Detail |
| --- | --- |
| Files changed | `scripts/replay_runner.py` (199, split), `scripts/replay_day.py` (177: `position_values`; its `ReplayDayResult` may carry counts), `scripts/replay_outputs.py` (80); new `scripts/fidelity_export*.py`, `scripts/replay_fidelity*.py`; tests under `tests/` |
| Agents affected | none; scripts import scanner, analyst, PM, provider domain and reporter functions, as S235 does |
| Contract change? | no |
| Graph vocabulary change? | no; the exporter only reads |
| New env keys / tunables | none (`POSTGRES_DSN` is read by the existing graph env when the planner runs the export) |
| Deploy implication | **none**: scripts are not in any image |

---

## Steps, in order

1. **Read the laws** and write the Law reading record.
2. **Record DL-238.**
3. **Split `replay_runner.py`** with no behaviour change: S235's tests stay green, untouched.
4. **Plant the failing tests first** (A1, A3, A5 at least) and paste the red output.
5. **Implement** Part A, then B, then C.
6. **Prove the guards can fail (DL-70)**: each plant in the test plan, red, restored.
7. **`make ci` green**, redirected to a file, never piped.
8. **Fill the handback sections.**

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 identical inputs agree | a synthetic export whose live outputs were produced by the fleet's own functions on its own inputs | Layer 1 reports 100 % match on all three stages, zero causes; verdict `PASS` |
| A2 | a changed live output is caught and located | A1's export with one live recommendation's confidence moved by 0.01 | exactly one Layer 1 row mismatches, stage `analyst`, that ticker; cause `unexplained`; scanner and PM stages still 100 % (**stage isolation**: PM ran on the live recommendation set) |
| A3 | 🪤 **Trap 1**: the book's market values reach the PM | an export whose PM decision depends on a sector or cluster cap filled by existing holdings | the replay's PM approves or rejects as live did; plant `position_values={}` → red |
| A4 | `not_persisted` is named, not guessed | an export missing `benchmark` (as live before `09-04`) | the scanner row's cause is `not_persisted:benchmark`; no default benchmark is invented |
| A5 | `code_changed` needs git evidence | a session whose deploy SHA differs from `HEAD` in `agents/analyst/…` (a tiny git repo in `tmp_path`) | the session is non-clean, its differences carry `code_changed:<that path>`, and it is **not** pooled into the verdict |
| A6 | the verdict follows DL-237 | pooled fixtures at 89 %, 90 %, and a denominator below the floor | `FAIL`, `PASS`, `INSUFFICIENT` respectively; an `unexplained` difference on a clean session makes `FAIL` whatever the percentage |
| A7 | Layer 2 order and content | a fixture where only volume differs between the snapshot and the cache | step 1 changes candidates; steps 2–5 change nothing further; Jaccard values exact |
| A8 | Layer 3 counts | an export with 4 approvals, 2 vetoed, 1 dropped, 1 filled | the four counts, per session |
| A9 | exporter reads, never writes | the in-memory store, wrapped to count writes | 0 `merge_node`, 0 `add_edge` calls; one JSON per `sched-*` run; `manual-*` and resume keys excluded; a resumed session followed through `linked_from_key` |
| A10 | outputs refuse the worktree | `--out` inside the repo, for both commands | `ValueError` naming the path |
| A11 | `sessions.csv` carries the counts | S235's fixture run | the new columns equal counts taken from the day results; reasons header is the sorted union |
| A12 | progress goes to stderr only | S235's fixture run with and without progress | output files byte-identical; stderr lines at the interval and at the end |
| A13 | S235 unchanged | S235's whole replay test suite | green, untouched, after the split |

---

## Success factors

- [ ] Two commands exist: `fidelity_export.py export` and `replay_fidelity.py run`, both refusing
      worktree outputs.
- [ ] Layer 1 is stage-isolated, and every difference carries exactly one cause from the closed list.
- [ ] The verdict in `summary.json` is computed over clean sessions only, as DL-237 defines it.
- [ ] Layer 2 swaps in the fixed order; Layer 3 counts from the export only.
- [ ] `sessions.csv` carries the pipeline counts; progress goes to stderr; S235's tests are untouched and
      green.
- [ ] Trap 1 is fixed in `replay_day.py` (`position_values` from the book), with its guard planted.
- [ ] No contract, agent or law change; the exporter makes no graph write.
- [ ] DL-238 recorded with rejected alternatives.
- [ ] Every guard planted, watched to fail, restored, stated per guard.
- [ ] Every touched module < 200 lines; no baseline entry added.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **Trap 1: the replay's PM does not see what the book is worth.** Live passes `position_values` from
the broker snapshot (`graph_portfolio.py:34`); the replay passes `{}`. Any cap that sums held value
(sector, cluster, position) then sees an empty book. This also affects every S235 replay, including the
ten-year smoke run, so **fix it in `replay_day.py` for both paths** (the ledger knows each line's
latest close) and say in the handback that the smoke number predates the fix.
🪤 **Trap 2: feeding the replay's own upstream output into the next stage** turns one scanner
difference into twenty analyst "differences". Layer 1 feeds each stage the **live** upstream; only
Layer 2 chains.
🪤 **Trap 3: `benchmark` is empty in the snapshots before `2026-09-04`.** Live computed relative
strength from somewhere; find where, or name it `not_persisted`. Never substitute the cache's SPY in
Layer 1.
🪤 **Trap 4: a snapshot's `bars` cover the declared history window**, not the analyst's own lookback
(DL-233's recorded note: graph-pull runs ship ~203 bars). Pass them as live did; do not re-window
them in Layer 1.
🪤 **Trap 5: two runs on one date.** `09-16` and `09-24` each have a `manual-*` run beside the
scheduled one. Only `sched-*` runs are sessions; the book the scheduled run saw is its own
`BrokerPositionSnapshot`, not the day's latest.
🪤 **Trap 6: a matching count is not a matching decision.** Compare per ticker (and rank for
candidates), never "live approved 2, replay approved 2".
🪤 **Trap 7: `confidence` equality.** Serialisation through JSON may perturb the last bits; the
tolerance is 1e-9 absolute, stated once, used everywhere. A difference above it is a difference.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass, no baseline entry.
  📌 Current sizes: `replay_runner.py` **199**, `replay_marks.py` **194**, `replay_ledger.py` **186**,
  `replay_day.py` **177**, `replay_outputs.py` **80**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: the 1e-9 tolerance, the progress interval and the DL-237 floor are named constants
  with a comment citing DL-237 (scripts are not `tunable()` territory).
- `make ci` **every step** green, **100.00 % coverage floor**, redirected to a file, never piped.
- Version bump MINOR, `uv.lock` staged with it. 🪤 In a Codex sandbox `uv lock` may need the network:
  if it fails, say exactly how `uv.lock` was touched and leave it owed.
- Secrets never through the worktree. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0** from the worktree whose `HEAD` is
   the commit; the printed SHA equals `git rev-parse HEAD`. Check the branch ref's open code-scanning
   alerts before merging (the gate reads `main`'s).
2. Merge to `main`, tag, push. Post-merge CodeQL green.
3. **Planner, main checkout with `.env`:** `fidelity_export.py export --start 2026-07-07 --end <last
   session> --out <OneDrive>\trading-agents-data\fidelity\export`, then `replay_fidelity.py run`
   against it and the cache. Wait for at least `sched-2026-09-28` to widen the clean set.
4. Record the verdict (`PASS` / `FAIL` / `INSUFFICIENT`) against DL-237 in the closeout and the
   design log. On `FAIL`, P17 stops: the named causes become the work.
5. **No deploy**: scripts are in no image.

---

## Handover — paste this to Codex

```text
Sprint 237 — trading-agents. Spec: docs/sprints/sprint-237-on-the-fleets-own-inputs-the-replay-decides-what-the-fleet-decided.md
Read the whole spec first. Branch: sprint-237-the-replay-decides-what-the-fleet-decided (from main).
Your worktree has no .env and no network: every proof is on synthetic fixtures. The live export is the planner's.

MUST RULE: read scanner, analyst, PM and reporter laws.md + test-plan.md, docs/laws/conventions.md and
drift-register.md BEFORE code. Fill the Law reading record first. Law-cycle answer expected: No
(scripts/ and tests/ only). If you need a contracts/ or agent change, STOP and report.

What to build:
A. S235 residue: split scripts/replay_runner.py (199 lines) FIRST with no behaviour change; sessions.csv
   gains members, candidates, recommendations_{buy,hold,sell}, approved_{buy,sell}, rejected_<reason>
   (sorted union); a progress line to STDERR every --progress-every sessions (default 20) and at the end;
   outputs byte-identical with or without it.
B. scripts/fidelity_export.py export --start --end --out: read-only through the kernel graph store (no
   raw SQL, zero writes). One JSON per sched-YYYY-MM-DD run (exclude manual-*, resume runs and
   resume-link: keys; follow linked_from_key for a resumed stage). Chain: RunRequest -INGESTED_BY->
   MarketData -SCANNED_BY-> ScanRun -ANALYZED_BY-> AnalystRun -EVALUATED_BY-> PMRun -DELIBERATED_BY->
   DeliberationRun / -EXECUTED_BY-> ExecutionRun; RunRequest -REFRESHES-> BrokerPositionSnapshot;
   OrderIntent -EMITTED_BY-> PMRun; Rejection -REJECTED_IN-> PMRun. Export the stored MarketData.snapshot,
   the RegimeContext, the book, what the analyst read for held stops, the deploy in force (latest
   DeployRecord before ScanRun.created_at), every live stage output, vetoes, execution counts, fills.
   Anything live used that is not stored goes in not_persisted, never guessed. Refuse --out inside the repo.
C. scripts/replay_fidelity.py run --export --cache --out, three layers:
   L1 stage-isolated on LIVE inputs (each stage gets the live upstream, never the replay's): scanner vs
      live candidates (set + rank + filter_trace); analyst vs live recommendations per ticker (action,
      exit_trigger, confidence |d|<=1e-9, technical_score, suggested_stop_pct); PM vs live intents and
      rejections per ticker (decision, reason, quantity, stop pct). Every difference gets exactly one cause:
      code_changed:<path> (git diff --name-only <deploy sha> HEAD over decision paths), not_persisted:<field>,
      harness:<what>, unexplained. A harness: cause you find is FIXED in this sprint.
   L2 chained, same code, cumulative swaps in this order: live -> SIP volume -> no fundamentals -> no news
      -> no earnings -> cache bars; Jaccard vs step 0 for candidates and approvals, tickers in/out.
   L3 live only: approvals -> vetoed -> submitted -> dropped/rejected -> filled/expired, counts.
   Verdict per DL-237 over CLEAN sessions only (deploy SHA's decision paths == HEAD); PASS/FAIL/INSUFFICIENT
   computed into summary.json and fidelity.md; non-clean sessions reported beside it, never pooled.

TRAP 1 (fix it): scripts/replay_day.py passes PortfolioState(position_values={}); live passes each
holding's market value (agents/portfolio_manager/graph_portfolio.py:34). Fix for both the replay and the
fidelity PM stage; plant {} and watch A3 go red. Say in the handback that S235's smoke numbers predate it.
Other traps: benchmark is empty in snapshots before 2026-09-04 (not_persisted, never the cache's SPY in L1);
snapshots ship the declared history window, don't re-window in L1; only sched-* runs are sessions; compare
per ticker, never counts.

DO NOT: write a filter, score, sizing rule or return of your own; replay the deliberator; check out old
code; commit any exported or vendor data (the fixture is synthetic); touch contracts/, agents/, laws.md;
add a module-size baseline entry; pipe make ci.

Record your decisions as DL-238 before implementing (DL-237 is the planner's bar). Plant each guard, watch
it fail, restore. make ci redirected to a file, exit 0, 100.00 %. Version: next MINOR, uv.lock with it (if
uv lock needs network, say so and leave it owed). Fill Law reading record, Test plan results, Closeout
(red run, green run, guards, line counts, make ci), Return notes; Status: BUILT. Push the branch.
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

*Re-read in full for the return (R1–R10), 2026-09-27, before the first code change of the return:
`agents/{scanner,analyst,portfolio_manager,reporter}/laws/laws.md` and `test-plan.md`,
`docs/laws/conventions.md`, `docs/laws/drift-register.md`; and, for the clauses Layer 3 counts by,
`DLIB-OUT-02`/`DLIB-OUT-04` and `EXEC-OUT-07`/`EXEC-STA-05`. Tree: the claude.ai cloud container,
`/home/user/trading-agents`, branch `sprint-237-the-replay-decides-what-the-fleet-decided`; no `.env`
exists in this tree.*

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| Part A: `replay_runner.py` split, `sessions.csv` counts, stderr progress (accepted, kept) | reporter `laws.md` + `test-plan.md`; conventions; drift register | `RPT-OUT-07` (returns only through `calculate_performance`), `RPT-NEV-02` | No new approach. Reading scope item 1 against the output found that an absent reason wrote a blank, not `0`: fixed and guarded (A11). |
| Scanner stage replay (Layer 1 and 2) | scanner `laws.md` + `test-plan.md` | `SCAN-IDM-01` (⬜: same `MarketData` → same `CandidateSet`), `SCAN-OUT-02`, `SCAN-OUT-06`/`07` (a skipped gate says so), `SCAN-NEV-02`, `SCAN-OBS-01` | Yes. The replay runs `scan_market_node` itself, so the universe and as-of come from the `MarketData` node as live read them. `SCAN-OUT-06` means an empty benchmark skips the beta gate rather than failing, so an empty stored benchmark is replayed as empty and named `not_persisted` only on evidence a benchmark was used (DL-238 D5). |
| Analyst stage replay and its held inputs | analyst `laws.md` + `test-plan.md`; `DRIFT-074` | `ANLZ-IDM-01` (🟩), `ANLZ-OUT-01`, `ANLZ-OUT-03`, `ANLZ-NEV-03`, `ANLZ-OBS-01` (⬜), `ANLZ-OUT-07`/`ANLZ-OBS-06` (the target estimate) | Yes. No clause names the held-stop check (`DRIFT-074`, still OPEN), so the only authority on what live read is `agents/analyst/run.py`: thresholds and refs from the graph at run time. They cannot be rebuilt as of the run without a formula of our own, so they are `not_persisted` (R7, DL-238 D4). |
| PM stage replay and the book | PM `laws.md` + `test-plan.md`; `DRIFT-036`, `DRIFT-039`, `DRIFT-065` | `PM-IDM-01`, `PM-IDN-01` ("the current portfolio state"), `PM-OUT-03`, `PM-NEV-04`, `PM-NEV-06`/`07`/`08`/`09` (deployed-capital denominators), `PM-OBS-01` (⬜, `DRIFT-039`) | Yes. Reading `PM-IDN-01` beside `graph_portfolio.py` showed the live PM values held names at adoption, not at the current mark; that is a finding (`DRIFT-079`, appended to the register), and the replay reproduces what live read rather than what the law intends (DL-238 D3). |
| Layer 3 counts | deliberator `DLIB-OUT-02`/`04`; execution `EXEC-OUT-07`, `EXEC-STA-05` | `vetoed_tickers` holds only `overturn`; `dropped` is distinct from `rejected`; `Fill.status` never changes, `broker_status` carries the outcome | Yes. Outcomes are read from `broker_status` and `drop_reason`, and `vetoed` counts `overturn` verdicts (R6). |
| Exporter read path and output refusal | conventions; drift register; the agent books above | `SCAN-OBS-01`, `ANLZ-OBS-01`, `PM-OBS-01` (reconstructable runs), `RPT-NEV-02` (read others' facts, write none) | No change: reads only through `GraphStore`, no `merge_node`/`add_edge` (A9 counts them), output refused inside the worktree (A10). |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No. The return
touches `scripts/`, `tests/`, this spec, `docs/design-log.md`, `docs/sprints/{README,INDEX}.md`,
`docs/STATE.md` and one appended row in `docs/laws/drift-register.md`. No `contracts/`, `agents/` or
`laws.md` file changes, and the tool adds no guarantee to any agent.

**Contradictions found between a law and this spec:** None. One tension is recorded rather than
resolved: R1 reads "`position_values` from the book", while the live PM reads the book's `Position`
facts, whose values are adoption-time marks. The replay follows what live read (R1's "as
`graph_portfolio.py` builds it"); DL-238 D3 and `DRIFT-079` carry the reasoning.

**Laws found silent where a decision was needed:** (1) the analyst's held-stop check (`DRIFT-074`,
OPEN, unchanged); (2) the PM's valuation of held names: no clause says whether "current portfolio
state" means the current mark, and the code uses the adoption-time mark (`DRIFT-079`, appended OPEN);
(3) `DRIFT-039` (no `portfolio_state_snapshot`), which is why the book is rebuilt from the
`BrokerPositionSnapshot` and `Position` facts at all.

**Clauses that were ⬜ and are now proven:** None. The S237 tests cite `SCAN-IDM-01`, `ANLZ-IDM-01`
and `PM-IDM-01` in their docstrings, but they live in `tests/`, not with the agent, and the test-plans
are under `agents/`, which this sprint may not edit; no row moves.

---

## Test plan results — fill at handback

*Rewritten for the return: A1–A13 as the plan writes them (R8). "Failed first" names the red that was
seen before the code that turns it green existed; the full red output is in the Closeout.*

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a1_identical_inputs_agree` — five runs decided by the fleet's own graph-pull stages (`scan_market_node`, `analyze_scan_node`, `evaluate_analyst_node`, monitor adoption), exported by the exporter, replayed: 100 % at all three stages, zero causes, `PASS`, `replayed` 5/5/5; measured: scanner 105 units over 5 sessions, analyst 110 tickers, PM 88 judged (10 passthroughs, 10 agree) | `tests/test_replay_fidelity.py` | Passed; failed first (`run_fidelity` had no replay to run) | `SCAN-IDM-01`, `ANLZ-IDM-01`, `PM-IDM-01` |
| A2 | `test_a2_a_changed_live_output_is_caught_and_located` — one live `hold` confidence +0.01: exactly one row differs (analyst, that ticker, `confidence`, `unexplained`); scanner and PM 100 %; `FAIL` | `tests/test_replay_fidelity.py` | Passed; the returned build read `PASS` on the same edit (Closeout, probe line 1) | `ANLZ-IDM-01`, `PM-IDM-01` |
| A3 | `test_a3_the_books_market_values_reach_the_pm` — live `sector_concentration` rejections reproduced; with the book's values removed the same PM approves one of them (in-test counterfactual); Part A's `test_replay_day_passes_holding_market_values_to_pm` kept for the S235 path | `tests/test_replay_fidelity_book.py`; `tests/test_replay_day_portfolio_values.py` | Passed; `position_values={}` planted: red | `PM-NEV-06`, `PM-NEV-08` |
| A4 | `test_a4_a_benchmark_live_used_but_never_stored_is_named` (replay: `T31` survives without SPY, every difference `not_persisted:benchmark`, other sessions untouched, nothing substituted) + `test_the_export_names_a_benchmark_live_used_but_never_stored` + `test_a_benchmark_is_named_only_on_evidence_live_used_one` | `tests/test_replay_fidelity.py`; `tests/test_fidelity_export_edges.py`; `tests/test_fidelity_export_book.py` | Passed | `SCAN-OUT-06`, `SCAN-OUT-07`, `SCAN-IDM-01` |
| A5 | `test_a5_code_changed_needs_git_evidence` — a tiny git repo whose HEAD changes `agents/analyst/domain/analyze.py`: all five sessions non-clean, the difference `code_changed:agents/analyst/domain/analyze.py`, analyst units pooled 0, `INSUFFICIENT` | `tests/test_replay_fidelity_git.py` | Passed; failed first (no git evidence was taken) | `ANLZ-IDM-01` |
| A6 | `test_a6_the_verdict_follows_dl237[89-percent, 90-percent, below-the-floor]` → `FAIL`, `PASS`, `INSUFFICIENT`; `test_a6_an_unexplained_clean_difference_fails_whatever_the_percentage` (99 % → `FAIL`) | `tests/test_replay_fidelity_verdict.py` | Passed; failed first (module did not exist) | `ANLZ-IDM-01` |
| A7 | `test_a7_only_the_volume_swap_moves_the_decisions` — snapshot volume at half the cache's SIP volume, no fundamentals/news/earnings: step 1 changes candidates, steps 2–5 change nothing further, Jaccard equals the set arithmetic exactly, 0 unswapped bars | `tests/test_replay_fidelity_layer2.py` | Passed; failed first (Layer 2 passed fixture rows through) | `SCAN-IDM-01` |
| A8 | `test_a8_layer3_counts_approvals_vetoes_drops_and_fills` — 4 approvals, 2 `overturn` (a `revise` in `vetoed_tickers` not counted), 1 dropped, 1 filled; plus `test_layer3_reads_the_live_fill_shape_end_to_end` on fills written by execution's own writers | `tests/test_replay_fidelity_layer3.py` | Passed; failed first (module did not exist; the returned build read `filled 0`) | `DLIB-OUT-02`, `DLIB-OUT-04`, `EXEC-OUT-07`, `EXEC-STA-05` |
| A9 | `test_a9_one_json_per_scheduled_run_read_and_never_written` — 0 `merge_node`/`add_edge` during export; files for the two `sched-*` runs only (a `manual-*` run and the `*-resume-analyst` child excluded); the resumed session carries the original `ScanRun` through `linked_from_key` and the resume's `PMRun` | `tests/test_fidelity_export.py` | Passed | `SCAN-OBS-01`, `ANLZ-OBS-01`, `PM-OBS-01`, `RPT-NEV-02` |
| A10 | `test_a10_fidelity_outputs_refuse_the_worktree` + `test_a10_the_export_refuses_the_worktree` — `ValueError` naming the path; nothing created | `tests/test_replay_fidelity.py`; `tests/test_fidelity_export.py` | Passed | `RPT-NEV-02` |
| A11 | `test_a11_reason_columns_are_the_sorted_union_with_zero_where_absent` — five sessions with different reasons: header is the sorted union, `0` where absent; Part A's `test_sessions_csv_counts_pipeline_outputs_and_progress_is_stderr_only` kept | `tests/test_replay_runner_counts.py`; `tests/test_replay_runner_progress.py` | Passed; **failed first on the returned Part A** (a blank, not `0`), fixed here | `RPT-OUT-07`, `PM-OUT-03` |
| A12 | `test_a12_progress_lands_at_the_interval_and_the_end_on_stderr_only` — every 2 of 5: lines at 2/5, 4/5 and 5/5 only, stdout empty, the four output files byte-identical | `tests/test_replay_runner_counts.py` | Passed | `RPT-OUT-07` |
| A13 | S235's suite, untouched: `git diff origin/main -- tests/test_replay_{runner,day,episode_exits,no_lookahead,ledger,broker,outputs,series,settings,regime,env_names,universe}.py` is empty | `tests/test_replay_*.py` | Passed, except 2 in `test_replay_universe.py` that fetch VIX from `cdn.cboe.com` and fail in this container on `main` too (egress 403; see Not met) | per their own docstrings |

**Tests added beyond the plan (regressions on the live shapes and the fail-closed branches):**
`test_the_export_carries_the_deploy_as_live_writes_it` (`git_sha`, no `sha`);
`test_an_unknown_deploy_is_never_clean[no-deploy-key, no-deploy, blank-sha, unresolvable-sha]`;
`test_a_tunables_change_marks_every_session_non_clean`; `test_a_change_outside_the_decision_paths_stays_clean`;
`test_an_export_carrying_replay_outputs_is_refused[replay, layer2]`;
`test_a_stage_with_no_replay_is_never_read_as_the_live_output`;
`test_fills_are_the_pm_runs_by_source_run_id_with_broker_status`;
`test_held_stops_are_named_not_persisted_and_never_attached`;
`test_the_book_is_the_position_facts_the_live_stages_read`; `test_a_stale_book_names_the_held_positions`;
`test_drift_079_the_pm_weighs_a_held_name_at_its_adoption_mark`;
`test_a_held_stop_exit_is_attributed_to_the_unpersisted_held_stops`;
`test_an_account_the_broker_did_not_answer_is_replayed_as_live_read_it`;
`test_a_book_the_export_could_not_rebuild_names_held_positions`;
`test_a_run_whose_regime_was_not_stored_replays_the_scanner_only`;
`test_every_float_is_compared_within_the_one_tolerance`; `test_a_scan_without_a_stored_filter_trace_compares_membership_only`;
`test_each_broker_outcome_is_one_bucket_and_resting_stops_are_not_orders`;
`test_a_run_that_stored_nothing_is_exported_empty_and_compares_nothing`;
`test_the_deploy_is_the_latest_readable_record_at_or_before_the_scan`;
`test_a_lot_that_returns_after_it_was_superseded_is_named_not_guessed`;
`test_projection_helpers_keep_json_safe_and_fail_closed`;
`test_non_clean_sessions_and_passthroughs_are_never_pooled`; `test_an_unexplained_diagnostic_difference_also_fails`;
`test_every_stage_has_its_floor[scanner-floor, pm-floor, both-floors-met]`;
`test_a_stage_under_the_bar_fails_even_below_its_floor`;
`test_layer2_is_skipped_and_said_so_without_a_cache`;
`test_a_ticker_the_cache_lacks_keeps_its_volume_and_is_counted`; `test_a_session_without_a_snapshot_has_no_layer2_rows`;
`test_a_held_line_is_worth_its_latest_visible_close_and_never_a_later_one` (Part A helper).
Fixtures: `tests/fidelity_fleet.py`, `tests/fidelity_fleet_data.py`, `tests/fidelity_fleet_outcomes.py`,
`tests/fidelity_harness.py` — synthetic data, the fleet's own writers and stages; no vendor data.

---

## Closeout — evidence

**Status:** BUILT (the return; the first handback's closeout is superseded, and its gate proof was
for `c67a62e4`, not for this build)

**Tree the proofs ran in (and `.env` present?):** a claude.ai cloud container,
`/home/user/trading-agents`, branch `sprint-237-the-replay-decides-what-the-fleet-decided`, from
`0923eb38`. No `.env` exists in this tree; no database, no OneDrive cache, no network data source.
Every proof is on synthetic fixtures committed under `tests/`; no vendor or exported data is
committed. Dependencies: `uv sync --frozen` from the existing lock. `pyproject.toml` and `uv.lock`
are untouched (the version is already `0.117.00`).

**Result:** Layer 1 replays each stage through the fleet's own composition (`scan_market_node`,
`run_analysis`, `run_evaluation`) on the exported live inputs; an export carrying `replay` or
`layer2` is refused; a stage without a replay is `harness:not_replayed`; the deploy is read as
`git_sha` and only a resolvable SHA with no decision-path diff is clean; the tunables and issuer-map
packs are decision paths at their full paths; the verdict is per stage and per ticker with its
floors (R5); Layer 2 runs the fixed cumulative swaps from `--cache` or says it was skipped; Layer 3
reads `Fill.source_run_id` and `broker_status` and counts `overturn` verdicts; held stops are named
`not_persisted`, never attached; the held book is the `Position` facts the live stages read.
Found and filed: `DRIFT-079` (the live PM weighs held names at their adoption-day mark).

**Files changed:** `scripts/fidelity_exporter.py`, `scripts/fidelity_export_helpers.py` (rewritten);
new `scripts/fidelity_export_book.py`, `scripts/fidelity_export_outcomes.py`;
`scripts/replay_fidelity_compare.py`, `scripts/replay_fidelity_layers.py` (rewritten); new
`scripts/replay_fidelity_{inputs,stages,session,causes,git,verdict,layer2,cache,layer3,report}.py`;
Part A: `scripts/replay_counters.py` (`zero_absent_reasons`), `scripts/replay_session.py` (calls it);
tests: `tests/fidelity_fleet.py`, `tests/fidelity_fleet_data.py`, `tests/fidelity_fleet_outcomes.py`,
`tests/fidelity_harness.py`, `tests/test_fidelity_export{,_book,_edges}.py`,
`tests/test_replay_fidelity{,_book,_edges,_git,_layer2,_layer3,_verdict}.py`,
`tests/test_replay_runner_counts.py`, `tests/test_replay_session_helpers.py`; docs: this spec,
`docs/design-log.md` (DL-238 rewritten), `docs/laws/drift-register.md` (`DRIFT-079` appended),
`docs/sprints/README.md`, `docs/sprints/INDEX.md`, `docs/STATE.md`. No `contracts/`, `agents/` or
`laws.md` file changed; `scripts/module_size_baseline.py` unchanged.

**Design decisions:** [DL-238](../design-log.md), rewritten for the return (R10) with the first
version's overstatement named at its top.

**Proof — the red run first** (the new tests on `0923eb38`'s code, before any fix):

```text
$ uv run --frozen pytest tests/test_replay_fidelity.py tests/test_replay_fidelity_git.py \
    tests/test_replay_fidelity_verdict.py tests/test_replay_fidelity_layer2.py \
    tests/test_replay_fidelity_layer3.py tests/test_replay_fidelity_book.py \
    tests/test_fidelity_export.py tests/test_replay_runner_counts.py --no-cov -q
E   ModuleNotFoundError: No module named 'scripts.replay_fidelity_verdict'
E   ModuleNotFoundError: No module named 'scripts.replay_fidelity_layer3'
E   ModuleNotFoundError: No module named 'scripts.replay_fidelity_inputs'
E   ModuleNotFoundError: No module named 'scripts.fidelity_export_outcomes'
Interrupted: 4 errors during collection

$ uv run --frozen pytest tests/test_replay_fidelity.py tests/test_replay_fidelity_git.py \
    tests/test_replay_fidelity_layer2.py tests/test_replay_runner_counts.py --no-cov -q
E   TypeError: run_fidelity() got an unexpected keyword argument 'repo'      (x15)
E   AssertionError: assert [['', '2', ''... ['', '', '']] == [['0', '2', '...0', '0', '0']]
FAILED tests/test_replay_fidelity.py::test_a1_identical_inputs_agree
FAILED tests/test_replay_fidelity.py::test_a2_a_changed_live_output_is_caught_and_located
FAILED tests/test_replay_fidelity.py::test_a4_a_benchmark_live_used_but_never_stored_is_named
FAILED tests/test_replay_fidelity.py::test_an_export_carrying_replay_outputs_is_refused[replay]
FAILED tests/test_replay_fidelity.py::test_an_export_carrying_replay_outputs_is_refused[layer2]
FAILED tests/test_replay_fidelity.py::test_a_stage_with_no_replay_is_never_read_as_the_live_output
FAILED tests/test_replay_fidelity.py::test_a10_fidelity_outputs_refuse_the_worktree
FAILED tests/test_replay_fidelity_git.py::test_a5_code_changed_needs_git_evidence
FAILED tests/test_replay_fidelity_git.py::test_a_tunables_change_marks_every_session_non_clean
FAILED tests/test_replay_fidelity_git.py::test_a_change_outside_the_decision_paths_stays_clean
FAILED tests/test_replay_fidelity_git.py::test_an_unknown_deploy_is_never_clean[no-deploy]
FAILED tests/test_replay_fidelity_git.py::test_an_unknown_deploy_is_never_clean[blank-sha]
FAILED tests/test_replay_fidelity_git.py::test_an_unknown_deploy_is_never_clean[unresolvable-sha]
FAILED tests/test_replay_fidelity_layer2.py::test_a7_only_the_volume_swap_moves_the_decisions
FAILED tests/test_replay_fidelity_layer2.py::test_layer2_is_skipped_and_said_so_without_a_cache
FAILED tests/test_replay_runner_counts.py::test_a11_reason_columns_are_the_sorted_union_with_zero_where_absent
16 failed, 2 passed in 6.20s
```

The signature errors say little about behaviour, so the returned code was also probed directly on a
fleet-produced export (five fleet runs, one filled buy, one `BrokerStopOrder` for held `T03`, one
live `hold` confidence moved by 0.01, the deploy SHA `000…0` that no repo holds):

```text
1 verdict with a moved confidence, unresolvable SHA: PASS 987 {'causes': {}} non_clean: []
2 deploy keys exported: ['actor', 'deployed_at', 'git_sha', 'tag'] -> replay reads deploy['sha'] = ''
3 fills exported for a live filled buy: []
4 held stop facts attached: ['T03']
5 tunables change detected as decision code: ()
6 export carrying a replay block accepted; verdict: FAIL
7 market props exported: ['key', 'label', 'snapshot'] (no tickers/window_end)
```

Each line is one of the planner's findings reproduced on synthetic data: R1/R2 (1, 6), R2 (2), R6 (3),
R7 (4), R3 (5), and the scanner's universe and as-of never exported (7).

**Proof — the green run:**

```text
$ uv run --frozen pytest tests/test_replay_fidelity{,_book,_edges,_git,_layer2,_layer3,_verdict}.py \
    tests/test_fidelity_export{,_book,_edges}.py tests/test_replay_runner_counts.py \
    tests/test_replay_runner_progress.py tests/test_replay_day_portfolio_values.py \
    tests/test_replay_session_helpers.py --no-cov -o addopts=""
tests/test_replay_fidelity.py .......                                    [ 12%]
tests/test_replay_fidelity_book.py ....                                  [ 19%]
tests/test_replay_fidelity_edges.py .....                                [ 28%]
tests/test_replay_fidelity_git.py ........                               [ 42%]
tests/test_replay_fidelity_layer2.py ....                                [ 49%]
tests/test_replay_fidelity_layer3.py ..                                  [ 52%]
tests/test_replay_fidelity_verdict.py ..........                         [ 70%]
tests/test_fidelity_export.py ....                                       [ 77%]
tests/test_fidelity_export_book.py ...                                   [ 82%]
tests/test_fidelity_export_edges.py .....                                [ 91%]
tests/test_replay_runner_counts.py ..                                    [ 94%]
tests/test_replay_runner_progress.py .                                   [ 96%]
tests/test_replay_day_portfolio_values.py .                              [ 98%]
tests/test_replay_session_helpers.py .                                   [100%]
============================= 57 passed in 28.30s ==============================
```

**Guards planted (DL-70), each red, then restored and green** (a harness replaced one line, ran the
named tests, restored the file, ran them again):

```text
RED  planted -> 2 failed in 3.67s | restored -> GREEN 2 passed in 2.22s :: R1 replay read from the file (refusal removed)
RED  planted -> 1 failed in 2.76s | restored -> GREEN 1 passed in 2.80s :: R2 live fallback (no replay reads the live block)
RED  planted -> 3 failed, 1 passed in 5.77s | restored -> GREEN 4 passed in 5.63s :: R2 empty SHA counted clean
RED  planted -> 1 failed in 2.86s | restored -> GREEN 1 passed in 2.99s :: R3 tunables path as a bare name
RED  planted -> 2 failed in 1.72s | restored -> GREEN 2 passed in 1.73s :: R6 fill link by order_ref/pm_run_id
RED  planted -> 2 failed in 1.08s | restored -> GREEN 2 passed in 1.13s :: R6 outcome read from Fill.status
RED  planted -> 1 failed in 0.64s | restored -> GREEN 1 passed in 0.53s :: R6 vetoed counted from vetoed_tickers
RED  planted -> 1 failed in 1.25s | restored -> GREEN 1 passed in 1.16s :: R7 every BrokerStopOrder attached (re-run, see below)
RED  planted -> 2 failed in 3.35s | restored -> GREEN 2 passed in 3.57s :: A3 Trap 1: position_values={} (re-planted on the final read-only book)
RED  planted -> 1 failed in 1.34s | restored -> GREEN 1 passed in 1.20s :: DRIFT-079 the snapshot's current mark instead of the adoption mark
RED  planted -> 1 failed in 3.04s | restored -> GREEN 1 passed in 2.79s :: Trap 2: PM fed the replay's analyst output
RED  planted -> 1 failed in 0.35s | restored -> GREEN 1 passed in 0.35s :: R5 hold passthroughs pooled into the PM bar
RED  planted -> 1 failed in 0.33s | restored -> GREEN 1 passed in 0.34s :: R5 unexplained counted on judged rows only
RED  planted -> 1 failed in 0.33s | restored -> GREEN 1 passed in 0.36s :: R5 INSUFFICIENT decided before FAIL
RED  planted -> 1 failed in 3.10s | restored -> GREEN 1 passed in 3.08s :: R4 volume swapped at step 2, not step 1
RED  planted -> 1 failed in 0.51s | restored -> GREEN 1 passed in 0.49s :: A11 no zero where a reason is absent
```

(R7's first plant run went red but pytest spent minutes rendering a `not in` over a 1.5 MB JSON
string; the assertion was changed to a count and the plant re-run: the line above.)

**Module line counts:** scripts: `fidelity_export.py` 41, `fidelity_exporter.py` 152, `fidelity_export_helpers.py` 116, `fidelity_export_book.py` 126, `fidelity_export_outcomes.py` 89, `replay_fidelity.py` 33, `replay_fidelity_cache.py` 122, `replay_fidelity_causes.py` 91, `replay_fidelity_compare.py` 119, `replay_fidelity_git.py` 99, `replay_fidelity_inputs.py` 144, `replay_fidelity_layer2.py` 112, `replay_fidelity_layer3.py` 66, `replay_fidelity_layers.py` 162, `replay_fidelity_report.py` 141, `replay_fidelity_session.py` 82, `replay_fidelity_stages.py` 118, `replay_fidelity_verdict.py` 99, `replay_runner.py` 82, `replay_session.py` 190, `replay_session_helpers.py` 68, `replay_counters.py` 62, `replay_day.py` 180. Tests: `fidelity_fleet.py` 177, `fidelity_fleet_data.py` 194, `fidelity_fleet_outcomes.py` 104, `fidelity_harness.py` 176, `test_fidelity_export.py` 151, `test_fidelity_export_book.py` 89, `test_fidelity_export_edges.py` 155, `test_replay_fidelity.py` 182, `test_replay_fidelity_book.py` 135, `test_replay_fidelity_edges.py` 127, `test_replay_fidelity_git.py` 139, `test_replay_fidelity_layer2.py` 141, `test_replay_fidelity_layer3.py` 128, `test_replay_fidelity_verdict.py` 134, `test_replay_runner_counts.py` 146, `test_replay_session_helpers.py` 48. Every module is under 200 (the largest, `replay_session.py`, is Part A's at 190); `scripts/module_size_baseline.py` is unchanged.

**R9 — coverage the gate cannot see** (`[tool.coverage.run] source` excludes `scripts/`; the
project's `addopts` add their own `--cov` sources and a 100 % floor over them, so they are cleared
with `-o addopts=""` to report only these modules):

```text
$ uv run --frozen pytest <the S237 tests, and S235's runner tests for the Part A modules> \
    -o addopts="" --cov-branch --cov-report=term-missing \
    --cov=scripts.replay_fidelity_compare --cov=scripts.replay_fidelity_layers \
    --cov=scripts.fidelity_exporter --cov=scripts.fidelity_export_helpers \
    --cov=scripts.fidelity_export_book --cov=scripts.fidelity_export_outcomes \
    --cov=scripts.replay_fidelity_{inputs,stages,session,causes,git,verdict,layer2,cache,layer3,report} \
    --cov=scripts.replay_{counters,session,session_helpers,runner}
Name                                  Stmts   Miss Branch BrPart    Cover   Missing
-----------------------------------------------------------------------------------
scripts/fidelity_export_book.py          52      0     16      0  100.00%
scripts/fidelity_export_helpers.py       62      0     24      0  100.00%
scripts/fidelity_export_outcomes.py      33      0      4      0  100.00%
scripts/fidelity_exporter.py             59      0      8      0  100.00%
scripts/replay_counters.py               20      0      2      0  100.00%
scripts/replay_fidelity_cache.py         44      0     10      0  100.00%
scripts/replay_fidelity_causes.py        37      0     12      0  100.00%
scripts/replay_fidelity_compare.py       56      0      8      0  100.00%
scripts/replay_fidelity_git.py           40      0      4      0  100.00%
scripts/replay_fidelity_inputs.py        61      0      4      0  100.00%
scripts/replay_fidelity_layer2.py        37      0      4      0  100.00%
scripts/replay_fidelity_layer3.py        24      0      8      0  100.00%
scripts/replay_fidelity_layers.py        63      0     18      0  100.00%
scripts/replay_fidelity_report.py        38      0      6      0  100.00%
scripts/replay_fidelity_session.py       30      0      4      0  100.00%
scripts/replay_fidelity_stages.py        37      0      6      0  100.00%
scripts/replay_fidelity_verdict.py       42      0     14      0  100.00%
scripts/replay_runner.py                 24      0      0      0  100.00%
scripts/replay_session.py                63      0      6      0  100.00%
scripts/replay_session_helpers.py        30      0     12      0  100.00%
-----------------------------------------------------------------------------------
TOTAL                                   852      0    170      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
74 passed in 51.64s
```

Every verdict branch is hit: `replay_fidelity_verdict.py` 42 statements and 14 branches, none missed
(FAIL on a stage under 90 %, FAIL on an unexplained difference judged or diagnostic, FAIL before
INSUFFICIENT, INSUFFICIENT per floor, PASS).

**`make ci`:** exit **2**, on the finished tree (`make ci > ci_final.txt 2>&1; echo $?`, file read, not piped).
Steps 1–11 green: ruff; `ruff format` (1402 files already formatted); mypy (no issues in 1055 source
files); import-linter (5 kept, 0 broken); module size (warnings only, S237's `replay_fidelity_layers.py`
162 among them; no block); module header; law coverage; PARAM/settings sync; sprint status
(`sprint-237…: BUILT`, `UNMAPPED=0`); markdown links; version scheme. Step 12, pytest:
`2 failed, 3452 passed, 6 skipped`, coverage `TOTAL 18835 0 4088 0 100.00%`; the two failures are
`test_replay_universe.py::test_universe_build_leaves_existing_replay_cache_untouched` and
`::test_from_snapshot_rebuilds_without_wikipedia_fetch`, both `ProxyError … cdn.cboe.com … 403
Forbidden` (below). `make` stops there, so steps 13–15 were run one by one on the same tree: dependency
audit exit 0 (`No unaccepted vulnerabilities; 1 accepted advisory re-checked`), detect-secrets
`Passed`, untracked secrets exit 0.

**`make gate-ran`: OWED.** This container has no `gh` CLI, so the target cannot run here (CLAUDE.md,
DL-228). The branch is pushed; the planner runs `make gate-ran` from a worktree whose `HEAD` is the
pushed SHA and checks the printed SHA against `git rev-parse HEAD`.

**Not met / verified failing:**

- `make ci` does not exit 0 in this container: two S235 tests in `tests/test_replay_universe.py`
  (`test_universe_build_leaves_existing_replay_cache_untouched`,
  `test_from_snapshot_rebuilds_without_wikipedia_fetch`) fetch VIX from `cdn.cboe.com`, which the
  session's egress policy refuses (403). They fail identically on a clean `origin/main` worktree
  (`e5b7d70`) here, and this sprint does not touch them (A13). Every other step and test is green.
  The remote gate, which has network, is the proof for them. Root cause and fix: *Return notes*,
  last item (branch `chore-replay-universe-vix-offline`).
- `make gate-ran`: owed (above). Remote CI results read through the GitHub connector are an
  observation, not `GATE PROVEN`.
- The live export and the verdict are the planner's; nothing here ran against the spine.
- `uv.lock` and the version: untouched, as instructed (`0.117.00`, refreshed in the first build).

---

## Return notes

- **R1 (done).** Layer 1 calls the fleet: `scan_market_node` on the exported `MarketData` node (its
  `tickers` and `window_end` are now exported), `run_analysis` on the live `CandidateSet`, and
  `run_evaluation` on the live `RecommendationSet` with `PortfolioState` from
  `portfolio_from_graph` and settings from `build_effective_settings`, plus the pack's issuer map.
  These are R1's calls in the fleet's own composition (DL-238 D2 says why not re-composed here). An
  export with `replay`/`layer2` is refused. A1's live side is produced by the fleet's graph-pull
  stages and reads `PASS` at 100 %; A2 shows a 0.01 move is caught.
- **R2 (done).** No replay is `harness:not_replayed`, never the live block. The deploy is read as
  `git_sha`; a missing key, empty value, blank SHA or one git cannot resolve is non-clean,
  `code_changed:unknown_deploy`. The fixture's deploy is written by `orchestration.deploy_record`.
- **R3 (done).** Decision paths name `orchestration/packs/trading_tunables.json` in full, and add
  `orchestration/packs/trading_issuer_map.json`, which the live PM reads (DL-238 D7).
- **R4 (done).** Layer 2 loads the S235 cache and runs the cumulative swaps in the fixed order
  through the same stage calls, anchored on the live book, regime and sectors; step 5 is the cache's
  bars and SPY over `declared_lookback_days`. Without `--cache` it is skipped and both reports say so.
- **R5 (done).** Per-stage units, fields and floors as written; `hold_recommendation` passthroughs
  counted beside the PM bar; `fidelity.md` states each stage's number, denominator and floor. One
  reading to check: DL-237's "zero unexplained differences" is applied to every clean difference,
  judged or diagnostic.
- **R6 (done).** Fills are the `Fill` nodes whose `source_run_id` is the `PMRun` key; the outcome is
  `broker_status`; `vetoed` counts `overturn` verdicts. The spec's "expired" is counted as
  `EXEC-OUT-07`'s `dropped` (live `Fill.broker_status` never holds `expired`).
- **R7 (done, as not persisted).** The stored stop facts do not allow a rebuild as of the run
  (DL-238 D4), so nothing is exported and both gaps are named whenever the book holds a name; a
  live stop exit on a held name is attributed to `not_persisted:held_stops`.
- **R8 (done).** A1–A13 as written, the live-shape regressions, and every listed plant (plus
  Trap 1, Trap 2, R4, R5, R6 and A11 plants), each red then green.
- **R9 (done).** 100.00 % line and branch over the 20 S237 modules, pasted above.
- **R10 (done).** DL-238 rewritten to this build, its first version's overstatement named; the STATE
  line reads BUILT only for what is built.
- **For the planner, beyond the R-items.** (a) `DRIFT-079`: the live PM values a held name at its
  adoption-day mark, and the replay reproduces that; a fix to the PM will move live decisions and
  this baseline together. (b) Part A's `sessions.csv` wrote a blank for an absent reason; fixed.
  (c) A holding that returns to a lot the monitor superseded earlier stays unheld in the graph
  (DL-238, found on the way (c)); not filed, not measured live. (d) A resumed PM reads no
  snapshot: resume clones none, and `portfolio_from_graph` selects by the child's run id. Measured on
  the fleet's own code, the resumed PM sizes on `starting_cash` ($100,000). The replay reproduces
  what `portfolio_from_graph` reads, and the export names `held_positions` for such a session. Not
  measured live.
- S235's smoke numbers predate the Part A `position_values` fix, as the first handback said.
- **The two `cdn.cboe.com` failures: root cause and fix, on a separate branch (not part of S237).**
  *Cause:* S235 (`5bceb3a`) added `build_context_files(cache_dir, sessions, bar_fetcher,
  vix_fetcher=vix_history)` to `scripts/sp500_context.py`, where the real Cboe download is the
  default, and `build_universe` (`scripts/replay_universe.py:112`) called it with the bar fetcher
  only; `build_universe` had no VIX parameter at all. So the two `build_universe` tests in
  `tests/test_replay_universe.py`, which inject their page and bar sources, could not inject VIX,
  and every run downloaded
  `https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv`. Wherever the
  network is open (the planner's machine, GitHub CI) this passed silently; the cloud session's
  egress policy refuses the host (403), so it failed here first. `tests/test_sp500_context.py`
  injects `vix_fetcher`, which is why only these two tests were affected.
  *Fix:* branch `chore-replay-universe-vix-offline`, `ebbb78e5`, from `main` `e5b7d70`, pushed,
  not merged. `build_universe` takes `vix_fetcher` and passes it through (the real download stays
  the command-line default; the file is 199 lines). Both tests inject a stub and assert its value
  reaches `sp500_vix.csv.gz`, and an autouse guard in the module fails any real HTTP call and
  names the URL, so a leak like this now fails everywhere, not only where egress is blocked.
  Version `0.116.01` → `0.116.02` (fix).
  *Proof:* red first (`unexpected keyword argument 'vix_fetcher'`, 2 failed); guard planted
  (parameter kept, passthrough dropped: both tests fail on the guard's "network call in a unit
  test"), restored, green; `UV_FROZEN=1 make ci` in that worktree exits **0**, all 15 steps,
  `3397 passed, 6 skipped`, coverage 100.00 %.
  *Owed:* `uv lock` (it cannot re-resolve here, since `download.pytorch.org` is blocked, so
  `uv.lock` still reads `0.116.01`; CI syncs with `--frozen`), and `make gate-ran`. Both branches
  change the `pyproject.toml` version: if S237 merges first, the chore becomes `0.117.01` and the
  lock is refreshed again. No STATE.md or design-log line was written on the chore branch, to avoid
  conflicting with this branch's STATE.md edit.

---

## Planner review — returned 2026-09-27

**Handback `c67a62e4` is returned, not merged.** The gate is green (`GATE PROVEN for
c67a62e4…`, CI, CodeQL and Security Findings, attempt 1; 0 open error-level alerts on the branch),
and Part A holds: the runner split, the `sessions.csv` counts, stderr progress, and the
`position_values` fix (quantity × latest visible close, the shape `graph_portfolio.py` uses live).
**Parts B and C do not do what the spec asks, and on live data the tool certifies the harness without
running it.**

**Measured, planner, main checkout on this branch with `.env`, 2026-09-27.** The live export
(read-only, 12 s) over `sched-2026-09-22` → `09-25` wrote four sessions of about 5 MB each, with
the right deploys (s225, s225, s227, s228b), regime, full snapshots, 18 candidates, 26
recommendations, and intents and rejections. Then `replay_fidelity.py run` on that export:

```text
"clean": {"agreement": 1.0, "denominator": 1008, "matches": 1008, "pooled": {"causes": {}}},
"non_clean": [],
"verdict": "PASS"
```

No stage was replayed. `layer1_rows` reads `session["replay"]`, which the exporter never writes, and
falls back to the **live** block when it is absent, so it compared live with live. All four sessions
counted as clean: the exporter writes the deploy as `git_sha`, `run_fidelity` reads `sha`, and an
empty SHA counts as "no code changed". Those sessions ran s225–s228b, whose `contracts/` files differ
from `HEAD` in files the analyst imports. Layer 3 read `filled 0` on all four sessions, but SCHW, CSCO
(09-22) and BMY (09-23) filled at the broker.

### Returned items — each needs a test that fails first

- **R1 (blocker). Layer 1 runs the fleet's functions.** Rebuild each stage's inputs from the export as
  contract objects and call them: *scanner*, `apply_filters` + `rank_survivors` on the snapshot's bars,
  benchmark, earnings and `earnings_horizon_days`; *analyst*, `scoring_universe` over the **live**
  `CandidateSet` and the held book, then `score_candidates` with the snapshot as `MarketData`
  (fundamentals, news, sectors, earnings), the exported `RegimeContext` and the benchmark, then
  `split_decisions`; *PM*, `evaluate_recommendations` over the **live** `RecommendationSet`, with the
  `PortfolioState` built as `agents/portfolio_manager/graph_portfolio.py` builds it (cash = account
  equity; positions, refs and `position_values` from the book), and settings from
  `build_effective_settings`. Replay outputs are **computed, never read**: an export file carrying a
  `replay` or `layer2` key is refused.
- **R2 (blocker). Fail closed.** A stage with no replay output is `harness:not_replayed`, never the
  live block. A session with no deploy, or a SHA `git` cannot resolve, is non-clean
  (`code_changed:unknown_deploy`). Read `git_sha`, the `DeployRecord` field. The fixture's deploy
  must have the live shape.
- **R3. The tunables path.** `_DECISION_PATHS` holds `trading_tunables.json`, but the file lives at
  `orchestration/packs/trading_tunables.json`, so a tunables change never marks a session non-clean.
- **R4. Build Layer 2** as specced: `--cache` loads the S235 cache, and the cumulative swaps run in the
  fixed order (SIP volume, then no fundamentals, no news, no earnings, then cache bars over
  `declared_lookback_days`), each step through the same stage calls as R1, anchored on the live book.
  Without `--cache`, Layer 2 is skipped, and `summary.json` and `fidelity.md` say so.
- **R5. The verdict per stage, per [DL-237](../design-log.md) as amended today:**
  - *scanner:* per session and ticker, candidate membership and rank;
  - *analyst:* per ticker, `action`, `exit_trigger`, and `confidence` within 1e-9 (`technical_score`
    and `suggested_stop_pct` are diagnostics);
  - *PM:* per ticker **over judged recommendations only** (`buy` and `sell`): decision and reason,
    plus quantity and stop pct for an approval. `hold_recommendation` passthroughs are counted
    beside it, never pooled; on 09-25 they were 25 of the 26 PM rows.
  - *floors:* analyst ≥ 100 tickers, PM ≥ 10 judged recommendations, scanner ≥ 4 sessions.
  - *overall:* `FAIL` if any stage is under 90 % or any clean difference is `unexplained`, else
    `INSUFFICIENT` if any floor is unmet, else `PASS`. `fidelity.md` states each stage's number and
    denominator.
- **R6. Layer 3 reads the live Fill shape.** A PM run's fills are the `Fill` nodes whose
  `source_run_id` equals the `PMRun` key (180 carry it). The outcome is `broker_status`, because
  `status` stays `pending` by design. Measured values: buy `filled` 49, buy `rejected` 102, sell
  `filled` 10. `vetoed` counts overturn verdicts.
- **R7. Held-stop inputs are what the analyst read, or `not_persisted`.** Live reads
  `open_position_stop_thresholds(graph)` and `active_broker_stop_refs(graph)` from the graph as it
  stood at run time (`agents/analyst/run.py:65-82`). The export currently attaches every
  `BrokerStopOrder` ever placed for a held name (47 → 55 over four sessions). Reconstruct them as of
  `ScanRun.created_at` if the stop nodes carry the times to do it; otherwise export nothing and name
  `not_persisted:held_stops` and `not_persisted:active_broker_stop_refs`, so a held-name difference
  is attributed to them.
- **R8. The test plan, A1–A13 as written.** The table renumbered it into 8 rows and dropped A1, A2, A4,
  A6, A7, A8, A9 and A12 without a reason. A1's live side must be produced by the fleet's own
  functions, so that its `PASS` means something. Add regressions on the live shapes (`git_sha`,
  `source_run_id`, `broker_status`), and plant, per DL-70: replay read from the file; the live
  fallback; an empty SHA counted clean; the tunables path; the fill link. Each goes red, then is
  restored.
- **R9. Coverage the gate cannot see.** `[tool.coverage.run] source` excludes `scripts/`, so the
  handback's 100.00 % covers none of this sprint's code. Paste `pytest --cov=scripts.replay_fidelity_compare
  --cov=scripts.replay_fidelity_layers --cov=scripts.fidelity_exporter
  --cov=scripts.fidelity_export_helpers --cov-branch --cov-report=term-missing` for the S237 tests, with
  every verdict branch hit.
- **R10. Say what is built.** DL-238 Decision 2 describes stage replays that did not exist at
  `c67a62e4`, and the STATE line read "built". Correct DL-238 to what the returned build does, and
  never write a `Result:` for work not done (LAW-02).

**Planner corrections owned here, not by the builder.** The spec's *"4 clean sessions (09-22 → 09-25)"*
was marked *[ASSUMED]* and does not hold under the rule it asked for: s225–s228b differ from `HEAD` in
`contracts/` files the analyst imports. **The clean set starts at `sched-2026-09-28` (s232, 0 files).**
DL-237's amendment records that, and the PM-denominator fix in R5.
