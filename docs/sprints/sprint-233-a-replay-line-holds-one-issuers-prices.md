<!-- Agent: planning | Role: sprint handover -->
# Sprint 233 — a replay line holds one issuer's prices, chained where its ticker changed

**Phase:** Etalon-first continuous improvement (DL-19) · next leg P17, item **E17.2b** (finishes E17.2)
**Branch:** `sprint-233-a-replay-line-holds-one-issuers-prices`
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** M
**Decisions:** [DL-227](../design-log.md) (S231's design and its 2026-09-26 amendment, which this sprint
answers) · [DL-226](../design-log.md) · [R008](../research/survivorship-free-universe/INDEX.md) ·
work-queue **82** · the builder records its decisions as the next free DL number (**DL-229** today;
S232 holds DL-228)

> **Why this bump kind.** No new capability. S231 promised *"the S&P 500 as it stood"*; its cache holds
> other issuers' prices on some lines and says they are covered. Making the promise true is a PATCH.

**Builder:** Codex. **Your worktree has no `.env` and no network.** Every proof is on synthetic fixtures;
the live build is the planner's, after merge. **If a number you measure differs from one written here,
stop and report. Do not adjust and continue.**

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

**No agent law book binds `scripts/`.** What binds this sprint: [`docs/laws/conventions.md`](../laws/conventions.md)
(module header, no magic numbers, citations in test docstrings), `CLAUDE.md` (the 200-line block covers
`scripts/`; header `Agent:`/`Role:`/`External I/O:`), [DL-227](../design-log.md) and its amendment, and
the **licensing rule** in `scripts/replay_dataset.py`'s docstring: *the repository is public and Alpaca
SIP bars are licensed, so the cache lives outside the worktree and is never committed.*

### The rule

1. **Before writing code**, read the files in the map below — whole file, first time.
2. There is no agent `test-plan.md` for `scripts/`; **the test plan in this spec is the contract**.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a rule contradicts this spec, STOP and report.**
7. **If a rule is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Tests cite the test-plan row they prove in their docstrings (`"""S233-A4: ..."""`).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**The planner's expected answer is No.** Everything lives in `scripts/` and `tests/`; no agent, no
contract, no image. If your design needs an agent or `contracts/` change, stop and report.

### Element → rule map

| Element you will touch | Read first | Why it binds |
| --- | --- | --- |
| `scripts/replay_dataset_sources.py` (90 lines) | its docstring; `scripts/replay_dataset.py` | `daily_bars` also builds `bars.csv.gz`; **its default request must not change** |
| `scripts/sp500_bars.py` (163) | DL-227 *Bars* | batching, the single re-fetch, window trimming |
| `scripts/sp500_membership.py` (179), `scripts/sp500_symbol_map.csv` (10) | DL-227, R008 | facts only, each row with measured evidence |
| `scripts/replay_universe.py` (161), `scripts/replay_universe_cache.py` (138), `scripts/sp500_coverage.py` (102) | DL-227 *Coverage and files* | the build order, the cache files, the coverage payload |
| `scripts/replay_dataset.py` (142), `scripts/exp013_regime_sizing.py` | read only | **must not change behaviour**: EXP-011 to EXP-013 reproduce from `bars.csv.gz` / `vix.csv.gz` via `load()` |

⚠️ **One invariant: no licensed or copied data enters the repo.** Fixtures are **synthetic** prices that
reproduce the measured *shapes* below, never Alpaca bars. The new known-moves CSV holds dates, kinds and
evidence text, not prices.

---

## Goal

After this sprint every line in the replay cache holds one issuer's prices. Each bar window is fetched
by the name as it stood on the window's last day (Alpaca `asof`), so a ticker's present-day owner no
longer supplies another company's history. Where a line changes source (a rename, or a map row), the
earlier source is chained to the later one on **unadjusted** closes, so the switch day's return is what
traded, not an artefact of two adjustment bases. A switch that still moves hard must name its corporate
action, and a single-day move beyond a named limit must be a listed, evidenced event, or the build fails.

## Why (context)

S231 merged on 2026-09-26 and its live build read **99.68 %** coverage with **0** unreconciled records.
The planner then checked identity, which the build does not, and found lines holding other companies'
prices, counted as *covered*. P17's walk-forward (E17.3) books P&L from these closes, so a wrong issuer
is a wrong result, not a gap. The cause is one request parameter: the builder never sends `asof`, and
Alpaca then resolves each symbol through its **present-day** lineage.

