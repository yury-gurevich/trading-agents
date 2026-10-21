<!-- Agent: planning | Role: sprint handover -->
# Sprint 287 — The daily brief and the dashboard say what the held book stands to gain and lose

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-287-the-brief-shows-the-books-odds`
**Status:** BUILT
**Version:** *next available MINOR at merge* (`0.130.00` while `main` is `0.129.00`)
**Effort:** M
**Decisions:** [DL-311](../design-log.md) (decided, nine decisions with the roads not taken) · work-queue 92 ([DL-240](../design-log.md): the book as a distribution; [DL-310](../design-log.md): the nightly held claims this sprint reads)

> **Why this bump kind.** The brief and the dashboard gain a dimension they did not have: the held book, its names past their target and the forecast's odds for it. A MINOR.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `orchestration/laws/dispatcher/laws.md`, `surfaces/laws/laws.md` | Two **locked constitutions** (the daily brief is the dispatcher's, `DSP-IDN-04`; the dashboard is surfaces') | **LOCKED. Read-only during a build**, except Appendix section 2, which you apply exactly. A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `orchestration/laws/dispatcher/test-plan.md`, `surfaces/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read them to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`IDN`** (DSP-IDN-04: the brief reports and never decides), **`OUT`** (DSP-OUT-06 and DSP-OUT-08/09, where the brief's lines sit; the new DSP-OUT-10; SRF-OUT-01, SRF-OUT-05, SRF-OUT-06; the new SRF-OUT-09), **`DEP`** (DSP-DEP-01), **`CAP`** (the dispatcher's `labels_read`, checked by `orchestration/tests/test_dispatcher_capability.py`), **`FAIL`** (DSP-FAIL-03: nothing in the brief can stop a fire).

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read each book's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Yes: two new guarantees, no contract change.** The brief now carries the book's lines (`DSP-OUT-10`) and the dashboard a book panel (`SRF-OUT-09`). The cycle is written for you in Appendix section 2: dispatcher v1.7 → v1.8 (`DSP-OUT-10` new; `DSP-DEP-01` and `CAP` amended for the `Position` and `BarrierForecast` reads; `DSP-OUT-09` moved back under the Outputs heading, where it belongs; a Changelog line), surfaces v1.8 → v1.9 (`SRF-OUT-09` new; the test-plan's status line, left at v1.6, aligned; a Changelog line), the `test-plan.md` rows naming your tests, and both rollups: dispatcher **46 / 49 → 47 / 50**, surfaces **31 / 38 → 32 / 39**. **`contracts/` is not touched.**

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `orchestration/book_odds.py` (new) | dispatcher `laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `DSP-OUT-10` (the book, the session's claim by key, what is no claim); `DSP-DEP-01`, `CAP` (reads `Position` and `BarrierForecast`, writes nothing) |
| `orchestration/book_brief.py` (new) | same | `DSP-OUT-10` (every word and figure of the two lines) |
| `orchestration/daily_brief_facts.py`, `daily_brief_text.py` | same | `DSP-OUT-06` (a malformed fact names its field), `DSP-OUT-08/09` and `DSP-OUT-10` (where the lines sit), `DSP-FAIL-03` |
| `orchestration/Dockerfile` | `tests/test_dispatch_scheduled_run.py` (the image must copy every module its entrypoint imports) | the slim dispatcher image copies modules one by one |
| `surfaces/dashboard/projections_book.py` (new), `app.py`, `static/book.js` (new), `static/index.html` | surfaces `laws.md` + `test-plan.md` | `SRF-OUT-09`; `SRF-OUT-01` (the selected run scopes the panel); `SRF-OUT-05` (no sprint id in operator text); `SRF-OUT-06` (no unwired control) |

⚠️ **Nothing on the decision path moves, and nothing is written.** The brief and the panel read the active Positions and the forecaster's held claims; no file under `contracts/`, `kernel/`, `agents/`, `orchestration/packs/` or `orchestration/history_window.py` changes, and no graph label, property, env key or tunable is added. If your change needs one, stop and report: a decision-path deploy restarts the fidelity count EXP-014 and EXP-022 wait on.

---

## Goal

At merge, every finished daily brief whose book holds a name carries, after its fills, the book's lines: how many names are past the target their buy declared, their gain now, how much of it is above target, and what they would hold at their stops; then the forecast's odds for the book over the next 10 sessions (how many names it expects at target first, at stop first and at neither, which names are likelier to reach their stop, which have no forecast), each read from the forecaster's held claim for the run's session by key. A RED brief carries none. The dashboard's trading section shows the same lines and one row per held name, the likeliest to reach its stop first on top.

## Why (context)

Item 92: the book only exits on its stop, and every step that would sell waits for EXP-022, which waits for the fidelity PASS. S286 (deployed 2026-10-21) states a barrier claim on every held name each night; nothing shows it. On 2026-10-20, 13 of the 34 held names closed past the target their buy declared, with $1,229 of gain, and at their stops the same 13 would hold $593 less than they cost: each stop stays at its entry less its width. The operator reads the brief once a day, and it says nothing of the book. This sprint puts the held claims and that stake in front of them, with no decision path, so it deploys while the count runs.

### Measured, 2026-10-21 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| What the brief says today | the verdict, equity, scoreboard, orders, fills, the container and LLM lines, needs-you; nothing of a held name's price, stop or target | *[measured 2026-10-21]* `orchestration/daily_brief_text.py::compose_brief` read whole |
| What the dashboard shows of the book | graph against broker quantity per ticker | *[measured 2026-10-21]* `surfaces/dashboard/projections_state.py::run_positions` |
| The held claim's figures | `entry_close` (the claim's close), `stop_price`, `target_price`, `target_basis` (`declared` / `rebased`), `p_stop_first`, `p_target_first`, `p_neither`, `horizon_sessions`; key `barrier-garch-v1:held:{ticker}:{as_of}` | *[measured 2026-10-21]* `agents/forecaster/barrier_store.py::write_claim` and `BarrierClaim.key` read whole |
| The book on 2026-10-20 | 34 held, 32 claims; 13 past target: **+$1,229.08 now, +$484.12 above target, −$592.89 at their stops** (the drop to the stops, $1,821.97, exceeds their gain); odds over 32 names: 13.3 target first, 4.3 stop first, 14.4 neither; 5 likelier to stop (TGT 61 %, NVDA 57 %, GOOG 43 %, TXN 35 %, CAT 28 %); no forecast: PM, UNH. DL-310's figures to the cent | *[measured 2026-10-21]* kit `s287_f1.py` on S286's frozen book and the claims S286's forecaster stated on it (`s287_freeze_claims.py`: 35 claims, 32 held, the same two refusals as S286's F1) → `f1_proto.txt`, digest `0a8e6318978cd7b0` |
| The reads | one `Position` listing and one keyed `BarrierForecast` read per held name; no claim listing | *[measured 2026-10-21]* the prototype under the planner's A4 (a graph that counts its reads) |
| The dispatcher image | syncs `--extra runtime --no-dev`, copies modules one by one and no `agents/forecaster/` module; numpy is a dev dependency only, so the job cannot import forecaster code | *[measured by reading, 2026-10-21]* `orchestration/Dockerfile`, `pyproject.toml`; the image was not built |
| Whether the held odds are calibrated | *[ASSUMED — not measured]* unknown: no held claim settles before about 2026-11-04; on buy claims S241's F4 found the stop first 47.6 % of the time against 29.4 % declared. The line says `not yet scored` | the held scorecard after the first settlements |
| Whether the held claims exist when the brief is sent | *[ASSUMED — not measured]* yes: the brief goes at the first fire after the run's `Snapshot`, and the forecaster answers within the run; if not, the brief says `no forecast for <session>` | S286's F2 on `sched-2026-10-21` (the claims' `created_at` against the `Snapshot`'s), and this sprint's F2 |

---

## Scope — and what is deliberately NOT here

1. **The book's odds** (`orchestration/book_odds.py`, Appendix section 1): the active Positions summed by ticker, each joined to its held claim for one session read by key; a claim lacking a figure, or holding one that is not a number, is no claim; nothing held is no book.
2. **The brief's book lines** (`orchestration/book_brief.py`): the first line on the names past their target, the second the forecast's odds; one line when no claim exists.
3. **The brief** (`daily_brief_facts.py`, `daily_brief_text.py`): the lines after the fills and before the container and LLM lines on a finished brief; the session is the `RunRequest`'s `requested_at`, a malformed one a `BriefDataError` naming the field; the dispatcher's `Dockerfile` copies the two new modules.
4. **The dashboard panel** (`surfaces/dashboard/projections_book.py`, `app.py`, `static/book.js`, `static/index.html`): `/api/runs/{run}/book` and a panel under the trading section.
5. **The law cycle** (Appendix section 2), exactly.

### Out of scope (do NOT build this sprint)

- **Any exit, notice or alarm.** No sell, no take-profit, no message on the night a name crosses its target: EXP-022 decides exits, and a notice is another sprint (DL-311, named).
- **The held scorecard's skill in the line.** No held claim has settled; the line says `not yet scored`.
- **Anything the forecaster, the PM or another agent reads or writes.** The brief and the panel only read.
- **The dashboard chat's context bundle.** `run_bundle` does not gain the book.
- **No `laws.md` edit** beyond Appendix section 2. **No ADR reversal.**

### The road not taken (LAW-06)

- **The drop to the stops (−$1,821.97) as the figure.** Rejected: larger, but it hides that the winners would end as losses; the gain at the stops says it.
- **Naming every name past its target in the brief.** Rejected: thirteen names is no glance; the dashboard lists them.
- **A line per held name.** Rejected: thirty-four lines.
- **The run's broker snapshot as the book.** Rejected (DL-310's reason): its holdings carry no position_ref; the active Positions are what the claims were stated for.
- **Recomputing the barriers from the broker's prices.** Rejected: the odds stand on the claim's own close, stop and target.
- **Importing the forecaster's label and key.** Rejected: it loads forecaster code and numpy into an image that has neither; a test pins the dispatcher's copy instead.
- **A forecast-exit replay experiment, or a take-profit built switched off.** Rejected by the operator for this sprint (DL-311).

---

## The design decisions this sprint has to make

**None are left to make: DL-311 records D1 to D9 with the rejected alternatives, on `main`.** Do not add a design-log entry. If a decision there does not survive contact with the code, stop and report.

---

## Blast radius — measured 2026-10-21

| What | Detail |
| --- | --- |
| Files changed | Production (Appendix section 1, 9 files): new `orchestration/book_odds.py` **169**, `orchestration/book_brief.py` **70**, `surfaces/dashboard/projections_book.py` **73**, `surfaces/dashboard/static/book.js` **64**; `orchestration/daily_brief_facts.py` 170 → **182**, `orchestration/daily_brief_text.py` 183 → **185**, `surfaces/dashboard/app.py` 184 → **186**, `surfaces/dashboard/static/index.html` 151 → **153**, `orchestration/Dockerfile` 123 → **125**. Law and rollups (section 2): the two `laws.md` and `test-plan.md`, `docs/laws/ledger.md`, `docs/laws/INDEX.md`. Your tests: four test files and a helper (Test plan). `pyproject.toml`, `uv.lock` (the bump) |
| Agents affected | none. `orchestration` imports `contracts.positions` (unchanged); `surfaces` imports `orchestration` (allowed) |
| Contract change? | **No** |
| Graph vocabulary change? | **No** (nothing is written) |
| New env keys / tunables | none (the three- and four-name limits are display constants, like the container line's) |
| Deploy implication | **An image-only retag.** The brief is sent by the dispatcher job; "Build and push agent images" builds its image from the merged tag with the two new modules. No fidelity decision path (`scripts/replay_fidelity_git.py`'s `DECISION_PATHS`): the count holds. The dashboard runs locally: restart it to load the panel |
| Rollback | Retag to `s286`. A retag does not undo the briefs already sent (Telegram messages); nothing else is written |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **No design-log entry**: DL-311 is decided.
3. **Write the tests A1 to A15 under the exact names in the Test plan** and run them on the unchanged tree: every one fails or errors except A11, which passes there (the unchanged brief has no book line at all) and must still pass after. Paste the output.
4. **Apply Appendix section 1 exactly.**
5. **Apply Appendix section 2 exactly** (law cycle, rollups).
6. **Plant the breaks B1 to B26** one at a time against your tests alone; each turns at least one red; restore each.
7. **Bump MINOR, `uv lock --offline`, `make ci` redirected to a file.**
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

Each docstring cites the clauses in the last column. The names are fixed: the test-plan rows in Appendix section 2 cite them. Paths: `orchestration/tests/` unless the row names `surfaces/tests/`. A helper module of your own (fixtures for held lots and held claims, a graph that counts its reads) is fine. The session in A1 to A9 and A13 to A15 is 2026-10-20; A10 to A12 use the existing brief fixtures' run, `sched-2026-09-25` (`daily_brief_fixtures.seed_run`, `daily_brief_scenarios.seed_pair`), and key their claims by 2026-09-25.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 `test_book_odds.py::test_the_book_joins_each_held_name_to_its_sessions_claim` | COP held in two lots, 8 @ 12441 and 2 @ 13000 cents; three COP claims: the held one for 2026-10-20 (close 145.95, stop 117.08, target 130.5765, `rebased`, odds 0.002 / 0.395 / 0.603), a held one for 2026-10-17 and a **buy** claim `barrier-garch-v1:COP:2026-10-20`, both with other figures | one name: COP, quantity 10, cost 125528; its claim `HeldClaim(close_cents=14595, stop_cents=11708, target_cents=13058, passed=True, p_stop=0.002, p_target=0.395, p_neither=0.603, horizon_sessions=10)` (note 145.95 × 100 is 14594.999…: the cents are rounded); nothing unforecast (`DSP-OUT-10`) |
| A2 | `…odds.py::test_a_name_without_a_readable_claim_is_unforecast` | DOW, MO, PFE, XOM held; DOW's claim has `stop_price` `True`; MO has none; PFE's is whole; XOM's node has no properties | `unforecast` is DOW, MO, XOM; only PFE is forecast (`DSP-OUT-10`) |
| A3 | `…odds.py::test_nothing_held_is_no_book` | a closed lot, a `broker_absent` lot and a `broker_superseded_by` lot, and a held claim for the closed lot's ticker | `book_odds` is `None` (`DSP-OUT-10`) |
| A4 | 🎯 `…odds.py::test_the_book_reads_positions_once_and_each_claim_by_key` | four held names with claims, on a graph that counts `list_nodes` and `get_node` by label, the counters cleared after planting | listings exactly `{"Position": 1}`, keyed reads exactly `{"BarrierForecast": 4}` (`DSP-OUT-10`) |
| A5 | `…odds.py::test_the_label_and_prefix_are_the_forecasters` | — | `BARRIER_LABEL` equals `agents.forecaster.barrier_store.BARRIER_LABEL`; `HELD_CLAIM_PREFIX` equals `f"{BARRIER_MODEL_ID}:{HELD_KEY_SEGMENT}:"`; `PASSED_BASIS` is one of `held_claim.TargetBasis`'s values (`DSP-OUT-10`) |
| A6 | 🎯 `test_book_brief.py::test_the_book_line_totals_the_names_past_their_target` | COP 8 @ 12441, claim close 145.95 / stop 117.08 / target 130.58, `rebased`, odds 0.002 / 0.395 / 0.603; MO 5 @ 6500 and 3 @ 6700, close 74.64 / stop 62.00 / target 71.80, `rebased`, 0.002 / 0.030 / 0.968; KO 10 @ 8692, close 93.49 / stop 82.57 / target 95.612, `declared`, 0.001 / 0.550 / 0.449; GOOG 3 @ 34170, close 336.40 / stop 324.61 / target 375.87, `declared`, 0.430 / 0.071 / 0.499 | exactly `("Book: 4 held · 2 past their target: +$243.44 now (+$145.68 above target), −$88.64 at their stops", "Odds, next 10 sessions, 4 names (not yet scored): target first 1.0 · stop first 0.4 · neither 2.5 · likelier to stop: GOOG 43 %")`, the minus being U+2212 (`DSP-OUT-10`) |
| A7 | 🎯 `…brief.py::test_the_odds_line_sums_the_claims_and_names_the_likelier_to_stop` | TGT, NVDA, AMD, TXN, CAT with p_stop 0.61, 0.57, 0.57, 0.35, 0.28, each p_target 0.1 and p_neither 0.9 − p_stop; KO with 0.2 / 0.2 / 0.6 (a tie: not likelier to stop); PM, UNH, ABT, BA, WFC held with no claim | the odds line exactly `"Odds, next 10 sessions, 6 names (not yet scored): target first 0.7 · stop first 2.6 · neither 2.7 · likelier to stop: TGT 61 %, AMD 57 %, NVDA 57 % and 2 more · no forecast: ABT, BA, PM, UNH and 1 more"` (`DSP-OUT-10`) |
| A8 | `…brief.py::test_a_book_with_no_claim_says_so_in_one_line` | KO and PM held; KO's only claim is for 2026-10-17 | `("Book: 2 held · no forecast for 2026-10-20",)`; and `book_lines(None)` is `()` (`DSP-OUT-10`) |
| A9 | `…brief.py::test_no_name_past_its_target_reads_none` | KO 10 @ 8692 with a `declared` claim, odds 0.0 / 0.5 / 0.5 | the first line `"Book: 1 held · none past its target"`; the second ends `"target first 0.5 · stop first 0.0 · neither 0.5"` (`DSP-OUT-10`) |
| A10 | 🎯 `test_daily_brief_book.py::test_a_finished_brief_carries_the_book_after_its_fills` | `seed_pair`, then A6's four names with their claims keyed 2026-09-25; one dispatcher fire at 22:50 (`daily_brief_fixtures.fire`); then a `BriefFacts` with `containers`, `llm` and `book` set, composed | the one brief sent is `A1_TEXT` with A6's two lines inserted after `Filled: none`; the composed one ends book, book, containers, LLM, needs-you (`DSP-OUT-10`, `DSP-OUT-06`) |
| A11 | `…brief_book.py::test_a_red_brief_carries_no_book` | a run through `ExecutionRun` (no `Snapshot`) and A6's book | no brief line starts `Book:` or `Odds,` (`DSP-OUT-10`) |
| A12 | `…brief_book.py::test_a_malformed_session_names_its_field` | `seed_pair` and A6's book; the run's chain with its `RunRequest` node replaced by one whose `requested_at` is `"x"` | `brief_facts` raises `BriefDataError` whose message is exactly `RunRequest.requested_at` (`DSP-OUT-10`) |
| A13 | 🎯 `surfaces/tests/test_dashboard_book.py::test_the_book_view_says_what_the_brief_says_and_leads_with_the_stop` | a `RunRequest` for `sched-2026-10-20` (`place_run_request`, as of 2026-10-20), A6's book and PM 2 @ 18000 with no claim; `GET /api/runs/sched-2026-10-20/book` through `build_app` | 200; `as_of` `"2026-10-20"`; `lines` equal `book_lines(book_odds(graph, 2026-10-20))`; rows in the order GOOG, COP, MO, KO, PM; COP's row exactly `{"ticker": "COP", "quantity": 8, "forecast": true, "close_cents": 14595, "stop_cents": 11708, "target_cents": 13058, "past_target": true, "p_target_first": 0.395, "p_stop_first": 0.002, "p_neither": 0.603, "gain_cents": 17232}`; PM's exactly `{"ticker": "PM", "quantity": 2, "forecast": false}` (`SRF-OUT-09`, `SRF-OUT-01`) |
| A14 | `…dashboard_book.py::test_a_run_with_no_request_or_no_book_shows_nothing` | `run_book` called directly: an unknown run; a `RunRequest` whose `requested_at` is `"soon"`; the 2026-10-20 run with nothing held | `{"as_of": None, "lines": [], "rows": []}` twice, then `{"as_of": "2026-10-20", "lines": [], "rows": []}` (`SRF-OUT-09`) |
| A15 | `…dashboard_book.py::test_the_panel_is_served_and_wired` | `build_app` on that graph; `GET /` and `GET /book.js` | the page holds `<div id="bookbody">` and `<script src="/book.js`; the script is served 200 as JavaScript, listens for `dashboard:run-selected` and asks `"/book"`; neither text carries `S28` (`SRF-OUT-09`, `SRF-OUT-05`) |

On the unchanged tree every one fails or errors except A11. After Appendix section 1 all fifteen pass, and the existing suites pass unchanged (`orchestration/tests/test_dispatcher_capability.py` passes only with section 2's `CAP`; `tests/test_dispatch_scheduled_run.py` only with section 1's `Dockerfile`).

---

## Success factors

- [x] On the built tree, F1 (kit `s287_f1.py`, run from the built tree with its own venv) prints exactly the prototype's output (`f1_proto.txt`, digest `0a8e6318978cd7b0`): the two book lines above, a whole brief with them after `Filled: none`, 34 dashboard rows.
- [x] No file under `contracts/`, `kernel/`, `agents/` or a decision path changes; no existing test changes.
- [x] Design decisions recorded with rejected alternatives: DL-311, already on `main`.
- [x] Law cycle done as Appendix section 2: `DSP-OUT-10` and `SRF-OUT-09` 🟩; dispatcher 47 / 50 and surfaces 32 / 39 in both rollups.
- [x] B1 to B26 each planted, watched to fail against your tests alone, restored — stated per break.
- [x] Every touched module < 200 lines, test files included.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **The session is the `RunRequest`'s `requested_at`, not a property called `as_of`.** `place_run_request` writes `requested_at` (the as-of date); the claims are keyed by that day. A10 goes through a real fire so a wrong field fails it.
🪤 **Read each claim by its key; never list `BarrierForecast`.** About 36 claims a night accumulate; A4 counts the reads.
🪤 **A held claim's key has its own segment** (`…:held:…`). The buy claim on the same bar has other figures (A1).
🪤 **Round the cents.** `145.95 × 100` is `14594.999…`; `int()` loses a cent (A1).
🪤 **"Likelier to stop" is strictly greater**: a name at equal odds is not (A7's KO).
🪤 **The figure is the gain at the stops**, the gain less the drop to the stops, not the drop itself (A6: −$88.64, not $332.08).
🪤 **The lines sit after the fills and before the container and LLM lines, and only on a finished brief** (A10, A11).
🪤 **The dispatcher image copies modules one by one**: a new module the brief imports must be in `orchestration/Dockerfile`, or `tests/test_dispatch_scheduled_run.py` fails, and the job would fail on the fleet.
🪤 **Do not import from `agents/forecaster/` in production code** (the brief's existing `agents.supervisor` import is in the image). The dispatcher image has no forecaster code and no numpy; A5 (a test) is the only place the two are compared.
🪤 **`daily_brief_text.py` is 185 lines and `daily_brief_facts.py` 182 after section 1**: do not grow them; keep each new test file under 200 after `ruff format`.
🪤 **Write files with an editor, not a shell heredoc** (Git Bash's heredoc has eaten backslashes before). The minus in the brief is U+2212: in a test write it as `chr(0x2212)` or an escape, or ruff's `RUF001` stops the commit.

**The breaks** (plant one at a time in production code, run your A1 to A15 alone, expect red, restore). Each is an exact replacement of text in the file after section 1:

| # | File | Replace | With |
| --- | --- | --- | --- |
| B1 | `orchestration/book_odds.py` | `for node in active_position_nodes(graph):` | `for node in graph.list_nodes("Position"):` |
| B2 | same | `held[0] += quantity` | `held[0] = quantity` |
| B3 | same | `held[1] += quantity * int(node.props["opened_price_cents"])` | `held[1] += int(node.props["opened_price_cents"])` |
| B4 | same | `f"{HELD_CLAIM_PREFIX}{ticker}:{day}"` | `f"barrier-garch-v1:{ticker}:{day}"` |
| B5 | same | `day = as_of.isoformat()` | `day = "2026-10-17"` |
| B6 | same | `isinstance(v, (int, float)) and not isinstance(v, bool)` | `isinstance(v, (int, float))` |
| B7 | same | `passed=node.props.get("target_basis") == PASSED_BASIS` | the same with `!=` |
| B8 | same | `close_cents=round(close * 100)` | `close_cents=int(close * 100)` |
| B9 | same | `if c.p_stop > c.p_target` | `if c.p_stop >= c.p_target` |
| B10 | same | `key=lambda item: (-item[1], item[0])` | `key=lambda item: (item[1], item[0])` |
| B11 | same | the first of the three sums in `expected`, `sum(c.p_target for c in claims),` | `sum(c.p_stop for c in claims),` |
| B12 | same | `return self.quantity * (claim.close_cents - claim.target_cents)` | `return self.quantity * (claim.target_cents - claim.close_cents)` |
| B13 | same | `HELD_CLAIM_PREFIX: Final = "barrier-garch-v1:held:"` | `HELD_CLAIM_PREFIX: Final = "barrier-garch-v1:held-"` |
| B14 | same | `_claim(graph.get_node(BARRIER_LABEL, f"{HELD_CLAIM_PREFIX}{ticker}:{day}")),` | `_claim(next((n for n in graph.list_nodes(BARRIER_LABEL) if n.key == f"{HELD_CLAIM_PREFIX}{ticker}:{day}"), None)),` |
| B15 | `orchestration/book_brief.py` | `at_stops = gain - sum(` | `at_stops = sum(` |
| B16 | same | `if not odds.forecast:` | `if not odds.names:` |
| B17 | same | `LEANING_NAMED = 3` | `LEANING_NAMED = 5` |
| B18 | same | `UNFORECAST_NAMED = 4` | `UNFORECAST_NAMED = 5` |
| B19 | `daily_brief_facts.py`, `daily_brief_text.py` | three edits: move the `book=book_lines(book_odds(graph, _session(nodes["RunRequest"]))),` line from the `replace(...)` call into the first `BriefFacts(...)` (after its `llm=` line); and in `compose_brief`'s RED branch, `(_header(facts), stage, _orders(facts.orders), *sensed, _needs_you(facts))` | `(_header(facts), stage, _orders(facts.orders), *facts.book, *sensed, _needs_you(facts))` |
| B20 | `orchestration/daily_brief_text.py` | `*facts.book,` then `*sensed,` (the finished branch) | `*sensed,` then `*facts.book,` |
| B21 | `orchestration/daily_brief_facts.py` | `str(request.props.get("requested_at", ""))[:10]` | `str(request.props.get("as_of", ""))[:10]` |
| B22 | same | `raise BriefDataError("RunRequest.requested_at") from exc` | `return date(2000, 1, 1)` |
| B23 | `surfaces/dashboard/projections_book.py` | `-(n.claim.p_stop if n.claim else 0)` | `(n.claim.p_stop if n.claim else 0)` |
| B24 | same | `key=lambda n: (n.claim is None,` | `key=lambda n: (n.claim is not None,` |
| B25 | same | `"lines": list(book_lines(odds)),` | `"lines": [],` |
| B26 | `surfaces/dashboard/app.py` | the `_RUN_VIEWS` entry `"book": run_book,` | nothing (the line removed) |

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes after the Appendix: `daily_brief_text.py` **185**, `daily_brief_facts.py` **182**, `book_odds.py` **169**, `surfaces/dashboard/app.py` **186**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. No tunable is added: the three- and four-name limits are named display constants, as the container line's are.
- Faults, not silent failure: a malformed session is a `BriefDataError` naming its field (`DSP-OUT-06`), caught by the brief's existing boundary (`DSP-FAIL-03`); a claim missing a figure is listed as no forecast, never dropped.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a pipe.**
- Version bump MINOR, `uv.lock` staged with it.
- Secrets never through the worktree — your worktree has **no `.env`**, and nothing in this sprint needs one. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0** from the branch's worktree; check the printed SHA against `git rev-parse HEAD`.
2. Planner's review: CodeQL set-diff against the baseline branch first; the blobs against `prototype_blobs.txt` (kit); the planner's tests on the built tree; B1 to B26 against Codex's tests alone; F1 (equals `f1_proto.txt` byte for byte).
3. Merge to `main` locally and push; tag `v<version>`; post-merge CodeQL.
4. **Deploy, on the operator's word: an image-only retag** from the tag. The fidelity count holds (no decision path); record the rollback tag `s286`. F2 on the first weekday night after: 8 / 8; the brief carries the book's two lines after `Filled:`, their figures equal to the reader run on the live graph for that session (read-only), or one `no forecast` line if the held claims were not yet written (then read their `created_at` against the `Snapshot`'s); no `compose failed` or `send failed` in the job's lines. Restart the local dashboard and look at the panel for that run.

---

## Handover — paste this to Codex

```text
You are building Sprint 287 in the worktree ../ta-s287, on the branch
sprint-287-the-brief-shows-the-books-odds. Never work on main. The worktree and its venv are
ready; never run a bare `uv sync` (it needs the network and you have none).

Read docs/sprints/sprint-287-the-brief-shows-the-books-odds.md, whole, before anything else. It
is the spec, and its bottom sections are your handback. The Appendix holds the production code
and the law text, which you apply exactly. Your work is the tests A1 to A15, the breaks, the bump
and the evidence.

In order:
1. Read orchestration/laws/dispatcher/laws.md and test-plan.md, surfaces/laws/laws.md and
   test-plan.md, docs/laws/conventions.md and docs/laws/drift-register.md, whole. Fill the Law
   reading record in the spec BEFORE any code.
2. Write the tests A1 to A15 under the exact file paths and names in the Test plan (three files
   under orchestration/tests/, one under surfaces/tests/; a helper module of your own is fine),
   each docstring citing the clauses in its row, each asserting the exact strings and numbers its
   row gives. Run them on the unchanged tree and paste the output into the Closeout: every one
   fails or errors except A11, which passes.
3. Apply Appendix section 1 exactly (9 files: 5 Python modules, 3 of them new; the dispatcher's
   Dockerfile; the dashboard's index.html and new book.js). Change nothing else in production code.
4. Apply Appendix section 2 exactly (the two books' laws.md and test-plan.md, docs/laws/ledger.md,
   docs/laws/INDEX.md). Change no existing test. The test-plan rows name your tests; if a name
   differs, your name is wrong.
5. Plant the breaks B1 to B26 (Traps: each row is an exact replacement) one at a time; each must
   turn at least one of your A1 to A15 red; restore each before the next. Record each in the
   Closeout.
6. Bump the version MINOR to the next number after main's in pyproject.toml, run
   uv lock --offline, stage uv.lock. Run make ci redirected to a file and read the file. If the
   dependency audit is the only step that fails for want of network, say so; the planner runs it.
   Paste the step lines and their verdicts into the Closeout, not the whole log.
7. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in the sprint's
   row of docs/sprints/README.md. Commit on the branch if your sandbox lets you write the
   repository's git directory; if not, leave the tree uncommitted and say so. Do not edit
   docs/STATE.md, docs/design-log.md or docs/work-queue.md.

DO NOT: reach the network or any live service; run infra/ scripts, pwsh or any az command; change
contracts/, kernel/, agents/, orchestration/packs/, orchestration/history_window.py or any
Dockerfile but orchestration/Dockerfile's two COPY lines in section 1; import from agents/ in
the modules you add (the brief's existing supervisor import stays; tests may, as A5 does); write
to the graph; add or reword a law clause beyond
section 2; add a design-log entry; use noqa; let any module, test files included, reach 200 lines;
measure make ci through a pipe; write files with a shell heredoc.

Traps (the spec's Traps section has them all): the session is the RunRequest's requested_at; read
each claim by key, never list them; the held key has its own segment; round the cents; likelier to
stop is strictly greater; the first line's last figure is the gain at the stops, not the drop to
them; the lines go after the fills, before the container and LLM lines, on a finished brief only;
the dispatcher image copies modules one by one; the brief's minus is U+2212.

Two tiers when something does not fit. A wrong command, count, path or line number whose intent is
plain: correct it, record it in Return notes, and carry on. A law that contradicts the spec, an
existing test failing outside section 2's files, or a measurement in the spec that does not
reproduce: STOP and report. State anything not done as "not done" or "verified failing". Never
write a Result for work you have not done.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output: the step lines and their verdicts, not the whole `make ci` log.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| Book reader and book wording | `orchestration/laws/dispatcher/laws.md` and `test-plan.md`, whole; `docs/laws/conventions.md` and `drift-register.md`, whole (2026-10-21, before code) | DSP-IDN-04, DSP-OUT-06/08/09, new DSP-OUT-10, DSP-DEP-01, CAP, DSP-FAIL-03 | Retain Appendix exactly: active lots, session-keyed held claims, rounded cents, no writes or decision changes. DSP-DEP-01 is partial and remains gray. |
| Brief facts, composition and dispatcher image | Same dispatcher book and plan; `tests/test_dispatch_scheduled_run.py`, whole | DSP-IDN-04, DSP-OUT-06/08/09/10, DSP-FAIL-03, CAP | Put the lines only on finished briefs after fills; copy both imports in the slim image. |
| Dashboard projection, route and static panel | `surfaces/laws/laws.md` and `test-plan.md`, whole; conventions and drift register above | SRF-OUT-01/05/06, new SRF-OUT-09 | Selected-request session; brief's own lines; forecast rows first, stop probability descending; no control or writes. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** Yes, two new guarantees, no contract change. Apply Appendix section 2 exactly: DSP-OUT-10 and SRF-OUT-09, dispatcher v1.8 and surfaces v1.9, their named test-plan rows and both rollups. DL-311 D1-D9 and its ruled-out alternatives were read; no design decision is left open.

**Contradictions found between a law and this spec:** None found in the complete reading. The specified amendment supplies the new read capability and guarantees.

**Laws found silent where a decision was needed:** The two new output guarantees are absent before this sprint; Appendix section 2 explicitly supplies them. No additional silence needing a decision was found.

**Clauses that were ⬜ and are now proven:** No pre-existing gray clause changed status. New DSP-OUT-10 and SRF-OUT-09 now have passing cited functional tests; dispatcher 47 / 50 and surfaces 32 / 39. DSP-DEP-01 remains partial/gray (clock/calendar/universe dependencies unproven); SRF-IDN-01/02, SRF-TRG-01, SRF-SEC-01/02, SRF-DEP-01 and SRF-PERF-02 remain gray. This sentence records the final proof; the reading record above preceded the first code edit.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_the_book_joins_each_held_name_to_its_sessions_claim` | `orchestration/tests/test_book_odds.py` | PASS (baseline FAIL) | DSP-OUT-10 |
| A2 | `test_a_name_without_a_readable_claim_is_unforecast` | `orchestration/tests/test_book_odds.py` | PASS (baseline FAIL) | DSP-OUT-10 |
| A3 | `test_nothing_held_is_no_book` | `orchestration/tests/test_book_odds.py` | PASS (baseline FAIL) | DSP-OUT-10 |
| A4 | `test_the_book_reads_positions_once_and_each_claim_by_key` | `orchestration/tests/test_book_odds.py` | PASS (baseline FAIL) | DSP-OUT-10 |
| A5 | `test_the_label_and_prefix_are_the_forecasters` | `orchestration/tests/test_book_odds.py` | PASS (baseline FAIL) | DSP-OUT-10 |
| A6 | `test_the_book_line_totals_the_names_past_their_target` | `orchestration/tests/test_book_brief.py` | PASS (baseline FAIL) | DSP-OUT-10 |
| A7 | `test_the_odds_line_sums_the_claims_and_names_the_likelier_to_stop` | `orchestration/tests/test_book_brief.py` | PASS (baseline FAIL) | DSP-OUT-10 |
| A8 | `test_a_book_with_no_claim_says_so_in_one_line` | `orchestration/tests/test_book_brief.py` | PASS (baseline FAIL) | DSP-OUT-10 |
| A9 | `test_no_name_past_its_target_reads_none` | `orchestration/tests/test_book_brief.py` | PASS (baseline FAIL) | DSP-OUT-10 |
| A10 | `test_a_finished_brief_carries_the_book_after_its_fills` | `orchestration/tests/test_daily_brief_book.py` | PASS (baseline FAIL) | DSP-OUT-10, DSP-OUT-06 |
| A11 | `test_a_red_brief_carries_no_book` | `orchestration/tests/test_daily_brief_book.py` | PASS (baseline PASS) | DSP-OUT-10 |
| A12 | `test_a_malformed_session_names_its_field` | `orchestration/tests/test_daily_brief_book.py` | PASS (baseline FAIL) | DSP-OUT-10 |
| A13 | `test_the_book_view_says_what_the_brief_says_and_leads_with_the_stop` | `surfaces/tests/test_dashboard_book.py` | PASS (baseline FAIL) | SRF-OUT-09, SRF-OUT-01 |
| A14 | `test_a_run_with_no_request_or_no_book_shows_nothing` | `surfaces/tests/test_dashboard_book.py` | PASS (baseline FAIL) | SRF-OUT-09 |
| A15 | `test_the_panel_is_served_and_wired` | `surfaces/tests/test_dashboard_book.py` | PASS (baseline FAIL) | SRF-OUT-09, SRF-OUT-05 |

**Tests added beyond the plan:** None. `orchestration/tests/book_fixtures.py` supplies synthetic lots, claims, fixed expected lines and the counting graph.

---

## Closeout — evidence

**Status:** BUILT — local branch only; full CI verified failing at the offline dependency audit.

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\Downloads\project\ta-s287`, branch `sprint-287-the-brief-shows-the-books-odds`, starting HEAD/main `bd3b5c5f3f156ee7ce880747e12800ed07a5905c`; clean at start; `.env` absent. Full CI used a credential-stripped child environment, `UV_OFFLINE=1`, `UV_NO_SYNC=1`, and an external socket guard allowing only local test servers; no external service was reached.

**Result:** A1-A15: 14 failed / 1 passed before production edits (A11 passed), then 15 passed. All 26 exact breaks independently made an A test fail and were restored byte for byte. All 15 Appendix production/law blobs match `prototype_blobs.txt`. F1 equals `f1_proto.txt` byte for byte: 2 book lines, 34 dashboard rows, digest `0a8e6318978cd7b0`. Full pytest: `5279 passed, 9 skipped, 2470 warnings in 462.77s (0:07:42)`, 100.00 % coverage. Version `0.130.00`; `uv lock --offline` resolved 180 packages and changed only the project version to `0.130.0`; `uv.lock` staged. The dependency audit is the only failing CI step; its external advisory lookup is not done.

**Files changed:** The exact 9 section-1 files and 6 section-2 files; the four planned test files and `orchestration/tests/book_fixtures.py`; `pyproject.toml`, `uv.lock`; this sprint document and `docs/sprints/README.md` (24 files). No existing test, excluded tree/path, other Dockerfile, STATE, design-log or work-queue change.

**Design decisions:** recorded as [`DL-311`](../design-log.md) — on `main` before the build; the rejected alternatives are there.

**Proof — the red run first:**

The red and green runs used `uv run --offline --no-sync pytest --no-cov -v orchestration/tests/test_book_odds.py orchestration/tests/test_book_brief.py orchestration/tests/test_daily_brief_book.py surfaces/tests/test_dashboard_book.py` from the recorded worktree.

```text
============================= test session starts =============================
collecting ... collected 15 items

orchestration/tests/test_book_odds.py::test_the_book_joins_each_held_name_to_its_sessions_claim FAILED [  6%]
orchestration/tests/test_book_odds.py::test_a_name_without_a_readable_claim_is_unforecast FAILED [ 13%]
orchestration/tests/test_book_odds.py::test_nothing_held_is_no_book FAILED [ 20%]
orchestration/tests/test_book_odds.py::test_the_book_reads_positions_once_and_each_claim_by_key FAILED [ 26%]
orchestration/tests/test_book_odds.py::test_the_label_and_prefix_are_the_forecasters FAILED [ 33%]
orchestration/tests/test_book_brief.py::test_the_book_line_totals_the_names_past_their_target FAILED [ 40%]
orchestration/tests/test_book_brief.py::test_the_odds_line_sums_the_claims_and_names_the_likelier_to_stop FAILED [ 46%]
orchestration/tests/test_book_brief.py::test_a_book_with_no_claim_says_so_in_one_line FAILED [ 53%]
orchestration/tests/test_book_brief.py::test_no_name_past_its_target_reads_none FAILED [ 60%]
orchestration/tests/test_daily_brief_book.py::test_a_finished_brief_carries_the_book_after_its_fills FAILED [ 66%]
orchestration/tests/test_daily_brief_book.py::test_a_red_brief_carries_no_book PASSED [ 73%]
orchestration/tests/test_daily_brief_book.py::test_a_malformed_session_names_its_field FAILED [ 80%]
surfaces/tests/test_dashboard_book.py::test_the_book_view_says_what_the_brief_says_and_leads_with_the_stop FAILED [ 86%]
surfaces/tests/test_dashboard_book.py::test_a_run_with_no_request_or_no_book_shows_nothing FAILED [ 93%]
surfaces/tests/test_dashboard_book.py::test_the_panel_is_served_and_wired FAILED [100%]
======================== 14 failed, 1 passed in 12.87s ========================
RED_EXIT=1
```

**Proof — the green run:**

```text
============================= test session starts =============================
collecting ... collected 15 items

orchestration/tests/test_book_odds.py::test_the_book_joins_each_held_name_to_its_sessions_claim PASSED [  6%]
orchestration/tests/test_book_odds.py::test_a_name_without_a_readable_claim_is_unforecast PASSED [ 13%]
orchestration/tests/test_book_odds.py::test_nothing_held_is_no_book PASSED [ 20%]
orchestration/tests/test_book_odds.py::test_the_book_reads_positions_once_and_each_claim_by_key PASSED [ 26%]
orchestration/tests/test_book_odds.py::test_the_label_and_prefix_are_the_forecasters PASSED [ 33%]
orchestration/tests/test_book_brief.py::test_the_book_line_totals_the_names_past_their_target PASSED [ 40%]
orchestration/tests/test_book_brief.py::test_the_odds_line_sums_the_claims_and_names_the_likelier_to_stop PASSED [ 46%]
orchestration/tests/test_book_brief.py::test_a_book_with_no_claim_says_so_in_one_line PASSED [ 53%]
orchestration/tests/test_book_brief.py::test_no_name_past_its_target_reads_none PASSED [ 60%]
orchestration/tests/test_daily_brief_book.py::test_a_finished_brief_carries_the_book_after_its_fills PASSED [ 66%]
orchestration/tests/test_daily_brief_book.py::test_a_red_brief_carries_no_book PASSED [ 73%]
orchestration/tests/test_daily_brief_book.py::test_a_malformed_session_names_its_field PASSED [ 80%]
surfaces/tests/test_dashboard_book.py::test_the_book_view_says_what_the_brief_says_and_leads_with_the_stop PASSED [ 86%]
surfaces/tests/test_dashboard_book.py::test_a_run_with_no_request_or_no_book_shows_nothing PASSED [ 93%]
surfaces/tests/test_dashboard_book.py::test_the_panel_is_served_and_wired PASSED [100%]

============================= 15 passed in 3.57s ==============================
GREEN_EXIT=0
```

Existing image-closure and capability tests, unchanged:

```text
.......                                                                  [100%]
7 passed in 5.07s
EXISTING_EXIT=0
```

Frozen F1 and exact Appendix proof:

```text
code from C:\Users\yury_\Downloads\project\ta-s287\orchestration\book_odds.py
APPENDIX_BLOBS=15/15
F1_BYTES_EQUAL=True
2 book lines, 34 dashboard rows; digest 0a8e6318978cd7b0
```

**Guards planted:** `GUARDS_PROVEN=26/26; ALL_MUTATED_FILES_RESTORED`. Each ran only the four planned test files; each restoration was checked against the original bytes before the next plant.

| Break | A tests made red | Observed result |
| --- | --- | --- |
| B1 | A3 | exit 1; 1 failed, 14 passed in 5.93s; bytes restored |
| B2 | A1, A6, A10 | exit 1; 3 failed, 12 passed in 6.05s; bytes restored |
| B3 | A1, A6, A10, A13 | exit 1; 4 failed, 11 passed in 5.96s; bytes restored |
| B4 | A1, A2, A4, A6, A7, A9, A10, A13 | exit 1; 8 failed, 7 passed in 6.03s; bytes restored |
| B5 | A1, A2, A4, A6, A7, A8, A9, A10, A13 | exit 1; 9 failed, 6 passed in 6.01s; bytes restored |
| B6 | A2 | exit 1; 1 failed, 14 passed in 5.91s; bytes restored |
| B7 | A1, A6, A9, A10, A13 | exit 1; 5 failed, 10 passed in 6.18s; bytes restored |
| B8 | A1, A6, A10, A13 | exit 1; 4 failed, 11 passed in 5.92s; bytes restored |
| B9 | A7 | exit 1; 1 failed, 14 passed in 5.93s; bytes restored |
| B10 | A7 | exit 1; 1 failed, 14 passed in 5.85s; bytes restored |
| B11 | A6, A7, A9, A10 | exit 1; 4 failed, 11 passed in 5.92s; bytes restored |
| B12 | A6, A10 | exit 1; 2 failed, 13 passed in 5.99s; bytes restored |
| B13 | A1, A2, A4, A5, A6, A7, A9, A10, A13 | exit 1; 9 failed, 6 passed in 5.91s; bytes restored |
| B14 | A4 | exit 1; 1 failed, 14 passed in 5.93s; bytes restored |
| B15 | A6, A10 | exit 1; 2 failed, 13 passed in 6.38s; bytes restored |
| B16 | A8 | exit 1; 1 failed, 14 passed in 5.98s; bytes restored |
| B17 | A7 | exit 1; 1 failed, 14 passed in 5.93s; bytes restored |
| B18 | A7 | exit 1; 1 failed, 14 passed in 6.10s; bytes restored |
| B19 | A11 | exit 1; 1 failed, 14 passed in 5.91s; bytes restored |
| B20 | A10 | exit 1; 1 failed, 14 passed in 5.84s; bytes restored |
| B21 | A10 | exit 1; 1 failed, 14 passed in 6.02s; bytes restored |
| B22 | A12 | exit 1; 1 failed, 14 passed in 5.96s; bytes restored |
| B23 | A13 | exit 1; 1 failed, 14 passed in 5.85s; bytes restored |
| B24 | A13 | exit 1; 1 failed, 14 passed in 5.85s; bytes restored |
| B25 | A13 | exit 1; 1 failed, 14 passed in 6.13s; bytes restored |
| B26 | A13 | exit 1; 1 failed, 14 passed in 6.00s; bytes restored |

**Module line counts:** All 11 touched Python files are below 200 lines after formatting.

```text
orchestration/book_odds.py: 169
orchestration/book_brief.py: 70
orchestration/daily_brief_facts.py: 182
orchestration/daily_brief_text.py: 185
surfaces/dashboard/projections_book.py: 73
surfaces/dashboard/app.py: 186
orchestration/tests/book_fixtures.py: 124
orchestration/tests/test_book_odds.py: 108
orchestration/tests/test_book_brief.py: 90
orchestration/tests/test_daily_brief_book.py: 80
surfaces/tests/test_dashboard_book.py: 88
```

Other section-1 counts reproduce: `orchestration/Dockerfile` 125, `book.js` 64, `index.html` 153.

**`make ci`:** Redirected directly to `%TEMP%/s287-ci.txt` (no pipe), exit 2. Read the saved output; the first 13 steps passed. Steps 15 and 16 were run separately after step 14 stopped make and passed. The online dependency audit is **NOT RUN**; full CI is **not green**.

```text
uv run ruff check . --output-format=github -> PASS
uv run ruff format --check . -> PASS
uv run mypy kernel contracts agents orchestration surfaces -> PASS
uv run lint-imports -> PASS
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts -> PASS
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts -> PASS
uv run python scripts/check_law_coverage.py -> PASS
uv run python scripts/check_param_law_sync.py -> PASS
uv run python scripts/check_sprint_status.py -> PASS
uv run python scripts/check_tracker_size.py -> PASS
uv run python scripts/check_markdown_links.py -> PASS
uv run python scripts/check_version_scheme.py -> PASS
uv run pytest -> PASS
uv run python scripts/check_dependency_audit.py -> VERIFIED FAILING (offline advisory lookup)
TOTAL                                                           21860      0   4688      0  100.00%
========= 5279 passed, 9 skipped, 2470 warnings in 462.77s (0:07:42) ==========
make: exit 2 at dependency audit
OSError: S287 offline proof: external DNS blocked
uv run pre-commit run detect-secrets --all-files -> PASS (run separately after make stopped)
uv run python scripts/check_untracked_secrets.py -> PASS (run separately after make stopped)
```

After filling this handback and changing both statuses to BUILT, the document checks were run again:

```text
uv run python scripts/check_sprint_status.py -> PASS (exit 0)
docs_seen=292 SPEC=10 BUILT=1 MERGED=281 UNMAPPED=0 MISSING=0
uv run python scripts/check_tracker_size.py -> PASS (exit 0; existing size warnings remain)
uv run python scripts/check_markdown_links.py -> PASS (exit 0)
git diff --check -> PASS (exit 0)
```

**`make gate-ran`:** not done; no push or network access, so no remote exact-SHA proof.

**Not met / verified failing:** `make ci` verified failing only at the dependency audit because external DNS is blocked; a fresh advisory result is not done and remains the planner's. Push, remote CI/Security Findings/CodeQL, merge, image build, deployment, F2 live brief proof and local dashboard restart/inspection are not done.

---

## Return notes

- Count correction: section 1 contains six Python modules (three new), not five; its nine-file total is correct. The supplied diff was applied without modification.
- The first F1 helper invocation used the same temporary filename for stdout and its output artifact. Corrected the helper to separate them, reran F1, and used only the clean byte-for-byte comparison above. No repository source changed for this correction.
- No law/spec contradiction or existing-test failure was found; no drift row or extra law wording was added. DSP-DEP-01 remains partial/gray. New DSP-OUT-10 and SRF-OUT-09 are proven; both exact rollups are dispatcher 47 / 50 and surfaces 32 / 39.
- No bare `uv sync`, infrastructure script, `pwsh`, `az`, live service, graph write outside synthetic fixtures, push, merge or deployment was run. All proof tooling and full logs are outside the worktree under `%TEMP%/s287-*`.
- Planner carry-forward: run the online dependency audit and remote exact-SHA gates, review, then handle merge/deploy/F2 in the specified order. F1 is locally reproduced; no live result is inferred from it.

---

## Appendix — the prototype (`proto-s287` `80a9b573`: `make ci` 5,279 passed, 9 skipped, 100.00 %, every step green, the dependency audit included; 26 / 26 breaks red against the planner's tests; F1 digest `0a8e6318978cd7b0`)

Apply with `git apply` from the worktree root: section 1, then section 2. Section 1 is production code, the dispatcher's `Dockerfile` and the dashboard's two static files; section 2 the law cycle and both rollups. Both are the prototype's diff against `main` `1134e8ee`, unedited.

### Section 1 — production code, the dispatcher's Dockerfile and the dashboard's static files (9 files)

```diff
diff --git a/orchestration/Dockerfile b/orchestration/Dockerfile
index d18fde05..ff4375e7 100644
--- a/orchestration/Dockerfile
+++ b/orchestration/Dockerfile
@@ -66,6 +66,8 @@ COPY agents/supervisor/store.py agents/supervisor/store.py
 COPY orchestration/__init__.py orchestration/__init__.py
 COPY orchestration/batch_chain.py orchestration/batch_chain.py
 COPY orchestration/batch_trace.py orchestration/batch_trace.py
+COPY orchestration/book_brief.py orchestration/book_brief.py
+COPY orchestration/book_odds.py orchestration/book_odds.py
 COPY orchestration/container_alarm_text.py orchestration/container_alarm_text.py
 COPY orchestration/container_brief.py orchestration/container_brief.py
 COPY orchestration/llm_brief.py orchestration/llm_brief.py
diff --git a/orchestration/book_brief.py b/orchestration/book_brief.py
new file mode 100644
index 00000000..04132060
--- /dev/null
+++ b/orchestration/book_brief.py
@@ -0,0 +1,70 @@
+"""The daily brief's book lines: what the held names stand to gain and lose.
+
+Agent: orchestration
+Role: word `book_odds`' totals as the brief's two book lines (DL-311, `DSP-OUT-10`):
+      the names past their declared target, their gain now and at their stops; then
+      the forecast's expected count of names at target first, stop first and
+      neither, the names likelier to stop, and the names with no forecast.
+External I/O: none.
+"""
+
+from __future__ import annotations
+
+from typing import TYPE_CHECKING
+
+from orchestration.daily_brief_text import signed_dollars
+
+if TYPE_CHECKING:
+    from orchestration.book_odds import BookOdds
+
+_SEP = " · "
+#: How many names a part of the odds line names before it counts the rest.
+LEANING_NAMED = 3
+UNFORECAST_NAMED = 4
+
+
+def book_lines(odds: BookOdds | None) -> tuple[str, ...]:
+    """The book line, and the odds line when a claim exists; nothing with no book."""
+    if odds is None:
+        return ()
+    held = f"Book: {len(odds.names)} held"
+    if not odds.forecast:
+        return (f"{held}{_SEP}no forecast for {odds.as_of.isoformat()}",)
+    return (f"{held}{_SEP}{_passed(odds)}", _odds(odds))
+
+
+def _passed(odds: BookOdds) -> str:
+    passed = odds.passed
+    if not passed:
+        return "none past its target"
+    gain = sum(name.gain_cents(claim) for name, claim in passed)
+    above = sum(name.above_target_cents(claim) for name, claim in passed)
+    at_stops = gain - sum(name.to_stop_cents(claim) for name, claim in passed)
+    return (
+        f"{len(passed)} past their target: {signed_dollars(gain)} now "
+        f"({signed_dollars(above)} above target), "
+        f"{signed_dollars(at_stops)} at their stops"
+    )
+
+
+def _odds(odds: BookOdds) -> str:
+    target, stop, neither = odds.expected()
+    horizon = "/".join(str(sessions) for sessions in odds.horizons)
+    parts = [
+        f"Odds, next {horizon} sessions, {len(odds.forecast)} names (not yet scored): "
+        f"target first {target:.1f}",
+        f"stop first {stop:.1f}",
+        f"neither {neither:.1f}",
+    ]
+    leaning = [f"{ticker} {round(p * 100)} %" for ticker, p in odds.leaning_to_stop]
+    if leaning:
+        parts.append(f"likelier to stop: {_named(leaning, LEANING_NAMED)}")
+    if odds.unforecast:
+        parts.append(f"no forecast: {_named(list(odds.unforecast), UNFORECAST_NAMED)}")
+    return _SEP.join(parts)
+
+
+def _named(items: list[str], limit: int) -> str:
+    named = ", ".join(items[:limit])
+    rest = len(items) - limit
+    return f"{named} and {rest} more" if rest > 0 else named
diff --git a/orchestration/book_odds.py b/orchestration/book_odds.py
new file mode 100644
index 00000000..bcba2359
--- /dev/null
+++ b/orchestration/book_odds.py
@@ -0,0 +1,169 @@
+"""The book's odds: each held name, its stop and target, and what its forecast says.
+
+Agent: orchestration
+Role: join the book (the active Positions, by ticker) to the forecaster's held claim
+      for one session (`barrier-garch-v1:held:{ticker}:{as_of}`, DL-310) and total
+      what the brief and the dashboard say of it (DL-311): the names past their
+      declared target, their gain, the part above the target and the drop to their
+      stops; how many names the forecast expects to reach target first, stop first
+      or neither; the names leaning to their stop; the names with no claim.
+External I/O: reads the injected GraphStore (Position listed once, then one claim
+      read by key per held name); never writes.
+
+Every figure is a stored one or a sum of them: a claim's close, stop and target are
+the forecaster's, a name's quantity and entry its Positions'.
+"""
+
+from __future__ import annotations
+
+from dataclasses import dataclass
+from typing import TYPE_CHECKING, Final, cast
+
+from contracts.positions import active_position_nodes
+
+if TYPE_CHECKING:
+    from datetime import date
+
+    from kernel import GraphStore, Node
+
+#: The forecaster's label and held-claim key prefix (agents/forecaster/barrier_store),
+#: named here so the dispatcher job loads no forecaster code; a test pins them equal.
+BARRIER_LABEL: Final = "BarrierForecast"
+HELD_CLAIM_PREFIX: Final = "barrier-garch-v1:held:"
+#: A held claim's `target_basis` once its close is at or past the declared target.
+PASSED_BASIS: Final = "rebased"
+_FIGURES = (
+    "entry_close",
+    "stop_price",
+    "target_price",
+    "p_stop_first",
+    "p_target_first",
+    "p_neither",
+    "horizon_sessions",
+)
+
+
+@dataclass(frozen=True)
+class HeldClaim:
+    """What the session's held claim says of one name, in cents and probabilities."""
+
+    close_cents: int
+    stop_cents: int
+    target_cents: int
+    passed: bool
+    p_stop: float
+    p_target: float
+    p_neither: float
+    horizon_sessions: int
+
+
+@dataclass(frozen=True)
+class HeldName:
+    """One held ticker: its lots summed, and its claim when the session has one."""
+
+    ticker: str
+    quantity: int
+    cost_cents: int
+    claim: HeldClaim | None
+
+    def gain_cents(self, claim: HeldClaim) -> int:
+        """The unrealised gain at the claim's close."""
+        return self.quantity * claim.close_cents - self.cost_cents
+
+    def above_target_cents(self, claim: HeldClaim) -> int:
+        """How far the close is above the declared target, for the whole holding."""
+        return self.quantity * (claim.close_cents - claim.target_cents)
+
+    def to_stop_cents(self, claim: HeldClaim) -> int:
+        """What the holding gives back from the close if it falls to its stop."""
+        return self.quantity * (claim.close_cents - claim.stop_cents)
+
+
+@dataclass(frozen=True)
+class BookOdds:
+    """The book on one session, as its held claims read it."""
+
+    as_of: date
+    names: tuple[HeldName, ...]
+
+    @property
+    def forecast(self) -> tuple[tuple[HeldName, HeldClaim], ...]:
+        """Each name the session's claims cover, with its claim."""
+        return tuple((n, n.claim) for n in self.names if n.claim is not None)
+
+    @property
+    def passed(self) -> tuple[tuple[HeldName, HeldClaim], ...]:
+        """The covered names whose close is at or past their declared target."""
+        return tuple((n, c) for n, c in self.forecast if c.passed)
+
+    @property
+    def unforecast(self) -> tuple[str, ...]:
+        """The held names the session has no readable claim for."""
+        return tuple(n.ticker for n in self.names if n.claim is None)
+
+    @property
+    def leaning_to_stop(self) -> tuple[tuple[str, float], ...]:
+        """Names likelier to hit their stop first than their target, likeliest first."""
+        leaning = [
+            (n.ticker, c.p_stop) for n, c in self.forecast if c.p_stop > c.p_target
+        ]
+        return tuple(sorted(leaning, key=lambda item: (-item[1], item[0])))
+
+    @property
+    def horizons(self) -> tuple[int, ...]:
+        """The claims' horizons in sessions, each once (the model has one: 10)."""
+        return tuple(sorted({c.horizon_sessions for _, c in self.forecast}))
+
+    def expected(self) -> tuple[float, float, float]:
+        """How many names the claims expect at target first, stop first, neither."""
+        claims = [c for _, c in self.forecast]
+        return (
+            sum(c.p_target for c in claims),
+            sum(c.p_stop for c in claims),
+            sum(c.p_neither for c in claims),
+        )
+
+
+def book_odds(graph: GraphStore, as_of: date) -> BookOdds | None:
+    """The book on ``as_of`` with each name's held claim; None when nothing is held."""
+    lots: dict[str, list[int]] = {}
+    for node in active_position_nodes(graph):
+        quantity = int(node.props["quantity"])
+        held = lots.setdefault(str(node.props["ticker"]), [0, 0])
+        held[0] += quantity
+        held[1] += quantity * int(node.props["opened_price_cents"])
+    if not lots:
+        return None
+    day = as_of.isoformat()
+    names = tuple(
+        HeldName(
+            ticker,
+            quantity,
+            cost,
+            _claim(graph.get_node(BARRIER_LABEL, f"{HELD_CLAIM_PREFIX}{ticker}:{day}")),
+        )
+        for ticker, (quantity, cost) in sorted(lots.items())
+    )
+    return BookOdds(as_of, names)
+
+
+def _claim(node: Node | None) -> HeldClaim | None:
+    """The claim's figures; None when there is no claim or a figure is not a number."""
+    if node is None:
+        return None
+    values = [node.props.get(name) for name in _FIGURES]
+    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
+        return None
+    close, stop, target, p_stop, p_target, p_neither, horizon = (
+        float(cast("float", v)) for v in values
+    )
+    return HeldClaim(
+        close_cents=round(close * 100),
+        stop_cents=round(stop * 100),
+        target_cents=round(target * 100),
+        passed=node.props.get("target_basis") == PASSED_BASIS,
+        p_stop=p_stop,
+        p_target=p_target,
+        p_neither=p_neither,
+        horizon_sessions=int(horizon),
+    )
diff --git a/orchestration/daily_brief_facts.py b/orchestration/daily_brief_facts.py
index 30f06e6f..da6a199a 100644
--- a/orchestration/daily_brief_facts.py
+++ b/orchestration/daily_brief_facts.py
@@ -15,11 +15,14 @@ import math
 import re
 from collections.abc import Mapping
 from dataclasses import dataclass, replace
+from datetime import date
 from typing import TYPE_CHECKING

 from agents.supervisor.domain.health import compute_health
 from contracts.run_posture import RUN_POSTURE_DEGRADED, run_posture
 from orchestration.batch_chain import CHAIN, POSITION_SYNC_KEY
+from orchestration.book_brief import book_lines
+from orchestration.book_odds import book_odds
 from orchestration.container_brief import container_line
 from orchestration.daily_brief_fills import fills_between, parse_instant, run_orders
 from orchestration.daily_brief_text import (
@@ -92,9 +95,18 @@ def brief_facts(
         scoreboard=_clause(snapshot),
         fills=fills_between(fills, reference.created if reference else None, created),
         last_stage=None,
+        book=book_lines(book_odds(graph, _session(nodes["RunRequest"]))),
     )


+def _session(request: Node) -> date:
+    """The run's session, the day its held claims are keyed by (DL-311)."""
+    try:
+        return date.fromisoformat(str(request.props.get("requested_at", ""))[:10])
+    except ValueError as exc:
+        raise BriefDataError("RunRequest.requested_at") from exc
+
+
 def _source_key(pm_run: Node) -> str:
     """A resumed run's PMRun links to the decision its Fills name (resume.py)."""
     return str(pm_run.props.get("linked_from_key") or pm_run.key)
diff --git a/orchestration/daily_brief_text.py b/orchestration/daily_brief_text.py
index e02721ff..d259cbf2 100644
--- a/orchestration/daily_brief_text.py
+++ b/orchestration/daily_brief_text.py
@@ -71,6 +71,7 @@ class BriefFacts:
     last_stage: str | None = None
     containers: str | None = None
     llm: str | None = None
+    book: tuple[str, ...] = ()


 def compose_brief(facts: BriefFacts) -> str:
@@ -92,6 +93,7 @@ def compose_brief(facts: BriefFacts) -> str:
             facts.scoreboard or "Scoreboard: not in this run's report",
             _orders(facts.orders),
             _fills(facts.fills),
+            *facts.book,
             *sensed,
             _needs_you(facts),
         )
diff --git a/surfaces/dashboard/app.py b/surfaces/dashboard/app.py
index e36bdf1f..667fcb8b 100644
--- a/surfaces/dashboard/app.py
+++ b/surfaces/dashboard/app.py
@@ -16,6 +16,7 @@ from urllib.parse import parse_qs
 from surfaces.dashboard import hold_answer_route, projections, projections_state
 from surfaces.dashboard.bundle_azure import container_logs
 from surfaces.dashboard.chat import handle_chat
+from surfaces.dashboard.projections_book import run_book
 from surfaces.dashboard.projections_fleet import fleet_projection
 from surfaces.dashboard.projections_infra import infra_projection
 from surfaces.dashboard.projections_performance import performance_vital
@@ -41,6 +42,7 @@ _RUN_VIEWS: dict[str, Callable[[GraphStore, str], object]] = {
     "flags": lambda g, r: projections_state.run_flags(g, r),
     "positions": projections_state.run_positions,
     "recovery": projections_state.run_recovery,
+    "book": run_book,
 }

 _CONTAINER = re.compile(r"[a-z0-9][a-z0-9-]{0,62}")
diff --git a/surfaces/dashboard/projections_book.py b/surfaces/dashboard/projections_book.py
new file mode 100644
index 00000000..da780eb6
--- /dev/null
+++ b/surfaces/dashboard/projections_book.py
@@ -0,0 +1,73 @@
+"""Dashboard book projection: the held names and their odds on the run's session.
+
+Agent: surfaces
+Role: project `orchestration.book_odds` for the selected run as one row per held
+      name and the brief's own book lines (DL-311, `SRF-OUT-09`), so the panel and
+      the brief say the same thing; the likeliest to reach its stop first leads.
+External I/O: reads the injected GraphStore; never writes.
+"""
+
+from __future__ import annotations
+
+from datetime import date
+from typing import TYPE_CHECKING
+
+from orchestration.book_brief import book_lines
+from orchestration.book_odds import book_odds
+from surfaces.dashboard.projections import run_request_node
+
+if TYPE_CHECKING:
+    from kernel import GraphStore
+    from orchestration.book_odds import HeldName
+
+
+def run_book(graph: GraphStore, run_id: str) -> dict[str, object]:
+    """The book on the run's session: the brief's lines and a row per held name."""
+    session = _session(graph, run_id)
+    odds = None if session is None else book_odds(graph, session)
+    return {
+        "as_of": None if session is None else session.isoformat(),
+        "lines": list(book_lines(odds)),
+        "rows": [] if odds is None else [_row(name) for name in _ordered(odds.names)],
+    }
+
+
+def _session(graph: GraphStore, run_id: str) -> date | None:
+    node = run_request_node(graph, run_id)
+    if node is None:
+        return None
+    try:
+        return date.fromisoformat(str(node.props.get("requested_at", ""))[:10])
+    except ValueError:
+        return None
+
+
+def _ordered(names: tuple[HeldName, ...]) -> list[HeldName]:
+    """Forecast names, likeliest to reach the stop first on top; then the rest."""
+    return sorted(
+        names,
+        key=lambda n: (n.claim is None, -(n.claim.p_stop if n.claim else 0), n.ticker),
+    )
+
+
+def _row(name: HeldName) -> dict[str, object]:
+    claim = name.claim
+    row: dict[str, object] = {
+        "ticker": name.ticker,
+        "quantity": name.quantity,
+        "forecast": claim is not None,
+    }
+    if claim is not None:
+        row.update(
+            {
+                "close_cents": claim.close_cents,
+                "stop_cents": claim.stop_cents,
+                "target_cents": claim.target_cents,
+                "past_target": claim.passed,
+                "p_target_first": claim.p_target,
+                "p_stop_first": claim.p_stop,
+                "p_neither": claim.p_neither,
+                "gain_cents": name.gain_cents(claim),
+            }
+        )
+    return row
diff --git a/surfaces/dashboard/static/book.js b/surfaces/dashboard/static/book.js
new file mode 100644
index 00000000..ea32164b
--- /dev/null
+++ b/surfaces/dashboard/static/book.js
@@ -0,0 +1,64 @@
+/* Trading panel: the book on the selected run's session, as its held forecasts read it.
+   The brief's own book lines head the panel; each held name follows, the likeliest to
+   reach its stop first leading. A run with no book or no forecast says so. */
+(function () {
+  "use strict";
+  var body = document.getElementById("bookbody");
+  if (!body) return;
+
+  function esc(value) {
+    return String(value == null ? "" : value).replace(/[&<>"']/g, function (c) {
+      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
+    });
+  }
+
+  function money(cents) {
+    if (cents == null) return "—";
+    var sign = cents < 0 ? "−" : "";
+    var abs = Math.abs(cents);
+    var whole = Math.floor(abs / 100).toLocaleString("en-US");
+    return sign + "$" + whole + "." + String(abs % 100).padStart(2, "0");
+  }
+
+  function pct(p) {
+    return p == null ? "—" : Math.round(p * 100) + " %";
+  }
+
+  function row(r) {
+    var past = r.past_target ? " <span class='chip good'>past target</span>" : "";
+    var none = r.forecast ? "" : " <span class='chip warn'>no forecast</span>";
+    return "<tr><td class='mono'>" + esc(r.ticker) + past + none + "</td><td class='mono'>" +
+      esc(r.quantity) + "</td><td class='mono'>" + money(r.close_cents) + "</td><td class='mono'>" +
+      money(r.stop_cents) + "</td><td class='mono'>" + money(r.target_cents) + "</td><td class='mono'>" +
+      pct(r.p_target_first) + "</td><td class='mono'>" + pct(r.p_stop_first) + "</td><td class='mono'>" +
+      money(r.gain_cents) + "</td></tr>";
+  }
+
+  function render(data) {
+    if (!data || data.error) {
+      body.innerHTML = "<p class='muted'>Book unavailable for this run.</p>";
+      return;
+    }
+    if (!data.rows || !data.rows.length) {
+      body.innerHTML = "<p class='muted'>Nothing held on this run's session.</p>";
+      return;
+    }
+    var lines = (data.lines || []).map(function (line) {
+      return "<p>" + esc(line) + "</p>";
+    }).join("");
+    body.innerHTML = lines + "<div style='overflow-x:auto'><table><thead><tr><th>Ticker</th>" +
+      "<th>Qty</th><th>Close</th><th>Stop</th><th>Target</th><th>Target first</th>" +
+      "<th>Stop first</th><th>Gain</th></tr></thead><tbody>" + data.rows.map(row).join("") +
+      "</tbody></table></div><p class='muted'>Odds over the next sessions from the nightly " +
+      "forecast, not yet scored on held names. Session " + esc(data.as_of) + ".</p>";
+  }
+
+  window.addEventListener("dashboard:run-selected", function (event) {
+    var runId = event.detail && event.detail.runId;
+    if (!runId) return;
+    fetch("/api/runs/" + encodeURIComponent(runId) + "/book")
+      .then(function (r) { return r.json(); })
+      .then(render)
+      .catch(function () { render(null); });
+  });
+})();
diff --git a/surfaces/dashboard/static/index.html b/surfaces/dashboard/static/index.html
index a44c8be0..3a8b0ca7 100644
--- a/surfaces/dashboard/static/index.html
+++ b/surfaces/dashboard/static/index.html
@@ -104,6 +104,7 @@
         <div class="panel"><h3>Positions — graph vs broker <a class="chip acc" href="https://app.alpaca.markets/" target="_blank" rel="noopener">Alpaca ↗</a></h3><div id="posbody"></div></div>
         <div class="panel"><h3>Recovery ladder</h3><div id="recbody"></div></div>
       </div>
+      <div class="panel" style="margin-top:12px"><h3>Book — what the held names stand to gain and lose</h3><div id="bookbody"></div></div>
     </section>
   </main>

@@ -147,5 +148,6 @@
   <script src="/chat.js?v=125-1"></script>
   <script src="/performance.js?v=20260925-scoreboard"></script>
   <script src="/scorecard.js?v=20260927-unattended"></script>
+  <script src="/book.js?v=20261021-book-odds"></script>
 </body>
 </html>
```

### Section 2 — the law cycle and both rollups (6 files)

```diff
diff --git a/docs/laws/INDEX.md b/docs/laws/INDEX.md
index 5227dc00..4bea1a93 100644
--- a/docs/laws/INDEX.md
+++ b/docs/laws/INDEX.md
@@ -52,8 +52,8 @@ Each agent's law files live at `agents/<name>/laws/`:
 | curator | ✅ LOCKED v1.1 (S205) | 23 / 47 | S205 rewrites and proves `CUR-TYP-01`; counters are clauses proven / clauses declared |
 | researcher | ✅ LOCKED v1.2 (DL-203) | 20 / 43 | DL-203 reconciles `PARAM` only; S205 rewrites and proves `RES-TYP-01`; counters are clauses proven / clauses declared |
 | master | ✅ LOCKED v1.12 (S277, DL-289) | 33 / 58 | S277 (DL-289 amendment 4) re-proves every-candidate probing, later proven fallback/key handover, refusal and unanswered pass-over, and recorded llm_fallbacks; no clause added. S276 (DL-289 amendment 1) adds and proves MST-OUT-05, MST-NEV-08 and MST-FAIL-08; amended MST-OUT-04, MST-NEV-07 and MST-OBS-04 re-proven for ordered candidate choice, key containment and recorded passed-over outcomes. Before that S272 (DL-297) adds and proves MST-TRG-03, MST-ORD-04 and MST-OBS-05 and proves amended MST-OUT-03; DRIFT-113 corrected, recovery at boot not built; before that S262 (DL-282) amends and re-proves `MST-OUT-04` for selected-vendor readiness and adds and proves `MST-NEV-07` for validated probe/key selection; DRIFT-105 corrected; before that S251 adds and proves `MST-FAIL-07` (the start-up refusal of an unhonourable remediation mode; remediation outside the constitution until DL-36 C/D; DRIFT-059); S244 amends and proves `MST-TRG-01`/`MST-ORD-02`, re-proves `MST-STA-02`/`MST-IDM-01`, and adds and proves `MST-IDM-03` (boot-id replay), `MST-ORD-03` (concurrent EHLO) and `MST-FAIL-06` (loud budget exhaustion), DRIFT-091; S232 adds and proves `MST-DEP-05` (substrate-only imports) and corrects `MST-NEV-01`/`MST-SEC-03`/`MST-DEP-03` to name the pack data actually consulted; DL-203 reconciles `PARAM` only; S217 adds and proves `MST-OUT-04` whole-fleet readiness and `MST-FAIL-05` classification; S205 rewrites and proves `MST-TYP-01`; S188 adds and proves credential-test handover guards; RSA/Key Vault clauses deferred S74; S204 gives every clause a row and makes rowless clauses a hard gate |
-| dispatcher | ✅ LOCKED v1.7 (S285, DL-309) | 46 / 49 | S285 (DL-309) adds and proves DSP-NEV-04 (a placed run is never held again) and DSP-OBS-04 (each fire's line says what it did), amends DSP-TRG-01 and DSP-PERF-01 (the last placing fire is the 23:10 tick) and DSP-IDM-02, and proves DSP-TYP-01 with the fourth action, `already-placed`. S278 (DL-301 amendment 7) amends and re-proves DSP-IN-05 for named platform failures, unknown warnings except the five measured deploy/wake by-products, and the platform's own safe why; A31-A37 also re-prove DSP-IDM-04 and DSP-OUT-07. No clause added; count unchanged. S277 (DL-289 amendment 4) re-proves DSP-OUT-09 with activation parts before the runs switch lines; no clause added. S276 (DL-289 amendment 1) adds and proves DSP-OUT-09 for the brief LLM line; DSP-DEP-01 and CAP include recent AgentInstance reads, dependency envelope still gray. Before that S275 (DL-301 amendments 1 and 2) adds and proves the ten sensor clauses; A1–A30 pass and all 35 specified breaks turn a builder test red, then restore. S251 names the daily brief in the purpose line and `DSP-IDN-03` (DRIFT-077); Component book under `orchestration/laws/dispatcher/`; scheduled placement, the human-hold loop and the daily brief (S234, DL-230/DL-231); `orchestration.dispatcher.Dispatcher` named out of scope by DL-221; closes DRIFT-068 and DRIFT-069 |
-| surfaces | ✅ LOCKED v1.8 (S274, S270, S267, S263, S262, S251, S236, S229, S228) | 31 / 38 | S274 (DL-300) reconciles `PARAM` only: `master_window_start_utc` is 22:00, the master's live wake (DL-294 amendment 1); no clause changes; before that S270 (DL-295) reconciles `PARAM` only: `window_end_utc` is 23:30 and the new `window_days_utc` is 1-5, the operator's wake window (DL-294); no clause changes; before that S267 (DL-288) adds and proves `SRF-DEP-04`: complete-tag evidence from every attempt of a successful image-build run, latest first and earlier attempts newest first, with main-history and unreadable-evidence guards; DRIFT-111 corrected; before that S263 (DL-284) amends and re-proves `SRF-DEP-03` for model-family disconnection and its start-up reason; before that S262 (DL-282) adds and proves `SRF-DEP-03`: dashboard chat binds only through its selected provider and disconnects for absent keys, unknown providers and either vendor configuration error; DRIFT-105 corrected; before that S251 narrows `SRF-OUT-03` (quick asks write no audit fact; DRIFT-078); Component book under `surfaces/laws/`; dashboard, CLI, MCP, chat and operator-intent write boundaries; S236 adds and proves `SRF-OUT-08` (the unattended scorecard) and the `scorecard` tool, and files DRIFT-078; selected-run scoping cites corrected DRIFT-022 |
+| dispatcher | ✅ LOCKED v1.8 (S287, DL-311) | 47 / 50 | S287 (DL-311) adds and proves DSP-OUT-10 (the brief's book lines: the held names past their declared target and the forecast's odds, from the active Positions and the session's held claims read by key), amends DSP-DEP-01 and CAP for the Position and BarrierForecast reads, and moves DSP-OUT-09 back under Outputs. S285 (DL-309) adds and proves DSP-NEV-04 (a placed run is never held again) and DSP-OBS-04 (each fire's line says what it did), amends DSP-TRG-01 and DSP-PERF-01 (the last placing fire is the 23:10 tick) and DSP-IDM-02, and proves DSP-TYP-01 with the fourth action, `already-placed`. S278 (DL-301 amendment 7) amends and re-proves DSP-IN-05 for named platform failures, unknown warnings except the five measured deploy/wake by-products, and the platform's own safe why; A31-A37 also re-prove DSP-IDM-04 and DSP-OUT-07. No clause added; count unchanged. S277 (DL-289 amendment 4) re-proves DSP-OUT-09 with activation parts before the runs switch lines; no clause added. S276 (DL-289 amendment 1) adds and proves DSP-OUT-09 for the brief LLM line; DSP-DEP-01 and CAP include recent AgentInstance reads, dependency envelope still gray. Before that S275 (DL-301 amendments 1 and 2) adds and proves the ten sensor clauses; A1–A30 pass and all 35 specified breaks turn a builder test red, then restore. S251 names the daily brief in the purpose line and `DSP-IDN-03` (DRIFT-077); Component book under `orchestration/laws/dispatcher/`; scheduled placement, the human-hold loop and the daily brief (S234, DL-230/DL-231); `orchestration.dispatcher.Dispatcher` named out of scope by DL-221; closes DRIFT-068 and DRIFT-069 |
+| surfaces | ✅ LOCKED v1.9 (S287, S274, S270, S267, S263, S262, S251, S236, S229, S228) | 32 / 39 | S287 (DL-311) adds and proves `SRF-OUT-09` (the selected run's book panel: the brief's book lines and a row per held name, the likeliest to reach its stop first leading) and aligns the test-plan's status line; before that S274 (DL-300) reconciles `PARAM` only: `master_window_start_utc` is 22:00, the master's live wake (DL-294 amendment 1); no clause changes; before that S270 (DL-295) reconciles `PARAM` only: `window_end_utc` is 23:30 and the new `window_days_utc` is 1-5, the operator's wake window (DL-294); no clause changes; before that S267 (DL-288) adds and proves `SRF-DEP-04`: complete-tag evidence from every attempt of a successful image-build run, latest first and earlier attempts newest first, with main-history and unreadable-evidence guards; DRIFT-111 corrected; before that S263 (DL-284) amends and re-proves `SRF-DEP-03` for model-family disconnection and its start-up reason; before that S262 (DL-282) adds and proves `SRF-DEP-03`: dashboard chat binds only through its selected provider and disconnects for absent keys, unknown providers and either vendor configuration error; DRIFT-105 corrected; before that S251 narrows `SRF-OUT-03` (quick asks write no audit fact; DRIFT-078); Component book under `surfaces/laws/`; dashboard, CLI, MCP, chat and operator-intent write boundaries; S236 adds and proves `SRF-OUT-08` (the unattended scorecard) and the `scorecard` tool, and files DRIFT-078; selected-run scoping cites corrected DRIFT-022 |

 See [ledger.md](ledger.md) for the canonical version of this table.

diff --git a/docs/laws/ledger.md b/docs/laws/ledger.md
index 02edbb14..8744db40 100644
--- a/docs/laws/ledger.md
+++ b/docs/laws/ledger.md
@@ -49,8 +49,8 @@ and torn down to zero. Historical Neo4j rows remain valid evidence for the pre-S
 | operator | ✅ v1.10 (LOCKED) | 20 / 51 | 🟨 partial — **20 of 51 clauses proven** after S269 (DL-292) rewords and re-proves `OPR-FAIL-02`: only text, a number or a boolean is a value; `null`, lists and objects are omitted from required and optional parameters, so missing required values are refused with the existing sentence and audit, while scalar text and blank-text behavior are unchanged; DRIFT-112 corrected; no clause added; before that S268 (DL-290) rewords and re-proves `OPR-FAIL-02`: an intent of no known family, or lacking a parameter its family requires under any accepted name, is refused before its audit, which reads `refused`, and no `Intent` is written; the prompt states each family's parameter names; DRIFT-109 corrected; no clause added; before that S265 (DL-286) rewords and re-proves `OPR-FAIL-01`: failed requests are audited on both capabilities, one operator fault and one plain reason, no grammar or error text in graph; malformed JSON is a fault-free refusal; DRIFT-107/108 corrected; no clause added; before that S264 (DL-285) re-proves `OPR-STA-03` for vendor stop reasons and billed counts on both reply paths and adds/proves `OPR-FAIL-04` for audited, fault-free cut-offs with one sentence and explicit grammar preserved; DRIFT-106 corrected; before that S263 (DL-284) amends and re-proves `OPR-DEP-01` for provider effort resolution and pre-call model-family refusal; PARAM effort and CAP reconciled; before that S262 (DL-282) amends and re-proves `OPR-DEP-01` for the selected vendor, model resolution and no fallback; PARAM reconciled; before that S256 (DL-272) rewrites and proves `OPR-IDM-02`: duplicate commands share audit/intent while every model call has its own row; DRIFT-104 corrected; S222 proves `OPR-SEC-01` key containment and `OPR-DEP-01` Anthropic-only dependency; S205 rewrites and proves `OPR-TYP-01`; 31 have a gray row |
 | supervisor | ✅ v1.3 (LOCKED) | 23 / 48 | 🟨 partial — **23 of 48 clauses proven** after S251 (DL-260) declares the divergence-family exception in `SUP-IDN-02` (DRIFT-094) and proves `SUP-OBS-02` on its real sources (live `Fault` incidents, unresolved critical Flags; DRIFT-076); v1.2 (DL-225) was never reflected here and is now; after S205 rewrites and proves `SUP-TYP-01`; S179 proves append-only `FaultResolution` retirement (`SUP-OBS-03`); 26 have a gray row |
 | master | ✅ v1.12 (LOCKED) | 33 / 58 | S277 (DL-289 amendment 4) re-proves every-candidate probing, later proven fallback/key handover, refusal and unanswered pass-over, and recorded llm_fallbacks; no clause added. S276 (DL-289 amendment 1) adds and proves MST-OUT-05, MST-NEV-08 and MST-FAIL-08; amended MST-OUT-04, MST-NEV-07 and MST-OBS-04 re-proven for ordered candidate choice, key containment and recorded passed-over outcomes. 🟨 partial — **33 of 58 clauses proven** after S272 (DL-297) adds and proves MST-TRG-03, MST-ORD-04 and MST-OBS-05 and proves amended MST-OUT-03; DRIFT-113 corrected, recovery at boot not built; before that S262 (DL-282) amends and re-proves `MST-OUT-04` for selected-vendor readiness and adds and proves `MST-NEV-07` for validated probe/key selection; DRIFT-105 corrected; before that S251 (DL-260) adds and proves `MST-FAIL-07`: master refuses to start in a remediation mode it cannot honour; attempting remediation is stated outside the constitution until DL-36 Pieces C/D (DRIFT-059); after S244 amends and proves `MST-TRG-01` (`POST /ehlo`, the agent's bounded resend with one boot id) and `MST-ORD-02` (master may be asleep or busy), re-proves `MST-STA-02`/`MST-IDM-01` on their amended text, and adds and proves `MST-IDM-03` (a repeated boot id replays), `MST-ORD-03` (concurrent EHLO service) and `MST-FAIL-06` (a spent budget exits loud); S232 adds and proves `MST-DEP-05` (substrate-only imports) and corrects `MST-NEV-01`/`MST-SEC-03`/`MST-DEP-03` to name the pack data actually consulted; S217 adds and proves `MST-OUT-04` whole-fleet readiness and `MST-FAIL-05` classification; S205 rewrites and proves `MST-TYP-01`; S188 adds and proves credential-test handover guards; S204 gives every clause a row and promotes missing rows to a hard gate · RSA signing + Key Vault + integration clauses deferred (S73/S74) |
-| dispatcher | ✅ v1.7 (LOCKED) | 46 / 49 | S285 (DL-309) adds and proves DSP-NEV-04 (a placed run is never held again) and DSP-OBS-04 (each fire's line says what it did), amends DSP-TRG-01 and DSP-PERF-01 (the last placing fire is the 23:10 tick) and DSP-IDM-02, and proves DSP-TYP-01 with the fourth action, `already-placed`. S278 (DL-301 amendment 7) amends and re-proves DSP-IN-05 for named platform failures, unknown warnings except the five measured deploy/wake by-products, and the platform's own safe why; A31-A37 also re-prove DSP-IDM-04 and DSP-OUT-07. No clause added; count unchanged. S277 (DL-289 amendment 4) re-proves DSP-OUT-09 with activation parts before the runs switch lines; no clause added. S276 (DL-289 amendment 1) adds and proves DSP-OUT-09 for the brief LLM line; DSP-DEP-01 and CAP include recent AgentInstance reads, dependency envelope still gray. S275 (DL-301 amendments 1 and 2) adds and proves the ten sensor clauses; A1–A30 pass and all 35 specified breaks turn a builder test red, then restore. 🟨 partial — **46 of 49 clauses proven**; S251 names the daily brief in the purpose line and `DSP-IDN-03`'s scope (DRIFT-077), count unchanged; after S234 adds and proves the daily brief (`DSP-IDN-04`, `DSP-TRG-03`, `DSP-OUT-06`, `DSP-IDM-03`, `DSP-SEC-02`, `DSP-FAIL-03`) and proves `DSP-SEC-01` across every port operation; `DSP-DEP-01` amended and still gray (partial: `CAP` conformance). S229 covered scheduled run placement, readiness holds, degraded placement, human answers and notices; names `orchestration.dispatcher.Dispatcher` out of scope by DL-221; closes DRIFT-068 and DRIFT-069. |
-| surfaces | ✅ v1.8 (LOCKED) | 31 / 38 | 🟨 partial — **31 of 38 clauses proven**; S274 (DL-300) reconciles `PARAM` only: `master_window_start_utc` is 22:00, the master's live wake (DL-294 amendment 1); no clause changes; before that S270 (DL-295) reconciles `PARAM` only: `window_end_utc` is 23:30 and the new `window_days_utc` is 1-5, the operator's wake window (DL-294); no clause changes; before that S267 (DL-288) adds and proves `SRF-DEP-04`: complete-tag evidence from every attempt of a successful image-build run, latest first and earlier attempts newest first, with main-history and unreadable-evidence guards; DRIFT-111 corrected; before that S263 (DL-284) amends and re-proves `SRF-DEP-03` for model-family disconnection and its start-up reason; before that S262 (DL-282) adds and proves `SRF-DEP-03`: dashboard chat binds only through its selected provider and disconnects for absent keys, unknown providers and either vendor configuration error; DRIFT-105 corrected; before that S251 narrows `SRF-OUT-03` to model-composed answers and names the quick asks as graph reads that write no audit fact (DRIFT-078), count unchanged; after S236 adds and proves `SRF-OUT-08` (the unattended vital and the `scorecard` answer: G1, G3 and two clocks from the acceptance gate's verdict and the records human actions leave) and lists `scorecard` in `SRF-TRG-02`; DRIFT-078 is filed for `SRF-OUT-03`'s silence on the quick asks. S228 added and proved `SRF-OUT-07` (28 of 35); S229 authored the book (27 of 34). Covers dashboard, CLI, MCP, chat and operator-intent write boundaries; selected-run scoping cites DRIFT-022 as already corrected. |
+| dispatcher | ✅ v1.8 (LOCKED) | 47 / 50 | S287 (DL-311) adds and proves DSP-OUT-10 (the brief's book lines: the held names past their declared target and the forecast's odds, from the active Positions and the session's held claims read by key), amends DSP-DEP-01 and CAP for the Position and BarrierForecast reads, and moves DSP-OUT-09 back under Outputs. S285 (DL-309) adds and proves DSP-NEV-04 (a placed run is never held again) and DSP-OBS-04 (each fire's line says what it did), amends DSP-TRG-01 and DSP-PERF-01 (the last placing fire is the 23:10 tick) and DSP-IDM-02, and proves DSP-TYP-01 with the fourth action, `already-placed`. S278 (DL-301 amendment 7) amends and re-proves DSP-IN-05 for named platform failures, unknown warnings except the five measured deploy/wake by-products, and the platform's own safe why; A31-A37 also re-prove DSP-IDM-04 and DSP-OUT-07. No clause added; count unchanged. S277 (DL-289 amendment 4) re-proves DSP-OUT-09 with activation parts before the runs switch lines; no clause added. S276 (DL-289 amendment 1) adds and proves DSP-OUT-09 for the brief LLM line; DSP-DEP-01 and CAP include recent AgentInstance reads, dependency envelope still gray. S275 (DL-301 amendments 1 and 2) adds and proves the ten sensor clauses; A1–A30 pass and all 35 specified breaks turn a builder test red, then restore. 🟨 partial — **47 of 50 clauses proven**; S251 names the daily brief in the purpose line and `DSP-IDN-03`'s scope (DRIFT-077), count unchanged; after S234 adds and proves the daily brief (`DSP-IDN-04`, `DSP-TRG-03`, `DSP-OUT-06`, `DSP-IDM-03`, `DSP-SEC-02`, `DSP-FAIL-03`) and proves `DSP-SEC-01` across every port operation; `DSP-DEP-01` amended and still gray (partial: `CAP` conformance). S229 covered scheduled run placement, readiness holds, degraded placement, human answers and notices; names `orchestration.dispatcher.Dispatcher` out of scope by DL-221; closes DRIFT-068 and DRIFT-069. |
+| surfaces | ✅ v1.9 (LOCKED) | 32 / 39 | 🟨 partial — **32 of 39 clauses proven**; S287 (DL-311) adds and proves `SRF-OUT-09` (the selected run's book panel: the brief's book lines and a row per held name, the likeliest to reach its stop first leading) and aligns the test-plan's status line; before that S274 (DL-300) reconciles `PARAM` only: `master_window_start_utc` is 22:00, the master's live wake (DL-294 amendment 1); no clause changes; before that S270 (DL-295) reconciles `PARAM` only: `window_end_utc` is 23:30 and the new `window_days_utc` is 1-5, the operator's wake window (DL-294); no clause changes; before that S267 (DL-288) adds and proves `SRF-DEP-04`: complete-tag evidence from every attempt of a successful image-build run, latest first and earlier attempts newest first, with main-history and unreadable-evidence guards; DRIFT-111 corrected; before that S263 (DL-284) amends and re-proves `SRF-DEP-03` for model-family disconnection and its start-up reason; before that S262 (DL-282) adds and proves `SRF-DEP-03`: dashboard chat binds only through its selected provider and disconnects for absent keys, unknown providers and either vendor configuration error; DRIFT-105 corrected; before that S251 narrows `SRF-OUT-03` to model-composed answers and names the quick asks as graph reads that write no audit fact (DRIFT-078), count unchanged; after S236 adds and proves `SRF-OUT-08` (the unattended vital and the `scorecard` answer: G1, G3 and two clocks from the acceptance gate's verdict and the records human actions leave) and lists `scorecard` in `SRF-TRG-02`; DRIFT-078 is filed for `SRF-OUT-03`'s silence on the quick asks. S228 added and proved `SRF-OUT-07` (28 of 35); S229 authored the book (27 of 34). Covers dashboard, CLI, MCP, chat and operator-intent write boundaries; selected-run scoping cites DRIFT-022 as already corrected. |

 *2026-09-23 — [DL-203](../design-log.md) (work-queue item 33) amended nine of these laws in
 their `PARAM` tables only — analyst, deliberator, execution, forecaster, master,
diff --git a/orchestration/laws/dispatcher/laws.md b/orchestration/laws/dispatcher/laws.md
index 26c88798..a58f0f4a 100644
--- a/orchestration/laws/dispatcher/laws.md
+++ b/orchestration/laws/dispatcher/laws.md
@@ -1,6 +1,6 @@
 # `Dispatcher` — Laws

-**Prefix:** `DSP` · **status:** LOCKED v1.7 · **Owner:** Yury Gurevich
+**Prefix:** `DSP` · **status:** LOCKED v1.8 · **Owner:** Yury Gurevich

 > Decide whether the scheduled daily graph-pull run is placed, skipped, held, or placed in degraded posture,
 > brief the operator once on each run it placed, and tell the operator when a container of the
@@ -117,15 +117,32 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   it recorded no alarm in 24 hours; or how many alarms it recorded in 24 hours, repeats counted as in
   `DSP-OUT-07`, naming at most three kinds of failure with their apps and counting the rest. Before the
   first read the brief carries no such line.
-
-## Prohibitions (`NEV`)
-
 - **DSP-OUT-09** — A brief whose last 24 hours hold an `AgentInstance` activated on an LLM candidate
   with another passed over, or whose run's `DeliberationRun` names an `llm_switches` line, carries
   one line after the container line and before needs-you: `LLM: ` then, for each distinct choice and
   passed-over list, the agent types sorted, ` on ` the chosen `vendor/model/effort`, and in brackets
   `passed over ` each passed-over line; then each `llm_switches` line followed by ` during the run`;
   the parts joined by ` · `. With neither there is no line.
+- **DSP-OUT-10** — A finished brief whose book holds a name carries the book's lines after the
+  fills and before the container line (DL-311). The book is the active `Position` lots, summed by
+  ticker (the quantity, and the cost as quantity × `opened_price_cents`), each joined to its held
+  claim for the run's session, read by key (`barrier-garch-v1:held:{ticker}:{session}`, the session
+  being the `RunRequest`'s `requested_at`), never by listing the claims; a claim lacking a figure the
+  lines need, or holding one that is not a number, is no claim. With no claim for the session the
+  brief carries one line, `Book: N held · no forecast for <session>`. Otherwise two. The first is
+  `Book: N held · ` then, over the claims whose `target_basis` is `rebased` (the close at or past the
+  declared target): how many, their gain now (quantity × close − cost), the part of it above the
+  target (quantity × (close − `target_price`)) and their gain at their stops (the gain less quantity
+  × (close − `stop_price`)); or `none past its target`. The second is `Odds, next H sessions, M names
+  (not yet scored): ` then the sums of the claims' `p_target_first`, `p_stop_first` and `p_neither`
+  to one decimal; then the names whose `p_stop_first` exceeds their `p_target_first`, likeliest
+  first and ties by ticker, three named with their chance in whole percent and the rest counted;
+  then the held names with no claim, four named and the rest counted. Prices are cents rounded from
+  the claim's dollars, and every figure is a stored one or a sum of them. A RED brief carries no
+  book line.
+
+## Prohibitions (`NEV`)
+
 - **DSP-NEV-01** — The scheduled dispatcher never writes master-owned `FleetPreflight` evidence.
 - **DSP-NEV-02** — The scheduled dispatcher never talks to the broker, never chooses tickers beyond
   the configured universe membership, and never decides what to buy, sell, size, or veto.
@@ -211,7 +228,9 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   (`DEP-CLOCK`), provider-owned market calendar, configured universe source, and Telegram port for
   optional operator notices, answers, and the daily brief. For the brief its graph reads include the
   run's chain to its `Snapshot`, `Fill`, `Fault` and `Flag` facts with their resolutions, the
-  master's `AgentInstance` records of the last 24 hours, and the pack's acceptance verdict. The sensor depends on the job's managed-identity endpoint and the log
+  master's `AgentInstance` records of the last 24 hours, the active `Position` lots and the
+  forecaster's held `BarrierForecast` claims for the run's session, and the pack's acceptance
+  verdict. The sensor depends on the job's managed-identity endpoint and the log
   workspace's query API.

 ## Observability & audit (`OBS`)
@@ -248,7 +267,8 @@ green only when a functional test cites its ID (conventions §3). Tests + status
       "FleetPreflight", "RunRequest", "RunHold", "RunHoldAnswer", "MarketData", "ScanRun",
       "AnalystRun", "PMRun", "DeliberationRun", "OrderIntent", "ExecutionRun", "MonitorRun",
       "Snapshot", "Fill", "Fault", "FaultResolution", "Flag", "FlagResolution",
-      "BrokerPositionSnapshot", "ContainerEvent", "ContainerSensorRead", "AgentInstance"
+      "BrokerPositionSnapshot", "ContainerEvent", "ContainerSensorRead", "AgentInstance",
+      "Position", "BarrierForecast"
     ],
     "access": "bounded dispatcher placement; the brief marks only its own RunRequest"
   },
@@ -321,3 +341,8 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   by the fire's tick, and leaves a run 20 minutes before the 23:30 window end; a placed run is
   never held again; each fire's line says what it did. New `DSP-NEV-04` and `DSP-OBS-04`;
   `DSP-TRG-01`, `DSP-IDM-02`, `DSP-TYP-01` (now proven) and `DSP-PERF-01` amended.
+- v1.8 — S287 (DL-311, work-queue 92): the brief's book lines, the held names past their
+  declared target and the forecast's odds for the book, read from the active Positions and the
+  session's held claims by key. New `DSP-OUT-10`; `DSP-DEP-01` and `CAP` amended for the
+  `Position` and `BarrierForecast` reads. `DSP-OUT-09` moves back under Outputs: since v1.4 it
+  sat under the Prohibitions heading. 46 / 49 → 47 / 50.
diff --git a/orchestration/laws/dispatcher/test-plan.md b/orchestration/laws/dispatcher/test-plan.md
index a30a720d..9b668bce 100644
--- a/orchestration/laws/dispatcher/test-plan.md
+++ b/orchestration/laws/dispatcher/test-plan.md
@@ -1,6 +1,6 @@
 # `Dispatcher` — Law Test-Plan

-**Prefix:** `DSP` · **status:** LOCKED v1.7 · **aligned with:** laws.md LOCKED v1.7
+**Prefix:** `DSP` · **status:** LOCKED v1.8 · **aligned with:** laws.md LOCKED v1.8

 | Clause | Description | Test | Status |
 | --- | --- | --- | --- |
@@ -36,7 +36,7 @@
 | DSP-TYP-01 | `ScheduledDispatchResult` action space is `placed`, `already-placed`, `skipped`, or `held`, with readiness details only when relevant. | `tests/test_dispatch_fire_lines.py::test_the_result_names_one_of_four_actions_and_readiness_only_when_held` | 🟩 |
 | DSP-SEC-01 | Telegram credentials remain inside the injected Telegram port and are never logged or returned by scheduled-dispatch logic. | `tests/test_dispatcher_credential.py::test_the_bot_credential_never_leaves_the_port_on_any_path`; `orchestration/tests/test_container_vocabulary.py::test_a28_send_alarm_posts_only_chat_and_plain_text` | 🟩 |
 | DSP-SEC-02 | P&L amounts leave the dispatcher only in the daily brief, only to the configured operator chat, and only through the injected Telegram port (DL-230); the job's printed output and every fault carry no amount, a brief's fault naming its step and an error type, never a value. | `tests/test_dispatch_brief_script.py::test_a10_no_amount_leaves_through_the_job_log_or_a_fault`; `orchestration/tests/test_daily_brief_dispatch.py::test_a6_a_failed_send_changes_nothing_else_and_the_next_fire_retries`; `orchestration/tests/test_daily_brief_boundaries.py::test_a7_a_malformed_snapshot_is_a_fault_and_nothing_else`; `orchestration/tests/test_telegram_brief.py::test_send_brief_posts_plain_text_to_the_configured_chat_only`; `orchestration/tests/test_telegram_brief.py::test_a_refused_brief_leaves_the_ports_error_word_and_never_its_text`; `tests/test_dispatcher_credential.py::test_the_bot_credential_never_leaves_the_port_on_any_path` | 🟩 |
-| DSP-DEP-01 | The scheduled dispatcher depends on graph, UTC clock, provider calendar, universe source and Telegram for optional notices, answers and brief. Brief reads include its run chain to Snapshot, Fill, Fault and Flag with resolutions, master-owned AgentInstance records of the last 24 hours, and pack acceptance. Sensor depends on managed identity and the log query API. | partial: `orchestration/tests/test_dispatcher_capability.py::test_every_fire_stays_inside_the_declared_capability` holds the graph reads, writes and Telegram operations of real fires against `CAP`; no test proves the UTC clock, provider calendar or universe-source dependencies; partial AgentInstance reads: `orchestration/tests/test_llm_brief_candidates.py::test_a22_llm_line_groups_replicas_and_filters_old_or_undated`; `orchestration/tests/test_llm_brief_candidates.py::test_a24_real_fire_carries_the_candidate_line`; clock/calendar/universe dependencies remain unproven | ⬜ |
+| DSP-DEP-01 | The scheduled dispatcher depends on graph, UTC clock, provider calendar, universe source and Telegram for optional notices, answers and brief. Brief reads include its run chain to Snapshot, Fill, Fault and Flag with resolutions, master-owned AgentInstance records of the last 24 hours, active Position lots and the session's held BarrierForecast claims, and pack acceptance. Sensor depends on managed identity and the log query API. | partial: `orchestration/tests/test_dispatcher_capability.py::test_every_fire_stays_inside_the_declared_capability` holds the graph reads, writes and Telegram operations of real fires against `CAP`; no test proves the UTC clock, provider calendar or universe-source dependencies; partial AgentInstance reads: `orchestration/tests/test_llm_brief_candidates.py::test_a22_llm_line_groups_replicas_and_filters_old_or_undated`; `orchestration/tests/test_llm_brief_candidates.py::test_a24_real_fire_carries_the_candidate_line`; clock/calendar/universe dependencies remain unproven | ⬜ |
 | DSP-OBS-01 | Holds, releases, answers, notices, degraded causes, and Telegram faults are reconstructable from graph facts and returned results. | `orchestration/tests/test_scheduled_dispatch_notices.py::test_c2_new_hold_sends_one_notice_and_marks_the_hold`; `orchestration/tests/test_scheduled_dispatch_notices.py::test_c6_run_now_places_despite_a_failing_preflight`; `orchestration/tests/test_scheduled_dispatch_degraded_notices.py::test_degraded_run_sends_one_informational_notice_and_no_hold`; `orchestration/tests/test_scheduled_dispatch_polling.py::test_c12_telegram_outage_records_a_fault_without_stopping_dispatch` | 🟩 |
 | DSP-OBS-02 | Human notice deadlines name Melbourne time first and include UTC fallback. | `orchestration/tests/test_act_by_local_time.py::test_act_by_reads_melbourne_first_and_follows_daylight_saving`; `orchestration/tests/test_act_by_local_time.py::test_act_by_falls_back_to_utc_without_usable_zone_data`; `orchestration/tests/test_act_by_local_time.py::test_a_new_hold_notice_carries_the_local_deadline` | 🟩 |
 | DSP-PERF-01 | Human override placement is bounded to the 22:30-23:10 UTC action window. | `orchestration/tests/test_scheduled_dispatch_polling.py::test_late_run_now_is_recorded_but_never_placed`; `orchestration/tests/test_scheduled_dispatch_once.py::test_a_held_run_released_at_the_2310_fire_is_placed_and_at_2320_is_not`; `orchestration/tests/test_daily_brief_boundaries.py::test_a4_the_brief_survives_the_windows_early_return` | 🟩 |
@@ -53,3 +53,4 @@
 | DSP-OUT-09 | A recent activation with another candidate passed over, or the runs DeliberationRun naming switches, adds one LLM line after containers and before needs-you. Sorted agent types are grouped by distinct choice/passed-over list with chosen vendor/model/effort and reasons; then each run switch followed by during the run. Parts join with the middle-dot separator; neither fact means no line. | `orchestration/tests/test_llm_brief_candidates.py::test_a21_quiet_night_has_no_llm_line`; `test_a22_llm_line_groups_replicas_and_filters_old_or_undated`; `test_a23_llm_line_follows_container_before_needs_you`; `test_a24_real_fire_carries_the_candidate_line`; `orchestration/tests/test_llm_brief_switches.py::test_a19_brief_names_each_switch_in_run_order`; `orchestration/tests/test_llm_brief_switches.py::test_a20_activation_parts_precede_run_switches`; `orchestration/tests/test_llm_brief_switches.py::test_a21_no_switch_means_no_line`; `orchestration/tests/test_llm_brief_switches.py::test_a22_real_fire_carries_the_runs_switch` | 🟩 |
 | DSP-NEV-04 | The dispatcher never holds a run whose day-keyed `RunRequest` exists: a later fire reads no readiness, writes no `RunHold` and sends no hold notice; it reports `already-placed` and, inside the action window, retries only an unsent degraded notice. | `orchestration/tests/test_scheduled_dispatch_once.py::test_a_placed_run_is_never_held_when_a_later_check_fails`; `orchestration/tests/test_scheduled_dispatch_once.py::test_an_override_placed_run_is_already_placed_at_the_next_fire`; `orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only`; `orchestration/tests/test_scheduled_dispatch_notices.py::test_c5_rehold_after_release_gets_its_own_notice` | 🟩 |
 | DSP-OBS-04 | Each fire prints one line naming what it did and why: `placed` with the calendar's reason, `already-placed` on every later fire, `held` with the readiness state or that the action window has passed, `skipped` with the calendar's reason, the operator, or which side of the action window the fire is on. | `tests/test_dispatch_fire_lines.py::test_each_fire_prints_what_it_did`; `tests/test_dispatch_fire_lines.py::test_a_skip_answer_still_says_operator`; `orchestration/tests/test_scheduled_dispatch_once.py::test_a_night_places_the_run_once_and_every_later_fire_says_so` | 🟩 |
+| DSP-OUT-10 | A finished brief whose book holds a name carries the book's lines after the fills: the active Positions by ticker joined to the session's held claims, read by key; one line with no claim, else the names past their declared target (gain now, above target, at their stops) and the odds line (expected target first, stop first, neither; three likelier to stop; four with no forecast). A RED brief has none. | `orchestration/tests/test_book_odds.py::test_the_book_joins_each_held_name_to_its_sessions_claim`; `orchestration/tests/test_book_odds.py::test_a_name_without_a_readable_claim_is_unforecast`; `orchestration/tests/test_book_odds.py::test_nothing_held_is_no_book`; `orchestration/tests/test_book_odds.py::test_the_book_reads_positions_once_and_each_claim_by_key`; `orchestration/tests/test_book_odds.py::test_the_label_and_prefix_are_the_forecasters`; `orchestration/tests/test_book_brief.py::test_the_book_line_totals_the_names_past_their_target`; `orchestration/tests/test_book_brief.py::test_the_odds_line_sums_the_claims_and_names_the_likelier_to_stop`; `orchestration/tests/test_book_brief.py::test_a_book_with_no_claim_says_so_in_one_line`; `orchestration/tests/test_book_brief.py::test_no_name_past_its_target_reads_none`; `orchestration/tests/test_daily_brief_book.py::test_a_finished_brief_carries_the_book_after_its_fills`; `orchestration/tests/test_daily_brief_book.py::test_a_red_brief_carries_no_book`; `orchestration/tests/test_daily_brief_book.py::test_a_malformed_session_names_its_field` | 🟩 |
diff --git a/surfaces/laws/laws.md b/surfaces/laws/laws.md
index 0640b0c8..c330524c 100644
--- a/surfaces/laws/laws.md
+++ b/surfaces/laws/laws.md
@@ -1,6 +1,6 @@
 # `Surfaces` — Laws

-**Prefix:** `SRF` · **status:** LOCKED v1.8 · **Owner:** Yury Gurevich
+**Prefix:** `SRF` · **status:** LOCKED v1.9 · **Owner:** Yury Gurevich

 > Project graph-backed operating evidence to the human and route only bounded, audited operator intents.

@@ -74,6 +74,14 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   graph cannot see are listed with every answer. The window is dates: the selected run does not scope
   it, and `SRF-OUT-01` does not cover it. An empty window or an unreadable graph reads unavailable and
   shows no number. They make no model call and no agent request.
+- **SRF-OUT-09** — The selected run's book panel (`/api/runs/{run}/book`, DL-311) shows the book on
+  the run's session (its `RunRequest`'s `requested_at`) as the daily brief reads it: the brief's own
+  book lines, then one row per held name with its ticker and quantity and, from its held claim, the
+  close, stop and target in cents, whether the close is past the target, the three chances and the
+  gain at the close. Names with a claim lead, ordered by their chance of the stop first, highest
+  first and ties by ticker; a name with none follows, showing its ticker, its quantity and that it
+  has no forecast. A run whose session is not a date, or with nothing held, shows no row. The panel
+  reads only; it writes nothing and offers no control.

 ## Prohibitions (`NEV`)

@@ -226,6 +234,11 @@ green only when a functional test cites its ID (conventions §3). Tests + status

 ## Changelog

+- v1.9 — S287 / DL-311 (2026-10-21): new `SRF-OUT-09`, the selected run's book
+  panel: the brief's own book lines and one row per held name, the likeliest to reach its stop
+  first leading. The test-plan's status line, left at v1.6 by the PARAM-only v1.7 and v1.8, is
+  aligned. 31 / 38 → 32 / 39.
+
 - v1.8 — S274 / DL-300 (2026-10-14): PARAM only. master_window_start_utc is 22:00, the master's
   live wake (DL-294 amendment 1). No clause changes.

diff --git a/surfaces/laws/test-plan.md b/surfaces/laws/test-plan.md
index 5be453e7..f8beaecc 100644
--- a/surfaces/laws/test-plan.md
+++ b/surfaces/laws/test-plan.md
@@ -1,6 +1,6 @@
 # `Surfaces` — Law Test-Plan

-**Prefix:** `SRF` · **status:** LOCKED v1.6 · **aligned with:** laws.md LOCKED v1.6
+**Prefix:** `SRF` · **status:** LOCKED v1.9 · **aligned with:** laws.md LOCKED v1.9

 | Clause | Description | Test | Status |
 | --- | --- | --- | --- |
@@ -42,3 +42,4 @@
 | SRF-OBS-02 | Context bundles contain per-container logs and image evidence when available, and name unavailable or partial evidence truthfully. | `surfaces/tests/test_dashboard_bundle_azure.py::test_bundle_has_per_container_logs_and_real_image_tags`; `surfaces/tests/test_dashboard_bundle_azure.py::test_bundle_partial_log_failure_and_unavailable_mode` | 🟩 |
 | SRF-PERF-01 | Log and bundle reads are bounded by tail settings; invalid tail inputs fall back to the default. | `surfaces/tests/test_dashboard_app.py::test_s123_routes_use_fake_azure_and_tail_bounds`; `surfaces/tests/test_dashboard_bundle_azure.py::test_bundle_has_per_container_logs_and_real_image_tags` | 🟩 |
 | SRF-PERF-02 | Projection, fleet, cost, self-heal, GitHub, and Azure reads are bounded by declared timeout/cache settings. | _tbd_ | ⬜ |
+| SRF-OUT-09 | The selected run's book panel shows the brief's own book lines, then a row per held name from its held claim for the run's session (close, stop, target, past target, the three chances, gain), the likeliest to reach its stop first leading and names with no claim last; no session or no book, no row; it reads only. | `surfaces/tests/test_dashboard_book.py::test_the_book_view_says_what_the_brief_says_and_leads_with_the_stop`; `surfaces/tests/test_dashboard_book.py::test_a_run_with_no_request_or_no_book_shows_nothing`; `surfaces/tests/test_dashboard_book.py::test_the_panel_is_served_and_wired` | 🟩 |
```