### Measured, 2026-09-26 — read these before designing

All from the planner's session on `main` @ `01fe3927`, live Alpaca SIP (`adjustment=all` unless marked
*raw*), the cache in `%USERPROFILE%\OneDrive\trading-agents-data`. **Denominator:** member-sessions over
the **2,697** SPY sessions 2016-01-04 → 2026-09-24, **732** membership episodes. The scripts are in the
planner's scratchpad, not the repo; their results are below and are **not reproducible in your worktree**
(no network). Your proofs are the synthetic fixtures in the test plan.

| # | Claim | Value | How it was measured |
| --- | --- | --- | --- |
| 1 | S231's cache | coverage **99.68 %** (1,355,406 / 1,359,748), 52 shortfalls, 0 unreconciled | *[measured]* `replay_universe.py build --end 2026-09-24 --from-snapshot`, then `--describe` |
| 2 | 🎯 **CTRA holds Contura Energy** from 2018-11-09 to 2021-10-01 | stored close 57.62 → 2.84 → 10.42 while Cabot (COG pinned `asof` 2021-09-30) traded 15–19; a **constant 0.81** ratio to AMR (Contura's successor) through 2021-02 | *[measured]* stored series vs `COG` pinned vs `AMR` |
| 3 | 🎯 **DD holds another issuer** 2016-01-04 → 2017-08-31 | the default series' daily return differs from E.I. du Pont's raw trades (DD *raw* pinned `asof` 2017-08-31: $63.07 → $83.93) by > 0.5 pt on **86 of 419** days; the pinned series on **4 of 419** (dividend days) | *[measured]* returns of each series vs raw |
| 4 | 🎯 **PSKY's Paramount years are corrupt** | S231's PARA window (2022-02-17 → 2025-08-06) closes run **57.8 → 110,500**; pinned `asof` 2025-08-06 they read **9.44 → 35.48** | *[measured]* old cache vs a pinned build |
| 5 | 🎯 **SW holds no WestRock** | the reconstruction has one SW episode 2016-01-04 → 2026-09-24 and **no WRK line**; SW's bars before 2016-05-16 read ~$187–196, then drop to $29 in one day. `WRK` pinned `asof` 2024-07-05 returns **2,140** rows, raw $45.52 → $51.51 | *[measured]* membership CSV; stored bars; `WRK` pinned |
| 6 | The pin fixes rows 2–4 and recovers sessions | a full build with every request pinned `asof` its window's last day: **99.96 %** (1,359,179 / 1,359,748), 44 shortfalls; STI +990, CTRA +720, ANDV +397, TE +125, SNDK +91 member-sessions (STI and TE were R008's *no bars*) | *[measured]* the S231 builder run with a pinned bar fetcher into a scratch cache, 382 requests, 600 s |
| 7 | The pin is safe elsewhere | re-fetching every episode pinned `asof` its last day: **728 of 732** hold a constant ratio to the stored series (same issuer, same returns); the 4 others are CTRA and DD (rows 2–3) and APTV and VTRS, whose map-row boundaries step (row 11). 🪤 The probe cannot see PSKY's or SW's early years (rows 4–5): it compares only dates both series hold | *[measured]* per-episode probe, all 732 |
| 8 | Batched vs single pinned requests | PARA and CTRA identical; DD differs in **level only** (both pinned series match raw returns on 415 of 419 days) | *[measured]* one symbol vs four in a request, same `asof` |
| 9 | Four renames the map lacks | BBWI ← **LB** to 2021-08-02 (1,405 rows), UAA ← **UA** to 2016-04-07 (66), AA ← **AA** to 2016-10-05 (192; the default mapping cuts at old Alcoa's 2016-10-06 reverse split), FTI ← **FTI** to 2017-01-13 (261; FMC Technologies before the Technip merger) — each row count equals the missing sessions exactly | *[measured]* each symbol pinned `asof` the range's last day |
| 10 | 🪤 **The DLPH row ends on the wrong day** | the committed row says `2016-01-04 → 2017-12-04` (*"switch date ASSUMED"*). Pinned `asof` 2017-12-04, DLPH returns **11** rows (2017-11-17 → 12-04) of **Delphi Technologies'** when-issued trading. Pinned `asof` **2017-11-16** it returns **474** raw rows of Delphi Automotive ($83.99 → $99.24), and APTV's own lineage starts 2017-11-17 (raw $98.70) | *[measured]* |
| 11 | 🎯 **Two adjustment bases make a false move at a switch** | with each window pinned, the switch day's adjusted move vs SPY is VTRS **−17.3 %** and LIN **−7.7 %**; on **raw** closes it is VTRS **+3.6 %** and LIN **−0.5 %**. Each earlier source is adjusted only up to its own last day, so the successor's later dividends open a gap | *[measured]* raw and adjusted closes of both sides of all 10 non-DLPH switches |
| 12 | Raw moves at every switch | UA→UAA **−48.9 %** (the class C share dividend), LB→BBWI **−18.1 %** (the Victoria's Secret spin), WRK→SW ≈ **−15.6 %** (raw 51.51 → 43.46; the deal paid cash), PARA→PSKY +6.4 %, SATS→ECHO −3.9 %, MYL→VTRS +3.6 %, FLT→CPAY +1.7 %, RE→EG −1.5 %, VIAC→PARA +1.4 %, PX→LIN −0.5 %, CBS→VIAC 0.0 %, DLPH→APTV −0.5 % | *[measured]* raw, pinned. WRK→SW excludes SPY's move *[ASSUMED small]* |
| 13 | Single-day moves beyond **50 %** of SPY's, same source | **10** in the pinned build: MRNA 2026-08-19 **+176 %**, SW 2016-05-16 −85 %, TGNA 2017-06-01 −79 %, RTX 2020-04-03 −71 %, FRC 2023-03-13 −62 %, SIVB 2023-03-09 −60 %, GL 2024-04-11 −54 %, PCG 2019-01-14 −52 %, ABMD 2022-11-01 +51 %, APA 2020-03-09 −50 %. Beyond 40 %: 25; beyond 25 %: 186 | *[measured]* consecutive-session close ratio over SPY's |
| 14 | MRNA's move is real | raw and adjusted agree: $62.96 → $174.38 on **199 M** shares (prior days ~4 M) | *[measured]* |
| 15 | 🪤 **TGNA's move is Alpaca's adjustment error** | raw $23.74 → $15.35 (**−35 %**, the 1-for-3 Cars.com spin); adjusted $57.86 → $12.47, with pre-spin **volume divided by 3**: the distribution was applied like a split | *[measured]* raw vs adjusted, pinned |
| 16 | RTX, FRC, SIVB, GL, PCG, ABMD, APA | public events (the UTX–Raytheon merger with the Carrier/Otis spins; two bank failures; a short report; PG&E's bankruptcy filing; J&J's ABIOMED bid; the March 2020 oil crash) | *[ASSUMED — public record; raw vs adjusted not measured]*. The planner measures each at the live check |
| 17 | The old dataset's request | `replay_dataset.py` calls `daily_bars(tickers, end)` with no `asof`; `bars.csv.gz` is built that way | *[measured]* read |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first** (A1, A3, A4 below). Watch them fail on `main`. Paste the red output.
2. **`daily_bars` can pin and can read raw.** Add keyword arguments `asof: str | None = None` and
   `adjustment: str = "all"`. `asof` is sent only when given; with neither argument the request is
   **byte-for-byte what it is today** (row 17), so `bars.csv.gz` and `load()` are untouched.
3. **Every bar window is fetched pinned `asof` its last day.** `fetch_bars_for_windows` passes
   `asof=<end>` on the batch request (a batch already shares one `(first, last)`, so `end` *is* each
   window's last day) and `asof=window.last` on the single re-fetch. The session list (SPY) is pinned the
   same way and keeps its **closes**, which items 5 and 6 need.
4. **The symbol map.** Add the four rows of row 9 and a `WRK` row for line SW (`2016-01-04 → 2024-07-05`,
   row 5); change the DLPH row's `to` to **2017-11-16** (row 10). Every row's `evidence` names the
   measurement (the table above is the source). Add an optional **`action`** column: empty, or the named
   corporate action at the row's switch (for example `class C share dividend`). Rows without the column
   still load.
5. **Chain at every source switch on raw closes.** Within a line, where consecutive sessions come from
   different symbols, fetch the **raw** close of both sides (each pinned `asof` its own window's last
   day) and rescale the earlier window's OHLC so the switch day's close-to-close ratio equals the raw
   ratio. Chain backwards from the latest window, which is never rescaled. Returns **inside** a window do
   not change (a constant factor). Record every switch in the coverage payload: line, both symbols, both
   dates, the raw move, the move vs SPY, and the owning map row's `action`.
6. **Two build guards, each failing the build loudly, naming what it found.**
   - **Switch guard:** a switch whose raw move vs SPY exceeds `SWITCH_MOVE_LIMIT` (**0.10**; below it, the largest
     measured switch is PARA→PSKY at +6.4 %) fails unless its map row names an
     `action`. Measured today: UAA, BBWI and SW need one (row 12).
   - **Move guard:** a same-source single-day move vs SPY beyond `MOVE_REVIEW_LIMIT` (**0.50**, row 13)
     fails unless listed in a committed `scripts/sp500_known_moves.csv` (`line,date,kind,evidence`;
     `kind` ∈ `event | distribution | adjustment-error`). Seed it from rows 13–16: **MRNA** `event`
     (measured), **TGNA** `adjustment-error` (measured), **RTX** `distribution`, and `event` for FRC, SIVB,
     GL, PCG, ABMD, APA (their evidence says *public record, raw not measured*). **SW 2016-05-16 is not
     listed**: the WRK row removes it, and a test proves the guard would have caught it.
7. **`--describe`** adds one line each for switches (count, how many carry an `action`) and known moves
   (count by kind).
8. **The design decisions** go to `docs/design-log.md` as the next free DL (**DL-229** today) before
   implementation.

### Out of scope (do NOT build this sprint)

- **Repairing Alpaca's adjustment errors** (TGNA, row 15). The move guard makes them visible and listed;
  rebuilding adjustments from raw bars and corporate-action feeds is its own measurement. E17.3 decides
  how its return engine treats an `adjustment-error` or a `distribution` day.
- **Adjusting spin-offs or distributions at a switch** (UAA, BBWI, SW). The raw move is what traded; the
  `action` names why. Valuing the distributed shares needs data we do not have.
- **The 43 *ends early* shortfalls** (deal closes, 1–5 sessions each). Named residue, as in S231.
- **`replay_dataset.py`, `bars.csv.gz`, `vix.csv.gz`, `load()`, EXP-011 to EXP-013.** Read only.
- **E17.3** (the walk-forward itself).
- **No `laws.md` edit. No ADR reversal.**

### The road not taken (LAW-06)

- **Pin `asof` to the episode's last day instead of the window's.** Rejected: a window cut by a map row
  (DLPH, CBS, VIAC, PARA, MYL, PX, and the new rows) needs its **own** symbol as it stood at **its** end;
  the episode's end names a different ticker. `asof = window.last` covers both cases with one rule.
- **An `asof` column on map rows.** Rejected: row 9 and row 10 are each reproduced by the uniform rule
  (`asof` = the row's `to`), so a per-row override adds a knob with no measured use.
- **Single-symbol requests everywhere.** Rejected: row 8 measured batched pinned requests returning the
  same returns (DD differs only by a constant factor), and batching keeps the build near 10 minutes.
- **Keep the default mapping and add map rows for the bad lines.** Rejected: rows 2–4 cannot be expressed
  as rows (COG under the default mapping stops at 2018-11-08), and row 7 shows the pin is right for the
  other 726.
- **Chain on adjusted closes, or not at all.** Rejected by row 11: two adjustment bases produce −17.3 %
  where +3.6 % traded.
- **Trust coverage as the identity check.** Rejected: rows 2–5 were all *covered*.
- **A guard on every move beyond 25 %.** Rejected: 186 events, mostly real; a list nobody reviews is not
  a guard. 50 % is 10 reviewed events.
- **Drop the DLPH row.** Rejected: row 10 recovers 474 real sessions of Delphi Automotive with the right
  end date.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Which map row owns a switch.** A `bars` row owns the switches at its two boundaries; a `rename` row
   owns the switch on its `from` date. Decide what happens when two rows claim one switch.
2. **Where the chain factors live.** Apply them to the stored bars (the cache holds chained prices), or
   store raw factors beside unchained bars. Recommended: store chained bars **and** the per-switch record,
   so a reader never has to chain and the audit trail survives.
3. **How the raw boundary closes are fetched** (one request per switch side, or grouped) without breaking
   the pin rule.
4. **The known-moves file's key and matching** (line + date of the move's second session), and how an
   unlisted move and a listed-but-absent move are reported.
5. **Module boundaries**: `sp500_bars.py` is 163 lines and `sp500_membership.py` 179, so chaining and the
   guards need new modules (for example `sp500_chain.py`, `sp500_guards.py`).

🪤 **Take the next free DL number, then re-check it at merge.** DL-227 is S231's; S232 (unmerged) holds
**DL-228**. Take DL-229 and check again when you hand back.

---

## Blast radius — measured 2026-09-26

| What | Detail |
| --- | --- |
| Files changed | `scripts/replay_dataset_sources.py` (90), `scripts/sp500_bars.py` (163), `scripts/sp500_membership.py` (179), `scripts/sp500_symbol_map.csv` (9 → 14 data rows + a column), `scripts/replay_universe.py` (161), `scripts/replay_universe_cache.py` (138), `scripts/sp500_coverage.py` (102) only if the payload moves; **new** chaining and guard modules, **new** `scripts/sp500_known_moves.csv`; tests `tests/sp500_fixtures.py` (95), `tests/test_sp500_bars.py` (106), `tests/test_replay_universe.py` (145), `tests/test_sp500_membership.py` (87), new test modules |
| Agents affected | none. No agent imports `scripts/` |
| Contract change? | no |
| Graph vocabulary change? | no |
| New env keys / tunables | none. The two limits are named constants in `scripts/`, each with its measured reason |
| Deploy implication | **none.** `scripts/` ships in no image |

---

## Steps, in order

1. **Read the rules** (MUST RULE above) and write the Law reading record.
2. **Record DL-229.**
3. **Plant the failing tests first** (A1, A3, A4) and watch them fail on `main`. Paste the red output.
4. **Implement** scope items 2–7.
5. **Prove the guards can fail (DL-70)**: drop the `asof` on the batch call (A1 red); chain on adjusted
   closes (A4 red); remove the `action` check (A6 red); remove the known-moves lookup (A7 red). Restore
   each.
6. **`make ci` green** — every step, **redirected to a file, never piped**.
7. **Fill the handback sections.**

---

## Test plan

All fixtures are **synthetic**: invented prices with the measured shapes, never Alpaca data.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 every window is fetched by the name as it stood | a fake `daily_bars` recording each call's `asof`; windows with different ends, one batch short so the single re-fetch runs | every batch call carries `asof` = its shared window end; every single re-fetch carries `asof` = that window's last day; the SPY session call is pinned to the build's end |
| A2 | the old dataset's request does not move | `requests.get` faked; call `daily_bars(["AAA"], "2020-01-02")` | the params hold **no** `asof` key and `adjustment == "all"`; with `asof=`/`adjustment="raw"` they carry both. The existing S231-A14 test still passes unchanged |
| A3 | 🎯 a reused ticker keeps its own issuer (the CTRA shape) | a fake that returns issuer B's prices for `XYZ` when `asof` is absent or later than 2018-11-08, and issuer A's when pinned to the episode's end | the built line holds A's closes on every session; no B close appears |
| A4 | 🎯 a switch is chained on raw closes (the VTRS shape) | two sources; adjusted levels differ by 20 % across the switch while raw closes are 15.855 → 16.34 | the switch day's close ratio equals 16.34 / 15.855 to 1e-9; every within-window daily return is unchanged to 1e-12; the latest window is not rescaled |
| A5 | chaining runs backwards through several switches (the PSKY shape) | three switches on one line | each switch ratio equals its raw ratio; factors compose; the switch records carry both symbols, dates, raw move, move vs SPY |
| A6 | 🪤 an undeclared hard switch fails the build (the UAA shape) | raw −48.9 % at a switch; the owning row with and without `action` | without: the build raises naming the line, both symbols and the date; with `action="class C share dividend"`: it passes and the record carries the action |
| A7 | 🪤 an unlisted big move fails the build (the SW shape) | a same-source −85 % day vs SPY, not in the known-moves file | the build raises naming line and date; listed with `kind=adjustment-error`: it passes and `--describe` counts it by kind |
| A8 | a move under the limit is not reviewed | a −49 % same-source day | no failure, no record |
| A9 | the map loads with and without `action` | two CSVs, one lacking the column | identical rows, `action` empty where absent |
| A10 | 🪤 the DLPH row ends where the lineage does | the committed map | the DLPH row's `to` is 2017-11-16 and APTV's own window starts 2017-11-17 |
| A11 | the existing S231 guarantees hold | S231-A1 to A14 | all pass; the cache still refuses a path inside the repo |

---

## Success factors

- [ ] Every bar request in the build is pinned `asof` its window's last day (A1); the old request is
      unchanged (A2).
- [ ] A reused ticker keeps its issuer on the fixture (A3).
- [ ] Every switch is chained on raw closes and recorded (A4, A5).
- [ ] An undeclared hard switch and an unlisted big move each fail the build, naming what they found
      (A6, A7), and a declared/listed one passes and is recorded.
- [ ] The map carries the 5 new rows, the corrected DLPH end, and `action` for UAA, BBWI and SW; the
      known-moves file carries the 9 seeded rows with their evidence.
- [ ] DL-229 recorded with rejected alternatives.
- [ ] Every guard planted, watched to fail, restored — stated per guard.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **`asof` changes the adjustment base, not only the mapping.** Two pinned windows of one line are
adjusted to different days; that is why a switch must be chained on raw closes (row 11), and why the
same symbol in two requests can differ by a constant factor (row 8). Compare returns, never levels.
🪤 **A pinned series equal to the stored one proves nothing about its early years.** SW's pinned and
default series agree, and both are wrong before 2016-05-16 (row 5). That is what the move guard is for.
🪤 **The batch re-fetch must be pinned too.** If only the batch call carries `asof`, every window the
batch drops (DL-227: DOW, DLPH) comes back from the single call under the default mapping.
🪤 **`daily_bars` builds `bars.csv.gz` as well.** A default of `asof=<end>` would silently change a
dataset three experiments were measured on. The default is "not sent".
🪤 **Do not seed the known-moves file with SW.** The WRK row removes that move; listing it would hide the
next lineage error of the same kind.
🪤 **Your worktree has no network.** The live build, the raw boundary closes and the verification of
the seeded moves are the planner's, after merge.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Near the block: `scripts/sp500_wiki.py` **197**, `scripts/sp500_membership.py` **179**,
  `scripts/sp500_bars.py` **163**, `scripts/replay_universe.py` **161**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: `SWITCH_MOVE_LIMIT` and `MOVE_REVIEW_LIMIT` are named constants whose comments cite
  the measurement (rows 12 and 13).
- Faults, not silent failure: a guard raises with the line, symbols and dates it found.
- `make ci` **every step** green, **100.00 % coverage floor**, **redirected to a file, never piped**.
- Version bump of the kind named at the top, `uv.lock` staged with it.
- Secrets never through the worktree. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**, run from the worktree whose
   `HEAD` is the commit being proven; check the printed SHA against `git rev-parse HEAD`.
2. Merge to `main` locally and push. Post-merge CodeQL.
3. **No deploy.** `scripts/` ships in no image.
4. **Planner's live build (the functionality check)**, from the main checkout with `.env`:
   `replay_universe.py build --end <yesterday> --from-snapshot`, then `--describe`. **Pass:**
   - coverage ≥ **99.9 %** *[projected from rows 6, 9 and 10: ≈ 99.99 %]*, 0 unreconciled;
   - the per-episode identity probe (DL-227 amendment) finds **0** lines whose returns differ from their
     pinned series, and CTRA, DD, PSKY and SW read their own issuers (rows 2–5);
   - every switch is chained and recorded; UAA, BBWI and SW carry an `action`; no other switch exceeds
     the limit;
   - every seeded known move is re-measured raw vs adjusted, and its `kind` is corrected where the raw
     bars say otherwise;
   - `bars.csv.gz` and `vix.csv.gz` are SHA-256 identical before and after; `git status` is clean.

   Record it in `docs/laws/functionality-checks.md`. **E17.3 may read the cache only after this passes.**

---

## Handover — paste this to Codex

```text
Sprint 233 — a replay line holds one issuer's prices, chained where its ticker changed (P17 E17.2b).
Spec: docs/sprints/sprint-233-a-replay-line-holds-one-issuers-prices.md (read all of it).

Branch: sprint-233-a-replay-line-holds-one-issuers-prices, in its own worktree. Never main.
You have NO .env and NO network. Every proof is on SYNTHETIC fixtures; never commit Alpaca data.

Why: S231's cache (merged 2026-09-26) reads 99.68 % coverage, but the planner measured lines holding
other issuers' prices, all counted as covered: CTRA 2018-2021 is Contura Energy, DD 2016-2017 is not
old DuPont, PSKY's 2022-2025 closes run to 110,500, SW has no WestRock. Cause: the builder never sends
Alpaca's `asof`, so each symbol resolves through its present-day lineage.

MUST RULE before any code: no agent law book binds scripts/; read docs/laws/conventions.md,
docs/laws/drift-register.md, CLAUDE.md, DL-227 (with its 2026-09-26 amendment), and the licensing rule
in scripts/replay_dataset.py. Fill the Law reading record first. Law-cycle answer expected: NO.

Build:
1. Red first: A1 (every request pinned asof its window's last day), A3 (a reused ticker keeps its
   issuer), A4 (a switch is chained on raw closes). Paste the red run.
2. daily_bars(..., asof=None, adjustment="all"): asof sent only when given; with neither argument the
   request is exactly today's (bars.csv.gz depends on it).
3. fetch_bars_for_windows: asof=end on the batch call, asof=window.last on the single re-fetch; the SPY
   session fetch is pinned and keeps its closes.
4. Map: add bars rows BBWI<-LB to 2021-08-02, UAA<-UA to 2016-04-07, AA<-AA to 2016-10-05,
   FTI<-FTI to 2017-01-13, SW<-WRK to 2024-07-05; DLPH row `to` becomes 2017-11-16. Optional `action`
   column; UAA, BBWI and SW rows carry one. Evidence text from the spec's Measured table.
5. Chain at every source switch: raw closes of both sides (each pinned asof its own window's last
   day); rescale the earlier window so the switch-day ratio equals the raw ratio; chain backwards from
   the latest window; record every switch in the coverage payload.
6. Guards that fail the build, naming what they found: a switch beyond SWITCH_MOVE_LIMIT=0.10 vs SPY
   without an `action`; a same-source day beyond MOVE_REVIEW_LIMIT=0.50 vs SPY not in the new
   scripts/sp500_known_moves.csv (seed: MRNA event, TGNA adjustment-error, RTX distribution, FRC,
   SIVB, GL, PCG, ABMD, APA event). Do NOT list SW.
7. --describe gains a switches line and a known-moves line.

Order: DL-229 (re-check the number) -> red A1/A3/A4 -> implement -> DL-70 plants (no asof on the batch
call; chain on adjusted closes; drop the action check; drop the known-moves lookup; each must go red;
restore) -> make ci redirected to a file, exit 0, 100.00 %.

DO NOT:
- change daily_bars' default request, replay_dataset.py, load(), bars.csv.gz or vix.csv.gz behaviour.
- add an asof column to the map (the uniform rule asof = window.last reproduces every measured case).
- chain on adjusted closes, or compare levels between pinned series: compare returns.
- try to repair Alpaca's adjustment errors or value spin-offs: record and name them.
- grow sp500_wiki.py (197), sp500_membership.py (179), sp500_bars.py (163) or replay_universe.py (161)
  past 200: new modules.
- claim a live proof: the live build is the planner's after merge.
- pin a version: PATCH, next available at merge, uv.lock staged with it.

Handback: Law reading record, Test plan results, Closeout (red then green, DL-70 plants, line counts,
make ci file + exit code), Return notes. Status: BUILT, and this sprint's README.md row leads with BUILT
in the same commit. Commit your work on the branch (you cannot push; the planner pushes and gates it).
Anything not met: "not done".
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
| *builder fills* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *builder fills*

**Contradictions found between a law and this spec:** *builder fills*

**Laws found silent where a decision was needed:** *builder fills*

**Clauses that were ⬜ and are now proven:** *builder fills*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | *builder fills* | | | |

**Tests added beyond the plan:** *builder fills*

---

## Closeout — evidence

**Status:** *builder fills: BUILT*

**Tree the proofs ran in (and `.env` present?):** *builder fills*

**Result:** *builder fills*

**Files changed:** *builder fills*

**Design decisions:** *builder fills: DL-229*

**Proof — the red run first:**

```text
builder fills
```

**Proof — the green run:**

```text
builder fills
```

**Guards planted:** *builder fills*

**Module line counts:** *builder fills*

**`make ci`:** *builder fills*

**`make gate-ran`:** *planner, after push*

**Not met / verified failing:** *builder fills*

---

## Return notes

- *builder fills*
